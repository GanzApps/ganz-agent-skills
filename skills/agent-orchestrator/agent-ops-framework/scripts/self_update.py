import os
#!/usr/bin/env python3
"""
Agent Skill Self-Update Script
Updates agent to latest skill framework and reports skill_version.
Run via cron or task: AGENT_NAME=mr-kim python3 agent-self-update.py
"""

import os
import sys
import json
import time
import signal
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Config
SUPABASE_URL = "https://lyhhfqbkwamodswxewql.supabase.co"
SUPABASE_KEY = os.environ.get("MISSION_CONTROL_SUPABASE_ANON_KEY", "")
SKILL_VERSION = "v6"  # Current skill framework version
GITHUB_URL = "https://github.com/GanzApps/ganz-agent-skills.git"
GITHUB_BRANCH = "master"

MY_NAME = os.environ.get("AGENT_NAME", "zeanna")
SKILL_DIR = os.environ.get("SKILL_DIR", "/root/.openclaw/workspace/skills/agent-ops-framework")


def supabase_rest(query, method="GET", data=None):
    url = f"{SUPABASE_URL}/rest/v1/{query}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}


def report_skill_version():
    """Update heartbeat with current skill_version."""
    result = supabase_rest(
        f"agent_heartbeats?agent_name=eq.{MY_NAME}",
        "PATCH",
        {"skill_version": SKILL_VERSION, "last_seen": "now()"}
    )
    if "error" not in result:
        print(f"[UPDATE] Reported skill_version={SKILL_VERSION}")
    return "error" not in result


def main():
    print(f"[UPDATE] Starting skill self-update for {MY_NAME}")
    print(f"[UPDATE] Target skill version: {SKILL_VERSION}")
    
    # Check current version
    current = supabase_rest(f"agent_heartbeats?agent_name=eq.{MY_NAME}&select=skill_version")
    current_version = current[0].get("skill_version", "v1") if current and not "error" in current else "unknown"
    print(f"[UPDATE] Current skill_version: {current_version}")
    
    if current_version == SKILL_VERSION:
        print(f"[UPDATE] Already on {SKILL_VERSION}, skipping download")
        return
    
    # Clone latest from GitHub
    print(f"[UPDATE] Cloning {GITHUB_URL} branch {GITHUB_BRANCH}")
    import tempfile, subprocess
    tmpdir = tempfile.mkdtemp()
    result = subprocess.run(
        ["git", "clone", "--branch", GITHUB_BRANCH, "--depth", "1", "--filter=blob:none", GITHUB_URL, tmpdir],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"[UPDATE] Clone failed: {result.stderr}")
        return

    # Copy framework files
    framework_dir = os.path.join(tmpdir, "skills", "agent-ops-framework")
    if not os.path.exists(framework_dir):
        framework_dir = tmpdir  # fall back if repo root
    for fname in ["SKILL.md", "agent_worker_template.py"]:
        src = os.path.join(framework_dir, fname)
        dst = os.path.join(SKILL_DIR, fname)
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            print(f"[UPDATE] Copied {fname}")
    
    # Update agent name in worker
    worker_path = os.path.join(SKILL_DIR, "agent_worker_template.py")
    if os.path.exists(worker_path):
        with open(worker_path, "r") as f:
            content = f.read()
        if f'MY_NAME = "zeanna"' in content and MY_NAME != "zeanna":
            content = content.replace(f'MY_NAME = "zeanna"', f'MY_NAME = "{MY_NAME}"')
            with open(worker_path, "w") as f:
                f.write(content)
            print(f"[UPDATE] Updated MY_NAME to {MY_NAME}")
    
    # Report new version
    report_skill_version()
    
    # Cleanup
    import shutil as sh
    sh.rmtree(tmpdir, ignore_errors=True)
    
    print(f"[UPDATE] Complete! Now on skill_version={SKILL_VERSION}")


if __name__ == "__main__":
    main()