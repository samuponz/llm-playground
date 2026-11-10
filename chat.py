"""A minimal chat loop: our own version of `ollama run`.

The model remembers nothing between requests. This program keeps the whole
conversation in the list `messages` and sends all of it with every question.

After each answer it shows what the turn cost: tokens read and written, speed,
and how full the context window is.

Set LLM_SYSTEM to start every chat with a system message (instructions for the model).

Commands: /history (show what is sent), /context (context window usage),
/confidence (colour each answer token by how sure the model was, on/off),
/unsure (the least sure tokens of the last answer), /clear (forget everything), /bye (quit).
"""
import json
import math
import readline  # noqa: F401  (makes input() support arrow keys and line editing)
import time

from openai import APIConnectionError, NotFoundError, OpenAI

import config
from confidence import SCALE, colour, least_sure, show
from stats import TurnStats, context_report, context_warning, cut_warning, usage_line
from tracing import NoTrace, Trace

GREY = "\033[90m"  # terminal colour codes, used to show thinking text in grey
RESET = "\033[0m"

# Ollama ignores the API key, but the openai package requires one
client = OpenAI(base_url=config.BASE_URL, api_key="ollama")


def ask(messages, confidence=False):
    """Send the whole conversation and print the answer as it streams in.

    With confidence on, each answer token is printed on its colour (see confidence.py).
    Returns the answer text, the thinking text ("" when off), the turn's numbers, and
    the answer tokens with their probabilities ([] when confidence is off).
    """
    # Thinking is on by default in Qwen3; "none" turns it off
    options = {} if config.THINKING else {"reasoning_effort": "none"}
    if confidence:  # also send back each token's probability and the top 20 alternatives
        options |= {"logprobs": True, "top_logprobs": 20}
    sent_at = time.perf_counter()
    stream = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        stream=True,  # receive the answer token by token instead of all at the end
        stream_options={"include_usage": True},  # token counts arrive in the last chunk
        **options,
    )

    answer = ""
    thinking = ""
    tokens = []
    in_thinking = False
    first_at = None
    usage = None
    for chunk in stream:
        if chunk.usage:
            usage = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        # Thinking text arrives in "reasoning", an extra field Ollama adds to OpenAI's format
        reasoning = getattr(delta, "reasoning", None)
        if (reasoning or delta.content) and first_at is None:
            first_at = time.perf_counter()

        if reasoning:
            if not in_thinking:
                print(GREY, end="")
                in_thinking = True
            print(reasoning, end="", flush=True)
            thinking += reasoning

        if delta.content:
            if in_thinking:
                print(RESET + "\n")
                in_thinking = False
            logprobs = chunk.choices[0].logprobs
            if confidence and logprobs and logprobs.content:
                for t in logprobs.content:  # one chunk may hold several tokens
                    p = math.exp(t.logprob)  # log-probability -> probability
                    alternatives = [(a.token, math.exp(a.logprob)) for a in t.top_logprobs]
                    tokens.append({"token": t.token, "p": p, "alternatives": alternatives})
                    show(t.token, p)
            else:
                print(delta.content, end="", flush=True)
            answer += delta.content

    done_at = time.perf_counter()
    print(RESET if in_thinking else "")

    first_at = first_at or done_at
    stats = TurnStats(
        read=usage.prompt_tokens if usage else 0,
        wrote=usage.completion_tokens if usage else 0,
        first_token_s=first_at - sent_at,
        writing_s=done_at - first_at,
    )
    return answer, thinking, stats, tokens


def legend():
    return "  ".join(f"{colour(lowest + 0.001)} {label} {RESET}" for lowest, label, _ in SCALE)


def main():
    thinking = "on" if config.THINKING else "off"
    print(f"Chatting with {config.MODEL} (thinking {thinking}).")
    if config.SYSTEM:
        print(f"System message: {config.SYSTEM}")
    print("Commands: /history  /context  /confidence  /unsure  /clear  /bye")

    settings = {"model": config.MODEL, "base_url": config.BASE_URL,
                "context_size": config.CONTEXT_SIZE, "thinking_enabled": config.THINKING,
                "system": config.SYSTEM}
    trace = Trace(settings) if config.TRACE else NoTrace()
    if trace.path:
        print(f"Saving this session to {trace.path}")

    # The whole memory of the conversation. A system message, if set, always comes first.
    start = [{"role": "system", "content": config.SYSTEM}] if config.SYSTEM else []
    messages = list(start)
    last_stats = None  # numbers from the last answered request, for /context
    was_cut = False  # has the server already dropped part of this conversation?
    confidence = False  # colour answers by token probability? (/confidence)
    last_tokens = []  # the last answer's tokens with their probabilities, for /unsure

    while True:
        try:
            text = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):  # Ctrl+D or Ctrl+C
            print()
            break

        if not text:
            continue
        if text == "/bye":
            break
        if text == "/clear":
            messages[:] = start  # keep the system message: it belongs to the app, not the chat
            last_stats = None  # the numbers described a history that no longer exists
            last_tokens = []
            was_cut = False
            trace.write("clear")
            print("(history cleared: the model now knows nothing about this chat)")
            continue
        if text == "/history":
            print(json.dumps(messages, indent=2, ensure_ascii=False))
            continue
        if text == "/context":
            print(context_report(last_stats, config.CONTEXT_SIZE, messages))
            continue
        if text == "/confidence":
            confidence = not confidence
            print(f"(confidence colours {'on' if confidence else 'off'})")
            if confidence:
                print(legend())
            continue
        if text == "/unsure":
            if last_tokens:
                least_sure(last_tokens)
            else:
                print("(no probabilities yet: turn on /confidence, then ask something)")
            continue

        messages.append({"role": "user", "content": text})
        previous_stats = last_stats
        try:
            answer, thinking, last_stats, last_tokens = ask(messages, confidence)
        except KeyboardInterrupt:
            print(RESET + "\n(answer interrupted)")
            messages.pop()  # forget the unanswered question
            trace.write("interrupted", question=text)
            continue
        except APIConnectionError:
            print(f"Cannot reach the model server at {config.BASE_URL}.")
            print("Is it running?  docker compose up -d ollama")
            messages.pop()
            trace.write("error", error="connection", question=text)
            continue
        except NotFoundError:
            print(f"Model {config.MODEL} not found. Download it:")
            print(f"  docker compose exec ollama ollama pull {config.MODEL}")
            messages.pop()
            trace.write("error", error="model not found", question=text)
            continue

        messages.append({"role": "assistant", "content": answer})

        print(GREY + usage_line(last_stats, config.CONTEXT_SIZE) + RESET)
        cut = cut_warning(previous_stats, last_stats, config.CONTEXT_SIZE, was_cut)
        was_cut = was_cut or cut is not None
        warning = cut or context_warning(last_stats, config.CONTEXT_SIZE)
        if warning:
            print(warning)
        trace.turn(text, answer, thinking, last_stats, warning, last_tokens)

    trace.write("session_end", turns=len([m for m in messages if m["role"] == "assistant"]))


if __name__ == "__main__":
    main()
