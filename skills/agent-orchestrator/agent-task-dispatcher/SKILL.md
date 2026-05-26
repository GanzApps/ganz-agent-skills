---
name: agent-task-dispatcher
description: "Create tasks in Supabase agent_tasks table for partner agents with prerequisite gating. Dispatches to Mr. Kim, Miss X, or ZenoA ONLY after verifying prerequisites are met."
category: agent-orchestration
risk: medium
---

# Agent Task Dispatcher

## Core Principle: Prerequisite Gating

**Before ANY insert to `agent_tasks`, run prerequisite check first.**

If prerequisites fail → create a setup/prerequisite task FIRST, then block the main task until it completes.

---

## Trigger Syntax

```
dispatch <agent> <task_type>: <instruction>
```

**Examples:**
```
dispatch mr-kim code: fix auth bug in backend
dispatch miss-x research: competitor analysis on fitness apps
dispatch zenoa code: add markdown renderer component to porto repo
dispatch mr-kim file: list files in /workspace
```

---

## Prerequisites Per Agent

| Check | Mr. Kim | Miss X | ZenoA |
|-------|---------|--------|-------|
| Heartbeat alive (< 30 min) | ✅ | ✅ | ✅ |
| GitHub token available | ✅ | ✅ | ✅ |
| Can clone repos from GitHub | ✅ | ✅ | ✅ |
| Has required task capability | ✅ | ✅ | ✅ |

---

## Prerequisite Verification (Required Before Insert)

```python
import subprocess
from datetime import datetime
import json

SUPABASE_URL = "https://lyhhfqbkwamodswxewql.supabase.co"
SERVICE_KEY = "MISSION_CONTROL_SUPABASE_SERVICE_KEY"

def verify_and_dispatch(agent: str, task_type: str, instruction: str,
                       payload: dict = None, source_channel: str = None,
                       repo_url: str = None):
    """
    Main dispatch function. Verifies prerequisites first.
    If blocked, creates prerequisite task THEN blocks main task.
    """
    task_id = f"{agent}-{int(datetime.now().timestamp())}"

    # STEP 1: Check prerequisites
    heartbeat = get_heartbeat(agent)
    blockers = []

    # Check 1: Heartbeat alive?
    if not heartbeat:
        blockers.append("HEARTBEAT_MISSING")
    else:
        last_seen = datetime.fromisoformat(heartbeat["last_seen"].replace("Z", "+00:00"))
        if (datetime.now(last_seen.tzinfo) - last_seen).total_seconds() > 1800:
            blockers.append("HEARTBEAT_STALE")

    # Check 2: GitHub credentials (for code/file/deploy tasks)?
    if task_type in ("code", "file", "deploy"):
        if not check_github_credentials(agent):
            blockers.append("GITHUB_CREDENTIALS_MISSING")

    # Check 3: Capability?
    caps = heartbeat.get("capabilities", []) if heartbeat else []
    if caps and task_type not in caps:
        blockers.append(f"CAPABILITY_MISSING:{task_type}")

    # STEP 2: If blocked, handle based on blocker type
    if blockers:
        # HUMAN GATE — GitHub token missing
        if "GITHUB_CREDENTIALS_MISSING" in blockers:
            # Tell Ganz directly (this is the human gate — do NOT auto-configure)
            # notify_Ganz should ping/DM Ganz: "🔑 {agent} needs a GitHub token"
            # Example: send message to Ganz via Discord DM
            # For now: return human_gate status
            insert_task({
                "task_id": task_id,
                "agent_name": agent,
                "task_type": task_type,
                "instruction": instruction,
                "payload": {**(payload or {}), "repo": repo_url},
                "status": "blocked",
                "assigned_to": agent,
                "source_channel": source_channel,
                "blocked_by": "HUMAN_GATE_GITHUB"
            })
            return {
                "status": "blocked_human",
                "task_id": task_id,
                "reason": "GITHUB_CREDENTIALS_MISSING",
                "message": f"🔑 {agent} needs a GitHub token. TELL GANZ directly. Task is blocked.",
                "blockers": blockers
            }

        # Other blockers (worker restart, etc.)
        prereq_task_id = f"prereq-{task_id}"
        prereq_instruction = build_prereq_instruction(blockers, agent)
        insert_task({
            "task_id": prereq_task_id,
            "agent_name": agent,
            "task_type": "setup",
            "instruction": prereq_instruction,
            "status": "pending",
            "payload": {"unblocks": task_id, "blockers": blockers}
        })
        insert_task({
            "task_id": task_id,
            "agent_name": agent,
            "task_type": task_type,
            "instruction": instruction,
            "payload": {**(payload or {}), "repo": repo_url},
            "status": "blocked",
            "assigned_to": agent,
            "source_channel": source_channel,
            "blocked_by": prereq_task_id
        })
        return {
            "status": "blocked",
            "task_id": task_id,
            "prerequisite": prereq_task_id,
            "blockers": blockers
        }

    # STEP 3: All clear — insert main task
    insert_task({
        "task_id": task_id,
        "agent_name": agent,
        "task_type": task_type,
        "instruction": instruction,
        "payload": {**(payload or {}), "repo": repo_url},
        "status": "pending",
        "assigned_to": agent,
        "source_channel": source_channel
    })
    return {"status": "dispatched", "task_id": task_id}


def build_prereq_instruction(blockers: list, agent: str) -> str:
    """Build instruction for prerequisite task based on blockers."""
    instructions = []
    if "HEARTBEAT_MISSING" in blockers or "HEARTBEAT_STALE" in blockers:
        instructions.append(
            f"Restart the {agent} worker. Ensure heartbeat script is running "
            f"and Update `agent_heartbeats` table with current timestamp."
        )
    # NOTE: GitHub credentials missing is a HUMAN GATE.
    # The main dispatch function should have already told GANZ directly.
    # This function only handles non-GitHub blockers.
    # GitHub blocker is resolved externally by Ganz.
    return " || ".join(instructions)


def check_github_credentials(agent_name: str) -> bool:
    """Check if agent has GitHub credentials."""
    if agent_name == "zenoa":
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "43.156.250.253",
             "echo $GITHUB_TOKEN | grep -q . && echo OK || echo MISSING"],
            capture_output=True, text=True, timeout=8
        )
        return "OK" in result.stdout
    else:
        result = subprocess.run(
            ["bash", "-c",
             "echo $GITHUB_TOKEN | grep -q . && echo OK || echo MISSING"],
            capture_output=True, text=True, timeout=5
        )
        return "OK" in result.stdout
```

---

## Repo in Task Instruction

**ALWAYS include GitHub repo URL in the instruction:**
```
dispatch zenoa code: add markdown renderer to porto
→ instruction must include: Repo: https://github.com/username/repo-name
```

**Template for repo-based tasks:**
```
Task: <description>
Repo: https://github.com/{owner}/{repo}
Branch: main
Steps:
1. git clone https://github.com/{owner}/{repo}.git (if not present)
2. <specific implementation steps>
3. git push origin branch-name
4. Create PR to main branch
```

---

## How It Works

```
User dispatch command
       │
       ▼
┌─────────────────────────┐
│  verify_prerequisites   │
│  1. Heartbeat alive?    │
│  2. GitHub token?       │
│  3. Capability match?  │
└─────────────────────────┘
       │
  ┌────┴────┐
  │ ALL OK  │  → insert task as "pending"
  │ BLOCKED │  → create prereq task → mark main as "blocked"
  └─────────┘
       │
  Partner agent polls → claims → executes → posts result
```

---

## Supabase Credentials

| Item | Value |
|------|-------|
| URL | `https://lyhhfqbkwamodswxewql.supabase.co` |
| Key | Service role key (for writes) |

## Agent Capabilities

| Agent | Handles | Notes |
|-------|---------|-------|
| mr-kim | code, research | Has Codex/shell execution |
| miss-x | code, research, image, video, file | Full executor |
| zenoa | code, image, video, file, deploy | Has Hermes/shell |

## Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Ready for agent to claim |
| `in_progress` | Agent is working on it |
| `completed` | Done, result posted |
| `failed` | Error after max retries |
| `blocked` | Waiting on prerequisite task |

## Queue Query Rules

**When listing or viewing the task queue:**
- Filter to active tasks only: `status in ('pending', 'blocked', 'in_progress')`
- Do NOT show `completed`, `done`, or `error` tasks in the active queue
- Sort: `priority DESC, created_at ASC` (highest priority first, oldest among same priority)
- Only unassigned tasks (`assigned_to IS NULL`) appear in the queue for agents to claim

**When re-queueing a task:**
- Set `assigned_to = null` before re-dispatching
- Set `status = 'pending'`
- Optionally bump priority if it became more urgent
- Do NOT re-dispatch with a stale `assigned_to` value

**Supabase query for active queue:**
```
GET /rest/v1/agent_tasks
?select=task_id,status,priority,blocked_by,task_type,created_at,instruction
&status=in.(pending,blocked,in_progress)
&order=priority.desc,created_at.asc
```

## Priority Guide

| Priority | Use When |
|----------|---------|
| 1 | Normal tasks |
| 3 | High priority, needs attention soon |
| 5 | Critical, drop everything |

---

## Verification

After dispatching, watch the source channel for the agent's response.

Expected response time: 30s-2min depending on task complexity.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Task shows "blocked" | Check `blocked_by` field — complete prerequisite first |
| Agent doesn't pick up | Check heartbeat: `SELECT * FROM agent_heartbeats` |
| GitHub credentials missing | Blocked task will auto-create setup task |
| Wrong agent assigned | Specify agent explicitly: `dispatch mr-kim ...` |
| Result posted wrong channel | Verify source_channel is set to current channel ID |
| Task stuck pending | Check if agent heartbeat is stale |
