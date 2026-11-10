"""Reading the numbers from the last line of an answer from Ollama's own API."""
import pytest

from ollama_api import timings

# A real last line (qwen3:1.7b, second turn of a chat), without the text fields
DONE = {"done": True, "load_duration": 2683783, "prompt_eval_count": 48,
        "prompt_eval_cached_count": 14, "prompt_eval_duration": 573832000,
        "eval_count": 5, "eval_duration": 835199000}


def test_timings_from_nanoseconds_to_seconds():
    t = timings(DONE)
    assert (t["read"], t["cached"], t["wrote"]) == (48, 14, 5)
    assert t["load_s"] == pytest.approx(0.0027, abs=1e-4)
    assert t["reading_s"] == pytest.approx(0.574, abs=1e-3)
    assert t["writing_s"] == pytest.approx(0.835, abs=1e-3)


def test_missing_fields_count_as_zero():
    # e.g. older Ollama versions have no prompt_eval_cached_count
    assert timings({"done": True}) == {"read": 0, "cached": 0, "wrote": 0,
                                       "load_s": 0, "reading_s": 0, "writing_s": 0}
