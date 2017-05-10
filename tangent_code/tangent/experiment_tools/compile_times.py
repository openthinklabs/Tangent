__author__ = 'mauricio'

import sys
import os

def window_from_filename(filename):
    start_w = -8
    while "0" <= filename[start_w - 1] <= "9":
        start_w -= 1

    window = filename[start_w:-7]

    return int(window)


def process_file(filename):
    # read entire file ...
    input_file = open(filename, "r", encoding='utf-8')
    all_lines = input_file.readlines()
    input_file.close()

    current_query = -1
    query_count = 0

    index_time = 0.0
    query_times = []
    query_names = []

    for line in all_lines:
        if line[0] == "I":
            parts = line.split("\t")

            # collect stats ...
            if parts[1] == "it":
                index_time += float(parts[2])

            elif parts[1] == "qt":
                if query_count > 0:
                    query_times.append(float(parts[2]))
                else:
                    query_times.append(-1.0)

        elif line[0] == "Q":
            parts = line.split("\t")

            query_names.append(parts[1])

            current_query += 1
            query_count = 0

        elif line[0] == "R":
            query_count += 1

    return index_time, query_times, query_names


def main():
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython compile_times.py   out_file   [input_files]")
        print("")
        print("Where:")
        print("\tout_file\t: File where results are appended")
        print("\tinput_files\t: Files to process")
        return

    output_filename = sys.argv[1]

    for filename in sys.argv[2:]:
        print("Processing: " + filename)

        window = window_from_filename(filename)

        base_e = filename[-5:-4]

        index_time, query_times, query_names = process_file(filename)

        if not os.path.exists(output_filename):
            out_file = open(output_filename, "w")

            header = "w,e,index_time"
            for query_name in query_names:
                header += "," + query_name.strip()

            out_file.write(header + "\n")
        else:
            out_file = open(output_filename, "a")

        line = str(window) + "," + str(base_e) + "," + str(index_time)
        for time in query_times:
            line += "," + str(time)

        out_file.write(line + "\n")

        out_file.close()

    print("Finished!")


main()