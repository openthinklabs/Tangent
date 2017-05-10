import sys
import math
import numpy as np

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

        if len(parts) == 7:
            formula_id = parts[1]
            #doc = parts[2]
            #loc = parts[3]
            #rank = parts[4]
            #group = parts[5]
            slt = parts[6]

            #current_results.append((formula_id, doc, loc, rank, group, slt))
            current_results.append(slt)

    return results


def filter_unique_slt(results, max_k):
    for query_id in results:
        query_slts = results[query_id]

        last_slt = query_slts[0]
        filtered = [last_slt]

        for pos in range(1, len(query_slts)):
            if query_slts[pos] != last_slt:
                last_slt = query_slts[pos]
                filtered.append(last_slt)

                if len(filtered) >= max_k:
                    break

        results[query_id] = filtered

    return results

def load_gold_standard(filename, max_k):
    input_file = open(filename, "r")
    lines = input_file.readlines()
    input_file.close()

    ranks = {}
    top_relevance = []
    for idx, line in enumerate(lines):
        if idx == 0:
            continue

        parts = line.strip().split("\t")

        #SLT	rank	group	score1	score2	score3

        slt = parts[0]
        mss = float(parts[3])

        ranks[slt] = mss

        if len(top_relevance) < max_k:
            top_relevance.append(mss)

    return ranks, top_relevance


def DCG(values, max_k):
    result = 0.0
    if len(values) > 0:
        result = values[0]

        for k in range(1, min(max_k, len(values))):
            result += values[k] / math.log(k + 1, 2)

    return result


def compute_nDCG(ranks, k_values, gold_std_prefix):
    nDCG = {k: {} for k in k_values}

    max_k = max(k_values)

    for query_id in ranks:
        # load ground truth ...
        gold_std, top_gold_mss = load_gold_standard(gold_std_prefix + query_id + ".tsv", max_k)

        # compute IDCGp
        IDCG = {k : DCG(top_gold_mss, k) for k in k_values}

        # obtain relevance values ...
        rel_values = []
        for pos in range(min(max_k, len(ranks[query_id]))):
            slt = ranks[query_id][pos]
            if slt not in gold_std and "\\" in slt:
                slt = slt.replace("\\", "\\\\")
                if slt not in gold_std:
                    print("Query " + query_id + ", Not found in Gold Standard: " + slt)
                    rel_values.append(0.0)
                    continue

            rel_values.append(gold_std[slt])

        # now, compute nDCGp
        for k in k_values:
            if k <= len(rel_values):
                nDCG[k][query_id] = DCG(rel_values, k) / IDCG[k]

    return nDCG

def show_nDCG(nDCG, condition):
    #sorted_k = [str(x) for x in sorted([int(x) for x in nDCG])]
    sorted_k = sorted(list(nDCG.keys()))

    row_str = condition + "\t{0:.2f}\t{1:.2f}\t{2}"
    for k in sorted_k:
        # convert values to NP matrix and then get AVG and STD
        values = [nDCG[k][query_id] for query_id in nDCG[k]]
        tempo = np.array(values)

        avg = tempo.mean() * 100.0
        std = tempo.std()  * 100.0

        print(row_str.format(avg, std, k))


def save_nDCG(nDCG, output_filename):
    out_file = open(output_filename, "w")
    out_file.write("queryId\tk\tnDCG\n")

    for k in nDCG:
        for query_id in nDCG[k]:
            out_file.write(query_id + "\t" + str(k) + "\t" + str(nDCG[k][query_id]) + "\n")

    out_file.close()

def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython nDCG_metrics.py core_input gs_prefix output_dist K_values")
        print("")
        print("Where:")
        print("\tcore_input\t: Path to File with core results in tsv format")
        print("\tgs_prefix\t: Prefix for gold standard files")
        print("\toutput_dist\t: File where the raw nDCG values will be stored")
        print("\tK_values\t: Maximum rank values to consider, use 0 for Infinite")
        print("")
        return

    core_filename = sys.argv[1]
    gold_prefix = sys.argv[2]
    output_filename = sys.argv[3]

    condition = core_filename.split("/")[-1]

    #print("------------ Metrics for ----------")
    #print("File: " + condition)

    K_values = []
    for arg_val in sys.argv[4:]:
        try:
            K_values.append(int(arg_val))
        except:
            print("Invalid K value: " + arg_val)
            return

    K_values = sorted(K_values)

    max_K = K_values[-1]

    # load input ...
    records = load_csv(core_filename, "\t")

    records = filter_unique_slt(records, max_K)

    results = compute_nDCG(records, K_values, gold_prefix)

    # show results ...
    show_nDCG(results, condition)

    # save results ...
    save_nDCG(results, output_filename)


if __name__ == "__main__":
    main()