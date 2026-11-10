# 006: How much does temperature spread the answers?

**Date:** 2026-11-08 · **Ollama:** 0.40.11 · **Models:** `qwen3:1.7b`, `qwen3:4b-q4_K_M`,
thinking off · **Interface:** OpenAI-style API, one user message per request

## Question

Sampling draws a token at random, weighted by the model's probability list ([4d](../04d-sampling.md)).
Temperature reshapes that list before the draw. So: ask the *same* question many times at
different temperatures — how many *different* answers come out? And does it depend on the
question?

## Setup

Two prompts, each asked 8 times at temperature 0, 0.6 and 1.5 (`max_tokens=12`, thinking
off). Count the distinct answers.

| Prompt | Kind |
|---|---|
| `What is the capital of France? Answer with just the city name, nothing else.` | one right answer |
| `Suggest a name for a pet cat. Reply with just the name, one word.` | open |

## Result

**`qwen3:1.7b`**, distinct answers out of 8 runs:

| Prompt | T=0 | T=0.6 | T=1.5 |
|---|---|---|---|
| capital of France | 1 (`Paris` ×8) | 1 (`Paris` ×8) | 1 (`Paris` ×8) |
| pet cat name | 1 (`Whiskers` ×8) | 5 | 8 |

<details>
<summary>Cat names (1.7B)</summary>

- **T=0.6**: `Whiskers` ×4, then `Bree`, `Miso`, `Milo`, `Belle` once each.
- **T=1.5**: all 8 different: `Whiskers`, `Misty`, `Milla`, `Buster`, `Luna`, `Felix`,
  `Poppy`, `Whistl` (the last one cut off — hot sampling starting to pick junk).

</details>

**`qwen3:4b-q4_K_M`**, pet cat name, distinct out of 8:

| T=0 | T=0.6 | T=1.5 |
|---|---|---|
| 1 (`Miso` ×8) | 3 (`Milo` ×4, `Miso` ×3, `Whisker` ×1) | 4 (`Miso`, `Milo`, `Luna`, `Whisker`) |

## What it shows

- **Temperature 0 is repeatable.** Both models, both prompts: the same answer 8/8. Greedy
  decoding always takes the top token, so there is nothing to vary.
- **The question decides how much spread is possible.** "Capital of France" gave `Paris`
  8/8 even at T=1.5: the list is so peaked on one token that no temperature can shake it.
  The open prompt spread from 1 → 5 → 8 answers. Temperature can only spread what the list
  already leaves room for.
- **The bigger model is more consistent at the same temperature.** At T=1.5 the 1.7B gave
  8 different names; the 4B gave 4. The 4B is more confident, so its list is sharper, so
  the same temperature produces less spread. Size shows up as a peakier distribution.
- **Too hot starts producing junk** (`Whistl`): past a point, flattening the list lets
  broken or off-topic tokens win.

This is the mechanism behind experiment 005 needing 3 runs per test: at Qwen's default
`temperature 0.6`, an uncertain list (e.g. "reveal the secret" vs "refuse") lands
differently on different runs.
