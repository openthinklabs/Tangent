"""
    Tangent
    Copyright (c) 2013, 2015 David Stalnaker, Richard Zanibbi, Nidhin Pattaniyil,
                  Andrew Kane, Frank Tompa, Kenny Davila Castellanos

    This file is part of Tangent.

    Tanget is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tangent is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tangent.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
        - Richard Zanibbi: rlaz@cs.rit.edu
"""
from concurrent.futures import ProcessPoolExecutor
import csv
import multiprocessing
import sys
import codecs
from tangent.utility.Stats import Stats
from tangent.math.version03_index import Version03Index
from tangent.math.math_extractor import MathExtractor
from tangent.utility.control import Control
from tangent.math.mathdocument import MathDocument
import time

from multiprocessing import Lock
sys.setrecursionlimit(10000)
from sys import argv, exit
import math

"""
Indexer is a standalone script that indexes a collection

Supports mathml,.xhtml and tex files
"""

def print_help_and_exit():
    """
    Prints usage statement
    """

    print("Usage: python index.py [<cntl-file>] or python index.py help")
    print("       default <cntl-file> is tangent.cntl")
    print()
    print("where <cntl-file> is a tsv file that contains a list of parameter-value pairs")
    print("and must include at least the following entries:")
    print("     doc_list\\t<doc-id mapping file name>")
    print("and may optionally include:")
    print("     window\\t<window-size>")
    print("     chunk_size\\t<chunk_size>")
    print("           number of documents per batch, default=200")
    print("as well as other pairs.")
    print("N.B. index.py will update <cntl-file> to also include:")
    print("     cntl, file_skips, and index_fileids.")
    exit()


def read_file(filename, file_id, missing_tags=None, problem_files=None):
    """
    Read file for parsing

    :type filename: string
    :param filename: file to be parsed

    :rtype: list(SymbolTree)
    :return list of Symbol trees found in the file
    """
    #s = time.time()
    (ext,content) = MathDocument.read_doc_file(filename)
    if ext == '.tex':
        t = MathExtractor.parse_from_tex(content, file_id)
        #print("file %s took %s"%(file_id,time.time()-s))
        return [t]
    elif ext in {'.xhtml', '.mathml', '.mml', '.html'}:
        t = MathExtractor.parse_from_xml(content, file_id, missing_tags=missing_tags, problem_files=problem_files)
        #print("file %s took %s per expr"%(file_id,(time.time()-s)/len(t)))
        return t
    else:
        problem_files["unknown_filetype"] = problem_files.get("unknown_filetype", set())
        problem_files["unknown_filetype"].add(filename)
        print('Unknown filetype %s for %s' % (ext, filename))
        return []

def math_indexer_task(pargs) -> (str, list):
    """
    creates index tuples for the expressions in this subcollection
    :param pargs:
    :return: (fileid, combined_stats)
    """
    math_index, cntl, chunkid = pargs
    combined_stats = Stats()

    docs = MathDocument(cntl)

    (chunk_size, mappings) = docs.read_mapping_file(chunkid)
    combined_stats.num_documents += len(mappings)

    seen_docs = []  # just dump them as they come
    for (doc_id, filename) in enumerate(mappings,start=chunkid*chunk_size):
##        print('parsing %s, id:%s ' % (filename, doc_id),flush=True)
        try:
            # get all the symbol trees found in file
            for tree in read_file(filename, doc_id, missing_tags=combined_stats.missing_tags,
                               problem_files=combined_stats.problem_files):
                combined_stats.num_expressions += 1
                combined_stats.global_expressions += len(tree.position)
                # pairs = tree.get_pairs(window) do not store pairs -- will be created in C++ module
                seen_docs.append(tree)
        except Exception as err:
            reason = str(err)
            print("Failed to process document "+filename+": "+reason, file=sys.stderr)
            combined_stats.problem_files[reason] = combined_stats.problem_files.get(reason, set())
            combined_stats.problem_files[reason].add(doc_id)

    fileid = math_index.add(seen_docs)
    print("%s is done saving to database %s" % (chunkid,fileid), flush=True)
    return fileid, combined_stats

if __name__ == '__main__':

    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    if (len(argv) > 2 or (len(argv) == 2 and argv[1] == 'help')):  # uses control file to control all parameters
        print_help_and_exit()
    else:
        start = time.time()
        try:
            cntl = Control(argv[1]) if len(argv) == 2 else Control()
        except Exception as err:
            print("Error in reading <cntl-file>: " +str(err))
            print_help_and_exit()

        doc_id_mapping_path = cntl.read("doc_list")
        if not doc_id_mapping_path:
            print("<cntl-file> missing doc_list")
            print_help_and_exit()
        window = cntl.read("window",num=True)
        if window and window < 1:  # window values smaller than 2 make no sense
            print('Window values smaller than 1 not permitted -- using 1')
            window = 1
        chunk_size = cntl.read("chunk_size",num=True,default=200)

        print("reading %s" % doc_id_mapping_path, flush=True)
        mappings = []
        filepos = []

        num_docs = 0
        row = "-"
        with open(doc_id_mapping_path, newline='', encoding='utf-8') as mapping_file:
            while True:
                if num_docs % chunk_size == 0:
                    filepos.append(mapping_file.tell())
                num_docs += 1
                row = mapping_file.readline()
                if row == "":
                    num_docs -= 1
                    if num_docs % chunk_size == 0:
                        del filepos[-1]
                    break
        cntl.store("file_skips",str(filepos))

        print("There are " + str(num_docs) + " documents to index", flush=True)
        combined_stats = Stats()

        if num_docs > 0:
            math_index = Version03Index(cntl, window=window)

            max_jobs = min(10,num_docs)
            manager = multiprocessing.Manager()
            lock = manager.Lock()

            #identify chunks to be indexed by each process
            args = [(math_index, cntl, chunkid) for chunkid in list(range(len(filepos)))]

            fileids = set()

##            for p in args:  # single-process execution, for debugging
##                fileid, stats = math_indexer_task(p)
##                fileids.add(fileid)
##                combined_stats.add(stats)

            with ProcessPoolExecutor(max_workers=max_jobs) as executor:
                for fileid, stats in executor.map(math_indexer_task, args):
                    fileids.add(fileid)
                    combined_stats.add(stats)

            for fileid in fileids:
                math_index.closeDB(fileid, mode="i")
            cntl.store("index_fileids",str(fileids))

        print("Done indexing collection %s" % (doc_id_mapping_path))
        combined_stats.dump()

        cntl.dump()  # output the revised cntl file

        end = time.time()
        elapsed = end - start

        print("Elapsed time %s" % (elapsed))
