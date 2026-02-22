#!/usr/bin/env python3
# utilities/deploy_voice.py

"""Copy a voice package directory to the TALK-CLOCK SD card.

Usage:
    python deploy_voice.py <source_path>

Example:
    python deploy_voice.py ./talking-clock-audio/audio/en_US_lessac_medium_standard/
"""

import sys
import shutil
import platform
from pathlib import Path


def find_sd_card() -> Path:
    """Locate the TALK-CLOCK SD card mount point.

    Returns:
        Path to the SD card root.

    Raises:
        FileNotFoundError: If TALK-CLOCK is not found.
    """
    system = platform.system()

    if system == "Darwin":
        candidate = Path("/Volumes/TALK-CLOCK")
    elif system == "Windows":
        import string
        drives = [Path(f"{d}:/") for d in string.ascii_uppercase if Path(f"{d}:/").exists()]
        candidate = next((d for d in drives if (d / "TALK-CLOCK.txt").exists() or d.name == "TALK-CLOCK"), None)
        if candidate is None:
            raise FileNotFoundError("TALK-CLOCK SD card not found. Check it is inserted and mounted.")
        return candidate
    else:
        candidate = Path("/media") / (Path.home().name) / "TALK-CLOCK"
        if not candidate.exists():
            candidate = Path("/mnt/TALK-CLOCK")

    if not candidate.exists():
        raise FileNotFoundError(f"TALK-CLOCK SD card not found at {candidate}. Check it is inserted and mounted.")

    return candidate


def deploy_voice(source: Path, sd_root: Path) -> None:
    """Copy a voice directory to the SD card, replacing any existing copy.

    Args:
        source: Path to the voice package directory.
        sd_root: Path to the SD card root.
    """
    dest = sd_root / source.name

    if dest.exists():
        print(f"Removing existing: {dest}")
        shutil.rmtree(str(dest))

    print(f"Copying {source} -> {dest}")
    shutil.copytree(source, dest)
    print("Done.")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    source = Path(sys.argv[1]).resolve()

    if not source.exists():
        print(f"Error: source path does not exist: {source}")
        return 1

    if not source.is_dir():
        print(f"Error: source must be a directory: {source}")
        return 1

    try:
        sd_root = find_sd_card()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    print(f"SD card found at: {sd_root}")
    deploy_voice(source, sd_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())