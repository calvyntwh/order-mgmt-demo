## GitHub Copilot / Agent Instructions

Purpose
-------
This document explains how contributors should use GitHub Copilot, Copilot Chat agents, and editor helpers to keep `todo.md` accurate for this repository. We prefer editor-first, human-reviewed updates rather than automated server-side edits.

Why it matters
-------------
- `todo.md` is the canonical project tracker for the demo. Keeping it current keeps demos reliable and reduces reviewer friction.

When to update `todo.md`
------------------------
Update `todo.md` when a PR changes the demo workflow or user-facing behavior. Examples:
- Add/remove/rename public routes or endpoints under any `services/*` (web-gateway, auth-service, order-service).
- Change auth/session semantics (cookies, JWT signing/rotation, Valkey/refresh-token patterns).
- Modify infra or dev scripts that affect local demos (anything under `infra/` or `docker-compose*.yml`).
- Add or change health/metrics endpoints that the demo or smoke scripts rely on.

Do NOT update `todo.md` for purely internal refactors, formatting, or whitespace-only changes.

Editor-first guidance for Copilot / VS Code agents
-------------------------------------------------
- Use Copilot Chat or the `@workspace` agent to draft `todo.md` entries. Always review and edit suggestions before committing.
- Example prompts:
  - "Summarize these changed files and produce one concise `todo.md` checklist item with an owner placeholder and 2 acceptance steps."
  - "Given these files: services/web-gateway/app/main.py and services/auth-service/app/auth.py, suggest a `todo.md` entry for adding an `/admin` auth guard and how to test it."

Local developer workflow (recommended)
------------------------------------
1. Quick check which files changed against `main`:

```bash
git fetch origin main
git diff --name-only origin/main...HEAD
```

2. If results include `services/`, `infra/`, or `docker-compose*.yml`, draft a `todo.md` entry with Copilot Chat, refine it, and add it to the tracker in your branch.
3. Add a short `Tracker update:` section in your PR body with the exact line you added to `todo.md`.

PR checklist and opt-out
-----------------------
- Suggested PR checklist items:
  - [ ] Tests added/updated as needed
  - [ ] `todo.md` updated if this PR changes UX, routes, infra, or demo behavior
  - Tracker update: (paste the `todo.md` line here)

- If the PR intentionally does not require a tracker update (pure refactor), add `NO_TODO_CHECK` at the top of the PR body or use the `no-todo-check` label.

Useful prompts (copyable)
-------------------------
- "Analyze these changed files: {list files}. Produce a single concise `todo.md` item describing the work, owner placeholder, and 2 acceptance criteria steps."
- "Convert this commit message into a `todo.md` item: '{commit subject and body}'. Include owner: @TODO and a short verification step."

Local tooling and tests
----------------------
- There is a small helper: `scripts/mark_todo_done.py` — use it to mark an item done locally before merging.
  - Examples:

```bash
# Mark by numeric id or bracketed id
python scripts/mark_todo_done.py 6
python scripts/mark_todo_done.py "[6]"

# Mark by substring (first match)
python scripts/mark_todo_done.py "fix gateway"

# Mark all matches
python scripts/mark_todo_done.py "common" --all

# If your `todo.md` is in a different path
python scripts/mark_todo_done.py --file path/to/todo.md "[6]"
```

- To run the helper tests from repo root (no global installs required):

```bash
make test-mark-todo
```

- There is a VS Code task `mark-todo-done` (Run Task) that prompts for the query and runs the helper.

Questions, changes, and maintainers
----------------------------------
Open an issue or ping the maintainers listed in `README.md` if you want to change these instructions, add curated prompts, or extend the local tooling.

Accepted workflow summary
------------------------
- Use Copilot Chat to draft concise `todo.md` additions.
- Manually review and commit the change in your branch.
- Run `scripts/mark_todo_done.py` and commit the change before merging.
- Include the tracker update in your PR body to help reviewers.

