# 004: Is the hand-written chat template exact?

**Date:** 2026-11-03 · **Ollama:** 0.40.11 · **Model:** `qwen3:1.7b` · **Interface:**
[`template.py`](../../template.py) and the OpenAI-style API

## Question

[`template.py`](../../template.py) rebuilds the text Ollama gives the model. Is it the
same text, token for token?

## Setup

For each chat, the messages were:

1. rendered with `template.render()` and counted with Qwen3's tokenizer;
2. sent to Ollama (`max_tokens=1`, thinking off with `reasoning_effort: "none"`), reading
   `usage.prompt_tokens` from the reply.

## Result

| Chat | Thinking | `template.py` | Ollama |
|---|---|---|---|
| `My name is Sam.` | off | 21 | 21 ✅ |
| system "You are a helpful assistant. Answer briefly." + `What is the capital of Italy?` | off | 37 | 37 ✅ |
| `My name is Sam.` → "Nice to meet you, Sam!" → `What is my name?` | off | 43 | 43 ✅ |
| `My name is Sam.` | on | 15 | 15 ✅ |

## What it shows

- **The hand-written template is exact** for these cases: system message, several
  turns, thinking on and off.
- **5 typed tokens become 21.** The other 16 are the template's wrapping.
- **Thinking off costs 6 tokens more than thinking on**: the empty
  `<think>↵↵</think>↵↵` block written for the model.
- Not tested: an earlier answer that contained reasoning (Qwen's template removes it
  from the history), and tool calls.
