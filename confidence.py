"""Watch the model's confidence, token by token, while it answers.

    docker compose run --rm app python confidence.py "In che anno è nato Giacomo Leopardi?"
    docker compose run --rm app python confidence.py --temperature 0 "Who wrote Hamlet?"
    docker compose run --rm app python confidence.py --markdown traces/confidence-....json

Each token is printed on a coloured background: how probable that token was in the
model's own list when it was chosen (green = sure, red = unsure). This is the model's
confidence, not correctness: a model can be sure and wrong.

The probabilities come from the OpenAI-style API (logprobs), streamed with each token.
Only the top 20 alternatives are returned, not all ~150,000 tokens.
Each run is saved to traces/ (when LLM_TRACE is on) for later visualisations.
"""
import argparse
import json
import math
import os
import time

from openai import OpenAI

import config

client = OpenAI(base_url=config.BASE_URL, api_key="ollama")

# (lowest probability, label, background colour as red, green, blue)
SCALE = [
    (0.90, "sure ≥90%", (60, 170, 80)),
    (0.50, "50-90%", (220, 200, 60)),
    (0.20, "20-50%", (235, 140, 50)),
    (0.00, "unsure <20%", (215, 60, 60)),
]
RESET = "\033[0m"


def background(p):
    """The (red, green, blue) background colour for probability p."""
    return next(rgb for lowest, _, rgb in SCALE if p >= lowest)


def colour(p):
    """Terminal code for black text on the background matching probability p."""
    r, g, b = background(p)
    return f"\033[48;2;{r};{g};{b}m\033[38;2;0;0;0m"


def show(token, p):
    """Print one token on its colour. Newlines are printed outside the colour,
    otherwise the background would paint the rest of the terminal line."""
    parts = token.split("\n")
    for i, part in enumerate(parts):
        if i > 0:
            print()
        if part:
            print(f"{colour(p)}{part}{RESET}", end="", flush=True)


def ask(prompt, temperature, top):
    """Stream the answer; print each token as it arrives; return all tokens with
    their probability and alternatives."""
    options = {} if config.THINKING else {"reasoning_effort": "none"}
    settings = {} if temperature is None else {"temperature": temperature}
    stream = client.chat.completions.create(
        model=config.MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        logprobs=True,
        top_logprobs=top,
        extra_body=options,
        **settings,
    )
    tokens = []
    for chunk in stream:
        if not chunk.choices or not chunk.choices[0].logprobs:
            continue
        for t in chunk.choices[0].logprobs.content or []:  # one chunk may hold several
            p = math.exp(t.logprob)                          # log-probability -> probability
            alternatives = [(a.token, math.exp(a.logprob)) for a in t.top_logprobs]
            tokens.append({"token": t.token, "p": p, "alternatives": alternatives})
            show(t.token, p)
    print()
    return tokens


def entropy(alternatives):
    """How spread out the list was, in bits: 0 = one sure choice, 1 = a coin flip
    between two, 2 = four equal choices... Computed on the top alternatives only."""
    return -sum(p * math.log2(p) for _, p in alternatives if p > 0)


def summary(tokens):
    print()
    print("  ".join(f"{colour(lo + 0.001)} {label} {RESET}" for lo, label, _ in SCALE))
    counts = [sum(1 for t in tokens if t["p"] >= lo and
                  all(t["p"] < hi for hi, _, _ in SCALE[:i])) for i, (lo, _, _) in enumerate(SCALE)]
    print(f"{len(tokens)} tokens: " +
          ", ".join(f"{c} {label}" for c, (_, label, _) in zip(counts, SCALE)))

    print()
    least_sure(tokens)


def least_sure(tokens, n=5):
    """Print the n tokens the model was least sure of, with the top of its list."""
    unsure = sorted(tokens, key=lambda t: t["p"])[:n]
    print("Least sure tokens (what else the model considered):")
    for t in unsure:
        others = ", ".join(f"{a!r} {p:.0%}" for a, p in t["alternatives"][:4])
        print(f"  {t['token']!r:<14} {t['p']:>5.0%}   entropy {entropy(t['alternatives']):.1f} bits"
              f"   list: {others}")


def save(prompt, temperature, tokens):
    if not config.TRACE:
        return
    os.makedirs("traces", exist_ok=True)
    path = time.strftime("traces/confidence-%Y%m%d-%H%M%S.json")
    with open(path, "w") as f:
        json.dump({"model": config.MODEL, "prompt": prompt, "temperature": temperature,
                   "tokens": tokens}, f, ensure_ascii=False, indent=1)
    print(f"\nsaved {path}")


def markdown(path):
    """Turn a saved run into text for the docs: each token that was not sure gets a
    coloured square after it (sure tokens stay plain, so the text stays readable)."""
    with open(path) as f:
        run = json.load(f)
    squares = ["🟩", "🟨", "🟧", "🟥"]

    def square(p):
        return next(sq for sq, (lowest, _, _) in zip(squares, SCALE) if p >= lowest)

    temperature = "model default" if run["temperature"] is None else run["temperature"]
    print(f"Model `{run['model']}`, temperature {temperature}. "
          f"Prompt: *{run['prompt']}*\n")
    print("".join(t["token"] if t["p"] >= SCALE[0][0] else t["token"] + square(t["p"])
                  for t in run["tokens"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("prompt", help="the question, or with --markdown a saved run")
    parser.add_argument("--markdown", action="store_true",
                        help="print a saved run (traces/confidence-*.json) for the docs")
    parser.add_argument("--temperature", type=float, default=None,
                        help="default: the model's own setting (0.6 for Qwen3)")
    parser.add_argument("--top", type=int, default=20, help="alternatives per token (max 20)")
    args = parser.parse_args()
    if args.markdown:
        markdown(args.prompt)
        return

    print(f"{config.MODEL}, temperature "
          f"{'model default' if args.temperature is None else args.temperature}\n")
    tokens = ask(args.prompt, args.temperature, args.top)
    summary(tokens)
    save(args.prompt, args.temperature, tokens)


if __name__ == "__main__":
    main()
