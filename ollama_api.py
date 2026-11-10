"""A tiny client for Ollama's own API (/api/...), used only by the dashboard.

Everywhere else we use the OpenAI-style API (/v1), so the code would also work with
other servers. The dashboard is a lab for *this* server, and Ollama's own API gives
two things the OpenAI-style one doesn't:
  - a context size per request (options.num_ctx); changing it reloads the model;
  - exact timings: loading, reading the prompt, writing, and tokens reused from cache.

No extra package: Python's urllib reads the answer line by line as it streams.
"""
import json
import math
import urllib.request

import config

# The OpenAI-style address ends in /v1; Ollama's own API is at the same server, /api
SERVER = config.BASE_URL.removesuffix("/v1")


def stream_chat(messages, num_ctx, think, temperature=None, top_logprobs=0):
    """Send the conversation; yield ("thinking", text), ("content", text) as the
    answer streams, then ("done", numbers) once at the end.

    With top_logprobs > 0, each answer piece also comes with its tokens:
    ("tokens", [{"token", "p", "alternatives"}, ...]), as in confidence.py."""
    options = {"num_ctx": num_ctx}
    if temperature is not None:
        options["temperature"] = temperature
    body = {"model": config.MODEL, "messages": messages, "think": think, "options": options}
    if top_logprobs:
        body |= {"logprobs": True, "top_logprobs": top_logprobs}
    request = urllib.request.Request(f"{SERVER}/api/chat", data=json.dumps(body).encode())
    with urllib.request.urlopen(request) as response:
        for line in response:  # one JSON object per line
            if not line.strip():
                continue
            chunk = json.loads(line)
            message = chunk.get("message", {})
            if message.get("thinking"):
                yield "thinking", message["thinking"]
            if message.get("content"):
                yield "content", message["content"]
                if chunk.get("logprobs"):
                    yield "tokens", [probabilities(t) for t in chunk["logprobs"]]
            if chunk.get("done"):
                yield "done", chunk


def probabilities(logprob):
    """One token from Ollama's logprobs, in the format confidence.py uses."""
    return {"token": logprob["token"],
            "p": math.exp(logprob["logprob"]),  # log-probability -> probability
            "alternatives": [(a["token"], math.exp(a["logprob"]))
                             for a in logprob.get("top_logprobs", [])]}


def timings(done):
    """The numbers from the last line of an answer, in seconds and tokens.
    Ollama measures durations in nanoseconds."""
    seconds = lambda key: done.get(key, 0) / 1e9
    return {
        "read": done.get("prompt_eval_count", 0),          # whole prompt, cache included
        "cached": done.get("prompt_eval_cached_count", 0),  # part reused from the KV cache
        "wrote": done.get("eval_count", 0),
        "load_s": seconds("load_duration"),                 # loading the model (0 if loaded)
        "reading_s": seconds("prompt_eval_duration"),       # reading the new prompt tokens
        "writing_s": seconds("eval_duration"),
    }
