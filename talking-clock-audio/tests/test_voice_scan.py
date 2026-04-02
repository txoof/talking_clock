# test_voices.py
#
# Smoke test for voices.py
# Run on Mac against a local mock SD structure, no Pico needed.
#
# Usage:
#   python test_voices.py
#
# Expects a directory called "sd_mock/" next to this file structured as:
#   sd_mock/
#     audio_assets/
#       volume_boop.wav
#     en_US_lessac_medium_standard/
#       vocab.json
#       audio/
#         ... wav files ...

import os
import sys
import json

# Patch SD_ROOT to point at local mock before importing
os.environ["SD_ROOT_OVERRIDE"] = "sd_mock"

# Inline the module logic with override so we don't need CircuitPython
SD_ROOT = "sd_mock"
VOCAB_FILE = "vocab.json"
FALLBACK_AUDIO = "sd_mock/audio_assets/volume_boop.wav"

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
    voices = {}
    try:
        entries = os.listdir(SD_ROOT)
    except OSError as e:
        print(f"Cannot read SD root: {e}")
        return voices

    for name in entries:
        voice_path = f"{SD_ROOT}/{name}"
        vocab_path = f"{voice_path}/{VOCAB_FILE}"

        if not os.path.isfile(vocab_path):
            continue

        try:
            with open(vocab_path, "r") as f:
                vocab = json.load(f)
        except Exception as e:
            print(f"Skipping {name}: vocab.json unreadable ({e})")
            continue

        missing = [t for t in REQUIRED_TOKENS if t not in vocab]

        if missing:
            print(f"Voice {name}: missing tokens {missing}")
        else:
            print(f"Voice {name}: OK")

        voices[name] = {"path": voice_path, "vocab": vocab, "missing": missing}

    return voices


def resolve_token(voice_entry, token):
    vocab = voice_entry["vocab"]
    if token in vocab:
        filename = vocab[token]
        return f"{voice_entry['path']}/audio/{filename}"
    print(f"Token '{token}' not found, using fallback")
    return FALLBACK_AUDIO


if __name__ == "__main__":
    print("--- Scanning voices ---")
    voices = scan_voices()

    if not voices:
        print("No voices found. Check that sd_mock/ exists with at least one voice directory.")
        sys.exit(1)

    print(f"\nFound {len(voices)} voice(s): {list(voices.keys())}")

    print("\n--- Token resolution spot check ---")
    for name, entry in voices.items():
        print(f"\nVoice: {name}")
        for token in REQUIRED_TOKENS:
            path = resolve_token(entry, token)
            print(f"  {token} -> {path}")