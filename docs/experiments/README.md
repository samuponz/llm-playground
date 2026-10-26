# Experiments

Real conversations with the models, logged word for word, fact-checked against a cited
source, with what each one shows. They are the evidence behind the concept pages.

| # | Experiment | Shows |
|---|---|---|
| [001](001-what-a-model-knows.md) | What a model knows (and makes up) | the model can't see its environment, can't look inside itself, and fills gaps in its memory with plausible inventions |
| [002](002-context-overflow.md) | What happens when the context window is full | the server silently drops the oldest messages; the model doesn't notice; a smaller window is faster |
| [003](003-what-text-costs.md) | What a text costs in tokens | the same paragraph costs 32% more tokens in Italian; rare names, typos and numbers cost more; the model never sees letters |

## How each experiment is logged

1. **Setup**: date, Ollama version, model, thinking on/off, interface
2. **Prompt**: exactly what was typed
3. **Answer**: word for word (in a collapsible section)
4. **Fact check**: each claim vs a cited source (✅ right, ⚠️ partly, ❌ wrong)
5. **What it shows**

Answers vary between runs: the models sample with `temperature 0.6`, so the same
question can give different (and differently wrong) answers.
