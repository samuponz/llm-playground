"""Traces: each chat session saved as JSON Lines, the raw material for visualisations."""
import json

from stats import TurnStats
from tracing import NoTrace, Trace

SETTINGS = {"model": "qwen3:1.7b", "context_size": 4096}
STATS = TurnStats(read=49, wrote=3, first_token_s=0.3281, writing_s=0.12)


def events(trace):
    """Read the trace back: one JSON object per line."""
    with open(trace.path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def test_session_start_holds_the_settings(tmp_path):
    trace = Trace(SETTINGS, folder=tmp_path)
    [start] = events(trace)
    assert start["event"] == "session_start"
    assert start["model"] == "qwen3:1.7b"
    assert "time" in start


def test_turns_are_counted_and_stats_rounded(tmp_path):
    trace = Trace(SETTINGS, folder=tmp_path)
    trace.turn("Hi", "Hello!", "", STATS, None)
    trace.turn("And?", "Yes.", "", STATS, None)
    _, first, second = events(trace)
    assert (first["turn"], second["turn"]) == (1, 2)
    assert first["stats"]["first_token_s"] == 0.328  # rounded to the millisecond
    assert first["stats"]["tokens_per_second"] == 25.0
    assert first["stats"]["context_used"] == 52


def test_tokens_saved_only_with_confidence_on(tmp_path):
    trace = Trace(SETTINGS, folder=tmp_path)
    trace.turn("Hi", "Hello!", "", STATS, None)  # /confidence off
    tokens = [{"token": "Hello", "p": 0.9, "alternatives": [["Hello", 0.9], ["Hi", 0.1]]}]
    trace.turn("Hi", "Hello!", "", STATS, None, tokens)  # /confidence on
    _, off, on = events(trace)
    assert "tokens" not in off
    assert on["tokens"] == tokens


def test_accents_are_kept_readable(tmp_path):
    trace = Trace(SETTINGS, folder=tmp_path)
    trace.turn("Dov'è nato Leopardi?", "A Recanati.", "", STATS, None)
    with open(trace.path, encoding="utf-8") as f:
        text = f.read()
    assert "Dov'è" in text  # not "Dov'è"


def test_one_event_per_line_even_with_newlines_in_the_answer(tmp_path):
    trace = Trace(SETTINGS, folder=tmp_path)
    trace.turn("List two", "1. one\n2. two", "", STATS, None)
    assert [e["event"] for e in events(trace)] == ["session_start", "turn"]


def test_no_trace_writes_nothing(tmp_path):
    trace = NoTrace()
    trace.write("session_start")
    trace.turn("Hi", "Hello!", "", STATS, None)
    assert trace.path is None
    assert list(tmp_path.iterdir()) == []
