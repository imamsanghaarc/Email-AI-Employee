# PLAN.md — AI Employee MCP

Build plan for turning this repo into a single hosted MCP server that any MCP-capable AI
agent can connect to, where each user supplies their own Odoo / Gmail / LinkedIn
credentials and no paid LLM API key is ever required.

> **Filename hazard — read this first.**
> This file is `PLAN.md` at the repo root, deliberately uppercase. It is **not** the same
> thing as `AI_Employee_Vault/Needs_Action/Plan.md`, which is a runtime artifact consumed by
> `scripts/ralph_wiggum_loop.py` (it reads `- [ ]` checkboxes and ticks them off).
> Never put this plan inside `AI_Employee_Vault/Needs_Action/` — `run_ai_employee.py --once`
> regex-rewrites *every* `- [ ]` to `- [x]` in that folder and moves the file to `Done/`,
> which would silently destroy it.

---

## 1. Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Single unified **MCP server** (FastMCP) | Both existing servers (`mcp/odoo-mcp`, `mcp/ex-business-mcp`) are already FastMCP, so this is a merge not a rewrite |
| D2 | Hosted on **Google Cloud Run**, free tier | 2M req/mo, 180k vCPU-s, 360k GiB-s; scales to zero. Cloud Run supports **streamable HTTP only, not stdio** |
| D3 | **No LLM calls anywhere** in the server | The connecting agent does all reasoning. Deletes `claude_reasoning_loop.py` LLM paths, `generate_sales_post.py`, and the `anthropic`/`openai` deps |
| D4 | **Email + password** auth | No external IdP; we own hashing and resets |
| D5 | Credentials in **Supabase Postgres** | See Open Blocker B1 — no correct project connected yet |
| D6 | **LinkedIn auto-post** ships | User decision. Risk documented in §5, not re-litigated here |
| D7 | **Public GitHub** | Requires the PII scrub in Phase 0 to land first |

## 2. Target architecture

```
MCP client (Claude Code / Cursor / opencode / Zed)
        │  streamable HTTP over HTTPS
        ▼
Cloud Run  ──  ai-employee-mcp (FastMCP)
        │            │
        │            ├─ auth         register / login / token (D4)
        │            ├─ creds        set_credentials / credentials_status / disconnect
        │            ├─ odoo         search_read, create_record, update_record, accounting_summary
        │            ├─ gmail        send_email, read_recent, mark_read   (OAuth2)
        │            ├─ linkedin     post_linkedin (D6, behind approval guardrail)
        │            └─ approval     request_approval / approval_status
        ▼
   Supabase Postgres — users, sessions, credentials (encrypted), approvals, audit_log
```

**No LLM in this diagram.** That is the whole point of D3.

### The credential pattern (why it is not "the tool asks the user")

MCP tool calls are one-shot request/response — a tool **cannot** pause, prompt a human, and
resume. So the requested UX is implemented as a protocol-legal equivalent:

1. Agent calls `post_linkedin(...)` with nothing stored
2. Server returns `{status: "credentials_required", provider: "linkedin", missing: [...]}`
3. Agent asks the user in normal chat
4. Agent calls `save_credentials(provider, creds)`
5. Agent retries the original call

To a user this is indistinguishable from "the tool asked me". Gmail additionally offers a
real OAuth2 browser flow so the Gmail credential never passes through chat at all.

## 3. Phases

Each phase ends green in CI before the next begins.

### Phase 0 — De-risk (do this first)
- [ ] Scrub real PII from `AI_Employee_Vault/Done/email_*.md` (8 files, real Gmail addresses)
- [ ] Move hardcoded Odoo password out of `scripts/setup_odoo_playwright.py:18`
- [ ] `git init`, tighten `.gitignore` (vault captured content, `logs/`, `.env`)
- [ ] First commit + push to public GitHub

### Phase 1 — Package & merge
- [ ] `pyproject.toml`, `ai_employee_mcp/` package, console entrypoint
- [ ] Merge the two servers into one FastMCP app; preserve existing tool names
- [ ] Dual transport: stdio (local dev) **and** streamable HTTP (Cloud Run)
- [ ] Config layer: typed settings, no bare `os.environ.get` scattered per module

### Phase 2 — Credentials
- [ ] AES-GCM envelope encryption for secrets at rest
- [ ] `set_credentials` / `credentials_status` / `disconnect`
- [ ] `credentials_required` structured error on every tool that needs a provider
- [ ] Migration files for `users`, `sessions`, `credentials`, `approvals`, `audit_log`
- [ ] **Hard rule:** raw third-party passwords are never returned by any tool

### Phase 3 — Auth
- [ ] Argon2id password hashing + per-user salt
- [ ] `register` / `login` / `logout` / `token`; bearer auth on every tool
- [ ] Session expiry + revoke
- [ ] Rate limiting on login (brute force)

### Phase 4 — Guardrails
- [ ] `approval_required` gate on all side-effecting tools (post / send / delete)
- [ ] Human writes `APPROVED`/`REJECTED`; default-deny on timeout
- [ ] Per-tool permission scopes per user
- [ ] Immutable `audit_log` for every credential read, auth attempt, and side effect
- [ ] Explicit cap on autonomous bulk actions, replacing the vault loop's `MAX_ITERATIONS`

### Phase 5 — Providers
- [ ] Odoo: JSON-RPC, API-key auth, input validation on model names
- [ ] Gmail: OAuth2 flow, token refresh, send/read/mark-read
- [ ] LinkedIn: Playwright auto-post per D6, hard rate limit, fails closed
- [ ] `Dockerfile`, non-root user, read-only rootfs
- [ ] `/healthz` and `/readyz` endpoints for Cloud Run

### Phase 6 — Tests (real, no mocks-only theatre)
- [ ] `pytest` suite — this repo currently has **zero** Python tests
- [ ] Unit: encryption round-trip, auth, permission checks, tool schemas
- [ ] Integration: FastMCP in-memory client against fake Odoo/Gmail servers
- [ ] Live smoke tests gated behind `LIVE=1` + real creds, **never** in CI by default
- [ ] No test may post to a real social account without explicit human approval

### Phase 7 — CI/CD
- [ ] GitHub Actions: lint + typecheck + unit/integration tests on push & PR
- [ ] Dependency review, secret scanning, pinned actions
- [ ] `gcloud run deploy` on tag, gated behind a manual approval environment
- [ ] Migration apply as a separate manual step — **never** auto-run on push

### Phase 8 — Deploy
- [ ] Cloud Run: streamable HTTP, `--no-allow-unauthenticated`
- [ ] Production Supabase project + migrations applied
- [ ] Smoke test the deployed `/mcp` endpoint with a real MCP client
- [ ] README rewrite: the current one documents a non-existent `mcp/mcp-odoo-adv/`

## 4. Testing strategy

There is no existing test suite — `tests/` holds 17 `.md` fixtures, and README's
`pytest tests/` does nothing. So the suite is built from scratch. Layers:

- **Unit** — fast, no network, no credentials. Runs on every commit.
- **Integration** — FastMCP in-memory client against local fake Odoo/Gmail HTTP servers.
  Proves tool wiring and the credentials_required contract.
- **Live** — real accounts, opt-in via `LIVE=1`. Every live test that writes to an external
  system requires explicit human approval first. Excluded from CI.

A change is "done" when unit + integration pass and a real MCP client has exercised it —
not when a diagnostic script printed `success` (see `scripts/test_linkedin_integration.py`).

## 5. Known risks — accepted, documented, not resolved

- **LinkedIn ToS (D6).** No official posting API exists; browser automation violates
  LinkedIn's Terms. Accounts can be restricted or banned. Mitigated by rate limits, the
  Phase 4 approval gate, and failing closed — but the risk is inherent to the feature.
  Users must be told plainly before connecting a real account.
- **Credential custody.** Hosting centrally means holding users' Odoo/Gmail/LinkedIn
  secrets. A breach compromises every user. Mitigated by envelope encryption, per-user
  scoping, audit log, and never returning raw secrets.
- **Cloud Run ephemeral filesystem.** No SQLite on disk, ever — scale-to-zero wipes it.
  All state in Supabase (D5).
- **Free-tier limits.** 2M req/mo is generous but not infinite; per-user quotas required
  before any public launch.

## 6. Open blockers — need a human

- **B1 — Supabase project.** The only connected Supabase project is an unrelated
  **student portal** app (`students`, `fee_payments`, `enrollments`, 219 visitor rows).
  AI Employee tables must **not** go there. Need a fresh project, connected to this repo.
- **B2 — Cloud Run access.** `gcloud` is not installed here and no GCP project is
  configured. Deployment and all live smoke tests are blocked on this machine.
- **B3 — Git remote.** Not a git repo yet. CI cannot run until a GitHub remote exists.