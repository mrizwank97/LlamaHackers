
import autogen

def user_proxy_agent():
    return autogen.ConversableAgent(
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


def doc_parser_agent(llm_config):
    return autogen.ConversableAgent(
            name="Doc Parse Caller",
            llm_config=llm_config,
            description="A caller for parsing documents",
            system_message="You are a helpful AI assistant. Use the provided python function parse_pdfs(directory), to parse the documents at the directory '../data/'.",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        )
def doc_parser(llm_config):
    return autogen.ConversableAgent(
            name="Doc Parser",
            llm_config=llm_config,
            system_message="You are an executer that parses documents. If you receive a python call instruction, then you execute it, or else ignore the message."
                        "Reply TERMINATE afer you execute the python function",
        )
    
def doc_classifier(llm_config):
    return autogen.ConversableAgent(
            name="Doc Classifier",
            llm_config=llm_config,
            description="A classifier that classifies the text that has been parsed",
            system_message="""
                For each document provided, analyze its content and categorize it into one of the following categories: ['Passport', 'Residence Permit', 'Transaction', 'Health Insurance', 'Other']. Your response should strictly follow this dictionary structured format:

                {
                "category_name": "<summarized_content>",
                }

                Always include each key exactly as shown. The category_name field should contain the best matching category from the predefined options, and the summarized_content value should include a summary of the parsed document and keep all the essential information only. 
                Adhere precisely to this format of a single dictionary of only string keys and values. DO NOT include file names.
                """
        )
    
def chief_verifier_agent(llm_config):
    return autogen.ConversableAgent(
            name="Chief Verifier",
            llm_config=llm_config,
            description="The Chief verifier",
            system_message="You are the chief verifier."
                        "You collect the information from the Doc Classifier and pass the information to your team."
        )
    
    
def create_agent(name, description, system_message, llm_config):
    return autogen.ConversableAgent(
            name = name,
            llm_config = llm_config,
            description = description,
            system_message = system_message
        )