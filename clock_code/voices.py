# voices.py
#
# Scans the SD card for available voices and validates their vocab.json.
# A voice is any directory under /sd/ that contains a vocab.json file.
#
# Required tokens - if any are missing the voice is still accepted but
# missing tokens fall back to /sd/audio_assets/volume_boop.wav at runtime.

import os
import json

SD_ROOT = "/sd"
VOCAB_FILE = "vocab.json"
FALLBACK_AUDIO = "/sd/audio_assets/volume_boop.wav"

REQUIRED_TOKENS = [
    "menu.enter",
    "menu.exit",
    "menu.set_time",
    "menu.set_alarm",
    "menu.alarm_enabled",
    "menu.voice",
    "menu.mode",
    "menu.announce_interval",
    "toggle.True",
    "toggle.False",
    "interval.hourly",
    "interval.half",
    "interval.quarter",
    "voice.name",
    "mode.operational",
    "mode.broadcast",
    "mode.standard",
    "mode.casual",
]


def _scan_modes(voice_path):
    """Return sorted list of mode names from <voice>/rules/.

    A mode is any file matching <mode>_rules.json.
    """
    rules_path = f"{voice_path}/rules"
    modes = []
    try:
        for entry in os.listdir(rules_path):
            if entry.endswith("_rules.json"):
                modes.append(entry[: -len("_rules.json")])
    except OSError:
        pass
    return sorted(modes)


def scan_voices():
    """Scan SD card for available voices.

    Returns a dict keyed by voice directory name. Each value is a dict with:
        path       - full path to voice directory
        vocab      - loaded vocab dict
        modes      - sorted list of available mode names
        missing    - list of required tokens not found in vocab
    """
    voices = {}

    try:
        entries = os.listdir(SD_ROOT)
    except OSError as e:
        print(f"Cannot read SD root: {e}")
        return voices

    for name in entries:
        voice_path = f"{SD_ROOT}/{name}"
        vocab_path = f"{voice_path}/{VOCAB_FILE}"

        try:
            os.stat(vocab_path)
        except OSError:
            continue

        try:
            with open(vocab_path, "r") as f:
                vocab = json.load(f)
        except Exception as e:
            print(f"Skipping {name}: vocab.json unreadable ({e})")
            continue

        missing = [t for t in REQUIRED_TOKENS if t not in vocab]
        modes   = _scan_modes(voice_path)

        if missing:
            print(f"Voice {name}: missing tokens {missing} - will use fallback")
        else:
            print(f"Voice {name}: OK")
        print(f"Voice {name}: modes {modes}")

        voices[name] = {
            "path":    voice_path,
            "vocab":   vocab,
            "modes":   modes,
            "missing": missing,
        }

    return voices


def load_rules(voice_entry, mode):
    """Load rules JSON for a given voice and mode.

    Args:
        voice_entry: single entry from scan_voices() return value.
        mode: mode name string e.g. "casual".

    Returns:
        Parsed rules dict, or None if file not found.
    """
    path = f"{voice_entry['path']}/rules/{mode}_rules.json"
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"load_rules failed {path}: {e}")
        return None


def resolve_token(voice_entry, token):
    """Resolve a token to an audio file path.

    Uses fallback if the token is missing from vocab.

    Args:
        voice_entry: single entry from scan_voices() return value
        token: vocab key string e.g. "menu.enter"

    Returns:
        Full path to wav file.
    """
    vocab = voice_entry["vocab"]
    if token in vocab:
        filename = vocab[token]
        return f"{voice_entry['path']}/audio/{filename}"
    print(f"Token '{token}' not found, using fallback")
    return FALLBACK_AUDIO
