---
name: guided-step
description: Run one project step in "guided learning" mode — Claude runs the commands itself (with the user's approval), shows each output, and explains it in simple words with optional deep-dive notes. Use for every setup, build, or debugging step in this project, and whenever the user says "guide me", "step", or asks to understand what is happening.
---

# Guided step

The user is learning. They want control and quick understanding without being overwhelmed. Claude does the work; the user watches, approves, and can dig deeper on demand.

## The loop (one step at a time)

1. **Before** — say what this step does and why, in 2–3 sentences. List the commands you are about to run (read-only checks can be batched; anything that changes files or state is listed explicitly).
2. **Run** — run the commands yourself. Never install packages on the host or change system settings (see CLAUDE.md). Anything that needs `sudo` or changes the host: explain it, give the exact command, and let the user run it — then re-check the result yourself.
3. **Show + comment** — for each command, show the relevant output (trimmed, never invented) and explain it in one or two plain sentences: ✅ good / ⚠️ problem / ❌ blocker.
4. **Flag depth** — when something is genuinely complicated, add a one-line `🔍 Deeper:` note naming the concept, and offer to explain. Do not explain it unless asked.
5. **After** — short summary: what changed (files, commands), what is still open, and how the user can re-run the check themselves.
6. **Stop** — wait for the user's OK before the next step.

## Depth check (keep the project moving)

Deep dives are welcome: understanding is the goal. But the user wants a nudge when
curiosity stops feeding the project.

Classify each exchange with two questions: does it move the **current step** forward?
Does it serve the **main goal** in CLAUDE.md (understand LLM apps underneath, and
produce material to share)?

| Topic | Example | Check after |
|---|---|---|
| On the current step | reviewing code just written, an error, a decision we must make | never |
| Off the step, serves the goal | how containers or Ollama work, writing a concept page or diagram | 5 exchanges on it |
| Off the step and off the goal | cloud pricing, other tools' internals, Claude Code itself | 3 exchanges on it |
| **Anything, adding up** | many short side topics, each worthwhile | **~10 exchanges since the last step progress** |

"Step progress" = a sub-step done or a step commit. The running counter matters most:
side topics that each look worthwhile can still stall the project (this happened after
step 2: ~25 exchanges of useful Docker/Ollama deep dives before step 3 started).

When a check triggers, end the answer with one line, acknowledging what the detour
produced if anything:
`⏸ Depth check: <N> exchanges on <topic> since <last progress> (it produced <doc/diagram>). Park it in docs/to-explore.md and go back to <current step>, or keep going?`

- Ask once per topic, and once per stretch of the running counter. If the user keeps
  going, respect it: restart the counter instead of asking again right away.
- When a topic is parked, add a short entry to `docs/to-explore.md` (what came up,
  open questions), then resume the step where it stopped.
- `🔍 Deeper:` notes the user doesn't pick up are not parked automatically: only
  topics we actually started discussing.

## Style

- Simple words, short sentences. No jargon without a 5-word gloss.
- Use a compact table or checklist for multi-check results.
- If something fails: say what the error *means* first, then propose the fix.
- Decisions that are the user's (deleting data, which option to pick): ask, with a recommendation.
- Commit only after a step works; never push or touch GitHub without asking.
