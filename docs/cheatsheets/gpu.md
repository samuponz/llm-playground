# GPU cheatsheet

`nvidia-smi` works on your host and inside the ollama container.

## What is on the GPU now?

| Command | What it shows |
|---|---|
| `nvidia-smi` | Full table: GPU name, memory used/total, processes |
| `nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv` | Just the numbers |
| `watch -n 1 nvidia-smi` | Refresh every second (Ctrl+C to quit) |
| `nvidia-smi -l 1 --query-gpu=memory.used,utilization.gpu --format=csv` | One line per second, good for watching a model load |
| `docker compose exec ollama nvidia-smi` | The same, seen from inside the container |

## How is a model split between GPU and CPU?

| Command | What it shows |
|---|---|
| `docker compose exec ollama ollama ps` | `PROCESSOR` column, e.g. `49%/51% CPU/GPU` |
| `curl -s 127.0.0.1:11434/api/ps \| jq '.models[] \| {name, size, size_vram}'` | Exact bytes: total vs on GPU |
| `docker compose logs ollama \| grep "offloaded"` | `offloaded 14/29 layers to GPU` |
| `docker compose logs ollama \| grep "gpu memory"` | What Ollama thinks is free, and its safety margin |

## Our numbers (step 1, context 4096)

| Model | GPU memory used | Layers on GPU | Speed |
|---|---|---|---|
| nothing loaded | 5 MiB | | |
| qwen3:1.7b | ~990 MiB | 14 / 29 | ~16 tokens/s |
| qwen3:4b-q4_K_M | ~940 MiB | 7 / 37 | ~6 tokens/s |

## Try this

1. In one terminal: `nvidia-smi -l 1 --query-gpu=memory.used,utilization.gpu --format=csv`
2. In another: `docker compose exec ollama ollama run qwen3:1.7b "Write a short poem"`
3. Watch memory jump when the model loads, and utilization rise while it writes.
4. Then `docker compose exec ollama ollama stop qwen3:1.7b` and watch memory drop.
