---
name: discord-channel-listener
description: "Create Discord channels and connect them to Zeanna's auto-listener. Use when: (1) Creating new Discord channels that need bot auto-response, (2) Adding channels to OpenClaw Discord plugin config, (3) Setting up channel-specific listeners for any purpose (blog, news, monitoring, etc.), (4) Troubleshooting why a channel isn't responding to messages."
---

# Discord Channel Listener Setup

## Purpose
Create Discord channels and wire them into Zeanna's listener so I auto-respond to messages there.

## Prerequisites
- Discord bot token (valid, not 401)
- Guild ID where channel lives
- OpenClaw gateway running

## Step 1: Create Channel

```
message action=channel-create
  channel: discord
  guildId: <guild_id>
  name: <channel_name>
  topic: <description>
```

Save the returned `channel.id` — needed for Step 2.

## Step 2: Add to Discord Config

**CRITICAL:** Edit the ACTIVE config file:
- **Active:** `/root/.openclaw/openclaw.json` ← always edit this one
- **Secondary:** `/root/openclaw/openclaw.json` ← ignore unless directed

Find the Discord section:

```json
"discord": {
  "token": "<bot_token>",
  "enabled": true,
  "groupPolicy": "open",
  "guilds": {
    "<guild_id>": {
      "requireMention": false,
      "channels": {
        "<existing_channel_1>": {},
        "<existing_channel_2>": {},
        "<NEW_CHANNEL_ID>": {
          "requireMention": false
        }
      }
    }
  }
}
```

Add the new channel ID with `"requireMention": false` so I respond without needing @Zeanna.

## Step 3: Restart Gateway

```
gateway action=restart
  reason: "Added channel <id> to Discord config"
```

Wait for restart confirmation (usually 5-10 seconds).

## Step 4: Verify

1. Post test message in new channel
2. Confirm I auto-respond
3. If no response → see Troubleshooting

## Troubleshooting

### Channel Not Responding

1. **Check active config location:**
   ```bash
   ls -la /root/.openclaw/openclaw.json /root/openclaw/openclaw.json
   ```
   The one with the **newer timestamp** is active.

2. **Verify channel ID is in active config:**
   ```bash
   grep -A 20 '"discord":' /root/.openclaw/openclaw.json | grep <channel_id>
   ```

3. **Test Discord token:**
   ```bash
   curl -s -H "Authorization: Bot <token>" https://discord.com/api/v10/users/@me
   ```
   Should return bot user info, not 401.

4. **Check channel exists via API:**
   ```bash
   curl -s -H "Authorization: Bot <token>" https://discord.com/api/v10/channels/<channel_id>
   ```

5. **Restart gateway** — config changes only take effect after restart.

### Common Mistakes

- **Editing wrong config file** — `/root/openclaw/` vs `/root/.openclaw/`
- **Forgetting to restart gateway** after adding channel
- **Wrong channel ID** — double-check the ID from channel-create response
- **Token mismatch** — Composio Discord connection may use different token than openclaw.json

## One-Liner Check

After setup, verify everything:
```bash
grep "<channel_id>" /root/.openclaw/openclaw.json && echo "✅ Config OK" || echo "❌ Missing from config"
```

## File Locations

| File | Purpose |
|------|---------|
| `/root/.openclaw/openclaw.json` | **Active config** — edit this |
| `/root/openclaw/openclaw.json` | Backup/secondary — ignore |
| `~/.openclaw/workspace/skills/discord-channel-listener/SKILL.md` | This skill |
