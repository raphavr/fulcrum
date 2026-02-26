#!/usr/bin/env python3
"""
Metrics Session Start Hook

Initializes session tracking:
- Generates a unique session ID
- Detects project name from git remote
- Reads plugin version from plugin.json
- Writes session state to .claude/workflow-session.json
- Initializes empty workflow state file for stage transitions
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Python inserts the script's directory into sys.path[0] automatically when
# run by absolute path, so this sibling import works without any path surgery.
from kafka_producer import send_event

session_id = str(uuid.uuid4())
start_time = datetime.now(timezone.utc).isoformat()

# Detect project name from git remote
project = "unknown"
try:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    )
    remote_url = result.stdout.strip()
    # Extract repo name from URL patterns:
    # git@bitbucket.org:company/checkout-service.git → checkout-service
    # https://bitbucket.org/company/checkout-service.git → checkout-service
    match = re.search(r"/([^/]+?)(?:\.git)?$", remote_url)
    if match:
        project = match.group(1)
except Exception:
    # Not a git repo or no remote configured
    pass

# Get plugin version from plugin.json
plugin_version = "unknown"
try:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).parent.parent)
    plugin_meta = json.loads(
        (Path(plugin_root) / ".claude-plugin" / "plugin.json").read_text()
    )
    plugin_version = plugin_meta.get("version", "unknown")
except Exception:
    # plugin.json not found or malformed
    pass

# Initialize state directory and files
state_dir = Path(".claude")
state_dir.mkdir(parents=True, exist_ok=True)

(state_dir / "workflow-session.json").write_text(
    json.dumps(
        {
            "session_id": session_id,
            "start_time": start_time,
            "project": project,
            "plugin_version": plugin_version,
        },
        indent=2,
    )
)

# Initialize state file for stage transitions (preserve across sessions in same feature cycle)
state_file = state_dir / "workflow-state.jsonl"
if not state_file.exists():
    state_file.write_text("")

try:
    send_event(
        event_type="workflow.session.started",
        session_id=session_id,
        project=project,
        plugin_version=plugin_version,
        metadata={},
    )
    print(
        f"[metrics] Session {session_id} started for project {project} "
        f"(plugin v{plugin_version})"
    )
except Exception as err:
    print(f"[metrics] Unexpected error: {err}", file=sys.stderr)
