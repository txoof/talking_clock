# Talking Clock

Accessible clock that announces the time on demand by a button push, or periodically.

This clock is designed to be built out of market components, and tell the time in any language for which there is a Piper TTS model. 

# Talking Clock - To Do

## Bugs

- [x] Long-press of the announcement button does not appear to exit the menu
- [x] Long-press of any button does not appear to exit the menu

## Firmware / Features

- [x] Need to make sure time announcement works as expected
- [x] Need to build out alarm
- [x] Print menu levels to serial terminal for debugging
- [x] Implement new rules on clock to use updated voice model vocabulary and rules

## Audio Quality

Adjust audio to default to one of the following:
- 1000Hz All
- 700Hz, 2400

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
- [ ] update tca to generate all models
  - [ ] update config yaml to specify favored voice model

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

## Bill of Materials

### Electronics

| Part                         | Specifications               | Notes                                               | Link                                                                                                                            |
| ---------------------------- | ---------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Raspbery Pi Pico             |                              | Pico or Pico W                                      |                                                                                                                                 |
| SPI SD Card Reader           | 3.3V-5V Level Shifted        |                                                     | [TinyTronics 000375](https://www.tinytronics.nl/en/data-storage/modules/microsd-card-adapter-module-3.3v-5v-with-level-shifter) |
| I2C DS3231 RTC Module        |                              | Requires Battery                                    | [TinyTronics  005849](https://www.tinytronics.nl/en/sensors/time/keyestudio-ds3231-rtc-module-i2c)                              |
| I2C MAX98357A Amp            | 3W                           | Clones Available                                    | [Adafruit 3006](https://www.adafruit.com/product/3006)                                                                          |
| Mono-Speaker                 | 4 ohm 5 Watt                 | Enclosed speaker has superior sound                 | [Kiwi Electronics](https://www.kiwi-electronics.com/en/mono-enclosed-speaker-4-ohm-5w-20413)                                    |
| Arcade Button                | 30 mm                        |                                                     | [Kiwi Electronics](https://www.kiwi-electronics.com/en/30mm-arcade-button-black-3860?search=arcade%20button)                    |
| Momentary Push Button Switch | Panel Mount - LxWxH 37x14x14 | 2x Required -  TRU COMPONENTS TC-DT310WS or similar | [Conrad.com](https://www.conrad.com/en/p/tru-components-tc-dt310ws-tc-dt310ws-pushbutton-momentary-1-pc-s-1589423.html)         |


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
|                                                                                                  |                                                                                    |
