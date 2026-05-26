---
name: auto-blog-channel
description: "Automated blog channel setup and management for Discord. Creates listening channels, configures auto-response, and prepares workspace for blog content capture. Use when: (1) Setting up a new blog monitoring channel in Discord, (2) Configuring auto-listener for blog content capture, (3) Managing blog post workflow from Discord to external platforms, (4) Creating content production pipelines with Discord as input source."
---

# Auto-Blog Channel Skill

## Purpose
Set up Discord channels that listen for blog content, capture ideas, and prepare auto-post workflows.

## Workflow

### 1. Create Channel
```
message action=channel-create
  guildId: <server_id>
  name: <channel_name>
  topic: <description>
```

### 2. Configure Discord Plugin
Edit `/root/.openclaw/openclaw.json` (active config, NOT `/root/openclaw/`):

```json
"discord": {
  "token": "<bot_token>",
  "enabled": true,
  "groupPolicy": "open",
  "guilds": {
    "<guild_id>": {
      "requireMention": false,
      "channels": {
        "<existing_channels>": {},
        "<new_channel_id>": {
          "requireMention": false
        }
      }
    }
  }
}
```

**Critical:** Always edit `/root/.openclaw/openclaw.json` — this is the active config. `/root/openclaw/openclaw.json` is a backup/secondary copy.

### 3. Restart Gateway
```
gateway action=restart
  reason: "Added new channel to Discord config"
```

### 4. Verify Setup
- Post test message in new channel
- Confirm auto-response works
- Check channel appears in gateway config

## Troubleshooting

### Channel Not Responding
1. Check which config is active: `ls -la /root/.openclaw/openclaw.json /root/openclaw/openclaw.json`
2. Verify channel ID is in the ACTIVE config
3. Confirm Discord token is valid: `curl -H "Authorization: Bot <token>" https://discord.com/api/v10/users/@me`
4. Restart gateway after config changes

### Token Issues
- Composio Discord connection may have different token than openclaw.json
- Test token directly with Discord API before assuming it's stale
- Bot token format: `MTQ5...` (starts with base64-encoded bot ID)

## Blog Content Capture

When listener is active:
- Capture messages as blog post ideas
- Draft content from channel discussions
- Queue for approval before auto-posting
- Tag hot topics for priority processing

## Publishing Pipeline
For actual article writing → cover image → database publishing workflow, use the **`ganzblog-article-publisher`** skill.

This skill only handles channel setup and listening. The publishing pipeline is a separate workflow.

## File Locations
- Active config: `/root/.openclaw/openclaw.json`
- Secondary config: `/root/openclaw/openclaw.json` (do not edit unless directed)
- Skill directory: `~/.openclaw/workspace/skills/auto-blog-channel/`

## Supabase Project Tracking (IMPORTANT)
This skill uses **GanzBlog Supabase** (`lmtnkbyrhqdyozkngaku`) for blog data.

**DO NOT confuse with Mission Control Supabase** (`lyhhfqbkwamodswxewql`).

When writing code/scripts that connect to Supabase, always verify which project:
- **GanzBlog**: articles, blog content, covers storage (`covers` bucket)
- **Mission Control**: agent_tasks, SDLC pipeline tickets, Mr. Kim bridge

Store credentials in `TOOLS.md` — never hardcode project refs in scripts.
