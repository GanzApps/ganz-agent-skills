---
name: agent-ops-framework
version: 6.0.0
date_added: "2026-05-18"
last_updated: "2026-05-27"
description: "Multi-agent task framework with Supabase Realtime + polling, atomic claim, and standard task handlers. All Zeanna partner agents run this."
category: agent-orchestration
risk: medium
---

# Agent Ops Framework v6.0.0

Generic multi-agent task framework for Zeanna's partner agents (Mr. Kim, ZenoA, Miss X).

**Version:** All agents report `skill_version: v6.0.0` via heartbeat on startup.

---

## Architecture

```
Zeanna (Conductor)
    │
    │ INSERT task → agent_tasks
    ▼
Supabase: agent_tasks (Realtime ON)
    │
    ├─► INSERT event  ──► on_task_insert()  ──► claim → execute
    ├─► UPDATE event  ──► on_task_update()  ──► claim if unblocked
    ├─► DELETE event  ──► on_task_delete()  ──► log cancellation
    │
    │ Polling (every 30s) ──► catch missed events during reconnect
    ▼
All Agents (both run together)
    │
    └─► result → Discord source_channel
```

**Both Realtime and polling run simultaneously.** Realtime delivers instant delivery; polling catches any events during reconnection windows. This is not a "fallback" — polling is a safety net that runs always.

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v6.0.0 | 2026-05-27 | Realtime + polling both active, canonical worker template, blocked_by UPDATE handler |
| v5.0.0 | 2026-05-18 | Source channel tracking, heartbeat |
| v4.0.0 | 2026-05-15 | Unblock mechanism, heartbeat table |
| v3.0.0 | 2026-05-10 | Multi-agent via Supabase |

---

## Setup Prerequisites

Run these in Supabase SQL Editor before deploying any agent worker.

### 1. Create Tables

```sql
-- agent_tasks: the shared task queue
CREATE TABLE IF NOT EXISTS agent_tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE,
  agent_name TEXT,                          -- creator (usually zeanna)
  assigned_to TEXT,                         -- agent currently handling
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending','claimed','running','done','error','blocked'
  )),
  task_type TEXT NOT NULL CHECK (task_type IN (
    'research','code','image','video','file','deploy','setup','general'
  )),
  instruction TEXT NOT NULL,
  payload JSONB,
  priority INT DEFAULT 5,                   -- 1=critical, 5=normal, 10=low
  result TEXT,
  result_data JSONB,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  max_retries INT DEFAULT 3,
  blocked_by TEXT,                          -- task_id of prerequisite task
  source_channel TEXT NOT NULL,             -- 'discord:CHANNEL_ID'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  claimed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- agent_heartbeats: agent health + version tracking
CREATE TABLE IF NOT EXISTS agent_heartbeats (
  agent_name TEXT PRIMARY KEY,
  status TEXT DEFAULT 'idle' CHECK (status IN ('idle','busy')),
  current_task_id UUID,
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  skill_version TEXT,
  capabilities TEXT[]
);
```

### 2. Enable Realtime on agent_tasks

```sql
-- In Supabase dashboard: Database → Replication → agent_tasks
-- OR run:
ALTER PUBLICATION supabase_realtime ADD TABLE agent_tasks;
```

### 3. Register Agent Heartbeat

```sql
-- Register each agent. Run once per agent machine.
INSERT INTO agent_heartbeats (agent_name, status, capabilities, skill_version, last_seen)
VALUES
  ('mr-kim', 'idle', ARRAY['research','code'], 'v6.0.0', NOW()),
  ('zenoa',  'idle', ARRAY['file','code','deploy'], 'v6.0.0', NOW()),
  ('miss-x', 'idle', ARRAY['image','video','code'], 'v6.0.0', NOW())
ON CONFLICT (agent_name) DO UPDATE SET
  skill_version = EXCLUDED.skill_version,
  capabilities = EXCLUDED.capabilities,
  last_seen = NOW();
```

### 4. Verify Setup

```sql
SELECT agent_name, status, skill_version, last_seen FROM agent_heartbeats;
```

Expected: `skill_version = v6.0.0` for all registered agents.

---

## Canonical Worker

**Only one worker template:** `scripts/worker_template.py`

All agents use this same file. Configure via environment variables — no file edits needed per agent.

```bash
# Minimal env for worker
export SUPABASE_URL="https://lyhhfqbkwamodswxewql.supabase.co"
export SUPABASE_KEY="<from .env>"
export AGENT_NAME="mr-kim"           # change per agent
export AGENT_CAPABILITIES="research,code,general"
export SKILL_VERSION="v6.0.0"
export POLL_INTERVAL="30"

python3 scripts/worker_template.py
```

---

## How Tasks Flow

### Zeanna Creates Task

```python
supabase.table("agent_tasks").insert({
    "task_id": "my-task-001",
    "task_type": "code",
    "instruction": "Fix the login bug in https://github.com/owner/repo",
    "payload": {"repo": "https://github.com/owner/repo"},
    "priority": 3,
    "source_channel": "discord:1497264979160727724"
}).execute()
```

### INSERT Event → Agent Claims Instantly

Realtime fires `on_task_insert()` → agent checks:
1. `is_agent_idle()` — heartbeat says I'm free
2. `blocked_by` is null — no prerequisite blocking me
3. `task_type` in MY_CAPABILITIES — I can handle this
4. `assigned_to` is null or me — not already claimed

If all pass → `claim_task()` (atomic UPDATE WHERE status='pending') → `execute_task()` → result posted to `source_channel`.

### UPDATE Event → Agent Re-claims When Unblocked

When prerequisite completes, Zeanna clears `blocked_by`:

```python
supabase.table("agent_tasks").update({
    "status": "pending",
    "blocked_by": None
}).eq("id", task_id).execute()
```

Realtime fires `on_task_update()` → detects `blocked_by` was cleared → attempts claim immediately.

### Polling Catches Reconnection Gaps

If Realtime disconnects (network blip), `on_task_update()` won't fire during the gap. The polling thread wakes every 30s and claims any newly unblocked or new tasks the Realtime missed. Both run together.

---

## Task Handlers

Standard handler signature — all agents implement this map:

```python
TASK_HANDLERS = {
    "research": execute_research,
    "code":     execute_code,
    "image":    execute_image,
    "video":    execute_video,
    "file":     execute_file,
    "deploy":   execute_deploy,
    "setup":    execute_setup,
    "general":  execute_general,   # fallback for unknown types
}

def execute_task(task: dict) -> dict:
    task_type  = task.get("task_type", "general")
    instruction = task.get("instruction", "")
    payload     = task.get("payload", {}) or {}
    handler     = TASK_HANDLERS.get(task_type, execute_general)
    return handler(instruction, payload)
```

### Handler Signature

```python
def handler(instruction: str, payload: dict) -> dict:
    """
    Returns:
        {
            "status":     "done" | "error",
            "result":     str,       # Human-readable output
            "result_data": dict | None  # Structured: URLs, files, etc.
        }
    """
```

---

## Atomic Claim Protocol

```python
def claim_task(task_id: str) -> bool:
    """Atomically claim — only succeeds if status still pending."""
    result = supabase.table("agent_tasks").update({
        "status": "claimed",
        "assigned_to": AGENT_NAME,
        "claimed_at": datetime.utcnow().isoformat()
    }).eq("id", task_id).eq("status", "pending").execute()
    return len(result.data) > 0
```

**Rule:** Never UPDATE without `WHERE status='pending'`. If another agent claimed first, our UPDATE returns 0 rows → `claim_task()` returns False → we skip.

---

## Heartbeat Gate

Before claiming ANY task:

```python
def is_agent_idle() -> bool:
    hb = supabase.table("agent_heartbeats").select("status","current_task_id")\
           .eq("agent_name", MY_NAME).single().execute()
    if not hb.data:
        return True   # New agent, no record yet
    return hb.data["status"] == "idle" and hb.data.get("current_task_id") is None
```

**Only claim if `is_agent_idle() == True`.** If busy, skip — another task is already in progress.

---

## Prerequisite / Blocking

### Block a Task

```python
supabase.table("agent_tasks").update({
    "status": "blocked",
    "blocked_by": "some-prerequisite-task-id"
}).eq("id", task_id).execute()
```

### Unblock (when prerequisite done)

```python
supabase.table("agent_tasks").update({
    "status": "pending",
    "blocked_by": None
}).eq("id", task_id).execute()
```

The `on_task_update()` Realtime handler fires on this UPDATE → detects `blocked_by` cleared → claims immediately.

---

## Discord Notifications

Post to `source_channel` on every event:

| Status | Emoji | Message |
|--------|-------|---------|
| claimed | 🎯 | `🎯 {AGENT} claimed {task_id}` |
| running | ⏳ | `⏳ {AGENT} working on {task_id}` |
| done | ✅ | `✅ {AGENT} completed {task_id}: {result}` |
| error | 🔴 | `🔴 {AGENT} error on {task_id}: {message}` |
| retry | 🔁 | `🔁 {AGENT} retry {n}/{max_retries}: {reason}` |

`source_channel` format: `discord:CHANNEL_ID` (e.g. `discord:1497264979160727724`).
Working Agent thread for coordination: `1504502974632820787`.

---

## Environment Variables

**Required** — no hardcoded secrets:

```bash
SUPABASE_URL=https://lyhhfqbkwamodswxewql.supabase.co
SUPABASE_KEY=<from .env — NOT hardcoded>
AGENT_NAME=mr-kim              # or zenoa, miss-x
AGENT_CAPABILITIES=research,code,general
SKILL_VERSION=v6.0.0
POLL_INTERVAL=30               # seconds between poll cycles
DISCORD_BOT_TOKEN=<from .env>
GITHUB_TOKEN=<for code/deploy tasks — from .env>
```

---

## End-to-End Deploy Checklist

For a new agent machine, in order:

**Step 1 — Supabase setup (once per project)**
```sql
-- Run in SQL Editor (see Setup Prerequisites above)
```

**Step 2 — Clone the framework**
```bash
git clone https://github.com/GanzApps/ganz-agent-skills.git
cd ganz-agent-skills/skills/agent-orchestrator/agent-ops-framework
```

**Step 3 — Register heartbeat**
```sql
-- Run INSERT (see Setup Prerequisites step 3)
```

**Step 4 — Configure env**
```bash
export SUPABASE_URL="https://lyhhfqbkwamodswxewql.supabase.co"
export SUPABASE_KEY="<key from .env>"
export AGENT_NAME="mr-kim"
export AGENT_CAPABILITIES="research,code"
export SKILL_VERSION="v6.0.0"
```

**Step 5 — Test locally**
```bash
python3 scripts/worker_template.py
# Worker should log: "Agent worker starting — mr-kim v6.0.0"
# Should log: "Realtime subscription active"
```

**Step 6 — Configure systemd** (Linux only)
```ini
[Unit]
Description=Zeanna Agent Worker (%i)
After=network-online.target

[Service]
Type=simple
User=root
EnvironmentFile=/root/.openclaw/workspace/.env
WorkingDirectory=/root/.openclaw/workspace/skills/agent-ops-framework
ExecStart=/usr/bin/python3 scripts/worker_template.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable agent-worker@mr-kim
sudo systemctl start agent-worker@mr-kim
sudo journalctl -u agent-worker@mr-kim -f  # verify it's running
```

**Step 7 — Verify**
```sql
SELECT agent_name, status, skill_version, last_seen
FROM agent_heartbeats
WHERE agent_name = 'mr-kim';
```
Expected: `status = idle`, `skill_version = v6.0.0`, `last_seen` within 1 minute.

---

## Safety Rules

1. **Atomic claim only** — never UPDATE without `WHERE status='pending'`
2. **Heartbeat gate** — only claim when `is_agent_idle() == True`
3. **Max retries = 3** — hard limit; after that task goes to `error`
4. **blocked_by first** — skip any task with a non-null `blocked_by`
5. **Graceful shutdown** — on SIGTERM, mark current task `pending` for re-claim
6. **Realtime + polling both active** — polling is not optional, it catches reconnect gaps
7. **skill_version in heartbeat** — every agent reports `v6.0.0` on startup

---

## Files in This Framework

```
agent-ops-framework/
├── SKILL.md                      ← This file (v6.0.0)
├── CHANGELOG.md                  ← Version history
├── VERSION.md                    ← Version marker (v6.0.0)
├── docs/
│   ├── SETUP_QUICK.md            ← 5-min setup guide
│   └── SETUP_FULL.md             ← Detailed installation guide
└── scripts/
    ├── worker_template.py        ← Canonical worker (all agents use this)
    └── self_update.sh            ← Pull latest from GitHub (cron: hourly)
```

---

## Questions / Issues

→ Comment on https://github.com/GanzApps/ganz-agent-skills/pull/1