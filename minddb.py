import requests

def get_data_from_mindb(url="http://127.0.0.1:47334/api/sql/query"):
    resp = requests.post(url, json={'query':
                    """SELECT text_content FROM my_web.crawler  where url='https://dofi.ibz.be/en'  LIMIT 100"""})
    data = resp.json()["data"]
    # from langchain.schema.document import Document

    docs = []
    # for i in data:
    #     docs = [] 
    for document in data:
        # doc_present = Document(page_content=document[0],  metadata={"source": document[1]})
        docs.append(document[0])
    return docs