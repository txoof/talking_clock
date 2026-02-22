# talking_clock

Accessible clock that announces the time

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
