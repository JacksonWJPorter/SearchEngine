import json
import os
import time
import re
import math
from datetime import datetime
import nltk


def tokenize(text):
    tokens = re.findall(r'\w+', text.lower())
    return tokens

def bm25_retrieval(query, inverted_index, lexicon, doc_lengths, avg_doc_length, N, k1=1.2, b=0.75):
    scores = {}

    for term in query:
        if term in lexicon:
            term_postings = inverted_index[lexicon[term]]
            ni = len(term_postings)  # Number of docs containing the term

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
    return sorted_scores[:1000] 

class SearchEngine:
    def __init__(self, data_directory):
        self.data_directory = data_directory
        self.inverted_index = self.load_inverted_index()
        self.avg_doc_length, self.doc_lengths, self.N = self.load_avg_doc_length()
        self.lexicon = self.load_lexicon()
        self.id_to_docno, self.docno_to_id = self.load_mappings()
        self.full_documents = {}

    def load_inverted_index(self):
        with open(os.path.join(self.data_directory, 'inverted_index.json'), 'r') as f:
            return json.load(f)

    def load_avg_doc_length(self):
        with open(os.path.join(self.data_directory, 'doc-lengths.txt'), 'r') as f:
            doc_lengths = [int(line.strip()) for line in f]
            N = len(doc_lengths)
            avg_doc_length = sum(doc_lengths)/N if N else 0
            return avg_doc_length, doc_lengths, N

    def load_lexicon(self):
        with open(os.path.join(self.data_directory, 'Lexicon', 'lexicon_term_to_id.json'), 'r') as f:
            return json.load(f)

    def load_mappings(self):
        with open(os.path.join(self.data_directory, 'id_to_docno.json'), 'r') as f:
            id_to_docno = json.load(f)
        with open(os.path.join(self.data_directory, 'docno_to_id.json'), 'r') as f:
            docno_to_id = json.load(f)
        return id_to_docno, docno_to_id

    def prompt_query(self):
        return input("Enter your query (or type 'Q' to quit): ").strip()

    def search(self, query):
        return bm25_retrieval(tokenize(query), self.inverted_index, self.lexicon,self.doc_lengths, self.avg_doc_length, self.N, k1=1.2, b=0.75)

    def display_results(self, results, query):
        # Pull all info about docs to display
        for rank, (doc_id, _) in enumerate(results[:10], 1):
            docno = self.id_to_docno[str(doc_id)]
            year = "19" + docno[6:8]
            month = docno[2:4]
            day = docno[4:6]

            dir_path = os.path.join(self.data_directory, year, month, day)

            internal_id = self.docno_to_id[docno]
            metadata_file = os.path.join(dir_path, f"{internal_id:04}_metadata.json")
            doc_file = os.path.join(dir_path, f"{internal_id:04}.txt")

            with open(doc_file, 'r') as f:
                full_document = f.read()
            self.full_documents[docno] = full_document

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                docno = metadata['docno']
                internal_id: self.docno_to_id[docno]
                date_numerical = f"{month}/{day}/{year}"
                date_obj = datetime.strptime(date_numerical, "%m/%d/%Y")
                date = f"{date_obj.strftime('%B')} {int(date_obj.strftime('%d'))}, {date_obj.strftime('%Y')}"
                headline = metadata.get('headline', '')

            snippet = self.generate_snippet_from_text(full_document, query)

            # If doc has no headline
            if not headline:
                headline = snippet[:50] + '...'
            
            print(f"{rank}. {headline} ({date})")
            print(f"{snippet} ({docno})\n")


    def generate_snippet_from_text(self, text, query):
        query_terms = set(tokenize(query))
        sentences = nltk.sent_tokenize(text)

        best_snippet = ""
        best_score = float('-inf')

        metadata_end_identifier = "words"  
        main_text_started = False

        for sentence in sentences:
            if metadata_end_identifier in sentence.lower():
                main_text_started = True
                continue  # Skip to next sentence after identifying end of metadata

            if not main_text_started or sentence.isupper() or len(sentence.split()) < 4:
                continue  # Skip metadata, upper case headings, or very short sentences

            sentence_words = set(tokenize(sentence.lower()))
            common_terms = query_terms.intersection(sentence_words)

            if common_terms:
                score = len(common_terms) - 0.1 * sentences.index(sentence)
                if score > best_score:
                    best_snippet = sentence
                    best_score = score

        return best_snippet or "No relevant snippet found."




    def run(self):
        while True:
            query = self.prompt_query()
            if query.lower() == 'q':
                break

            start_time = time.time()
            results = self.search(query)
            self.display_results(results, query)
            print(f"Retrieval took {time.time() - start_time:.02f} seconds.")

            while True:
                user_input = input("Enter rank to view document, 'N' for new query, or 'Q' to quit: ").strip().lower()
                if user_input == 'q':
                    return
                elif user_input == 'n':
                    break
                elif user_input.isdigit():
                    rank = int(user_input)
                    if 1 <= rank <= len(results):
                        doc_id = results[rank - 1][0]
                        docno = self.id_to_docno[str(doc_id)]
                        if docno in self.full_documents:
                            print(self.full_documents[docno])
                    else:
                        print("Invalid rank number. Please input rank 1-10.")
                else:
                    print("Invalid input. Please input try again.")



if __name__ == "__main__":
    data_directory = "/Users/jackson/Desktop/SearchEngineHW5/data"
    engine = SearchEngine(data_directory)
    engine.run()
