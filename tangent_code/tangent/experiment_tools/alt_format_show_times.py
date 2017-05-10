import os
import sys
import numpy as np


def extract_times(alt_filename, query_groups):
    in_file = open(alt_filename, "r", encoding="utf-8")
    lines = in_file.readlines()
    in_file.close()

    total_time = 0.0
    all_times = {}
    for line in lines:
        parts = line.strip().split("\t")

        if len(parts) >=3 and parts[0].upper() == "QUERY":
            query_id = parts[1]
            #assume time is field 2
            query_time = float(parts[2])

            current_group = ""
            for query_group in query_groups:
                if query_id in query_groups[query_group]:
                    current_group = query_group
                    break

            if not current_group in all_times:
                all_times[current_group] = []

            all_times[current_group].append(query_time)

    return all_times


def read_query_groups(groups_filename):
    input_file = open(groups_filename, 'r', encoding="utf-8")
    all_lines = input_file.readlines()
    input_file.close()

    groups = {}
    for line in all_lines:
        parts = line.strip().split(",")

        if len(parts) == 2:
            group_name, query_id = parts[1], parts[0]

            if not group_name in groups:
                groups[group_name] = []

            groups[group_name].append(query_id)

    return groups


def main():
    if len(sys.argv) < 3:
        print("Usage")
        print("\tpython3 alt_format_show_times.py query_groups alt_file_1 [alt_file_2...]")
        print("")
        print("Where:")
        print("\tquery_groups:\tPath to file containing query groups")
        print("\talt_file:\tPath to input alt file")
        return

    query_groups = read_query_groups(sys.argv[1])
    #print(query_groups)

    all_times = []
    times_per_group = {}
    for alt_filename in sys.argv[2:]:
        current_times = extract_times(alt_filename, query_groups)

        for group_name in current_times:
            if group_name not in times_per_group:
                times_per_group[group_name] = []

            times_per_group[group_name] += current_times[group_name]
            all_times += current_times[group_name]

    all_times = np.array(all_times)
    print(all_times)

    total_time = all_times.sum()
    mean_time = all_times.mean()
    median_time = np.median(all_times)
    min_time = all_times.min()
    max_time = all_times.max()
    print("All Queries:")
    print("\tTotal execution time for all queries: " + str(total_time) + " (" + str(total_time / 1000) + " s)")
    print("\tMean time: " + str(mean_time) + " (" + str(mean_time / 1000) + " s)")
    print("\tMin time: " + str(min_time) + " (" + str(min_time / 1000) + " s)")
    print("\tMax Time: " + str(max_time) + " (" + str(max_time / 1000) + " s)")
    print("\tMedian Time: " + str(median_time) + " (" + str(median_time / 1000) + " s)")

    for group_name in times_per_group:
        group_times = np.array(times_per_group[group_name])

        total_time = group_times.sum()
        mean_time = group_times.mean()
        median_time = np.median(group_times)
        min_time = group_times.min()
        max_time = group_times.max()
        print("Group: " + group_name)
        print("\tTotal execution time for all queries: " + str(total_time) + " (" + str(total_time / 1000) + " s)")
        print("\tMean time: " + str(mean_time) + " (" + str(mean_time / 1000) + " s)")
        print("\tMin time: " + str(min_time) + " (" + str(min_time / 1000) + " s)")
        print("\tMax Time: " + str(max_time) + " (" + str(max_time / 1000) + " s)")
        print("\tMedian Time: " + str(median_time) + " (" + str(median_time / 1000) + " s)")





    print("Finished!")

if __name__ == '__main__':
    main()
