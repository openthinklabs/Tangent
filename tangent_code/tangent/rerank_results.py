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
__author__ = 'KDavila'

import os
import sys
import time
import codecs
import pickle
import csv

from tangent.utility.control import Control
from tangent.math.mathdocument import MathDocument

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

def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython3 rerank_results.py control input_results metric output_results")
        print("")
        print("Where:")
        print("\tcontrol:\tPath to tangent control file")
        print("\tinput_results:\tPath to file with results to re-rank")
        print("\tmetric:\t\tSimilarity metric to use [0-4]")
        print("\toutput_results:\tPath to file where re-ranked results will be stored")
        print("")
        print("Optional:")
        print("\t-w\twindow\t\t: Window for pair generation")
        print("\t-h\thtml_prefix\t: Prefix for HTML output (requires dot)")
        print("\t-c\tcondition\t: Current test condition")
        print("\t-s\tstats\t\t: File to store stats")
        print("\t-t\ttimes\t\t: File to accumulate time stats")
        print("\t-k\tmax_results\t: K number of results to rerank as maximum")
        return

    control_filename = sys.argv[1]
    input_filename = sys.argv[2]

    try:
        metric = int(sys.argv[3])
        if metric < -1 or metric > 11:
            print("Invalid similarity metric function")
            return
    except:
        print("Invalid similarity metric function")
        return

    output_filename = sys.argv[4]

    optional_params = optional_parameters(sys.argv[5:])

    #load control file
    control = Control(control_filename) # control file name (after indexing)
    math_doc = MathDocument(control)

    if "w" in optional_params:
        try:
            window = int(optional_params["w"])
            if window <= 0:
                print("Invalid window")
                return
        except:
            print("Invalid value for window")
            return
    else:
        window = int(control.read("window"))

    if "h" in optional_params:
        html_prefix = optional_params["h"]
        if not os.path.isdir(html_prefix):
            os.makedirs(html_prefix)

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

    if "k" in optional_params:
        try:
            max_k = int(optional_params["k"])
        except:
            print("Invalid max_results parameter")
            return
    else:
        max_k = 0

    if "t" in optional_params:
        times_file = optional_params["t"]
    else:
        times_file = None

    in_file = open(input_filename, 'r', newline='', encoding='utf-8')
    reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    lines = [row  for row in reader]
    in_file.close()

    mathml_cache_file = control_filename + ".retrieval_2.cache"
    if not os.path.exists(mathml_cache_file):
        mathml_cache = MathMLCache(control_filename)
    else:
        cache_file = open(mathml_cache_file, "rb")
        mathml_cache = pickle.load(cache_file)
        cache_file.close()

    current_query = None
    current_name = None
    current_tuple_retrieval_time = 'undefined'
    all_queries = []

    #read all results to re-rank
    for idx, line in enumerate(lines):
        #parts = line.strip().split("\t")
        parts = line

        if len(parts) == 2:
            if parts[0][0] == "Q":
                current_name = parts[1]
                current_query = None


            elif parts[0][0] == "E":
                if current_name is None:
                    print("invalid expression at " + str(idx) + ": query name expected first")
                else:
                    query_expression = parts[1]

                    #query_offset = len(all_queries)
                    query_offset = int(current_name.split("-")[-1]) - 1

                    if html_prefix != None:
                        mathml = mathml_cache.get(-1, query_offset, query_expression, True)

                        # create empty directories for this query ...
                        if not os.path.isdir(html_prefix + "/" + current_name):
                            os.makedirs(html_prefix + "/" + current_name)

                        if not os.path.isdir(html_prefix + "/" + current_name + "/images"):
                            os.makedirs(html_prefix + "/" + current_name + "/images")
                    else:
                        mathml = None

                    current_query = Query(current_name, query_expression, mathml, current_tuple_retrieval_time, max_k)
                    current_name = None
                    all_queries.append(current_query)

                    print("Query: " + current_query.name + ": " + current_query.expression)
                    #print(mathml)
                    #current_query.tree.save_as_dot("expre_" + str(idx) + ".gv")

            elif parts[0][0] == "C":
                if current_query is None:
                    print("invalid constraint at " + str(idx) + ": query expression expected first")
                else:
                    # create a constraint tree
                    current_query.set_constraints(parts[1])

        # RZ: Record tuple-based retrieval time and other metrics.
        if len(parts) == 3 and parts[0][0] == "I" and current_query != None:
            if parts[1] == "qt":
                current_query.initRetrievalTime = float( parts[2] )
            elif parts[1] == "post":
                current_query.postings = int( parts[2] )
            elif parts[1] == "expr":
                current_query.matchedFormulae = int( parts[2] )
            elif parts[1] == "doc":
                current_query.matchedDocs = int( parts[2] )

        if len(parts) == 5:
            if parts[0][0] == "R":
                doc_id = int(parts[1])
                location = int(parts[2])
                doc_name = math_doc.find_doc_file(doc_id)

                expression = parts[3]
                score = float(parts[4])

                if html_prefix != None:
                    mathml = mathml_cache.get(doc_id, location, expression)
                else:
                    mathml = None

                if current_query is None:
                    print("Error: result listed before a query, line " + str(idx))
                else:
                    current_query.add_result(doc_id, doc_name, location, expression, score, mathml)

    cache_file = open(mathml_cache_file, "wb")
    pickle.dump(mathml_cache, cache_file, pickle.HIGHEST_PROTOCOL)
    cache_file.close()

    # now, re-rank...
    print("Results loaded, reranking ...")

    # compute similarity first...

    start_time = time.time()
    for q_idx, query in enumerate(all_queries):
        #print("Evaluating: " + query.name + " - " + query.expression)

        query_start_time = time.time() * 1000 # RZ: ms
        for res_idx, exp_result in enumerate(query.results):
            result = query.results[exp_result]

            #print("Candidate: " + result.expression)

            scores = [0.0]
            if metric == -1:
                # bypass mode, generate HTML for original core ranking
                scores = [result.original_score]
                matched_c = {}
            elif metric == 0:
                # same as original based on f-measure of matched pairs..
                pairs_query = query.tree.root.get_pairs("", window)
                pairs_candidate = result.tree.root.get_pairs("", window)
                scores, matched_q, matched_c = similarity_v00(pairs_query, pairs_candidate)
            elif metric == 1:
                # based on testing of alignments....
                scores, matched_q, matched_c = similarity_v01(query.tree, result.tree)
            elif metric == 2:
                # Same as 0 but limiting to matching total symbols first...
                pairs_query = query.tree.root.get_pairs("", window)
                pairs_candidate = result.tree.root.get_pairs("", window)
                scores, matched_q, matched_c = similarity_v02(pairs_query, pairs_candidate)
            elif metric == 3:
                # modified version of 2 which performs unification....
                pairs_candidate = result.tree.root.get_pairs("", window)
                scores, matched_q, matched_c, unified_c = similarity_v03(pairs_query, pairs_candidate)
                result.set_unified_elements(unified_c)
            elif metric == 4:
                # modified version of 1 which performs unification ...
                sim_res = similarity_v04(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)
            elif metric == 5:
                # modified version of 4 which allows multiple sub matches
                sim_res = similarity_v05(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
            elif metric == 6:
                # modified version of 4 which allows subtree matches for wildcards (partial support)...
                sim_res = similarity_v06(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)
            elif metric == 7:
                # modified version of 4 which allows subtree matches for wildcards (partial support)...
                sim_res = similarity_v07(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)
            elif metric == 8:
                # modified version of 4 which allows subtree matches for wildcards (partial support)...
                sim_res = similarity_v08(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)
            elif metric == 9:
                # modified version of 4 which allows subtree matches for wildcards (partial support)...
                sim_res = similarity_v09(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)
            elif metric == 10:
                # modified version of 4 which allows subtree matches for wildcards (partial support)...
                sim_res = similarity_v10(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)
            elif metric == 11:
                # matching of metric 06 with scores from metric 04 (MSS)
                sim_res = similarity_v11(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
                result.set_unified_elements(unified_c)
                result.set_wildcard_matches(wildcard_c)
                result.set_all_unified(unified)


            result.set_matched_elements(matched_c)

            result.new_scores = scores

        query_end_time = time.time() * 1000 # RZ: ms

        # re-rank based on new score(s)
        query.sort_results()
        query.sort_documents()
        query.elapsed_time = query_end_time - query_start_time 

    end_time = time.time() 
    elapsed = end_time - start_time
    print("Elapsed Time Ranking: " + str(elapsed) + "s")

    #now, store the re-ranked results...
    out_file = open(output_filename, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    for query in all_queries:
        csv_writer.writerow([])
        query.output_query(csv_writer)
        query.output_sorted_results(csv_writer)

        if html_prefix is not None:
            print("Saving " + query.name + " to HTML file.....")
            query.save_html(html_prefix + "/" + query.name)
    out_file.close()

    #if stats file is requested ...
    if stats_file is not None:
        out_file = open(stats_file, "w")
        out_file.write(Query.stats_header("\t"))
        for query in all_queries:
            query.output_stats(out_file,"\t", condition)
        out_file.close()

    # if times file is requested ...
    if times_file is not  None:
        sorted_queries = sorted([(query.name.strip(), query) for query in all_queries])

        if os.path.exists(times_file):
            out_file = open(times_file, "a")
        else:
            out_file = open(times_file, "w")
            header = "condition," + ",".join([name for (name, query) in sorted_queries])
            out_file.write(header + "\n")

        line = condition

        for name, query in sorted_queries:
            line += "," + str(query.elapsed_time)

        out_file.write(line + "\n")

        out_file.close()

    print("Finished successfully")
    

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    main()
