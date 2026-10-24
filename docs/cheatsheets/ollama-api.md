# Ollama HTTP API cheatsheet

Everything (the CLI, our Python code) talks to Ollama over HTTP. With `curl` you send
the same requests by hand and see the raw replies.

From your terminal the address is `http://127.0.0.1:11434`.
(From inside the app container it is `http://ollama:11434`.)

```bash
B=http://127.0.0.1:11434   # shortcut used below
```

Two families of endpoints:

- `/api/...`: Ollama's own API, more details (timings, thinking, raw mode)
- `/v1/...`: a copy of OpenAI's API. **Our Python code uses this one.**

## Server and models

```bash
curl -s $B/api/version                                       # {"version":"0.40.11"}
curl -s $B/api/tags | jq '.models[].name'                    # downloaded models
curl -s $B/api/ps   | jq '.models[] | {name, size, size_vram}'  # loaded models; size_vram = bytes on GPU
curl -s $B/api/show -d '{"model":"qwen3:1.7b"}' | jq '.capabilities'
```

## One question: `/api/generate`

```bash
curl -s $B/api/generate -d '{
  "model": "qwen3:1.7b",
  "prompt": "Say hi",
  "think": false,
  "stream": false
}' | jq '{response, prompt_eval_count, eval_count}'
```

- `prompt_eval_count`: tokens read. `eval_count`: tokens written.
- Durations are in **nanoseconds**: `eval_count / eval_duration * 1e9` = tokens/s.
- Set `"think": true` and look at the extra `thinking` field.

## A conversation: `/api/chat`

The model has **no memory**. To continue a conversation, you send the whole history:

```bash
curl -s $B/api/chat -d '{
  "model": "qwen3:1.7b",
  "messages": [
    {"role": "user",      "content": "My name is Sam."},
    {"role": "assistant", "content": "Nice to meet you, Sam!"},
    {"role": "user",      "content": "What is my name?"}
  ],
  "think": false,
  "stream": false
}' | jq '{content: .message.content, prompt_eval_count}'
```

Remove the first two messages and ask again: it no longer knows.

## The OpenAI-style endpoint: `/v1/chat/completions`

Same idea, OpenAI's format. This is exactly what our Python code will send.

```bash
curl -s $B/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "qwen3:1.7b",
  "messages": [{"role": "user", "content": "Say hi"}],
  "reasoning_effort": "none"
}' | jq '{content: .choices[0].message.content, usage}'
```

- `"reasoning_effort": "none"` turns thinking off here (instead of `"think": false`).
- `usage` = token counts, in OpenAI's naming (`prompt_tokens`, `completion_tokens`).

## Streaming: watch tokens arrive one by one

Without `"stream": false`, the reply comes as many small JSON lines, one per token:

```bash
curl -sN $B/api/generate -d '{"model":"qwen3:1.7b","prompt":"Count to 5","think":false}'
```

Pretty version, text only:

```bash
curl -sN $B/api/generate -d '{"model":"qwen3:1.7b","prompt":"Count to 10","think":false}' \
  | jq -j '.response'; echo
```

## Raw mode: skip the template

Normally Ollama wraps your text in the chat template. With `"raw": true` you write the
whole text yourself, special tokens included:

```bash
curl -s $B/api/generate -d '{
  "model": "qwen3:1.7b",
  "prompt": "<|im_start|>user\nSay hi<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n",
  "raw": true,
  "stream": false
}' | jq '{response, prompt_eval_count}'
```

## Try this

- Compare `prompt_eval_count` for "Say hi" in normal mode (18) vs raw mode (14).
  Where do the 4 extra tokens come from? Hint: `ollama show qwen3:1.7b --template`.
- In raw mode, remove `<|im_start|>assistant` at the end. What does the model do now?
- Run the streaming command and look at the timestamps (`created_at`) between tokens.
