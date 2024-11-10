import argparse
import ollama
import chromadb
from config import load_config
# from langchain.prompts import ChatPromptTemplate
from embedding_functions import OllamaEmbeddingFunction
from chromadb.utils.embedding_functions import huggingface_embedding_function



# PROMPT_TEMPLATE = """
# Answer the question based only on the following context:

# {context}

# ---

# Answer the question based on the above context: {question}
# """

from groq import Groq

client = Groq(api_key="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")

def main():
    """
    Prompts the LLM model to answer user query with RAG based context.
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    # query_text = args.query_text
    query_text = input("query text: ")
    config = load_config()
    
    query_rag(query_text, config)


histories = {"rizwan"= [], "prasjant" [], "zgvf"}



PROMPT_TEMPLATE = """
Answer the below question using only the context documents. If the information is not present do not respond with wrong answers. and only give me the anser, if you have question you can ask the user. Try to be helpul

Question:
{question}

Context:
{context}

Answer:
"""



def query_rag(config):
    """
    Performs similarity search with ChromaDB embeddings for RAG-based query.
    Appends conversation history and runs continuously unless stopped manually.
    """
    embedding_function = huggingface_embedding_function.HuggingFaceEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5", api_key="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"
    )
    
    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    db = chroma_client.get_collection(
        name="document_embeddings",
        embedding_function=embedding_function
    )
    
    history = []  # List to keep track of conversation history
    
    while True:  # Infinite loop
        query_text = input("Enter your query (type 'exit' to stop): ")
        
        if query_text.lower() == "exit":
            print("Stopping the conversation...")
            break  # Exit the loop if 'exit' is typed
        
        results = db.query(
            query_texts=[query_text],
            n_results=10
        )
        
        # print("Results:", results)
        
        context_text = "Answer the below question using only the context documents. If the information is not present do not respond with wrong answers. and only give me the anser, if you have question you can ask the user. Try to be helpul\n\n--\n\n".join([result for i, result in enumerate(results['documents'][0])])
        prompt = f"{context_text}\n\n--\n\n" + "\n".join([f"User: {entry['user']}\nAI: {entry['ai']}" for entry in history]) + f"\nUser: {query_text}\nAI:"
        
        
        response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "I want to apply for card",
            },
            {
                ""
            }
        ],
        model="llama-3.2-11b-text-preview",
        stream=False,
    )
        
        answer = response.choices[0].message.content
        print("AI Response:"q, answer)
        
        # Append the new user input and AI response to the history
        history.append({"user": query_text, "ai": answer})

        print("-----")

# Call the function with your config
query_rag(config={})