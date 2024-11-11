from langchain_community.document_loaders import PyPDFDirectoryLoader
import backend.utils.common as common

def parse_pdfs(directory:str = common.user_data_folder) -> dict:
    parsed_data = {}
    loader = PyPDFDirectoryLoader(directory, extract_images=True)
    documents = loader.load()
    for page in documents:
        if parsed_data.get(page.metadata["source"]) is None:
            parsed_data[page.metadata["source"]] = [page.page_content]
        else:
            parsed_data[page.metadata["source"]].append(page.page_content)
    return parsed_data