
import os
import csv
import sys
import codecs
import time
import fnmatch
from multiprocessing import Pool

from tangent.ranking.query import Query
from tangent.ranking.ranking_functions import *
from tangent.math.symboltree import SymbolTree

MIN_CHUNK_SIZE = 1000
N_SCORES = 7
SIM_FUNCTION = similarity_v06

def read_queries(filename):
    # read all text ...
    input_file = open(filename, "r", newline='', encoding='utf-8')
    reader = csv.reader(input_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    all_text = [row  for row in reader]
    input_file.close()

    current_query = None
    found_queries = []
    for parts in all_text:
        if len(parts) == 0:
            continue

        if parts[0] == "Q":
            current_query = parts[1]

        if parts[0] == "E":
            if current_query is not None:
                current_expression = parts[1]
                found_queries.append((current_query, current_expression))

            current_query = None

    return found_queries

def find_substructures(expressions_data):
    sub_groups = []

    query_expression, candidates_data = expressions_data

    if len(candidates_data) > 1:
        query = Query("query", query_expression)

        # create query tree ....
        rank = -1
        scores = None
        prev_scores = None

        for data_idx, candidate_data in enumerate(candidates_data):
            candidate_exp = candidate_data[0]
            rank = int(candidate_data[1])

            query.add_result(0, "", 0, candidate_exp, 0.0)

            result = query.results[candidate_exp]

            try:
                sim_res = SIM_FUNCTION(query.tree, result.tree, query.constraints)
                scores, matched_q, matched_c, unified_c, wildcard_c, unified = sim_res
            except:
                print("Error processing: ")
                print("Q: " + query_expression, flush=True)
                print("C: " + candidate_exp, flush=True)
                continue

            result.set_unified_elements(unified_c)
            result.set_matched_elements(matched_c)
            result.set_wildcard_matches(wildcard_c)
            result.new_scores = scores

            if prev_scores is None:
                prev_scores = scores
            else:
                if prev_scores != scores:
                    print("Error: Scores changed!")
                    print(prev_scores)
                    print(scores)
                    prev_scores = scores

        query.sort_results()

        if len(query.sorted_results) > 1:
            print("Error: Did not expect More than 1 group")
            print("-> " + str(len(query.sorted_results)))


        group = query.sorted_results[0]

        # for each sub group ...
        structures = []
        current_structure = 0
        for subgroup in group:
            # next substructure group in the overall rank...
            current_structure += 1

            structure_elements = []
            for sg_idx, expression in enumerate(subgroup):
                structure_elements.append(expression)

            structures.append(structure_elements)

    else:
        # just one expression in rank, no need to re-evaluate score ...
        candidate_data = candidates_data[0]
        candidate_exp = candidate_data[0]
        rank = int(candidate_data[1])
        scores = [float(part) for part in candidate_data[2:(2 + N_SCORES)]]

        # the list of structures only contains one structure with the same structure
        structures = [[candidate_exp]]

    return (rank, scores, structures)

def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython gold_standard_groups.py input_dir output_dir n_jobs [queries]")
        print("")
        print("Where:")
        print("\tinput_dir\t: Path to Directory that contains gold standard scores")
        print("\toutput_dir\t: Directory used to store final gold standard ranks")
        print("\tn_jobs\t\t: Number of jobs to use to compute the groups")
        print("\tqueries\t\t: Files that contain the queries")
        return

    input_dir = sys.argv[1]
    output_dir = sys.argv[2] + "/"

    try:
        n_jobs = int(sys.argv[3])
    except:
        print("Invalid number of jobs")
        return
    try:
        complete_list = os.listdir(input_dir)
        filtered_list = []
        for file in complete_list:
            if fnmatch.fnmatch(file, '*.tsv'):
                filtered_list.append(file)

        filtered_list = sorted(filtered_list)
    except:
        print( "Invalid input path!" )
        return

    all_queries = {}
    for filename in sys.argv[4:]:
        all_queries.update(read_queries(filename))

    start_time = time.time()
    for filename in filtered_list:
        # read file ...
        in_file = open(input_dir + "/" + filename, "r", encoding="'UTF-8'")
        exp_reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        all_expressions = [row for row in exp_reader]
        in_file.close()

        query_name = filename[:-4]
        if not query_name in all_queries:
            print("Query: " + query_name + " not found!")
            continue

        print("Processing Query: " + query_name)

        query_expression = all_queries[query_name]
        output_filename = output_dir + filename

        # prepare output ...
        out_file = open(output_filename, "w", encoding="'UTF-8'")
        csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        csv_writer.writerow(["SLT", "rank", "group"] + ["score" + str(n + 1) for n in range(N_SCORES)])
        out_file.close()

        pool = Pool(processes=n_jobs)

        current_pos = 1
        current_substructure = 0
        while current_pos < len(all_expressions):
            # read n_jobs groups, then create subgroups in parallel ..
            current_groups = []
            last_group = []
            last_rank = -1
            chunk_size = 0
            while current_pos < len(all_expressions):
                parts = all_expressions[current_pos]
                rank = int(parts[1])

                if rank != last_rank:
                    if len(last_group) > 0:
                        current_groups.append((query_expression, last_group))
                        last_group = []

                        if len(current_groups) >= n_jobs and chunk_size >= MIN_CHUNK_SIZE:
                            # next batch of groups to process completed...
                            break

                    last_rank = rank


                last_group.append(parts)
                chunk_size += 1

                current_pos += 1

            if len(last_group) > 0:
                current_groups.append((query_expression, last_group))

            print("Proccessing until rank " + str(last_rank), flush=True)

            # process them in parallel
            results = pool.map(find_substructures, current_groups)
            """
            print("Before: " + str(chunk_size) + ", After: " + str(sum([sum([len(subgroup) for subgroup in structures]) for rank, scores, structures in results])) +
                  ", G.B = " + str(len(current_groups)) + ", G.A = " + str(len(results)))
            """
            out_file = open(output_filename, "a", encoding="'UTF-8'")
            csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
            # combine results and output them to file
            for rank, scores, structures in results:
                for subgroup in structures:
                    # next substructure group in the overall rank...
                    current_substructure += 1

                    for expression in subgroup:
                        row = [expression, str(rank), str(current_substructure)] + [str(score) for score in scores]
                        csv_writer.writerow(row)

            out_file.close()

    end_time = time.time()

    elapsed = end_time - start_time
    print("Total elapsed time: " + str(elapsed))



if __name__ == '__main__':
    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')
    main()
