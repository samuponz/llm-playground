# 4f. Confidence across an answer

For every token it writes, the model has a probability list ([4d](04d-sampling.md)). The
probability of the token it actually chose tells you **how sure the model was at that
point**. Colour each token by it and you can watch confidence rise and fall along an
answer, live.

```bash
docker compose run --rm -e LLM_MODEL=qwen3:1.7b app python confidence.py "Who was Giacomo Leopardi?"
```

[`confidence.py`](../confidence.py) streams the answer with a coloured background per
token, then lists the least sure tokens and what else the model considered. Each run is
saved to `traces/`.

| Colour | Probability of the chosen token |
|---|---|
| 🟩 green | ≥ 90%: sure |
| 🟨 yellow | 50–90% |
| 🟧 orange | 20–50% |
| 🟥 red | < 20%: unsure, another token was more likely or the list was flat |

**Confidence is not correctness.** The model has no access to the truth, only to its own
list. Usually the two go together; the examples below show when they don't.

## Why the whole answer, not just the first token

The token that matters is rarely the first one. In "Giacomo Leopardi è nato nel 1798",
the first tokens just repeat the question; the fact comes at position 10–13. And the
model only reaches that point after choosing every earlier token, because each list
depends on what is already written. So you have to look at every step.

## Reading the examples

In the examples, sure tokens are plain text and every other token is followed by its
square. They were made from saved runs with
`python confidence.py --markdown traces/confidence-….json`.

### 1. Right by luck, wrong with hesitation (Leopardi)

`qwen3:1.7b`, temperature 0.6 (the model's default). *Tell me in three sentences who
Giacomo Leopardi was, with his birth year and birthplace.*

> Giacomo Leopardi was an Italian poet and literary🟥 critic known🟨 for his deep🟨
> intros🟥pection and melanch🟥olic style🟨. He was born in 17🟧98 in Sp🟥ole🟨to, Italy.
> His🟧 work🟧 often explored themes of identity🟥, despair🟥, and the human condition.

| Token | p | The model's list |
|---|---|---|
| "1" | 100% | |
| **"7"** | **40%** | **"8" 60%**, "7" 40% |
| "9", "8" | 100% | |
| **" Sp"** (Spoleto) | **7%** | " Liv" 20%, " Piet" 13%, " S" 7%, " F" 7%… |

- **Numbers are written digit by digit** (Qwen's tokenizer splits them), so each digit
  is its own decision. The uncertainty sat on one digit: 18xx or 17xx.
- **The year came out right by luck.** The model preferred "8" (60%), which would have
  been wrong; sampling drew the less likely "7". At temperature 0 it would have written
  18xx.
- **Once "17" was written, "98" was certain.** Confidence is always *given what came
  before*: a choice, right or wrong, makes the next tokens look sure.
- **The birthplace is wrong (Leopardi was born in Recanati), and it is red.** A flat list
  over many town names: the model was guessing, and the colour shows it. Recanati is not
  even in the top 4.
- **Most red tokens are harmless wording**: "literary" (the model preferred
  "philosopher"), "identity", "despair". Low confidence on word choice is normal.

The same fact, asked differently (`In che anno è nato Giacomo Leopardi?`, temperature 0),
was written with every digit at ~100%. Confidence depends on the prompt, not only on
the fact.

### 2. A confident invention (a made-up person)

`qwen3:1.7b`, temperature 0. The name is invented; the question takes for granted that
the person exists. *Who is Ettore Valsecchi Ambrosoli, the painter from Bergamo? Answer
in three sentences.*

> Ettore Valsecchi Ambrosoli was🟨 a🟨 renowned🟧 Italian painter from Bergamo, known for
> his vibrant🟧 and🟨 expressive🟨 style🟨.🟨 He gained🟨 recognition🟨 for🟨 his work🟧
> during🟨 the early🟨 20th century, particularly🟨 in🟨 the realm🟧 of modern🟨 art🟨. His
> paintings often depicted🟨 everyday🟧 life and landscapes🟨, reflecting🟨 the🟨 cultural
> and social atmosphere🟧 of his time.

**Not a single red token**, and every word of it is made up. The model doesn't hesitate
on *whether* the person exists: it writes a plausible, generic biography where every
step is a reasonable next word. The colours show spread-out wording (yellow, orange) but
no "I'm guessing a fact" moment, because no specific fact is ever stated: "early 20th
century", "landscapes", "everyday life" fit any painter.

A run asking about a real but obscure person (not saved here, it named someone) showed
the same mix: words copied from the question (the town) were green every time;
invented specifics (a birth day, a goal count) were orange or red; but the central
invention ("an Italian footballer") was ~100% sure.

## With vs without context

[Experiment 009](experiments/009-confidence-with-context.md): the same question at
temperature 0, once alone and once after a short paragraph saying Leopardi was born in
Recanati on 29 June 1798.

| Fact token | Without context | With context |
|---|---|---|
| Birthplace | " Piet" (an invented "Pietrino") 37% 🟧 | " Rec" 67% 🟨, then "an", "ati" 100% |
| Year, hundreds digit | "8" 62% 🟨 → 1813 ❌ | "7" 100% → 1798 ✅ |

With the answer in the prompt the model copies it, and the colours go green. Without
it, the model was wrong and still had no red token. Retrieval (step 7) is the job of
getting that paragraph into the prompt.

## What the colours can and cannot tell you

| Pattern | Meaning | Example |
|---|---|---|
| Green on words from the prompt | copying from the context is easy | the town named in the question |
| Red on a specific fact (name, number) | the model is guessing: likely wrong | "Sp" in Spoleto |
| Red or orange on ordinary words | several good synonyms: harmless | "literary" vs "philosopher" |
| Green right after a guess | confidence is conditional on what came before | "98" after "17" |
| All green/yellow, nothing red | **not** proof of truth: fluent inventions look like this | the made-up painter |

So low confidence on a fact is a useful warning; high confidence is not a guarantee.
How often "sure" means "right" is called **calibration**; small models are often poorly
calibrated.

## Limits of this view

- Only the top 20 alternatives are returned (out of ~150,000), so entropy and "what else
  it considered" cover the head of the list only.
- With sampling on (temperature > 0), a red token can mean the die picked an unlikely
  token, not that the model was unsure overall. `--temperature 0` always takes the top
  token: repeatable, but it hides "right by luck" cases like the year above.

## Ideas to continue

- **In the chat**: a `/confidence` toggle in `chat.py` to colour every answer, and `/why`
  to list the least sure tokens of the last answer. Later, the same colours in the
  step 6 dashboard.
- **Calibration**: over many questions, how often is a wrong fact red, and how often
  green?
- The saved runs in `traces/` hold every token with its alternatives: raw material for a
  later "hover to see the list" visualisation.
