"""The lab dashboard: chat on the left, live numbers on the right.

    docker compose run --rm app python dashboard.py

Same idea as chat.py (the program keeps the history and resends it every time), in a
full-screen terminal app built with Textual. It talks to Ollama's own API
(ollama_api.py) to get exact timings and, later, to change the context size.

Keys: Enter sends, Ctrl+L clears the history, Ctrl+Q quits.
"""
import time
from urllib.error import HTTPError, URLError

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Input, Static

import config
from confidence import SCALE, background
from ollama_api import SERVER, stream_chat, timings
from stats import TurnStats, context_bar, context_warning, cut_warning


class Message(Static):
    """One message in the chat panel."""


def style(p):
    """Black text on the background colour for probability p (scale from confidence.py)."""
    r, g, b = background(p)
    return f"black on rgb({r},{g},{b})"


def coloured(tokens):
    """The answer so far, each token on its colour."""
    text = Text()
    for t in tokens:
        text.append(t["token"], style=style(t["p"]))
    return text


def explain(error):
    """Turn a network error into what to do about it."""
    if isinstance(error, HTTPError) and error.code == 404:
        return (f"Model {config.MODEL} not found. Download it:\n"
                f"  docker compose exec ollama ollama pull {config.MODEL}")
    if isinstance(error, URLError):
        return (f"Cannot reach the model server at {SERVER}. Is it running?\n"
                f"  docker compose up -d ollama")
    return f"Error talking to Ollama: {error}"


class Dashboard(App):
    TITLE = "LLM lab"
    CSS = """
    #chat  { width: 2fr; border: round $primary; padding: 0 1; }
    #side  { width: 1fr; }
    #turn  { border: round $secondary; padding: 0 1; height: auto; }
    .user  { color: $accent; margin-top: 1; }
    .thinking { color: $text-muted; }
    .note  { color: $warning; }
    """
    BINDINGS = [("f2", "toggle_confidence", "Confidence colours"),
                ("ctrl+l", "clear", "Clear history"), ("ctrl+q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.messages = []        # the whole memory of the conversation, as in chat.py
        self.last_stats = None    # numbers of the last answered request
        self.was_cut = False      # has the server already dropped part of this chat?
        self.confidence = False   # colour each answer token by its probability (F2)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield VerticalScroll(id="chat")
            with Vertical(id="side"):
                yield Static("Ask something.", id="turn")
        yield Input(placeholder="Type a question, Enter to send")
        yield Footer()

    def on_mount(self):
        self.query_one("#chat").border_title = f"Chat · {config.MODEL}"
        self.query_one("#turn").border_title = "Last turn"
        self.query_one(Input).focus()

    def say(self, text, kind):
        """Add a message to the chat panel and scroll to it."""
        widget = Message(text, classes=kind)
        chat = self.query_one("#chat")
        chat.mount(widget)
        chat.scroll_end(animate=False)
        return widget

    def on_input_submitted(self, event: Input.Submitted):
        question = event.value.strip()
        if not question:
            return
        event.input.value = ""
        event.input.disabled = True  # one question at a time
        self.say(f">>> {question}", "user")
        self.messages.append({"role": "user", "content": question})
        self.answer()

    @work(thread=True)
    def answer(self):
        """Stream the answer in a background thread, so the screen stays responsive.
        Widgets may only be changed from the main thread: hence call_from_thread."""
        ui = self.call_from_thread
        thinking_widget = answer_widget = None
        thinking = answer = ""
        tokens = []  # answer tokens with their probabilities (confidence on)
        sent_at = time.perf_counter()
        first_at = None
        top = 20 if self.confidence else 0
        try:
            for kind, data in stream_chat(self.messages, config.CONTEXT_SIZE, config.THINKING,
                                          top_logprobs=top):
                if kind != "done" and first_at is None:
                    first_at = time.perf_counter()
                if kind == "thinking":
                    thinking += data
                    if thinking_widget is None:
                        thinking_widget = ui(self.say, "", "thinking")
                    ui(thinking_widget.update, Text(thinking))
                elif kind == "content":
                    answer += data
                    if answer_widget is None:
                        answer_widget = ui(self.say, "", "answer")
                    if not top:  # with confidence on, "tokens" right after draws it
                        ui(answer_widget.update, Text(answer))
                    ui(self.query_one("#chat").scroll_end, animate=False)
                elif kind == "tokens":
                    tokens += data
                    ui(answer_widget.update, coloured(tokens))
                else:
                    numbers = timings(data)
        except OSError as error:  # server not reachable, model missing...
            self.messages.pop()  # forget the unanswered question
            ui(self.say, explain(error), "note")
            ui(self.ready)
            return

        self.messages.append({"role": "assistant", "content": answer})
        done_at = time.perf_counter()
        stats = TurnStats(read=numbers["read"], wrote=numbers["wrote"],
                          first_token_s=(first_at or done_at) - sent_at,
                          writing_s=numbers["writing_s"])
        warning = cut_warning(self.last_stats, stats, config.CONTEXT_SIZE, self.was_cut)
        self.was_cut = self.was_cut or warning is not None
        warning = warning or context_warning(stats, config.CONTEXT_SIZE)
        self.last_stats = stats
        ui(self.show_turn, stats, numbers, warning, tokens)
        ui(self.ready)

    def show_turn(self, stats, numbers, warning, tokens):
        speed = stats.wrote / stats.writing_s if stats.writing_s else 0
        used = stats.read + stats.wrote
        lines = [
            f"read   {stats.read:>5} tokens  ({numbers['cached']} reused from cache)",
            f"wrote  {stats.wrote:>5} tokens  {speed:.1f} tok/s",
            "",
            f"load model    {numbers['load_s']:6.2f} s",
            f"read prompt   {numbers['reading_s']:6.2f} s",
            f"first token   {stats.first_token_s:6.2f} s",
            f"write answer  {numbers['writing_s']:6.2f} s",
            "",
            f"context {used}/{config.CONTEXT_SIZE} ({used / config.CONTEXT_SIZE:.0%})",
            context_bar(used / config.CONTEXT_SIZE, width=24),
        ]
        if warning:
            lines += ["", warning]
        if tokens:
            lines += ["", "least sure tokens:"]
            for t in sorted(tokens, key=lambda t: t["p"])[:3]:
                others = ", ".join(f"{a!r} {p:.0%}" for a, p in t["alternatives"][1:3]
                                   if a != t["token"])
                lines.append(f" {t['token']!r} {t['p']:.0%}  (also: {others})")
        self.query_one("#turn").update(Text("\n".join(lines)))

    def ready(self):
        field = self.query_one(Input)
        field.disabled = False
        field.focus()

    def action_toggle_confidence(self):
        self.confidence = not self.confidence
        if self.confidence:
            legend = Text("(confidence colours on, from the next answer: ")
            for lowest, label, _ in SCALE:
                legend.append(f" {label} ", style=style(lowest + 0.001))
            self.say(legend + Text(")"), "note")
        else:
            self.say("(confidence colours off)", "note")

    def action_clear(self):
        self.messages.clear()
        self.last_stats = None
        self.was_cut = False
        self.query_one("#chat").remove_children()
        self.say("(history cleared: the model now knows nothing about this chat)", "note")
        self.query_one("#turn").update("Ask something.")


if __name__ == "__main__":
    Dashboard().run()
