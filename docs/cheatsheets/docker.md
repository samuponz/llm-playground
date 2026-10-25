# Docker cheatsheet

| Tool | Works on | Run from | Refers to containers by |
|---|---|---|---|
| `docker ...` | the whole machine | any folder | container name or ID, image name |
| `docker compose ...` | one project (`docker-compose.yml` + `.env`) | the project folder | service name (`ollama`, `app`) |

Both are clients of the **Docker Engine** (`dockerd`), a background service that owns
every container. Check it with `systemctl is-active docker`.

## Docker: basic commands

### See what exists

| Command | Shows |
|---|---|
| `docker ps` | running containers |
| `docker ps -a` | all containers, including stopped (`Exited`) ones |
| `docker images` | downloaded and built images |
| `docker volume ls` | volumes (persistent storage) |
| `docker stats` | live CPU and memory per container (Ctrl+C to quit) |
| `docker top <container>` | processes inside a container |
| `docker logs -f <container>` | a container's output, live |
| `docker inspect <container>` | every detail, as JSON (add `--format '{{...}}'` to pick one) |
| `docker system df` | disk used by images, containers, volumes |

### Run, enter, stop, remove

| Command | Does |
|---|---|
| `docker run --rm -it <image> <cmd>` | start a new container (`-it` interactive terminal, `--rm` delete when stopped) |
| `docker exec -it <container> <cmd>` | run a command in a running container, e.g. `bash` |
| `docker stop <container>` | stop it politely (forced after 10 s) |
| `docker start <container>` | start a stopped container again |
| `docker rm <container>` | delete a stopped container |
| `docker rmi <image>` | delete an image |

Names must be typed in full; IDs can be shortened to any unique start (`docker stop cdca`).
In zsh, Tab completes names.

### Clean up

| Command | Deletes |
|---|---|
| `docker container prune` | all stopped containers |
| `docker image prune` | unused, untagged images |
| `docker system prune` | stopped containers, unused networks and images, build cache (asks first) |

Volumes are only deleted when you ask explicitly (`docker volume rm`, `prune --volumes`).

## Docker Compose: project commands

Run these from the project folder.

### Services

| Command | Does |
|---|---|
| `docker compose up -d` | start all long-running services in the background |
| `docker compose up -d ollama` | start one service; also **recreates** it after config changes |
| `docker compose ps` | the project's service containers (not one-off `run` containers) |
| `docker compose logs -f ollama` | follow a service's log (Ctrl+C stops following, not the service) |
| `docker compose stop ollama` / `start ollama` | pause / resume a service, same container |
| `docker compose restart ollama` | restart with the **same** settings |
| `docker compose down` | stop and remove the project's containers and network |
| `docker compose down -v` | ⚠️ also delete the volumes (here: all downloaded models) |

`up` never creates duplicates: if the service is already running, it does nothing.

### One-off commands

| Command | Does |
|---|---|
| `docker compose run --rm app` | new container running the default command (the chat) |
| `docker compose run --rm app bash` | a shell in a new container |
| `docker compose run --rm app python` | a Python prompt |
| `docker compose run --rm -e NAME=value app` | override an environment variable for this run |
| `docker compose exec ollama bash` | a shell in the running service container |
| `docker compose exec ollama ollama ps` | a command in the running service container |

`run` creates a new container **every time**.

### Build and configuration

| Command | Does |
|---|---|
| `docker compose build app` | rebuild the image (after changing `Dockerfile` or `requirements.txt`) |
| `docker compose config` | the final configuration, with every `${...}` filled in from `.env` |
| `NAME=value docker compose config` | same, with a value overridden for one command |

Precedence for `${NAME:-default}` in `docker-compose.yml`: a variable set in the
terminal → `.env` → the default after `:-`. Inside the container these become
environment variables (Python: `os.environ`).

## Concepts in brief

### `run` vs `exec`

| | `run` | `exec` |
|---|---|---|
| Container | creates a new one from the image | uses one already running |
| After exit | removed with `--rm`, otherwise kept as `Exited` | keeps running |
| Image ENTRYPOINT | applies | skipped |

### ENTRYPOINT and CMD

An image starts with ENTRYPOINT (fixed) + CMD (default, replaced by what you type after
the image or service name).

| Image | ENTRYPOINT | CMD | So `run <image> bash` gives |
|---|---|---|---|
| `ollama/ollama` | `/bin/ollama` | `serve` | `/bin/ollama bash` ✗ |
| our `app` | none | `python chat.py` | `bash` ✓ |

Replace the ENTRYPOINT when needed: `docker compose run --rm --entrypoint bash ollama`.

### Terminals: `-it` and `-T`

Interactive programs (shells, Python prompt, `top`, the chat) need a terminal: `-it` with
`docker`, the default with `docker compose`. `-T` = no terminal, for scripted commands.

### `--rm` and orphan containers

A container belongs to the Engine, not to the terminal that started it.

| You... | Result |
|---|---|
| quit the program (`exit`, Ctrl+D, `/bye`) | container stops; `--rm` deletes it |
| close the terminal window | only the client dies: the container keeps running (orphan) |
| omit `--rm` | the stopped container stays on disk |

`--rm` never stops anything: it deletes the container once it has stopped.

### Disposable containers

Anything changed inside a container disappears when it is removed. What persists: the
image (Dockerfile), mounted folders, volumes.

### Slim images

Minimal images such as `python:3.12-slim` have no `top`, `ps`, `man` or editors. Use
`docker top` / `docker stats` from the host, read `/proc` inside, or install a tool
temporarily as root (`run -u root ... apt-get install procps`).

## This project

| Service | Image | Role | Typical command |
|---|---|---|---|
| `ollama` | `ollama/ollama` | model server, always running (`restart: unless-stopped`) | `docker compose exec ollama ...` |
| `app` | built from our `Dockerfile` | our Python code, started when needed | `docker compose run --rm app` |

| Task | Command |
|---|---|
| start the model server | `docker compose up -d ollama` |
| chat | `docker compose run --rm app` |
| models loaded right now | `docker compose exec ollama ollama ps` |
| model split GPU/CPU | `docker compose logs ollama \| grep -E "offloaded\|KV buffer"` |
| HTTP requests to Ollama | `docker compose logs -f ollama \| grep GIN` |
| stop leftover chats/shells, keep ollama | `docker stop $(docker ps -q --filter label=com.docker.compose.project=llm_playground --filter label=com.docker.compose.oneoff=True)` |
| stop everything | `docker compose down` (models are kept) |

The four `ps`, from outermost to innermost:

| Command | Lists |
|---|---|
| `ps aux` | Linux processes ([linux.md](linux.md)) |
| `docker ps` | containers on the machine |
| `docker compose ps` | this project's service containers |
| `ollama ps` | models loaded in Ollama's memory |

## Try this

1. `docker compose logs -f ollama` in one terminal; `docker compose exec ollama ollama run qwen3:1.7b "hi"`
   in another. Watch the model load, the GPU split and the request.
2. Start a chat, close the window instead of typing `/bye`, then find and stop the orphan
   with `docker ps` and `docker stop`.
