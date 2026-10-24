# Docker Compose cheatsheet

Compose reads `docker-compose.yml` (plus the files listed in `COMPOSE_FILE` in `.env`).
Service names: `ollama`, `app`.

## Start, stop, status

| Command | What it does |
|---|---|
| `docker compose up -d ollama` | Start the model server in the background (`-d` = detached) |
| `docker compose ps` | What is running, and on which port |
| `docker compose restart ollama` | Restart the server with the **same** settings (see note) |
| `docker compose down` | Stop and remove the containers. **Models are kept** (they live in the volume) |
| `docker compose down -v` | ⚠️ Also deletes the volume = **all downloaded models** |

Note: after changing `.env` or `docker-compose.yml`, use `docker compose up -d ollama`
(not `restart`). It recreates the container with the new settings.

## Logs: what is the server doing?

| Command | What it does |
|---|---|
| `docker compose logs -f ollama` | Follow the log live (Ctrl+C stops following, not the server) |
| `docker compose logs --since 10m ollama` | Only the last 10 minutes |
| `docker compose logs ollama \| grep GIN` | One line per HTTP request (`GIN` is Ollama's web server) |
| `docker compose logs ollama \| grep -E "offloaded\|KV buffer"` | How a model was split between GPU and CPU |

## Look inside a container

| Command | What it does |
|---|---|
| `docker compose exec ollama sh` | Open a shell **inside** the running ollama container (`exit` to leave) |
| `docker compose exec ollama ls /root/.ollama/models/blobs` | The model files (named by their sha256 fingerprint) |
| `docker compose run --rm app python` | A Python prompt in a **new** app container, removed after (`--rm`) |
| `docker compose run --rm app env \| grep LLM_` | The settings our code will see |

`exec` = run in the container that is already running. `run` = start a fresh one.

## Resources and disk

| Command | What it does |
|---|---|
| `docker stats` | Live CPU and RAM per container (Ctrl+C to quit) |
| `docker volume ls` | Volumes; ours is `llm_playground_ollama_models` |
| `docker images` | Downloaded images (ollama is ~8 GB: it bundles GPU libraries) |
| `docker system df` | Total disk used by Docker |

## Config and builds

| Command | What it does |
|---|---|
| `docker compose config` | The final config after merging files and filling in `.env` |
| `docker compose build app` | Rebuild the app image (only needed when `requirements.txt` or `Dockerfile` change) |

## Try this

1. Run `docker compose logs -f ollama` in one terminal.
2. In another, run `docker compose exec ollama ollama run qwen3:1.7b "hi"`.
3. Watch the first terminal: the model loading, the GPU split, the HTTP request.
