#!/usr/bin/env bash
# self_update.sh — Pull latest agent-ops-framework from GitHub
# Run via cron: 0 * * * * /path/to/self_update.sh
# No R2, no tarball — GitHub only.

set -e

AGENT_NAME="${AGENT_NAME:-zeanna}"
SKILL_DIR="${SKILL_DIR:-/root/.openclaw/workspace/skills/agent-ops-framework}"
GITHUB_REPO="https://github.com/GanzApps/ganz-agent-skills"
LOG_FILE="/tmp/agent-update.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

log "Self-update starting for $AGENT_NAME"

# git required
if ! command -v git &> /dev/null; then
    log "git not found, skipping"
    exit 0
fi

mkdir -p "$SKILL_DIR"
cd "$SKILL_DIR"

# Fresh clone if not a git repo (first run)
if [ ! -d ".git" ]; then
    log "Fresh clone of $GITHUB_REPO"
    git clone "$GITHUB_REPO" .
fi

# Fetch + reset (discard local changes — this is a clean deployment dir)
log "Fetching latest..."
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Already up to date at $(git rev-parse --short HEAD)"
    exit 0
fi

log "Updating: $(git rev-parse --short HEAD) → $(git rev-parse --short origin/main)"
git reset --hard origin/main

# Update AGENT_NAME in worker via env substitution (don't hardcode sed)
# Worker reads from env, so nothing to patch in the file itself.
# Only restart worker if it's running.
WORKER_PID=$(pgrep -f "worker_template.py" 2>/dev/null || true)
if [ -n "$WORKER_PID" ]; then
    log "Restarting worker (PID: $WORKER_PID)..."
    pkill -f "worker_template.py"
    sleep 2
    nohup python3 scripts/worker_template.py >> "$LOG_FILE" 2>&1 &
    log "Worker restarted"
fi

log "Update complete — now on $(git rev-parse --short HEAD)"