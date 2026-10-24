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

## Old GPUs and CUDA versions

- Ollama 0.40.11 skips the MX150 in its CUDA 13 library (`compute capability not in
  compiled architectures`, cc 6.1) and falls back to its CUDA 12 library.
- A future Ollama version may drop CUDA 12, and the GPU would silently stop being used.
  This is why the image version is pinned.
