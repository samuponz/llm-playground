# Experiments

Real conversations with the models, logged word for word, fact-checked against a cited
source, with what each one shows. They are the evidence behind the concept pages.

| # | Experiment | Shows |
|---|---|---|
| [001](001-what-a-model-knows.md) | What a model knows (and makes up) | the model can't see its environment, can't look inside itself, and fills gaps in its memory with plausible inventions |
| [002](002-context-overflow.md) | What happens when the context window is full | the server silently drops the oldest messages; the model doesn't notice; a smaller window is faster |
| [003](003-what-text-costs.md) | What a text costs in tokens | the same paragraph costs 32% more tokens in Italian; rare names, typos and numbers cost more; the model never sees letters |
| [004](004-chat-template-check.md) | Is the hand-written chat template exact? | `template.py` matches Ollama's prompt token count in every case; 5 typed tokens become 21 |
| [005](005-system-message.md) | Does a small model follow the system message? | style and language always; rules only on 4B (1.7B gives away the secret); when the user asks for the opposite, the user wins |
| [006](006-temperature-spread.md) | How much does temperature spread the answers? | T=0 is repeatable; temperature only spreads what the list leaves room for ("Paris" never varies); the bigger model stays more consistent at the same temperature |
| [007](007-kv-cache-size.md) | How big is the KV cache, and what does it cost? | the size formula is exact; doubling context doubles the cache and pushes layers to the CPU; flash attention + `q8_0` fits the most layers and is fastest (+12%) |
| [008](008-quantization.md) | What does quantization look like, and what does it cost? | real weights are a heavy-tailed bell; each block of 32 snaps to 16 levels and one outlier coarsens its whole block; "Q4" averages 5.3 bits; Q8 was 1.5× slower and not visibly better |
| [009](009-confidence-with-context.md) | Does context turn a guess into a sure answer? | with the answer pasted in, the 1.7B model copies it and the fact tokens go from orange/yellow to green; without it, it was wrong (1813, "Pietrino") with no red token |

## How each experiment is logged

1. **Setup**: date, Ollama version, model, thinking on/off, interface
2. **Prompt**: exactly what was typed
3. **Answer**: word for word (in a collapsible section)
4. **Fact check**: each claim vs a cited source (✅ right, ⚠️ partly, ❌ wrong)
5. **What it shows**

Answers vary between runs: the models sample with `temperature 0.6`, so the same
question can give different (and differently wrong) answers.
