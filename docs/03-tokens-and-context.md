# 3. Tokens and the context window

Models don't read characters or words: they read **tokens**, pieces of text of roughly
3–4 characters on average in English (how text is cut: [04-tokens.md](04-tokens.md)). Everything has a cost in tokens: the question, the
whole history re-sent each turn, the answer, and the thinking.

The **context window** is the maximum number of tokens the model can handle in one
request: template + history + new question + answer. Here it is 4096
(`LLM_CONTEXT_SIZE`, applied by the Ollama server).

## What the chat shows after each answer

```
[read 52 · wrote 6 · 14.2 tok/s · first token 0.4 s · context 58/4096 (1%)]
```

| Number | Meaning | Source |
|---|---|---|
| **read** | tokens the model read: template + **whole** history + new question | Ollama (`usage.prompt_tokens`) |
| **wrote** | tokens it generated: answer **+ thinking** if on | Ollama (`usage.completion_tokens`) |
| **tok/s** | writing speed: wrote ÷ time from first to last token | measured in `chat.py` |
| **first token** | wait before anything appears: reading the prompt (+ loading the model after a pause) | measured in `chat.py` |
| **context** | read + wrote: how much of the window this request filled | computed in [`stats.py`](../stats.py) |

`/context` shows the same as a bar, plus how many messages the history holds.
Above 80% full, the chat warns.

## The history makes every turn read more

A real session with `qwen3:1.7b`, thinking off:

| Turn | You asked | read | wrote | context |
|---|---|---|---|---|
| 1 | My name is Sam. | 25 | 9 | 34 |
| 2 | What is my name? | **52** | 6 | 58 |
| 3 | A 3-line poem about GPUs | **77** | 25 | 102 |

Each question is ~10 tokens, but **read** grows by the whole previous turn every time:
the model re-reads everything, because it remembers nothing.

```
turn 1:  [template][q1]                              → a1
turn 2:  [template][q1][a1][q2]                      → a2
turn 3:  [template][q1][a1][q2][a2][q3]              → a3
         └──────────── read ────────────┘   └ wrote ┘
```

## Reading is fast, writing is slow

The two phases have very different speeds (step 1 measurements):

| Model | Reading (prompt) | Writing (answer) |
|---|---|---|
| qwen3:1.7b | ~74 tokens/s | ~14 tokens/s |
| qwen3:4b-q4_K_M | ~24 tokens/s | ~6 tokens/s |

Reading processes all prompt tokens together; writing produces one token at a time,
each needing a full pass through the model. As the history grows, **first token** grows
(more to read) while **tok/s** stays about the same.

## Thinking costs tokens too

Same question, "What is 2+2? One word.", `qwen3:1.7b`:

| | read | wrote | visible answer |
|---|---|---|---|
| thinking off | 20 | 2 | "4" |
| thinking on | 20 | **210** | "Four" |

The thinking fills the window during the request. Our history keeps only the answer, so
it doesn't weigh on the next turn.

## Try it

```bash
docker compose run --rm -e LLM_MODEL=qwen3:1.7b app
```

Chat a few turns and watch **read** grow; type `/context`. Then turn thinking on
(`-e LLM_THINKING=true`) and compare **wrote**.

## When the window is full

The server silently drops the oldest part of the conversation, and the model doesn't
notice: see [experiment 002](experiments/002-context-overflow.md). The chat detects it
from the numbers and warns with ✂ (`read` went down, or `read + wrote` exceeded the
window), until `/clear`.
