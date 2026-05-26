# Agent Ops Framework v6 — 5-Minute Setup

## Requirements
- Python 3.8+
- Internet (for Supabase + GitHub)
- Discord bot token

## 1. Clone Framework

```bash
git clone https://github.com/GanzApps/ganz-agent-skills.git
cd ganz-agent-skills/skills/agent-orchestrator/agent-ops-framework
```

## 2. Set Environment Variables

```bash
export SUPABASE_URL="https://lyhhfqbkwamodswxewql.supabase.co"
export SUPABASE_KEY="<from .env>"
export AGENT_NAME="mr-kim"      # or: zenoa, miss-x
export AGENT_CAPABILITIES="research,code,image,video,file"
export SKILL_VERSION="v6.0.0"
export DISCORD_BOT_TOKEN="<from .env>"
```

## 3. Configure Agent Name

Edit `scripts/worker_template.py`:
```python
AGENT_NAME = os.getenv("AGENT_NAME", "mr-kim")  # change per agent
AGENT_CAPABILITIES = os.getenv("AGENT_CAPABILITIES", "research,code").split(",")
```

## 4. Run

```bash
python3 scripts/worker_template.py
```

## 5. Verify

Check Supabase heartbeat:
```sql
SELECT agent_name, status, skill_version, last_seen
FROM agent_heartbeats
WHERE agent_name IN ('mr-kim', 'zenoa', 'miss-x');
```

Expected: `skill_version = v6.0.0`, `status = idle`

## What Happens

1. Worker starts → subscribes to Supabase Realtime
2. Worker reports `skill_version=v6.0.0` to heartbeat
3. Zeanna creates task → INSERT event fires → agent claims instantly
4. Agent executes → posts to source_channel → marks done
5. If Realtime drops → falls back to polling every 30s
