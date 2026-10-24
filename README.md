# LLM playground

Learn how LLM apps work underneath by building each piece by hand, with small models
running locally in [Ollama](https://ollama.com). Everything runs in Docker.

Status: step 1 of the plan (containers and models). The chat app comes next.

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

## Useful commands

| Command | What it does |
|---|---|
| `docker compose up -d ollama` | Start the model server in the background |
| `docker compose logs -f ollama` | Follow the server's log (Ctrl+C to stop following) |
| `docker compose exec ollama ollama list` | Downloaded models |
| `docker compose down` | Stop everything (models stay in the `ollama_models` volume) |

## Learn more

- [docs/01-setup.md](docs/01-setup.md): what the containers do, and GPU vs CPU
