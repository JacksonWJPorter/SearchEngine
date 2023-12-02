import argparse
import numpy as np

# Based on code by Mark D. Smucker and Nimesh Ghelani.

class QrelsParser:
    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        qrels_data = {}
        with open(self.filename, 'r') as file:
            for line in file:
                parts = line.strip().split()
                topic_id, _, docno, relevance = parts
                topic_id = int(topic_id)
                relevance = int(relevance)
                if topic_id not in qrels_data:
                    qrels_data[topic_id] = {}
                qrels_data[topic_id][docno] = relevance
        return qrels_data

class ResultsParser:
    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        results_data = {}
        with open(self.filename, 'r') as file:
            for line in file:
                parts = line.strip().split()
                topic_id, _, docno, rank, score, _ = parts
                topic_id = int(topic_id)
                rank = int(rank)
                score = float(score)
                if topic_id not in results_data:
                    results_data[topic_id] = [] 
                results_data[topic_id].append((topic_id, rank, docno, score))
        return results_data


def compute_average_precision(relevant_docs, retrieved_docs):
    # Calculate Average Precision
    precision_values = []
    relevant_count = 0
    for i, doc in enumerate(retrieved_docs):
        if doc in relevant_docs:
            relevant_count += 1
            precision_at_i = relevant_count / (i + 1)
            precision_values.append(precision_at_i)
    if not precision_values:
        return 0.0  # No relevant docs retrieved
    return sum(precision_values) / len(relevant_docs)

def compute_precision_at_k(relevant_docs, retrieved_docs, k):
    # Calculate Precision@k
    if not retrieved_docs:
        return 0.0
    relevant_count = sum(1 for doc in retrieved_docs[:k] if doc in relevant_docs)
    return relevant_count / k

def compute_ndcg(relevant_docs, retrieved_docs, k):
    # Calculate NDCG@k
    ideal_dcg = sum(1 / np.log2(i + 2) for i in range(min(k, len(relevant_docs))))
    dcg = sum(1 / np.log2(i + 2) if doc in relevant_docs else 0 for i, doc in enumerate(retrieved_docs[:k]))
    if ideal_dcg == 0:
        return 0.0
    return dcg / ideal_dcg

def main():
    # Command line parsing
    parser = argparse.ArgumentParser(description='Calculate evaluation scores for a given results file and qrels file')
    parser.add_argument('--qrel', required=True, help='Path to qrels file')
    parser.add_argument('--results', required=True, help='Path to results file')
    parser.add_argument('--output', required=True, help='Path to output file')
    parser.add_argument('--k', type=int, required=True, help='Value of k for Precision@k and NDCG@k')

    args = parser.parse_args()
    qrel_parser = QrelsParser(args.qrel)
    results_parser = ResultsParser(args.results)

    qrels_data = qrel_parser.parse()
    results_data = results_parser.parse() 

    # Loop through evaluation measures and topics
    with open(args.output, 'w') as output_file:
        for metric in ['ap', 'p_at_10', 'ndcg_at_10', 'ndcg_at_1000']:
            for topic_id in range(401, 451):
                if topic_id not in [416, 423, 437, 444, 447]:
                    relevant_docs = [docno for docno, relevance in qrels_data.get(topic_id, {}).items() if relevance == 1]
                    retrieved_docs = [doc[2] for doc in results_data.get(topic_id, [])]
                    score_retrieved_docs = results_data.get(topic_id, []) 
                    if not retrieved_docs:
                        print(f"No results found for topic {topic_id}")
                        ap = 0.0
                        precision_at_k = 0.0
                        ndcg_at_k = 0.0
                        ndcg_at_1000 = 0.0
                    else:
                        # Sort by score first, if not then docno in lexicographical order
                        score_retrieved_docs.sort(key=lambda x: (float(x[3]), x[2]), reverse=True)

                        if metric == 'ap':
                            ap = compute_average_precision(relevant_docs, retrieved_docs)
                        elif metric == 'p_at_10':
                            precision_at_k = compute_precision_at_k(relevant_docs, retrieved_docs, 10)
                        elif metric == 'ndcg_at_10':
                            ndcg_at_k = compute_ndcg(relevant_docs, retrieved_docs, 10)
                        elif metric == 'ndcg_at_1000':
                            ndcg_at_1000 = compute_ndcg(relevant_docs, retrieved_docs, 1000)

                    if metric == 'ap':
                        output_file.write(f"{metric}\t{topic_id}\t{ap:.4f}\n")
                    elif metric == 'p_at_10':
                        output_file.write(f"{metric}\t{topic_id}\t{precision_at_k:.4f}\n")
                    elif metric == 'ndcg_at_10':
                        output_file.write(f"{metric}\t{topic_id}\t{ndcg_at_k:.4f}\n")
                    elif metric == 'ndcg_at_1000':
                        output_file.write(f"{metric}\t{topic_id}\t{ndcg_at_1000:.4f}\n")

if __name__ == '__main__':
    main()
