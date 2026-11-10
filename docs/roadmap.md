# Roadmap

Each step ends with something that works, a commit, and a concept page in `docs/`.
Side questions that come up go to [to-explore.md](to-explore.md).
Page file names follow these steps; for the order to read them in, see [README.md](README.md).

| Step | What | Status |
|---|---|---|
| 0 | Host setup: Docker Engine, NVIDIA Container Toolkit, git and a deploy key | ✅ |
| 1 | Containers and models: `ollama` + `app` services, GPU check, qwen3 models | ✅ |
| 2 | Chat loop that keeps history (`chat.py`): the model has no memory | ✅ |
| 3 | Make the internals visible: usage line, `/context`, overflow detection, traces | ✅ |
| 4 | Core concepts, hands-on | ✅ |
| **5** | **Tests and GitHub Actions** | in progress |
| 6 | Terminal lab dashboard | |
| 7 | Knowledge base: RAG and alternatives, measured | |
| later | Tool calling; JavaScript visualisations for sharing | |

## 3. Make the internals visible

- 3a. After each answer: tokens read and written, speed, time to first token, context
  fill. `/context` command with a fill bar. Warning above 80%.
- 3b. Experiment 002: overflow a small context window. Does the model forget? Can we
  detect the cut?
- 3c. Traces: each session saved to `traces/` (JSON Lines): the exact messages sent,
  answers, token counts, timings. Raw material for later visualisations.

## 4. Core concepts, hands-on

One concept page plus a small experiment each, with numbers from this laptop:

- ✅ **Tokens and the tokenizer**: what a token is, why "Leopardi" costs more than "Sam".
  [04a-tokens.md](04a-tokens.md), [experiment 003](experiments/003-what-text-costs.md),
  `tokens.py`.
- ✅ **KV cache**: what it stores, why context size costs memory, why it pushes layers off
  the GPU. [04b-kv-cache.md](04b-kv-cache.md), [experiment 007](experiments/007-kv-cache-size.md).
- ✅ **Chat templates**: how a list of messages becomes one text with special tokens.
  [04c-chat-templates.md](04c-chat-templates.md),
  [experiment 004](experiments/004-chat-template-check.md), `template.py`.
- ✅ **Sampling**: temperature, top-k, top-p: why the same question gives different answers.
  [04d-sampling.md](04d-sampling.md), [experiment 006](experiments/006-temperature-spread.md),
  `sampling.py`.
- ✅ **Quantization**: what `Q4_K_M` means and what it costs in quality.
  [04e-quantization.md](04e-quantization.md), [experiment 008](experiments/008-quantization.md),
  `weights.py`.
- ✅ **Confidence across an answer** (4f): the probability of every token, live,
  coloured green (sure) to red (unsure). Fact vs wording, and with vs without context
  (prepares step 7). [04f-confidence.md](04f-confidence.md),
  [experiment 009](experiments/009-confidence-with-context.md), `confidence.py`.
  Still open, listed on the page: chat integration (step 6) and calibration.

## 5. Tests and GitHub Actions

`pytest` tests for code that needs no model (settings, stats, traces, chat template,
sampling math, confidence colours), and a workflow that builds the app image and runs
them on every push. [05-tests.md](05-tests.md), `tests/`,
`.github/workflows/tests.yml`.

## 6. Terminal lab dashboard

A terminal interface (TUI) to chat while watching, live: GPU and CPU usage, memory, the
GPU/CPU split, tokens, speed and the context window filling up. Controls to change the
context size, temperature and thinking, and to edit the history, to see their effect.

Open decisions: the TUI library; which controls need Ollama's own API (e.g. context size
per request is not in the OpenAI-style API).

## 7. Knowledge base: RAG and alternatives, measured

Can a small local model become useful with the right context? Start from
[experiment 001](experiments/001-what-a-model-knows.md) (Leopardi): no context vs pasted
context vs retrieval (embeddings), then measure accuracy, speed and memory.

Expected trade-off, from step 1 numbers: the 4B model reads ~24 tokens/s, so 2,000
tokens of retrieved text ≈ 85 s before the first word, plus a bigger KV cache and less
room in the context window. Retrieving less but better will matter most.

## Later

- Tool calling: calculator and weather tools (the original plan).
- JavaScript / web visualisations of traces and concepts, for sharing the material.
