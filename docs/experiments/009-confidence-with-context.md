# 009: Does context turn a guess into a sure answer?

**Date:** 2026-11-10 · **Ollama:** 0.40.11 · **Model:** `qwen3:1.7b`, thinking off,
temperature 0 · **Interface:** `confidence.py` (OpenAI-style API with logprobs)

## Question

In [4f](../09-confidence.md), asked where Leopardi was born, the small model wrote a
red " Sp" (Spoleto, wrong): it was guessing. If we paste a paragraph with the answer
above the question, does the model copy it, and does the colour turn green?
This is the idea behind step 7 (giving a model the right context).

## Setup

The same question twice, at temperature 0 (the model always takes its top token, so the
only difference between the runs is the context).

- **Without context:**
  `Tell me in three sentences who Giacomo Leopardi was, with his birth year and birthplace.`
- **With context:** the same question, after this paragraph:
  `Giacomo Leopardi (Recanati, 29 June 1798 - Naples, 14 June 1837) was an Italian poet,
  essayist and philosopher. He spent his youth in his father's library in Recanati, in
  the Marche region.`

```bash
docker compose run --rm -e LLM_MODEL=qwen3:1.7b app python confidence.py --temperature 0 "<prompt>"
```

## Answers

<details>
<summary>Without context</summary>

> Giacomo Leopardi was an Italian poet and philosopher born in 1813 in Pietrino, a small
> town in the Tuscan region. He is considered one of the most important poets of the
> 19th century, known for his deep emotional expression and exploration of human
> nature. His works often reflect on themes of love, death, and the human condition.

</details>

<details>
<summary>With context</summary>

> Giacomo Leopardi was an Italian poet, essayist, and philosopher born in Recanati,
> Marche, on 29 June 1798. He spent his early life in his father's library and developed
> a deep love for literature and philosophy. Leopardi is considered one of the most
> important poets of the 19th century, known for his introspective and melancholic style.

</details>

## Fact check

Source: [Giacomo Leopardi, Encyclopaedia Britannica](https://www.britannica.com/biography/Giacomo-Leopardi):
born 29 June 1798, Recanati (Papal States, today Marche).

| Claim | Without context | With context |
|---|---|---|
| Birth year | ❌ 1813 | ✅ 1798 |
| Birthplace | ❌ "Pietrino, Tuscany" (no such town) | ✅ Recanati, Marche |
| Birth day | not stated | ✅ 29 June |

## The fact tokens

| Token | Without context | With context |
|---|---|---|
| Birthplace, first token | " Piet" **37%** 🟧 (" F" 10%, " Liv" 9%, " S" 6%) | " Rec" **67%** 🟨, then "an", "ati" 100% |
| Year, hundreds digit | "8" **62%** 🟨 (vs "7" 38%) | "7" **100%** 🟩 |
| Year, last two digits | "1", "3" 100% | "9", "8" 100% |
| Region | " Tus" (Tuscany) **20%** 🟧 | "Marche", copied from the paragraph |
| Sure tokens (≥ 90%) in the whole answer | 50 of 77 (65%) | 68 of 83 (82%) |
| Red tokens (< 20%) | 0 | 0 |

The 33% left over next to " Rec" is a bare space token, most likely the start of the
same word split differently, not a different town. The list doesn't show what would come
after it, so this can't be confirmed.

## What it shows

- **Context turns a guess into a copy.** With the paragraph, every fact is right and
  sure. Copying from the prompt is the easiest thing a model does, so the
  probability list collapses onto the word that is already there.
- **The whole answer gets surer, not only the facts** (65% → 82% sure tokens). The
  paragraph also suggests the wording ("essayist", "father's library").
- **Wrong without being red.** At temperature 0 the model took its top choice, "8" at
  62%, and wrote 18xx. Once "18" was written, "13" was 100% sure. The invented town was
  only orange. Without context there was a warning, but only on 2 of 77 tokens, and
  no red at all.
- **Temperature 0 does not mean right.** In 4f, sampling at 0.6 drew the less likely "7"
  and got the year right by luck. Here the top choice was wrong.
- For step 7, retrieval has to do one job: get the right paragraph into the prompt.
  After that, even the 1.7B model copies it reliably.
