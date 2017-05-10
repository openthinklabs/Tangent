
import sys


def load_csv(input_filename, delimiter=","):
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

        parts = line.strip().split(delimiter)

        if len(parts) == 2:
            query_id = parts[0]
            formula_id = parts[1]

            if query_id != current_query:
                current_query = query_id
                current_results = []
                results[current_query] = current_results

            current_results.append(formula_id)

        if len(parts) == 7:
            query_id = parts[0]
            formula_id = parts[1]
            doc = parts[2]
            loc = parts[3]
            rank = parts[4]
            group = parts[5]
            slt = parts[6]

            if query_id != current_query:
                current_query = query_id
                current_results = []
                results[current_query] = current_results

            current_results.append((formula_id, doc, loc, rank, group, slt))

    return results


def filter_records(records, truth):
    results = {}
    for query_id in records:
        # getting the document where target is located ....
        doc_id = truth[query_id][0].strip().split(".")[1]

        print("Query: " + str(query_id) + ", Doc: " + str(doc_id))

        docs_order = []
        docs_dict = {}
        for data in records[query_id]:
            formula_id, doc, loc, rank, group, slt = data
            original_doc = formula_id.split(".")[1]

            # only add each document first time seen ...
            if original_doc not in docs_dict:
                docs_dict[original_doc] = True
                docs_order.append(data)

        print("Original size: " + str(len(records[query_id])) + ", new size: " + str(len(docs_order)))

        results[query_id] = docs_order


    return results


def save_records(results, filename):
    sorted_queries = [str(x) for x in sorted([int(x) for x in results])]

    out_file = open(filename, "w")
    out_file.write("queryId\tformulaId\tdoc\tloc\trank\tgroup\tslt\n")
    for query_id in sorted_queries:
        for formula_id, doc, loc, rank, group, slt in results[query_id]:
            out_file.write(query_id + "\t" + str(formula_id) + "\t" + str(doc) + "\t" + str(loc) + "\t" +
                           str(rank) + "\t" + str(group) + "\t" + slt + "\n")

    out_file.close()


def main():
    if len(sys.argv) < 4:
        print("Usage")
        print("\tpython filter_csv.py input ground_truth output")
        print("")
        print("Where:")
        print("\tinput\t\t: Path to File with results in tsv format")
        print("\tground_truth\t: Path to File with ground truth in csv format")
        print("\toutput\t\t: Path  to file to store filtered tsv results")
        print("")
        return

    input_filename = sys.argv[1]
    truth_filename = sys.argv[2]
    output_filename = sys.argv[3]

    print("Loading input ...")
    records = load_csv(input_filename, "\t")

    print("Loading Ground Truth ...")
    truth = load_csv(truth_filename, ",")

    # now, do the filtering ...
    print("Filtering ... ")
    filtered = filter_records(records, truth)

    # save results ...
    save_records(filtered, output_filename)

    print("Finished!")


if __name__ == "__main__":
    main()
