# 002: What happens when the context window is full

**Date:** 2026-10-25 · **Ollama:** 0.40.11 · **Model:** qwen3:1.7b, thinking off
· **Context:** shrunk to **256** tokens (normally 4096) · **Interface:** `chat.py`

## Question

The history grows every turn, the window doesn't. When the history no longer fits,
does the server refuse, warn, or quietly drop something? Does the model notice?

## Setup

```bash
LLM_CONTEXT_SIZE=256 docker compose up -d ollama            # server: small window
LLM_CONTEXT_SIZE=256 docker compose run --rm -e LLM_MODEL=qwen3:1.7b app
docker compose up -d ollama                                 # afterwards: back to 4096
```

The context size is a server setting (`OLLAMA_CONTEXT_LENGTH`): changing it means
recreating the Ollama container. The same value is passed to the app for its display.

Script: tell the model a name, ask for five short poems to fill the window, ask for the
name again.

## Result

One run (the chat's own usage lines):

| Turn | Asked | read | wrote | context | Chat says |
|---|---|---|---|---|---|
| 1 | My name is Sam. Remember it. | 30 | 3 | 33 (13%) | |
| 2 | 4 lines about the sea | 50 | 39 | 89 (35%) | |
| 3 | … mountains | 105 | 52 | 157 (61%) | |
| 4 | … the city at night | 176 | 45 | 221 (86%) | ⚠ 86% full |
| 5 | … the forest | 238 | 44 | **282 (110%)** | ✂ overflowed while writing |
| 6 | … the desert | **217** | 58 | 275 (107%) | ✂ read went down: cut |
| 7 | What is my name? | 225 | 6 | 231 (90%) | |

Answers to "What is my name?" in three runs of the same script:

| Run | Answer |
|---|---|
| 1 | "You are named **Elias**." |
| 2 | "Your name is unknown." |
| 3 | "Your name is... you." |

Meanwhile our program's history still contained all 14 messages, the first being
*"My name is Sam. Remember it."*: **we sent it; the server dropped it.**

The Ollama log at the moment of overflow:

```
slot context shift, n_keep = 4, n_left = 251, n_discard = 125
stop processing: n_tokens = 175, truncated = 1
```

## What it shows

- **No error, no refusal: a silent cut.** When a request doesn't fit, the server (llama.cpp
  underneath) keeps the first few tokens (`n_keep = 4`), **discards the oldest part of
  the conversation** (`n_discard = 125` tokens) and continues. Nothing in the API
  response says so.
- **Two moments of cutting:** while writing (turn 5: read + wrote went past 256, a
  "context shift" made room mid-answer), and before reading (turn 6: the prompt was
  trimmed, so `read` went *down* although our history grew).
- **The model doesn't know what it lost.** It doesn't say "my memory was cut": it
  invents ("Elias"), dodges ("you"), or, by luck, admits it doesn't know. Three runs,
  three answers, because sampling is random (temperature 0.6).
- **Detectable from the numbers only.** The chat now warns with ✂ when `read` drops or
  `read + wrote` exceeds the window, and keeps warning until `/clear`, since a history
  that outgrew the window stays too long.

## Bonus: a smaller window made the model faster

| Context | KV cache | Layers on GPU | Writing speed |
|---|---|---|---|
| 4096 | 448 MiB | 14 / 29 | ~14 tokens/s |
| 256 | **28 MiB** | **21 / 29** | **~20 tokens/s** |

The memory reserved for the context window (the KV cache) shrank 16×, so 7 more layers
of the model fit on the 2 GB GPU, and writing got ~40% faster. Context size costs
memory even when the conversation is short. More in step 4 (KV cache).

## Real chat apps

Every chat app must handle this. Common strategies, from simplest:

1. **Cut silently** (what Ollama does by default): cheap, but the model forgets without knowing.
2. **Drop the oldest messages on purpose**, maybe keeping the first one (system prompt).
3. **Summarise** old messages into a short note (what Claude Code's `/compact` does): saves
   space, loses details.
4. **Bigger window**: more memory and slower, as the bonus table shows.
