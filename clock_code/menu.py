# menu.py
#
# Audio-only settings menu state machine.
#
# This module is event-driven. The main loop calls handle_event() with each
# button event and calls tick() on every iteration for timeout checking.
# It never blocks and never reads buttons directly.
#
# Button constants match code.py:
#   ANNOUNCE = 0, PLUS = 1, MINUS = 2
#
# Callers must supply two callables at construction:
#   play_token(token)         - plays a token through the active voice
#   play_token_for_voice(voice_entry, token)
#                             - plays a token through a specific voice entry
#   on_action(action)         - called when an action item is confirmed

import time

ANNOUNCE = 0
PLUS     = 1
MINUS    = 2

STATE_IDLE = "idle"
STATE_MENU = "menu"

INACTIVITY_TIMEOUT = 30.0


class Menu:
    def __init__(self, items, config, save_config, play_token, on_action,
                 play_token_for_voice=None, voices=None):
        """Initialise the menu.

        Args:
            items:                list of item dicts from menu.json.
            config:               the live config dict (mutated directly on toggle).
            save_config:          callable(config) - persists config to SD.
            play_token:           callable(token) - plays token in active voice.
            on_action:            callable(action) - fires when action confirmed.
            play_token_for_voice: callable(voice_entry, token) - for voice toggle.
            voices:               the full voices dict from scan_voices().
        """
        self._items                = items
        self._config               = config
        self._save                 = save_config
        self._play                 = play_token
        self._play_for_voice       = play_token_for_voice
        self._voices               = voices or {}
        self._on_action            = on_action

        self._state      = STATE_IDLE
        self._index      = 0
        self._last_event = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def active(self):
        """True when the menu is open."""
        return self._state == STATE_MENU

    def enter(self):
        """Open the menu."""
        self._state      = STATE_MENU
        self._index      = 0
        self._last_event = time.monotonic()
        print("Menu: entered")
        self._play("menu.enter")
        self._speak_current()

    def handle_event(self, key, press_type):
        """Process a button event while menu is active.

        Any long press exits the menu.
        Short PLUS/MINUS scrolls. Short ANNOUNCE confirms.

        Returns:
            True if the event was consumed by the menu.
        """
        if self._state != STATE_MENU:
            return False

        self._last_event = time.monotonic()

        if press_type == "long":
            print(f"Menu: long-press exit (key={key})")
            self._exit()
            return True

        if key == PLUS and press_type == "short":
            self._scroll(1)
            return True

        if key == MINUS and press_type == "short":
            self._scroll(-1)
            return True

        if key == ANNOUNCE and press_type == "short":
            print(f"Menu: confirm on '{self._items[self._index]['id']}'")
            self._confirm()
            return True

        return True  # consume all events while menu is open

    def tick(self):
        """Call from main loop every iteration to check inactivity timeout."""
        if self._state != STATE_MENU:
            return
        if (time.monotonic() - self._last_event) >= INACTIVITY_TIMEOUT:
            print("Menu: inactivity timeout, exiting")
            self._exit()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _scroll(self, direction):
        self._index = (self._index + direction) % len(self._items)
        item = self._items[self._index]
        print(f"Menu: scroll to [{self._index}] '{item['id']}'")
        self._speak_current()

    def _speak_current(self):
        item = self._items[self._index]
        self._play(item["audio_token"])

    def _confirm(self):
        item = self._items[self._index]

        if item["type"] == "action":
            self._exit(silent=True)
            self._on_action(item["action"])

        elif item["type"] == "toggle":
            self._cycle_toggle(item)

    def _cycle_toggle(self, item):
        options = item["options"]
        if not options:
            print(f"Menu: toggle '{item['id']}' has no options")
            return

        config_key = item["config_key"]
        current    = self._config.get(config_key)

        current_idx = 0
        for i, opt in enumerate(options):
            if opt["value"] == current:
                current_idx = i
                break

        next_idx   = (current_idx + 1) % len(options)
        next_opt   = options[next_idx]
        next_value = next_opt["value"]

        self._config[config_key] = next_value
        self._save(self._config)
        print(f"Menu: {config_key} {current!r} -> {next_value!r}")

        if item["id"] == "voice":
            # Announce the new voice name in that voice's own language
            target_entry = self._voices.get(next_value)
            if target_entry and self._play_for_voice:
                self._play_for_voice(target_entry, "voice.name")
            else:
                self._play(next_opt["audio_token"])
            self._on_action("reload_voice")

        elif item["id"] == "mode":
            self._on_action("reload_mode")

        else:
            self._play(next_opt["audio_token"])

    def _exit(self, silent=False):
        self._state = STATE_IDLE
        if not silent:
            self._play("menu.exit")
        print("Menu: exited")
