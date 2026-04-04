# src/talking_clock_audio/deploy.py

"""SD card deployment for talking-clock-audio voice packages.

Handles:
- Mounted volume detection across macOS, Linux, and Windows
- Scanning local and SD card voice packages
- Copying voice packages to SD card
- Deleting voice packages from SD card
"""

import json
import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


GENERATION_INFO_FILE = "generation_info.json"
VOICE_SUBDIRS = {"audio", "rules"}
VOICE_FILES = {"vocab.json", GENERATION_INFO_FILE}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class VoicePackage:
    """A voice package on disk, either local or on the SD card.

    Attributes:
        name: Directory name, e.g. 'en_US_lessac_medium'.
        path: Full path to the package directory.
        locale: Locale code from generation_info.json, or None if missing.
        voice: Voice name from generation_info.json, or None if missing.
        quality: Quality level from generation_info.json, or None if missing.
        generated_at: ISO timestamp string, or None if missing.
        info: Full parsed generation_info.json dict, or empty dict.
    """
    name: str
    path: Path
    locale: Optional[str]
    voice: Optional[str]
    quality: Optional[str]
    generated_at: Optional[str]
    info: dict


# ---------------------------------------------------------------------------
# Volume detection
# ---------------------------------------------------------------------------

def detect_mounted_volumes() -> list[Path]:
    """Return candidate mounted volumes for the current platform.

    macOS:   /Volumes/* (excludes the root system volume)
    Linux:   /media/<user>/* and /mnt/*
    Windows: scans drive letters A-Z for removable drives

    Returns:
        List of Path objects for candidate volumes.
    """
    system = platform.system()

    if system == "Darwin":
        base = Path("/Volumes")
        return sorted(
            p for p in base.iterdir()
            if p.is_dir() and p.name != "Macintosh HD"
        ) if base.exists() else []

    if system == "Linux":
        candidates = []
        user = os.environ.get("USER", "")
        for base in [Path(f"/media/{user}"), Path("/media"), Path("/mnt")]:
            if base.exists():
                for p in base.iterdir():
                    if p.is_dir():
                        candidates.append(p)
        return sorted(set(candidates))

    if system == "Windows":
        import string
        import ctypes
        candidates = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                drive = Path(f"{letter}:\\")
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(str(drive))
                # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3
                # Include both removable and fixed to not exclude SD readers
                if drive_type in (2, 3) and letter != "C":
                    candidates.append(drive)
        return candidates

    return []


# ---------------------------------------------------------------------------
# Package scanning
# ---------------------------------------------------------------------------

def _read_generation_info(package_dir: Path) -> dict:
    """Read generation_info.json from a package directory.

    Returns empty dict if the file is missing or unreadable.
    """
    info_path = package_dir / GENERATION_INFO_FILE
    if not info_path.exists():
        return {}
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _is_voice_package(path: Path) -> bool:
    """Return True if path looks like a valid generated voice package.

    A package must contain vocab.json and an audio/ subdirectory.
    """
    return (path / "vocab.json").exists() and (path / "audio").is_dir()


def scan_local_packages(source_dir: Path) -> list[VoicePackage]:
    """Scan a local audio directory for generated voice packages.

    Args:
        source_dir: Path to the local audio output directory.

    Returns:
        List of VoicePackage objects, sorted by name.
    """
    if not source_dir.exists():
        return []

    packages = []
    for entry in sorted(source_dir.iterdir()):
        if not entry.is_dir():
            continue
        if not _is_voice_package(entry):
            continue
        info = _read_generation_info(entry)
        packages.append(VoicePackage(
            name=entry.name,
            path=entry,
            locale=info.get("locale"),
            voice=info.get("voice"),
            quality=info.get("quality"),
            generated_at=info.get("generated_at"),
            info=info,
        ))
    return packages


def scan_sd_packages(sd_root: Path) -> list[VoicePackage]:
    """Scan the root of a mounted SD card for deployed voice packages.

    Args:
        sd_root: Path to the mounted SD card volume root.

    Returns:
        List of VoicePackage objects, sorted by name.
    """
    return scan_local_packages(sd_root)


# ---------------------------------------------------------------------------
# Copy and delete
# ---------------------------------------------------------------------------

def copy_package(package: VoicePackage, sd_root: Path) -> Path:
    """Copy a voice package directory to the SD card root.

    Copies the entire package directory tree. Destination is
    sd_root / package.name.

    Args:
        package: The local VoicePackage to copy.
        sd_root: Root path of the mounted SD card.

    Returns:
        Path to the destination directory on the SD card.

    Raises:
        OSError: If the copy fails.
    """
    destination = sd_root / package.name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(str(package.path), str(destination))
    return destination


def delete_package(package: VoicePackage) -> None:
    """Delete a voice package directory from the SD card.

    Args:
        package: The VoicePackage to delete. Its path must point to
            a directory on the SD card.

    Raises:
        OSError: If the delete fails.
    """
    if package.path.exists():
        shutil.rmtree(package.path)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def format_package_summary(package: VoicePackage) -> str:
    """Return a one-line human-readable summary of a voice package.

    Args:
        package: The VoicePackage to summarize.

    Returns:
        Formatted string, e.g. 'en_US_lessac_medium  (lessac medium, 2025-04-01)'
    """
    parts = []
    if package.voice:
        parts.append(package.voice)
    if package.quality:
        parts.append(package.quality)
    if package.generated_at:
        date = package.generated_at[:10]
        parts.append(date)
    detail = ", ".join(parts) if parts else "no info"
    return f"{package.name:<32} ({detail})"