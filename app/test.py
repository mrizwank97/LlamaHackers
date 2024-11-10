import os
import autogen
from agent_generator import AgentGenerator
from typing import Annotated, Literal
from datetime import date
import utils.verifiers as verifier_util


def main():

    documents = [
        {
            "name":"Residence Permit",
            "verifier_type" : "Prompt_Verifier",
            "prompt":   f'''
                    Your role is a Residence Permit Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
                    If a key named "Residence Permit" is present in the dictionary, examine its content to verify whether the residence permit is valid beyond today’s date which is {date.today()}. 
                    Provide a precise response indicating whether the residence permit is valid or expired, based on the expiration information in the document. DO NOT use any code to verify the content.
                    '''
        }, 
        {
            "name":"Passport",
            "verifier_type" : "Prompt_Verifier",
            "prompt":   f'''
                    Your role is a Passport Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
                    If a key named "Passport" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date.today()}. 
                    Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the summary content. DO NOT use any code to verify the content.
                    '''
        },
        {   "name": "Enrollment Letter",
            "verifier_type" : "System_Doc_Verifier",
            "template_name": "Template_enrollement.pdf"
        },
        {   "name": "Health Insuarance",
            "verifier_type" : "Prompt_Verifier",
            "prompt":   f'''
                    Your role is a Health Insuarance Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
                    If a key named "Health Insuarance" is present in the dictionary, examine its content to verify whether the document is valid beyond today’s date which is {date.today()}. 
                    Provide a precise response indicating whether the document is valid or expired, based on the expiration information in the summary content. DO NOT use any code to verify the content.
                    '''
        }
    ]

    agent_generator = AgentGenerator()

    user_proxy = agent_generator.getUserProxyAgent()

    doc_parse_caller, doc_parser = agent_generator.getUserDocParserAgents()

    doc_classes = [doc["name"] for doc in documents]
    doc_classes.append('Other')

    classification_prompt = f"""
For each document provided, analyze its content and categorize it into one of the following categories: {doc_classes}."""+ """Your response should strictly follow this dictionary structured format:

{
  "category_name": "<summarized_content>",
}

Always include each key exactly as shown. The category_name field should contain the best matching category from the predefined options, and the summarized_content value should include a summary of the parsed document and keep all the essential information only. 
Adhere precisely to this format of a single dictionary of only string keys and values. DO NOT include file names.
        """

    parsed_doc_classifier = agent_generator.getDefaultAgent("Doc Classifier", classification_prompt, 
                                                     "A classifier that classifies the text that has been parsed")

    chief_verifier = agent_generator.getDefaultAgent("Chief Verifier", "You are the chief verifier."
                   "You collect the information from the Doc Classifier and pass the information to your team.",
                   "You are the chief verifier")


    ## Chat : Initialization (Until Classification of documents)
    groupchat = autogen.GroupChat(
        agents=[user_proxy, doc_parse_caller, doc_parser, parsed_doc_classifier, chief_verifier],
        messages=[],
        max_round=5,
        allowed_or_disallowed_speaker_transitions={
            user_proxy: [doc_parse_caller],
            doc_parse_caller: [doc_parser],
            doc_parser: [parsed_doc_classifier],
            parsed_doc_classifier: [chief_verifier],
            chief_verifier: [user_proxy],
        },
        speaker_transitions_type="allowed",
    )

    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=agent_generator.llm_config)

    ## Generate Verifiers
    verification_chats = []

    for doc in documents:

        match doc['verifier_type']:
            
            case "Prompt_Verifier":
                verifier = agent_generator.getDefaultAgent(doc["name"]+" Verifier", doc["prompt"])

                verification_chats.append({
                    "recipient": verifier,
                    "message": verifier_util.verify_doc,
                    "max_turns": 1,
                    "summary_method": "reflection_with_llm",
                    "summary_args": {"summary_prompt" : 
                        "Return review into as JSON object only:"
                        "{'Agent': 'Verifier Name', 'Verification': '', 'Remarks': ''}."
                        "You should replace the value of Verifier Name with your role name, for example X Reviewer, where X represents the information you are reviewing." 
                        "For the verification, provide a one sentence answer only, and provide the reason for your decision in the remarks key value pair"},
                },)

            case "System_Doc_Verifier":

                system_message = verifier_util.verify_system_doc_sysmessage(doc['name'], doc['template_name'])
            
                verifier = agent_generator.getDefaultAgent(doc["name"]+" Verifier", system_message)
                groupchat2 = autogen.GroupChat(
                    agents=[chief_verifier, doc_parse_caller, doc_parser, verifier],
                    messages=[],
                    max_round=5,
                    allowed_or_disallowed_speaker_transitions={
                        chief_verifier: [doc_parse_caller],
                        doc_parse_caller: [doc_parser],
                        doc_parser: [verifier]
                    },
                    speaker_transitions_type="allowed",
                )

                nested_manager = autogen.GroupChatManager(groupchat=groupchat2, llm_config=agent_generator.llm_config)

                verification_chats.append({
                    "recipient": nested_manager,
                    "message": verifier_util.verify_system_doc_message,
                    "max_turns": 1,
                    "summary_method": "reflection_with_llm",
                    "summary_args": {"summary_prompt" : 
                        "Return review into as JSON object only:"
                        "{'Agent': 'Verifier Name', 'Verification': '', 'Remarks': ''}."
                        "You should replace the value of Verifier Name with your role name, for example X Reviewer, where X represents the information you are reviewing." 
                        "For the verification, provide a one sentence answer only, and provide the reason for your decision in the remarks key value pair"},
                },)
    
    summary_verifier = agent_generator.getDefaultAgent("Verification Summarizer",
                                                       "You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them",
                                                       "Summarizer for all verifications provided"   
                                                       )
    verification_chats.append({
            "recipient": summary_verifier,
            "max_turns": 1,
            "message": "You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them"
        })
    
    chief_verifier.register_nested_chats(verification_chats, trigger = manager)

    result = user_proxy.initiate_chat(
        manager,
        message="I have some pdf documents in the directory '../data/', and I would like to know what type of documents they are (in terms of classification)",
    )





if __name__ == "__main__":
    main()