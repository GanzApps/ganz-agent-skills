---
name: agent-ops-framework
version: 6.0.0
date_added: "2026-05-18"
last_updated: "2026-05-27"
description: "Generic multi-agent task framework with Realtime + polling, atomic claim, and standard task handlers"
category: agent-orchestration
risk: medium
---

# Agent Ops Framework v6.0.0

Generic multi-agent task framework. All Zeanna partner agents (Mr. Kim, ZenoA, Miss X) run this framework to claim and execute tasks from a shared Supabase queue.

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v6.0.0 | 2026-05-27 | Realtime subscription + polling fallback, generic task handlers, INSERT/UPDATE/DELETE events |
| v5.0.0 | 2026-05-18 | Source channel tracking, Working Agent thread, heartbeat |
| v4.0.0 | 2026-05-15 | Unblock mechanism, agent heartbeat table |
| v3.0.0 | 2026-05-10 | Multi-agent via Supabase |
| v1-v2 | Earlier | Initial Zeanna setup |

---

## Architecture

```
Zeanna (Conductor)
    │
    │ creates task with source_channel
    ▼
Supabase: agent_tasks
    │
    │ INSERT/UPDATE/DELETE events
    ▼
All Agents (Realtime subscription) ──► Primary: instant via Realtime
    │                                     │
    │ polling fallback (every 30s)        │ Fallback: if Realtime fails
    ▼                                     ▼
    ┌──────────────────────────────────────┐
    │           Task Execution              │
    │  claim → execute → result → Discord  │
    └──────────────────────────────────────┘
```

---

## Tables Schema

### agent_tasks

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | uuid | ✅ | PK, auto-generated |
| task_id | text | ✅ | Human-readable ID, e.g. `markdown-renderer-001` |
| agent_name | text | | Original creator (zeanna) |
| assigned_to | text | | Agent currently handling |
| status | text | ✅ | `pending` `claimed` `running` `done` `error` `blocked` |
| task_type | text | ✅ | `research` `code` `image` `video` `file` `deploy` `setup` `general` |
| instruction | text | ✅ | Full task description (Markdown OK) |
| payload | jsonb | | Additional context: `{repo, depth, etc}` |
| priority | int | | 1=critical, 5=normal, 10=low. Default 5 |
| result | text | | Output/error message |
| result_data | jsonb | | Structured result: `{url, files, etc}` |
| error_message | text | | Error details |
| retry_count | int | | Current retry #. Default 0 |
| max_retries | int | | Hard limit. Default 3 |
| blocked_by | text | | task_id of blocking prerequisite |
| source_channel | text | ✅ | Origin channel: `discord:1497264979160727724` |
| created_at | timestamptz | ✅ | Auto |
| updated_at | timestamptz | | Auto on update |
| claimed_at | timestamptz | | When agent claimed |
| completed_at | timestamptz | | When done/error |

### agent_heartbeats

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| agent_name | text | ✅ | PK, e.g. `mr-kim` |
| status | text | ✅ | `idle` `busy` |
| current_task_id | uuid | | FK to agent_tasks.id |
| last_seen | timestamptz | ✅ | Last poll/heartbeat |
| skill_version | text | | e.g. `v6.0.0` — set by agent on startup |
| capabilities | text[] | | What this agent can handle |

---

## Task Lifecycle

```
pending → claimed → running → done
                    ↘ error → (retry logic)
pending → blocked (waiting on prerequisite)
```

### Status Meanings

| Status | Who Sets | Meaning |
|--------|----------|---------|
| `pending` | Zeanna | Ready for agent to claim |
| `claimed` | Agent | Agent picked it up, executing soon |
| `running` | Agent | Actively working |
| `done` | Agent | Completed successfully |
| `error` | Agent | Failed (may retry) |
| `blocked` | Agent or Zeanna | Waiting on prerequisite |

---

## Event Types (Realtime + Polling)

Agents listen for all three Supabase events:

| Event | Trigger | Agent Response |
|-------|---------|----------------|
| `INSERT` | New task created | Check if can handle → claim → execute |
| `UPDATE` | Task unblocked or reassigned | Check blocked_by cleared → claim if unclaimed |
| `DELETE` | Task cancelled | Stop processing if we claimed it |

### Priority Rules

When multiple tasks available:
1. Highest priority number first (1=critical)
2. Among same priority: oldest created_at first (FIFO)

---

## Generic Task Handlers

All agents implement this standard handler map:

```python
TASK_HANDLERS = {
    "research":   execute_research,
    "code":       execute_code,
    "image":      execute_image,
    "video":      execute_video,
    "file":       execute_file,
    "deploy":     execute_deploy,
    "setup":      execute_setup,
    "general":    execute_general,
}

def execute_task(task: dict) -> dict:
    """Standard task executor — route to handler by task_type."""
    task_type = task.get("task_type", "general")
    instruction = task.get("instruction", "")
    payload = task.get("payload", {})

    handler = TASK_HANDLERS.get(task_type, execute_general)
    return handler(instruction, payload)
```

### Required Handler Signature

```python
def handler(instruction: str, payload: dict) -> dict:
    """
    Returns:
        {
            "status": "done" | "error",
            "result": str,           # Human-readable output
            "result_data": dict | None  # Structured data: URLs, files, etc.
        }
    """
```

---

## Claim Protocol (Atomic)

### Step 1 — Verify can claim

```python
def can_claim_task(task: dict, agent_caps: list[str]) -> bool:
    return (
        task["status"] == "pending"
        and task.get("retry_count", 0) < task.get("max_retries", 3)
        and (task.get("assigned_to") is None or task.get("assigned_to") == MY_NAME)
        and task.get("blocked_by") is None
        and task["task_type"] in agent_caps
    )
```

### Step 2 — Atomic Claim

```python
def claim_task(task_id: str) -> bool:
    """Atomic claim — only succeeds if status still pending."""
    result = supabase.table("agent_tasks").update({
        "status": "claimed",
        "assigned_to": MY_NAME,
        "claimed_at": "now()"
    }).eq("id", task_id).eq("status", "pending").execute()
    return len(result.data) > 0
```

### Step 3 — On Failure

If claim fails (race condition) → skip, task went to another agent.

---

## Heartbeat Gate

Before claiming ANY task:

```python
def is_agent_idle() -> bool:
    hb = supabase.table("agent_heartbeats").select("*").eq("agent_name", MY_NAME).single().execute()
    if not hb.data:
        return True  # New agent, no record yet
    record = hb.data
    return record["status"] == "idle" and record.get("current_task_id") is None
```

**Only claim if `is_idle() == True`.** If busy, skip this cycle.

---

## Discord Notifications

### Rule: Post to `source_channel` on all events

| Event | Emoji | Example |
|-------|-------|---------|
| Claim | 🎯 | `🎯 {AGENT} claimed {task_id}` |
| Start | ⏳ | `⏳ {AGENT} working on {task_id}` |
| Progress | 🧵 | `🧵 {AGENT}: {update}` |
| Done | ✅ | `✅ {AGENT} completed {task_id}` |
| Error | 🔴 | `🔴 {AGENT} error on {task_id}: {error}` |
| Blocked | 🔒 | `🔒 {AGENT} blocked on {task_id}: {reason}` |

**Source channel** comes from `task["source_channel"]` (e.g. `discord:1497264979160727724`).

---

## Prerequisite / Blocking

### Block a Task

```python
supabase.table("agent_tasks").update({
    "status": "blocked",
    "blocked_by": prerequisite_task_id
}).eq("id", task_id).execute()
```

### Unblock

When prerequisite completes:
```python
supabase.table("agent_tasks").update({
    "status": "pending",
    "blocked_by": None
}).eq("id", task_id).execute()
```

Agent watching via Realtime `UPDATE` event will see `blocked_by` cleared and can claim.

---

## Environment Variables

Agents MUST have these set:

```bash
SUPABASE_URL=https://lyhhfqbkwamodswxewql.supabase.co
SUPABASE_KEY=<from .env — NOT hardcoded>
AGENT_NAME=mr-kim          # or zenoa, miss-x
DISCORD_BOT_TOKEN=<from .env — NOT hardcoded>
GITHUB_TOKEN=<for code tasks — NOT hardcoded>
SKILL_VERSION=v6.0.0       # reported to heartbeat on startup
```

---

## Supabase Realtime Subscription

### Primary Mode (Realtime)

```python
def subscribe_to_tasks():
    """Listen for INSERT/UPDATE/DELETE on agent_tasks."""
    supabase.channel("agent_tasks")
        .on("postgres_changes",
            {"event": "INSERT", "schema": "public", "table": "agent_tasks"},
            on_task_insert)
        .on("postgres_changes",
            {"event": "UPDATE", "schema": "public", "table": "agent_tasks"},
            on_task_update)
        .on("postgres_changes",
            {"event": "DELETE", "schema": "public", "table": "agent_tasks"},
            on_task_delete)
        .subscribe()
```

### Fallback Mode (Polling)

If Realtime connection fails, fall back to polling:

```python
POLL_INTERVAL = 30  # seconds
while True:
    if not realtime_connected:
        tasks = supabase.table("agent_tasks").select("*")\
            .eq("status", "pending")\
            .not_.is_("blocked_by", "not_is", None)\
            .in_("task_type", MY_CAPABILITIES)\
            .order("priority", desc=True)\
            .order("created_at")\
            .limit(5).execute()
        for task in tasks.data:
            process(task)
    time.sleep(POLL_INTERVAL)
```

---

## Safety Rules

1. **Atomic claim only** — never UPDATE without WHERE status='pending'
2. **Heartbeat gate** — only claim when idle
3. **Max retries = 3** — hard limit, after that task goes to error
4. **blockers first** — check `blocked_by` before claiming
5. **Post all events to source_channel** — claim/start/done/error/blocked
6. **Graceful shutdown** — on SIGTERM, mark current task as pending for re-claim
7. **Skill version** — report `skill_version=v6.0.0` to heartbeat on startup

---

## Files in This Framework

```
agent-ops-framework/
├── SKILL.md                      ← This file (v6.0.0)
├── CHANGELOG.md                  ← Version history
├── VERSION.md                    ← Current version marker
├── docs/
│   ├── SETUP_QUICK.md            ← 5-min setup guide
│   └── SETUP_FULL.md             ← Detailed installation
├── scripts/
│   ├── worker_template.py        ← Ready-to-run worker (generic)
│   ├── self_update.sh            ← Pull latest from GitHub
│   └── heartbeat_ping.sh         ← Keepalive ping
└── examples/
    ├── mr-kim-worker.py         ← Mr. Kim config
    ├── zenoa-worker.py           ← ZenoA config
    └── miss-x-worker.py          ← Miss X config
```

---

## Questions / Comments

→ Open an issue on https://github.com/GanzApps/ganz-agent-skills
