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
import os
from sys import argv
import sys
import codecs
from bs4 import BeautifulSoup
import time
import re

from tangent.math.version03_index import Version03Index
from tangent.math.math_extractor import MathExtractor
from tangent.utility.control import Control
from tangent.utility.Stats import Stats

sys.setrecursionlimit(10000)

"""
    The main application that given an nticr-like query file, queries the collection and returns the results
    Code is based on tangent/ntcir/ntcir11.py
    Revised 12/2015 to integrate all phases (FWT)
"""


def print_help_and_exit():
    """
    Prints usage statement
    """

    print("Usage: python runquery.py [<cntl-file>] or python runquery.py help")
    print("       default <cntl-file> is tangent.cntl")
    print()
    print("where <cntl-file> is a tsv file that contains a list of parameter-value pairs")
    print("and must include at least the following entries:")
    print("     queries\\t<file with queries in NTCIR format>")
    print("     database\\t<directory for storing database query files or results>")
    print("and may optionally include:")
    print("     window\\t<window-size>")
    print("     topk\\t<result-count>")
    print("         where 100 is default")
    print("     run\\t<arbitrary name for query run>")
    print("     mWeight\\t<percentage of weight for math (as opposed to text) matching")
    print("         where 50 is default")
    print("     mScore\\t{'core' | 'MSS'}")
    print("         where 'MSS' reranking is default")
    print("     runmode\\t{'now'} if immediate execution desired")
    print("         => requires all the following entries:")
    print("        mathURL\\t<address of math core search engine>")
    print("        mathPort\\t<base port for math core search engine>")
    print("            where port used is sum of mathPort+window")
    print("        textURL\\t<address for text search engine>")
    print("        textPort\\t<port for text search engine>")
    print("        textPath\\t<URL's path extension for text search engine>")
    print("        resultFile\\t<file for storing search results>")
    print("        doc_list\\t<file listing document locations")
    print("as well as other pairs.")
    exit()

def process_query_batch(args):
    """
    Given a query, generate query tuples for the math index
    :param args:
    :return: nil
    """
    stats = Stats()
    fileid = os.getpid()

    query_list, topk, math_index = args
    math_index.openDB(fileid,topk)

    stats.num_documents = len(query_list)

    for (query_num,query_string) in query_list:
        trees = MathExtractor.parse_from_xml(query_string, query_num, stats.missing_tags, stats.problem_files)
        stats.num_expressions += len(trees)

        # also need to handle keyword queries if present
        terms =  re.findall(r"<keyword[^>]*>\s*([^<]*\S)\s*</keyword>",query_string)
        stats.num_keywords += len(terms)

        math_index.search(fileid, query_num, trees, terms, topk)
    
    math_index.closeDB(fileid)
    return (fileid,stats)


def get_query(query_obj):
    """
    Parse the query object in xml and get the math and text
    :param query_obj:
    :return: query num, doc = '<doc>' formula* keyword* '</doc>'
    """
    query_num = query_obj.num.text.strip().translate({10:r"\n",9:r"\t"})
    query_list = []
    # get formulas
    for f in query_obj.findAll("formula"):
        math = f.find("m:math")  # assumes m is used for namespace
        query_list.append(str(math))

    # get keywords
    for k in query_obj.findAll("keyword"):
        # print("Keyword in query: "+str(k))
        query_list.append(str(k))

    return query_num, "<doc>" + " ".join(query_list) + "</doc>"

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
        
        query_file = cntl.read("queries")
        if not query_file:
            print("<cntl-file> missing queries")
            print_help_and_exit()
        window = cntl.read("window",default=0,num=True)
        if window and window < 0:  # negative window values make no sense
            print('Negative window values not permitted -- using 1')
            window = 1
        topk = cntl.read("topk",default=100,num=True)
        if topk < 1:  # non-positive values make no sense
            print('Non-positive topk values not permitted -- using 100')
            topk = 100
        run_tag = cntl.read("run",default="")
        run_tag = 'rituw_' + run_tag
##        system = cntl.read("system",default='Wikipedia')
##        if system not in ['Wikipedia', 'ntcir']:
##            print("Invalid system. Using 'Wikipedia' instead of %s\n" % system)
##            system = 'Wikipedia'

        math_index = Version03Index(cntl, window=window)

##        if cntl.read("results"):
##            # try ingesting and processing results (temporary setting)
##            tuples = math_index.get(query_file)
##            for qid,hit in tuples.items():
##                print(qid,hit)
##        else:
        
        with open(query_file, encoding='utf-8') as file:
            parsed = BeautifulSoup(file,"html.parser")

        query_list = parsed.find_all("topic")
        print("There are %s queries." % len(query_list))
        combined_stats = Stats()
        fileids = set()

##          try:
        query_list_m = list(map(get_query,query_list)) # whole batch for now
        args = [(query_list_m, topk, math_index)]
    
        for p in args:  # single-process execution
            (fileid,stats) = process_query_batch(p)
            fileids.add(fileid)
            combined_stats.add(stats)
##          except Exception as err:
##              reason = str(err)
##              print("Failed to process queries: "+reason, file=sys.stderr)

        cntl.store("query_fileids",str(fileids))
        
        print("Done preparing query batch for %s" % (query_file))
        combined_stats.dump()

        cntl.dump()  # output the revised cntl file

        end = time.time()
        elapsed = end - start

        print("Elapsed time %s" % (elapsed))
