"""A minimal chat loop: our own version of `ollama run`.

The model remembers nothing between requests. This program keeps the whole
conversation in the list `messages` and sends all of it with every question.

Commands: /history (show what is sent), /clear (forget everything), /bye (quit).
"""
import json
import readline  # noqa: F401  (makes input() support arrow keys and line editing)

from openai import APIConnectionError, NotFoundError, OpenAI

import config

GREY = "\033[90m"  # terminal colour codes, used to show thinking text in grey
RESET = "\033[0m"

# Ollama ignores the API key, but the openai package requires one
client = OpenAI(base_url=config.BASE_URL, api_key="ollama")


def ask(messages):
    """Send the whole conversation, print the answer as it streams in, return its text."""
    # Thinking is on by default in Qwen3; "none" turns it off
    options = {} if config.THINKING else {"reasoning_effort": "none"}
    stream = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        stream=True,  # receive the answer token by token instead of all at the end
        **options,
    )

    answer = ""
    in_thinking = False
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        # Thinking text arrives in "reasoning", an extra field Ollama adds to OpenAI's format
        reasoning = getattr(delta, "reasoning", None)
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

    print(RESET if in_thinking else "")
    return answer


def main():
    thinking = "on" if config.THINKING else "off"
    print(f"Chatting with {config.MODEL} (thinking {thinking}).")
    print("Commands: /history  /clear  /bye")

    messages = []  # the whole memory of the conversation

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
            print("(history cleared: the model now knows nothing about this chat)")
            continue
        if text == "/history":
            print(json.dumps(messages, indent=2, ensure_ascii=False))
            continue

        messages.append({"role": "user", "content": text})
        try:
            answer = ask(messages)
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


if __name__ == "__main__":
    main()
