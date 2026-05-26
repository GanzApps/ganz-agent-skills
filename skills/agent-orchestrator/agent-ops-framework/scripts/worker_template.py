#!/usr/bin/env python3
"""
Agent Worker Template
Multi-agent task consumer for Supabase shared queue.
Copy this file and configure for your agent.
"""

import os
import time
import json
from datetime import datetime
from supabase import create_client, Client

# ─── CONFIG ───
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lyhhfqbkwamodswxewql.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
AGENT_NAME = os.getenv("AGENT_NAME", "mr-kim")  # Change this per agent

# What this agent can do
AGENT_CAPABILITIES = [
    "research",
    "code",
    # "image",      # Uncomment if agent can do images
    # "video",      # Uncomment if agent can do video
    # "file",       # Uncomment if agent can do file ops
]

# Polling interval (seconds)
POLL_INTERVAL = 30

# ─── SETUP ───
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
def update_heartbeat(status="idle", current_task_id=None):
    """Update agent heartbeat in Supabase."""
    try:
        supabase.table("agent_heartbeats").upsert({
            "agent_name": AGENT_NAME,
            "status": status,
            "current_task_id": current_task_id,
            "last_seen": datetime.utcnow().isoformat(),
            "capabilities": AGENT_CAPABILITIES
        }).execute()
    except Exception as e:
        log(f"Heartbeat failed: {e}")





def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{AGENT_NAME}] {msg}")


def get_pending_tasks():
    """Fetch claimable tasks this agent can handle.
    
    Fetches all pending tasks where this agent is named OR assigned.
    Capability check happens in process_task() before claim/reject.
    """
    try:
        response = supabase.table("agent_tasks") \
            .select("*") \
            .eq("status", "pending") \
            .lt("retry_count", "max_retries") \
            .or_(f"agent_name.eq.{AGENT_NAME},assigned_to.eq.{AGENT_NAME}") \
            .gt("created_at", (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()) \
            .order("priority", desc=True) \
            .order("created_at", desc=False) \
            .limit(5) \
        .execute()
        return response.data or []
    except Exception as e:
        log(f"Failed to fetch tasks: {e}")
        return []


def claim_task(task_id: str) -> bool:
    """Atomically claim a task. Returns True if successful.
    
    Safety: only claim if pending + not maxed retries + not already claimed
    """
    try:
        # Double-check task is still claimable before claiming
        check = supabase.table("agent_tasks") \
            .select("status, retry_count, max_retries") \
            .eq("id", task_id) \
            .single() \
            .execute()
        
        if not check.data:
            log(f"Task {task_id} not found")
            return False
            
        task = check.data
        if task["status"] != "pending":
            log(f"Task {task_id} not pending (status: {task['status']})")
            return False
            
        if task["retry_count"] >= task["max_retries"]:
            log(f"Task {task_id} max retries exceeded")
            return False
        
        # Atomic claim
        response = supabase.table("agent_tasks") \
            .update({
                "status": "claimed",
                "assigned_to": AGENT_NAME,
                "claimed_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", task_id) \
            .eq("status", "pending") \
            .execute()
        return len(response.data) > 0
    except Exception as e:
        log(f"Failed to claim task: {e}")
        return False


def update_task_status(task_id: str, status: str, result: str = None, result_data: dict = None):
    """Update task status and optionally result."""
    update = {"status": status, "updated_at": datetime.utcnow().isoformat()}
    if result:
        update["result"] = result
    if result_data:
        update["result_data"] = result_data
    if status in ("done", "error"):
        update["completed_at"] = datetime.utcnow().isoformat()
    
    supabase.table("agent_tasks").update(update).eq("id", task_id).execute()


def execute_task(task: dict) -> dict:
    """
    Execute the task. Override this for your agent's capabilities.
    Returns: {"status": "done|error", "result": str, "result_data": dict}
    """
    task_type = task.get("task_type", "general")
    instruction = task.get("instruction", "")
    payload = task.get("payload", {})
    
    log(f"Executing: {instruction}")
    
    # ─── TASK ROUTING ───
    if task_type not in AGENT_CAPABILITIES:
        return {
            "status": "rejected",
            "result": f"Task type '{task_type}' not in agent capabilities {AGENT_CAPABILITIES}",
            "result_data": {}
        }
    if task_type == "research":
        return execute_research(instruction, payload)
    elif task_type == "code":
        return execute_code(instruction, payload)
    else:
        return {
            "status": "error",
            "result": f"Unknown task type: {task_type}",
            "result_data": {}
        }


def execute_research(instruction: str, payload: dict) -> dict:
    """Example research task handler."""
    # TODO: Implement actual research logic
    # For now, return a placeholder
    return {
        "status": "done",
        "result": f"Research completed for: {instruction}",
        "result_data": {
            "topic": payload.get("topic", ""),
            "findings": ["Finding 1", "Finding 2"],
            "sources": []
        }
    }


def execute_code(instruction: str, payload: dict) -> dict:
    """Example code task handler."""
    # TODO: Implement actual code generation
    return {
        "status": "done",
        "result": f"Code generated for: {instruction}",
        "result_data": {
            "language": payload.get("language", "python"),
            "code": "# TODO: Generated code here"
        }
    }


def post_discord_status(task_id: str, status: str, message: str):
    """Post status update to Discord."""
    # TODO: Implement Discord webhook/bot posting
    # For now, just log
    log(f"Discord [{status}]: {message}")


def reject_task(task_id: str, reason: str):
    """Reject a task — capability or assignment mismatch.
    Sets status=rejected so orchestrator knows this was inspected.
    """
    try:
        supabase.table("agent_tasks").update({
            "status": "rejected",
            "error_message": reason,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()
        log(f"Rejected task: {reason}")
    except Exception as e:
        log(f"Failed to reject task: {e}")
    """Requeue a failed task for retry."""
    try:
        supabase.table("agent_tasks").update({
            "status": "pending",
            "retry_count": new_retry_count,
            "error_message": error_msg,
            "assigned_to": None,
            "claimed_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).execute()
        log(f"Requeued task for retry {new_retry_count}")
    except Exception as e:
        log(f"Failed to requeue task: {e}")


def process_task(task: dict):
    """Process a single task end-to-end with retry logic."""
    task_id = task["id"]
    task_name = task.get("task_id", "unknown")
    task_type = task.get("task_type", "general")
    max_retries = task.get("max_retries", 3)
    retry_count = task.get("retry_count", 0)
    assigned_to = task.get("assigned_to") or task.get("agent_name")
    
    # Check if already failed too many times
    if retry_count >= max_retries:
        log(f"Task {task_name} exceeded max retries ({max_retries}), skipping")
        post_discord_status(task_name, "error", f"❌ {AGENT_NAME} skipping #{task_name}: max retries exceeded")
        return
    
    # If pre-assigned to this agent, verify capability match first
    if assigned_to == AGENT_NAME and task_type not in AGENT_CAPABILITIES:
        log(f"Task {task_name} assigned to me but type '{task_type}' not in my capabilities {AGENT_CAPABILITIES} — rejecting")
        reject_task(task_id, f"capability mismatch: task_type='{task_type}' not in agent capabilities {AGENT_CAPABILITIES}")
        post_discord_status(task_name, "rejected", f"🚫 {AGENT_NAME} rejected #{task_name}: type '{task_type}' not supported")
        return
    
    # If task is unassigned, also check capability match before claiming
    if not assigned_to and task_type not in AGENT_CAPABILITIES:
        log(f"Task {task_name} has type '{task_type}' not in my capabilities {AGENT_CAPABILITIES} — rejecting")
        reject_task(task_id, f"capability mismatch: unassigned task_type='{task_type}' not in agent capabilities {AGENT_CAPABILITIES}")
        post_discord_status(task_name, "rejected", f"🚫 {AGENT_NAME} rejected #{task_name}: type '{task_type}' not supported")
        return
    
    # 1. Claim
    if not claim_task(task_id):
        log(f"Failed to claim task {task_name} (race condition)")
        return
    
    log(f"Claimed task: {task_name}")
    update_heartbeat("busy", task_id)
    post_discord_status(task_name, "claimed", f"🔧 {AGENT_NAME} claimed task #{task_name}")
    
    # 2. Mark running
    update_task_status(task_id, "running")
    post_discord_status(task_name, "running", f"⏳ {AGENT_NAME} working on #{task_name}")
    
    try:
        # 3. Execute
        result = execute_task(task)
        
        # 4. Store result
        update_task_status(
            task_id,
            result["status"],
            result.get("result"),
            result.get("result_data")
        )
        
        if result["status"] == "done":
            log(f"Completed task: {task_name}")
            update_heartbeat("idle", None)
            post_discord_status(task_name, "done", f"✅ {AGENT_NAME} completed #{task_name}")
        else:
            # Task failed but retryable
            log(f"Task failed: {task_name}, retry {retry_count + 1}/{max_retries}")
            post_discord_status(task_name, "error", f"❌ {AGENT_NAME} failed #{task_name}: {result.get('result')} (retry {retry_count + 1}/{max_retries})")
            
            # Increment retry and requeue if not maxed
            if retry_count + 1 < max_retries:
                requeue_task(task_id, retry_count + 1, result.get('result'))
            
    except Exception as e:
        log(f"Exception processing task {task_name}: {e}")
        post_discord_status(task_name, "error", f"❌ {AGENT_NAME} crashed on #{task_name}: {e} (retry {retry_count + 1}/{max_retries})")
        
        # Increment retry and requeue if not maxed
        if retry_count + 1 < max_retries:
            requeue_task(task_id, retry_count + 1, str(e))
        else:
            update_task_status(task_id, "error", error_message=str(e))


def main():
    log(f"Agent worker started. Capabilities: {AGENT_CAPABILITIES}")
    log(f"Polling every {POLL_INTERVAL}s...")
    
    while True:
        try:
            tasks = get_pending_tasks()
            
            if tasks:
                log(f"Found {len(tasks)} pending tasks")
                for task in tasks:
                    process_task(task)
            else:
                # No tasks, sleep
                time.sleep(POLL_INTERVAL)
                
        # Update heartbeat every iteration
        update_heartbeat("idle", None)
        
        except Exception as e:
            log(f"Error in main loop: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
