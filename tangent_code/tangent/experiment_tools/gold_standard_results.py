
import os
import csv
import sys
import codecs
import time
import fnmatch
import subprocess

def read_queries(filename):
    # read all text ...
    input_file = open(filename, "r", newline='', encoding='utf-8')
    reader = csv.reader(input_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    all_text = [row  for row in reader]
    input_file.close()

    current_query = None
    found_queries = []
    for parts in all_text:
        if len(parts) == 0:
            continue

        if parts[0] == "Q":
            current_query = parts[1]

        if parts[0] == "E":
            if current_query is not None:
                current_expression = parts[1]
                found_queries.append((current_query, current_expression))

            current_query = None

    return found_queries


def get_topk_gs_formulas(gs_filename, top_k):
    input_file = open(gs_filename, "r", newline='', encoding='utf-8')
    reader = csv.reader(input_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    # read the header of the file ...
    header = next(reader)

    # now, read each result ...
    top_results = []
    for idx in range(top_k):
        try:
            parts = next(reader)
        except:
            print("Less than " + str(top_k) + " results found in " + gs_filename)
            break

        #slt, rank, group, score1 .... scoren
        slt = parts[0]
        scores = [float(score) for score in parts[3:]]

        top_results.append((slt, scores))

    input_file.close()

    return top_results

def get_formulae_locations_from_engine(engine_exe, engine_idx, engine_window, formulas):
    # Load Core Engine on a subprocess
    engine = subprocess.Popen([engine_exe, "-i", engine_idx], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # query for core engine
    query = u"K\t1\n"
    query += u"W\t" + str(engine_window) + "\n"

    for idx, formula in enumerate(formulas):
        query += u"Q\tQ-" + str(idx) + "\n"
        query += u"E\t" + formula + "\t[0]\n"


    query += u"X\n"

    # execute query ...
    e_out, e_err = engine.communicate(query.encode(encoding='utf-8'))

    if len(e_err) > 0:
        print("From Core-Engine: ")
        print(e_err)

    # decode engine output .. from binary to fields
    output_lines = e_out.decode(encoding="utf-8").split("\n")
    reader = csv.reader(output_lines, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    locations = {}
    # find locations retrieved
    current_formula = None
    for row in reader:
        if len(row) > 0 and row[0] == "Q":
            query_idx = int(row[1][2:])
            current_formula = formulas[query_idx]
            locations[current_formula] = []

        if len(row) > 0 and row[0] == "R":
            if row[3] == current_formula:
                doc = int(row[1])
                loc = int(row[2])

                locations[current_formula].append((doc, loc))
            else:
                print("Formula not found: " + current_formula)
                print(row, flush=True)
                raise Exception("Formula not found by engine")

    return locations

def main():
    if len(sys.argv) < 8:
        print("Usage")
        print("\tpython gold_standard_results.py input_dir output_file queries top-K engine index window")
        print("")
        print("Where:")
        print("\tinput_dir\t: Path to Directory that contains gold standard groups")
        print("\toutput\t\t: Path to file where results will be stored")
        print("\tqueries\t\t: File that contain the queries")
        print("\ttop-K\t\t: Number of top unique formulas that will be expanded")
        print("\tengine\t\t: Path to Core-Engine executable")
        print("\tindex\t\t: Path to Core-Engine Index file to use")
        print("\twindow\t\t: Window size used by Core-Engine index")
        return

    input_dir = sys.argv[1]
    output_filename = sys.argv[2]
    queries_filename = sys.argv[3]

    engine_exe = sys.argv[5]
    engine_idx = sys.argv[6]



    try:
        window_size = int(sys.argv[7])
    except:
        print("Invalid window size for core-engine index")
        return

    try:
        top_k = int(sys.argv[4])
        if top_k < 1:
            print("Invalid Top-K selected")
            return
    except:
        print("Invalid Top-K selected")
        return

    try:
        complete_list = os.listdir(input_dir)
        filtered_list = []
        for file in complete_list:
            if fnmatch.fnmatch(file, '*.tsv'):
                filtered_list.append(file)

        filtered_list = sorted(filtered_list)
    except:
        print( "Invalid input path!" )
        return

    all_queries = read_queries(queries_filename)

    out_file = open(output_filename, "w", encoding="'UTF-8'")
    csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    # empty required stats at beginning
    csv_writer.writerow(["I", "read", "0"])
    csv_writer.writerow([])

    for query_name, query_expression in all_queries:
        input_filename = query_name + ".tsv"
        if not input_filename in filtered_list:
            print("Gold standard for query \"" + query_name + "\" not found", flush=True)
        else:
            print("Processing Query: " + query_name, flush=True)

        # get the top-K formulas from the gold standard
        top_results = get_topk_gs_formulas(input_dir + "/" + input_filename, top_k)

        print("... getting locations from core-engine index...", flush=True)
        # call the core-engine, get documents and locations for this formulas
        top_formulas = [formula for formula, scores in top_results]
        locations = get_formulae_locations_from_engine(engine_exe, engine_idx, window_size, top_formulas)

        print("... adding to output file ...", flush=True)

        # output results for current query ...
        csv_writer.writerow(["Q", query_name])
        csv_writer.writerow(["E", query_expression])

        # write each individual result with its locations ...
        for formula, scores in top_results:

            # for each location
            for doc, loc in locations[formula]:
                csv_writer.writerow(["R", str(doc),	str(loc), formula,	str(scores[0])])

        csv_writer.writerow(["I", "qt", "0.0"])
        csv_writer.writerow(["I", "post", "0"])
        csv_writer.writerow(["I", "postsk", "0"])
        csv_writer.writerow(["I", "expr", "0"])
        csv_writer.writerow(["I", "exprsk", "0"])
        csv_writer.writerow(["I", "doc", "0"])
        csv_writer.writerow([])

    # empty required stats at the end
    csv_writer.writerow(["I", "dictDocIDs", "0"])
    csv_writer.writerow(["I", "dictExpressions", "0"])
    csv_writer.writerow(["I", "dictTerms", "0"])
    csv_writer.writerow(["I", "dictRelationships", "0"])
    csv_writer.writerow(["I", "lexTokenTuples",	"0", "0", "0", "0"])
    csv_writer.writerow(["I", "subExprDoc", "0"])
    csv_writer.writerow([])
    csv_writer.writerow(["X"])
    out_file.close()

    print("Finished!")

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    main()
