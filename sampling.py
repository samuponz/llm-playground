"""Watch how a token is chosen: the probability list, then the three knobs.

    docker compose run --rm app python sampling.py "Pick a random number between 1 and 10."

The model does not pick one answer. For the next token it gives every token a score,
those scores become probabilities, and one token is drawn at random, weighted by its
probability. That draw is "sampling". temperature, top_k and top_p reshape the list
*before* the draw. This script shows the list change at each step, then rolls the die.

We ask the model for the top candidates through the OpenAI-style API (logprobs). The
model's log-probabilities act as the scores: re-running softmax on them reshapes the
list exactly as the real sampler would. We only see the top ~20 tokens, not all ~150k,
so the tail is missing; enough to see what each knob does.
"""
import math
import random
import sys

from openai import OpenAI

import config

client = OpenAI(base_url=config.BASE_URL, api_key="ollama")

BAR = "█"
BAR_WIDTH = 40


def candidates(prompt):
    """Ask the model for the next-token scores: [(token, score), ...], best first.

    score is the natural log-probability (temperature 1). A bigger score = more likely.
    """
    options = {} if config.THINKING else {"reasoning_effort": "none"}
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1,          # we only care about the first token's list
        temperature=1,         # the model's natural distribution, so we can reshape it
        logprobs=True,
        top_logprobs=20,       # the most the API returns
        extra_body=options,
    )
    top = response.choices[0].logprobs.content[0].top_logprobs
    return [(t.token, t.logprob) for t in top]


def softmax(scores, temperature):
    """Turn scores into probabilities. Dividing by temperature reshapes the list:
    small temperature sharpens it (gaps grow), large temperature flattens it."""
    hottest = max(scores)  # subtract the max first, so exp() never overflows
    weights = [math.exp((s - hottest) / temperature) for s in scores]
    total = sum(weights)
    return [w / total for w in weights]


def show(pairs, title, floor=0.001):
    """Print each token as a bar, longest first. Tokens below the floor (0.1% by
    default) are summed into one line, so the long tail does not drown the list."""
    print(f"\n{title}")
    shown = [(t, p) for t, p in pairs if p >= floor]
    for token, prob in shown:
        print(f"  {token!r:14} {prob:6.1%} {BAR * round(prob * BAR_WIDTH)}")
    rest = pairs[len(shown):]
    if rest:
        print(f"  {f'+{len(rest)} more':14} {sum(p for _, p in rest):6.1%} "
              f"(each below {floor:.1%})")


def apply_top_k(pairs, k):
    """Keep only the k most likely tokens, drop the rest, then renormalise."""
    kept = pairs[:k]
    total = sum(p for _, p in kept)
    return [(t, p / total) for t, p in kept]


def apply_top_p(pairs, p):
    """Keep the most likely tokens until they add up to p, drop the rest, renormalise."""
    kept, running = [], 0.0
    for token, prob in pairs:
        kept.append((token, prob))
        running += prob
        if running >= p:
            break
    total = sum(pr for _, pr in kept)
    return [(t, pr / total) for t, pr in kept]


def main():
    prompt = " ".join(sys.argv[1:])
    if not prompt:
        print(__doc__)
        return

    tokens_scores = candidates(prompt)
    tokens = [t for t, _ in tokens_scores]
    scores = [s for _, s in tokens_scores]

    # 1. The natural list (what the model thinks, temperature 1)
    base = list(zip(tokens, softmax(scores, 1.0)))
    show(base, "1. The model's list (temperature 1)")

    # 2. Temperature: sharpen, then flatten
    for temp in (0.2, 1.5):
        label = "sharper (predictable)" if temp < 1 else "flatter (adventurous)"
        show(list(zip(tokens, softmax(scores, temp))), f"2. temperature {temp} — {label}")

    # 3. top_k on the natural list: keep the 5 best
    show(apply_top_k(base, 5), "3. top_k = 5 — keep the 5 most likely, drop the rest")

    # 4. top_p on the natural list: keep tokens until they add up to 0.9
    show(apply_top_p(base, 0.9), "4. top_p = 0.9 — keep the top tokens up to 90%")

    # 5. Roll the die on the natural list, a few times
    picks = random.choices(tokens, weights=[p for _, p in base], k=10)
    print("\n5. Ten draws from the list (temperature 1):")
    print("  " + "  ".join(repr(p) for p in picks))


if __name__ == "__main__":
    main()
