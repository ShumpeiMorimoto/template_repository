"""PostToolUse hook for Edit|Write: run ruff format on the edited .py file."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        path = (data.get("tool_input") or {}).get("file_path")
        if isinstance(path, str) and path.endswith(".py") and Path(path).is_file():
            subprocess.run(
                ["uv", "run", "ruff", "format", path],
                cwd=os.environ.get("CLAUDE_PROJECT_DIR") or None,
                capture_output=True,
                timeout=25,
                check=False,
            )
    except Exception:
        pass
    sys.exit(0)


main()
