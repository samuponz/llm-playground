"""Save each chat session to traces/ as JSON Lines: one event per line.

Raw material for later visualisations: it records exactly what was sent to the
model and what came back, so a real conversation can be replayed turn by turn.
The file is appended after every event, so a crash loses nothing written so far.
"""
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone

from stats import context_used, tokens_per_second

TRACES_DIR = "traces"


def now_utc():
    return datetime.now(timezone.utc)


class Trace:
    def __init__(self, settings, folder=TRACES_DIR):
        os.makedirs(folder, exist_ok=True)
        self.path = os.path.join(folder, now_utc().strftime("%Y-%m-%dT%H-%M-%SZ") + ".jsonl")
        self.turns = 0
        self.write("session_start", **settings)

    def write(self, event, **data):
        """Append one event as a JSON line."""
        line = {"time": now_utc().isoformat(timespec="milliseconds"), "event": event, **data}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def turn(self, messages_sent, answer, thinking, stats, warning):
        """One answered question: the exact request and everything measured."""
        self.turns += 1
        self.write(
            "turn",
            turn=self.turns,
            messages_sent=messages_sent,
            answer=answer,
            thinking=thinking,
            stats={
                **{k: round(v, 3) for k, v in asdict(stats).items()},  # seconds to the ms
                "tokens_per_second": round(tokens_per_second(stats), 2),
                "context_used": context_used(stats),
            },
            warning=warning,
        )


class NoTrace:
    """Used when tracing is off (LLM_TRACE=false): same methods, does nothing."""
    path = None

    def write(self, event, **data):
        pass

    def turn(self, messages_sent, answer, thinking, stats, warning):
        pass
