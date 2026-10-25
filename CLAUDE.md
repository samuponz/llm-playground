# Local LLM playground

A learning project for running small LLMs locally with Ollama and building tool-calling on top of them.

## Goal

1. **Now: learn.** Understand how LLM apps work underneath by building each piece
   by hand: chat history, tokens and context, sampling, thinking, tool calling,
   GPU/CPU offloading. No frameworks; make the internals visible.
2. **Later: share.** Turn what I learned into material that helps anyone understand
   how LLMs work: runnable with Docker, with diagrams, visualisations and animations.

While building, keep phase 2 in mind: plain language, a diagram in `docs/` for
each concept, beginner-readable code, and saved traces of real runs that future
visualisations can replay.

## About me

I'm new to local LLMs. When you make a non-obvious decision (library choice, model setting, architecture), explain it briefly in your reply so I learn why, not just what.

Work step by step with the `guided-step` skill. I tend to dig deep into side topics, even useful ones. Watch two things: whether a topic moves the current step forward, and whether it serves the goal above. Ask me once whether to park it in `docs/to-explore.md` and get back to the step after 3 off-goal exchanges, 5 on-goal ones, or about 10 exchanges since the last step progress whatever the topic (details in the skill).

## Hardware constraints

- 2017 ASUS Vivobook, Linux, 16 GB RAM (~12 GB free), NVIDIA MX150 with 2 GB VRAM.
- Models only partly fit on the GPU (even `qwen3:1.7b`); the rest runs on the CPU. Measured with Ollama 0.40.11 at context 4096: ~16 tokens/s on 1.7B, ~6 tokens/s on 4B. Expect ~3 tokens/s on 8B.
- The MX150 (compute capability 6.1) only works through Ollama's CUDA 12 library. Keep the Ollama image version pinned, and check the GPU is still used after upgrading.
- Keep memory use modest: one model loaded at a time, context around 4096 tokens.

## Docker: everything runs in containers

I don't want to install project dependencies on the host. The host only has Docker, the NVIDIA driver, and the NVIDIA Container Toolkit (I install and manage these myself).

- Never install packages on the host (no `pip install`, `apt install`, or global npm installs). Never change system settings.
- Use Docker Compose with two services:
  - `ollama`: the official `ollama/ollama` image, with GPU access, port 11434, and a named volume for downloaded models so they survive rebuilds.
  - `app`: our Python code, built from a `Dockerfile`, with the project folder mounted so code changes don't need a rebuild.
- Inside Compose, the app reaches Ollama at `http://ollama:11434/v1`, not `localhost`.
- Run everything through Compose: the app, tests, and one-off commands (e.g. `docker compose run --rm app pytest`, `docker compose exec ollama ollama pull qwen3:4b`).
- If the GPU isn't available inside the container, the setup must still work on CPU. Tell me rather than working around it on the host.
- If I already run Ollama directly on the host, it will conflict on port 11434. Point this out if it happens.

## Models

- Default: `qwen3:4b-q4_K_M` (everyday development and tool calling). Not plain `qwen3:4b`: that tag now points to Qwen3-4B-Thinking-2507, which cannot turn thinking off.
- Fast checks: `qwen3:1.7b` (lower quality; about half runs on the GPU, see `docs/01-setup.md`).
- Quality checks: `qwen3:8b` (slow; use to see whether a failure is the model's limit). Before using it, check with `ollama show` that its thinking `levels` include `false`.
- Qwen3 "thinking" mode is on by default and slows responses a lot. Default to thinking off for tool calls; make it a setting.

## Stack and conventions

- Python 3 in the `app` container, dependencies in `requirements.txt`. No virtual environment needed; the container is the isolated environment.
- Talk to Ollama through its OpenAI-compatible endpoint using the `openai` Python package, not the native `ollama` library. This keeps the code portable to bigger machines or cloud models later.
- Model name, base URL, context size and thinking on/off come from environment variables (via a `.env` file read by Compose) with sensible defaults. Never hard-code them in logic. Commit a `.env.example`, never the real `.env`.
- Keep each tool in its own module under `tools/`, with a clear JSON schema and a short, precise description. Small models pick tools much more reliably when descriptions are explicit and parameters are few.
- Use free APIs that need no key where possible (e.g. Open-Meteo for weather).
- Prefer small, readable files over clever abstractions. This is a learning codebase.

## Git and GitHub

The project lives in a GitHub repository.

- Keep a `.gitignore` covering `.env`, Python caches, and any local model or data files. Never commit secrets, API keys, or model weights.
- Make small commits, one logical change each, with clear messages in the imperative ("Add weather tool", "Fix context size setting").
- Commit after each working step, not before it works. Ask me before pushing, creating branches, or changing anything on GitHub.
- Add a GitHub Actions workflow that runs the pytest tests that don't need a model, so every push is checked automatically.

## Testing

- Before saying something works, run it through Compose against the `ollama` service with `qwen3:1.7b` for speed.
- Tool functions themselves (calculator, weather parsing) get plain unit tests with `pytest` that don't need a model. These are the tests that run on GitHub Actions.

## Diagrams and docs

- When explaining architecture or data flow, create or update a Mermaid diagram in `docs/`. GitHub renders Mermaid automatically.
- Keep `README.md` current with how to set up and run the project, starting from a fresh clone.

## Out of scope for now

- No web UI yet (planned later for visualisations).
- Tool calling: later, after chat, tokens and thinking are clear.
- No fine-tuning, no cloud APIs unless I ask.
