"""A minimal chat loop: our own version of `ollama run`.

The model remembers nothing between requests. This program keeps the whole
conversation in the list `messages` and sends all of it with every question.

After each answer it shows what the turn cost: tokens read and written, speed,
and how full the context window is.

Commands: /history (show what is sent), /context (context window usage),
/clear (forget everything), /bye (quit).
"""
import json
import readline  # noqa: F401  (makes input() support arrow keys and line editing)
import time

from openai import APIConnectionError, NotFoundError, OpenAI

import config
from stats import TurnStats, context_report, context_warning, usage_line

GREY = "\033[90m"  # terminal colour codes, used to show thinking text in grey
RESET = "\033[0m"

# Ollama ignores the API key, but the openai package requires one
client = OpenAI(base_url=config.BASE_URL, api_key="ollama")


def ask(messages):
    """Send the whole conversation and print the answer as it streams in.

    Returns the answer text and the turn's numbers (a TurnStats).
    """
    # Thinking is on by default in Qwen3; "none" turns it off
    options = {} if config.THINKING else {"reasoning_effort": "none"}
    sent_at = time.perf_counter()
    stream = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        stream=True,  # receive the answer token by token instead of all at the end
        stream_options={"include_usage": True},  # token counts arrive in the last chunk
        **options,
    )

    answer = ""
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

        if delta.content:
            if in_thinking:
                print(RESET + "\n")
                in_thinking = False
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
    return answer, stats


def main():
    thinking = "on" if config.THINKING else "off"
    print(f"Chatting with {config.MODEL} (thinking {thinking}).")
    print("Commands: /history  /context  /clear  /bye")

    messages = []  # the whole memory of the conversation
    last_stats = None  # numbers from the last answered request, for /context

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
            messages.clear()
            last_stats = None  # the numbers described a history that no longer exists
            print("(history cleared: the model now knows nothing about this chat)")
            continue
        if text == "/history":
            print(json.dumps(messages, indent=2, ensure_ascii=False))
            continue
        if text == "/context":
            print(context_report(last_stats, config.CONTEXT_SIZE, messages))
            continue

        messages.append({"role": "user", "content": text})
        try:
            answer, last_stats = ask(messages)
        except KeyboardInterrupt:
            print(RESET + "\n(answer interrupted)")
            messages.pop()  # forget the unanswered question
            continue
        except APIConnectionError:
            print(f"Cannot reach the model server at {config.BASE_URL}.")
            print("Is it running?  docker compose up -d ollama")
            messages.pop()
            continue
        except NotFoundError:
            print(f"Model {config.MODEL} not found. Download it:")
            print(f"  docker compose exec ollama ollama pull {config.MODEL}")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": answer})

        print(GREY + usage_line(last_stats, config.CONTEXT_SIZE) + RESET)
        warning = context_warning(last_stats, config.CONTEXT_SIZE)
        if warning:
            print(warning)


if __name__ == "__main__":
    main()
