# LLM playground

Learn how LLM apps work underneath by building each piece by hand, with small models
running locally in [Ollama](https://ollama.com). Everything runs in Docker.

Status: step 3 of the [roadmap](docs/roadmap.md) done: the chat shows tokens, speed and
context usage, warns when the context overflows, and records sessions. Next: step 4,
core concepts (tokens, KV cache, sampling, quantization).

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
```

After each answer the chat shows tokens read and written, speed, and how full the
context window is. Inside the chat: `/history` shows exactly what is sent to the model,
`/context` shows the context window, `/clear` forgets the conversation, `/bye` (or
Ctrl+D) quits. Each session is saved to `traces/` (not committed; turn off with
`LLM_TRACE=false`): see [docs/traces.md](docs/traces.md).

## Useful commands

| Command | What it does |
|---|---|
| `docker compose up -d ollama` | Start the model server in the background |
| `docker compose logs -f ollama` | Follow the server's log (Ctrl+C to stop following) |
| `docker compose exec ollama ollama list` | Downloaded models |
| `docker compose down` | Stop everything (models stay in the `ollama_models` volume) |

## Learn more

- [docs/roadmap.md](docs/roadmap.md): the plan, step by step
- [docs/cheatsheets/](docs/cheatsheets/README.md): tested terminal commands for Docker, Ollama, its HTTP API, the GPU and git
- [docs/01-setup.md](docs/01-setup.md): what the containers do, and GPU vs CPU
- [docs/02-chat-history.md](docs/02-chat-history.md): the model has no memory; the program resends the history
- [docs/03-tokens-and-context.md](docs/03-tokens-and-context.md): tokens, the context window, reading vs writing speed
- [docs/traces.md](docs/traces.md): the format of recorded chat sessions
- [docs/concepts/containers.md](docs/concepts/containers.md): how containers work (namespaces, cgroups, images)
- [docs/concepts/ollama.md](docs/concepts/ollama.md): how Ollama works (server and clients, model files, local vs cloud, security)
- [docs/experiments/](docs/experiments/README.md): real conversations, fact-checked: what models know and make up
