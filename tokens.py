"""Show how a text is split into tokens, the pieces a model actually reads.

    docker compose run --rm app python tokens.py "Giacomo Leopardi"
    echo "some text" | docker compose run --rm -T app python tokens.py

Ollama cannot show this (it only reports how many tokens a request had), so we load
Qwen3's tokenizer ourselves with Hugging Face's `tokenizers` library. All Qwen3 models
share the same tokenizer. It is downloaded once into models/ (not committed).
"""
import os
import sys
import urllib.request

from tokenizers import Tokenizer

# Pinned to one commit, so the file never changes under us
TOKENIZER_URL = ("https://huggingface.co/Qwen/Qwen3-4B/resolve/"
                 "1cfa9a7208912126459214e8b04321603b3df60c/tokenizer.json")
TOKENIZER_PATH = "models/qwen3-tokenizer.json"

# Two background colours, alternating, so you can see where each token ends
COLOURS = ["\033[44m", "\033[45m"]  # blue, magenta
RESET = "\033[0m"


def load_tokenizer():
    if not os.path.exists(TOKENIZER_PATH):
        print(f"Downloading the Qwen3 tokenizer to {TOKENIZER_PATH} (11 MB, once)...",
              file=sys.stderr)
        os.makedirs(os.path.dirname(TOKENIZER_PATH), exist_ok=True)
        urllib.request.urlretrieve(TOKENIZER_URL, TOKENIZER_PATH)
    return Tokenizer.from_file(TOKENIZER_PATH)


def pieces(tokenizer, text):
    """Split text into (token id, piece of the original text) pairs."""
    encoding = tokenizer.encode(text, add_special_tokens=False)
    # offsets = where each token starts and ends in the text. A character made of
    # several bytes (e.g. an emoji) can be split over tokens: then pieces repeat.
    return [(token_id, text[start:end])
            for token_id, (start, end) in zip(encoding.ids, encoding.offsets)]


def visible(piece):
    """Make spaces and newlines visible: they are part of tokens too."""
    return piece.replace(" ", "·").replace("\n", "↵\n")


def show(tokenizer, text):
    result = pieces(tokenizer, text)
    coloured = "".join(COLOURS[i % 2] + visible(piece) + RESET
                       for i, (_, piece) in enumerate(result))
    print(coloured)
    print("ids:", " ".join(str(token_id) for token_id, _ in result))

    words = len(text.split())
    per_word = f" · {len(result) / words:.2f} tokens per word" if words else ""
    print(f"{len(result)} tokens · {words} words · {len(text)} characters{per_word}")


def main():
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().rstrip("\n")
    if not text:
        print(__doc__)
        return
    show(load_tokenizer(), text)


if __name__ == "__main__":
    main()
