rp_prompt = """
Your role is a Residence Permit Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
If a key named "Residence Permit" is present in the dictionary, examine its content to verify whether the residence permit is valid beyond today’s date which is {date}. 
Provide a precise response indicating whether the residence permit is valid or expired, based on the expiration information in the document. DO NOT use any code to verify the content.
"""


passport_prompt = """
Your role is a Passport Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
If a key named "Passport" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date}. 
Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the summary content. DO NOT use any code to verify the content.
"""

summarizer_prompt = """You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them"""

classification_prompt = """
    For each document provided, analyze its content and categorize it into one of the following categories: {doc_classes}. Your response should strictly follow this dictionary structured format:

    {{
    "category_name": "<summarized_content>",
    }}

    Always include each key exactly as shown. The category_name field should contain the best matching category from the predefined options, and the summarized_content value should include a summary of the parsed document and keep all the essential information only. 
    Adhere precisely to this format of a single dictionary of only string keys and values. DO NOT include file names.
            """
