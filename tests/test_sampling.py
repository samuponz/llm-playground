"""The sampling math from 4d: softmax with temperature, top-k, top-p."""
import math

import pytest

from sampling import apply_top_k, apply_top_p, softmax

# A list like the ones in docs/04d-sampling.md, already sorted best first
PAIRS = [("7", 0.5), ("3", 0.3), ("5", 0.15), ("9", 0.05)]


def test_softmax_gives_probabilities():
    probs = softmax([2.0, 1.0, 0.0], temperature=1.0)
    assert sum(probs) == pytest.approx(1.0)
    assert probs[0] > probs[1] > probs[2]


def test_softmax_of_log_probabilities_at_temperature_1_gives_them_back():
    # This is why sampling.py can reuse the model's logprobs as scores
    probs = [0.5, 0.3, 0.2]
    again = softmax([math.log(p) for p in probs], temperature=1.0)
    assert again == pytest.approx(probs)


def test_low_temperature_sharpens_high_temperature_flattens():
    scores = [2.0, 1.0, 0.0]
    cold, normal, hot = (softmax(scores, t)[0] for t in (0.2, 1.0, 5.0))
    assert cold > normal > hot
    assert cold > 0.99         # nearly always the top token
    assert hot < 0.5           # close to an even three-way split


def test_softmax_does_not_overflow_on_huge_scores():
    probs = softmax([1000.0, 999.0], temperature=0.1)  # exp(10000) would overflow
    assert sum(probs) == pytest.approx(1.0)


def test_top_k_keeps_k_and_renormalises():
    kept = apply_top_k(PAIRS, 2)
    assert [t for t, _ in kept] == ["7", "3"]
    assert [p for _, p in kept] == pytest.approx([0.625, 0.375])


def test_top_p_keeps_tokens_until_they_reach_p():
    # 0.5 < 0.7, then 0.5 + 0.3 = 0.8 >= 0.7: stop
    kept = apply_top_p(PAIRS, 0.7)
    assert [t for t, _ in kept] == ["7", "3"]
    assert sum(p for _, p in kept) == pytest.approx(1.0)


def test_top_p_always_keeps_at_least_one_token():
    assert [t for t, _ in apply_top_p(PAIRS, 0.01)] == ["7"]
