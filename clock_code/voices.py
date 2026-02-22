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
    "menu.announce_interval",
    "toggle.True",
    "toggle.False",
    "interval.hourly",
    "interval.half",
    "interval.quarter",
]


def scan_voices():
    """Scan SD card for available voices.

    Returns a dict keyed by voice directory name. Each value is a dict with:
        path       - full path to voice directory
        vocab      - loaded vocab dict
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

        if missing:
            print(f"Voice {name}: missing tokens {missing} - will use fallback")
        else:
            print(f"Voice {name}: OK")

        voices[name] = {
            "path": voice_path,
            "vocab": vocab,
            "missing": missing,
        }

    return voices


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