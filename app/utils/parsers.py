import os
from pypdf import PdfReader
from langchain_community.document_loaders import PyPDFDirectoryLoader

def parse_pdfs_basic(directory:str = "./data/template/"):
    parsed_content = {}
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            parsed_content[filename[:-4]] = text

    return parsed_content


def parse_pdfs(directory:str ="../data/") -> dict:
    parsed_data = {}
    loader = PyPDFDirectoryLoader(directory, extract_images=True)
    documents = loader.load()
    for page in documents:
        if parsed_data.get(page.metadata["source"]) is None:
            parsed_data[page.metadata["source"]] = [page.page_content]
        else:
            parsed_data[page.metadata["source"]].append(page.page_content)
    return parsed_data