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

def condition_to_graph_title(condition):
    parts = condition.split("_")

    e = None
    w = None
    for part in parts:
        if part[0] == "e":
            e = part[1:]
        if part[0] == "w":
            w = part[1:]

    if e == "1":
        e_prefix = "e_"
    elif e == "2":
        e_prefix = "s_"
    else:
        e_prefix = ""

    return e_prefix + "w" + w

def main():
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython split_times.py  compiled_times")
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

    parts = lines[0].strip().split(",")


    if parts[0] == "w" and parts[1] == "e":
        split_condition = False
        start_queries = 2
    else:
        split_condition = True
        start_queries = 1

    # assume index time comes after condition/Window-EOB
    if output_index_filename is not None:
        start_queries += 1

    query_names = parts[start_queries:]

    print("Queries found: ")
    print(query_names)

    indexing_times = {}
    indexing_counts = {}

    query_times = {query: {} for query in query_names}
    query_valid = [True for query in query_names]

    all_conditions = []

    max_e = 2
    for line in lines[1:]:
        parts = line.strip().split(",")

        if split_condition:
            # get the two values from a single field
            cond_parts = parts[0].split("_")

            window = -1
            e_base = -1
            for c_part in cond_parts:
                if c_part[0] == "w":
                    window = int(c_part[1:])
                if c_part[0] == "e":
                    e_base = int(c_part[1:])

        else:
            window = int(parts[0])
            e_base = int(parts[1])

        if window == 0:
            window = "a"

        if e_base > max_e:
            max_e = e_base

        # indexing time ....
        if output_index_filename is not None:
            # indexing ....
            q_time = float(parts[start_queries - 1])

            if window not in indexing_times:
                indexing_times[window] = {e_value: 0.0 for e_value in range(max_e + 1)}
                indexing_counts[window] = {e_value: 0 for e_value in range(max_e + 1)}

            indexing_times[window][e_base] += q_time
            indexing_counts[window][e_base] += 1

        # queries ...
        if output_query_filename is not None:
            condition = "e" + str(e_base) + "_w" + str(window)
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
        tempo_windows = []
        all_pairs = False
        for key in indexing_times:
            if key != "a":
                tempo_windows.append(key)
            else:
                all_pairs = True

        windows = sorted(tempo_windows)
        if all_pairs:
            windows.append("a")

        out_file = open(output_index_filename, "w")
        header = "window," + ",".join(["e_" + str(e) for e in range(max_e + 1)])
        out_file.write(header + "\n")
        for window in windows:
            line = str(window)
            for e in range(max_e + 1):
                if indexing_counts[window][e] > 0:
                    indexing_times[window][e] /= float(indexing_counts[window][e])

                line += "," + str(indexing_times[window][e])
            line += "\n"

            out_file.write(line)
        out_file.close()

    # then, output times per query
    if output_query_filename is not None:
        all_conditions = sorted(all_conditions)

        out_file = open(output_query_filename, "w")
        header = "query," + ",".join([condition_to_graph_title(cond) for cond in all_conditions]) + "\n"
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