#!/usr/bin/env python3
"""
Metrics Session End Hook

Reads artifacts (state file, git history, specs) and emits
a workflow.session.completed event with session metrics.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from kafka_producer import send_event


def main() -> None:
    # Read session info
    try:
        session = json.loads(Path(".claude/workflow-session.json").read_text())
    except Exception:
        # No session file — nothing to report
        return

    end_time = datetime.now(timezone.utc).isoformat()
    start_dt = datetime.fromisoformat(session["start_time"])
    end_dt = datetime.fromisoformat(end_time)
    duration_seconds = round((end_dt - start_dt).total_seconds())

    # Read state file for stage transitions
    stages: list[dict] = []
    try:
        text = Path(".claude/workflow-state.jsonl").read_text()
        stages = [json.loads(line) for line in text.splitlines() if line.strip()]
    except Exception:
        # No state entries
        pass

    # Deduplicate while preserving insertion order (mirrors JS [...new Set(...)])
    def _unique_ordered(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    stages_entered = _unique_ordered(
        [s["stage"] for s in stages if s.get("action") == "entered"]
    )
    stages_completed = _unique_ordered(
        [s["stage"] for s in stages if s.get("action") == "completed"]
    )

    # Detect entry point from first stage entered
    entry_point = stages_entered[0] if stages_entered else "unknown"

    # Check for spec file
    spec_created = False
    spec_requirements_count = 0
    try:
        specs_dir = Path("docs/specs")
        if specs_dir.exists():
            # Sort for consistent ordering (iterdir() order is not guaranteed)
            spec_files = sorted(f for f in specs_dir.iterdir() if f.suffix == ".md")
            spec_created = len(spec_files) > 0
            if spec_created:
                latest_spec = spec_files[-1]
                content = latest_spec.read_text()
                spec_requirements_count = sum(
                    1 for line in content.splitlines() if line.startswith("- [ ]")
                )
    except Exception:
        # No specs dir
        pass

    # Check git activity since session start
    commits_count = 0
    files_changed_count = 0
    try:
        log = subprocess.run(
            ["git", "log", f'--since={session["start_time"]}', "--oneline"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits_count = len([l for l in log.stdout.splitlines() if l])
        if commits_count > 0:
            diff = subprocess.run(
                ["git", "diff", "--stat", f"HEAD~{commits_count}", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            files_changed_count = sum(
                1 for l in diff.stdout.splitlines() if "|" in l
            )
    except Exception:
        # Git errors (not a repo, no commits, etc.)
        pass

    # Determine outcome
    if "finish" in stages_completed:
        outcome = "branch_finished"
    elif stages_entered:
        outcome = "in_progress"
    else:
        outcome = "abandoned"

    send_event(
        event_type="workflow.session.completed",
        session_id=session["session_id"],
        project=session["project"],
        plugin_version=session.get("plugin_version", "unknown"),
        metadata={
            "total_duration_seconds": duration_seconds,
            "entry_point": entry_point,
            "stages_entered": stages_entered,
            "stages_completed": stages_completed,
            "spec_created": spec_created,
            "spec_requirements_count": spec_requirements_count,
            "commits_count": commits_count,
            "files_changed_count": files_changed_count,
            "outcome": outcome,
        },
    )

    print(
        f"[metrics] Session {session['session_id']} completed "
        f"({outcome}, {duration_seconds}s)"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"[metrics] Unexpected error: {err}", file=sys.stderr)
