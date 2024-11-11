exp_doc_prompt = """
Your role is a {doc_name} Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
If a key named "{doc_name}" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date}. 
Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the document. DO NOT use any code to verify the content.
"""



# passport_prompt = """
# Your role is a {doc_name} Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
# If a key named "{doc_name}" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date}. 
# Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the summary content. DO NOT use any code to verify the content.
# """

summarizer_prompt = """You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them"""


# classification_prompt = """For each document provided, analyze its content and assign it to one of the following categories: ['Passport', 'Residence Permit', 'Transaction', 'Health Insurance', 'Education Registration Certificate', 'Other']. The output should be a dictionary. The dictionary format should follow below guidelines

# Guidelines:
# 1. Use the  dictonary key to indicate the best matching category from the list.
# 2. For the <content> field:
#    - If the key is 'Education Registration Certificate', include the full parsed document content.
#    - For all other categories, provide a summary that captures all essential details of the document.

# Output
# Your response must strictly follow the dictionary structure below:

# {{
#   "Passport": <content>,
#   "Transaction": <content>,
#   "Residence Permit": <content>,
#   "Health Insurance": <content>,
#   "Education Registration Certificate": <content>,
#   "Other": <content>,
# }}"""

classification_prompt = """For each document provided, analyze its content and assign it to one of the following categories: {doc_classes}. The output should be a dictionary. The dictionary format should follow below guidelines

Guidelines:
1. Use the  dictonary key to indicate the best matching category from the list.
2. For the <content> field:
   - If the key is 'Education Registration Certificate', include the full parsed document content.
   - For all other categories, provide a summary that captures all essential details of the document.

Output
Your response must strictly follow the dictionary structure below:

{response}"""

# health_insurance_prompt = '''
#                 Your role is a Health Insuarance Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
#                 If a key named "Health Insuarance" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date}. 
#                 Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the summary content. DO NOT use any code to verify the content.
#                 '''


ps_prompt = '''
Your role is a {doc_name} Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
If a key named "{doc_name}" is present in the dictionary, examine its content to verify whether the user has a subsistence of more than {doc_name} euros. 
Provide a precise response indicating whether the user has enough subsistence. DO NOT use any code to verify the content.
'''