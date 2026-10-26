"""Turn a list of chat messages into the one text the model actually reads.

The model knows nothing about "messages" or "roles": it continues a text. Before each
request, Ollama pastes the messages into one text using the model's chat template.
This is a hand-written copy of Qwen3's template as Ollama 0.40.11 applies it, without
the tool-calling parts. See the original with:

    docker compose exec ollama ollama show --template qwen3:4b-q4_K_M

Try it:

    docker compose run --rm app python template.py "My name is Sam."
"""
import re
import sys

import config
from tokens import load_tokenizer

# Special tokens are shown in yellow, so they stand out from the text you typed.
# Newlines are shown as a grey ↵: they are tokens too.
YELLOW = "\033[33m"
GREY = "\033[90m"
RESET = "\033[0m"
SPECIAL = re.compile(r"<\|[a-z_]+\|>|</?think>")


def render(messages, thinking):
    """The exact text the model reads for this list of messages."""
    text = ""

    # System messages are joined into one block at the very top. Ollama's template
    # leaves a blank line after "system" (Qwen's original template does not).
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    if system:
        text += f"<|im_start|>system\n\n{system}<|im_end|>\n"

    chat = [m for m in messages if m["role"] != "system"]
    last_user = max((i for i, m in enumerate(chat) if m["role"] == "user"), default=-1)

    for i, m in enumerate(chat):
        last = i == len(chat) - 1
        if m["role"] == "user":
            text += f"<|im_start|>user\n{m['content']}"
            if i == last_user:
                # How thinking is switched on or off: a word appended to your question
                text += " /think" if thinking else " /no_think"
            text += "<|im_end|>\n"
        elif m["role"] == "assistant":
            text += f"<|im_start|>assistant\n{m['content']}"
            if not last:  # a last assistant message stays open: the model continues it
                text += "<|im_end|>\n"

    if chat and chat[-1]["role"] != "assistant":
        # Open the assistant's turn: the most likely next text is now its answer
        text += "<|im_start|>assistant\n"
        if not thinking:
            # Thinking off: an empty reasoning block, written for the model
            text += "<think>\n\n</think>\n\n"
    return text


def highlight(text):
    text = SPECIAL.sub(lambda match: YELLOW + match.group() + RESET, text)
    return text.replace("\n", GREY + "↵" + RESET + "\n")


def count_tokens(text, tokenizer=None):
    tokenizer = tokenizer or load_tokenizer()
    return len(tokenizer.encode(text, add_special_tokens=False).ids)


def main():
    question = " ".join(sys.argv[1:])
    if not question:
        print(__doc__)
        return
    text = render([{"role": "user", "content": question}], config.THINKING)
    print(highlight(text))
    print("─" * 40)
    print(f"{count_tokens(text)} tokens (thinking {'on' if config.THINKING else 'off'})")


if __name__ == "__main__":
    main()
