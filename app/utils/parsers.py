import os
from pypdf import PdfReader

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