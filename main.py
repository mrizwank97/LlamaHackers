import os
from autogen import AssistantAgent, UserProxyAgent

api_key = os.environ.get("GROQ_API_KEY")

config_list = [
  {
    "model": "llama-3.2-3b-preview",
    "base_url": "https://api.groq.com/openai/v1/chat/completions",
    "api_type": "groq",
    "api_key": api_key,
  }
]

assistant = AssistantAgent("assistant", llm_config={"config_list": config_list})

user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "coding", "use_docker": False})
user_proxy.initiate_chat(assistant, message="Plot a chart of NVDA and TESLA stock price change YTD.")