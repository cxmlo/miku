"""Check or update the compatibility copy served from /island."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "miku_ui" / "src"
MIRROR = ROOT / "miku_island"
MIRRORED_FILES = (
    Path("index.html"),
    Path("miku_settings.html"),
    Path("bridge.js"),
    Path("sound_fx.js"),
    Path("assets") / "app_icon.png",
    Path("assets") / "app_character.jpg",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or sync the legacy /island frontend mirror from miku_ui/src."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="copy the canonical Tauri frontend files into miku_island",
    )
    args = parser.parse_args()

    stale: list[Path] = []
    for relative_path in MIRRORED_FILES:
        source_path = SOURCE / relative_path
        mirror_path = MIRROR / relative_path
        if not source_path.is_file():
            parser.error(f"canonical frontend file is missing: {source_path}")

        if args.sync:
            mirror_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, mirror_path)
        elif not mirror_path.is_file() or source_path.read_bytes() != mirror_path.read_bytes():
            stale.append(relative_path)

    if stale:
        print("Island compatibility copy is out of sync:")
        for relative_path in stale:
            print(f"  {relative_path.as_posix()}")
        print("Run: python scripts/sync_island.py --sync")
        return 1

    print("Island compatibility copy is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
