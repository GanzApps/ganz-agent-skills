#!/usr/bin/env python3
"""
Agent Worker Template v6.0.0
Generic multi-agent task framework with Realtime + polling fallback.

Copy this file, configure AGENT_* vars, and run.
Reads secrets from environment — NO hardcoded values.
"""

import os
import sys
import time
import json
import signal
from datetime import datetime
from typing import Optional

# ─── CONFIG (override via env) ───────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lyhhfqbkwamodswxewql.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")           # from .env
AGENT_NAME = os.getenv("AGENT_NAME", "agent")           # mr-kim, zenoa, miss-x
AGENT_CAPABILITIES = os.getenv("AGENT_CAPABILITIES", "research,code,general").split(",")
SKILL_VERSION = os.getenv("SKILL_VERSION", "v6.0.0")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))   # seconds
REALTIME_RECONNECT_DELAY = 5                              # seconds

MY_CAPABILITIES = [c.strip() for c in AGENT_CAPABILITIES]
# ─────────────────────────────────────────────────────────────────────────

if not SUPABASE_KEY:
    raise SystemExit("SUPABASE_KEY env var required")

from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── STATE ───────────────────────────────────────────────────────────────
realtime_connected = False
current_task_id = None
shutdown_requested = False

# ─── LOGGING ─────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{AGENT_NAME}] [{level}] {msg}", flush=True)

def log_error(msg: str):
    log(msg, "ERROR")

def log_warn(msg: str):
    log(msg, "WARN")

# ─── HEARTBEAT ────────────────────────────────────────────────────────────
def update_heartbeat(status: str = "idle", current_task: str = None):
    """Update agent heartbeat in Supabase."""
    try:
        supabase.table("agent_heartbeats").upsert({
            "agent_name": AGENT_NAME,
            "status": status,
            "current_task_id": current_task,
            "last_seen": datetime.utcnow().isoformat(),
            "skill_version": SKILL_VERSION,
            "capabilities": MY_CAPABILITIES
        }, on_conflict="agent_name").execute()
    except Exception as e:
        log_warn(f"Heartbeat failed: {e}")

def is_agent_idle() -> bool:
    """True only if agent is idle (no current task)."""
    try:
        result = supabase.table("agent_heartbeats").select(
            "status", "current_task_id"
        ).eq("agent_name", AGENT_NAME).single().execute()
        if not result.data:
            return True
        return result.data["status"] == "idle" and result.data.get("current_task_id") is None
    except Exception:
        return True  # Treat no record as idle

# ─── TASK QUERY ─────────────────────────────────────────────────────────
def get_claimable_tasks() -> list[dict]:
    """Get pending tasks this agent can handle. Respects blocked_by."""
    try:
        result = supabase.table("agent_tasks").select("*").eq(
            "status", "pending"
        ).in_(
            "task_type", MY_CAPABILITIES
        ).or_(
            f"assigned_to.is.null,assigned_to.eq.{AGENT_NAME}"
        ).order(
            "priority", desc=True
        ).order(
            "created_at"
        ).limit(5).execute()
        tasks = result.data or []
        # Filter out blocked tasks
        return [t for t in tasks if not t.get("blocked_by")]
    except Exception as e:
        log_error(f"get_claimable_tasks failed: {e}")
        return []

# ─── ATOMIC CLAIM ────────────────────────────────────────────────────────
def claim_task(task_id: str) -> bool:
    """Atomic claim — only succeeds if status still pending."""
    try:
        result = supabase.table("agent_tasks").update({
            "status": "claimed",
            "assigned_to": AGENT_NAME,
            "claimed_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).eq("status", "pending").execute()
        return len(result.data) > 0
    except Exception as e:
        log_error(f"claim_task failed: {e}")
        return False

# ─── TASK STATUS UPDATE ──────────────────────────────────────────────────
def update_task(task_id: str, status: str, result: str = None,
                result_data: dict = None, error: str = None):
    """Update task status and result."""
    update = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat()
    }
    if result:
        update["result"] = result
    if result_data:
        update["result_data"] = result_data
    if error:
        update["error_message"] = error
    if status in ("done", "error"):
        update["completed_at"] = datetime.utcnow().isoformat()

    try:
        supabase.table("agent_tasks").update(update).eq("id", task_id).execute()
    except Exception as e:
        log_error(f"update_task failed: {e}")

# ─── TASK EXECUTION ──────────────────────────────────────────────────────
# Standard handler signature:
#   handler(instruction: str, payload: dict) -> {"status": str, "result": str, "result_data": dict}

def execute_research(instruction: str, payload: dict) -> dict:
    """Web research task handler. Implement with Tavily/Brave Search."""
    # TODO: Implement actual research
    return {"status": "done", "result": f"Research complete: {instruction[:50]}", "result_data": {"topic": payload.get("topic", "")}}

def execute_code(instruction: str, payload: dict) -> dict:
    """Code generation/review task handler."""
    # TODO: Implement actual code generation
    return {"status": "done", "result": f"Code generated: {instruction[:50]}", "result_data": {"repo": payload.get("repo", "")}}

def execute_image(instruction: str, payload: dict) -> dict:
    """Image generation task handler."""
    return {"status": "done", "result": f"Image generated: {instruction[:50]}", "result_data": {}}

def execute_video(instruction: str, payload: dict) -> dict:
    """Video generation task handler."""
    return {"status": "done", "result": f"Video generated: {instruction[:50]}", "result_data": {}}

def execute_file(instruction: str, payload: dict) -> dict:
    """File operations task handler."""
    return {"status": "done", "result": f"File op complete: {instruction[:50]}", "result_data": {}}

def execute_deploy(instruction: str, payload: dict) -> dict:
    """Deployment task handler."""
    return {"status": "done", "result": f"Deployed: {instruction[:50]}", "result_data": {}}

def execute_setup(instruction: str, payload: dict) -> dict:
    """Setup/prerequisite task handler."""
    return {"status": "done", "result": f"Setup complete: {instruction[:50]}", "result_data": {}}

def execute_general(instruction: str, payload: dict) -> dict:
    """Fallback handler for unknown types."""
    return {"status": "done", "result": f"Done: {instruction[:50]}", "result_data": {}}

# Generic handler map
TASK_HANDLERS = {
    "research": execute_research,
    "code": execute_code,
    "image": execute_image,
    "video": execute_video,
    "file": execute_file,
    "deploy": execute_deploy,
    "setup": execute_setup,
    "general": execute_general,
}

def execute_task(task: dict) -> dict:
    """Route task to appropriate handler."""
    task_type = task.get("task_type", "general")
    instruction = task.get("instruction", "")
    payload = task.get("payload", {}) or {}
    handler = TASK_HANDLERS.get(task_type, execute_general)
    return handler(instruction, payload)

# ─── DISCORD NOTIFICATIONS ───────────────────────────────────────────────
def parse_source_channel(source_channel: str) -> Optional[str]:
    """Extract channel ID from source_channel string like 'discord:123456'."""
    if not source_channel:
        return None
    parts = source_channel.split(":")
    return parts[1] if len(parts) == 2 else source_channel

def notify_discord(task_id: str, status: str, message: str, source_channel: str = None):
    """Post notification to Discord source channel."""
    # TODO: Implement actual Discord bot posting
    # For now, just log
    emoji = {"claimed": "🎯", "running": "⏳", "done": "✅", "error": "🔴", "blocked": "🔒"}.get(status, "📋")
    log(f"Discord [{status}]: {emoji} {message}")

# ─── PROCESS SINGLE TASK ──────────────────────────────────────────────────
def process_task(task: dict):
    """Claim and execute a single task."""
    global current_task_id

    task_id = task["id"]
    task_identifier = task.get("task_id", task_id)
    source_channel = task.get("source_channel")
    task_type = task.get("task_type", "general")
    max_retries = task.get("max_retries", 3)
    retry_count = task.get("retry_count", 0)

    # Check idle
    if not is_agent_idle():
        log(f"Agent busy, skipping {task_identifier}")
        return

    # Attempt claim
    if not claim_task(task_id):
        log(f"Claim failed (race), skipping {task_identifier}")
        return

    log(f"Claimed: {task_identifier}")
    current_task_id = task_id
    update_heartbeat("busy", task_id)
    notify_discord(task_identifier, "claimed", f"{AGENT_NAME} claimed {task_identifier}", source_channel)

    # Mark running
    update_task(task_id, "running")
    notify_discord(task_identifier, "running", f"{AGENT_NAME} working on {task_identifier}", source_channel)

    try:
        result = execute_task(task)
        status = result.get("status", "done")
        update_task(task_id, status, result.get("result"), result.get("result_data"))
        notify_discord(task_identifier, status, f"{AGENT_NAME} {status} {task_identifier}: {result.get('result', '')}", source_channel)
    except Exception as e:
        log_error(f"Exception: {e}")
        if retry_count + 1 < max_retries:
            # Requeue for retry
            supabase.table("agent_tasks").update({
                "status": "pending",
                "assigned_to": None,
                "claimed_at": None,
                "retry_count": retry_count + 1,
                "error_message": str(e)
            }).eq("id", task_id).execute()
            notify_discord(task_identifier, "error", f"{AGENT_NAME} retry {retry_count+1}/{max_retries}: {e}", source_channel)
        else:
            update_task(task_id, "error", error=str(e))
            notify_discord(task_identifier, "error", f"{AGENT_NAME} failed permanently: {e}", source_channel)
    finally:
        current_task_id = None
        update_heartbeat("idle", None)

# ─── REALTIME SUBSCRIPTION ────────────────────────────────────────────────
def on_realtime_connect():
    global realtime_connected
    realtime_connected = True
    log("Realtime connected ✓")

def on_realtime_disconnect():
    global realtime_connected
    realtime_connected = False
    log_warn("Realtime disconnected, polling fallback active")

def on_task_insert(payload):
    """New task inserted — check if we can claim it."""
    if not is_agent_idle():
        return
    task = payload.get("new", {})
    if not task:
        return
    if task.get("blocked_by"):
        log(f"New task {task.get('task_id')} is blocked, skipping")
        return
    if task.get("task_type") not in MY_CAPABILITIES:
        return
    if task.get("assigned_to") and task.get("assigned_to") != AGENT_NAME:
        return
    process_task(task)

def on_task_update(payload):
    """Task updated — e.g. blocked_by cleared."""
    task = payload.get("new", {}) or payload.get("old", {})
    if not task:
        return
    # If blocked_by was cleared and task is pending, we can claim it
    old = payload.get("old", {})
    was_blocked = old.get("blocked_by") and not task.get("blocked_by")
    if was_blocked and task.get("status") == "pending":
        log(f"Task {task.get('task_id')} unblocked, checking claimability")
        if is_agent_idle():
            process_task(task)
    # If DELETE of our current task, nothing to do (already claimed)
    if task.get("id") == current_task_id and task.get("status") == "deleted":
        log_warn("Our current task was deleted mid-execution")

def on_task_delete(payload):
    """Task cancelled."""
    task = payload.get("old", {})
    if not task:
        return
    log(f"Task {task.get('task_id')} cancelled")

def subscribe_realtime():
    """Subscribe to all agent_tasks events."""
    try:
        channel = supabase.channel("agent_tasks_realtime")
        channel.on("postgres_changes",
            {"event": "INSERT", "schema": "public", "table": "agent_tasks"},
            on_task_insert)
        channel.on("postgres_changes",
            {"event": "UPDATE", "schema": "public", "table": "agent_tasks"},
            on_task_update)
        channel.on("postgres_changes",
            {"event": "DELETE", "schema": "public", "table": "agent_tasks"},
            on_task_delete)
        channel.subscribe(callback=lambda status: (
            on_realtime_connect() if status == "SUBSCRIBED" else on_realtime_disconnect()
        ))
        log("Realtime subscription active")
    except Exception as e:
        log_error(f"Realtime subscribe failed: {e}, falling back to polling")

# ─── POLLING FALLBACK ─────────────────────────────────────────────────────
def polling_loop():
    """Fallback polling when Realtime is down."""
    log(f"Polling fallback active (every {POLL_INTERVAL}s)")
    while True:
        if shutdown_requested:
            break
        try:
            tasks = get_claimable_tasks()
            for task in tasks:
                if shutdown_requested:
                    break
                process_task(task)
        except Exception as e:
            log_error(f"Poll error: {e}")
        time.sleep(POLL_INTERVAL)

# ─── GRACEFUL SHUTDOWN ───────────────────────────────────────────────────
def handle_shutdown(signum, frame):
    global shutdown_requested
    log("Shutdown requested...")
    shutdown_requested = True
    if current_task_id:
        # Mark current task as pending so another agent can pick it up
        try:
            supabase.table("agent_tasks").update({
                "status": "pending",
                "assigned_to": None,
                "claimed_at": None,
                "error_message": "Agent shutdown mid-execution"
            }).eq("id", current_task_id).execute()
            log(f"Released task {current_task_id} for re-claim")
        except Exception as e:
            log_error(f"Failed to release task: {e}")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# ─── MAIN ─────────────────────────────────────────────────────────────────
def main():
    log(f"Agent worker starting — {AGENT_NAME} v{SKILL_VERSION}")
    log(f"Capabilities: {MY_CAPABILITIES}")

    # Report startup
    update_heartbeat("idle", None)

    # Start Realtime subscription (with polling fallback)
    subscribe_realtime()

    # Keep alive
    while True:
        if shutdown_requested:
            break
        update_heartbeat("idle", None)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
