import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "format-python.py"
UGLY = "x   =   {  'a':1 }\n"


def _run(stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(HOOK)], input=stdin, capture_output=True, check=False
    )


def _payload(path: Path) -> bytes:
    return json.dumps({"tool_input": {"file_path": str(path)}}).encode()


def test_python_file_is_reformatted(tmp_path: Path) -> None:
    f = tmp_path / "m.py"
    f.write_text(UGLY, encoding="utf-8")
    proc = _run(_payload(f))
    assert proc.returncode == 0
    assert proc.stdout == b""
    assert f.read_text(encoding="utf-8") == 'x = {"a": 1}\n'


def test_non_python_file_is_untouched(tmp_path: Path) -> None:
    f = tmp_path / "m.md"
    f.write_text(UGLY, encoding="utf-8")
    assert _run(_payload(f)).returncode == 0
    assert f.read_text(encoding="utf-8") == UGLY


def test_malformed_stdin_exits_zero() -> None:
    proc = _run(b"not json")
    assert proc.returncode == 0
    assert proc.stdout == b""
