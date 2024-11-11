import os
import autogen
import backend.utils.parsers as parsers
import backend.utils.retrievers as retrievers
import backend.utils.common as common

class AgentGenerator ():

    def __init__(self, llm_config = False):

        # TODO : Remove
        api_key = os.environ.get("GROQ_API_KEY")

        config_list = [
            {
                "model": "llama-3.2-90b-text-preview",
                "base_url": "https://api.groq.com/openai/v1/",
                "api_type": "groq",
                "api_key": api_key,
                # "api_rate_limit": 100
            }
        ]

        if llm_config:
            self.llm_config = llm_config
        else: 
            self.llm_config = {"config_list": config_list}

    
    def getUserProxyAgent(self):

        return autogen.ConversableAgent(
            name="User",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="NEVER",
            llm_config=False,
        )   

    def getDefaultAgent(self, name, system_message, description = None):

        return autogen.ConversableAgent(
            name=name,
            llm_config=self.llm_config,
            system_message = system_message,
            description = description
        )  
    
    def getUserDocParserAgent(self, tool_executor):


        doc_parse_caller = self.getDefaultAgent("Doc Parse Caller",
            f"""You are a python function caller. Use the provided python function parse_pdfs(directory), where the directory is '{common.user_data_folder}'. Reply with the python function call.""",
            "A caller for parsing documents")
        
        autogen.register_function(
            parsers.parse_pdfs,
            caller=doc_parse_caller,  
            executor=tool_executor,  
            name="parse_pdfs",  
            description="A simple document parser",  # A description of the tool.
        )
    
        return doc_parse_caller
    
    def getTemplateRetrieverAgent(self, tool_executor, file_name):


        template_retriever_caller = self.getDefaultAgent("Doc Retreival Caller",
            f'''You are a helpful AI assistant. Use the provided python function get_template_doc(file_name), where filename is {file_name}.''',
            "A caller for retreiving documents")
        
        autogen.register_function(
            retrievers.get_template_doc,
            caller=template_retriever_caller,  
            executor=tool_executor,  
            name="get_template_doc",  
            description="A simple document retreiver",  # A description of the tool.
        )
    
        return template_retriever_caller
