import re
import math
import sys
import os
import json
from collections import Counter

# Command args
if len(sys.argv) != 4:
    print("Usage: python BM25Retrieval.py <index_path> <queries_path> <results_path>")
    sys.exit(1)
_, index_path, queries_path, results_path = sys.argv

# Load files
with open(os.path.join(index_path, "Lexicon", "lexicon_term_to_id.json"), "r") as lexicon_file:
    lexicon = json.load(lexicon_file)

with open(os.path.join(index_path, "inverted_index.json"), "r") as index_file:
    inverted_index = json.load(index_file)

with open(queries_path, "r") as queries_file:
    queries = queries_file.read().splitlines()

with open("/Users/jackson/Desktop/SearchEngineHW4/dataHW4/doc-lengths.txt", "r") as doc_lengths_file:
    doc_lengths = [int(line.strip()) for line in doc_lengths_file]  
    N = len(doc_lengths)
    avg_doc_length = sum(doc_lengths)/N

with open("/Users/jackson/Desktop/SearchEngineHW4/dataHW4/id_to_docno.json", "r") as id_to_docno_file:
    id_to_docno = json.load(id_to_docno_file)

def tokenize(text):
    tokens = re.findall(r'\w+', text.lower())
    return tokens

def bm25_retrieval(query, inverted_index, doc_lengths, avg_doc_length, N, k1=1.2, b=0.75):
    scores = {}

    for term in query:
        if term in lexicon:
            term_postings = inverted_index[lexicon[term]]
            ni = len(term_postings)  # Number documents containing the term

            for posting in term_postings:
                doc_id, term_freq = posting[0], posting[1]
                doc_length = doc_lengths[doc_id - 1] if 1 <= doc_id <= len(doc_lengths) else 0

                K = k1 * ((1 - b) + b * doc_length / avg_doc_length)
                idf = math.log((N - ni + 0.5) / (ni + 0.5))
                score = (term_freq / (K + term_freq)) * idf

                if doc_id in scores:
                    scores[doc_id] += score
                else:
                    scores[doc_id] = score

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:1000]  # Retrieve top 1000 documents


# Write out TREC format
def write_trec_results_file(results, topic_id, username):
    with open(os.path.join(results_path, "hw4-bm25-stem-j6porter.txt"), "a") as output_file:
        for rank, (doc_id, score) in enumerate(results, start=1):
            doc_id_string = str(doc_id)
            if doc_id_string in id_to_docno:
                docno = id_to_docno.get(doc_id_string)
            output_file.write(f"{topic_id} Q0 {docno} {rank} {score} {username}\n")

# Iterate through all queries
for i in range(0, len(queries), 2):
    topic_id = queries[i]
    query_text = queries[i + 1]

    if int(topic_id) not in [416, 423, 437, 444, 447]:
        query = tokenize(query_text)
        results = bm25_retrieval(query, inverted_index, doc_lengths, avg_doc_length, N)
        write_trec_results_file(results, topic_id, 'j6porter') 
