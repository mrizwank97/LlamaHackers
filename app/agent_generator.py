import autogen
import utils.parsers as parsers

class AgentGenerator ():

    def __init__(self, llm_config = False):

        api_key = "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"

        config_list = [
            {
                "model": "llama-3.2-90b-text-preview",
                "base_url": "https://api.groq.com/openai/v1/chat/completions",
                "api_type": "groq",
                "api_key": api_key,
                "api_rate_limit": 100
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
    
    def getUserDocParserAgents(self):


        doc_parse_caller = self.getDefaultAgent("Doc Parse Caller",
            "You are a helpful AI assistant. Use the provided python function parse_pdfs(directory), to parse the documents at the directory '../data/'.",
            "A caller for parsing documents")

        doc_parser = self.getDefaultAgent("Doc Parser",
            "You are an executer that parses documents. If you receive a python call instruction, then you execute it, or else ignore the message."
                "Reply TERMINATE afer you execute the python function")
        
        autogen.register_function(
            parsers.parse_pdfs,
            caller=doc_parse_caller,  
            executor=doc_parser,  
            name="parse_pdfs",  
            description="A simple document parser",  # A description of the tool.
        )
    
        return doc_parse_caller, doc_parser
