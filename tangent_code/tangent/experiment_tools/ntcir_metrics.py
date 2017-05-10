
import sys

verbose = False

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


        if len(parts) == 3:
            formula_id = parts[1]
            slt = parts[2]

            current_results.append((formula_id, slt))

        if len(parts) == 7:
            formula_id = parts[1]
            doc = parts[2]
            loc = parts[3]
            rank = int(parts[4])
            group = int(parts[5])
            slt = parts[6]

            current_results.append((formula_id, doc, loc, rank, group, slt))

    return results


def compute_ranks(records, truth, topics):

    ranks = {}
    sorted_keys = [str(x) for x in sorted([int(x) for x in truth])]

    for query_id in sorted_keys:

        target_id, target_slt = truth[query_id][0]
        target_doc = target_id.split(".")[1]

        current_group = topics[query_id][0]

        if not current_group in ranks:
            ranks[current_group] = {
                "formula_success" : [],
                "formula_r" : [],
                "formula_mss_rank" : [],
                "formula_mss_group" : [],
                "page_success" : [],
                "page_r" : [],
                "slt_r" : [],
                "slt_page_r" : [],
                "count" : 1,
            }
        else:
            ranks[current_group]["count"] += 1

        first_doc = None
        first_slt = None
        formula_pos = None
        doc_slt_pos = None
        formula_mss_rank = None
        formula_mss_group = None

        if query_id in records:
            for idx, res_data in enumerate(records[query_id]):
                formula_id, doc, loc, rank, group, slt = res_data

                current_doc = formula_id.split(".")[1]

                # page-centric ....
                if first_doc is None and current_doc == target_doc:
                    first_doc = idx

                if doc_slt_pos is None and current_doc == target_doc and target_slt == slt:
                    doc_slt_pos = idx

                # formula-centric ....
                if formula_id == target_id:
                    formula_pos = idx
                    formula_mss_rank = rank
                    formula_mss_group = group

                # slt-centric
                if first_slt is None and target_slt == slt:
                    first_slt = idx

                if ((first_doc is not None) and (formula_pos is not None) and
                    (first_slt is not None) and (doc_slt_pos is not None)):
                    break

        if first_doc is not None:
            if first_doc + 1.0 > 100.0 or query_id == "87":
                print("Above 100: " + str(query_id) + ", " + str(first_doc + 1.0))
            ranks[current_group]["page_r"].append(first_doc + 1.0)
            ranks[current_group]["page_success"].append(query_id)

        else:
            ranks[current_group]["page_r"].append(0.0)

        if formula_pos is not None:
            if formula_pos > 0 and current_group == "E":
                print(query_id)
            ranks[current_group]["formula_r"].append(formula_pos + 1.0)
            ranks[current_group]["formula_success"].append(query_id)
            ranks[current_group]["formula_mss_rank"].append(formula_mss_rank)
            ranks[current_group]["formula_mss_group"].append(formula_mss_group)
        else:
            print("failed: " + query_id + ": " + target_slt)
            ranks[current_group]["formula_r"].append(0.0)
            ranks[current_group]["formula_mss_rank"].append(0.0)
            ranks[current_group]["formula_mss_group"].append(0.0)

        if first_slt is not None:
            ranks[current_group]["slt_r"].append(first_slt + 1.0)
        else:
            #print("failed: " + query_id + ": " + target_slt)
            ranks[current_group]["slt_r"].append(0.0)

        if doc_slt_pos is not None:
            ranks[current_group]["slt_page_r"].append(doc_slt_pos + 1.0)
        else:
            #print("failed: " + query_id + ": " + target_slt)
            ranks[current_group]["slt_page_r"].append(0.0)

        #print(query_id + ", " + str(first_doc) + ", " + str(formula_pos))

    return  ranks


def get_mrr(rankings, max_rank):
    total_rr = 0.0
    total_success = 0

    for rank in rankings:
        if (max_rank == 0 or rank <= max_rank) and rank > 0.0:
            total_rr += 1.0 / rank
            total_success += 1

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

    return success, mrr, smrr


def show_ranks(ranks, k, filter_topic):
    page_total_rr = []
    formula_total_rr = []
    formula_total_mss_rank = []
    formula_total_mss_group = []
    slt_total_rr = []
    slt_page_total_rr = []

    rank_name = str(k) if k > 0 else "Inf"

    row_str = "{0}:\t{1:.2f}\t{2:.2f}\t{3:.2f}\t{4:.2f}\t{5:.2f}\t{6:.2f}\t{7:.2f}\t{8:.2f}\t{9:.2f}\t{10:.2f}\t" + rank_name

    sorted_groups = sorted(list(ranks.keys()))

    for group in sorted_groups:
        page_total_rr += ranks[group]["page_r"]
        formula_total_rr += ranks[group]["formula_r"]
        formula_total_mss_rank += ranks[group]["formula_mss_rank"]
        formula_total_mss_group += ranks[group]["formula_mss_group"]
        slt_total_rr += ranks[group]["slt_r"]
        slt_page_total_rr += ranks[group]["slt_page_r"]

        if filter_topic != "0" and filter_topic != group:
            continue

        page_success, page_mrr, page_smrr = get_mrr(ranks[group]["page_r"], k)
        formula_success, formula_mrr, formula_smrr = get_mrr(ranks[group]["formula_r"], k)

        gs_succ, mss_mrr, mss_rank_smrr = get_mrr(ranks[group]["formula_mss_rank"], k)
        gs_succ, mss_mrr, mss_group_smrr = get_mrr(ranks[group]["formula_mss_group"], k)

        slt_succ, slt_mrr, slt_smrr = get_mrr(ranks[group]["slt_r"], k)

        slt_page_succ, slt_page_mrr, slt_page_smrrr = get_mrr(ranks[group]["slt_page_r"], k)

        print(row_str.format(group, page_success, page_smrr, formula_success, formula_smrr,
                             mss_rank_smrr, mss_group_smrr, slt_succ, slt_smrr, slt_page_succ, slt_page_smrrr))

    if filter_topic == "0" or filter_topic == "All":

        all_page_success, all_page_mrr, all_page_smrr = get_mrr(page_total_rr, k)
        all_formula_success, all_formula_mrr, all_formula_smrr = get_mrr(formula_total_rr, k)

        gs_succ, mss_mrr, mss_rank_smrr = get_mrr(formula_total_mss_rank, k)
        gs_succ, mss_mrr, mss_group_smrr = get_mrr(formula_total_mss_group, k)

        slt_succ, slt_mrr, slt_smrr = get_mrr(slt_total_rr, k)
        slt_page_succ, slt_page_mrr, slt_page_smrrr = get_mrr(slt_page_total_rr, k)

        print(row_str.format("All", all_page_success, all_page_smrr, all_formula_success, all_formula_smrr,
                             mss_rank_smrr, mss_group_smrr, slt_succ, slt_smrr, slt_page_succ, slt_page_smrrr))



def main():
    if len(sys.argv) < 6:
        print("Usage")
        print("\tpython ntcir_metrics.py input ground_truth topic_groups group [K_values]")
        print("")
        print("Where:")
        print("\tinput\t\t: Path to File with results in tsv format")
        print("\tground_truth\t: Path to File with ground truth in tsv format")
        print("\ttopic_groups\t: Path to file with topic groups")
        print("\ttopic\t\t: Show only topics of this groups. Use 0 for all topics.")
        print("\tK_values\t: Maximum rank values to consider, use 0 for Infinite")
        print("")
        return

    input_filename = sys.argv[1]
    truth_filename = sys.argv[2]
    topic_filename = sys.argv[3]

    filter_topic = sys.argv[4]

    K_values = []
    for arg_val in sys.argv[5:]:
        try:
            K_values.append(int(arg_val))
        except:
            print("Invalid K value: " + arg_val)
            return

    print("------------ Metrics for ----------")
    print("File: " + input_filename)

    #print("Loading input ...")
    records = load_csv(input_filename, "\t")

    #print("Loading Ground Truth ...")
    truth = load_csv(truth_filename, "\t")

    topics = load_csv(topic_filename, ",")

    #print("Computing rankings ...")
    ranks = compute_ranks(records, truth, topics)

    if verbose:
        print("Page-Centric")
        for group in ranks:
            count = sum([1 for x in ranks[group]["page_r"] if x > 0.0])
            print("Group: " + group + " (Success at K=Inf: " + str(count) + " of " + str(ranks[group]["count"]) + ")")
            print("Idx\tRank")
            for x in range(len(ranks[group]["page_r"])):
                print(str(x + 1) + "\t" + str(ranks[group]["page_r"][x]))

        print("Formula-Centric")
        for group in ranks:
            count = sum([1 for x in ranks[group]["formula_r"] if x > 0.0])
            print("Group: " + group + " (Success at K=Inf: " + str(count) + " of " + str(ranks[group]["count"]) + ")")
            print("Idx\tRank\tGS Rank\tGS Group")
            for x in range(len(ranks[group]["formula_r"])):
                if ranks[group]["formula_r"][x] > 0.0:
                    print(str(x + 1) + "\t" + str(ranks[group]["formula_r"][x]) + "\t" +
                          str(ranks[group]["formula_mss_rank"][x]) + "\t" + str(ranks[group]["formula_mss_group"][x]))
                else:
                    print(str(x + 1) + "\tFailure, exact id not found")

    # now, output ranks
    print("\tPage-centric\tFormula-centric\tGold Standard\tSLT-centric\tSLT-Page")
    print("Group\tSucc\tS MRR\tSucc\tS MRR\tS Rank\tS Group\tSucc\tS MRR\tSucc\tS MRR\tK")
    for k_value in K_values:
        show_ranks(ranks, k_value, filter_topic)

    #print("Finished")

if __name__ == "__main__":
    main()
