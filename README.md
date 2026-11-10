# LLM playground

Learn how LLM apps work underneath by building each piece by hand, with small models
running locally in [Ollama](https://ollama.com). Everything runs in Docker.

Status: steps 0–4 of the [roadmap](docs/roadmap.md) done: a chat that shows tokens,
speed and context usage, and hands-on pages on tokens, chat templates, sampling, the KV
cache and quantization. Next: step 5, tests and GitHub Actions.

## What you need

- [Docker Engine](https://docs.docker.com/engine/install/) with the Compose plugin
- Optional, for GPU speed: an NVIDIA GPU, its driver, and the
  [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- About 5 GB of disk for the models

No Python or other dependencies on your machine: they live in the containers.

## Setup

```bash
git clone https://github.com/samuponz/llm-playground.git
cd llm-playground
cp .env.example .env        # settings; on a machine without an NVIDIA GPU, see below
docker compose up -d ollama # start the model server
docker compose exec ollama ollama pull qwen3:1.7b        # small, fast model (~1.4 GB)
docker compose exec ollama ollama pull qwen3:4b-q4_K_M  # default model (~2.5 GB)
```

**No NVIDIA GPU?** In `.env`, change
`COMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml` to `COMPOSE_FILE=docker-compose.yml`.
Everything works on CPU, just slower.

## Check it works

```bash
docker compose exec ollama ollama run qwen3:1.7b "Say hi in five words"
docker compose exec ollama ollama ps    # PROCESSOR column: how much runs on GPU vs CPU
```

## Chat

```bash
docker compose run --rm app                              # default model (qwen3:4b-q4_K_M)
docker compose run --rm -e LLM_MODEL=qwen3:1.7b app      # fast model, for one run
docker compose run --rm -e LLM_THINKING=true app         # show the model's thinking (grey)
docker compose run --rm -e LLM_SYSTEM="Always answer in Italian." app  # add a system message
```

After each answer the chat shows tokens read and written, speed, and how full the
context window is. Inside the chat: `/history` shows exactly what is sent to the model,
`/context` shows the context window, `/confidence` colours each answer token by how sure
the model was ([docs/04f-confidence.md](docs/04f-confidence.md)), `/unsure` lists the least
sure tokens of the last answer, `/clear` forgets the conversation, `/bye` (or Ctrl+D) quits. Each session is saved to `traces/` (not committed; turn off with
`LLM_TRACE=false`): see [docs/traces.md](docs/traces.md).

## See the tokens

```bash
docker compose run --rm app python tokens.py "Mi chiamo Samuele."
```

Shows how a text is split into the tokens the model reads, with their IDs and counts.
The first run downloads Qwen3's tokenizer (11 MB) into `models/`. See
[docs/04a-tokens.md](docs/04a-tokens.md).

## See the weights

```bash
docker compose run --rm app python weights.py                       # formats and bits per weight
docker compose run --rm app python weights.py blk.0.attn_q.weight   # one matrix
docker compose run --rm app python weights.py blk.0.attn_q.weight --blocks   # + its blocks
```

Reads the model file straight from Ollama's storage (mounted read-only) and shows how
the weights are stored. For one matrix it prints statistics and saves a histogram and an
image to `docs/images/`. See [docs/04e-quantization.md](docs/04e-quantization.md).

## See the model's confidence

```bash
docker compose run --rm app python confidence.py "In che anno è nato Giacomo Leopardi?"
```

Streams the answer with each token coloured by how probable it was (green = sure,
red = unsure), then lists the least sure tokens and what else the model considered.
Confidence is not correctness: a model can be sure and wrong. Each run is saved to
`traces/`.

## Lab dashboard (work in progress)

```bash
docker compose run --rm app python dashboard.py
```

A full-screen terminal version of the chat, with the numbers of each turn on the side:
tokens read (and how many came from the cache), loading, reading and writing times,
context fill. Enter sends, Ctrl+L clears the history, Ctrl+Q quits.

## Run the tests

```bash
docker compose run --rm --no-deps app pytest
```

Tests for the code that needs no model (settings, stats, traces, chat template,
sampling math). `--no-deps` skips starting Ollama. GitHub runs the same tests on every
push. See [docs/05-tests.md](docs/05-tests.md).

## Useful commands

| Command | What it does |
|---|---|
| `docker compose up -d ollama` | Start the model server in the background |
| `docker compose logs -f ollama` | Follow the server's log (Ctrl+C to stop following) |
| `docker compose exec ollama ollama list` | Downloaded models |
| `docker compose down` | Stop everything (models stay in the `ollama_models` volume) |

## Learn more

- [docs/README.md](docs/README.md): all concept pages, in reading order
- [docs/roadmap.md](docs/roadmap.md): the plan, step by step
- [docs/experiments/](docs/experiments/README.md): real runs, logged and fact-checked
- [docs/cheatsheets/](docs/cheatsheets/README.md): tested terminal commands for Docker, Ollama, its HTTP API, the GPU and git
