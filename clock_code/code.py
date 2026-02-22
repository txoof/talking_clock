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
import time
import adafruit_ds3231

# SD card - must be initialized before any other SPI peripheral
try:
    spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
    sdcard = sdcardio.SDCard(spi, board.GP17)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    print("SD card mounted OK")
except Exception as e:
    print("SD card mount failed:", e)
    raise

# I2C RTC
i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
rtc = adafruit_ds3231.DS3231(i2c)

# Amp enable
gain = digitalio.DigitalInOut(board.GP13)
gain.direction = digitalio.Direction.OUTPUT
gain.value = True

# Buttons: GP6=announce, GP7=plus, GP8=minus
keys = keypad.Keys(
    (board.GP6, board.GP7, board.GP8),
    value_when_pressed=False,
    pull=True,
)
ANNOUNCE = 0
PLUS     = 1
MINUS    = 2

# I2S audio
audio = audiobusio.I2SOut(bit_clock=board.GP11, word_select=board.GP12, data=board.GP10)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=2048)
audio.play(mixer)

# --- Configuration ---
CONFIG_PATH = "/sd/configuration.json"
VOLUME_STEPS = 10
VOLUME_SAVE_DELAY = 10.0  # seconds after last change before writing to SD
HOLD_SECONDS = 3.0        # hold duration to enter set mode

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"volume_step": 7}  # default: 70%

def save_config(config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        print("Config saved.")
    except Exception as e:
        print("Config save failed:", e)

config = load_config()
volume_step = config.get("volume_step", 7)
mixer.voice[0].level = volume_step / VOLUME_STEPS
print(f"Volume: {volume_step}/{VOLUME_STEPS}")

volume_dirty_since = None  # timestamp of last volume change, None = clean

# --- Voice / vocab ---
VOICE = "en_US_lessac_medium_standard"
with open(f"/sd/{VOICE}/vocab.json", "r") as f:
    vocab = json.load(f)

BOOP_PATH = "/sd/audio_assets/volume_boop.wav"

def w(key):
    return vocab[key]

def get_audio_files(hour_24, minute):
    h12 = ((hour_24 + 11) % 12) + 1
    if hour_24 == 0 and minute == 0:
        return [w("words.midnight")]
    if hour_24 == 12 and minute == 0:
        return [w("words.noon")]
    if minute == 0:
        return [w(f"number_words.{h12}"), w("words.oclock")]
    if 0 < minute < 10:
        return [w(f"number_words.{h12}"), w("words.oh"), w(f"number_words.{minute}")]
    return [w(f"number_words.{h12}"), w(f"number_words.{minute}")]

def discard_events():
    while keys.events.get() is not None:
        pass

def play_file(path):
    with open(path, "rb") as f:
        wav = audiocore.WaveFile(f)
        mixer.voice[0].play(wav)
        while mixer.voice[0].playing:
            pass

def play_sequence(hour_24, minute):
    files = get_audio_files(hour_24, minute)
    print(f"{hour_24:02d}:{minute:02d} -> {files}")
    handles = []
    wavs = []
    try:
        for filename in files:
            path = f"/sd/{VOICE}/audio/{filename}"
            fh = open(path, "rb")
            handles.append(fh)
            wavs.append(audiocore.WaveFile(fh))
        for wav in wavs:
            mixer.voice[0].play(wav)
            while mixer.voice[0].playing:
                discard_events()
    finally:
        for fh in handles:
            fh.close()
        discard_events()

def play_boop():
    try:
        play_file(BOOP_PATH)
    except Exception as e:
        print("Boop failed:", e)

# --- State ---
mode = "normal"  # "normal", "set_hour", "set_minute"
set_hour = 0
set_minute = 0

# Hold detection for plus/minus
held = {PLUS: None, MINUS: None}

def print_time(label, h, m):
    print(f"{label}: {h:02d}:{m:02d}")

def now():
    t = rtc.datetime
    return t.tm_hour, t.tm_min

print("Ready.")
h, m = now()
print_time("RTC time", h, m)

while True:
    now_t = time.monotonic()
    event = keys.events.get()

    if event:
        key = event.key_number

        # Track press/release times for plus/minus hold detection
        if key in (PLUS, MINUS):
            if event.pressed:
                held[key] = now_t
            elif event.released:
                # Short release = volume change
                if held[key] is not None and (now_t - held[key]) < HOLD_SECONDS:
                    if mode == "normal":
                        if key == PLUS:
                            volume_step = min(VOLUME_STEPS, volume_step + 1)
                        else:
                            volume_step = max(0, volume_step - 1)
                        mixer.voice[0].level = volume_step / VOLUME_STEPS
                        print(f"Volume: {volume_step}/{VOLUME_STEPS}")
                        play_boop()
                        volume_dirty_since = now_t
                held[key] = None

        if mode == "normal":
            if event.pressed and key == ANNOUNCE:
                h, m = now()
                play_sequence(h, m)

        elif mode == "set_hour":
            if event.pressed:
                if key == PLUS:
                    set_hour = (set_hour + 1) % 24
                    print_time("Set hour", set_hour, set_minute)
                elif key == MINUS:
                    set_hour = (set_hour - 1) % 24
                    print_time("Set hour", set_hour, set_minute)
                elif key == ANNOUNCE:
                    mode = "set_minute"
                    print_time("Set minute", set_hour, set_minute)

        elif mode == "set_minute":
            if event.pressed:
                if key == PLUS:
                    set_minute = (set_minute + 1) % 60
                    print_time("Set minute", set_hour, set_minute)
                elif key == MINUS:
                    set_minute = (set_minute - 1) % 60
                    print_time("Set minute", set_hour, set_minute)
                elif key == ANNOUNCE:
                    t = rtc.datetime
                    rtc.datetime = time.struct_time((
                        t.tm_year, t.tm_mon, t.tm_mday,
                        set_hour, set_minute, 0,
                        t.tm_wday, t.tm_yday, t.tm_isdst
                    ))
                    mode = "normal"
                    print_time("Time saved", set_hour, set_minute)

    # Hold detection: 3s hold on plus or minus enters set mode
    if mode == "normal":
        for key in (PLUS, MINUS):
            if held[key] is not None and (now_t - held[key]) >= HOLD_SECONDS:
                held[key] = None
                h, m = now()
                set_hour = h
                set_minute = m
                mode = "set_hour"
                print_time("Set hour", set_hour, set_minute)
                break

    # Deferred volume save
    if volume_dirty_since is not None:
        if (now_t - volume_dirty_since) >= VOLUME_SAVE_DELAY:
            config["volume_step"] = volume_step
            save_config(config)
            volume_dirty_since = None

    time.sleep(0.02)