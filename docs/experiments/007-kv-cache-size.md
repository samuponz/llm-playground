# 007: How big is the KV cache, and what does it cost?

**Date:** 2026-11-09 · **Ollama:** 0.40.11 · **Models:** `qwen3:1.7b`, `qwen3:4b-q4_K_M`,
thinking off · **Interface:** `ollama run --verbose` inside the container

## Question

The KV cache formula ([4b](../04b-kv-cache.md)) predicts its size from the model's shape
and the context size. Is it exact? And what does a bigger or smaller cache do to the
GPU/CPU split and to speed on a 2 GB GPU?

## Setup

Six server configurations. For each one, the `ollama` container is recreated with the
settings, then the same prompt is run 3 times:
`Write a paragraph of about 120 words about the sea.`

```bash
LLM_CONTEXT_SIZE=4096 OLLAMA_FLASH_ATTENTION=true OLLAMA_KV_CACHE_TYPE=q8_0 \
  docker compose up -d --force-recreate ollama
docker compose exec -T ollama ollama run qwen3:1.7b --verbose --think=false "<prompt>" </dev/null
docker compose exec ollama ollama ps
docker compose logs ollama | grep -E "kv_cache: *size|offloaded"
```

`</dev/null` matters in a script: with an open input, `ollama run` waits to read more
prompt from it and hangs.

Model shape, from `ollama show qwen3:1.7b --verbose`: 28 layers (`block_count`),
16 query heads, 8 KV heads (`head_count_kv`), 128 numbers per head (`key_length`),
trained up to 40,960 tokens (`context_length`).

## Result

Machine idle (browser closed). Speed = writing speed, 3 runs each.

| Config | KV cache | Formula | Layers on GPU | CPU/GPU | Writing speed (tokens/s) |
|---|---|---|---|---|---|
| 1.7B, ctx 2048 | 224 MiB | 224 ✅ | 15 / 29 | 45% / 55% | 17.6 · 17.0 · 16.9 |
| 1.7B, ctx 4096 | 448 MiB | 448 ✅ | 11 / 29 | 54% / 46% | 16.4 · 16.5 · 16.5 |
| 1.7B, ctx 8192 | 896 MiB | 896 ✅ | 8 / 29 | 63% / 37% | 15.8 · 15.5 · 15.4 |
| 1.7B, ctx 4096, flash attention | 448 MiB | 448 ✅ | 14 / 29 | 49% / 51% | 18.2 · 18.1 · 18.0 |
| 1.7B, ctx 4096, flash attention + `q8_0` | **238 MiB** | 238 ✅ | **16 / 29** | 44% / 56% | **18.4 · 18.5 · 18.5** |
| 4B, ctx 4096 | 576 MiB | 576 ✅ (predicted before measuring) | 4 / 37 | 75% / 25% | 6.4 · 6.4 · 6.4 |

Formula: `2 × layers × KV heads × 128 × bytes per number × context`. For `q8_0` a
number costs 34/32 bytes, not 1: numbers are stored in blocks of 32, each with one
extra 2-byte scale (`448 × 34/32 ÷ 2 = 238`).

The log also shows where the cache sits, e.g. at ctx 4096:
`CPU KV buffer size = 288 MiB`, `CUDA0 KV buffer size = 160 MiB`. Each layer's slice of
the cache lives with its layer.

A first run with Firefox playing a video gave the same memory numbers but speeds
30–70% lower (the 4B fell to 1.8 tokens/s): half the model runs on the CPU, so a busy
CPU slows everything. Speed numbers need an idle machine.

## What it shows

- **The formula is exact.** Six configurations, six exact matches, including a
  prediction made before the measurement. The cache size is plain arithmetic.
- **Doubling the context doubles the cache, and pushes layers off the GPU:** 15 → 11 → 8
  layers for 2048 → 4096 → 8192.
- **Flash attention frees GPU room without shrinking the cache** (11 → 14 layers): it
  saves the temporary score table, not the cache.
- **`q8_0` halves the cache** (448 → 238 MiB); with flash attention, 16 layers fit, the
  most of any config, and it is the fastest: +12% over the default.
- **More GPU layers help less than expected.** 8 → 15 layers on the GPU gave only +10%
  speed. Writing a token means reading all the weights once, so speed is limited by
  memory bandwidth, and the MX150's memory (~48 GB/s) is not much faster than the
  laptop's RAM. Experiment 002's bigger jump (21 layers at ctx 256) suggests the gain
  grows once most of the model fits.
- **A short chat doesn't pay for an empty cache in speed**, only in memory: attention
  only reads the filled rows. The slowdown at 8192 comes from the layers moved to the CPU.

Open: step 1 measured 14 / 29 layers at ctx 4096, today 11 / 29 with the same version
and settings. Why the difference?
