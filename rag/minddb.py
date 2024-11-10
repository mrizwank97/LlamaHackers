import requests
import re

def clean_data(html_content):
    # print(html_content)
    # Define the start of the relevant content (from first heading #)
    start_pattern = re.compile(r"# .*", re.IGNORECASE)
    end_pattern = re.compile(r"## Sidebar navigation|© DOFI 2024", re.IGNORECASE)

    # Find the starting and ending indexes of the relevant content
    start_match = start_pattern.search(html_content)
    end_match = end_pattern.search(html_content)
    # Extract the content from start to end
    if start_match or end_match:
        start_index = start_match.start()
        end_index = end_match.start()

        # Return the cleaned content
        return html_content[start_index:end_index].strip()

    return html_content

def get_data_from_mindb(url="http://127.0.0.1:47334/api/sql/query"):
    resp = requests.post(url, json={'query':
                    """SELECT text_content, url FROM my_web.crawler  where url='https://dofi.ibz.be/en'  LIMIT 100"""})
    data = resp.json()["data"]
    # from langchain.schema.document import Document

    docs = []
    # for i in data:
    #     docs = [] 
    url = []
    for document in data:
        # doc_present = Document(page_content=document[0],  metadata={"source": document[1]})
        document[0] = clean_data(document[0])
        docs.append(document[0])
        url.append(document[1])

    return docs, url

