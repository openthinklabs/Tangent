
import sys

def load_tsv(input_filename):
    input_file = open(input_filename, "r")
    lines = input_file.readlines()
    input_file.close()

    results = {}
    for idx, line in enumerate(lines):
        if idx == 0:
            # assuming header, skip
            continue

        parts = line.strip().split("\t")

        query_id = parts[0]
        k = parts[1]
        nDCG = float(parts[2])

        if k not in results:
            results[k] = {}

        results[k][query_id] = nDCG

    return results

def find_common_queries(results):
    queries_counts = {}

    # count number of times that each query appears for each k
    for condition in results:
        for k in results[condition]:
            if k not in queries_counts:
                queries_counts[k] = {}

            for query_id in results[condition][k]:
                if query_id in queries_counts[k]:
                    queries_counts[k][query_id] += 1
                else:
                    queries_counts[k][query_id] = 1

    # find maximum count per k and assume common are only the ones that appear that number of times (on all conditions)
    common_queries = {}
    for k in queries_counts:
        common_queries[k] = []

        # find max count ...
        max_count = 0
        for query_id in queries_counts[k]:
            if queries_counts[k][query_id] > max_count:
                max_count = queries_counts[k][query_id]

        # filter by max count ...
        for query_id in queries_counts[k]:
            if queries_counts[k][query_id] == max_count:
                common_queries[k].append(query_id)

    return common_queries


def create_summaries(results, common_queries, output_prefix):
    for k in common_queries:
        valid_conditions = []
        for condition in results:
            if k in results[condition]:
                parts = condition.split("_")
                e = int(parts[2][1:])
                w = parts[1][1:]
                if w == "0":
                    w = "a"

                condition_name = ("" if e == 0 else "e_") + "w" + w

                valid_conditions.append((e, w, condition, condition_name))

        valid_conditions = sorted(valid_conditions)
        names = []
        conditions = []
        for e, w, condition, condition_name in valid_conditions:
            names.append(condition_name)
            conditions.append(condition)

        header = "queryId," + ",".join(names) + "\n"

        output = open(output_prefix + "_" + str(k) + ".csv", "w")
        output.write(header)

        for query_id in common_queries[k]:
            line = query_id
            for condition in conditions:
                line += "," + str(results[condition][k][query_id])

            line += "\n"

            output.write(line)

        output.close()


def main():
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython nDCG_summarize.py output_prefix [inputs]")
        print("")
        print("Where:")
        print("\toutput_prefix\t: Prefix for summary files")
        print("\t[inputs]\t: List of input files")
        print("")
        return

    output_prefix = sys.argv[1]

    # reading raw inputs ...
    all_results = {}
    for input_filename in sys.argv[2:]:
        condition = input_filename.split("/")[-1]
        condition = condition[condition.find("_") + 1:-4]

        print("Processing: " + condition)

        all_results[condition] = load_tsv(input_filename)

    # find common queries ...
    common_queries = find_common_queries(all_results)

    print("Common queries found per K:")
    print([(k, len(common_queries[k])) for k in common_queries])

    create_summaries(all_results, common_queries, output_prefix)


if __name__ == "__main__":
    main()