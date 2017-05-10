Instructions for using the tools for experiments with Tangent 0.33
===================================================================

Different tools are provided for computing distinct metrics used to evaluate the Tangent system and each of them is briefly described here.

Many of these tools are designed to compare the outputs from the core and the reranker produced by the system after running on different conditions. The tools asume a naming convention for these files which helps them identify the parameters set for each run. The convention is as follows:

{source}_m{method_id}_w{window_size}_e{EOL}.tsv

{source}	: Source of the output file. It can be "core" or "reranked".
{method_id}	: Similarity metric used. Note that MSS is metric #4.
{window_size}	: Window size used for pair generation.
{EOL}		: 1 if EOL were active and 0 otherwise.

For example, if the EOL pairs were active (e=1) and the results were reranked with MSS (method_id = 4), and the current window size is 2, the output files expected are:

Core results:		core_m4_w2_e1.tsv
Reranked results:	reranked_m4_w2_e1.tsv

Tools available:
====================================

** Changing system settings 

Window size used for indexing can be set in the tangent control file. Input documents are pre-processed and stored in an intermediate representation which includes information about the window size that will be used by the indexing program. It is possible to change the window size configuration on these intermediate files to avoid pre-processing the input dataset multiple times. For this purpose use change_window.py.

Usage
	python3 change_window.py window [input_files]

Where:
	window:		New value for window parameter
	input_files:	Input files to modify


** Computing Gold Standards for queries

Gold standards for a given set of queries can be computed. These consists of the reranking of all unique expresions in the dataset for each query using the specified reranking function like for example the MSS metric. The first step for reranking is the extraction of the list of unique expressions. This can be done using the extract_unique_expressions.py tool which takes as input the pre-processed files before indexing and outputs the list of uniques expressions found.

Usage
	python extract_unique_expressions.py [input_files]

Where:
	input_files	: Index files to process

Computing a gold standard for a single query is a slow task that might take several hours. The task itself is divided into two main steps: Computing the metric scores for each unique expression against each query, and the second is sorting these expressions by score and grouping them by similar structural matches (ranks and subranks). 

The first step, score calculation, can be executed using the gold_standard_scores.py. Note that it requires the file that contains the set of preprocessed queries. One temporary file will be produced for each individual query and these will be stored in the given output directory.

Usage
	python gold_standard_scores.py expressions output n_jobs [queries]

Where:
	expressions	: File that contains all unique expressions
	output	: Directory where gold standard scores will be stored
	n_jobs	: Number of process to use
	queries	: Files that contains indexed queries

The final gold standards are obtained using the gold_standard_groups.py tool. 

Usage
	python gold_standard_groups.py input_dir output_dir n_jobs [queries]

Where:
	input_dir	: Path to Directory that contains gold standard scores
	output_dir	: Directory used to store final gold standard ranks
	n_jobs		: Number of jobs to use to compute the groups
	queries		: Files that contain the queries


** Summarization Tools 

In order to compare results from multiple runs of the system under different conditions, some tools are provided that can be used to produce summaries of different statistics. 

Note that after running the core engine search, the system will produce tsv output containing not only the search results but also some general statistics about the current search index and other specific values that describe the behavior of the system for each specific query executed. 

Use the compile_stats.py program to compile these results from different runs of the system. The program will produce two separate summaries for global (index) statistics: one for EOL conditions and the other for no EOL conditions. Then, the program will also produce multiple separate summaries for query-level statistics 

Usage
	python compile_stats.py out_prefix [input_files]

Where:
	out_prefix	: Prefix for files where summarized results will be stored
	input_files	: Files to process

Among the multiple values collected by the compile_stats.py tool, there will time statistics like indexing, querying and reranking times. These values are variable for each run and one typically needs to run the system multiple times for each condition in order to analyze these values correctly. 

A different tool is provided for these variable statistics which collects the values from multiple runs into a single summary file. The program is called "compile_times.py".

Usage
	python compile_times.py   out_file   [input_files]

Where:
	out_file	: File where results are appended
	input_files	: Files to process

The compile_times.py tool appends the results from different runs into a single file. However, this file format might not be addequate for certain types of analysis that compare the time statistics for each individual query under different conditions. 

A variation of compile_times.py, compile_times_gen.py is provided for the same purpose to handle files that do not use the naming convention of the condition being evaluated.

Use the split_times.py tool to obtain different summaries (one per time statistic) sorted by queries and then by run. This output format accepts multiple runs per condition. However, it is recommended that the same number of runs is used for all conditions under which the system is being tested.

Usage
	python split_times.py  compiled_times

Where:
	compiled_times	: File where times have been compiled

Optional:
	-i	out_index_times	: File to store indexing times averages
	-q	out_query_times	: File to store raw query times


A variation of split_times.py, split_times_gen.py is provided to handle files that do not use the same naming convetions for conditions being evaluated.


The last tool provided for summarization is compile_indices_sizes.py. This tool takes as input the filenames of the core engine index files  and produces a file with a small summary of file sizes per condition. Note that this tool also assumes a naming convention for index filenames which must include "w{window_size}_e{EOL}" as part of the filename.

Usage
	python compile_indices_sizes.py out_sizes [indices]

Where:
	out_sizes	: File where summarized data will be stored
	indices	: Indices Files
      
** Evaluation tools

Different tools are provided for evaluation. There are some important differences between the internal representation of formulas used by our system and the formula representation used for certain benchmark task like the NTCIR-11 Wikipedia task. We provide the tools required to extend and modify our raw result files into new formats that are compatible with the NTCIR-11 Wikipedia task benchmark.

The results_tsv_to_docs_csv.py can convert a raw results TSV file (core or reranked) into a CSV format containing queryIds and mathml ids. In our internal representation, formulas are identified by their SLT strings which is a canonical representation. The mathml ids are the original identifiers given to each instance of each formula in their mathml representation in the Wikipedia task dataset. 

Usage
	python results_tsv_to_docs_csv.py input control output

Where:
	input	: Path to File with results in tsv format (Tangent offsets)
	control	: Path to Tangent Control File
	output	: Path  to file where csv results will be stored (Original doc offsets)


After obtaining a file which is compatible with the original Wikipedia task benchmark, it is possible to extended this format to add back our internal representation SLT and some additional information like MSS scores and Gold standard ranks for further analysis with the tools that we provide. Use extend_csv.py for this purpose.

Usage
	python extend_csv.py input_csv input_tsv gold_prefix output_csv

Where:
	input_csv	: Path to file with results in csv format
	input_tsv	: Path to file with results in original format
	gold_prefix	: Prefix used for gold standard files
	output_tsv	: Path to file where results will be stored


The distribution of nDCG values for the rankings produced for different queries can be obtained by using human ratings for relevance if available. Use nDCG_human.py to obtain these values for a given pair of results after reranking. Core results here are only included to compare the nDCG value for the same top-K results from the reranker if they had appear in their original order provided by the core engine.

Usage
	python nDCG_human.py core_tsv rerank_tsv human_rating

Where:
	core_tsv	: Path to File with core results in tsv format
	rerank_tsv	: Path to File with reranked results in tsv format
	human_rating	: Path to File with human ratings in csv format
	current_k	: nDCG @ current_k

An extension is provided as nDCG_human_to_new.py which can be used to compare NDCG values for multiple conditions at once.



The distribution of nDCG values for core engine results assuming the gold standards as the ideal relevance metric can be computed using the nDCG_metrics.py tool.

Usage
	python nDCG_metrics.py core_input gs_prefix output_dist K_values

Where:
	core_input	: Path to File with core results in tsv format
	gs_prefix	: Prefix for gold standard files
	output_dist	: File where the raw nDCG values will be stored
	K_values	: Maximum rank values to consider, use 0 for Infinite

A summary of nDCG values for different conditions can be obtained using the nDCG_summarize.py tool.

Usage
	python nDCG_summarize.py output_prefix [inputs]

Where:
	output_prefix	: Prefix for summary files
	[inputs]	: List of input files


Use ntcir_metrics.py to compute the Mean Reciprocal Rank of the target formulas for each query of the wikipedia task. The target formula id must be provided for each query in the ground truth csv file using queryId,mathml_id. A csv file containing the classification of each query must be provided. The tool will compute the Success rate and MRR values for each group of queries. 

The program accepts a list of K_values in order to compare the success rate of the system at different number of top-K documents. Four groups of Success and MRR are computed: Document-Centric, Formula-centric, Gold Standard Centric and SLT-centric. The first two correspond to the original metrics used for NTCIR-11 Wikipedia task. Gold Standard centric corresponds to the MRRs using the Gold standard Rank and Subrank as the current rank of the instead of using the raw position in the list of documents. Finally, SLT-Centric corresponds to the case where a formula is accepted as a match as long it is an exact match which allows different instances of the same formula match on the target document.

Usage
	python ntcir_metrics.py input ground_truth topic_groups group [K_values]

Where:
	input		: Path to File with results in tsv format
	ground_truth	: Path to File with ground truth in tsv format
	topic_groups	: Path to file with topic groups
	topic		: Show only topics of this groups. Use 0 for all topics.
	K_values	: Maximum rank values to consider, use 0 for Infinite

One important consideration of the NTCIR wikipedia task benchmark is that for the document-centric evaluation, the list of documents are reranked or filtered to remove those that appear multiple times in the results list and consider only the first time that each of them appears. Use filter_csv.py to filter the expanded result files.

Usage
	python filter_csv.py input ground_truth output

Where:
	input		: Path to File with results in tsv format
	ground_truth	: Path to File with ground truth in csv format
	output		: Path  to file to store filtered tsv results

The tool ntcir_metrics2.py can be used to create the evaluation tables for formula-centric and document-centric with a single script. 

Use the tool ntcir_metrics_from_math_ids.py to compute the MRR and Recall metrices directly from the unfiltered mathids files. This tool will do the filtering and produce results for formula-centric and document-centric evaluation. So far, this is the most convinient tool provided for computation of these metrics.

** NTCIR-12 Alternative formatting

The runquery.py program in the main directory of this distribution generates search results using the Alternative formatting provided for NTCIR-12 MathIR task.

By default, our runquery.py tool will group all matches for a query found on a given document. Use alt_format_expand_docs.py to expand each of these matches as a separate entry in the final rank.

By default, our runquery.py tool will provide only the file names for each document document matched. Use alt_format_expand_paths.py to  expand these file names to include the relative path of the file in the collection. 

Finally, the alt_format_show_times.py tool can be used to extract and display time statistics from .alt files.


