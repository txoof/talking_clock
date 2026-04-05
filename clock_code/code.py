import time
time.sleep(3)
print("start")

import board
import busio
import digitalio
import storage
import sdcardio
import audiobusio
import audiocore
import audiomixer
import keypad
import json
import os

import adafruit_ds3231

from voices import scan_voices, resolve_token, load_rules, scan_alarm_tones
from menu import Menu
from debug_mode import check_debug_boot, run_debug_mode
import pico_rules

VERSION = "0.4.0"

# --- Debug boot check (must run before keypad.Keys takes GP6) ---

_debug_boot = check_debug_boot()

# --- Hardware init ---

spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
sdcard = sdcardio.SDCard(spi, board.GP17)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
print("SD card mounted")

i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
rtc = adafruit_ds3231.DS3231(i2c)

gain = digitalio.DigitalInOut(board.GP13)
gain.direction = digitalio.Direction.OUTPUT
gain.value = True

sd = digitalio.DigitalInOut(board.GP9)
sd.direction = digitalio.Direction.OUTPUT
sd.value = True

ANNOUNCE = 0
PLUS     = 1
MINUS    = 2

if not _debug_boot:
    keys = keypad.Keys(
        (board.GP6, board.GP7, board.GP8),
        value_when_pressed=False,
        pull=True,
    )

audio = audiobusio.I2SOut(bit_clock=board.GP11, word_select=board.GP12, data=board.GP10)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=2048)
audio.play(mixer)

# --- Enter debug mode if ANNOUNCE was held at boot ---

if _debug_boot:
    print("Debug mode requested - handing off")
    run_debug_mode(mixer)
    # run_debug_mode never returns; reboot to exit
    while True:
        pass

# --- Config ---

CONFIG_PATH    = "/sd/config.json"
MENU_PATH      = "/menu.json"
VOLUME_STEPS   = 20
VOLUME_DELAY   = 5.5
HOLD_SECONDS   = 1.5
VALUE_REPEAT_INTERVAL = 0.150  # seconds between increments when held
ALARM_MAX_SECS = 300  # 5 minutes

DEFAULT_CONFIG = {
    "volume_step":       9,
    "voice":             "en_US_lessac_medium",
    "mode":              "standard",
    "alarm_enabled":     False,
    "alarm_hour":        7,
    "alarm_minute":      0,
    "alarm_tone":        "/sd/audio_assets/volume_boop.wav",
    "announce_interval": "off",
}

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            if k not in data:
                data[k] = v
        data["volume_step"] = max(1, data.get("volume_step", DEFAULT_CONFIG["volume_step"]))
        return data
    except Exception:
        return dict(DEFAULT_CONFIG)

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f)
        print("Config saved")
    except Exception as e:
        print("Config save failed:", e)

config = load_config()
save_config(config)

# --- Voice / vocab / rules ---

voices = scan_voices()
alarm_tones = scan_alarm_tones()
print(f"Alarm tones: {[t['filename'] for t in alarm_tones]}")

def load_voice(name):
    if name not in voices:
        name = list(voices.keys())[0]
        print(f"Requested voice not found, using {name}")
    return name, voices[name]

active_voice_name, active_voice = load_voice(config["voice"])
print(f"Voice: {active_voice_name}")

def reload_rules():
    global active_rules
    active_rules = load_rules(active_voice, config["mode"])
    if active_rules:
        print(f"Rules loaded: {config['mode']}")
    else:
        print(f"Rules load failed for mode: {config['mode']}")

active_rules = None
reload_rules()

# --- Startup diagnostics ---
if active_voice:
    print(f"Vocab: {len(active_voice['vocab'])} keys")
if active_rules:
    print(f"Rules: {list(active_rules.get('modes', {}).keys())}")
else:
    print("Rules: failed to load")

volume_step        = config.get("volume_step", 7)
mixer.voice[0].level = volume_step / VOLUME_STEPS
volume_dirty_since = None

# --- Audio ---

BOOP_PATH = "/sd/audio_assets/volume_boop.wav"
BEEP_PATH = "/sd/audio_assets/beep.wav"

def play_path(path):
    try:
        with open(path, "rb") as f:
            wav = audiocore.WaveFile(f)
            mixer.voice[0].play(wav)
            while mixer.voice[0].playing:
                pass
    except Exception as e:
        print(f"play_path failed {path}: {e}")

def stop_audio():
    mixer.voice[0].stop()

def play_token(token):
    path = resolve_token(active_voice, token)
    play_path(path)

def play_token_for_voice(voice_entry, token):
    """Resolve and play a token through a specific voice, not the active one."""
    path = resolve_token(voice_entry, token)
    play_path(path)

def play_boop():
    play_path(BOOP_PATH)

def discard_events():
    while keys.events.get() is not None:
        pass

def play_sequence(hour_24, minute):
    """Play a time announcement using active rules, interruptible by PLUS or MINUS."""
    vocab = active_voice["vocab"]

    if active_rules:
        files = pico_rules.get_audio_files(active_rules, vocab, config["mode"], hour_24, minute)
        if files:
            files = [f"{active_voice['path']}/audio/{f}" for f in files]
        else:
            print(f"No rule match for {hour_24:02d}:{minute:02d} in mode {config['mode']}")
            return
    else:
        print("No rules loaded, cannot announce")
        return

    print(f"{hour_24:02d}:{minute:02d} [{config['mode']}] -> {files}")

    handles = []
    wavs    = []
    try:
        for path in files:
            fh = open(path, "rb")
            handles.append(fh)
            wavs.append(audiocore.WaveFile(fh))
        for wav in wavs:
            mixer.voice[0].play(wav)
            while mixer.voice[0].playing:
                ev = keys.events.get()
                if ev and ev.pressed and ev.key_number in (PLUS, MINUS):
                    stop_audio()
                    discard_events()
                    return
    finally:
        for fh in handles:
            fh.close()
        discard_events()

# --- Menu ---

def load_menu_items():
    with open(MENU_PATH, "r") as f:
        data = json.load(f)
    items = data["items"]

    for item in items:
        if item["id"] == "voice":
            item["options"] = [
                {"value": name, "audio_token": "voice.name", "voice": name}
                for name in voices.keys()
            ]
        elif item["id"] == "mode":
            item["options"] = [
                {"value": m, "audio_token": f"mode.{m}"}
                for m in active_voice.get("modes", [])
            ]
        elif item["id"] == "alarm_tone":
            item["options"] = [
                {"value": t["path"], "audio_token": None, "index": t["index"], "path": t["path"]}
                for t in alarm_tones
            ]
    return items

def on_action(action):
    global mode, set_hour, set_minute, active_voice_name, active_voice, last_interaction, value_repeat_key, value_repeat_next, value_did_repeat

    if action == "set_time":
        h, m = now()
        set_hour          = h
        set_minute        = m
        mode              = "set_hour"
        last_interaction  = time.monotonic()
        value_repeat_key  = None
        value_repeat_next = None
        value_did_repeat  = False
        play_token("menu.set_time")
        play_sequence_hour(set_hour)

    elif action == "set_alarm":
        set_hour          = config["alarm_hour"]
        set_minute        = config["alarm_minute"]
        mode              = "set_alarm_hour"
        last_interaction  = time.monotonic()
        value_repeat_key  = None
        value_repeat_next = None
        value_did_repeat  = False
        play_token("menu.set_alarm")
        play_sequence_hour_alarm(set_hour)

    elif action == "reload_voice":
        name = config["voice"]
        active_voice_name, active_voice = load_voice(name)
        print(f"Voice reloaded: {active_voice_name}")
        reload_rules()
        play_token("menu.enter")

    elif action == "reload_mode":
        reload_rules()
        play_token(f"mode.{config['mode']}")
        h, m = now()
        play_sequence(h, m)

menu = Menu(
    items                = load_menu_items(),
    config               = config,
    save_config          = save_config,
    play_token           = play_token,
    on_action            = on_action,
    play_token_for_voice = play_token_for_voice,
    voices               = voices,
    play_path            = play_path,
)

# --- Time setting helpers ---

def play_sequence_hour(h):
    play_sequence(h, 0)

def play_sequence_hour_alarm(h):
    # Play hour for alarm setting - always appends day period word for clarity.
    play_sequence(h, 0)
    if active_rules:
        day_period_table = active_rules.get("day_period", [])
        period = pico_rules._resolve_period(day_period_table, h)
        if period:
            path = resolve_token(active_voice, f"words.{period}")
            play_path(path)

def play_sequence_minute(m):
    path = resolve_token(active_voice, f"number_words.{m}")
    play_path(path)

# --- Alarm ---

ALARM_TONE_REPEATS = 3
ALARM_CYCLE_PAUSE  = 3.0  # seconds between cycles

alarm_ringing    = False
alarm_start      = None
alarm_next_cycle = None

def _alarm_tone_path():
    return config.get("alarm_tone", "/sd/audio_assets/volume_boop.wav")

def check_alarm():
    global alarm_ringing, alarm_start, alarm_next_cycle
    if not config.get("alarm_enabled"):
        return
    t = rtc.datetime
    if t.tm_hour == config["alarm_hour"] and t.tm_min == config["alarm_minute"] and t.tm_sec < 2:
        if not alarm_ringing:
            alarm_ringing    = True
            alarm_start      = time.monotonic()
            alarm_next_cycle = alarm_start
            print("Alarm triggered")

def tick_alarm():
    global alarm_ringing, alarm_next_cycle
    if not alarm_ringing:
        return
    now_t = time.monotonic()
    if (now_t - alarm_start) >= ALARM_MAX_SECS:
        alarm_ringing = False
        print("Alarm timed out")
        return
    if now_t >= alarm_next_cycle:
        tone_path = _alarm_tone_path()
        for _ in range(ALARM_TONE_REPEATS):
            play_path(tone_path)
            if not alarm_ringing:
                return
        h, m = now()
        play_sequence(h, m)
        alarm_next_cycle = time.monotonic() + ALARM_CYCLE_PAUSE

def silence_alarm():
    global alarm_ringing
    alarm_ringing = False
    print("Alarm silenced")
    h, m = now()
    play_sequence(h, m)

# --- Auto-announce ---

last_announced_minute = -1

def check_auto_announce():
    global last_announced_minute
    interval = config.get("announce_interval", "off")
    if interval == "off":
        return
    t = rtc.datetime
    h = t.tm_hour
    m = t.tm_min
    if m == last_announced_minute:
        return
    announce = False
    if interval == "hourly" and m == 0:
        announce = True
    elif interval == "half" and m in (0, 30):
        announce = True
    elif interval == "quarter" and m in (0, 15, 30, 45):
        announce = True
    if announce:
        last_announced_minute = m
        play_sequence(h, m)

# --- State ---

mode             = "normal"
set_hour         = 0
set_minute       = 0
held             = {PLUS: None, MINUS: None, ANNOUNCE: None}
last_interaction = None
VALUE_ENTRY_TIMEOUT = 30.0

value_repeat_key  = None
value_repeat_next = None
value_did_repeat  = False

def now():
    t = rtc.datetime
    return t.tm_hour, t.tm_min

def print_status():
    print(f"Version: {VERSION}")
    print(f"Config: {config}")
    print(f"Voice: {active_voice_name}  Mode: {config['mode']}")

print_status()
h, m = now()
print(f"RTC time: {h:02d}:{m:02d}")

# --- Main loop ---

while True:
    now_t = time.monotonic()
    event = keys.events.get()

    if event:
        key = event.key_number

        if event.pressed:
            held[key] = now_t

        # --- Alarm silencing takes priority ---
        if alarm_ringing and event.pressed and key == ANNOUNCE:
            held[key] = None
            silence_alarm()
            continue

        # --- Menu active: forward all events ---
        if menu.active:
            if event.released:
                duration = (now_t - held[key]) if held[key] is not None else 0
                held[key] = None
                press_type = "long" if duration >= HOLD_SECONDS else "short"
                print(f"Menu: key={key} duration={duration:.2f}s type={press_type}")
                menu.handle_event(key, press_type)
            continue

        # --- Normal mode ---
        if mode == "normal":
            if key in (PLUS, MINUS):
                if event.released:
                    press_time = held.get(key)
                    held[key] = None
                    duration = (now_t - press_time) if press_time is not None else 0
                    if duration < HOLD_SECONDS:
                        if key == PLUS:
                            volume_step = min(VOLUME_STEPS, volume_step + 1)
                        else:
                            volume_step = max(1, volume_step - 1)
                        mixer.voice[0].level = volume_step / VOLUME_STEPS
                        print(f"Volume: {volume_step}/{VOLUME_STEPS}")
                        play_boop()
                        volume_dirty_since = now_t

            if event.pressed and key == ANNOUNCE:
                h, m = now()
                play_sequence(h, m)

            if event.released and key == ANNOUNCE:
                held[key] = None

        # --- Set time: hour ---
        elif mode == "set_hour":
            if event.pressed and key in (PLUS, MINUS):
                last_interaction    = now_t
                value_repeat_key    = key
                value_repeat_next   = now_t + HOLD_SECONDS
                value_did_repeat    = False
            elif event.released and key in (PLUS, MINUS):
                value_repeat_key  = None
                value_repeat_next = None
                last_interaction  = now_t
                if not value_did_repeat:
                    set_hour = (set_hour + 1) % 24 if key == PLUS else (set_hour - 1) % 24
                play_sequence_hour(set_hour)
                value_did_repeat = False
            elif event.pressed and key == ANNOUNCE:
                value_repeat_key = None
                last_interaction = now_t
                mode = "set_minute"
                play_sequence_minute(set_minute)

        # --- Set time: minute ---
        elif mode == "set_minute":
            if event.pressed and key in (PLUS, MINUS):
                last_interaction    = now_t
                value_repeat_key    = key
                value_repeat_next   = now_t + HOLD_SECONDS
                value_did_repeat    = False
            elif event.released and key in (PLUS, MINUS):
                value_repeat_key  = None
                value_repeat_next = None
                last_interaction  = now_t
                if not value_did_repeat:
                    set_minute = (set_minute + 1) % 60 if key == PLUS else (set_minute - 1) % 60
                play_sequence_minute(set_minute)
                value_did_repeat = False
            elif event.pressed and key == ANNOUNCE:
                value_repeat_key = None
                last_interaction = now_t
                t = rtc.datetime
                rtc.datetime = time.struct_time((
                    t.tm_year, t.tm_mon, t.tm_mday,
                    set_hour, set_minute, 0,
                    t.tm_wday, t.tm_yday, t.tm_isdst
                ))
                mode = "normal"
                play_sequence(set_hour, set_minute)

        # --- Set alarm: hour ---
        elif mode == "set_alarm_hour":
            if event.pressed and key in (PLUS, MINUS):
                last_interaction    = now_t
                value_repeat_key    = key
                value_repeat_next   = now_t + HOLD_SECONDS
                value_did_repeat    = False
            elif event.released and key in (PLUS, MINUS):
                value_repeat_key  = None
                value_repeat_next = None
                last_interaction  = now_t
                if not value_did_repeat:
                    set_hour = (set_hour + 1) % 24 if key == PLUS else (set_hour - 1) % 24
                play_sequence_hour_alarm(set_hour)
                value_did_repeat = False
            elif event.pressed and key == ANNOUNCE:
                value_repeat_key = None
                last_interaction = now_t
                mode = "set_alarm_minute"
                play_sequence_minute(set_minute)

        # --- Set alarm: minute ---
        elif mode == "set_alarm_minute":
            if event.pressed and key in (PLUS, MINUS):
                last_interaction    = now_t
                value_repeat_key    = key
                value_repeat_next   = now_t + HOLD_SECONDS
                value_did_repeat    = False
            elif event.released and key in (PLUS, MINUS):
                value_repeat_key  = None
                value_repeat_next = None
                last_interaction  = now_t
                if not value_did_repeat:
                    set_minute = (set_minute + 1) % 60 if key == PLUS else (set_minute - 1) % 60
                play_sequence_minute(set_minute)
                value_did_repeat = False
            elif event.pressed and key == ANNOUNCE:
                value_repeat_key = None
                last_interaction = now_t
                config["alarm_hour"]   = set_hour
                config["alarm_minute"] = set_minute
                save_config(config)
                mode = "normal"
                play_sequence(set_hour, set_minute)

    # --- Long press PLUS/MINUS in normal mode: enter menu ---
    if mode == "normal" and not menu.active:
        for key in (PLUS, MINUS):
            if held[key] is not None and (now_t - held[key]) >= HOLD_SECONDS:
                duration = now_t - held[key]
                print(f"Menu: long-press detected key={key} duration={duration:.2f}s")
                print_status()
                held[PLUS] = None
                held[MINUS] = None
                held[ANNOUNCE] = None
                menu.enter()
                discard_events()
                break

    # --- Value-entry inactivity timeout ---
    if mode in ("set_hour", "set_minute", "set_alarm_hour", "set_alarm_minute"):
        if last_interaction is not None and (now_t - last_interaction) >= VALUE_ENTRY_TIMEOUT:
            print(f"Value entry: inactivity timeout in mode '{mode}'")
            mode = "normal"
            last_interaction = None
            play_token("menu.exit")

    # --- Value-entry hold repeat ---
    if value_repeat_key is not None and mode in ("set_hour", "set_minute", "set_alarm_hour", "set_alarm_minute"):
        if now_t >= value_repeat_next:
            value_did_repeat   = True
            value_repeat_next  = now_t + VALUE_REPEAT_INTERVAL
            last_interaction   = now_t
            if value_repeat_key == PLUS:
                if mode in ("set_hour", "set_alarm_hour"):
                    set_hour = (set_hour + 1) % 24
                else:
                    set_minute = (set_minute + 1) % 60
            else:
                if mode in ("set_hour", "set_alarm_hour"):
                    set_hour = (set_hour - 1) % 24
                else:
                    set_minute = (set_minute - 1) % 60
            play_path(BEEP_PATH)

    # --- Menu inactivity timeout ---
    menu.tick()

    # --- Deferred volume save ---
    if volume_dirty_since is not None:
        if (now_t - volume_dirty_since) >= VOLUME_DELAY:
            config["volume_step"] = volume_step
            save_config(config)
            volume_dirty_since = None

    # --- Auto-announce and alarm ---
    if mode == "normal" and not menu.active and not alarm_ringing:
        check_auto_announce()
        check_alarm()

    if alarm_ringing:
        tick_alarm()

    time.sleep(0.02)