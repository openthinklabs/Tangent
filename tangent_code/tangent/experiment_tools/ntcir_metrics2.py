
import os
import sys


def get_conditions(raw_filenames):
    all_eob = []
    all_windows = []

    for input_file in raw_filenames:
        eob = None
        window = None

        parts = input_file.split(".")[0].split("_")
        for part in parts:
            if part[0] == "e":
                eob = int(part[1:])

            if part[0] == "w":
                window = int(part[1:])

        if eob is None or window is None:
            raise Exception("Could not identify EOB or Windows size for file: " + input_file)

        if eob not in all_eob:
            all_eob.append(eob)

        if window not in all_windows:
            all_windows.append(window)

    all_windows = sorted(all_windows)
    all_eob = sorted(all_eob)

    return all_eob, all_windows


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
            #if first_doc + 1.0 > 100.0 or query_id == "87":
            #    print("Above 100: " + str(query_id) + ", " + str(first_doc + 1.0))
            ranks[current_group]["page_r"].append(first_doc + 1.0)
            ranks[current_group]["page_success"].append(query_id)

        else:
            ranks[current_group]["page_r"].append(0.0)

        if formula_pos is not None:
            ranks[current_group]["formula_r"].append(formula_pos + 1.0)
            ranks[current_group]["formula_success"].append(query_id)
            ranks[current_group]["formula_mss_rank"].append(formula_mss_rank)
            ranks[current_group]["formula_mss_group"].append(formula_mss_group)
        else:
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
            ranks[current_group]["slt_page_r"].append(0.0)

        #print(query_id + ", " + str(first_doc) + ", " + str(formula_pos))

    return  ranks

def show_results_table(table_stats, title, topic_names):
    print("=======")
    print(title)

    per_topic = "\tS\tMRR" * len(topic_names)

    print("\t\t\t" + "\t\t".join(topic_names))
    print("K\tEOB\tWindow" + per_topic)

    for k in sorted(table_stats.keys()):
        for eob in sorted(table_stats[k]):
            for window in sorted(table_stats[k][eob]):
                current_line = str(k) + "\t" + str(eob) + "\t" + str(window)

                for topic in topic_names:
                    stat = table_stats[k][eob][window][topic]

                    current_line += "\t{0:.2f}\t{1:.2f}".format(stat["succ"], stat["mrr"])

                print(current_line)

def main():
    if len(sys.argv) < 6:
        print("Usage")
        print("\tpython ntcir_metrics2.py unfiltered_dir filtered_dir ground_truth topic_groups [K_values]")
        print("")
        print("Where:")
        print("\tunfiltered_dir\t: Path to unfiltered tsv files (all raw entries)")
        print("\tfiltered_dir\t: Path to filtered tsv files (one entry per document)")
        print("\tground_truth\t: Path to File with ground truth in tsv format")
        print("\ttopic_groups\t: Path to file with topic groups")
        print("\tK_values\t: Maximum rank values to consider, use 0 for Infinite")
        print("")
        return

    raw_input_directory = sys.argv[1]
    filt_input_directory = sys.argv[2]
    truth_filename = sys.argv[3]
    topic_filename = sys.argv[4]

    K_values = []
    for arg_val in sys.argv[5:]:
        try:
            K_values.append(int(arg_val))
        except:
            print("Invalid K value: " + arg_val)
            return

    raw_filenames = os.listdir(raw_input_directory)
    filt_filenames = os.listdir(filt_input_directory)

    # ground truth
    truth = load_csv(truth_filename, "\t")
    topics = load_csv(topic_filename, ",")

    topic_names = ["All", "E", "F", "V", "H"]

    print("Unfiltered Directory: " + raw_input_directory)
    print("Filtered Directory:" + filt_input_directory)
    print("K values: " + str(K_values))

    all_eob, all_windows = get_conditions(raw_filenames)

    print("EOB found: " + str(all_eob))
    print("Windows found: " + str(all_windows))

    # Page-Centric evaluation
    # Find specific target formula on target document
    # Find exact matching formula on target document
    tables = ["page", "target", "exact"]
    final_stats = {}


    final_stats = {
        table: {
            k: {
                eob: {
                    window: {
                        topic: {"mrr": 0.0, "succ": 0.0} for topic in topic_names
                    }
                    for window in all_windows
                }
                for eob in all_eob
            }
            for k in K_values
        }
        for table in tables
    }

    # compute statistics using files
    # first, unfiltered for exact and target
    for input_file in raw_filenames:
        eob = None
        window = None

        parts = input_file.split(".")[0].split("_")
        for part in parts:
            if part[0] == "e":
                eob = int(part[1:])

            if part[0] == "w":
                window = int(part[1:])

        if eob is None or window is None:
            print("Invalid file: " + input_file)
            continue

        records = load_csv(raw_input_directory + "/" + input_file, "\t")
        ranks = compute_ranks(records, truth, topics)

        for k in K_values:
            formula_total_rr = []
            slt_page_total_rr = []

            for group in ranks:
                formula_total_rr += ranks[group]["formula_r"]
                slt_page_total_rr += ranks[group]["slt_page_r"]

                formula_success, formula_mrr, formula_smrr = get_mrr(ranks[group]["formula_r"], k)
                slt_page_succ, slt_page_mrr, slt_page_smrrr = get_mrr(ranks[group]["slt_page_r"], k)

                final_stats["target"][k][eob][window][group]["succ"] = formula_success
                final_stats["target"][k][eob][window][group]["mrr"] = formula_smrr
                final_stats["exact"][k][eob][window][group]["succ"] = slt_page_succ
                final_stats["exact"][k][eob][window][group]["mrr"] = slt_page_smrrr

            #if eob == 1 and window == 0:
            #    print(input_file)
            #    print(formula_total_rr)


            formula_success, formula_mrr, formula_smrr = get_mrr(formula_total_rr, k)
            slt_page_succ, slt_page_mrr, slt_page_smrrr = get_mrr(slt_page_total_rr, k)

            final_stats["target"][k][eob][window]["All"]["succ"] = formula_success
            final_stats["target"][k][eob][window]["All"]["mrr"] = formula_smrr
            final_stats["exact"][k][eob][window]["All"]["succ"] = slt_page_succ
            final_stats["exact"][k][eob][window]["All"]["mrr"] = slt_page_smrrr

    # second, filtered for page-centric
    for input_file in filt_filenames:
        eob = None
        window = None

        parts = input_file.split(".")[0].split("_")
        for part in parts:
            if part[0] == "e":
                eob = int(part[1:])

            if part[0] == "w":
                window = int(part[1:])

        if eob is None or window is None:
            print("Invalid file: " + input_file)
            continue

        records = load_csv(raw_input_directory + "/" + input_file, "\t")
        ranks = compute_ranks(records, truth, topics)

        for k in K_values:
            page_total_rr = []

            for group in ranks:
                page_total_rr += ranks[group]["page_r"]

                page_success, page_mrr, page_smrr = get_mrr(ranks[group]["page_r"], k)

                final_stats["page"][k][eob][window][group]["succ"] = page_success
                final_stats["page"][k][eob][window][group]["mrr"] = page_smrr

            page_success, page_mrr, page_smrr = get_mrr(page_total_rr, k)

            final_stats["page"][k][eob][window]["All"]["succ"] = page_success
            final_stats["page"][k][eob][window]["All"]["mrr"] = page_smrr


    # show result tables
    show_results_table(final_stats["page"], "Page-Centric: Target Document found", topic_names)
    show_results_table(final_stats["target"], "Formula-Centric: Target Formula found", topic_names)
    show_results_table(final_stats["exact"], "SLT-Page-Centric: Target SLT on Target Document found", topic_names)


if __name__ == "__main__":
    main()
