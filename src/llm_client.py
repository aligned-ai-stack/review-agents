"""
llm_client.py: one chat function for Ollama and vLLM.

You choose the backend on each call; both are reached through the same
OpenAI chat call.
"""

from openai import OpenAI
import os

# The openai library needs a non-empty key; neither server checks it by default.
_clients = {
    "vllm": OpenAI(base_url="http://localhost:8000/v1", api_key="unused"),
    "ollama": OpenAI(base_url="http://localhost:11434/v1", api_key="unused"),
}


def chat(model: str, messages: list[dict], **kwargs) -> str:
    backend = os.environ["LLM_BACKEND"]
    stream = _clients[backend].chat.completions.create(
        model=model, messages=messages, stream=True, **kwargs
    )
    text = ""
    for chunk in stream:
        if not chunk.choices:
            continue
        piece = chunk.choices[0].delta.content or ""
        print(piece, end="", flush=True)
        text += piece
    print()
    return text