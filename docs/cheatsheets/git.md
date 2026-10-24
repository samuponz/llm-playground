# Git cheatsheet

This project pushes with a **deploy key** that only works for this repository.
The remote uses the SSH nickname `github-llm-playground` (defined in `~/.ssh/config`).

## Everyday

| Command | What it does |
|---|---|
| `git status` | What changed since the last commit |
| `git diff` | The exact lines that changed |
| `git add <file>` / `git add -A` | Pick changes for the next commit / pick everything |
| `git commit -m "Add chat loop"` | Save a snapshot (message in the imperative) |
| `git push` | Send commits to GitHub |
| `git pull` | Get commits from GitHub |

## Looking back

| Command | What it does |
|---|---|
| `git log --oneline` | One line per commit |
| `git log --stat` | Which files each commit touched |
| `git show <commit>` | What exactly one commit changed |
| `git diff HEAD~1` | Changes since the commit before the last |

## Undo (carefully)

| Command | What it does |
|---|---|
| `git restore <file>` | Throw away uncommitted changes to a file ⚠️ |
| `git restore --staged <file>` | Un-pick a file you `git add`ed (changes are kept) |

## Checks

| Command | What it does |
|---|---|
| `git remote -v` | Where `push` goes (should show `github-llm-playground`) |
| `ssh -T git@github-llm-playground` | Test the deploy key: `Hi samuponz/llm-playground!` |
| `git check-ignore -v .env` | Prove `.env` is ignored, and which `.gitignore` line does it |
