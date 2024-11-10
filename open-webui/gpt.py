from typing import Optional, Callable, Awaitable, Dict, Any, List, Union
from typing import List, Union, Generator, Iterator
import aiohttp
import json
import urllib.parse
import time
import asyncio
from pydantic import BaseModel, Field
import chromadb
from chromadb.utils.embedding_functions import huggingface_embedding_function
import requests
import os
import shutil
import time


class Pipe:
    """Pipeline for managing interactions with the AutoGen endpoint."""

    class Valves(BaseModel):
        AUTOGEN_BASE_URL: str = Field(
            default="http://localhost:8082/predict",
            description="Base URL for the AutoGen endpoint.",
        )
        emit_interval: float = Field(
            default=1.0, description="Interval in seconds between status emissions."
        )
        enable_status_indicator: bool = Field(
            default=True, description="Enable or disable status indicator emissions."
        )
        request_timeout: int = Field(
            default=300, description="Timeout for the HTTP client session in seconds."
        )
        debug: bool = Field(
            default=False, description="Enable or disable debug logging."
        )
        history_length: int = Field(
            default=1,
            description="Number of messages to include from the chat history, starting from the most recent. Default is 1, which includes the user's message and the previous assistant message if available.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.stop_emitter = asyncio.Event()

    async def emit_periodic_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        message: str,
        interval: float,
    ):
        """Emit status updates periodically until the stop event is set."""
        start_time = time.time()
        try:
            while not self.stop_emitter.is_set():
                elapsed_time = time.time() - start_time
                await self.emit_status(
                    __event_emitter__,
                    "info",
                    f"{message} (elapsed: {elapsed_time:.1f}s)",
                    False,
                )
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            if self.valves.debug:
                print("[DEBUG] Periodic status emitter cancelled.")

    async def inlet(self, body: dict, user: dict) -> dict:
        """Modifies form data before the OpenAI API request."""
        logger.info("Processing inlet request")

        # Extract file info for all files in the body
        # here i have created an inmemory dictionary to link users to their owned files
        print()
        print("I am body", body)
        print("I am user", user)
        file_info = self._extract_file_info(body)
        self.file_contents[user["id"]] = file_info
        return body

    def _extract_file_info(self, body: dict) -> list:
        """Extracts the file info from the request body for all files."""
        files = []
        for file_data in body.get("files", []):
            file = file_data["file"]
            file_id = file["id"]
            filename = file["filename"]
            file_content = file["data"]["content"]
            print(filename, file_id, file)
            print(file_content)

            # Create a OIFile object and append it to the list
            files.append(OIFile(file_id, filename, file_content))

        return files

    async def pipe(
        self,
        body: dict,
        # user: dict,
        __task__: None,
        session_id=None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Main handler for the AutoGen API interactions."""
        status_task = None
        start_time = time.time()
        try:
            # Start emitting status updates periodically
            if __event_emitter__ and self.valves.enable_status_indicator:
                self.stop_emitter.clear()
                status_task = asyncio.create_task(
                    self.emit_periodic_status(
                        __event_emitter__,
                        "Processing request to AutoGen endpoint...",
                        self.valves.emit_interval,
                    )
                )

            # Extract messages and prepare prompt
            messages = body.get("messages", [])
            self.move_new_files_in_last_minute(
                "/app/backend/data/uploads", "/app/backend/data/master_repo"
            )
            if not messages:
                return {"error": "No messages found in the request body"}

            # Combine messages to form a prompt
            prompt = self._get_combined_prompt(messages)

            # Prepare and make the API request
            response = await self.call_groq_api(prompt)

            # Extract content from the response
            # extracted_content = self._extract_content(response)

            # Emit completed status with elapsed time
            elapsed_time = time.time() - start_time
            self.emit_status(
                __event_emitter__,
                "info",
                f"Autogen - Pipe Completed (elapsed: {elapsed_time:.1f}s)",
                True,
            )

            return response

        except Exception as e:
            # Emit error status
            await self.emit_status(__event_emitter__, "error", f"Error: {str(e)}", True)
            if self.valves.debug:
                print(f"[DEBUG] Error during pipe: {e}")
            return {"error": str(e)}

        finally:
            # Stop the periodic status emitter
            if status_task:
                self.stop_emitter.set()
                await status_task

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        """Emit status updates at configured intervals."""
        if __event_emitter__:
            event = {
                "type": "status",
                "data": {"description": message, "done": done},
            }
            if self.valves.debug:
                print(f"[DEBUG] Emitting status event: {event}")
            await __event_emitter__(event)

    def _get_combined_prompt(self, messages: List[Dict[str, str]], id=None) -> str:
        """Combine the user's message and previous assistant messages based on the history length."""
        prompt_parts = []

        # Determine how many messages to include based on the valve setting
        history_length = (
            self.valves.history_length * 2
        )  # Each user message is paired with an assistant message
        recent_messages = (
            messages[-history_length:] if history_length < len(messages) else messages
        )
        last_message = messages[-1]
        chroma_extract = None
        if last_message.get("role", "assistant") == "user":
            # chroma_extract = self._chroma_extract(last_message.get("content", ""))
            url = "http://localhost:8000/extract"
            payload = {"query": last_message.get("content", "")}
            # Make the POST request
            response = requests.post(url, json=payload)
            chroma_extract = response.json()["context"]

        # Iterate through messages to form a cohesive prompt with roles labeled
        for message in recent_messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        # Join all parts with newlines to form the full prompt
        # combined_prompt =""
        combined_prompt = chroma_extract + "\n\n\n".join(prompt_parts)
        if self.valves.debug:
            print(f"[DEBUG] Combined prompt: {combined_prompt}")
        return combined_prompt

    async def call_autogen_api(self, prompt: str) -> str:
        """Make an asynchronous call to the AutoGen API."""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.valves.request_timeout)
        ) as session:
            url = f"{self.valves.AUTOGEN_BASE_URL}/{urllib.parse.quote(prompt)}"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self.valves.debug:
                print(f"[DEBUG] Calling API at: {url}")
                print(f"[DEBUG] Headers: {headers}")

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.text()
                    if self.valves.debug:
                        print(f"[DEBUG] API Response: {data}")
                    return data
                else:
                    raise ValueError(f"API call failed with status {response.status}")

    async def call_groq_api(self, prompt) -> str:
        # Send the prompt to the Groq API
        from groq import Groq

        client = Groq(
            api_key="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"
        )

        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt},
            ],
            model="llama-3.2-11b-text-preview",
            stream=False,
        )

        answer = response.choices[0].message.content
        return answer

    def _extract_content(self, response: str) -> str:
        """Extract the content from the API response."""
        try:
            data = json.loads(response)
            meta = data.get("data", {}).get("meta", {})
            messages = meta.get("messages", [])

            if len(messages) > 1:
                last_message = messages[-2].get("message", {}).get("content", "")
                if self.valves.debug:
                    print(f"[DEBUG] Extracted content: {last_message}")
                return last_message
            else:
                return "No valid content found in response"
        except json.JSONDecodeError as e:
            if self.valves.debug:
                print(f"[DEBUG] JSON parsing error: {e}")
            return "Error extracting content due to JSON parsing error"
        except Exception as e:
            if self.valves.debug:
                print(f"[DEBUG] Error extracting content: {e}")
            return "Error extracting content"

    async def _chroma_extract(self, query) -> str:
        embedding_function = (
            huggingface_embedding_function.HuggingFaceEmbeddingFunction(
                model_name="BAAI/bge-small-en-v1.5",
                api_key="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",
            )
        )
        chroma_client = chromadb.HttpClient(host="chroma-db", port=8000)
        db = chroma_client.get_collection(
            name="document_embeddings", embedding_function=embedding_function
        )
        results = db.query(query_texts=[query], n_results=5)
        context_text = "Answer the below question using only the context documents. If the information is not present do not respond with wrong answers. and only give me the anser, if you have question you can ask the user. Try to be helpul\n\n--\n\n".join(
            [result for i, result in enumerate(results["documents"][0])]
        )
        return context_text

    def move_new_files_in_last_minute(self, source_dir: str, destination_dir: str):
        """
        Move files that were modified in the last 1 minute from the source directory
        to the destination directory.

        Args:
            source_dir (str): The directory to check for new files.
            destination_dir (str): The directory to move new files to.
        """
        # Get the current time
        current_time = time.time()
        time_threshold = current_time - 600  # 60 seconds = 1 minute
        moved_files = set()
        files = sorted(
            [
                f
                for f in os.listdir(source_dir)
                if os.path.isfile(os.path.join(source_dir, f))
            ],
            key=lambda f: os.path.getmtime(os.path.join(source_dir, f)),
        )
        # Check for new files modified within the last 1 minute and move them
        for file_name in files:
            source_path = os.path.join(source_dir, file_name)
            file_mod_time = os.path.getmtime(source_path)
            print(source_path, file_mod_time)
            # Move only if the file was modified within the last minute
            print(file_mod_time)
            if file_mod_time >= time_threshold and file_name not in moved_files:
                underscore_index = file_name.find("_")

                new_file_name = file_name[underscore_index + 1 :]
                new_file_name = new_file_name.replace(" ", "_")

                destination_path = os.path.join(destination_dir, new_file_name)
                shutil.move(source_path, destination_path)
                print("Check here", destination_path)
                moved_files.add(file_name)
                print(f"Moved file: {file_name} to {destination_dir}")
