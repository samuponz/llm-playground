# Roadmap

Each step ends with something that works, a commit, and a concept page in `docs/`.
Side questions that come up go to [to-explore.md](to-explore.md).

| Step | What | Status |
|---|---|---|
| 0 | Host setup: Docker Engine, NVIDIA Container Toolkit, git and a deploy key | ✅ |
| 1 | Containers and models: `ollama` + `app` services, GPU check, qwen3 models | ✅ |
| 2 | Chat loop that keeps history (`chat.py`): the model has no memory | ✅ |
| 3 | Make the internals visible: usage line, `/context`, overflow detection, traces | ✅ |
| **4** | **Core concepts, hands-on** | next |
| 5 | Tests and GitHub Actions | |
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

- **Tokens and the tokenizer**: what a token is, why "Leopardi" costs more than "Sam".
- **KV cache**: what it stores, why context size costs memory, why it pushes layers off
  the GPU (see [to-explore.md](to-explore.md)).
- **Chat templates**: how a list of messages becomes one text with special tokens.
- **Sampling**: temperature, top-k, top-p: why the same question gives different answers.
- **Quantization**: what `Q4_K_M` means and what it costs in quality.

## 5. Tests and GitHub Actions

`pytest` tests for code that needs no model (settings parsing, traces), and a workflow
that runs them on every push.

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
