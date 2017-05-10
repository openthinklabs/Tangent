
import sys


def expand_documents(alt_filename, max_docs, out_filename):
    in_file = open(alt_filename, "r", encoding="utf-8")
    lines = in_file.readlines()
    in_file.close()

    out_file = open(out_filename, "w", encoding="utf-8")
    total_docs_query = 0
    next_rank = 1
    last_query_name = None
    for line in lines:
        parts = line.strip().split("\t")

        if len(parts) >= 3:
            if parts[0].upper() == "QUERY":
                if not last_query_name is None:
                    print(last_query_name + " - " + str(total_docs_query))
                total_docs_query = 0
                next_rank = 1
                last_query_name = parts[1]


            if parts[0].upper() != "RUN" and parts[0].upper() != "QUERY":
                # expand parts
                overhead = 3
                n_locations = int((len(parts) - overhead) / 3)

                to_add = min(n_locations, max(0, max_docs - total_docs_query))
                for i in range(to_add):
                    row  = [str(next_rank)] + parts[1:overhead] + parts[overhead + i * 3: overhead + (i + 1) * 3]
                    out_file.write("\t".join(row) + "\n")
                    next_rank += 1

                total_docs_query += n_locations
            else:
                # just write to file
                out_file.write("\t".join(parts) + "\n")
        else:
            # just write to file
            out_file.write("\t".join(parts) + "\n")

    if not last_query_name is None:
        print(last_query_name + " - " + str(total_docs_query))

    out_file.close()


def main():
    if len(sys.argv) < 4:
        print("Usage")
        print("\tpython3 alt_format_expand_paths.py alt_file out_file max_docs")
        print("")
        print("Where:")
        print("\talt_file:\tPath to input alt file")
        print("\tout_file:\tPath to output alt file")
        print("\tmax_docs:\tMaximum number of docs per query (=< 0 for unlimited)")
        return

    alt_filename = sys.argv[1]
    out_filename = sys.argv[2]

    try:
        max_docs = int(sys.argv[3])
    except:
        print("Invalid value for maximum number of docs per query")
        return

    print("Expanding ....")
    expand_documents(alt_filename, max_docs, out_filename)

    print("Finished!")

if __name__ == '__main__':
    main()
