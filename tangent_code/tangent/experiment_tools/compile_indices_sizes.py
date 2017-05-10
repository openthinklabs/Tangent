__author__ = 'mauricio'

import os
import sys

def condition_from_filename(filename):
    parts = filename.strip().split(".")[0].split("_")

    pos = len(parts) - 1
    e = None
    w = None
    while (e is None or w is None) and pos >= 0:
        if parts[pos][0] == "w":
            w = int(parts[pos][1:])
        if parts[pos][0] == "e":
            e = int(parts[pos][1:])
        pos -= 1

    return e, w

def main():
    if len(sys.argv) < 3:
        print("Usage")
        print("\tpython compile_indices_sizes.py out_sizes [indices]")
        print("")
        print("Where:")
        print("\tout_sizes\t: File where summarized data will be stored")
        print("\tindices\t: Indices Files")
        return

    out_filename = sys.argv[1]
    indices_filenames = sys.argv[2:]

    indices_sizes = {}
    all_pairs = False
    for index_filename in indices_filenames:
        print("Adding: " + index_filename)

        e, w = condition_from_filename(index_filename)

        if w == 0:
            w = "a"
            all_pairs = True


        # indexing ....
        file_size = os.stat(index_filename).st_size

        if w not in indices_sizes:
            indices_sizes[w] = {0: 0.0, 1: 0.0}

        indices_sizes[w][e] = file_size


        #condition = "e" + str(e) + "_w" + str(w)

    # ... sort window sizes considering that w=0 becomes "a" (all) and goes last
    tempo_windows = []
    for key in indices_sizes:
        if key != "a":
            tempo_windows.append(key)

    windows = sorted(tempo_windows)
    if all_pairs:
        windows.append("a")

    out_file = open(out_filename, "w")
    header = "window,e_0,e_1"
    out_file.write(header + "\n")
    for window in windows:

        line = str(window) + "," + str(indices_sizes[window][0]) + "," + str(indices_sizes[window][1]) + "\n"
        out_file.write(line)
    out_file.close()

main()