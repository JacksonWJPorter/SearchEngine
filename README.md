# MSCI 541: Search Engines
Name: Jackson Porter
WatIAM Student Id: j6porter

## How to Build and Run Programs

### Prerequisites
- Ensure you have Python 3.x installed on your machine.

### Running IndexEngine
To process the LATimes data, generate the metadata, build the inverted index and store the lexicon, run the following command:

    python IndexEngine.py <path_to_latimes.gz> <path_to_output_directory>

Replace **&lt;path_to_latimes.gz&gt;** with the path to your LATimes data file and **&lt;path_to_output_directory&gt;** with the directory where you want the metadata and processed documents to be saved.

### Running GetDoc
To retrieve a specific document using its **DOCNO**, run the following command:

    python GetDoc.py <path_to_output_directory> docno <docno>

To retrieve a specific document using its **Internal Id**, run the following command:

    python GetDoc.py <path_to_output_directory> id <id>

Replace **&lt;docno&gt;**/**&lt;id&gt;** with the DOCNO/Internal Id of your desired document, and **&lt;path_to_output_directory&gt;** with the path to your output directory.

### Running BooleanAND
To perform Boolean And retrieval with custom queries using the inverted index, lexicon, and metadata generated from IndexEngine.py, run the following command:

    python BooleanAND.py <index_path> <queries_path> <results_path>

Replace **&lt;index_path&gt;** with the path to your inverted_index.json file, **&lt;queries_path&gt;** with the path to your queries.txt file, and **&lt;results_path&gt;** with the directory where you want the query results to be written out to.

### Running EvaluationMetricsCalc
To calculate Average Precision, Precision@10, NDCG@10 and NDCG@1000 for topics 401-450 - excluding 416, 423, 437, 444, and 447 - with a Qrels file and different retrieval results files, run the following command:

    python3 EvaluationMetricsCalc.py --qrel <qrels_path> --results <results_path> --output <output_path> --k 10

Replace **&lt;qrels_path&gt;** with the path to your qrels.txt file, **&lt;results_path&gt;** with the path to your retrieval_results.txt file, and **&lt;output_path&gt;** with the file where you want the calculation results to be written out to.

### Running BM25Retrieval
To perform BM25 retrieval, run the following command:

    python3 BM25Retrieval.py <index_path> <queries_path> <results_path>

Replace **&lt;index_path&gt;** with the path to your inverted_index.json file, **&lt;queries_path&gt;** with the path to your queries.txt file, and **&lt;results_path&gt;** with the path to your retrieval_results.txt file.

### Running InteractiveRetrieval
To begin querying and viewing the LA Times documents, run the following command:

    python3  InteractiveRetrieval.py


