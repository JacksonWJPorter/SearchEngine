import sys
import os
import json
from html.parser import HTMLParser
import gzip
import re
from html import unescape
from PorterStemmer import PorterStemmer


class ArticleHandler(HTMLParser):
    def __init__(self):
        super().__init__()
        
        # Flags to keep track of which tags inside
        self.in_doc = False
        self.in_docno = False
        self.in_headline = False
        self.in_text = False
        self.in_graphic = False
        
        # Storage for current / all parsed articles
        self.current_article = {
            'doc_content': '',
            'docno': '',
            'headline': '',
            'text': '',
            'graphic': ''
        }
        self.articles = []

    # Handle start of an HTML tag
    def handle_starttag(self, tag, attrs):
        # Check which tag has been met and update flag
        if tag == 'doc':
            self.in_doc = True 
            self.current_article = {'doc_content': ''}
        elif tag == 'docno':
            self.in_docno = True
        elif tag == 'headline':
            self.in_headline = True
        elif tag == 'text':
            self.in_text = True
        elif tag == 'graphic':
            self.in_graphic = True


    # Handle end of an HTML tag
    def handle_endtag(self, tag):
        # Check which tag has ended and reset correct flag
        if tag == 'doc':
            self.in_doc = False
            self.articles.append(self.current_article)
        elif tag == 'docno':
            self.in_docno = False
        elif tag == 'headline':
            self.in_headline = False
        elif tag == 'text':
            self.in_text = False
        elif tag == 'graphic':
            self.in_graphic = False

    # Handle content/data between start and end tags
    def handle_data(self, data):
        self.current_article['doc_content'] += data
        # Append data to current article's content based on current tag
        if self.in_docno:
            self.current_article['docno'] = data.strip()
        elif self.in_headline:
            self.current_article.setdefault('headline', '')
            self.current_article['headline'] += data.strip() + " "
        elif self.in_text:
            self.current_article.setdefault('text', '')
            self.current_article['text'] += data.strip() + " "
        elif self.in_graphic:
            self.current_article.setdefault('graphic', '')
            self.current_article['graphic'] += data.strip() + " "

# Read latimes.gz line by line
def read_gz_file(file_path):
    with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            yield line

# Dictionaries to map doc numbers to internal IDs and vice-versa, store doc lengths, inverted index
docno_to_id = {}
id_to_docno = {}
doc_lengths = {}
inverted_index = []
term_id_to_index = {}

class Lexicon:
    def __init__(self):
        self.term_to_id = {}
        self.id_to_term = {}
        self.current_id = 0

    def get_id(self, term):
        if term not in self.term_to_id:
            self.term_to_id[term] = self.current_id
            self.id_to_term[self.current_id] = term
            self.current_id += 1
        return self.term_to_id[term]

    def get_term(self, term_id):
        return self.id_to_term.get(term_id)

    # Saving Lexicon
    def save_lexicon_term_to_id(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.term_to_id, f)

    def save_lexicon_id_to_term(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.id_to_term, f)

lexicon = Lexicon()

# Tokenization Function
def tokenize(text):
    tokens = re.findall(r'\w+', text.lower())
    return tokens

porter_stemmer = PorterStemmer()

# Tokenization and stemming function
def tokenize_and_stem(text):
    tokens = tokenize(text)
    stemmed_tokens = [porter_stemmer.stem(token, 0, len(token) - 1) for token in tokens]
    term_ids = [lexicon.get_id(token) for token in stemmed_tokens]
    return term_ids

# Update inverted index function (modified for stemmed tokens)
def update_index(internal_id, term_ids):
    term_frequencies = {}
    for term_id in term_ids:
        term_frequencies[term_id] = term_frequencies.get(term_id, 0) + 1

    for term_id, term_frequency in term_frequencies.items():
        if term_id in term_id_to_index:
            index = term_id_to_index[term_id]
        else:
            index = len(inverted_index)
            term_id_to_index[term_id] = index
            inverted_index.append([])

        inverted_index[index].append((internal_id, term_frequency))

def save_article_to_directory(article, output_directory, internal_id):
    docno = article['docno']
    year = "19" + docno[6:8]
    month = docno[2:4]
    day = docno[4:6]
    date = f"{month}/{day}/{year}"

    # Creating the directory path
    dir_path = os.path.join(output_directory, year, month, day)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Tokenize text from TEXT, HEADLINE, GRAPHIC
    full_text = unescape(re.sub(r'<.*?>', '', article.get('text', '') + article.get('headline', '') + article.get('graphic', '')))
    term_ids = tokenize_and_stem(full_text)

    # Saving the article's content to a .txt file
    doc_path = os.path.join(dir_path, f"{internal_id:04}.txt")
    with open(doc_path, 'w') as f:
        f.write(article['doc_content'])


    # Saving the article's metadata to a .json file
    metadata_path = os.path.join(dir_path, f"{internal_id:04}_metadata.json")
    metadata = {
        'docno': article['docno'],
        'date': date,
        'headline': article.get('headline', '')
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)

    # Update document length in dictionary
    doc_lengths[internal_id] = len(term_ids)

    # Updating document number to ID mapping
    docno_to_id[article['docno']] = internal_id
    id_to_docno[internal_id] = article['docno']

    update_index(internal_id, term_ids)

    return doc_path


def main():
    # Ensuring correct number of arguments
    if len(sys.argv) != 3:
        print("Usage: python IndexEngine.py <path_to_latimes.gz> <path_to_output_directory>")
        sys.exit(1)

    file_path = sys.argv[1]
    output_directory = sys.argv[2]

    # Check if output directory already exists
    if os.path.exists(output_directory):
        print("Error: Oops! Output directory already exists!")
        sys.exit(1)
    else:
        os.makedirs(output_directory)

    # HTML parser
    handler = ArticleHandler()

    for line in read_gz_file(file_path):
        handler.feed(line)

    # Saving each parsed article to corresponding output_directory
    internal_id = 1
    for article in handler.articles:
        save_article_to_directory(article, output_directory, internal_id)
        internal_id += 1

    # Saving document number to ID mappings
    with open(os.path.join(output_directory, "docno_to_id.json"), 'w') as f:
        json.dump(docno_to_id, f)
    with open(os.path.join(output_directory, "id_to_docno.json"), 'w') as f:
        json.dump(id_to_docno, f)
    
    # Saving document lengths
    with open(os.path.join(output_directory, "doc-lengths.txt"), 'w') as f:
        for internal_id, length in doc_lengths.items():
            f.write(f"{length}\n")

    # Saving inverted index
    with open(os.path.join(output_directory, "inverted_index.json"), 'w') as f:
        json.dump(inverted_index, f)
    
    # Saving lexicon
    if not os.path.exists("/Users/jackson/Desktop/SearchEngineHW4/dataHW4/Lexicon"):
        os.makedirs("/Users/jackson/Desktop/SearchEngineHW4/dataHW4/Lexicon")

    lexicon.save_lexicon_term_to_id(os.path.join(output_directory, "Lexicon", "lexicon_term_to_id.json"))
    lexicon.save_lexicon_id_to_term(os.path.join(output_directory, "Lexicon", "lexicon_id_to_term.json"))


if __name__ == "__main__":
    main()
