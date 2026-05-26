# Agent Dispatch Protocol (from Ganz, 2026-05-26 updated)

## Core Principle: Prerequisite Gating First

**NEVER dispatch a task without verifying the agent can actually execute it.**

If prerequisites are not met → the task is BLOCKED until the prerequisite is resolved FIRST.

```
[New task received]
       │
       ▼
┌─────────────────────────┐
│  PREREQUISITE CHECK     │
│  1. Heartbeat alive?   │
│  2. GitHub token?      │
│  3. Has required cap?  │
└─────────────────────────┘
       │
  ┌────┴────┐
  │ ALL OK  │  → dispatch task
  │BLOCKED  │  → create prerequisite task FIRST
  └─────────┘    → block parent task until prerequisite done
  → Report status to user: "Blocked by X — setting up now"
```

---

## Dispatch → Watch → Relay Result Workflow

### Step 1: Prerequisite Check (MANDATORY — do this BEFORE inserting task)

Per-agent prerequisite checklist:

| Prerequisite | Mr. Kim | Miss X | ZenoA |
|---|---|---|---|
| Heartbeat alive (< 30 min) | ✅ | ✅ | ✅ |
| GitHub token available | ✅ | ✅ | ✅ |
| Can clone repos from GitHub | ✅ | ✅ | ✅ |
| Required task capability | ✅ | ✅ | ✅ |

### Step 2: If Blocked → Create Prerequisite Task First

```
IF any prerequisite is missing:
    1. Create prerequisite task with task_type="setup"
    2. Insert main task with status="blocked" AND blocked_by=<prereq_task_id>
    3. Tell Ganz: "Blocked by [reason] — creating prerequisite task first"
    4. Wait for prerequisite to complete
    5. Then change main task status to "pending" and let agent claim it
```

### Step 3: Dispatch (only when prerequisites pass)

- Insert task into Supabase `agent_tasks` immediately
- Tell Ganz "dispatched ✅" right away

### Step 4: Watch (non-blocking)

- After dispatch, periodically check `agent_tasks` for `status=done`
- Do NOT wait idle — continue handling other things

### Step 5: Relay Result to Ganz

- When task status = `done`, fetch result from `agent_tasks`
- Reply in the **same channel where Ganz originally asked**
- Include: task outcome summary, which agent did it, time taken
- Then clean up the thread if one was posted

**Key principle: Never dispatch and go quiet. Ganz always gets an answer.**

---

## Repo Access = GitHub (Not Local)

**All dispatched tasks use GitHub as the source of truth.**

- Local paths are NOT shared between agents
- Task instructions must include: `Repo: https://github.com/{owner}/{repo}`
- Agents clone from GitHub, not from local filesystem

```
WRONG: "The repo is at /root/.openclaw/workspace/ugan-saripudin-porto"
RIGHT: "Clone https://github.com/{owner}/{repo}.git"
```

---

## Supabase Endpoints

| Table | URL |
|-------|-----|
| agent_tasks | `https://lyhhfqbkwamodswxewql.supabase.co/rest/v1/agent_tasks` |
| agent_heartbeats | `https://lyhhfqbkwamodswxewql.supabase.co/rest/v1/agent_heartbeats` |
| agent_dispatch | `https://lyhhfqbkwamodswxewql.supabase.co/rest/v1/agent_dispatch` |

Service role key: `***SECRET***` (use from .env → MISSION_CONTROL_SUPABASE_SERVICE_KEY)

---

## Agent Status

| Agent | Last Heartbeat | Status | Capabilities |
|-------|--------------|--------|-------------|
| mr-kim | 2026-05-22 19:24 | ⚠️ stale | research, code, image |
| zenoa | 2026-05-25 20:57 | ⚠️ stale — worker may need restart | image, video, code, file |
| miss-x | unknown | ❌ stale — needs worker restart | research, code, image, video, file |
| zeanna | 2026-05-20 03:09 | ⚠️ own script dead | (main orchestrator) |

---

## Key Discord IDs

| Channel | ID |
|---------|-----|
| #general | `1497264979160727724` |
| #monitor | `1497596257160659185` |
| #Working Agent thread | `1504502974632820787` |

---

## Note on RLS

RLS enabled on all agent_* tables with "Allow service role all" policy — service role key has full access, anon key restricted.

---

## Per-Task Prerequisites Detail

### For Code/File/Deploy Tasks (all agents)

1. **GitHub token** — agent must have `GITHUB_TOKEN` env var set that can access the repo
2. For ZenoA (remote worker): check via SSH `ssh 43.156.250.253 'echo $GITHUB_TOKEN'`
3. Task instruction MUST include GitHub repo URL, not local path

**⚠️ Human Gate — GitHub Token (Security Rule):**
- **DO NOT** auto-configure or SSH inject a GitHub token
- **DO** tell Ganz immediately via ping/DM when an agent needs GitHub access
- **DO** mark the task as `blocked` with `blocked_by="HUMAN_GATE_GITHUB"`
- **DO** wait for Ganz to manually provide the token to the partner agent before proceeding
- Ganz controls credential distribution — agents do not self-provision secrets

### For Image/Video Tasks

1. **Heartbeat alive** — worker must be polling
2. **Required API keys** — Codex/MiniMax/etc keys must be in env

### Restarting Stale Workers

```
Mr. Kim: ssh to his machine → restart heartbeat script
ZenoA:  ssh 43.156.250.253 → restart zenoa heartbeat script
Miss X:  ssh to her machine → restart heartbeat script
```

---

## Skill Files

Updated (2026-05-26):
- `skills/multi-agent-task-orchestrator/SKILL.md` — added prerequisite gating section
- `workspace/skills/agent-task-dispatcher/SKILL.md` — added prerequisite check before insert
