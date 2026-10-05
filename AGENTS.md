# AGENTS.md

Python "AI Employee" framework: autonomous loops that move Markdown task files between
folders in an Obsidian-style vault (`AI_Employee_Vault/`). Not a web app — there is no
build, no bundler, and no package to install.

## Run everything from the repo root

Nearly every script hardcodes a **bare relative** vault path:

```python
VAULT_DIR = "AI_Employee_Vault"   # watcher.py, scripts/*.py, ralph_wiggum_loop.py
```

No script anchors to `__file__`. Worse, the orchestrators shell out with *repo-root-relative*
paths, so running them from inside `scripts/` silently breaks:

- `scripts/run_ai_employee.py:87,105,125` → `subprocess.run([sys.executable, "scripts/task_planner.py"])`
- `scripts/ralph_wiggum_loop.py:198,298` → same `scripts/task_planner.py`
- `.agents/skills/gmail-send/scripts/send_email.py:11` → `load_dotenv(os.path.join(os.getcwd(), ".env"))`

Always `python scripts/<file>.py` from `E:\Hackathon-0-main`. Failures are swallowed
(`capture_output=True`, results often only logged), so a wrong CWD looks like "no tasks found".

## Entrypoints — three different `run_ai_employee.py`

The name is reused for three unrelated programs. Picking the wrong one is easy:

| Path | What it actually does |
|---|---|
| `run_ai_employee.py` (root) | Bulk **"Process Tasks"** impl of `GEMINI.md`. `--once` only. Regex-rewrites *every* task in `Needs_Action/`: `status: pending`→`completed`, `- [ ]`→`- [x]`, then moves to `Done/` and rewrites `Dashboard.md`. No planning, no approval. |
| `scripts/run_ai_employee.py` | Silver Tier scheduler: `--daemon --interval N`, `--once`, `--status`. Runs planner → moves tasks to `Needs_Approval/` → approval gate → `ralph_wiggum_loop.py`. **This is the one the docs mean.** |
| `.agents/skills/scheduler-silver-tier/scripts/run_ai_employee.py` | Third, drifted variant. Not wired into the pipeline. |

Other real entrypoints: `watcher.py` (Bronze, 5s poll, creates `task_<name>.md` tasks),
`scripts/watch_inbox.py` (Silver, 20s poll), `scripts/ralph_wiggum_loop.py` (Gold execution).

`--status` derives "daemon running" purely from the existence of `logs/ai_employee.lock`
(`scripts/run_ai_employee.py:74`). A stale lock makes status lie. Stale locks are auto-overwritten
on start, so prefer deleting `logs/ai_employee.lock` over debugging phantom daemons.

## There is no test suite and no lint config

`README.md` says `pytest tests/` and `flake8 scripts/ .agents/skills/` — **both are false**:

- `tests/` contains 17 `.md` fixture task files only. Zero Python tests, no `conftest.py`,
  no `pytest.ini`/`pyproject.toml`/`setup.cfg`/`tox.ini`/`.flake8`.
- `scripts/test_*.py` are **manual diagnostic scripts**, not pytest tests. Run them directly.
  `scripts/test_linkedin_integration.py` is a one-line stub that always prints `success`.

Don't add a fix "verified by tests" here — verify by running the script and inspecting the
resulting vault files and `logs/`. `playwright install` is a separate prerequisite after
`pip install -r requirements.txt`.

## Vault is the database — it mutates on every run

`Inbox/` → `Needs_Action/` → `Needs_Approval/` → `Done/` (failures → `Errors/`, plans → `Plans/`).

- Scripts **move and rewrite files for real**; there is no dry-run mode and no rollback.
- `scripts/ralph_wiggum_loop.py` is driven by checkboxes: it reads `Needs_Action/Plan.md`,
  finds the first `- [ ]` line, executes it, and flips it to `- [x]`. If no `Plan.md` exists
  it logs "Skipping" and exits. `MAX_ITERATIONS = 5`.
- `Plan.md` is special-cased and excluded from task lists
  (`ralph_wiggum_loop.py:287`, `scripts/run_ai_employee.py:94`) — don't treat it as a task.
- `AI_Employee_Vault/`, `logs/`, and `*.log` are git-ignored runtime state, but many `Done/`,
  `Errors/`, and `Inbox/` fixtures *are* committed. Don't mistake them for source.

## Config: `.env` is partial and inconsistently loaded

`.env.example` is fully commented out — copying it yields an empty, valid config.
Bronze needs no config; every LLM/integration path degrades to a template or a no-op.

- **Two different `.env` loaders.** Social/accounting/MCP scripts use `python-dotenv`
  (`load_dotenv()`); `scripts/claude_reasoning_loop.py` uses a hand-rolled `load_env()`
  parser at line 39. A key that works for one may not reach the other.
- **`VAULT_PATH` is mostly a lie.** It is honored by only 4 skill scripts
  (`file_watcher.py:13`, `generate_sales_post.py:333,372`, `accounting_manager.py:252`).
  The core pipeline ignores it and hardcodes `AI_Employee_Vault`. Don't relocate the vault
  expecting the daemon to follow.
- **Silent LLM fallback.** `scripts/claude_reasoning_loop.py:generate_plans()` tries
  OpenRouter → Gemini → Claude → OpenAI → template. A missing key produces a *working*
  template plan with only a `logger.warning`. Absence of an LLM looks identical to success —
  check `logs/` before concluding a key is wired up.

## Skill scripts are drifted duplicates, not a synced layer

`.agents/skills/*/scripts/` re-implements most of `scripts/`, and the copies **have diverged**.
Verified identical: only `watch_gmail.py`. Notably `scripts/task_planner.py` is ~12.9KB vs
3.1KB in the `task-planner` skill — they are not the same program. Two different
`accounting_manager.py` also exist (4KB `accounting-manager` vs 12KB `odoo-manager` skill),
though `README.md` lists that same filename for both.

When changing pipeline behavior, edit the `scripts/` copy the orchestrators actually invoke.
Treat `.agents/skills/*/scripts/` as a parallel implementation, and check which one a caller
uses before assuming a fix took effect.

## Doc drift — trust code over prose

`README.md` / `SETUP_GUIDE.md` / `ARCHITECTURE.md` contain claims that are false in this checkout:

- `mcp/mcp-odoo-adv/` is documented at length but **does not exist**. Only `mcp/odoo-mcp/`
  and `mcp/ex-business-mcp/` are present.
- `CONTRIBUTING.md` is linked but absent.
- `docs/SILVER_TIER.md` documents a `--log-level` flag that `scripts/run_ai_employee.py`
  does not implement (it hardcodes `logger.setLevel(logging.INFO)`).
- `README.md` claims "18 Skills"; there are 22 skill dirs, 21 with a `SKILL.md`.
  `production-testing/` has no `SKILL.md` — just loose `.md` files.
- `GEMINI.md` hardcodes WSL paths (`/mnt/e/ai_employee/AI_Employee_Vault/...`) from a
  different checkout. Substitute the real `AI_Employee_Vault/` path.
- `ARCHITECTURE.md` lists `odoorpc` as a dependency; it is not in `requirements.txt`.

`GEMINI.md`'s "Process Tasks" / "Make a Plan" workflows are real conventions worth preserving
(set frontmatter `status: completed`, tick checkboxes, move to `Done/`, update `Dashboard.md`
sections, append to `System_Log.md`) — but its paths are stale.

## Safety rails — do not weaken

`scripts/ralph_wiggum_loop.py` gates autonomous execution on `MAX_ITERATIONS = 5` and an
`is_risky()` keyword scan (`post`, `send`, `delete`, `rm`, `kill`, `publish`, `email`, `tweet`,
`linkedin`, `remove`) that routes steps to `Needs_Approval/` and **skips** them
(lines 28-37, 321-325). Approval files block on a human writing `APPROVED`/`REJECTED`.

These are the only things preventing runaway posting/emailing to real accounts. Keep them when
editing the loop, and prefer routing new side-effecting capability through `Needs_Approval/`.
