Instructions for installing and running Tangent 0.3.1
====================================================

Tangent uses python version 3, including the requests and beautiful soup modules.  Portions of the system also use LaTeXML for data conversion and various utilities (available through collections like MacPorts).

Add the directory containing the new tangent directory to your PYTHONPATH
(before any other directories that have other versions of tangent)

make (use dmake on Windows):
   creates executable for prototype search engine

** PREPARING FOR INDEXING

python index.py help
   displays help text for creating tuples for indexing

python index.py
    creates list of tuples for indexing as tangent/db-index/test_i_*.tsv
    This uses the default tangent.cntl as the control file.

python index.py my-own-file.cntl
    This uses the my-own-file.cntl as the control file, which must exist and have the few
    appropriate lines in it to specify database name, mapping file name, etc. See the help
    text for more detailed information.

** QUERYING

python query.py help
   displays help text for creating tuples for searching

python query.py
   creates list of tuples for searching as tangent/version032/db-index/test_q_*.tsv
   again, uses tangent.cntl as the default control file to provide parameters

python runquery.py
   used to execute queries that combine text and math expressions. A control file
   is required, and this file must contain parameters to connect to the text and
   math search engines. Execute without parameters for help

search [db-directory]
   script that runs the command below if no arguments are given. A directory
   containing index and query .tsv files may also be passed.
   Output is written to <dir>_results.tsv.

cat db-index/* | ./mathindex.exe > mathresults.tsv
   prototype generation of results from searching using files under db-index
   [N.B. assumes that all index files and all search files under db-index are to be used.
    Repeated calls to index.py and query.py with the same documents will produce
    duplicates, so change the argument to cat to specify just which files are desired.]

python3 reranking.py
    Reranks initial search results, and produces .html results pages.
    Run the command without arguments for information on usage.

search-rerank [db-directory]
    Run initial search followed by reranking (producing html pages). By default,
    runs over the db-index directory; if a directory is provided, produces
    initial results in file <dir>-results.tsv, and writes reranked results and
    .html files to directory <dir>-results.

** UTILITIES

python get_mathml.py <cntl> <docnum> <position>
   reads the MathML stored in the ith document at the jth relative position.
   Code like that can be inserted into any module desired to provide this functionality.
   (The module MathDocument is also used by index.py to read the documents for parsing.)
   N.B. using -1 in place of docnum retrieves the **query** expression at position j.

python docids2doclist.py <cntl> <docnums> <docnames>
   converts sets of document numbers into a list of filenames.
   Useful for debugging: error messages produced by index.py contain document numbers,
      but index.py requires a list of filenames as input

Documentation:
==============

Doxygen documentation of the source code in html can be viewed at:

doc/html/index.html

Currently Python, C and C++ code will be included in the doxygen files.

To update the documentation, make sure that doxygen is installed, and
then from the current directory issue:

    make docs    (on Windows: dmake docs)

Tangent 0.33 Code Organization:
===============================

tangent:
    combine_results.py	stand-alone routine to combine text and math search results
    index.py    stand-alone routine to parse data documents
    query.py    stand-alone routine to parse query documents
    run_query.py    stand-alone routine to execute queries
    rerank_results.py    stand-alone routine to process query results
    tangent.cntl    sample cntl file

    Makefile    makefile to create search engine and documentation

    mathindex.cpp    search engine code
    mathindexbase.h    search engine code
    mathindexmid.h    search engine code

    README.txt    this file

tangent/math:    routines to extract math expressions from documents
    exceptions.py
    latex_mml.py
    math_extractor.py
    mathdocument.py
    mathml.py
    mathsymbol.py
    mws.sty.ltxml
    symboltree.py
    version03_index.py

tangent/ranking:    routines to rerank and process query results
    alignment.py
    constraint_info.py
    document_rank_info.py
    mathml_cache.py
    query.py
    ranking_functions.py
    results.py
    wildcard_alignment.py

tangent/testing:    test data (documents) and test queries
    test_data
    test_queries
    testlist.txt    sample list of test files


tangent/text:    routines to handle text queries
    porter.py
    text_engine_client.py
    TextResult.py

tangent/utility:    various support routines
    comp_query.py
    control.py    read, access, and update .cntl file
    read_results.py
    Stats.py    collect parsing problems and statistics
    text_query.py

Interface to backend search engine:
===================================

Format of Files:

db-index/*_i_*.tsv
W	window
D	docID
E	expression	positions
E	expression	positions
...
D	docID
...
X

db-index/*_q_*.tsv
K	top-k
W	window
Q	queryID
E	expression	positions
E	expression	positions
...
T	keyword
T	keyword
...
Q	queryID
...
X

results.tsv
I	it	index-time(ms)

Q	queryID
E	queryExpr
R	docID	expression	score
R	docID	expression	score
...
I	qt	query-time(ms)
I	post	count
I	expr	count
I	doc	count

Q	queryID
...
X

where positions are expressed as [1] or [0, 5, 12] etc.
