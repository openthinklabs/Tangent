__author__ = 'mauricio'
import os
import codecs
import sys
import time
import csv
import math
import random
from multiprocessing import Pool


from tangent.ranking.query import Query
from tangent.ranking.ranking_functions import *
from tangent.math.symboltree import SymbolTree

# conf. Parameters

SIM_FUNCTION = similarity_v06
SCORE_ZERO_CHECK = 0
N_SCORES = 7

CHUNK_SIZE = 200
MAX_BATCH_SIZE=20000

DEBUG_START=0


if sys.stdout.encoding != 'utf8':
    sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf8':
    sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

def split_chunks(data, size, query):
    for n in range(0, len(data), size):
        yield (query, n,  data[n:n + size])

def eval_similarity(query_data):
    # do actually evaluate similarity ....
    query, start_idx, expressions = query_data

    csv_reader = csv.reader(expressions, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    end_idx = start_idx + len(expressions) - 1

    #create query slt
    query_name, query_expression = query
    query_tree = SymbolTree.parse_from_slt(query_expression)
    query_constraints = Query.create_default_constraints(query_tree)

    results = []
    for idx, parts in enumerate(csv_reader):
    #for idx, expression_info in enumerate(expressions):
        #parts = expression_info.strip().split("\t")
        expression = parts[0]
        doc_id = parts[1]
        location = parts[2]

        candidate_tree = SymbolTree.parse_from_slt(expression)

        try:
            data = SIM_FUNCTION(query_tree, candidate_tree, query_constraints)
            scores = data[0]
        except:
            print("Error processing: ")
            print(query_expression, flush=True)
            print(expression, flush=True)
            print("Doc: " + doc_id, flush=True)
            print("Loc: " + location, flush=True)
            continue

        # the index is only returned because some expressions might be absent in case of errors
        results.append((scores, start_idx + idx))

    print("Processed: " + str(start_idx) + " to " + str(end_idx) + " finished", flush=True)

    return results

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

def join_lists(lists):
    result = []
    for list in lists:
        result += list

    return result

def save_temporal(prefix, number, results, offset):
    out_file = open(prefix + str(number) + ".tsv", "w", encoding="'UTF-8'")
    csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    for scores, exp_idx in results:
        #line = str(exp_idx + offset) + "\t" + ("\t".join([str(score) for score in scores])) + "\n"
        #out_file.write(line)
        row = [str(exp_idx + offset)] + [str(score) for score in scores]
        csv_writer.writerow(row)

    out_file.close()

def load_temporal(prefix, number):
    results = []

    in_file = open(prefix + str(number) + ".tsv", "r", newline='', encoding='utf-8')
    reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    all_lines = [row  for row in reader]
    in_file.close()

    for parts in all_lines:
        idx = int(parts[0])

        #Note: not all scores are floats. This will result in larger output in final tsv file
        scores = [float(part) for part in parts[1:]]

        results.append((scores, idx))

    return results

def main():
    if len(sys.argv) < 4:
        print("Usage")
        print("\tpython gold_standard_scores.py expressions output n_jobs [queries]")
        print("")
        print("Where:")
        print("\texpressions\t: File that contains all unique expressions")
        print("\toutput\t: Directory where gold standard scores will be stored")
        print("\tn_jobs\t: Number of process to use")
        print("\tqueries\t: Files that contains indexed queries")
        return

    exp_filename = sys.argv[1]
    out_prefix = sys.argv[2] + "/"

    try:
        n_jobs = int(sys.argv[3])
    except:
        print("Invalid number of jobs")
        return

    print("Using " + str(n_jobs) + " jobs", flush=True)

    exp_file = open(exp_filename, "r", encoding="'UTF-8'")
    total_bytes_input = exp_file.seek(0, os.SEEK_END)
    exp_file.close()

    all_queries = []
    for filename in sys.argv[4:]:
        all_queries += read_queries(filename)

    # sort by name
    all_queries = sorted(all_queries)


    print("Total Queries Found: " + str(len(all_queries)), flush=True)

    start_time = time.time()
    if n_jobs > 1:
        pool = Pool(processes=n_jobs)

    processed = 0
    for query_name, query_exp in all_queries:
        print("Processing: " + query_name, flush=True)

        current_query = (query_name, query_exp)

        # first create separate files containing raw scores ...
        n_partitions = 0
        last_position = 0
        first_idx = 0
        input_complete = False
        while not input_complete:
            # read next batch ...
            current_expressions = []

            exp_file = open(exp_filename, "r", encoding="'UTF-8'")
            exp_file.seek(last_position, 0)

            while len(current_expressions) < MAX_BATCH_SIZE:
                line = exp_file.readline()
                if line:
                    #add to the current batch ...
                    current_expressions.append(line)
                else:
                    # EOF reached ...
                    input_complete = True
                    break

            last_position = exp_file.tell()
            exp_file.close()

            # process batch ...
            if len(current_expressions) > 0:
                n_partitions += 1
                print("Partition " + str(n_partitions) + " (" + str(last_position) + " of " + str(total_bytes_input) + ")" , flush=True)

                if processed == 0 and n_partitions < DEBUG_START:
                    print("Skipping .... ", flush=True)
                    continue

                # execute in parallel....
                chunks = split_chunks(current_expressions, CHUNK_SIZE, current_query)

                if n_jobs > 1:
                    results = pool.map(eval_similarity, chunks)
                else:
                    # debug: Single threaded ...
                    results = []
                    for chunk in chunks:
                        results.append(eval_similarity(chunk))

                # join results ...
                results = join_lists(results)

                # save them to temporal file
                save_temporal("gs_tempo_", n_partitions - 1, results, first_idx)

                first_idx += len(current_expressions)


        # "bubble-sort" the files raw score files in pairs
        print(" ... now sorting data in temporal files ... ", flush=True)
        print()
        for idx in range(n_partitions - 1):
            # load current temporal ...
            first_part = load_temporal("gs_tempo_", idx)
            n_first = len(first_part)

            # for every other part ...
            for idx2 in range(idx + 1, n_partitions):
                print("File " + str(idx) + " vs " + str(idx2), end="\r", flush=True)
                second_part = load_temporal("gs_tempo_", idx2)

                # combine and sort ....
                combined = first_part + second_part
                combined = sorted(combined, reverse=True)

                # now split again ...
                first_part = combined[:n_first]
                second_part = combined[n_first:]

                # save second part to file ...
                save_temporal("gs_tempo_", idx2, second_part, 0)

            # save current part to file ...
            save_temporal("gs_tempo_", idx, first_part, 0)

        # load each split and compute the ranks while sending results to final file
        print("")
        print(" ... Saving into single result file ... ", flush=True)

        # read all expressions ...
        exp_file = open(exp_filename, "r", newline='', encoding='utf-8')
        reader = csv.reader(exp_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        all_expressions = [row  for row in reader]
        exp_file.close()

        out_file = open(out_prefix + query_name + ".tsv", "w", encoding="'UTF-8'")
        csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

        csv_writer.writerow(["SLT", "rank"] + ["score" + str(n + 1) for n in range(N_SCORES)])

        current_rank = 0
        current_scores = [None] * N_SCORES

        for part_idx in range(n_partitions):
            results = load_temporal("gs_tempo_", part_idx)

            for scores, exp_idx in results:
                # check if expression is no longer relevant ...
                if scores[SCORE_ZERO_CHECK] <= 0.0:
                    break

                if scores != current_scores:
                    current_rank += 1
                    current_scores = scores

                slt = all_expressions[exp_idx][0]

                #line += "\t" + str(current_rank) + "\t" + ("\t".join([str(score) for score in scores])) + "\n"
                #out_file.write(line)
                row = [slt, str(current_rank)] + [str(score) for score in scores]
                csv_writer.writerow(row)

            # delete temporal files
            os.remove("gs_tempo_" + str(part_idx) + ".tsv")

        out_file.close()
        processed += 1

    end_time = time.time()

    elapsed_time = end_time - start_time
    print("Total elapsed time: " + str(elapsed_time))


if __name__ == '__main__':
    main()