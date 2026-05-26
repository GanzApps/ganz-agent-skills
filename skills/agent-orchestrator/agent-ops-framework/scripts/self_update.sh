#!/usr/bin/env bash
# self_update.sh — Pull latest agent-ops-framework from GitHub
# Run via cron: 0 * * * * /path/to/self_update.sh

set -e

AGENT_NAME="${AGENT_NAME:-zeanna}"
SKILL_DIR="${SKILL_DIR:-/root/.openclaw/workspace/skills/agent-ops-framework}"
GITHUB_REPO="https://github.com/GanzApps/ganz-agent-skills"
GITHUB_BRANCH="refs/heads/main"
LOG_FILE="/tmp/agent-update.log"

echo "[$(date)] Agent self-update starting for $AGENT_NAME" >> "$LOG_FILE"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "[$(date)] git not found, skipping" >> "$LOG_FILE"
    exit 0
fi

# Navigate to skill dir
mkdir -p "$SKILL_DIR"
cd "$SKILL_DIR"

# If not a git repo, clone fresh
if [ ! -d ".git" ]; then
    echo "[$(date)] Fresh clone of $GITHUB_REPO" >> "$LOG_FILE"
    git clone "$GITHUB_REPO" .
fi

# Fetch latest
echo "[$(date)] Fetching latest from $GITHUB_REPO" >> "$LOG_FILE"
git fetch origin

# Check if we're behind
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" = "$REMOTE" ]; then
    echo "[$(date)] Already up to date" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date)] Updating from $LOCAL → $REMOTE" >> "$LOG_FILE"
git checkout origin/main

# Update agent name in worker if needed
if [ "$AGENT_NAME" != "zeanna" ]; then
    sed -i "s/AGENT_NAME = .*/AGENT_NAME = \"$AGENT_NAME\"/" scripts/worker_template.py 2>/dev/null || true
    sed -i "s/AGENT_NAME=.*/AGENT_NAME=$AGENT_NAME/" .env 2>/dev/null || true
fi

# Restart worker if running
WORKER_PID=$(pgrep -f "worker_template.py" || true)
if [ -n "$WORKER_PID" ]; then
    echo "[$(date)] Restarting worker (PID: $WORKER_PID)..." >> "$LOG_FILE"
    pkill -f "worker_template.py"
    sleep 2
    cd "$SKILL_DIR"
    nohup python3 scripts/worker_template.py >> "$LOG_FILE" 2>&1 &
    echo "[$(date)] Worker restarted" >> "$LOG_FILE"
fi

echo "[$(date)] Update complete — now on $(git rev-parse --short HEAD)" >> "$LOG_FILE"