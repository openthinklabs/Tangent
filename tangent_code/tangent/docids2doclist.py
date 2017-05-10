import codecs
import sys
from sys import argv

from tangent.utility.control import Control
from tangent.math.mathdocument import MathDocument

__author__ = 'FWTompa'

if __name__ == '__main__':

    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    if len(argv) != 4 or argv[1] == "help":
        print("Use: python docids2doclist.py <cntl> <doc#s> <filelist>")
        print("        where doc#s is a file in which each line is a set of docids")
        print("        such as {23145, 31242, 125}")
        sys.exit()

    cntl = Control(argv[1]) # control file name (after indexing)
    md = MathDocument(cntl)
    doclist = []
    with open(argv[2], 'r', encoding='utf-8') as fin:
        while True:
            t = fin.readline()
            if t == "":
                break
            doclist.extend(t.strip("{} \n").split(", "))
    with open(argv[3], 'w', encoding='utf-8') as fout:
        for val in doclist:
            fout.write(md.find_doc_file(int(val))+"\n")
    print("Created list of %d file names" % len(doclist))
