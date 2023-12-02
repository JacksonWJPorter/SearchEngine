import os
import sys
import json

def get_document(path, search_type, search_value):
    # Load mappings
    with open(os.path.join(path, 'id_to_docno.json'), 'r') as f:
        id_to_docno = json.load(f)
    with open(os.path.join(path, 'docno_to_id.json'), 'r') as f:
        docno_to_id = json.load(f)

    # Find out search value
    if search_type == "id":
        search_value = str(search_value)
        docno = id_to_docno.get(search_value)
        if not docno:
            print("Error: Document with the given ID not found.")
            return
    else:
        docno = search_value

    # Extract year, month, and day from DOCNO
    year = "19" + docno[6:8]
    month = docno[2:4]
    day = docno[4:6]

    # Construct directory path using year, month, and day
    dir_path = os.path.join(path, year, month, day)

    # Construct metadata and document file paths using the id
    internal_id = docno_to_id.get(docno)
    metadata_file = os.path.join(dir_path, f"{internal_id:04}_metadata.json")
    doc_file = os.path.join(dir_path, f"{internal_id:04}.txt")

    if not os.path.exists(metadata_file) or not os.path.exists(doc_file):
        print("Error: Document or metadata not found.")
        return

    # Fetch and display metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
        print(f"docno: {metadata['docno']}")
        print(f"internal id: {docno_to_id[docno]}")
        print(f"date: {month}/{day}/{year}")
        print(f"headline: {metadata.get('headline', '')}")

    # Display raw document
    print("\nraw document:")
    with open(doc_file, 'r') as f:
        print(f.read())

if __name__ == "__main__":

    # Validate commnad line args
    if len(sys.argv) != 4:
        print("Usage: python GetDoc.py <path_to_directory> <'id' or 'docno'> <value>")
        sys.exit(1)

    _, path, search_type, search_value = sys.argv
    if search_type not in ["id", "docno"]:
        print("Error: The third argument must be either 'id' or 'docno'.")
        sys.exit(1)

    # If the search_type is "id", convert the value to an integer
    if search_type == "id":
        try:
            search_value = int(search_value)
        except ValueError:
            print("Error: When searching by 'id', the value must be an integer.")
            sys.exit(1)

    get_document(path, search_type, search_value)
