__author__ = 'mauricio'

import sys
import csv

def main():
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython extract_unique_expressions.py output_file [input_files]")
        print("")
        print("Where:")
        print("\toutput_file\t: Files where index results will be stored")
        print("\tinput_files\t: Index files to process")
        return

    full_dict = {}
    doc_id = -1

    output_filename = sys.argv[1]
    out_file = open(output_filename, "w", newline='', encoding='utf-8')
    csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    for filename in sys.argv[2:]:
        in_file = open(filename, "r", newline='', encoding='utf-8')
        reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        all_lines = [row  for row in reader]
        in_file.close()

        for line in all_lines:
            parts = line
            if len(parts) >= 2 and parts[0] == "E":
                #parts = line.strip().split("\t")

                expression = parts[1]

                if not expression in full_dict:
                    full_dict[expression] = True

                    subparts = parts[2].split(",")
                    first_location = subparts[0][1:]
                    if len(subparts) == 1:
                        first_location = first_location[:-1]


                    print(expression + "\t" + str(doc_id) + "\t" + str(first_location))
                    csv_writer.writerow([expression, str(doc_id), str(first_location)])

            if len(parts) > 0 and parts[0] == "D":
                #parts = line.strip().split("\t")

                doc_id = int(parts[1])

            if len(parts) > 0 and parts[0] == "Q":
                print("ERROR: A QUERY FILE HAS BEEN GIVEN AS INPUT")
                out_file.close()
                return

    out_file.close()

main()