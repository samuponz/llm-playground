# To explore later

Questions that came up while building, parked so we can go in depth later.
Each one is a candidate for its own doc page and visualisation.

## KV cache: what it is, and why context size costs memory

- Seen in step 1: for `qwen3:1.7b` with a 4096-token context, Ollama's log shows
  `llama_kv_cache: size = 448.00 MiB`, almost a third of the model's memory.
- Questions: what is stored in it? Why does it grow with context size, even when the
  conversation is short? What do `K (f16)` and `V (f16)` mean?

## Why the models only half fit on the 2 GB GPU

- Step 1 measurements (Ollama 0.40.11, context 4096, nothing else on the GPU):

  | Model | In memory | GPU layers | Split (CPU/GPU) | Speed |
  |---|---|---|---|---|
  | qwen3:1.7b | 1.9 GB | 14/29 | 49% / 51% | ~16 tokens/s |
  | qwen3:4b (thinking-only) | 1.8 GB | ? | 46% / 54% | ~5 tokens/s |

- Ollama keeps 457 MiB free as a safety margin (`minimum="457.0 MiB"`) and plans with
  1.5 GiB, but only ~1 GiB was actually used. Why the gap?
- Experiments to try: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`,
  a smaller context (2048). Do more layers fit on the GPU? How does speed change?

## Tokens (step 4a)

- **BPE by hand**: the vocabulary and merge rules are also inside the model's GGUF file.
  Read them with the `gguf` Python package and write the merge loop ourselves, then check
  it gives the same tokens as `tokens.py`.
- **Token embeddings**: what the model does with a token ID first (looks up a vector of
  numbers). Visualise which tokens end up close together.

## Parked from the Docker and Ollama deep dives (step 2)

Already covered in [concepts/containers.md](concepts/containers.md),
[concepts/ollama.md](concepts/ollama.md) and the cheatsheets. Still open:

- **Rootless Docker and user namespaces**: making root in a container not equal root on
  the host. What does it cost?
- **Image layers**: how Docker stores an 8 GB image once and shares it between containers.
- **System calls**: watch them with `strace`; why one shared kernel is stable enough.
- **PID 1 and zombies**: why `ollama serve` as PID 1 left a zombie, and Compose's
  `init: true`.
- **`docker attach` and detaching** (Ctrl+P Ctrl+Q): reconnecting to an orphan.
- **Why Docker bypasses ufw** (iptables chains), and safe remote access to Ollama
  (reverse proxy with a password, or a VPN).
- **Linux memory**: the page cache, and when swap becomes a problem.
- **Harness vs model fit**: give the same tools to qwen3 1.7B / 4B / 8B and measure how
  often each picks the right one (good chart for the shared material).
- **The LLM timeline** (2017 → today) as an interactive visualisation.

## Old GPUs and CUDA versions

- Ollama 0.40.11 skips the MX150 in its CUDA 13 library (`compute capability not in
  compiled architectures`, cc 6.1) and falls back to its CUDA 12 library.
- A future Ollama version may drop CUDA 12, and the GPU would silently stop being used.
  This is why the image version is pinned.
