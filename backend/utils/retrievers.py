from pymongo import MongoClient

def get_template_doc(file_name:str) -> str:
    client = MongoClient("mongodb://root:example@localhost:27017/")
    db = client["llamahackers"]
    collection = db["template"]
    
    document = collection.find_one({'file_name': file_name})
    
    if document:
        return document.get('parsed_document', None)
    else:
        return None