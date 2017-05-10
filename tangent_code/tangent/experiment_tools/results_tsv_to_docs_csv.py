
import io
import os
import sys
import xml
import pickle
from tangent.utility.control import Control
from tangent.math.mathdocument import MathDocument
from tangent.math.math_extractor import MathExtractor


class LocationCache:
    def __init__(self):
        self.cached_docs = {}

    def get_mathid(self, document_finder, doc, loc):
        if doc not in self.cached_docs:
            self.cached_docs[doc] = {}

        if loc not in self.cached_docs[doc]:
            mathml = document_finder.find_mathml(doc, loc)

            elem_content = io.StringIO(mathml) # treat the string as if a file
            root = xml.etree.ElementTree.parse(elem_content).getroot()

            if "id" in root.attrib:
                math_id = root.attrib["id"]
            else:
                print("ERROR: No formula id found for doc = " + str(doc) + ", loc = " + str(loc))
                math_id = "math.error"

            self.cached_docs[doc][loc] = math_id

        return self.cached_docs[doc][loc]




def get_tsv_results(filename):
    input_file = open(filename, 'r')
    all_lines = input_file.readlines()
    input_file.close()

    all_results = {}
    current_query = None
    current_query_results = []
    for line in all_lines:
        line = line.strip()

        parts = line.split("\t")

        if parts[0] == "Q":
            current_query = parts[1]
            current_query_results = []

            # This assumes the format "NTCIR11-Math-X"
            query_offset = int(current_query.split("-")[-1])

            all_results[query_offset] = {
                "offset"    : query_offset,
                "id"        : current_query,
                "results"   : current_query_results,
                "math_ids"  : [],
            }

        elif parts[0] == "R":
            doc = int(parts[1])
            loc = int(parts[2])

            current_query_results.append((doc, loc))

    return all_results

def find_formula_ids(tsv_results, control_filename, mathids_cache):
    control = Control(control_filename)
    document_finder = MathDocument(control)

    for query_offset in tsv_results:
        print("Processing Query: " + str(query_offset))
        total_locs = len(tsv_results[query_offset]["results"])
        for index, result in enumerate(tsv_results[query_offset]["results"]):
            doc, loc = result

            math_id = mathids_cache.get_mathid(document_finder, doc, loc)

            #print(str((query_offset, doc, loc, math_id)))
            tsv_results[query_offset]["math_ids"].append(math_id)
            
            if index > 0 and (index + 1) % 25 == 0:
                print("... done " + str(index + 1) + " of " + str(total_locs), end="\r")

def write_csv(tsv_results, out_filename):
    output_file = open(out_filename, "w")

    output_file.write("queryId,formulaId\n")

    for query_offset in sorted(list(tsv_results.keys())):
        for math_id in tsv_results[query_offset]["math_ids"]:
            output_file.write(str(query_offset) + "," + math_id + "\n")

    output_file.close()


def main():
    if len(sys.argv) < 4:
        print("Usage")
        print("\tpython results_tsv_to_docs_csv.py input control output")
        print("")
        print("Where:")
        print("\tinput\t: Path to File with results in tsv format (Tangent offsets)")
        print("\tcontrol\t: Path to Control File")
        print("\toutput\t: Path  to file where csv results will be stored (Original doc offsets)")
        print("")
        return

    input_filename = sys.argv[1]
    control_filename = sys.argv[2]
    output_filename = sys.argv[3]

    mathids_cache_file = control_filename + ".mathids.cache"
    if not os.path.exists(mathids_cache_file):
        mathids_cache = LocationCache()
    else:
        cache_file = open(mathids_cache_file, "rb")
        mathids_cache = pickle.load(cache_file)
        cache_file.close()

    print("Loading input...")
    input_results = get_tsv_results(input_filename)
    print("Finding math ids ...")
    find_formula_ids(input_results, control_filename, mathids_cache)
    print("Saving results ....")
    write_csv(input_results, output_filename)

    # save cache .,..
    cache_file = open(mathids_cache_file, "wb")
    pickle.dump(mathids_cache, cache_file, pickle.HIGHEST_PROTOCOL)
    cache_file.close()



    print("Finished")

if __name__ == "__main__":
    main()
