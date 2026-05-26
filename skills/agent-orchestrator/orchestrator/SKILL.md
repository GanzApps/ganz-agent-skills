---
name: multi-agent-task-orchestrator
description: "Route tasks to specialized AI agents with prerequisite gating, anti-duplication, quality gates, and 30-minute heartbeat monitoring"
category: agent-orchestration
risk: safe
source: community
source_repo: milkomida77/guardian-agent-prompts
source_type: community
date_added: "2026-04-09"
author: milkomida77
tags: [multi-agent, orchestration, task-routing, quality-gates, anti-duplication, prerequisite-gating]
tools: [claude, cursor, gemini]
---

# Multi-Agent Task Orchestrator

## Core Principle: Prerequisite Gating First

**NEVER dispatch a task without verifying the agent can actually execute it.**

Every dispatch follows this decision tree:

```
[New task received]
       │
       ▼
┌─────────────────────────┐
│  PREREQUISITE CHECK     │
│  1. Heartbeat alive?   │
│  2. GitHub repo access?│
│  3. Required skills?   │
│  4. Required tools?    │
│  5. Environment ready?│
└─────────────────────────┘
       │
  ┌────┴────┐
  │ ALL OK  │  → dispatch task
  │BLOCKED  │  → create prerequisite sub-task FIRST
  └─────────┘    → block parent task until prerequisite is done
```

---

## Step 1: Prerequisite Verification (MANDATORY)

Before inserting ANY task into `agent_tasks`, verify these per-agent prerequisites:

### Per-Agent Prerequisite Checklist

| Prerequisite | Mr. Kim | Miss X | ZenoA |
|---|---|---|---|
| Heartbeat alive (< 30 min) | ✅ | ✅ | ✅ |
| GitHub token / credentials | ✅ | ✅ | ✅ |
| Can clone repos from GitHub | ✅ | ✅ | ✅ |
| Has required task capability | ✅ | ✅ | ✅ |
| Node.js / npm (if needed) | ⚠️ shell | ⚠️ shell | ⚠️ shell |
| Required npm packages | per-task | per-task | per-task |

### Prerequisite Verification Steps

```python
import subprocess
from datetime import datetime, timedelta
import json, os

SUPABASE_URL = "https://lyhhfqbkwamodswxewql.supabase.co"
SERVICE_KEY = os.environ.get("MISSION_CONTROL_SUPABASE_SERVICE_KEY")  # service role

def verify_prerequisites(agent_name: str, task_type: str, task_id: str) -> dict:
    """
    Returns: {"ready": bool, "blocked_by": list[str], "actions": list[dict]}
    """
    blockers = []
    actions = []

    # 1. Check heartbeat
    heartbeat = get_heartbeat(agent_name)
    if not heartbeat:
        blockers.append("HEARTBEAT_MISSING")
        actions.append({
            "type": "worker_restart",
            "agent": agent_name,
            "reason": "No heartbeat record — worker not registered"
        })
    else:
        last_seen = datetime.fromisoformat(heartbeat["last_seen"].replace("Z", "+00:00"))
        age = (datetime.now(last_seen.tzinfo) - last_seen).total_seconds()
        if age > 1800:  # 30 min
            blockers.append("HEARTBEAT_STALE")
            actions.append({
                "type": "worker_restart",
                "agent": agent_name,
                "reason": f"Heartbeat is {age//60:.0f} min old — worker may be dead"
            })

    # 2. Check GitHub credentials (for code/file/deploy tasks)
    if task_type in ("code", "file", "deploy"):
        has_github = check_github_credentials(agent_name)
        if not has_github:
            blockers.append("GITHUB_CREDENTIALS_MISSING")
            actions.append({
                "type": "human_gate",
                "agent": agent_name,
                "reason": "No GitHub token. TELL GANZ (ping/DM) immediately — do NOT auto-configure. Block the task until Ganz manually provides the token to the partner agent."
            })

    # 3. Check required capability
    capabilities = heartbeat.get("capabilities", []) if heartbeat else []
    if task_type not in capabilities and capabilities != []:
        blockers.append(f"CAPABILITY_MISSING:{task_type}")
        actions.append({
            "type": "note",
            "agent": agent_name,
            "reason": f"Agent capability '{task_type}' not in {capabilities}"
        })

    return {
        "ready": len(blockers) == 0,
        "blocked_by": blockers,
        "actions": actions
    }

def check_github_credentials(agent_name: str) -> bool:
    """
    Check if agent has GitHub credentials.
    Agents need: GITHUB_TOKEN env var or ~/.ssh/id_rsa with access to the repo.
    """
    if agent_name == "zenoa":
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "43.156.250.253",
             "echo $GITHUB_TOKEN | grep -q . && echo OK || echo MISSING"],
            capture_output=True, text=True, timeout=8
        )
        return "OK" in result.stdout
    elif agent_name in ("mr-kim", "miss-x"):
        result = subprocess.run(
            ["bash", "-c", "echo $GITHUB_TOKEN | grep -q . && echo OK || echo MISSING"],
            capture_output=True, text=True, timeout=5
        )
        return "OK" in result.stdout
    return False
```

### Handling Blocked Tasks

```
IF verify_prerequisites() returns ready=False:
    1. Identify blocker type:
       - GITHUB_CREDENTIALS_MISSING → HUMAN GATE (tell Ganz, do NOT auto-configure)
       - HEARTBEAT_STALE / HEARTBEAT_MISSING → create setup task to restart worker
       - CAPABILITY_MISSING → note it, block task
    2. If HUMAN GATE:
       - Ping/DM Ganz immediately: "🔑 {agent} needs a GitHub token"
       - Insert task with status="blocked" and blocked_by="HUMAN_GATE_GITHUB"
       - Do NOT attempt to auto-configure the token
       - Wait for Ganz to confirm token is set before proceeding
    3. If other blocker:
       - Create prerequisite task with task_type="setup"
       - Mark main task as "blocked" linking to prerequisite task_id
       - Relay status to Ganz: "Blocked by X — setting up now"
    4. Only dispatch main task AFTER prerequisite completes
```

**Example blocked dispatch (with human gate):**
```
### Human Gate: GitHub Token (Security Rule)

**This is non-negotiable.**

When an agent lacks a GitHub token for a code/file/deploy task:
- **DO NOT** try to auto-configure, SSH inject, or guess the token
- **DO** tell Ganz immediately via ping/DM
- **DO** wait for Ganz to manually provide the token to the partner agent
- **DO** insert the task as `blocked` with `blocked_by="HUMAN_GATE_GITHUB"` until Ganz confirms

This is by design — Ganz controls which agents get access to which credentials. No agent self-provisions secrets.

```python
def notify_Ganz(message: str):
    # Send to Ganz via DM or ping in channel
    send_discord_dm("637310490023821323", message)
    # or post to channel with @ mention
    post_to_channel("🔑 " + message)
```
python
main_task_id = "markdown-renderer-upgrade"
prereq = verify_prerequisites("zenoa", "code", main_task_id)

if not prereq["ready"]:
    # HUMAN GATE — GitHub token missing
    if "GITHUB_CREDENTIALS_MISSING" in prereq["blocked_by"]:
        # Step 1: Tell Ganz directly (ping/DM) that agent needs a GitHub token
        notify_Ganz(
            f"🔑 `{agent_name}` needs a GitHub token to work on code tasks. "
            f"Please share the token directly with {agent_name} (not through me). "
            f"Task '{main_task_id}' is blocked until then."
        )
        # Step 2: Insert task as blocked with human_gate marker
        insert_task({
            "task_id": main_task_id,
            "agent_name": agent_name,
            "task_type": task_type,
            "instruction": instruction,
            "status": "blocked",
            "payload": {"repo": repo_url},
            "blocked_by": "HUMAN_GATE_GITHUB"
        })
        return {"status": "blocked_human", "reason": "awaiting_github_token", "task_id": main_task_id}

    # Non-GitHub blockers (worker restart, etc.) — create prerequisite task
    prereq_task_id = f"prereq-{main_task_id}"
    insert_task({
        "task_id": prereq_task_id,
        "task_type": "setup",
        "instruction": build_prereq_instruction(prereq["blocked_by"], agent_name),
        "status": "pending",
        "payload": {"unblocks": main_task_id}
    })
    update_task(main_task_id, {
        "status": "blocked",
        "blocked_by": prereq_task_id
    })
    return {"status": "blocked", "prerequisite": prereq_task_id}
```

---

## Step 2: Repo Access = GitHub (Not Local)

**CRITICAL: All dispatched tasks must use GitHub as the source of truth.**

- Agents clone from GitHub, not from local filesystem
- Task instructions must include the GitHub repo URL
- Local copies are not shared between agents unless explicitly synced

```
WRONG: "The repo is at /root/.openclaw/workspace/ugan-saripudin-porto"
RIGHT: "Clone from https://github.com/username/repo-name"
```

**Repo instruction template:**
```
Repo: https://github.com/{owner}/{repo}
Branch: main (or specify)
Clone if not present: git clone https://github.com/{owner}/{repo}.git
```

---

## Step 3: Task Routing with Capability Matching

Use keyword scoring to match tasks to the best agent:

```python
AGENTS = {
    "mr-kim": ["code", "implement", "function", "research", "analyze", "bug", "fix", "refactor", "api"],
    "miss-x": ["code", "research", "image", "video", "file", "test", "document"],
    "zenoa": ["code", "deploy", "image", "video", "file", "setup", "config"],
}

def route_task(description: str, required_task_type: str = None) -> str:
    """Route task to best-fit agent based on keywords and capabilities."""
    if required_task_type:
        # Direct request: route to specified agent if they have the capability
        for agent, caps in AGENTS.items():
            if required_task_type in caps:
                return agent
        return "mr-kim"  # safe fallback

    # Infer from keywords
    scores = {}
    for agent, keywords in AGENTS.items():
        scores[agent] = sum(1 for kw in keywords if kw in description.lower())
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "mr-kim"
```

---

## Step 4: Quality Gates

Agent output is a CLAIM. Test output is EVIDENCE.

```
After agent reports completion:
1. Were files actually modified? (git diff --stat)
2. Do tests pass? (npm test / pytest)
3. Were secrets introduced? (grep for API keys, tokens)
4. Did the build succeed? (npm run build)
5. Were only intended files touched? (scope check)
6. Verify PR was created on GitHub, not just local commits

Mark done ONLY after ALL checks pass.
```

---

## Step 5: 30-Minute Heartbeat Monitor

```
Every 30 minutes, ask:
1. "What have I DELEGATED in the last 30 minutes?"
2. If nothing → open the task backlog and assign the next task
3. Check for idle agents (no message in >30min on assigned task)
4. Relance idle agents or reassign their tasks
```

---

## Dispatch Flow

```
Zeanna (Orchestrator)
       │
       ▼
┌─────────────────────┐
│ PREREQUISITE CHECK  │
│ 1. Heartbeat alive? │
│ 2. GitHub token?    │
│ 3. Capability match?│
└─────────────────────┘
       │
  ┌────┴────┐
  │ PASS    │  → insert task → partner polls → executes → PR on GitHub
  │ FAIL    │  → create prerequisite task FIRST
  │         │    → block main task until prerequisite done
  └─────────┘
```

---

## Supabase Schema

```sql
CREATE TABLE IF NOT EXISTS agent_tasks (
  id UUID DEFAULT gen_random_uuid(),
  task_id TEXT PRIMARY KEY,
  agent_name TEXT,
  instruction TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  -- statuses: pending, in_progress, completed, failed, blocked
  result TEXT,
  result_data JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  task_type TEXT,
  payload JSONB,
  assigned_to TEXT,
  result_url TEXT,
  claimed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  priority INT DEFAULT 1,
  retry_count INT DEFAULT 0,
  max_retries INT DEFAULT 3,
  error_message TEXT,
  discord_message_id TEXT,
  source_channel TEXT,
  blocked_by TEXT  -- task_id of the prerequisite blocking this task
);

CREATE TABLE IF NOT EXISTS agent_heartbeats (
  agent_name TEXT PRIMARY KEY,
  status TEXT,
  current_task_id TEXT,
  last_seen TIMESTAMPTZ,
  capabilities TEXT[],
  version TEXT,
  skill_version TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_blocked ON agent_tasks(blocked_by);
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent not picking up tasks | Register agent in `agent_heartbeats` table first |
| Heartbeat stale | Restart worker script, update heartbeat record |
| GitHub credentials missing | Create setup task to install/configure GITHUB_TOKEN |
| Task blocked | Check `blocked_by` field, complete prerequisite first |
| Wrong agent assigned | Specify agent explicitly in dispatch |
| Result posted wrong channel | Verify source_channel is set correctly |
| Task stuck pending | Check if agent is idle: `SELECT status FROM agent_heartbeats` |
| Agent claims done but no PR | Execute quality gate: check git log and GitHub for PR |

## Related Skills

- `@agent-task-dispatcher` - For creating tasks via Supabase
- `@code-review` - For reviewing code after delegation
