## Tangent 0.3.1 Math Formula Search Engine##

*First Released August 2015*
*Current Release: June 2016*

*Authors:*

**Kenny Davila and Richard Zanibbi**,
Rochester Institute of Technology, USA

**Andrew Kane and Frank Tompa**,
University of Waterloo, Canada

-----

Tangent 0.3 is an application designed for indexing and retrieval of math formulas from large collections of documents or web pages. A complete description of our system may be found in our technical report:

[Tangent 0.3 arXiv preprint](http://arxiv.org/abs/1507.06235)



##License##
	LICENSE: Source code, data and results are being released under a Non-Commercial Creative Commons License (see the LICENSE file). 


**Please cite the paper above if you use the source code or data in this repository, and indicate any changes made when code or data are re-released.**




##Package Overview##

This package contains the tools, code and data used for the version of our paper submitted to NTCIR-12. The package contains two main directories:

+ **tangent_code** <br /> 
  Source code for Tangent system along with additional tools for experiments.

+ **results** <br />
  Set of results from for the NTCIR-12 MathIR Tasks: ArXiv Main Task, Wikipedia Main Task, and Wikipedia Formula Browsing Task.  


##Package Contents##



###Directory: tangent###

Contains all source code and test data required to run Tangent 0.3.1. The main directory has a set of python and C++ files used by Tangent. The pre-processing tools, re-ranking algorithm and experiment tools are all implemented in Python 3. The core-engine component has been implemented in C++. 

	NOTE: For detailed information about the source code and the tools, please see:
		tangent/readme.txt:  Basic instructions to compile and execute Tangent.
		tangent/experiment_tools/README_experiment_tools.txt: Describes tools for experiments.
  
The repository also contains the following sub-directories:

+ **experiment_tools** <br />
  A set of python scripts that can be used to obtain the different metrics for evaluation of our system. 

+ **math** <br />
  This module contains all the basic Python classes used by our system for pre-processing of data and data representation (Symbol Layout Trees). 

+  **ranking** <br /> A module which defines a set of classes and functions required for re-ranking of results using different similarity metrics including Maximum Subtree Similarity (MSS).  It also contains the set of classes used for generation of HTML search results.

+  **testing** <br />
   This directory contains some examples of the data and queries that can be accepted by our system. It contains the following files and sub-directories: 

  	+ **test_data:** A small Dataset containing files in different formats accepted by our system.
    
 	 + **test_queries:** Includes some examples of queries defined in the XML format supported by our system. Note that this folder includes the file NTCIR11-Math-queries.xml which defines the 100 queries used for the NTCIR-11 Wikipedia Task.
  	+ **testlist.txt:** This file has a listing of all the files contained in the test_data sub-directory, one file per line. This is the format used by our system to define a Dataset.  

+  **text** <br />
   Module used to connect to remote text-search engine (Solr) in order to handle keywords in queries. 

+  **utility** <br />
   Additional miscellaneous classes required by the Tangent system. 



###Directory: results###

The Results directory has two main sub-directories, one for arXiv tasks results called **ArXiv**, and the second for Wikipedia tasks results called **Wikipedia**.

####arXiv####

The results for the main arXiv task are located in the directory Task_Main.

+ **submissions** <br />

Contain results submitted for NTCIR-12 in two formats: .alt and .xml. The .xml is the official submission format, while the .alt format is human-readable.

####Wikipedia####

The results for the main Wikipedia task are located in the directory Task_Main, and the results for the Formula Browsing Subtask are located in Task_FormulaBrowing.

+ **submissions** <br />

Contain results submitted for NTCIR-12 in two formats: .alt and .xml. The .xml is the official submission format, while the .alt format is human-readable.

+ **core_output** <br />
  Raw results files produced by the core engine using different system configurations for the NTCIR-11 Wikipedia Task queries. All files are presented in TSV format and they contain the queries with their names and canonical **Symbol Layout Tree (SLT)** string encodings, along with the list of top-100 unique formulas and all the documents that contain each formula. Each file contains raw statistics associated to both the current index and statistics about each query execution. <br />
  
  A naming convention has been adopted to identify the system conditions used to generate each result file. If the file begins with the prefix "EOL" it means that the EOL pairs were active in the core engine. In addition, all files contain the sequence w\_{window\_size}.


+ **reranked_output** <br />
  Results files produced by the re-ranker program after sorting the raw results produced by the core-engine (core\_output directory). While the re-ranking method has been fixed to use the MSS metric, the original set of results retrieved by the core engine will affect the set of formulas included in each file. The same naming conventions and file formats used for the core\_output directory are applied here.  

+ **html** (example search engine retrieval pages (SERP) / 'result' pages) <br />
  Examples of the HTML output produced by our system. Results for selected conditions are included in sub-directories that are named with the same convention as the core\_output files, one sub-directory per condition. For each condition, a set of directories with HTML results per query is provided, and these directories are named query\_{query_number}. Each query directory contains 3 HTML files and a sub-directory containing all images used by these 3 files. The HTML files provided per query are:

  + **{query\_name}\_main.html:** Main results file which shows the matching formulas grouped by similar score and same structural matching. Diagrams of substructures that have been matched are provided for each structural group (click on the 'Graphs' button to see these).   
  + **{query\_name}\_docs.html:** Shows the final ranking of documents, considering that each document might contain multiple unique formula matches.
  + **{query\_name}_formulas.html** Extended version of the ranking per formula which shows the complete list of documents that contain each individual formulas. <br />
  
  + The HTML pages contain links which make possible to navigate from each view to any of the other two. *The pages also provide links to the visualization tool which highlights the matched formulas in their original documents. However, These links are broken and will not work under the current directory structure.
  Instead, some example formula-highlighting results are provided in a separate directory called **formula-highlighting**.*


