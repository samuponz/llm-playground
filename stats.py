"""Numbers about one chat turn: tokens, speed, context fill.

Pure functions (numbers in, text out), so they can be tested without a model.
"""
from dataclasses import dataclass

WARN_AT = 0.8  # warn when the context window is more than 80% full


@dataclass
class TurnStats:
    read: int            # tokens the model read: template + whole history + new question
    wrote: int           # tokens it generated: answer + thinking (if on)
    first_token_s: float # seconds from sending the request to the first token
    writing_s: float     # seconds from the first token to the last


def tokens_per_second(stats):
    """Writing speed. 0 when there is nothing to measure."""
    if stats.writing_s <= 0:
        return 0.0
    return stats.wrote / stats.writing_s


def context_used(stats):
    """Tokens this request occupied in the context window."""
    return stats.read + stats.wrote


def context_fraction(stats, context_size):
    return context_used(stats) / context_size


def usage_line(stats, context_size):
    """The grey line printed after each answer."""
    used = context_used(stats)
    return (
        f"[read {stats.read} · wrote {stats.wrote} · "
        f"{tokens_per_second(stats):.1f} tok/s · "
        f"first token {stats.first_token_s:.1f} s · "
        f"context {used}/{context_size} ({context_fraction(stats, context_size):.0%})]"
    )


def context_bar(fraction, width=30):
    """A text progress bar, e.g. [████░░░░░░]."""
    filled = round(min(max(fraction, 0.0), 1.0) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def context_report(stats, context_size, messages):
    """The text shown by the /context command."""
    if stats is None:
        return "No request yet: ask something first."

    used = context_used(stats)
    fraction = context_fraction(stats, context_size)
    user = sum(1 for m in messages if m["role"] == "user")
    assistant = sum(1 for m in messages if m["role"] == "assistant")
    return "\n".join([
        f"Context window: {used} / {context_size} tokens ({fraction:.0%})",
        context_bar(fraction),
        f"  last request read  {stats.read:5} tokens   (template + {max(len(messages) - 2, 0)} earlier messages + question)",
        f"  last answer wrote  {stats.wrote:5} tokens   (thinking included; only the answer is kept)",
        f"  free               {max(context_size - used, 0):5} tokens",
        f"Messages in history: {len(messages)} ({user} user, {assistant} assistant)",
    ])


def cut_warning(previous, current, context_size, already_cut=False):
    """Detect when the server dropped part of the conversation, otherwise None.

    Our history only grows, so the model should read more each turn. Two signs of a cut:
    - read went down: the server dropped old messages before reading the prompt;
    - read + wrote exceeded the window: it dropped old tokens while writing.
    Once cut, the history stays too long, so every later turn is cut too (until /clear).
    """
    if previous is not None and current.read < previous.read:
        return (f"✂ the server cut the conversation: it read {current.read} tokens, "
                f"fewer than last turn ({previous.read}). The oldest messages are gone for the model.")
    if context_used(current) > context_size:
        return (f"✂ the window overflowed while writing ({context_used(current)}/{context_size}): "
                f"the server dropped the oldest tokens to continue.")
    if already_cut:
        return "✂ still cut: the model only sees the most recent part of the chat. /clear to start over."
    return None


def context_warning(stats, context_size):
    """A warning when the window is nearly full, otherwise None."""
    fraction = context_fraction(stats, context_size)
    if fraction < WARN_AT:
        return None
    return f"⚠ context {fraction:.0%} full: the server may soon cut the oldest messages."
