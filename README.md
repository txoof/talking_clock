# talking_clock

Accessible clock that announces the time

# Talking Clock - To Do

## Bugs

- [x] Long-press of the announcement button does not appear to exit the menu
- [x] Long-press of any button does not appear to exit the menu

## Firmware / Features

- [x] Need to make sure time announcement works as expected
- [x] Need to build out alarm
- [x] Print menu levels to serial terminal for debugging
- [x] Implement new rules on clock to use updated voice model vocabulary and rules

## UX / Audio

- [x] When setting the alarm, AM and PM (or equivalent) must be used in all cases
- [x] When entering settings mode, it appears to advance two menu places
- [x] Rename menu items: replace "Alarm" with "Toggle Alarm" and "Set Alarm" with "Set Alarm Time"
- [x] When toggling alarm, device should announce "Alarm is on" or "Alarm is off"
- [x] Need sound effects for alarm
- [ ] Nederlandse stem is erg traag "...elf....over.....negen"
- [ ] Add menu item to wipe config

## Audio Package

- [x] Add a vocabulary item for the name of the current voice
- [x] Build out better rules for operational, broadcast, etc.
- [x] Build test cases for rules
- [x] Update tca to generate one directory per voice model with rule files and all samples

## Localization

- [x] Verify Dutch time logic produces natural phrasing (e.g. 8:10 should be "acht tien" not "tien over acht")

## Deployment

- [ ] Script to set up SD Card
- [ ] Script to deploy voices and default configuration to SD card
  - [ ] Interactive option to set voice, etc. while deploying
- [ ] 

## Audio sample requirements

All WAV files must match the mixer configuration exactly. Files that do not match
will fail to play silently or raise a `ValueError` at runtime on the Pico.

The constraints come from the `audiomixer.Mixer` initialization in `code.py`:
```python
mixer = audiomixer.Mixer(
    voice_count=1,
    sample_rate=22050,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=2048
)
```

If you change any of these values, all audio files on the SD card must be
re-converted to match.

### Required format

| Property    | Value                  |
| ----------- | ---------------------- |
| Format      | PCM WAV (uncompressed) |
| Sample rate | 22050 Hz               |
| Channels    | Mono (1 channel)       |
| Bit depth   | 16-bit signed          |

### Converting files with ffmpeg

Convert a single file:
```bash
ffmpeg -i input.wav -ar 22050 -ac 1 -sample_fmt s16 output.wav
```

Convert all WAV files in the current directory, writing results to a
`converted/` subdirectory:
```bash
mkdir -p converted
for f in *.wav; do
    ffmpeg -i "$f" -ar 22050 -ac 1 -sample_fmt s16 "converted/$f"
done
```

### Verifying a file before copying to the SD card

```bash
ffprobe -v error -show_entries stream=sample_rate,channels,sample_fmt \
    -of compact input.wav
```

Expected output:
```
sample_rate=22050|channels=1|sample_fmt=s16
```

## Attributions

### Audio Files

| Asset                                                                                            | Attribution                                                                        |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| [volume_boop.wav](./clock_code/sd_card/audio_assets/volume_boop.wav)                             | [546974__finix473__ui_click](https://freesound.org/people/finix473/sounds/546974/) |
| [alarms/accepted-sweet.wav](./clock_code/sd_card/audio_assets/alarms/accepted-sweet.wav)         | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/adventure-harp.wav](./clock_code/sd_card/audio_assets/alarms/adventure-harp.wav)         | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/bell-motif.wav](./clock_code/sd_card/audio_assets/alarms/bell-motif.wav)                 | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/sine-aww.wav](./clock_code/sd_card/audio_assets/alarms/sine-aww.wav)                     | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/sine-cellular.wav](./clock_code/sd_card/audio_assets/alarms/sine-cellular.wav)           | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/welcome-home-synth.wav](./clock_code/sd_card/audio_assets/alarms/welcome-home-synth.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/xd-mewtwo.wav](./clock_code/sd_card/audio_assets/alarms/xd-mewtwo.wav)                   | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms/xmas-miracle.wav](./clock_code/sd_card/audio_assets/alarms/xmas-miracle.wav)             | [akelley6](https://freesound.org/people/akelley6/packs/44231/)                     |
| [alarms](./clock_code/sd_card/audio_assets/alarms/digital-alarm.wav)                             | [Tempouser](https://freesound.org/people/Tempouser/)                               |
| [beep.wav](./clock_code/sd_card/audio_assets/beep.wav)                                           | [thisusernameis](https://freesound.org/people/thisusernameis/)                     |
|                                                                                                  |                                                                                    |

