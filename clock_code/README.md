# Talking Clock Firmware

This directory contains the CircuitPython firmware for the Talking Clock and all files that need to be deployed to the Pico and SD card.

## Requirements

### CircuitPython

The clock requires CircuitPython 10.x. The firmware was developed and tested against CircuitPython 10.1.4 on the Raspberry Pi Pico (RP2040).

To check the version currently installed on your Pico, connect it via USB and read `boot_out.txt` from the CIRCUITPY drive, or connect with mpremote and run:

```python
import sys
print(sys.version)
```

To install or update CircuitPython, download the UF2 file for the Raspberry Pi Pico from [circuitpython.org](https://circuitpython.org/board/raspberry_pi_pico/) and follow the instructions there.

It is best to prepare the Pico with CircuitPython prior to installing it in the enclosure!

### Libraries

The following Adafruit libraries are required:

```text
adafruit_ds3231==2.4.26
adafruit_bus_device==5.2.15
adafruit_register==1.11.1
```

Pre-compiled `.mpy` versions are included in `./lib/` and should be copied to the `lib/` directory on the CIRCUITPY drive. See the Installation section below.

## File Layout

Files are split between two destinations: the CIRCUITPY drive (the Pico itself) and the SD card.

### What goes on the Pico (CIRCUITPY)

Copy these files and directories to the root of the CIRCUITPY drive:

```text
code.py
menu.py
menu.json
debug_mode.py
pico_rules.py
voices.py
lib/
  adafruit_bus_device/
  adafruit_ds3231.mpy
  adafruit_register/
```

Do not copy `README.md`, `requirements.txt`, `sd_card/`, `libArchive/`, `stubArchive/`, or `__pycache__/` to the Pico.

### What goes on the SD card

The SD card must be formatted as FAT32 with the volume label `TALK-CLOCK`. Copy the contents of `./sd_card/` to the root of the SD card:

```text
audio_assets/
  volume_boop.wav          # played on volume change confirmation
  beep.wav                 # played during button hold-repeat in time setting
  alarms/                  # alarm tone WAV files
    accepted-sweet.wav
    adventure-harp.wav
    bell-motif.wav
    sine-aww.wav
    sine-cellular.wav
    welcome-home-synth.wav
    xd-mewtwo.wav
    xmas-miracle.wav
```

Voice packages are  included in the repository. They can be added to the SD card using `tca deploy`. See [Adding Voice Models](#adding-voice-models) below.

## Installation

### 1. Install CircuitPython

Download the UF2 file for the Raspberry Pi Pico from [circuitpython.org](https://circuitpython.org/board/raspberry_pi_pico/). Hold the BOOTSEL button on the Pico while connecting it via USB. It will mount as a drive called RPI-RP2. Copy the UF2 file to that drive. The Pico will reboot and mount as CIRCUITPY.

### 2. Install libraries

The required libraries are included in `./lib/`. Copy the entire `lib/` directory to the root of the CIRCUITPY drive:

```bash
cp -r ./lib /Volumes/CIRCUITPY/lib
```

Alternatively, install them using [circup](https://github.com/adafruit/circup), Adafruit's CircuitPython library manager:

```bash
pip install circup
circup install adafruit_ds3231 adafruit_bus_device adafruit_register
```

### 3. Copy firmware files

Copy the following files to the root of the CIRCUITPY drive:

```bash
cp code.py menu.py menu.json debug_mode.py pico_rules.py voices.py /Volumes/CIRCUITPY/
```

The Pico will restart automatically when `code.py` is copied or updated.

### 4. Prepare the SD card

Format the SD card as FAT32 and set the volume label to `TALK-CLOCK`. Copy the audio assets to the SD card:

```bash
cp -r ./sd_card/audio_assets /Volumes/TALK-CLOCK/audio_assets
```

Insert the SD card into the clock.

### Adding voice models

The clock requires at least one voice package on the SD card to announce the time. Voice packages are generated from Piper TTS voice models using the `tca` command-line tool included in the `talking-clock-audio/` directory of this repository.

See the [talking-clock-audio README](../talking-clock-audio/README.md) for the full workflow covering downloading voice models, generating audio packages, and deploying them to the SD card.

A minimal setup requires one voice package. The default voice expected by the firmware is `en_US_lessac_medium`. 

## Configuration

The firmware reads configuration from `/sd/config.json` on the SD card. This file is created automatically on first boot with default values if it does not exist. It is updated automatically when settings are changed through the menu.

### config.json reference

| Key | Default | Description |
| --- | ------- | ----------- |
| `volume_step` | `7` | Volume level from 0 (silent) to 10 (maximum) |
| `voice` | `"en_US_lessac_medium"` | Name of the active voice package directory on the SD card |
| `mode` | `"standard"` | Time announcement mode: `operational`, `broadcast`, `standard`, or `casual` |
| `alarm_enabled` | `false` | Whether the alarm is active |
| `alarm_hour` | `7` | Alarm hour in 24-hour format |
| `alarm_minute` | `0` | Alarm minute |
| `alarm_tone` | `"/sd/audio_assets/volume_boop.wav"` | Path to the alarm tone WAV file |
| `announce_interval` | `"off"` | Auto-announce interval: `"off"`, `"hourly"`, `"half"`, or `"quarter"` |

## Using the Clock

### Button interface

The clock has three buttons: ANNOUNCE, PLUS, and MINUS.

| Button                    | Normal mode               | In a menu         |
| ------------------------- | ------------------------- | ----------------- |
| ANNOUNCE                  | Announce the current time | Confirm selection |
| PLUS (short)              | Volume up                 | Scroll forward    |
| MINUS (short)             | Volume down               | Scroll back       |
| PLUS or MINUS (hold 1.5s) | Open settings menu        | Exit menu         |

Volume changes are confirmed with a short beep and saved automatically after 5.5 seconds of inactivity.

### Menu navigation

Open the menu by holding PLUS or MINUS for 1.5 seconds. The clock announces the name of each menu item as you scroll. Press ANNOUNCE to confirm a selection. Any long press exits the menu.

The menu contains the following items in order:

| Item                  | Description                                                 |
| --------------------- | ----------------------------------------------------------- |
| Set time              | Set the current hour and minute on the RTC                  |
| Set alarm             | Set the alarm hour and minute                               |
| Enable alarm          | Toggle the alarm on or off                                  |
| Alarm tone            | Cycle through available alarm tones                         |
| Announcement interval | Set auto-announce to off, hourly, half-hourly, or quarterly |
| Time format           | Cycle through available announcement modes                  |
| Voice                 | Cycle through available voice packages                      |

The menu closes automatically after 30 seconds of inactivity.

### Setting the time

Open the menu and select "Set time". The clock announces the current hour. Use PLUS and MINUS to adjust, holding for faster scrolling. Press ANNOUNCE to confirm the hour and move to minutes. Press ANNOUNCE again to save and return to normal mode. Time entry times out after 30 seconds of inactivity.

### Debug output

The firmware prints status and diagnostic information to the serial console. Connect via USB and open a serial terminal (115200 baud) or use mpremote to see output:

```bash
mpremote connect auto
```

Useful output includes the current version, loaded voice and mode, RTC time at boot, rule loading results, and any errors encountered during audio playback or SD card access.

## Troubleshooting

**Clock does not boot or CIRCUITPY does not appear**

Check that CircuitPython is installed. Hold BOOTSEL while connecting USB to enter bootloader mode, then reinstall the UF2.

**"SD card mounted" does not appear in serial output**

The SD card is not being detected. Check that the card is formatted as FAT32, fully inserted, and that the SPI wiring is correct. See the electronics README for pin assignments.

**No audio plays**

Check that at least one voice package exists on the SD card and that the `voice` key in `config.json` matches the directory name exactly. Check that the MAX98357A SD pin (GP9) is wired correctly -- see the electronics README for the known hardware gotcha regarding this pin.

**Time is wrong after a power cycle**

The RTC battery may be missing or flat. The DS3231 module requires a CR2032 battery to maintain time when the clock is unpowered. Set the time through the menu after replacing the battery.

**Audio is distorted, buzzes or is clipped**

Regenerate the voice package with adjusted processing settings. See the [talking-clock-audio README](../talking-clock-audio/README.md) for tuning the high-pass filter and soft limiter.
