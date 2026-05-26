# Agent Ops Framework v6 — Full Setup Guide

## Architecture Overview

```
Zeanna → agent_tasks (Supabase) → Agent (Realtime or Polling) → Discord source_channel
                                    ↑
                              Worker Template
                              (Generic v6.0.0)
```

## Prerequisite Check

Before starting, verify:
1. Supabase tables exist with correct schema
2. Agent has Discord bot token with Message Content Intent
3. GitHub token set (for code/deploy tasks)
4. Agent name registered in `agent_heartbeats`

## Supabase Setup

Run in SQL Editor:
```sql
-- agent_tasks table (if not exists)
CREATE TABLE IF NOT EXISTS agent_tasks (
  id UUID DEFAULT gen_random_uuid(),
  task_id TEXT PRIMARY KEY,
  agent_name TEXT,
  assigned_to TEXT,
  status TEXT DEFAULT 'pending',
  task_type TEXT NOT NULL,
  instruction TEXT NOT NULL,
  payload JSONB,
  priority INT DEFAULT 5,
  result TEXT,
  result_data JSONB,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  max_retries INT DEFAULT 3,
  blocked_by TEXT,
  source_channel TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  claimed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- agent_heartbeats table (if not exists)
CREATE TABLE IF NOT EXISTS agent_heartbeats (
  agent_name TEXT PRIMARY KEY,
  status TEXT DEFAULT 'idle',
  current_task_id UUID,
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  skill_version TEXT,
  capabilities TEXT[]
);

-- Enable Realtime on agent_tasks
ALTER PUBLICATION supabase_realtime ADD TABLE agent_tasks;
```

## Manual Agent Registration

```sql
INSERT INTO agent_heartbeats (agent_name, status, capabilities, skill_version)
VALUES ('mr-kim', 'idle', ARRAY['research','code'], 'v6.0.0')
ON CONFLICT (agent_name) DO NOTHING;
```

## Skill Update

```bash
# Auto-update via cron (hourly)
curl -sL https://raw.githubusercontent.com/GanzApps/ganz-agent-skills/main/scripts/self_update.sh | bash

# Manual
cd /root/.openclaw/workspace/skills/agent-ops-framework
git pull origin main
```

## Task Creation (Zeanna)

```python
supabase.table("agent_tasks").insert({
    "task_id": "my-task-001",
    "task_type": "code",
    "instruction": "Fix the login bug",
    "payload": {"repo": "https://github.com/owner/repo"},
    "priority": 3,
    "source_channel": "discord:1497264979160727724"
}).execute()
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent not picking up tasks | Check `agent_heartbeats.skill_version` is set |
| Realtime not connecting | Check Supabase project has Realtime enabled |
| Discord posts fail | Verify bot has Message Content Intent |
| Claim race condition | Normal — another agent won, skip this task |
