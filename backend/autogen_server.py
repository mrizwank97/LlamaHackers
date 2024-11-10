import json
import traceback
import uuid
from queue import Queue
from threading import Thread

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

# from backend.agent_workflow import AutogenWorkflow
from backend.workflows.doc_verification_workflow import DocumentVerificationWorkflow
from backend.data_model import Input, Output, StrOutput
from datetime import date
from backend.prompts import rp_prompt, passport_prompt, summarizer_prompt

empty_usage = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
}


def serve_autogen(inp: Input):
    model_dump = inp.model_dump()
    model_messages = model_dump["messages"]


    documents = [
        {
            "name":"Residence Permit",
            "verifier_type" : "Prompt_Verifier",
            "prompt":  rp_prompt.format(date=date.today())
        }, 
        {
            "name":"Passport",
            "verifier_type" : "Prompt_Verifier",
            "prompt": passport_prompt.format(date=date.today())
        },
        {   "name": "Enrollment Letter",
            "verifier_type" : "Template_Verifier",
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
    ## Generate Workflow
    workflow = DocumentVerificationWorkflow(documents)

    if inp.stream:
        queue = Queue()
        workflow.set_queue(queue)
        Thread(
            target=workflow.run,
            args=(
                model_messages[-1],
                inp.stream,
            ),
        ).start()
        return StreamingResponse(
            return_streaming_response(inp, queue),
            media_type="text/event-stream",
        )
    else:
        chat_results = workflow.run(
            message=model_messages[-1],
            stream=inp.stream,
        )
        return return_non_streaming_response(
            chat_results, inp.model
        )


def return_streaming_response(inp: Input, queue: Queue):
    while True:
        message = queue.get()
        if message == "[DONE]":
            yield "data: [DONE]\n\n"
            break
        chunk = Output(
            id=str(uuid.uuid4()),
            object="chat.completion.chunk",
            choices=[message],
            usage=empty_usage,
            model=inp.model,
        )
        yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        queue.task_done()


def return_non_streaming_response(chat_results, model):
    try:
        if chat_results:
            return StrOutput(
                msg=str(chat_results.chat_history[-1])
            ).model_dump()
        else:
            return Output(
                id="None",
                choices=[
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Sorry, I am unable to assist with that request at this time.",
                        },
                        "finish_reason": "stop",
                        "logprobs": None,
                    }
                ],
                usage=empty_usage,
                model=model,
            ).model_dump()

    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
