# Ollama CLI cheatsheet

The `ollama` command lives inside the container, so every command starts with
`docker compose exec ollama`. To save typing, add an alias to your shell:

```bash
alias ollama='docker compose exec ollama ollama'   # only works from the project folder
```

The commands below assume this alias.

## Models

| Command | What it does |
|---|---|
| `ollama list` | Downloaded models and their size on disk |
| `ollama pull qwen3:1.7b` | Download a model (find more at https://ollama.com/library) |
| `ollama rm qwen3:4b` | Delete a model |
| `ollama ps` | Models **loaded in memory** now, their size, CPU/GPU split, and when they unload |
| `ollama stop qwen3:1.7b` | Unload a model from memory now (frees GPU/RAM) |

A loaded model unloads by itself after 5 minutes without requests.

## Chat by hand

| Command | What it does |
|---|---|
| `ollama run qwen3:1.7b` | Interactive chat |
| `ollama run qwen3:1.7b "Say hi"` | One question, one answer |
| `ollama run qwen3:1.7b --think=false "Say hi"` | Without thinking |
| `ollama run qwen3:1.7b --verbose "Say hi"` | Also print token counts and speed |

Inside an interactive chat:

| Type | Effect |
|---|---|
| `/set nothink` / `/set think` | Thinking off / on |
| `/set verbose` | Show speed after every answer |
| `/set parameter temperature 0` | Change a sampling setting (0 = always pick the most likely token) |
| `/show info` | Model details |
| `/clear` | Forget the conversation so far |
| `"""` | Start/end a multi-line message |
| `/bye` | Quit |

## Inspect a model (under the hood)

| Command | What it shows |
|---|---|
| `ollama show qwen3:1.7b` | Size, quantization, context length, capabilities (e.g. thinking levels) |
| `ollama show qwen3:1.7b --parameters` | Default sampling settings (temperature, top_k, top_p, stop words) |
| `ollama show qwen3:1.7b --template` | The **chat template**: how your messages become one long text |
| `ollama show qwen3:1.7b --modelfile` | The recipe Ollama uses for this model (file + template + parameters) |

## Reading `--verbose` output

```
prompt eval count:    25 token(s)     ← tokens the model READ (your prompt + template)
prompt eval rate:     74.19 tokens/s  ← reading is fast: all tokens processed together
eval count:           36 token(s)     ← tokens the model WROTE
eval rate:            16.62 tokens/s  ← writing is slow: one token at a time
```

## Try this

- Ask the same question with `--think=false` and without, using `--verbose`.
  Compare `eval count`: thinking is just extra written tokens.
- Look at `--template` and find `<|im_start|>` and `<|im_end|>`: these special
  tokens mark where each message begins and ends.
