# 003: What a text costs in tokens

**Date:** 2026-10-26 · **Tokenizer:** Qwen3 (`tokenizer.json`, Hugging Face commit
`1cfa9a7`), shared by all Qwen3 models · **Interface:** [`tokens.py`](../../tokens.py)

## Question

The context window is measured in tokens, not words. How many tokens does a text cost?
Does Italian cost more than English? What about names, numbers, typos, code?

## Setup

```bash
docker compose run --rm app python tokens.py "Mi chiamo Samuele."
```

Ollama cannot show the split, so `tokens.py` loads Qwen3's tokenizer itself. To check
it is the same tokenizer Ollama uses, the same texts were sent to Ollama with
`raw: true` (no chat template) and the counts compared:

| Text | Ollama | `tokens.py` |
|---|---|---|
| `Giacomo Leopardi` | 5 | 5 |
| `Mi chiamo Samuele.` | 6 | 6 |
| `Ciao 👋 2026` | 9 | 9 |
| `La vita è una cosa splendida, ma anche dolorosa.` | 14 | 14 |

## Result

`·` is a space; `|` separates tokens.

**Same meaning, two languages:**

| Text | Tokens | Words | Chars per token |
|---|---|---|---|
| English paragraph (34 words) | **37** | 34 | 5.2 |
| Italian translation (35 words) | **49** | 35 | 4.1 |

```
The|·model|·does|·not|·remember|·anything|·between|·requests|.|·Our|·program|…
Il|·model|lo|·non|·ric|orda|·nulla|·tra|·una|·rich|iesta|·e|·l|'al|tra|.|·Il|·nostro|…
```

Common everyday words cost about the same in both languages (`la casa è grande e oggi il
tempo è bello`: 11 tokens, the English version: 10). The difference comes from longer and
less frequent words: `ric|orda`, `rich|iesta`, `convers|azione`, `preced|ente`.

**Other kinds of text:**

| Kind | Text | Tokens | Split |
|---|---|---|---|
| name | ` Sam` | 1 | `·Sam` |
| name | ` Samuele` | 2 | `·Sam\|uele` |
| name | ` Leopardi` | 2 | `·Leopard\|i` |
| name | ` Recanati` | 3 | `·Rec\|an\|ati` |
| word | ` conversation` | 1 | `·conversation` |
| typo | ` convresation` | 3 | `·conv\|res\|ation` |
| number | ` 2026` | 5 | `·\|2\|0\|2\|6` |
| number | ` 1234567.89` | 11 | one per digit and dot |
| code | `def add(a, b):` + `return a + b` | 11 | `def\|·add\|(a\|,\|·b\|):↵\|···\|·return\|…` |
| emoji | `👋🙂🚀` | 3 | one each |
| Chinese | `模型不记得任何东西` ("the model remembers nothing") | 5 | `模型\|不\|记得\|任何\|东西` |
| spaces | 8 spaces | 1 | runs of spaces are single tokens (code indentation) |

**The vocabulary:** 151,669 entries. 26 of them are special tokens, for example
`<|im_start|>`, `<|im_end|>`, `<think>`, `</think>`, `<tool_call>`, `<|endoftext|>`.

## What it shows

- **The same content cost Italian 32% more tokens than English** (49 vs 37). In
  practice an Italian chat fills the 4096 window about a third faster, and takes about
  a third longer to read. This is one paragraph, not a general measure, but the cause is
  visible: frequent English words are single tokens, longer Italian words are split.
- **Frequent = cheap.** `·Sam` and `·conversation` are one token. `Recanati` and a typo
  of `conversation` are three. Rare names, which is what a RAG system often has to
  handle, cost more.
- **The model never sees letters or digits as such.** `2026` is five separate digits;
  `conversation` is one opaque unit. Counting letters or doing arithmetic means working
  on pieces it can't look inside: one reason small models get these wrong.
- **A space belongs to the following word.** `Sam` at the start of a text is token
  23950, `·Sam` after a space is token 8224: two different units for the model.
- **Emoji are bytes.** Alone, each emoji here is one token. After a space, `👋` was split
  over two (`Ciao 👋 2026`: 9 tokens): the tokenizer works on the 4 bytes of the emoji,
  not on characters.
