# Version

**Current: v6.0.0**
**Date: 2026-05-27**

## Version Format

`v{MAJOR}.{MINOR}.{PATCH}`

- **MAJOR** — Breaking changes to protocol, table schema, or event types
- **MINOR** — New task handlers, new events, new features (backward compatible)
- **PATCH** — Documentation, bug fixes, non-breaking improvements

## Agents Running Each Version

| Agent | skill_version | Worker File |
|-------|--------------|-------------|
| mr-kim | v5.x | mr-kim-worker.js |
| zenoa | v5.x | (needs update) |
| miss-x | v5.x | (needs update) |
| zeanna | v1 | orchestrator only |

> Agents report their `skill_version` via `agent_heartbeats.skill_version` column on startup.

## How to Update

```bash
# On each agent machine:
cd ~/.openclaw/workspace/skills/agent-ops-framework
curl -sL https://github.com/GanzApps/ganz-agent-skills/archive/refs/heads/main.tar.gz | tar -xz
# Or run self_update.sh
./scripts/self_update.sh
```
