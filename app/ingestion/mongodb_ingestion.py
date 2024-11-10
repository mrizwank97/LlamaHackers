from pymongo import MongoClient
from app.utils.parsers import parse_pdfs_basic



def main():
    parsed_templates = parse_pdfs_basic(directory="./data/template/")
    mongodb_ingestion(parsed_templates, "template")


def mongodb_ingestion(data, col_name):
    client = MongoClient("mongodb://root:example@localhost:27017/")
    db = client["llamahackers"]
    collection = db[col_name]

    for file_name, parsed_document in data.items():
        document = {"file_name": file_name, "parsed_document": parsed_document}
        collection.insert_one(document)
        print(f"Data inserted for {file_name}.")


if __name__ == "__main__":
    main()