
import sys
import csv
import math
import statistics

def load_human_ratings(compiled_filename, query_offset):
    # read all text ...
    input_file = open(compiled_filename, "r", newline='', encoding='utf-8')
    reader = csv.reader(input_file, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    all_text = [row for row in reader]
    input_file.close()

    # capture unique ratings ...
    unique_ratigs = {}
    # process all lines, discard header ...
    for parts in all_text[2:]:
        user_id = parts[0]
        query_id = int(parts[1]) - query_offset

        rating = int(parts[3])
        math_id = parts[6]

        if not query_id in unique_ratigs:
            unique_ratigs[query_id] = {}

        if not math_id in unique_ratigs[query_id]:
            unique_ratigs[query_id][math_id] = {}

        unique_ratigs[query_id][math_id][user_id] = rating

    total_queries = len(unique_ratigs)
    total_candidates = 0
    total_unique_ratings = 0
    for query_id in unique_ratigs:
        total_candidates += len(unique_ratigs[query_id])

        for math_id in unique_ratigs[query_id]:
            total_unique_ratings += len(unique_ratigs[query_id][math_id])

    print("Total queries found: " + str(total_queries))
    print("Total candidates found: " + str(total_candidates))
    print("Total Unique ratings found: " + str(total_unique_ratings))

    return unique_ratigs


def get_ideal_rankings(unique_ratings):
    candidate_ratings = {}
    ideal_rankings = {}
    for query_id in unique_ratings:
        #if query_id == 60:
        #    continue
        ranking = []
        candidate_ratings[query_id] = {}
        for math_id in unique_ratings[query_id]:
            # the average rating for candidate math_id
            ratings = unique_ratings[query_id][math_id].values()

            rating_avg = statistics.mean(ratings)
            rating_std = statistics.stdev(ratings)

            ranking.append((rating_avg, -rating_std, math_id))

            candidate_ratings[query_id][math_id] = rating_avg


        ranking = sorted(ranking, reverse=True)

        ideal_rankings[query_id] = ranking

    return ideal_rankings, candidate_ratings


def print_ideal_rankings(ideal_rankings):
    for query_id in ideal_rankings:
        print(query_id)
        for c_avg, c_std, c_id in ideal_rankings[query_id]:
            print(str(c_avg) + ", " + str(c_std) + " - " + str(c_id))


def get_max_k(ideal_rankings):
    return min([len(ideal_rankings[query_id]) for query_id in ideal_rankings])


def load_mathids(filename):
    # read all text ...
    input_file = open(filename, "r", newline='', encoding='utf-8')
    reader = csv.reader(input_file, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    all_text = [row for row in reader]
    input_file.close()

    query_mathids = {}
    for parts in all_text[2:]:
        query_id = int(parts[0])
        math_id = parts[1]

        if not query_id in query_mathids:
            query_mathids[query_id] = []

        query_mathids[query_id].append(math_id)

    return query_mathids


def filter_rated_candidates(condition_mathids, candidate_ratings):

    filtered_candidates = {}
    filtered_ranks = {}
    for query_id in condition_mathids:
        if query_id in candidate_ratings:
            filtered = []
            ranks = []

            # query is in human ratings,
            for idx, math_id in enumerate(condition_mathids[query_id]):
                if math_id in candidate_ratings[query_id]:
                    filtered.append(math_id)
                    ranks.append(idx + 1)

            filtered_candidates[query_id] = filtered
            filtered_ranks[query_id] = ranks

    # minimum elements with rating after filtering per query
    #print(min([len(filtered_candidates[query_id]) for query_id in filtered_candidates]))
    print(filtered_ranks)

    return filtered_candidates


def DCG(values, max_k):
    result = 0.0
    if len(values) > 0:
        result = values[0]

        for k in range(1, min(max_k, len(values))):
            result += values[k] / math.log(k + 1, 2)

    return result


def compute_nDCG(filtered_mathids, ideal_rankings, candidate_ratings,top_K):
    nDCG_values = []

    # for each query
    for query_id in filtered_mathids:
        # get ideal DCG at K
        max_score = DCG([ideal_rankings[query_id][k][0] for k in range(top_K)], top_K)

        # get current DCG at Kfor k in range(top_K):
        current_ratings = []
        for k in range(top_K):
            if k < len(filtered_mathids[query_id]):
                mathid = filtered_mathids[query_id][k]

                current_ratings.append(candidate_ratings[query_id][mathid])
            else:
                # Less than K relevant scores?
                current_ratings.append(0.0)

        current_score = DCG(current_ratings, top_K)

        nDCG = current_score / max_score

        nDCG_values.append(nDCG)

    #print(nDCG_values)
    return statistics.mean(nDCG_values)

def compute_nDCG_table(filtered_files, ideal_rankings, candidate_ratings, max_K):
    nDCG_results = {}

    for k in range(1, max_K + 1):
        nDCG_results[k] = {}
        for idx, filtered_mathids in enumerate(filtered_files):
            nDCG_results[k][idx] = compute_nDCG(filtered_mathids, ideal_rankings, candidate_ratings, k)

    return nDCG_results


def print_nDCG_table(nDCG_results, n_files, max_K):

    header = "K\t" + "\t".join(["F#" + str(idx + 1) for idx in range(n_files)])
    print(header)

    for k in range(1, max_K + 1):
        print(str(k) + "\t" + "\t".join(["{0:.2f}".format(nDCG_results[k][idx]) for idx in range(n_files)]))


def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython3 nDCG_human_to_new.py human_rating max_k query_offset [inputs ...]")
        print("")
        print("Where:")
        print("\thuman_rating\t: Path to File with Compiled human ratings in csv format")
        print("\tmax_k\t\t: nDCG @ 1 to max K")
        print("\tquery_offset\t: Offset of human rating query ids")
        print("\tinputs\t\t: Path to Files with results with math_ids in csv format")
        print("")
        return

    compiled_filename = sys.argv[1]

    try:
        max_k = int(sys.argv[2])
        if max_k <= 0:
            print("Invalid Max K value")
            return
    except:
        print("Invalid Max K value")
        return

    try:
        query_offset = int(sys.argv[3])
    except:
        print("Invalid query offset value")
        return

    unique_ratings = load_human_ratings(compiled_filename, query_offset)
    ideal_rankings, candidate_ratings = get_ideal_rankings(unique_ratings)

    possible_max_k = get_max_k(ideal_rankings)
    final_max_k = min(possible_max_k, max_k)
    print("Maximum K possible = " + str(possible_max_k) + ", choosen = " + str(max_k) + ", used = " + str(final_max_k))


    print("Input files: ")
    filtered_files = []
    for idx, input_filename in enumerate(sys.argv[4:]):
        print(str(idx + 1) + " - " + input_filename)

        # load raw files
        condition_mathids = load_mathids(input_filename)

        # filter to keep results with rating only
        filtered_mathids = filter_rated_candidates(condition_mathids, candidate_ratings)

        filtered_files.append(filtered_mathids)

    # compute nDCG
    nDCG_results = compute_nDCG_table(filtered_files, ideal_rankings, candidate_ratings, final_max_k)

    # final output
    print_nDCG_table(nDCG_results, len(filtered_files), final_max_k)

    print("Finished!")

if __name__ == '__main__':
    main()