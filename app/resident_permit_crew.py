import os
import autogen
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders.image import UnstructuredImageLoader
from autogen import register_function
from typing import Annotated, Literal
from datetime import date

def main():

    api_key = os.environ.get("GROQ_API_KEY")

    config_list = [
    {
        "model": "llama-3.2-90b-text-preview",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "api_type": "groq",
        "api_key": api_key,
        "api_rate_limit": 100
    }
    ]

    llm_config={"config_list": config_list}


    user_proxy = autogen.ConversableAgent(
        name="User",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",
        # max_consecutive_auto_reply=10,
        # code_execution_config={
        #     "work_dir": "code",
        #     "use_docker": False
        # },
        llm_config=False,
    )

    doc_parse_caller = autogen.ConversableAgent(
        name="Doc Parse Caller",
        llm_config=llm_config,
        description="A caller for parsing documents",
        system_message="You are a helpful AI assistant. Use the provided python function parse_pdfs(directory), to parse the documents at the directory '../data/'.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    )

    doc_parser = autogen.ConversableAgent(
        name="Doc Parser",
        llm_config=llm_config,
        system_message="You are an executer that parses documents. If you receive a python call instruction, then you execute it, or else ignore the message."
                    "Reply TERMINATE afer you execute the python function",
    )

    cls_prompt = """
    For each document provided, analyze its content and categorize it into one of the following categories: ['Passport', 'Residence Permit', 'Transaction', 'Health Insurance', 'Other']. Your response should strictly follow this dictionary structured format:

    {
    "category_name": "<summarized_content>",
    }

    Always include each key exactly as shown. The category_name field should contain the best matching category from the predefined options, and the summarized_content value should include a summary of the parsed document and keep all the essential information only. 
    Adhere precisely to this format of a single dictionary of only string keys and values. DO NOT include file names.
    """

    doc_classifier = autogen.ConversableAgent(
        name="Doc Classifier",
        llm_config=llm_config,
        description="A classifier that classifies the text that has been parsed",
        system_message=cls_prompt
    )

    chief_verifier = autogen.ConversableAgent(
        name="Chief Verifier",
        llm_config=llm_config,
        description="The Chief verifier",
        system_message="You are the chief verifier."
                    "You collect the information from the Doc Classifier and pass the information to your team."
    )

    # health_insurance_verifier = autogen.ConversableAgent(
    #     name="Health Insurance Verifier",
    #     llm_config=llm_config,
    #     description="A verifier that checks if health insurance is still valid",
    #     system_message="You are a helpful AI assistant."
    #                    "If there exists a Health Insurance key in the dictionary received, then check its corresponding parsed document to see if the validity of the insurance is beyond today."
    #                 #    "Reply TERMINATE when the task is done.",
    # )

    rp_prompt = f'''
    Your role is a Residence Permit Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
    If a key named "Residence Permit" is present in the dictionary, examine its content to verify whether the residence permit is valid beyond today’s date which is {date.today()}. 
    Provide a precise response indicating whether the residence permit is valid or expired, based on the expiration information in the document. DO NOT use any code to verify the content.
    '''

    passport_prompt = f'''
    Your role is a Passport Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
    If a key named "Passport" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date.today()}. 
    Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the summary content. DO NOT use any code to verify the content.
    '''

    rp_verifier = autogen.ConversableAgent(
        name="Residence Permit Verifier",
        llm_config=llm_config,
        description="A verifier that checks if residence permit is still valid",
        system_message=rp_prompt
    )

    passport_verifier = autogen.ConversableAgent(
        name="Passport Verifier",
        llm_config=llm_config,
        description="A verifier that checks passport validity",
        system_message=passport_prompt
    )

    summary_verifier = autogen.ConversableAgent(
        name="Verification Summarizer",
        llm_config=llm_config,
        description="Summarizer for all verifications provided",
        system_message="You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them",
    )

    register_function(
        parse_pdfs,
        caller=doc_parse_caller,  
        executor=doc_parser,  
        name="parse_pdfs",  
        description="A simple document parser",  # A description of the tool.
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, doc_parse_caller, doc_parser, doc_classifier, chief_verifier],
        messages=[],
        max_round=5,
        allowed_or_disallowed_speaker_transitions={
            user_proxy: [doc_parse_caller],
            doc_parse_caller: [doc_parser],
            doc_parser: [doc_classifier],
            doc_classifier: [chief_verifier],
            # chief_verifier: [passport_verifier, rp_verifier],
            chief_verifier: [user_proxy],
        },
        speaker_transitions_type="allowed",
    )

    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    def verify_doc(recipient, messages, sender, config):
        return f'''Verify the following content. 
                \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}'''

    chief_verifier.register_nested_chats(
        [
            {
                "recipient": rp_verifier,
                "message": verify_doc,
                "max_turns": 1,
                "summary_method": "reflection_with_llm",
                "summary_args": {"summary_prompt" : 
                    "Return review into as JSON object only:"
                    "{'Agent': 'Verifier Name', 'Verification': '', 'Remarks': ''}."
                    "You should replace the value of Verifier Name with your role name, for example X Reviewer, where X represents the information you are reviewing." 
                    "For the verification, provide a one sentence answer only, and provide the reason for your decision in the remarks key value pair"},
            },
            {
                "recipient": passport_verifier,
                "message": verify_doc,
                "max_turns": 1,
                "summary_method": "reflection_with_llm",
                "summary_args": {"summary_prompt" : 
                    "Return review into as JSON object only:"
                    "{'Agent': 'Verifier Name', 'Verification': '', 'Remarks': ''}."
                    "You should replace the value of Verifier Name with your role name, for example X Reviewer, where X represents the information you are reviewing." 
                    "For the verification, provide a one sentence answer only, and provide the reason for your decision in the remarks key value pair"},
            },
            {
                "recipient": summary_verifier,
                "max_turns": 1,
                "message": "You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them"
            },
        ],
        trigger=manager,  # condition=my_condition,
    )

    result = user_proxy.initiate_chat(
        manager,
        message="I have some pdf documents in the directory '../data/', and I would like to know what type of documents they are (in terms of classification)",
    )


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



if __name__ == "__main__":
    # main()
    print(os.getcwd())



