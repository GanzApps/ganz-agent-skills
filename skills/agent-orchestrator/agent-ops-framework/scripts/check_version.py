#!/usr/bin/env python3
"""
Version checker — run inside worker loop.
Returns (needs_update: bool, latest_version: str)
Reads SKILL_VERSION from local file + compares against GitHub raw.
"""
import os, sys, requests

REPO_DIR = os.getenv("AGENT_OPS_DIR", "/root/.openclaw/workspace/skills/agent-orchestrator/agent-ops-framework")
GITHUB_REPO = "GanzApps/ganz-agent-skills"
WORKER_FILE = "skills/agent-orchestrator/agent-ops-framework/scripts/worker_template.py"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{WORKER_FILE}"

def get_local_version():
    worker_path = os.path.join(REPO_DIR, "scripts/worker_template.py")
    if not os.path.exists(worker_path):
        return "v0.0.0"
    with open(worker_path) as f:
        for line in f:
            if "SKILL_VERSION" in line and 'getenv' not in line:
                # Extract version from: SKILL_VERSION = "v7.0.0"
                import re
                m = re.search(r'SKILL_VERSION\s*=\s*["\']([^"\']+)["\']', line)
                if m:
                    return m.group(1)
    return "v0.0.0"

def get_remote_version():
    try:
        resp = requests.get(GITHUB_RAW, timeout=10)
        if resp.status_code != 200:
            return None
        for line in resp.text.split("\n"):
            if "SKILL_VERSION" in line and 'getenv' not in line:
                import re
                m = re.search(r'SKILL_VERSION\s*=\s*["\']([^"\']+)["\']', line)
                if m:
                    return m.group(1)
    except:
        pass
    return None

def needs_update():
    local = get_local_version()
    remote = get_remote_version()
    if not remote:
        return False, local
    # Simple version compare — strip 'v', compare tuples
    def parse(v):
        return tuple(int(x) for x in v.strip('v').split('.'))
    return parse(remote) > parse(local), local

if __name__ == "__main__":
    upd, ver = needs_update()
    print(f"current={ver} needs_update={upd}")
    sys.exit(0 if not upd else 1)
