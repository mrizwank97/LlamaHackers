# Install necessary libraries
# !pip install -U sentence-transformers chromadb

from sentence_transformers import SentenceTransformer
import chromadb
import numpy as np
from minddb import get_data_from_mindb
from embedding_functions import OllamaEmbeddingFunction
from llama_index.core.node_parser import  SemanticSplitterNodeParser
from config import load_config
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document
from chromadb.utils.embedding_functions import huggingface_embedding_function



# Initialize the SentenceTransformer model
# model = SentenceTransformer('all-MiniLM-L6-v2')
model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Initialize ChromaDB client
client = chromadb.HttpClient(host='localhost', port=8000)

# Create or connect to a ChromaDB collection
# collection = client.create_collection("document_embeddings")  # You can use create_collection or get_collection if it already exists
config = load_config()
# import chromadb.utils.embedding_functions as embedding_functions
# huggingface_ef = embedding_functions.HuggingFaceEmbeddingFunction(
embedding_function = huggingface_embedding_function.HuggingFaceEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5", api_key="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")



def remove_collection(client, col_name):
    """
    Removes the specified ChromaDB collection.
    """
    client.delete_collection(col_name)
    print(f"Removed ChromaDB collection {col_name}.")
remove_collection(client , "document_embeddings")
# remove_collection(client , "document_embeddings_new")



collection = client.get_or_create_collection(
        name="document_embeddings",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

document_count = collection.count()

print(document_count)

def chunk_document(text, max_chunk_size=500):
    """
    Splits the document text into chunks of approximately max_chunk_size words.
    Args:
        text (str): The document text.
        max_chunk_size (int): Maximum number of words per chunk.
    Returns:
        list: List of text chunks.
    """
    words = text.split()
    chunks = [' '.join(words[i:i + max_chunk_size]) for i in range(0, len(words), max_chunk_size)]
    return chunks

def embed_chunks(chunks, model):
    """
    Embeds each text chunk using Sentence Transformer model.
    Args:
        chunks (list): List of text chunks.
        model: SentenceTransformer model for embedding.
    Returns:
        list: List of embeddings for each chunk.
    """
    # chunk_list
    # for i in chunks
    # chunks = chunks[1].get_content()
    embeddings = model._get_text_embeddings(chunks)
    return embeddings

def load_into_chromadb(documents, model, collection, max_chunk_size=500):
    """
    Processes a list of documents, chunks them, embeds them, and loads the embeddings into ChromaDB.
    Args:
        documents (list): List of document texts.
        model: SentenceTransformer model for embedding.
        collection: ChromaDB collection to store the embeddings.
        max_chunk_size (int): Maximum number of words per chunk.
    """
    # db = chroma_client.get_or_create_collection(
    #     name="embeddings",
    #     embedding_function=embedding_func,
    #     metadata={"hnsw:space": "cosine"},
    # )
    # for doc_id, doc in enumerate(documents):
        # Step 1: Chunk the document
        # chunks = chunk_document(doc, max_chunk_size)
        
    chunks = SemanticSplitterNodeParser(
        buffer_size=1, breakpoint_percentile_threshold=95, embed_model=model)
    nodes = chunks.get_nodes_from_documents(documents, show_progress=True)
    # Step 2: Embed each chunk
    chunks = [i.get_content() for i in nodes]

    embeddings = embed_chunks(chunks, model)

    # Step 3: Add the chunks and their embeddings to ChromaDB
    # Each chunk gets a unique ID based on document and chunk index
    # metadata = [{"document_id": doc_id, "chunk_id": idx, "text": chunk} for idx, chunk in enumerate(chunks)]
    
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        # metadatas=metadata,
        ids= [str(i) for i in range(len(nodes))]
    )

# Example list of documents
documents, urls = get_data_from_mindb()
# # print(documents[0])
documents = [Document(text=i) for i in documents]

# # # Load documents into ChromaDB
load_into_chromadb(documents, model, collection, max_chunk_size=500)

# Verify: Retrieve some documents from ChromaDB to check
results = collection.query(query_embeddings=model.get_text_embedding("Documents needed for belgium student for a new resident permit"), n_results=20)

# results = collection.query(
#     # query_text="803",  # The string you want to match
#     n_results=10,  # Number of results to return
#     where={"content": {"$contains": "803"}}  # Adjust to your specific field name
# )
# Print results
for result in results['documents']:
    print(result)

