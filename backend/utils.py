from typing import Dict, List

from langchain_community.document_loaders import PyPDFDirectoryLoader

def parse_pdfs(directory: str = "../data/", extract_images: bool = True) -> Dict[str, List[str]]:
    """
    Parses PDF documents in a specified directory and returns their text content in a structured format.

    Parameters:
    - directory (str): Path to the directory containing PDF files.
    - extract_images (bool): Option to extract images alongside text, if supported by the loader.

    Returns:
    - Dict[str, List[str]]: A dictionary where each key is the PDF file name and each value is a list of strings,
      with each string representing the content of one page in the PDF.
    """
    parsed_data = {}
    
    try:
        # Initialize the loader with the specified directory and extraction options
        loader = PyPDFDirectoryLoader(directory, extract_images=extract_images)
        
        # Load the documents from the directory
        documents = loader.load()
        
        # Parse each page in each document
        for page in documents:
            # Use the source metadata as the key, and aggregate page contents
            source = page.metadata["source"]
            page_content = page.page_content
            
            if parsed_data.get(source) is None:
                parsed_data[source] = [page_content]
            else:
                parsed_data[source].append(page_content)
                
    except Exception as e:
        print(f"An error occurred while parsing PDFs: {e}")
    
    return parsed_data