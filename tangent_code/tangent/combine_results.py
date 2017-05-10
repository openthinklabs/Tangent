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
__author__ = 'KDavila, FWTompa'

import os
import sys
import time
import codecs
import pickle

from tangent.utility.control import Control
from tangent.math.mathdocument import MathDocument
from tangent.utility.read_results import ReadResults
from tangent.utility.comp_query import CompQuery

from tangent.ranking.query import Query
from tangent.ranking.ranking_functions import *
from tangent.ranking.mathml_cache import MathMLCache

def optional_parameters(args):
    values = {}

    pos = 0
    while pos < len(args):
        if args[pos][0] == "-":
            arg_name = args[pos][1:]
            if pos + 1 < len(args):
                values[arg_name] = args[pos + 1]
            else:
                print("incomplete parameter " + arg_name)
            pos += 2
        else:
            print("Unexpected value: " + args[pos])
            pos += 1

    return values


if __name__ == '__main__':
    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print("Usage")
        print("\tpython3 combine_results.py <cntl-file>")
        print("")
        print("where <cntl-file> is a tsv file that contains a list of parameter-value pairs")
        print("and must include at least the following entries:")
        print("     doc_list\\t<doc-id mapping file name>")
        print("           where the mapping file is itself a tsv file")
        print("           containing fileLocator-fileAbbr pairs")
        print("     file_skips\\t(created by formula indexing module)")
        print("     math_results\\t<file with results from core formula retrieval engine")
        print("     text_results\\t<file with results from text search engine>")
        print("     combined_results\\t<file to store combined results>")
        print("     combine_math\\t{'rerank' | 'average'} (mechanism for combining math results)")
        print("     mweight\\t0..100 (percentage of weight on formula matches)")
        print("and may optionally include:")
        print("     run\\t<arbitrary name for query run>")
        print("as well as other pairs.")
        print("")
        print("Optional additional command line parameters:")
        print("\t-w\twindow\t\t: Window for pair generation")
        exit()


    #load control file
    control = Control(sys.argv[1]) # control file name (after indexing)
    math_doc = MathDocument(control)

    minput_filename = control.read("math_results")
    tinput_filename = control.read("text_results")
    combiner = control.read("combine_math")
    mweight = control.read("mweight",num=True,default=70)
    output_filename = control.read("combined_results")
    
    optional_params = optional_parameters(sys.argv[2:])


    window = control.read("window",num=True,default=1)
    if "w" in optional_params:
        try:
            w = int(optional_params["w"])
            if w <= 0:
                print("Invalid window, using value from control file")
            else:
                window = wm
        except:
            print("Invalid value for window, using value from control file")

    if "h" in optional_params:
        html_prefix = optional_params["h"]
        if not os.path.isdir(html_prefix):
            os.makedirs(html_prefix)
        if not os.path.isdir(html_prefix + "/images"):
            os.makedirs(html_prefix + "/images")
    else:
        html_prefix = None

    if "c" in optional_params:
        condition = optional_params["c"]
        print("testing condition: " + condition)
    else:
        condition = "undefined"

    if "s" in optional_params:
        stats_file = optional_params["s"]
    else:
        stats_file = None

    if "t" in optional_params:
        times_file = optional_params["t"]
    else:
        times_file = None

    all_queries = ReadResults.read_math_results(minput_filename,math_doc)
    ReadResults.add_text_results(all_queries,tinput_filename,math_doc)

    start_time = time.time()
    for query in all_queries.values():
        query_start_time = time.time() * 1000 # RZ: ms
        query.combine_math_text(combiner,mweight)
        query_end_time = time.time() * 1000 # RZ: ms
        query.elapsed_time = query_end_time - query_start_time 

    end_time = time.time() 
    elapsed = end_time - start_time
    print("Elapsed Time Ranking Documents: " + str(elapsed) + "s")

    #now, output the re-ranked results...
    out_file = open(output_filename, "w", encoding='UTF-8')
    for query in all_queries.values():
        out_file.write("\n")
        query.output_query(out_file)
 
##        if html_prefix is not None:
##            print("Saving " + query.name + " to HTML file.....")
##            query.save_html(html_prefix)
    out_file.close()

##    #if stats file is requested ...
##    if stats_file is not None:
##        out_file = open(stats_file, "w")
##        out_file.write(Query.stats_header("\t"))
##        for query in all_queries:
##            query.output_stats(out_file,"\t", condition)
##        out_file.close()
##
##    # if times file is requested ...
##    if times_file is not  None:
##        sorted_queries = sorted([(query.name.strip(), query) for query in all_queries])
##
##        if os.path.exists(times_file):
##            out_file = open(times_file, "a")
##        else:
##            out_file = open(times_file, "w")
##            header = "condition," + ",".join([name for (name, query) in sorted_queries])
##            out_file.write(header + "\n")
##
##        line = condition
##
##        for name, query in sorted_queries:
##            line += "," + str(query.elapsed_time)
##
##        out_file.write(line + "\n")
##
##        out_file.close()

    print("Finished successfully")
    
