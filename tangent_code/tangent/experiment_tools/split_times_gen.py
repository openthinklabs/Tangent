__author__ = 'mauricio'

import sys

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
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython split_times_gen.py  compiled_times")
        print("")
        print("Where:")
        print("\tcompiled_times\t: File where times have been compiled")
        print("")
        print("Optional:")
        print("\t-i\tout_index_times\t: File to store indexing times averages")
        print("\t-q\tout_query_times\t: File to store raw query times")
        return

    input_filename = sys.argv[1]

    params = optional_parameters(sys.argv[2:])

    if "i" in params:
        output_index_filename = params["i"]
    else:
        output_index_filename = None

    if "q" in params:
        output_query_filename = params["q"]
    else:
        output_query_filename = None

    input_file = open(input_filename, "r")
    lines  = input_file.readlines()
    input_file.close()

    # assume index time comes after condition
    start_queries = 1
    if output_index_filename is not None:
        start_queries += 1

    parts = lines[0].strip().split(",")
    query_names = parts[start_queries:]

    print("Queries found: ")
    print(query_names)

    indexing_times = {}
    indexing_counts = {}

    query_times = {query: {} for query in query_names}
    query_valid = [True for query in query_names]

    all_conditions = []

    for line in lines[1:]:
        parts = line.strip().split(",")

        condition = parts[0]

        # indexing time ....
        if output_index_filename is not None:
            # indexing ....
            q_time = float(parts[start_queries - 1])

            if condition not in indexing_times:
                indexing_times[condition] = 0.0
                indexing_counts[condition] = 0.0

            indexing_times[condition] += q_time
            indexing_counts[condition] += 1

        # queries ...
        if output_query_filename is not None:
            if condition not in all_conditions:
                all_conditions.append(condition)

            for x in range(start_queries, len(parts)):
                time = float(parts[x])
                if time < 0.0:
                    query_valid[x - start_queries] = False

                current_query = query_names[x - start_queries]

                if condition not in query_times[current_query]:
                    query_times[current_query][condition] = []

                query_times[current_query][condition].append(time)

    # first output (index times)
    if output_index_filename is not None:
        # ... sort window sizes considering that w=0 becomes "a" (all) and goes last
        tempo_windows = [key for key in indexing_times]

        out_file = open(output_index_filename, "w")
        header = "condition"
        out_file.write(header + "\n")

        for condition in indexing_times:
            if indexing_counts[condition] > 0:
                indexing_times[condition] /= float(indexing_counts[condition])

            line += "," + str(indexing_times[condition]) + "\n"
            out_file.write(line)

        out_file.close()

    # then, output times per query
    if output_query_filename is not None:
        all_conditions = sorted(all_conditions)

        out_file = open(output_query_filename, "w")
        header = "query," + ",".join(all_conditions) + "\n"
        out_file.write(header)
        for query in query_times:
            if not query_valid[query_names.index(query)]:
                # skip this query...
                print("Skipping: " + query)
                continue

            # check lenghts per condition
            max_n = min([len(query_times[query][condition]) for condition in all_conditions])

            for n in range(max_n):
                line = query
                for condition in all_conditions:
                    line += "," + str(query_times[query][condition][n])
                line += "\n"

                out_file.write(line)

        out_file.close()

main()