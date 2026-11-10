# Docs: reading order

The file numbers follow the order the project was built (the steps in
[roadmap.md](roadmap.md)). This page lists the same pages in the order that is easiest
to learn from. Each concept page links to the experiments that back it.

## 1. The setup

- [01-setup.md](01-setup.md): what the two containers do, and GPU vs CPU
- [concepts/containers.md](concepts/containers.md): how containers work (namespaces,
  cgroups, images)
- [concepts/ollama.md](concepts/ollama.md): how Ollama works (server and clients, model
  files, security)

## 2. A chat, from the outside

- [02-chat-history.md](02-chat-history.md): the model has no memory; the program resends
  the whole conversation every time
- [03-tokens-and-context.md](03-tokens-and-context.md): the context window, and reading
  vs writing speed

## 3. Text in: what the model actually reads

- [04a-tokens.md](04a-tokens.md): what a token is, where the vocabulary comes from, why
  Italian costs more
- [04c-chat-templates.md](04c-chat-templates.md): how a list of messages becomes one text
  with special tokens

## 4. Choosing the next token

- [04d-sampling.md](04d-sampling.md): the probability list, temperature, top-k, top-p
- [04f-confidence.md](04f-confidence.md): how sure the model was at every token, and why
  sure is not the same as right

## 5. Cost: speed and memory

- [04b-kv-cache.md](04b-kv-cache.md): what the KV cache stores, and why a longer context
  costs memory
- [04e-quantization.md](04e-quantization.md): what `Q4_K_M` means, and what it costs in
  quality

## 6. Keeping it working

- [05-tests.md](05-tests.md): unit tests without a model, and GitHub Actions running
  them on every push

## Reference

- [experiments/](experiments/README.md): real runs, logged word for word and fact-checked
- [cheatsheets/](cheatsheets/README.md): tested commands for Docker, Ollama, its API, the
  GPU and git
- [traces.md](traces.md): the format of recorded chat sessions
- [roadmap.md](roadmap.md): the plan, step by step
- [to-explore.md](to-explore.md): side questions parked for later
