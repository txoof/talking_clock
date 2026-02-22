#!/usr/bin/env python3
# utilities/sync_sd_card.py

"""Sync clock_code/sd_card contents to the TALK-CLOCK SD card.

Repairs WAV files in sd_card/audio_assets to 22050 Hz mono before syncing.
Uses rsync to minimise unnecessary writes.

Usage:
    python sync_sd_card.py
"""

import sys
import shutil
import platform
import subprocess
import wave
from pathlib import Path

REQUIRED_SAMPLE_RATE = 22050
REQUIRED_CHANNELS = 1

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SD_CARD_SRC = REPO_ROOT / "clock_code" / "sd_card"
AUDIO_ASSETS_SRC = SD_CARD_SRC / "audio_assets"


def check_ffmpeg() -> None:
    """Confirm ffmpeg is available on PATH.

    Raises:
        SystemExit: If ffmpeg is not found.
    """
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg not found on PATH.")
        print("Install it with:")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   sudo apt install ffmpeg")
        print("  Windows: https://ffmpeg.org/download.html")
        sys.exit(1)


def check_rsync() -> None:
    """Confirm rsync is available on PATH.

    Raises:
        SystemExit: If rsync is not found.
    """
    if shutil.which("rsync") is None:
        print("Error: rsync not found on PATH.")
        print("Install it with:")
        print("  macOS:   brew install rsync")
        print("  Linux:   sudo apt install rsync")
        print("  Windows: available via WSL or https://itefix.net/cwrsync")
        sys.exit(1)


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
        candidate = next(
            (d for d in drives if (d / "TALK-CLOCK.txt").exists() or d.name == "TALK-CLOCK"),
            None,
        )
        if candidate is None:
            raise FileNotFoundError("TALK-CLOCK SD card not found. Check it is inserted and mounted.")
        return candidate
    else:
        candidate = Path("/media") / Path.home().name / "TALK-CLOCK"
        if not candidate.exists():
            candidate = Path("/mnt/TALK-CLOCK")

    if not candidate.exists():
        raise FileNotFoundError(
            f"TALK-CLOCK SD card not found at {candidate}. Check it is inserted and mounted."
        )

    return candidate


def wav_needs_repair(path: Path) -> tuple[bool, int, int]:
    """Check if a WAV file matches the required format.

    Args:
        path: Path to the WAV file.

    Returns:
        Tuple of (needs_repair, actual_channels, actual_sample_rate).
    """
    with wave.open(str(path), "rb") as f:
        channels = f.getnchannels()
        sample_rate = f.getframerate()

    needs_repair = channels != REQUIRED_CHANNELS or sample_rate != REQUIRED_SAMPLE_RATE
    return needs_repair, channels, sample_rate


def repair_wav(path: Path) -> None:
    """Repair a WAV file to mono 22050 Hz using ffmpeg, replacing the original.

    Args:
        path: Path to the WAV file to repair.
    """
    tmp = path.with_suffix(".tmp.wav")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(path),
            "-ac", str(REQUIRED_CHANNELS),
            "-ar", str(REQUIRED_SAMPLE_RATE),
            str(tmp),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tmp.replace(path)


def repair_audio_assets() -> None:
    """Check and repair all WAV files in sd_card/audio_assets."""
    if not AUDIO_ASSETS_SRC.exists():
        print(f"Warning: audio_assets not found at {AUDIO_ASSETS_SRC}, skipping repair.")
        return

    wav_files = list(AUDIO_ASSETS_SRC.rglob("*.wav"))
    if not wav_files:
        print("No WAV files found in audio_assets.")
        return

    print(f"Checking {len(wav_files)} WAV file(s) in audio_assets...")
    repaired = 0
    for wav in wav_files:
        needs_repair, channels, sample_rate = wav_needs_repair(wav)
        if needs_repair:
            print(f"  Repairing: {wav.name} ({channels}ch, {sample_rate}Hz -> {REQUIRED_CHANNELS}ch, {REQUIRED_SAMPLE_RATE}Hz)")
            repair_wav(wav)
            repaired += 1

    if repaired == 0:
        print("All WAV files OK.")
    else:
        print(f"Repaired {repaired} file(s).")


def sync_to_sd(sd_root: Path) -> None:
    """Sync sd_card contents to the SD card root using rsync.

    Args:
        sd_root: Path to the SD card root.
    """
    # Trailing slash on source is required by rsync to copy contents, not the directory itself
    source = str(SD_CARD_SRC) + "/"
    dest = str(sd_root) + "/"

    print(f"Syncing {SD_CARD_SRC} -> {sd_root}")
    result = subprocess.run(
        [
            "rsync",
            "--recursive",
            "--update",            # skip files that are newer on destination
            "--checksum",          # compare by checksum not just timestamp (FAT32 timestamps are unreliable)
            "--exclude=.DS_Store",
            "--exclude=.Trashes",
            "--exclude=.Spotlight-V100",
            "--exclude=.fseventsd",
            "--verbose",
            source,
            dest,
        ],
    )
    # rsync exit code 23 = partial transfer due to permission errors on system dirs; treat as OK
    if result.returncode not in (0, 23):
        print(f"Error: rsync exited with code {result.returncode}")
        sys.exit(result.returncode)


def main() -> int:
    if not SD_CARD_SRC.exists():
        print(f"Error: source directory not found: {SD_CARD_SRC}")
        return 1

    check_ffmpeg()
    check_rsync()

    repair_audio_assets()

    try:
        sd_root = find_sd_card()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    print(f"SD card found at: {sd_root}")
    sync_to_sd(sd_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())