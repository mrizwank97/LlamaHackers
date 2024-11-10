from __future__ import annotations

import os
import types
from functools import partial
from queue import Queue
from typing import Union, Dict

from autogen import ChatResult, GroupChat, Agent, OpenAIWrapper, ConversableAgent, UserProxyAgent, GroupChatManager
from autogen.code_utils import content_str
from autogen.io import IOStream
from termcolor import colored

import os
import autogen
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders.image import UnstructuredImageLoader
from autogen import register_function
from typing import Annotated, Literal
from datetime import date
# from utils import parse_pdfs


from backend.workflows.agents import AgentGenerator
from backend.utils import verifiers as verifier_util
from backend.prompts import summarizer_prompt, classification_prompt


from typing import Dict, List




def streamed_print_received_message(
        self,
        message: Union[Dict, str],
        sender: Agent,
        queue: Queue,
        index: int,
        *args,
        **kwargs,
):
    streaming_message = ""
    iostream = IOStream.get_default()
    # print the message received
    iostream.print(
        colored(sender.name, "yellow"), "(to", f"{self.name}):\n", flush=True
    )
    streaming_message += f"{sender.name} (to {self.name}):\n"
    message = self._message_to_dict(message)

    if message.get("tool_responses"):  # Handle tool multi-call responses
        if message.get("role") == "tool":
            queue.put(
                {
                    "index": index,
                    "delta": {"role": "assistant", "content": streaming_message},
                    "finish_reason": "stop",
                }
            )

        for tool_response in message["tool_responses"]:
            index += 1
            self._print_received_message(
                message=tool_response,
                sender=sender,
                queue=queue,
                index=index,
                *args,
                **kwargs,
            )

        if message.get("role") == "tool":
            return  # If role is tool, then content is just a concatenation of all tool_responses

    if message.get("role") in ["function", "tool"]:
        if message["role"] == "function":
            id_key = "name"
        else:
            id_key = "tool_call_id"
        id = message.get(id_key, "No id found")
        func_print = f"***** Response from calling {message['role']} ({id}) *****"
        iostream.print(colored(func_print, "green"), flush=True)
        streaming_message += f"{func_print}\n"
        iostream.print(message["content"], flush=True)
        streaming_message += f"{message['content']}\n"
        iostream.print(colored("*" * len(func_print), "green"), flush=True)
        streaming_message += f"{'*' * len(func_print)}\n"
    else:
        content = message.get("content")
        if content is not None:
            if "context" in message:
                content = GroqWrapper.instantiate(
                    content,
                    message["context"],
                    self.llm_config
                    and self.llm_config.get("allow_format_str_template", False),
                )
            iostream.print(content_str(content), flush=True)
            streaming_message += f"{content_str(content)}\n"
        if "function_call" in message and message["function_call"]:
            function_call = dict(message["function_call"])
            func_print = f"***** Suggested function call: {function_call.get('name', '(No function name found)')} *****"
            iostream.print(colored(func_print, "green"), flush=True)
            streaming_message += f"{func_print}\n"
            iostream.print(
                "Arguments: \n",
                function_call.get("arguments", "(No arguments found)"),
                flush=True,
                sep="",
            )
            streaming_message += f"Arguments: \n{function_call.get('arguments', '(No arguments found)')}\n"
            iostream.print(colored("*" * len(func_print), "green"), flush=True)
            streaming_message += f"{'*' * len(func_print)}\n"
        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                id = tool_call.get("id", "No tool call id found")
                function_call = dict(tool_call.get("function", {}))
                func_print = f"***** Suggested tool call ({id}): {function_call.get('name', '(No function name found)')} *****"
                iostream.print(colored(func_print, "green"), flush=True)
                streaming_message += f"{func_print}\n"
                iostream.print(
                    "Arguments: \n",
                    function_call.get("arguments", "(No arguments found)"),
                    flush=True,
                    sep="",
                )
                streaming_message += f"Arguments: \n{function_call.get('arguments', '(No arguments found)')}\n"
                iostream.print(colored("*" * len(func_print), "green"), flush=True)
                streaming_message += f"{'*' * len(func_print)}\n"

    iostream.print("\n", "-" * 80, flush=True, sep="")
    streaming_message += f"\n{'-' * 80}\n"
    queue.put(
        {
            "index": index,
            "delta": {"role": "assistant", "content": streaming_message},
            "finish_reason": "stop",
        }
    )

class DocumentVerificationWorkflow:

    def __init__(self, documents):
        self.queue: Queue | None = None
            
            
        agent_generator = AgentGenerator()

        self.user_proxy = agent_generator.getUserProxyAgent()

        tool_executor = agent_generator.getDefaultAgent("Tool Executor",
                    "You are an executer of python functions. If you receive a python call instruction, then you execute it, or else ignore the message."
                   "Reply TERMINATE afer you execute the python function")

        doc_parse_caller = agent_generator.getUserDocParserAgent(tool_executor)

        doc_classes = [doc["name"] for doc in documents]
        doc_classes.append('Other')

        doc_classification_response = { category : "<content>" for category in doc_classes }
        print(doc_classification_response)

        parsed_doc_classifier = agent_generator.getDefaultAgent("Doc Classifier", classification_prompt.format(doc_classes = doc_classes, response= doc_classification_response), 
                                                        "A classifier that classifies the text that has been parsed")

        chief_verifier = agent_generator.getDefaultAgent("Chief Verifier", "You are the chief verifier."
                   "You collect the information from the Doc Classifier and pass the information to your team.",
                    "You are the chief verifier")


        ## Chat : Initialization (Until Classification of documents)
        groupchat = autogen.GroupChat(
            agents=[self.user_proxy, doc_parse_caller, tool_executor, parsed_doc_classifier, chief_verifier],
            messages=[],
            max_round=5,
            allowed_or_disallowed_speaker_transitions={
                self.user_proxy: [doc_parse_caller],
                doc_parse_caller: [tool_executor],
                tool_executor: [parsed_doc_classifier],
                parsed_doc_classifier: [chief_verifier],
                chief_verifier: [self.user_proxy],
            },
            speaker_transitions_type="allowed",
        )

        self.manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=agent_generator.llm_config)

        ## Generate Verifiers
        verification_chats = []

        base_chat_element = {
                        "max_turns": 1,
                        "summary_method": "reflection_with_llm",
                        "summary_args": {"summary_prompt" : 
                            "Return review into as JSON object only:"
                            "{'Agent': 'Verifier Name', 'Verification': '', 'Remarks': ''}."
                            "You should replace the value of Verifier Name with your role name, for example X Reviewer, where X represents the information you are reviewing." 
                            "For the verification, provide a one sentence answer only, and provide the reason for your decision in the remarks key value pair"},
                    }

        for doc in documents:

            match doc['verifier_type']:
                
                case "Prompt_Verifier":
                    base_chat_element['recipient'] = agent_generator.getDefaultAgent(doc["name"]+" Verifier", doc["prompt"])
                    base_chat_element['message'] = verifier_util.verify_doc

                    verification_chats.append(base_chat_element)

                case "Template_Verifier":

                    system_message = verifier_util.verify_wtemplate_sysmessage(doc['name'])
                
                    verifier = agent_generator.getDefaultAgent(doc["name"]+" Verifier", system_message)

                    template_retrieval_caller = agent_generator.getTemplateRetrieverAgent(tool_executor, doc['template_name'])

                    groupchat2 = autogen.GroupChat(
                        agents=[chief_verifier, template_retrieval_caller, tool_executor, verifier],
                        messages=[],
                        max_round=5,
                        allowed_or_disallowed_speaker_transitions={
                            chief_verifier: [template_retrieval_caller],
                            template_retrieval_caller: [tool_executor],
                            tool_executor: [verifier]
                        },
                        speaker_transitions_type="allowed",
                    )

                    nested_manager = autogen.GroupChatManager(groupchat=groupchat2, llm_config=agent_generator.llm_config)
                    base_chat_element['recipient'] = nested_manager
                    base_chat_element['message'] = verifier_util.verify_system_doc_message

                    verification_chats.append(base_chat_element)
        
        summary_verifier = agent_generator.getDefaultAgent("Verification Summarizer", summarizer_prompt, "Summarizer for all verifications provided"   
                                                        )
        verification_chats.append({
                "recipient": summary_verifier,
                "max_turns": 1,
                "message": "You are the summarizer for all verifications provided. Aggregrate the decisions by the verifications provided and provide a detailed remark for each of them"
            })
        
        chief_verifier.register_nested_chats(verification_chats, trigger = self.manager)

    def set_queue(self, queue: Queue):
        self.queue = queue

    def run(
            self,
            message: str,
            stream: bool = False,
    ) -> ChatResult:

        if stream:
            # currently this streams the entire chat history, but you may want to return only the last message or a
            # summary
            index_counter = {"index": 0}
            queue = self.queue

            def streamed_print_received_message_with_queue_and_index(
                    self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    queue=queue,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            self.manager._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                self.manager,
            )

        chat_history = self.user_proxy.initiate_chat(
            self.manager,
            message="I have some pdf documents in the directory './data/user/', and I would like to know what type of documents they are (in terms of classification)",
        )
        if stream:
            self.queue.put("[DONE]")
        # print(chat_history.chat_history[-1]['content'])
        # currently this returns the entire chat history, but you may want to return only the last message or a summary
        return chat_history
