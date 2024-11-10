import os
import argparse
import shutil
import chromadb
from config import load_config
# from langchain.schema.document import Document
from embedding_functions import OllamaEmbeddingFunction
# from langchain_community.document_loaders import PyPDFDirectoryLoader
# from langchain_text_splitters import SentenceTransformersTokenTextSplitter
# import requests
from minddb import get_data_from_mindb
# from langchain_core.documents import Document




    


def main():
    """
    Loads the data and stores the vector embeddings into ChromaDB.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--rm_col", type=str, help="Name of the collection to remove from the database.")

    args = parser.parse_args()

    config = load_config()
    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    embedding_function = OllamaEmbeddingFunction(config=config)

    if args.rm_col is not None:
        remove_collection(chroma_client, args.rm_col)

    # documents = load_docs(path=config.DATA.STORAGE_PATH)
    documents = get_data_from_mindb()
    # docs = [] 
    # for document in documents:
    #     doc_present = Document(page_content=document[0],  metadata={"source": document[1]})
    #     docs.append(doc_present)
    chunks = split_docs(documents, config)
    load_to_db(chroma_client, chunks, embedding_function)


# def load_docs(path):
#     """
#     Loads PDF documents from a directory.
#     """
#     doc_loader = PyPDFDirectoryLoader(path)
#     return doc_loader.load()


def split_docs(docs, config):
    """
    Splits documents semantically into smaller chunks with overlap for context retention.
    """
    from langchain_text_splitters import SentenceTransformersTokenTextSplitter
    txt_splitter = SentenceTransformersTokenTextSplitter(
        model_name=f"sentence-transformers/{config.CHUNKING.MODEL}",
        chunk_size=config.CHUNKING.SIZE,
        chunk_overlap=config.CHUNKING.OVERLAP,
        length_function=len,
    )
    return txt_splitter.split_documents(docs)


def calculate_chunk_ids(chunks):
    """
    Assigns unique IDs to each chunk based on source and page number.
    """
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk.metadata["id"] = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

    return chunks


def load_to_db(chroma_client, chunks, embedding_func):
    """
    Adds document chunks with embeddings to Chroma.
    """
    db = chroma_client.get_or_create_collection(
        name="embeddings",
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )
    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    if new_chunks:
        print(f"Adding new documents: {len(new_chunks)}")
        chunk_dict = {
            "text": [chunk.page_content for chunk in new_chunks], 
            "metadata": [chunk.metadata for chunk in new_chunks], 
            "id": [chunk.metadata["id"] for chunk in new_chunks]
        }

        db.add(
            documents=chunk_dict["text"],
            metadatas=chunk_dict["metadata"],
            ids=chunk_dict["id"],
        )
    else:
        print("No new documents to add.")


def remove_collection(client, col_name):
    """
    Removes the specified ChromaDB collection.
    """
    client.delete_collection(col_name)
    print(f"Removed ChromaDB collection {col_name}.")



if __name__ == "__main__":
    main()