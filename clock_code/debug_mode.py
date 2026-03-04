# debug_mode.py
#
# Speaker test mode for the talking clock.
#
# Entry: hold ANNOUNCE (GP6) during boot. Checked before keypad is
# initialised using a plain digitalio read.
#
# Behaviour:
#   ANNOUNCE      - play all files in current variant directory in order
#                   interruptible at any point by PLUS or MINUS
#   PLUS          - next variant directory
#   MINUS         - previous variant directory
#   Reboot        - exit (hardware button on RUN pin)
#
# Files are read from /sd/debug/<variant>/ in sorted order.
# Directories are sorted alphabetically.
# Each directory is expected to contain exactly 3 files: label + 2 sentences.


import os
import time
import board
import digitalio
import audiocore
import keypad

DEBUG_ROOT  = "/sd/debug"
ANNOUNCE    = 0
PLUS        = 1
MINUS       = 2
HOLD_SECONDS = 1.5


def check_debug_boot():
    """Return True if ANNOUNCE is held at boot time.

    Uses a raw digitalio read before keypad is initialised.
    ANNOUNCE is GP6, pulled up, active low (value_when_pressed=False).
    """
    pin = digitalio.DigitalInOut(board.GP6)
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    pressed = not pin.value
    pin.deinit()
    return pressed


def _sorted_entries(path):
    """Return sorted list of entries in a directory, ignoring hidden files."""
    try:
        return sorted(e for e in os.listdir(path) if not e.startswith('.'))
    except OSError:
        return []


def _scan_variants():
    """Return sorted list of variant directory paths under DEBUG_ROOT."""
    dirs = []
    for entry in _sorted_entries(DEBUG_ROOT):
        full = f"{DEBUG_ROOT}/{entry}"
        try:
            os.listdir(full)  # will raise OSError if not a directory
            dirs.append(full)
        except OSError:
            pass
    return dirs


def _scan_files(variant_path):
    """Return sorted list of WAV file paths in a variant directory."""
    files = []
    for entry in _sorted_entries(variant_path):
        if entry.endswith('.wav'):
            files.append(f"{variant_path}/{entry}")
    return files


def run_debug_mode(mixer):
    """Run the speaker test loop.

    Args:
        mixer: Initialised audiomixer.Mixer with at least one voice.
    """
    print("DEBUG MODE")

    variants = _scan_variants()
    if not variants:
        print(f"No variant directories found in {DEBUG_ROOT}")
        return

    print(f"Found {len(variants)} variants:")
    for v in variants:
        print(f"  {v}")

    keys = keypad.Keys(
        (board.GP6, board.GP7, board.GP8),
        value_when_pressed=False,
        pull=True,
    )

    index = 0
    held = {ANNOUNCE: None, PLUS: None, MINUS: None}

    def stop():
        mixer.voice[0].stop()

    def play_file(path):
        """Play a single WAV file to completion, return False if interrupted."""
        try:
            with open(path, "rb") as f:
                wav = audiocore.WaveFile(f)
                mixer.voice[0].play(wav)
                while mixer.voice[0].playing:
                    ev = keys.events.get()
                    if ev and ev.pressed and ev.key_number in (PLUS, MINUS):
                        stop()
                        # drain the triggering event so main loop sees it
                        keys.events.clear()
                        return False
            return True
        except Exception as e:
            print(f"play_file failed {path}: {e}")
            return True

    def play_variant(variant_path):
        """Play all files in a variant directory in order."""
        files = _scan_files(variant_path)
        if not files:
            print(f"No WAV files in {variant_path}")
            return
        print(f"Playing: {variant_path} ({len(files)} files)")
        for path in files:
            print(f"  {path}")
            if not play_file(path):
                return

    def show_current():
        name = variants[index].split('/')[-1]
        print(f"Variant {index + 1}/{len(variants)}: {name}")

    show_current()

    while True:
        now_t = time.monotonic()
        event = keys.events.get()

        if event:
            key = event.key_number

            if event.pressed:
                held[key] = now_t

            if event.released:
                duration = (now_t - held[key]) if held[key] is not None else 0
                held[key] = None

                if key == ANNOUNCE:
                    play_variant(variants[index])

                elif key == PLUS:
                    stop()
                    index = (index + 1) % len(variants)
                    show_current()

                elif key == MINUS:
                    stop()
                    index = (index - 1) % len(variants)
                    show_current()

        time.sleep(0.02)
