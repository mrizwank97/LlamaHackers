from pymongo import MongoClient

client = MongoClient("mongodb://root:example@localhost:27017/")

db = client["mydatabase"]
collection = db["mycollection"]

data = {"name": "Alice", "age": 30, "city": "New York"}
collection.insert_one(data)

result = collection.find_one({"name": "Alice"})
print(result)
