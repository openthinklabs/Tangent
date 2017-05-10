
import sys


def get_tsv_results(filename):
    input_file = open(filename, 'r')
    all_lines = input_file.readlines()
    input_file.close()

    all_results = {}
    current_query = None
    current_query_results = []
    for line in all_lines:
        line = line.strip()

        parts = line.split("\t")

        if parts[0] == "Q":
            current_query = parts[1]
            current_query_results = []

            # This assumes the format "NTCIR11-Math-X"
            query_offset = int(current_query.split("-")[-1])

            all_results[query_offset] = {
                "offset"    : query_offset,
                "id"        : current_query,
                "results"   : current_query_results,
                "math_ids"  : [],
            }

        elif parts[0] == "R":
            doc = int(parts[1])
            loc = int(parts[2])
            slt = parts[3]

            current_query_results.append((doc, loc, slt))

    return all_results


def load_csv(input_filename):
    input_file = open(input_filename, "r")
    lines = input_file.readlines()
    input_file.close()

    results = {}
    current_query = None
    current_results = []
    for idx, line in enumerate(lines):
        if idx == 0:
            # assuming header, skip
            continue

        parts = line.strip().split(",")

        if len(parts) == 2:
            query_id = parts[0]
            formula_id = parts[1]

            if query_id != current_query:
                current_query = query_id
                current_results = []
                results[current_query] = current_results

            current_results.append(formula_id)

    return results


def load_gold_standard(filename):
    input_file = open(filename, "r")
    lines = input_file.readlines()
    input_file.close()

    ranks = {}
    for idx, line in enumerate(lines):
        if idx == 0:
            continue

        parts = line.strip().split("\t")

        slt = parts[0]
        ranks[slt] = {
            "rank" : parts[1],
            "group": parts[2],
        }

    return ranks


def find_ranks(csv_records, tsv_records, gold_prefix):
    sorted_queries = [str(x) for x in sorted([int(x) for x in csv_records])]

    final_results = {}
    for query_id in sorted_queries:
        print("Processing: " + query_id)
        current_tsv = tsv_records[int(query_id)]

        # load gold standard
        gold_std = load_gold_standard(gold_prefix + query_id + ".tsv")

        #print("Keys in GS: " + str(len(gold_std.keys())))

        current_results = []
        for idx, formula_id in enumerate(csv_records[query_id]):
            doc, loc, slt = current_tsv["results"][idx]

            if slt not in gold_std and "\\" in slt:
                slt = slt.replace("\\", "\\\\")
                if slt not in gold_std:
                    print("Not found: " + slt)

            rank = gold_std[slt]["rank"]
            group = gold_std[slt]["group"]

            current_results.append((formula_id, doc, loc, rank, group, slt))

        final_results[query_id] = current_results

    return final_results


def save_tsv(results, filename):
    sorted_queries = [str(x) for x in sorted([int(x) for x in results])]

    out_file = open(filename, "w")
    out_file.write("queryId\tformulaId\tdoc\tloc\trank\tgroup\tslt\n")
    for query_id in sorted_queries:
        for formula_id, doc, loc, rank, group, slt in results[query_id]:
            out_file.write(query_id + "\t" + str(formula_id) + "\t" + str(doc) + "\t" + str(loc) + "\t" +
                           str(rank) + "\t" + str(group) + "\t" + slt + "\n")

    out_file.close()


def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython extended_csv.py input_csv input_tsv gold_prefix output_csv")
        print("")
        print("Where:")
        print("\tinput_csv\t: Path to file with results in csv format")
        print("\tinput_tsv\t: Path to file with results in original format")
        print("\tgold_prefix\t: Prefix used for gold standard files")
        print("\toutput_tsv\t: Path to file where results will be stored")
        print("")
        return

    csv_filename = sys.argv[1]
    tsv_filename = sys.argv[2]
    gold_prefix = sys.argv[3]
    output_filename = sys.argv[4]

    print(csv_filename)
    print(tsv_filename)
    print(gold_prefix)
    print(output_filename)

    # load data ...
    print("Loading ")

    input_tsv = get_tsv_results(tsv_filename)
    input_csv = load_csv(csv_filename)

    # finding ranks ...
    print("Finding ranks")
    results = find_ranks(input_csv, input_tsv, gold_prefix)

    print("Saving file")
    save_tsv(results, output_filename)

    print("Finished!")




if __name__ == "__main__":
    main()
