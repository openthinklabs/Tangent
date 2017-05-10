import sys
import math

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

        if len(parts) == 3:
            if query_id != current_query:
                current_query = query_id
                current_results = {}
                results[current_query] = current_results

            formula_id = parts[1]
            relevance = float(parts[2])

            current_results[formula_id] = relevance

        if len(parts) == 7:
            if query_id != current_query:
                current_query = query_id
                current_results = []
                results[current_query] = current_results

            formula_id = parts[1]
            slt = parts[6]

            current_results.append((formula_id, slt))

    return results

def DCG(values, max_k):
    result = 0.0
    if len(values) > 0:
        result = values[0]

        for k in range(1, min(max_k, len(values))):
            result += values[k] / math.log(k + 1, 2)

    return result

def get_IDCG(human_rating, max_k):
    IDCG = {}
    for query_id in human_rating:
        values = sorted([human_rating[query_id][formula_id] for formula_id in human_rating[query_id]], reverse=True)
        IDCG[query_id] = DCG(values, max_k)

    return IDCG

def get_original_order(results, original, top_k, human_ratings):

    combined_order = {}
    for query_id in results:
        if query_id in human_ratings:
            # first, find the top_k elements on the current rank
            pos = 0

            current_top = []
            reranked_slts = {}
            while pos < len(results[query_id]) and len(current_top) < top_k:
                hit_formula_id, hit_slt = results[query_id][pos]
                if not hit_slt in reranked_slts:
                    reranked_slts[hit_slt] = 1
                else:
                    reranked_slts[hit_slt] += 1

                if hit_formula_id in human_ratings[query_id]:
                    current_top.append(hit_formula_id)
                pos += 1

            # now, find the same elements in the original rank
            original_top = []
            core_slts = {}
            pos = 0
            first_unseen = False
            max_p = 0
            while pos < len(original[query_id]) and len(original_top) < len(current_top):
                hit_formula_id, hit_slt = original[query_id][pos]

                if hit_formula_id in current_top:
                    original_top.append(hit_formula_id)

                if not hit_slt in core_slts:
                    core_slts[hit_slt] = 1
                    """
                    if len(core_slts) == top_k:
                        print(query_id + ", unseen: " + str(top_k - len(original_top)))
                    """
                else:
                    core_slts[hit_slt] += 1

                pos += 1

            #print(query_id + ": unique SLTs seen (reranker)\t:" + str(len(reranked_slts)))
            #print(query_id + ": unique SLTs seen (core)\t:" + str(len(core_slts)))
            """
            if len(reranked_slts) > 10:
                print(reranked_slts)
            """

            combined_order[query_id] = (current_top, original_top)


    return combined_order


def get_nDCGs(combined, human_ratings, IDCG, top_K):
    nDCGs = {}
    print("\tnDCG @ " + str(top_K))
    print("query\tcore\treranked")

    sorted_queries = [str(x) for x in sorted([int(x) for x in human_ratings])]
    for query_id in sorted_queries:
        core_values = [human_ratings[query_id][math_id] for math_id in combined[query_id][1]]
        reranked_values = [human_ratings[query_id][math_id] for math_id in combined[query_id][0]]

        core_nDCG = (DCG(core_values, len(core_values)) / IDCG[query_id]) * 100.0
        rerank_nDCG = (DCG(reranked_values, len(reranked_values)) / IDCG[query_id]) * 100.0


        print(query_id + "\t{0:.2f}\t{1:.2f}".format(core_nDCG, rerank_nDCG))

    return nDCGs

def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython nDCG_human.py core_tsv rerank_tsv human_rating")
        print("")
        print("Where:")
        print("\tcore_tsv\t: Path to File with core results in tsv format")
        print("\trerank_tsv\t: Path to File with reranked results in tsv format")
        print("\thuman_rating\t: Path to File with human ratings in csv format")
        print("\tcurrent_k\t: nDCG @ current_k")
        print("")
        return

    core_input_filename = sys.argv[1]
    rerank_input_filename = sys.argv[2]
    rating_filename = sys.argv[3]
    try:
        current_k = int(sys.argv[4])
    except:
        print("Invalid K value")
        return

    print(core_input_filename)
    print(rerank_input_filename)

    # load data ..
    core_records = load_csv(core_input_filename, "\t")
    rerank_records = load_csv(rerank_input_filename, "\t")
    human_rating = load_csv(rating_filename, ",")

    # get IDCG
    IDCG = get_IDCG(human_rating, current_k)

    # get top-10 in original order (order by core)
    combined = get_original_order(rerank_records, core_records, current_k, human_rating)

    # compute nDCG
    nDCGs = get_nDCGs(combined, human_rating, IDCG, current_k)

    #get_orders(records, human_rating)
    #query_id, nDCG


if __name__ == "__main__":
    main()