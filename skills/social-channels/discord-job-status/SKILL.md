---
name: discord-job-status
description: "Post live job/agent execution progress to Discord #monitor channel using single-message editing (Miss X style). Use when: (1) tracking multi-step task progress, (2) running agents/subagents and showing live status, (3) any long-running operation needs visible Discord progress updates. Centralizes all progress to #monitor channel without spawning new threads."
category: discord-automation
risk: safe
---

# Discord Job Status — Miss X Style Progress Tracker

Post live execution progress to Discord #monitor with single-message editing. One message per task, edited in-place as work progresses. No thread spam, no system message clutter.

## When to Use

- Multi-step agent tasks needing visible progress
- Long-running operations (research, builds, deployments)
- Swarm mode coordination — track parallel agents
- Any task where Ganz wants to see live status in Discord

## How It Works

```
Task Start   →  🛠️ **Task Name**
                ⏳ Initializing...
                
Progress     →  🔧 **Task Name**
                Running: web_search
                
Tool Done    →  ✅ web_search — 3 results
                
Complete     →  ✅ **Task Name** (12s)
                Found 3 results, saved to file
```

**Key behavior:** Same Discord message is edited throughout. No new messages, no threads.

## Scripts

### monitor_progress.py — Core Engine

Path: `scripts/monitor_progress.py`

**Commands:**

```bash
# Start tracking a task
python3 scripts/monitor_progress.py start <task_key>
# Returns: message_id

# Update progress
python3 scripts/monitor_progress.py update <task_key> <status> [details]
# status: running | progress | done | failed | waiting

# Mark complete
python3 scripts/monitor_progress.py finish <task_key> <success> [result_text]
# success: true | false

# Clear all progress messages
python3 scripts/monitor_progress.py clear
```

**Python API:**

```python
from scripts.monitor_progress import (
    get_or_create_progress_message,
    update_progress,
    finish_progress
)

# Start
task_key = "research-task-001"
get_or_create_progress_message(task_key)

# Update
update_progress(task_key, 'progress', 'Running: web_search')

# Finish
finish_progress(task_key, True, 'Found 5 sources', duration=15.3)
```

### progress_hook.py — Tool Call Interceptor

Path: `scripts/progress_hook.py`

Wraps tool execution with automatic Discord updates:

```python
from scripts.progress_hook import on_task_start, on_tool_start, on_tool_done, on_task_done

on_task_start("my-task", "Researching AI news")
on_tool_start("my-task", "web_search", {"query": "AI news"})
on_tool_done("my-task", "web_search", True, "3 results")
on_task_done("my-task", True, "Complete", 12.5)
```

### agent_runner.py — Command Wrapper

Path: `scripts/agent_runner.py`

Run any shell command with live Discord progress:

```bash
python3 scripts/agent_runner.py deploy "Deploying to production" \
  bash -c "./deploy.sh && echo 'Done'"
```

## Integration Patterns

### Pattern 1: Direct Python Import

```python
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/discord-job-status/scripts')
from monitor_progress import update_progress, finish_progress

def my_long_task():
    task = "data-processing"
    update_progress(task, 'running', 'Starting data processing...')
    
    # ... do work ...
    update_progress(task, 'progress', 'Step 2/5: Cleaning data')
    
    # ... more work ...
    finish_progress(task, True, 'Processed 10K records', 45.2)
```

### Pattern 2: Shell Command Wrapper

```bash
#!/bin/bash
TASK="backup-$(date +%s)"
python3 scripts/monitor_progress.py start "$TASK"

python3 scripts/monitor_progress.py update "$TASK" progress "Running: tar czf backup.tar.gz"
tar czf backup.tar.gz /data || {
    python3 scripts/monitor_progress.py finish "$TASK" false "tar failed"
    exit 1
}

python3 scripts/monitor_progress.py finish "$TASK" true "Backup complete: $(du -h backup.tar.gz)"
```

### Pattern 3: Swarm Mode Integration

When spawning subagents, track them centrally:

```python
from scripts.monitor_progress import update_progress

# In conductor loop:
for agent in running_agents:
    update_progress(
        f"swarm-{agent.id}", 
        'progress',
        f"Agent {agent.name}: {agent.status} ({agent.progress}%)"
    )
```

## Configuration

**Discord Channel:** `#monitor` — ID `1497596257160659185`

**Token source:** `~/.openclaw/openclaw.json` → `channels.discord.token`

**State file:** `~/.openclaw/workspace/state/monitor_progress.json` (tracks message IDs per task)

## Discord Format Rule (CRITICAL)

All progress messages MUST use `monitor_progress.py` — NOT native Discord `message` tool.

**Why:** Native Discord integration shows generic "discord" label. Custom progress shows `#channelname`.

**Correct format:**
```
🔧 task-name
⏳ Initializing...
📍 #monitor
```

**Incorrect format (DO NOT USE):**
```
🔧 • https://discord.com/channels/... • discord • 22:44 ❌ 0s
```

**Enforcement:**
- All async workflows must use `monitor_progress.py` via `exec`
- Never use `message` tool for progress updates
- Channel name auto-fetched from Discord API

**Example usage in workflows:**
```python
# At start
exec: python3 monitor_progress.py start {task_key}

# At each phase
exec: python3 monitor_progress.py update {task_key} progress "Phase 2/5..."

# At finish
exec: python3 monitor_progress.py finish {task_key} true "Done in 45s"
```

## Troubleshooting

**Message not updating?**
- Check `monitor_progress.json` for stale message IDs
- Run `python3 scripts/monitor_progress.py clear` to reset

**401 Unauthorized?**
- Discord bot token stale — check `openclaw.json`
- Bot needs `Send Messages` and `Edit Messages` permissions in #monitor

**Rate limited?**
- Discord allows 5 edits per 5 seconds per message
- Progress updates are batched if needed
