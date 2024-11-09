# Install necessary libraries
# !pip install -U sentence-transformers chromadb

from sentence_transformers import SentenceTransformer
import chromadb
import numpy as np
from minddb import get_data_from_mindb
from embedding_functions import OllamaEmbeddingFunction

from config import load_config

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB client
client = chromadb.HttpClient(host='localhost', port=8000)

# Create or connect to a ChromaDB collection
# collection = client.create_collection("document_embeddings")  # You can use create_collection or get_collection if it already exists
config = load_config()
embedding_function = OllamaEmbeddingFunction(config=config)

collection = client.get_or_create_collection(
        name="document_embeddings_new",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

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
    embeddings = model.encode(chunks)
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
    for doc_id, doc in enumerate(documents):
        # Step 1: Chunk the document
        chunks = chunk_document(doc, max_chunk_size)

        # Step 2: Embed each chunk
        embeddings = embed_chunks(chunks, model)

        # Step 3: Add the chunks and their embeddings to ChromaDB
        # Each chunk gets a unique ID based on document and chunk index
        metadata = [{"document_id": doc_id, "chunk_id": idx, "text": chunk} for idx, chunk in enumerate(chunks)]
        
        collection.add(
            documents=chunks,
            embeddings=embeddings.tolist(),
            metadatas=metadata,
            ids=[f"{doc_id}_{idx}" for idx in range(len(chunks))]  # Unique IDs for each chunk
        )

# Example list of documents
# documents = get_data_from_mindb()

# # # Load documents into ChromaDB
# load_into_chromadb(documents, model, collection, max_chunk_size=500)

# Verify: Retrieve some documents from ChromaDB to check
results = collection.query(query_embeddings=model.encode(["must provide proof that their means of subsistence exceed"]).tolist(), n_results=3)

# results = collection.query(
#     # query_text="803",  # The string you want to match
#     n_results=10,  # Number of results to return
#     where={"content": {"$contains": "803"}}  # Adjust to your specific field name
# )
# Print results
for result in results['documents']:
    print(result)
