import board
import busio
import digitalio
import storage
import sdcardio
import audiobusio
import audiocore
import audiomixer
import json
import time

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

# Amp enable
gain = digitalio.DigitalInOut(board.GP13)
gain.direction = digitalio.Direction.OUTPUT
gain.value = True

# Button on GP6, active low
button = digitalio.DigitalInOut(board.GP6)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# I2S audio
audio = audiobusio.I2SOut(bit_clock=board.GP11, word_select=board.GP12, data=board.GP10)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=2048)
audio.play(mixer)

# Load vocab map
VOICE = "en_US_lessac_medium_standard"
with open(f"/sd/{VOICE}/vocab.json", "r") as f:
    vocab = json.load(f)

def w(key):
    """Look up a vocab filename."""
    return vocab[key]

def get_audio_files(hour_24, minute):
    """Evaluate standard mode rules and return list of WAV filenames."""
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

def play_sequence(hour_24, minute):
    files = get_audio_files(hour_24, minute)
    print(f"{hour_24:02d}:{minute:02d} -> {files}")
    for filename in files:
        path = f"/sd/{VOICE}/audio/{filename}"
        with open(path, "rb") as f:
            wav = audiocore.WaveFile(f)
            mixer.voice[0].play(wav)
            while mixer.voice[0].playing:
                pass

print("Ready. Press button to play.")

TEST_HOUR = 8
TEST_MINUTE = 48

was_pressed = False

while True:
    pressed = not button.value
    if pressed and not was_pressed:
        play_sequence(TEST_HOUR, TEST_MINUTE)
    was_pressed = pressed
    time.sleep(0.05)