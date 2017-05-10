import os
import sys


def create_file_index(list_path, rem_prefix):
    in_file = open(list_path, "r", encoding="utf-8")
    lines = in_file.readlines()
    in_file.close()

    len_pre = len(rem_prefix)
    index = {}
    for line in lines:
        line = line.strip()
        if line[:len_pre] == rem_prefix:
            current_path = line[len_pre:]
        else:
            current_path = line

        filename = os.path.basename(current_path)

        if filename in index:
            print("Conflict found: Filename <<" + filename + ">> appears more than once in collection")

        index[filename] = current_path

    return index


def compute_total_time(alt_filename):
    in_file = open(alt_filename, "r", encoding="utf-8")
    lines = in_file.readlines()
    in_file.close()

    total_time = 0.0
    for line in lines:
        parts = line.strip().split("\t")

        if len(parts) >=3 and parts[0].upper() == "QUERY":
            #assume time is field 2
            query_time = float(parts[2])
            total_time += query_time

    return total_time

def replace_paths_and_time(alt_filename, file_index, out_filename, total_time):
    in_file = open(alt_filename, "r", encoding="utf-8")
    lines = in_file.readlines()
    in_file.close()

    out_file = open(out_filename, "w", encoding="utf-8")
    for line in lines:
        parts = line.strip().split("\t")

        if len(parts) >=4 and parts[0].upper() == "RUN":
            # correct time .... Field at 3
            parts[3] = str(total_time)
            out_file.write("\t".join(parts) + "\n")
        elif len(parts) < 3 or parts[0].upper() == "QUERY":
            # just write the same input line ...
            out_file.write(line)
        else:
            # modify the file name part ...
            if parts[2] in file_index:
                parts[2] = file_index[parts[2]]
                out_file.write("\t".join(parts) + "\n")
            else:
                print("Warning: <<" + parts[2] + ">> not found in file index, keeping original name")
                out_file.write(line)

    out_file.close()


def main():
    if len(sys.argv) < 4:
        print("Usage")
        print("\tpython3 alt_format_expand_paths.py alt_file list_path out_file [rem_prefix]")
        print("")
        print("Where:")
        print("\talt_file:\tPath to input alt file")
        print("\tlist_path:\tPath to the list of files in the collection")
        print("\tout_file:\tPath to output alt file")
        print("\trem_prefix:\tPrefix to remove from filenames in the collection")
        return

    alt_filename = sys.argv[1]
    list_path = sys.argv[2]
    out_filename = sys.argv[3]

    if len(sys.argv) >= 5:
        rem_prefix = sys.argv[4]
    else:
        rem_prefix = ""

    # read
    print("Generating index ...")
    file_index = create_file_index(list_path, rem_prefix)

    print("Total files in collection: " + str(len(file_index)))

    total_time = compute_total_time(alt_filename)
    print("Total execution time for queries: " + str(total_time))

    print("Replacing ....")
    replace_paths_and_time(alt_filename, file_index, out_filename, total_time)

    print("Finished!")

if __name__ == '__main__':
    main()
