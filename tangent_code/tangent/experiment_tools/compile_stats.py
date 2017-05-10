__author__ = 'mauricio'

import sys

stat_keys = ["index_time" , "doc_ids", "dict_expressions", "dict_terms", "dict_relationships", "unique_tuples",
             "total_tuple_count", "unique_var_tuples", "total_var_tuple_count", "sub_expr_docs"]
query_keys = ["time", "postings", "postings_skipped", "expressions", "expressions_skipped",  "documents", "count_results"]

def process_file(filename):
    print("Processing: " + filename)

    stats = {key: 0 for key in stat_keys }
    per_query = {}

    # read entire file ...
    input_file = open(filename, "r", encoding='utf-8')
    all_lines = input_file.readlines()
    input_file.close()

    current_query = None
    query_count = 0

    for line in all_lines:
        if line[0] == "I":
            parts = line.split("\t")

            # general stats ...
            if parts[1] == "it":
                stats["index_time"] += float(parts[2])
            elif parts[1] == "dictDocIDs":
                stats["doc_ids"] = int(parts[2])
            elif parts[1] == "dictExpressions":
                stats["dict_expressions"] = int(parts[2])
            elif parts[1] == "dictTerms":
                stats["dict_terms"] = int(parts[2])
            elif parts[1] == "dictRelationships":
                stats["dict_relationships"] = int(parts[2])
            elif parts[1] == "lexTokenTuples":
                stats["unique_tuples"] = int(parts[2])
                stats["total_tuple_count"] = int(parts[3])
                stats["unique_var_tuples"] = int(parts[4])
                stats["total_var_tuple_count"] = int(parts[5])
            elif parts[1] == "subExprDoc":
                stats["sub_expr_docs"] = int(parts[2])

            # numbers per query ...
            elif parts[1] == "qt":
                per_query[current_query]["time"] = float(parts[2])
                per_query[current_query]["count_results"] = query_count
            elif parts[1] == "post":
                per_query[current_query]["postings"] = int(parts[2])
            elif parts[1] == "postsk":
                per_query[current_query]["postings_skipped"] = int(parts[2])
            elif parts[1] == "expr":
                per_query[current_query]["expressions"] = int(parts[2])
            elif parts[1] == "exprsk":
                per_query[current_query]["expressions_skipped"] = int(parts[2])
            elif parts[1] == "doc":
                per_query[current_query]["documents"] = int(parts[2])

        elif line[0] == "Q":
            parts = line.split("\t")

            current_query = parts[1]
            per_query[current_query] = {key:-1 for key in query_keys}
            query_count = 0

        elif line[0] == "R":
            query_count += 1

    return stats, per_query

def window_from_filename(filename):
    start_w = -8
    while "0" <= filename[start_w - 1] <= "9":
        start_w -= 1

    window = filename[start_w:-7]

    if window == "0":
        window = "a"

    return window

def main():
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython compile_stats.py out_prefix [input_files]")
        print("")
        print("Where:")
        print("\tout_prefix\t: Prefix for files where summarized results will be stored")
        print("\tinput_files\t: Files to process")
        return

    output_prefix = sys.argv[1]

    all_stats = {"0" : {}, "1": {}}
    all_query_stats = {}

    for filename in sys.argv[2:]:
        current_stats, query_stats = process_file(filename)

        window = window_from_filename(filename)
        base_e = filename[-5:-4]

        all_stats[base_e][filename] = current_stats

        all_query_stats[filename] = (window, base_e, query_stats)

    # generate global stats files
    all_files_sorted = []
    for base_e in ["0", "1"]:

        out_file = open(output_prefix + "_global_e" + base_e + ".csv", "w")

        sorted_files = [x[1] for x in sorted([(window_from_filename(fname), fname) for fname in all_stats[base_e].keys()])]

        for idx, filename in enumerate(sorted_files):
            all_files_sorted.append(filename)

            if idx == 0:
                line = "filename,window"
                for stat in stat_keys:
                    line += "," + stat
                line += "\n"

                out_file.write(line)

            window = window_from_filename(filename)
            line = filename + "," + str(window)

            for stat in stat_keys:
                line += "," + str(all_stats[base_e][filename][stat])
            line += "\n"

            out_file.write(line)

        out_file.close()

    # check which queries are invalid ...
    invalid_queries = []
    query_names = {}
    for filename in all_query_stats:
        window, base_e, query_stats = all_query_stats[filename]
        for query_name in query_stats:
            query_names[query_name] = 0

            if query_stats[query_name]["count_results"] == 0:
                if query_name not in invalid_queries:
                    invalid_queries.append(query_name)


    print("Queries that will be excluded:" )
    print(invalid_queries)

    # index the query data for later output ...
    per_query_stats = {}
    for key in query_keys:
        per_query_stats[key] = {}

        header = "query"
        for filename in all_files_sorted:
            window, base_e, query_stats = all_query_stats[filename]

            condition = "w" + str(window) + "_e" + str(base_e)

            header += "," + ("b_w" if base_e == "1" else "w") + str(window)

            per_query_stats[key][condition] = {}

            for query_name in query_names:
                per_query_stats[key][condition][query_name] = query_stats[query_name][key]

        # generate per query stats files
        out_file = open(output_prefix + "_query_" + key + ".csv", "w")

        out_file.write(header + "\n")
        for query_name in query_names:
            line = query_name.strip()

            for filename in all_files_sorted:
                window, base_e, query_stats = all_query_stats[filename]

                condition = "w" + str(window) + "_e" + str(base_e)

                line += "," + str(per_query_stats[key][condition][query_name])

            out_file.write(line + "\n")


        out_file.close()



main()