# talking_clock

Accessible clock that announces the time

# Talking Clock - To Do

## Bugs

- [ ] Long-press of the announcement button does not appear to exit the menu
- [ ] Long-press of any button does not appear to exit the menu

## Firmware / Features

- [ ] Need to make sure time announcement works as expected
- [ ] Need to build out alarm
- [x] Print menu levels to serial terminal for debugging
- [ ] Implement new rules on clock to use updated voice model vocabulary and rules

## UX / Audio

- [ ] When setting the alarm, AM and PM (or equivalent) must be used in all cases
- [x] When entering settings mode, it appears to advance two menu places
- [ ] Rename menu items: replace "Alarm" with "Toggle Alarm" and "Set Alarm" with "Set Alarm Time"
- [ ] When toggling alarm, device should announce "Alarm is on" or "Alarm is off"
- [ ] Need sound effects for alarm
- [ ] Nederlanse stem is heel langzam "...elf....over.....negen"

## Audio Package

- [ ] Add a vocabulary item for the name of the current voice
- [x] Build out better rules for operational, broadcast, etc.
- [x] Build test cases for rules
- [x] Update tca to generate one directory per voice model with rule files and all samples

## Localization

- [x] Verify Dutch time logic produces natural phrasing (e.g. 8:10 should be "acht tien" not "tien over acht")

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

| Asset                                                        | Attribution                                                                        |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| [volume_boop.wav](./clock_code/audio_assets/volume_boop.wav) | [546974__finix473__ui_click](https://freesound.org/people/finix473/sounds/546974/) |
|                                                              |                                                                                    |
