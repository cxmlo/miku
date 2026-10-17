import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_island_compatibility_copy_matches_tauri_frontend():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_island.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "in sync" in result.stdout
