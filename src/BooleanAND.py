import os
import sys
import json
import re
from IndexEngine import Lexicon

# Command line args
if len(sys.argv) != 4:
    print("Usage: python BooleanAND.py <index_path> <queries_path> <results_path>")
    sys.exit(1)
_, index_path, queries_path, results_path = sys.argv

# Load Lexicon, InvIndex
with open(os.path.join(index_path, "Lexicon", "lexicon_term_to_id.json"), "r") as lexicon_file:
    lexicon = json.load(lexicon_file)

with open(os.path.join(index_path, "inverted_index.json"), "r") as index_file:
    inverted_index = json.load(index_file)

def boolean_and_retrieval(query_terms):

    matching_doc_ids = None 

    for term in query_terms:
        
        term_id = lexicon.get(term)

        if term_id is None:
            print(f"Term '{term}' not found in the lexicon.")
            sys.exit(1)

        # Retrieve the list of documents containing the term
        if term_id < len(inverted_index):
            term_postings = inverted_index[term_id]

            if matching_doc_ids is None:
                # If first term, initialize matching set with its doc IDs
                matching_doc_ids = set([internal_id for internal_id, _ in term_postings])
            else:
                # Set intersection with the current matching set
                matching_doc_ids &= set([internal_id for internal_id, _ in term_postings])

    # If there are matching documents, return the list; otherwise, return None
    return matching_doc_ids

# Read the queries from the queries file
with open(queries_path, "r") as queries_file:
    queries = queries_file.read().splitlines()

def tokenize(text):
    tokens = re.findall(r'\w+', text.lower())
    return tokens

# List to store the retrieval results
results = []

# Store the current topic and query terms
topic_id = None
query_terms = []

# Process each line
for line in queries:
    if line.isdigit():
        topic_id = line
    else:
        # This line contains query terms
        query_terms = tokenize(line)

        # Perform Boolean AND retrieval for the query
        matching_doc_ids = boolean_and_retrieval(query_terms)

        # Rank and score the retrieved documents
        rank = 1
        for internal_id in matching_doc_ids:
            # Calculate score
            score = len(matching_doc_ids) - rank

            # Find docno
            with open(os.path.join(index_path, 'id_to_docno.json'), 'r') as f:
                id_to_docno = json.load(f)

            # Convert internal_id to a string
            internal_id_str = str(internal_id)

            if internal_id_str in id_to_docno:
                docno = id_to_docno.get(internal_id_str)
                year = "19" + docno[6:8]
                month = docno[2:4]
                day = docno[4:6]
                date = f"{month}/{day}/{year}"

                # Append the result to the results list
                results.append((topic_id, docno, rank, score))
                rank += 1
            else:
                print(f"Key {internal_id_str} not found in id_to_docno dictionary")


# Sort results by topicID (ascending) and rank (ascending)
results.sort(key=lambda x: (int(x[0]), x[2]))

# Write out results
with open(os.path.join(results_path, "hw2-results-j6porter.txt"), "w") as output_file:
    for result in results:
        topic_id, docno, rank, score = result
        output_file.write(f"{topic_id} Q0 {docno} {rank} {score} j6porterAND\n")
