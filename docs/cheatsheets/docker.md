# Docker cheatsheet

Two tools in one sheet:

- **`docker ...`** works on the whole machine, from **any folder**. You name containers
  and images yourself (`llm_playground-ollama-1`).
- **`docker compose ...`** works on this project only, and only **from the project
  folder** (elsewhere: `no configuration file provided`). You use service names:
  `ollama` (long-running model server) and `app` (our Python code, started when needed).

## Stop things: which command, from where

| Want to stop... | Command | Run from |
|---|---|---|
| **one** container | `docker stop <name>` | any folder |
| **all leftover** chats/shells, keeping ollama | `docker stop $(docker ps -q --filter label=com.docker.compose.project=llm_playground --filter label=com.docker.compose.oneoff=True)` | any folder |
| **the whole project** (ollama too) | `docker compose down` | project folder |
| only the model server | `docker compose stop ollama` (start again: `docker compose start ollama`) | project folder |

```bash
docker ps                                        # 1. what is running? note the name
docker stop llm_playground-app-run-7b84da33d077  # 2. stop it (polite, forced after 10 s)
docker ps -a                                     # 3. gone: --rm deleted it once stopped
```

Tips: **names must be typed in full**, but **IDs can be shortened** to any unique start
(`docker ps` shows IDs in the first column; `docker stop cdca` works). In zsh, **Tab**
completes names after `docker stop `.

## Who does what

```
you ──► docker compose ──reads──► docker-compose.yml + .env (this folder)
             │ translates "ollama" → llm_playground-ollama-1
             ▼
you ──► docker ──────────────► Docker Engine (dockerd)  ──►  containers, images, volumes
                               (one per machine, knows no folders)
```

- **Docker Engine (`dockerd`)**: a background service started at boot. It owns every
  container. Check it: `systemctl is-active docker`.
- **`docker`**: a client that sends requests to the Engine. Sees the **whole machine**;
  you name containers and images yourself.
- **`docker compose`**: a translator. Reads the Compose file and `.env` **in the current
  folder**, uses short service names, adds all the settings (volumes, environment,
  network, user, GPU), and labels the containers it creates so it can find them later.
  From another folder: `no configuration file provided`.

## `run` vs `exec`

| | **`exec`**: inside a running container | **`run`**: start a new container |
|---|---|---|
| **`docker`** | `docker exec -it llm_playground-ollama-1 bash` | `docker run --rm -it ubuntu bash` |
| **`docker compose`** | `docker compose exec ollama bash` | `docker compose run --rm app bash` |

| | `run` | `exec` |
|---|---|---|
| Container | creates a **new** one from the image | uses one **already running** |
| After exit | removed (with `--rm`) | keeps running |
| ENTRYPOINT | applies | skipped |
| Here, use it for | `app`: the chat, tests, a throwaway shell | `ollama`: `ollama ps`, a shell, logs |

`docker compose up -d ollama` never duplicates: if the service runs, it does nothing.
`docker compose run` creates a new container **every time**.

## Start, stop, status

| Command | What it does |
|---|---|
| `docker compose up -d ollama` | Start the model server in the background (`-d` = detached) |
| `docker compose ps` | This project's **service** containers (hides one-off `run` containers!) |
| `docker ps` | **All** running containers on the machine, including `app-run-...` ones |
| `docker ps -a` | Also stopped ones (`Exited`) |
| `docker compose restart ollama` | Restart with the **same** settings |
| `docker compose up -d ollama` (again) | After changing `.env` or the Compose file: **recreates** with new settings |
| `docker compose down` | Stop and remove the containers. **Models are kept** (volume) |
| `docker compose down -v` | ⚠️ Also deletes the volume = **all downloaded models** |

`ollama` has `restart: unless-stopped`: Docker restarts it by itself, even after a
reboot, until you stop it.

## Shells and commands inside containers

| Command | What it does |
|---|---|
| `docker compose run --rm app bash` | A shell in a new app container (`exit` to leave) |
| `docker compose run --rm app python` | A Python prompt (try `import config; config.MODEL`) |
| `docker compose exec ollama bash` | A shell in the running ollama container |
| `docker compose run --rm --entrypoint bash ollama` | Replace an image's ENTRYPOINT (rarely needed) |
| `docker compose run --rm -u root app bash` | As root, e.g. to install a tool **temporarily** |

**`-it` vs `-T`**: interactive programs (bash, python, top, the chat) need a terminal:
Compose gives one by default. `-T` = no terminal, for scripted commands only.

### ENTRYPOINT and CMD

| Image | ENTRYPOINT (fixed) | CMD (default, replaceable) |
|---|---|---|
| `ollama/ollama` | `/bin/ollama` | `serve` |
| our `app` | none | `python chat.py` |

What you type after the service name **replaces CMD**, and is appended to ENTRYPOINT:

```
docker compose run app python -c "print(1)"   →  python -c "print(1)"         ✓
docker compose run ollama python -c "..."     →  /bin/ollama python -c "..."  ✗ unknown command
```

### Slim images have few tools

`python:3.12-slim` has no `top`, `ps`, `htop`, `man` or editors. Alternatives:

```bash
docker top llm_playground-ollama-1      # processes in a container, from the host
docker stats                            # live CPU/RAM per container
ls /proc ; cat /proc/1/cmdline          # inside: read process info directly (what top does)
```

Changes made inside a container (installed tools, files outside `/app`) **vanish when it
is removed**. Only the image (Dockerfile), mounted folders and volumes persist.

## Orphan containers

A container belongs to the **Engine**, not to your terminal. The terminal only runs a
client connected to it (tested):

| What you do | What happens |
|---|---|
| `/bye`, `exit`, Ctrl+D | the program ends → container stops → `--rm` deletes it ✓ |
| **close the terminal window** | only the client dies; the **container keeps running**, idle |
| forget `--rm` | the container stops but stays on disk as `Exited` |

`--rm` doesn't stop anything: it means "delete the container **once it has stopped**",
and the Engine applies it however it stops.

```bash
docker ps                                   # look for llm_playground-app-run-...
docker stop <name>                          # stop one (--rm then deletes it)
docker container prune                      # delete all stopped containers (asks first)

# stop every leftover one-off container of this project, not ollama:
docker stop $(docker ps -q --filter label=com.docker.compose.project=llm_playground \
                          --filter label=com.docker.compose.oneoff=True)
```

## Four kinds of `ps`

| Command | Lists | Seen here |
|---|---|---|
| `ps aux` | Linux **processes** | `/bin/ollama serve` (PID 66322, ~377 MB) |
| `docker ps` | **containers**, whole machine | ollama + any `app-run-...` |
| `docker compose ps` | this project's **service** containers | only `ollama` |
| `ollama ps` | **models loaded** in memory | empty after 5 idle minutes |

Nested boxes: the process `ollama serve` runs inside the container
`llm_playground-ollama-1`, which holds a model in memory while you chat.
More on host processes: [linux.md](linux.md).

## Settings: `.env` vs `docker-compose.yml`

- `docker-compose.yml` = the recipe, with blanks: `LLM_MODEL: ${LLM_MODEL:-qwen3:4b-q4_K_M}`
- `.env` = your values for the blanks: `LLM_MODEL=qwen3:4b-q4_K_M` (never committed)
- Who wins: a variable typed in the terminal → `.env` → the default after `:-`

| Command | What it does |
|---|---|
| `docker compose config` | The final recipe, every blank filled in: what Docker really uses |
| `LLM_MODEL=qwen3:1.7b docker compose config` | Same, with a one-command override |
| `docker compose run --rm -e LLM_MODEL=qwen3:1.7b app` | Override a container variable for one run |

Inside the container, the values are **environment variables**: Python reads them with
`os.environ` (see [config.py](../../config.py)). They are always text, read once at start.

## Logs: what is the server doing?

| Command | What it does |
|---|---|
| `docker compose logs -f ollama` | Follow the log live (Ctrl+C stops following, not the server) |
| `docker compose logs --since 10m ollama` | Only the last 10 minutes |
| `docker compose logs ollama \| grep GIN` | One line per HTTP request (`GIN` is Ollama's web server) |
| `docker compose logs ollama \| grep -E "offloaded\|KV buffer"` | How a model was split between GPU and CPU |

## Resources and disk

| Command | What it does |
|---|---|
| `docker stats` | Live CPU and RAM per container (Ctrl+C to quit) |
| `docker volume ls` | Volumes; ours is `llm_playground_ollama_models` |
| `docker images` | Downloaded images (ollama is ~8 GB: it bundles GPU libraries) |
| `docker system df` | Total disk used by Docker |
| `docker compose build app` | Rebuild the app image (only when `requirements.txt` or `Dockerfile` change) |

## Try this

1. Run `docker compose logs -f ollama` in one terminal.
2. In another, run `docker compose exec ollama ollama run qwen3:1.7b "hi"`.
3. Watch the first terminal: the model loading, the GPU split, the HTTP request.
4. Open a chat with `docker compose run --rm app`, close the window, then `docker ps`:
   find your orphan and stop it.
