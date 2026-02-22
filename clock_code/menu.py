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
# Events passed to handle_event() are plain dicts:
#   { "key": 0|1|2, "type": "short"|"long" }
#
# Callers must supply two callables at construction:
#   play_token(token)   - plays a single audio token, returns when done
#   on_action(action)   - called when an action item is confirmed
#                         e.g. on_action("set_time"), on_action("set_alarm")

import time

ANNOUNCE = 0
PLUS     = 1
MINUS    = 2

STATE_IDLE  = "idle"
STATE_MENU  = "menu"

INACTIVITY_TIMEOUT = 30.0


class Menu:
    def __init__(self, items, config, save_config, play_token, on_action):
        """Initialise the menu.

        Args:
            items:       list of item dicts from menu.json, with voice options
                         already populated for the "voice" toggle.
            config:      the live config dict (mutated directly on toggle).
            save_config: callable(config) - persists config to SD.
            play_token:  callable(token: str) - plays audio token, blocking.
            on_action:   callable(action: str) - fires when an action is confirmed.
        """
        self._items      = items
        self._config     = config
        self._save       = save_config
        self._play       = play_token
        self._on_action  = on_action

        self._state      = STATE_IDLE
        self._index      = 0
        self._last_event = None  # monotonic time of last interaction in menu

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def active(self):
        """True when the menu is open."""
        return self._state == STATE_MENU

    def enter(self):
        """Open the menu. Call when long-press PLUS/MINUS detected in normal mode."""
        self._state      = STATE_MENU
        self._index      = 0
        self._last_event = time.monotonic()
        self._play("menu.enter")
        self._speak_current()

    def handle_event(self, key, press_type):
        """Process a button event while menu is active.

        Args:
            key:        ANNOUNCE, PLUS, or MINUS
            press_type: "short" or "long"

        Returns:
            True if the event was consumed by the menu, False otherwise.
        """
        if self._state != STATE_MENU:
            return False

        self._last_event = time.monotonic()

        if key == PLUS and press_type == "short":
            self._scroll(1)
            return True

        if key == MINUS and press_type == "short":
            self._scroll(-1)
            return True

        if key == ANNOUNCE and press_type == "short":
            self._confirm()
            return True

        if key == ANNOUNCE and press_type == "long":
            self._exit()
            return True

        return True  # consume all events while menu is open

    def tick(self):
        """Call from main loop every iteration to check inactivity timeout."""
        if self._state != STATE_MENU:
            return
        if (time.monotonic() - self._last_event) >= INACTIVITY_TIMEOUT:
            print("Menu: inactivity timeout")
            self._exit()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _scroll(self, direction):
        self._index = (self._index + direction) % len(self._items)
        self._speak_current()

    def _speak_current(self):
        item = self._items[self._index]
        self._play(item["audio_token"])

    def _confirm(self):
        item = self._items[self._index]

        if item["type"] == "action":
            self._exit()
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

        # Find current index in options, default to 0 if not found
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
        print(f"Menu: {config_key} = {next_value}")

        # For voice toggle, caller is responsible for reloading vocab.
        # We signal this by firing on_action("reload_voice") after saving.
        if item["id"] == "voice":
            self._play(next_opt["audio_token"])
            self._on_action("reload_voice")
        else:
            self._play(next_opt["audio_token"])

    def _exit(self):
        self._state = STATE_IDLE
        self._play("menu.exit")
        print("Menu: exited")