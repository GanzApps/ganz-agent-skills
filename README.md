# ganz-agent-skills

Zeanna's skill bank and agent tools library.

## Structure

```
skills/           # Skill definitions (what to do)
  agent-orchestrator/
  content-pipeline/
  research-intelligence/
  developer-tools/
  social-channels/

tools/            # Scripts and configs (how to do) — coming soon
  scripts/
  cron/
  configs/
```

## Skills Index

See [SKILLS.md](SKILLS.md) for full skill inventory.

## Quick Start

Pull skills you need into your OpenClaw workspace:
```bash
git clone https://github.com/oeganz/ganz-agent-skills.git
cp -r skills/* ~/.openclaw/skills/
```

## For Agents

- Skills go in `~/.openclaw/skills/`
- Tools go in `~/.openclaw/workspace/tools/`
- Configs in `~/.openclaw/workspace/.env`
