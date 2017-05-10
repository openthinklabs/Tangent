
import sys

def load_csv(input_filename, delimiter):
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

        query_id = parts[0]

        if query_id != current_query:
            current_query = query_id
            current_results = []
            results[current_query] = current_results

        if len(parts) == 2:
            group = parts[1]

            current_results.append(group)

    return results

def filter_records(records, truth, verbose=False):
    results = {}
    for query_id in records:
        # getting the document where target is located ....
        doc_id = truth[query_id][0].strip().split(".")[1]

        if verbose:
            print("Query: " + str(query_id) + ", Target Doc: " + str(doc_id))

        docs_order = []
        docs_dict = {}
        for formula_id in records[query_id]:
            original_doc = formula_id.split(".")[1]

            # only add each document first time seen ...
            if original_doc not in docs_dict:
                docs_dict[original_doc] = True
                docs_order.append(formula_id)

        if verbose:
            print("Original size: " + str(len(records[query_id])) + ", new size: " + str(len(docs_order)))

        results[query_id] = docs_order

    return results


def get_mrr(rankings, max_rank):
    total_rr = 0.0
    total_success = 0
    failures = []

    for idx, rank in enumerate(rankings):
        if (max_rank == 0 or rank <= max_rank) and rank > 0.0:
            total_rr += 1.0 / rank
            total_success += 1
        else:
            failures.append(idx)

    if len(rankings) > 0:
        mrr = (total_rr / float(len(rankings))) * 100
        success = (total_success / float(len(rankings))) * 100
    else:
        mrr = 0.0
        success = 0.0

    if total_success > 0:
        smrr = (total_rr / float(total_success)) * 100
    else:
        smrr = 0.0

    return success, mrr, smrr, failures

def show_results_table(table_stats, title, topic_names):
    print("=======")
    print(title)

    per_topic = "\tS\tMRR" * len(topic_names)

    print("\t" + "\t\t".join(topic_names))
    print("K" + per_topic)

    for k in sorted(table_stats.keys()):
        current_line = str(k)

        for topic in topic_names:
            stat = table_stats[k][topic]

            current_line += "\t{0:.2f}\t{1:.2f}".format(stat["succ"], stat["mrr"])

        print(current_line)


def show_results_compact_format(table_page, table_formula, topic_names, minimal):
    print("=======")

    per_topic = "\t".join(topic_names)

    k_values = sorted(table_page.keys())

    if not minimal:
        print("\tRecall\t\t\t\t\t\tMRR")
        print("\tDocument-Centric\tFormula-Centric\t\tDocument-Centric\tFormula-Centric")
        print("K\t" + "\t".join([per_topic] * 4))

    for k in k_values:
        current_line = str(k)

        page_recall = ""
        form_recall = ""

        page_mrr = ""
        form_mrr = ""

        for topic in topic_names:
            stat_page = table_page[k][topic]
            stat_form = table_formula[k][topic]

            page_recall += "\t{0:.2f}".format(stat_page["succ"])
            form_recall += "\t{0:.2f}".format(stat_form["succ"])

            page_mrr += "\t{0:.2f}".format(stat_page["mrr"])
            form_mrr += "\t{0:.2f}".format(stat_form["mrr"])

        current_line += page_recall + form_recall + page_mrr + form_mrr

        print(current_line)


def compute_ranks(records, truth, topics):
    ranks = {}
    sorted_keys = [str(x) for x in sorted([int(x) for x in truth])]
    queries_by_group = {}

    for query_id in sorted_keys:
        # Ground Truth info
        target_id = truth[query_id][0]
        target_doc = target_id.split(".")[1]
        current_group = topics[query_id][0]

        if not current_group in queries_by_group:
            queries_by_group[current_group] = [query_id]
        else:
            queries_by_group[current_group].append(query_id)

        if not current_group in ranks:
            ranks[current_group] = {
                "formula_success" : [],
                "formula_r" : [],
                "page_success" : [],
                "page_r" : [],
                "count" : 1,
            }
        else:
            ranks[current_group]["count"] += 1

        first_doc = None
        formula_pos = None

        if query_id in records:
            for idx, formula_id in enumerate(records[query_id]):
                current_doc = formula_id.split(".")[1]

                # page-centric ....
                if first_doc is None and current_doc == target_doc:
                    first_doc = idx

                # formula-centric ....
                if formula_id == target_id:
                    formula_pos = idx

                if (first_doc is not None) and (formula_pos is not None):
                    break

        if first_doc is not None:
            #if first_doc + 1.0 > 100.0 or query_id == "87":
            #    print("Above 100: " + str(query_id) + ", " + str(first_doc + 1.0))
            ranks[current_group]["page_r"].append(first_doc + 1.0)
            ranks[current_group]["page_success"].append(query_id)

        else:
            ranks[current_group]["page_r"].append(0.0)
            #print("PAge failure")
            #print(query_id)

        if formula_pos is not None:
            ranks[current_group]["formula_r"].append(formula_pos + 1.0)
            ranks[current_group]["formula_success"].append(query_id)
        else:
            #print("Formula failure")
            #print(query_id)
            ranks[current_group]["formula_r"].append(0.0)

        #print(query_id + ", " + str(first_doc) + ", " + str(formula_pos))

    return ranks, queries_by_group

def main():
    if len(sys.argv) < 6:
        print("Usage")
        print("\tpython ntcir_metrics_from_math_ids.py results ground_truth topic_groups minimal [K_values]")
        print("")
        print("Where:")
        print("\tresults\t\t: Path to unfiltered csv files (using mathids only)")
        print("\tground_truth\t: Path to File with ground truth in csv format")
        print("\ttopic_groups\t: Path to file with topic groups")
        print("\tminimal\t\t: Produce minimal output")
        print("\tK_values\t: Maximum rank values to consider, use 0 for Infinite")
        print("")
        return

    # compute here the filtered records ...
    raw_results_filename = sys.argv[1]
    truth_filename = sys.argv[2]
    topic_filename = sys.argv[3]

    try:
        minimal = int(sys.argv[4])
        minimal = minimal > 0
    except:
        print("Invalid value for minimal output")
        return

    K_values = []
    for arg_val in sys.argv[5:]:
        try:
            K_values.append(int(arg_val))
        except:
            print("Invalid K value: " + arg_val)
            return



    # ground truth
    truth = load_csv(truth_filename, ",")
    topics = load_csv(topic_filename, ",")

    #topic_names = ["All", "E", "F", "V", "H"]
    topic_names = ["All", "Conc", "Var"]

    print("Unfiltered Results: " + raw_results_filename)

    if not minimal:
        print("K values: " + str(K_values))

    raw_results = load_csv(raw_results_filename, ",")
    filtered_results = filter_records(raw_results, truth)

    # Page-Centric evaluation
    # Find specific target formula on target document
    # Find exact matching formula on target document (not here)
    tables = ["page", "target"]

    final_stats = {}

    # assuming only one (unknown condition)
    final_stats = {
        table: {
            k: {
                topic: {"mrr": 0.0, "succ": 0.0} for topic in topic_names
            }
            for k in K_values
        }
        for table in tables
    }

    # compute statistics using files
    # first, unfiltered for exact and target
    ranks, queries_by_group = compute_ranks(raw_results, truth, topics)

    for k in K_values:
        formula_total_rr = []
        sorted_queries = []

        for group in ranks:
            formula_total_rr += ranks[group]["formula_r"]
            sorted_queries += queries_by_group[group]

            formula_success, formula_mrr, formula_smrr, failures = get_mrr(ranks[group]["formula_r"], k)

            final_stats["target"][k][group]["succ"] = formula_success
            final_stats["target"][k][group]["mrr"] = formula_mrr
            final_stats["target"][k][group]["smrr"] = formula_smrr


        formula_success, formula_mrr, formula_smrr, failures = get_mrr(formula_total_rr, k)
        if not minimal:
            print("Formula-based Failures at K = " + str(k) + ":\t" + str(sorted([sorted_queries[idx] for idx in failures])))

        final_stats["target"][k]["All"]["succ"] = formula_success
        final_stats["target"][k]["All"]["mrr"] = formula_mrr
        final_stats["target"][k]["All"]["smrr"] = formula_smrr

    # second, filtered for page-centric
    ranks, queries_by_group = compute_ranks(filtered_results, truth, topics)

    for k in K_values:
        page_total_rr = []
        sorted_queries = []

        for group in ranks:
            page_total_rr += ranks[group]["page_r"]
            sorted_queries += queries_by_group[group]

            page_success, page_mrr, page_smrr, failures = get_mrr(ranks[group]["page_r"], k)

            final_stats["page"][k][group]["succ"] = page_success
            final_stats["page"][k][group]["mrr"] = page_mrr
            final_stats["page"][k][group]["smrr"] = page_smrr

        page_success, page_mrr, page_smrr, failures = get_mrr(page_total_rr, k)
        if not minimal:
            print("Pased-based Failures at K = " + str(k) + ":\t" + str(sorted([sorted_queries[idx] for idx in failures])))

        final_stats["page"][k]["All"]["succ"] = page_success
        final_stats["page"][k]["All"]["mrr"] = page_mrr
        final_stats["page"][k]["All"]["smrr"] = page_smrr


    # show result tables
    #show_results_table(final_stats["page"], "Page-Centric: Target Document found", topic_names)
    #show_results_table(final_stats["target"], "Formula-Centric: Target Formula found", topic_names)

    show_results_compact_format(final_stats["page"], final_stats["target"], topic_names, minimal)


if __name__ == "__main__":
    main()

