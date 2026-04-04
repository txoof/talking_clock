# Talking Clock Audio

A command-line tool for generating multilingual time phrase audio files for the Talking Clock project.

- [Talking Clock Audio](#talking-clock-audio)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Generating a Voice Package](#generating-a-voice-package)
  - [Audio Sample Requirements](#audio-sample-requirements)
  - [Adding a New Language](#adding-a-new-language)
  - [Building a YAML configuration with an LLM](#building-a-yaml-configuration-with-an-llm)
  - [Deploying to the Clock](#deploying-to-the-clock)
  - [CLI Reference](#cli-reference)
  - [Project Structure](#project-structure)
  - [Audio Debug Mode](#audio-debug-mode)
  - [License](#license)
  - [Contributing](#contributing)
  - [Acknowledgments](#acknowledgments)
  - [Support](#support)

This package uses Piper TTS to synthesize spoken time announcements from YAML-defined phrase rules. It produces audio packages ready to deploy to the clock's SD card, along with the compiled rule files the Pico firmware uses to select and sequence audio at runtime.

## Requirements

- Python 3.11 or 3.12 (Python 3.14 not yet supported by piper-tts)
- piper-tts
- huggingface-hub
- pyyaml
- click
- questionary
- pycountry

See `pyproject.toml` for the complete dependency list.

## Installation

Install the talking clock audio (`tca`) command in a local virtual environment.

```bash
git clone https://github.com/txoof/talking-clock.git
cd talking-clock/talking-clock-audio
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Quick Start

The minimal path from a fresh install to deploying audio on the clock's SD card.

This walkthrough uses the english US (`en_US`) "lessac" voice as an example. Substitute your preferred locale and voice as needed.

### 1. Download a voice model

**List Available Models on Hugging Face**

```bash
$ tca list-models --remote | less

Found 152 voices in 45 locales:

ar_JO - Arabic (Jordan):
  ar_JO/kareem/low
  ar_JO/kareem/medium

bg_BG - Bulgarian (Bulgaria):
  bg_BG/dimitar/medium

...
en_GB - English (United Kingdom):
  en_GB/alan/low
  en_GB/alan/medium
  en_GB/alba/medium
  en_GB/aru/medium
  en_GB/cori/high
  en_GB/cori/medium
  en_GB/jenny_dioco/medium
  en_GB/northern_english_male/medium
  en_GB/semaine/medium
  en_GB/southern_english_female/low
  en_GB/vctk/medium

en_US - English (United States):
  en_US/amy/low
  en_US/amy/medium
  en_US/arctic/medium
  en_US/bryce/medium
  en_US/lessac/high
  en_US/lessac/low
  en_US/lessac/medium
  en_US/libritts/high
  en_US/libritts_r/medium
  en_US/sam/medium
...
```

**Download and Cache a Model**

```bash
tca get-model --locale en_US --voice lessac --quality medium
```

The files are cached in `./models`.

### 2. Generate the audio package

This will generate `.wav` files using the selected voice model.

```bash
tca generate --yaml time_phrases_en_US.yaml --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

### 3. Validate the output

This step displays some time phrases in using the defined rules allowing a visual and audio verification that the rules have been applied correctly.

```bash
tca validate --yaml time_phrases_en_US.yaml
```

Review the sample phrases for each mode. Check that the `Examples: OK` line appears for all modes.

### 4. Prepare the SD card

Use an SD card with at least 1GB of storage. Format the SD card as FAT32 and set the volume label to `TALK-CLOCK`. The volume lable is not required, but makes deploying easier.

### 5. Deploy audio to the clock

This will copy the appropriate files to the SD card. Make sure the SD card is mounted and available.

```bash
tca deploy
```

Select `TALK-CLOCK` from the volume list. Select the packages to copy. Insert the SD card into the clock.

## Generating a Voice Package

A voice package is a directory containing all the audio files and compiled rule files that are needed for a voice and a locale. Voice packages support up to four different "modes". The modes, operational, broadcast, standard and casual, are different ways of telling time in the selected language. Operational is typically used by the military and in aviation where ambiguity with time is unacceptable. Broadcast is the mode used often in airports, train stations and on news broadcasts where ambiguity is discouraged. Standard mode is typically used in semi-formal settings such as offices and schools. Casual mode is used on the street, among friends and family where precision is not crucial.

American English Example:

| Time    | Mode        | Phrase                 |
| ------- | ----------- | ---------------------- |
| 8:30 AM | Operational | oh eight thirty        |
| 8:45 PM | Operational | twenty fortyfive       |
| 9:27 AM | Broadcast   | nine twenty seven A.M. |
| 6:15 PM | Broadcast   | six fifteen P.M.       |
| 4:00 AM | Standard    | four o' clock          |
| 4:00 PM | Standard    | four o' clock          |
| 7:12 AM | Casual      | quarter after seven    |
| 9:28 PM | Casual      | half past nine         |

Voice packages are generated using a YAML file that contains all of the relevant words and rules required for building time phrases.

All modes are share a single set of audio files. Per-mode rules are stored separately within a `rules` sub directory. 

Generated packages are written to `./audio/` by default:

```text
en_US_lessac_medium
├── audio
│   ├── interval_half.wav
│   ├── interval_hourly.wav
...
│   └── words_zero.wav
├── generation_info.json
├── rules
│   ├── broadcast_rules.json
│   ├── casual_rules.json
│   ├── operational_rules.json
│   └── standard_rules.json
└── vocab.json
```

### Generate a package

```bash
tca generate --yaml time_phrases_en_US.yaml --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

If either option is omitted, `tca generate` will prompt you to select from available YAML files and downloaded models.

The output directory is derived from the model filename: `audio/<locale>_<voice>_<quality>/`

To write to a different location:

```bash
tca generate --yaml time_phrases_en_US.yaml --model <path> --output-dir ./my_output
```

To overwrite an existing package without confirmation:

```bash
tca generate --yaml time_phrases_en_US.yaml --model <path> --force
```

### Audio processing options

The generator applies two processing steps to every WAV file to improve intelligibility on the small speaker used in the clock.

**High-pass filter** removes low-frequency content that small speakers cannot reproduce cleanly. The default cutoff is 300Hz.

**Soft limiter** prevents clipping on loud peaks. The default threshold is 16000 (out of 32767).

These defaults work well for a standard 4-ohm 3-watt full-range driver with no enclosure. Adjust them if your speaker sounds distorted or muffled.

```bash
# Adjust high-pass filter cutoff
tca generate --yaml <file> --model <path> --highpass-cutoff 500

# Adjust soft limiter threshold
tca generate --yaml <file> --model <path> --speaker-threshold 24000

# Disable high-pass filter
tca generate --yaml <file> --model <path> --highpass-cutoff 0

# Disable soft limiter
tca generate --yaml <file> --model <path> --speaker-threshold 32767

# Disable all processing (raw TTS output)
tca generate --yaml <file> --model <path> --highpass-cutoff 0 --speaker-threshold 32767
```

### Troubleshooting audio quality

**Audio sounds clipped or distorted on the speaker**

Lower the soft limiter threshold. Start at 24000 and work downward until clipping disappears:

```bash
tca generate --yaml <file> --model <path> --speaker-threshold 24000
```

**Audio sounds muffled or boomy**

Raise the high-pass filter cutoff. Try 500Hz for small drivers:

```bash
tca generate --yaml <file> --model <path> --highpass-cutoff 500
```

**Audio sounds thin or tinny**

Lower the high-pass filter cutoff, or disable it entirely if your speaker handles bass well:

```bash
tca generate --yaml <file> --model <path> --highpass-cutoff 150
```

**Audio quality is fine on headphones but poor on the clock speaker**

The speaker in the clock enclosure may have different characteristics than your test speaker. Use the `tca debug` command to generate test audio with multiple processing variants and compare them directly on the hardware. See `tca debug --help` for details.

### Validate a package

After generating, run validate to confirm that the compiled rules produce the expected spoken phrases:

```bash
tca validate --yaml time_phrases_en_US.yaml
```

This compiles the rules, generates sample phrases for a set of representative times, and checks them against the `examples:` block in the YAML. A passing result looks like:

```Text
Mode: casual
========================================================
  Time     Label        Phrase
  ------- ----------- -----------------------------------
  00:00  midnight     midnight
  08:09  08:09        eight oh nine
  ...

  Examples: OK (5 checked)

========================================================
Result: OK
```

Any mismatch between the generated phrase and the expected phrase in the `examples:` block is reported as a warning. Fix the rules in the YAML and re-run until all modes pass.

## Audio Sample Requirements

All WAV files must match the mixer configuration exactly. Files that do not match will fail to play silently or raise a `ValueError` at runtime on the Pico.

The `tca generate` command always produces files in the correct format. This section is only relevant if you are sourcing audio files from another tool or converting existing files.

### Required format

| Property | Value |
| -------- | ----- |
| Format | PCM WAV (uncompressed) |
| Sample rate | 22050 Hz |
| Channels | Mono (1 channel) |
| Bit depth | 16-bit signed |

### Converting files with ffmpeg

Convert a single file:

```bash
ffmpeg -i input.wav -ar 22050 -ac 1 -sample_fmt s16 output.wav
```

Convert all WAV files in the current directory, writing results to a `converted/` subdirectory:

```bash
mkdir -p converted
for f in *.wav; do
    ffmpeg -i "$f" -ar 22050 -ac 1 -sample_fmt s16 "converted/$f"
done
```

### Verifying a file

```bash
ffprobe -v error -show_entries stream=sample_rate,channels,sample_fmt -of compact input.wav
```

Expected output:

```text
sample_rate=22050|channels=1|sample_fmt=s16
```

## Adding a New Language

Adding a new language requires three things: a YAML phrase configuration file, a downloaded Piper TTS voice model for that language and a run of `tca generate`.

### 1. Find a voice model

List available models on Hugging-Face:

```bash
tca list-models --remote | less
```

To find German voices:

```bash
tca list-models --remote | grep de_DE
```

Download the model:

```bash
tca get-model --locale de_DE --voice thorsten --quality medium
```

### 2. Create a phrase configuration

Copy the [template](./time_phrases_template.yaml) as a starting point:

```bash
cp time_phrases_template.yaml time_phrases_de_DE.yaml
```

Edit the file to fill in translations and adapt the casual mode rules to your language's conventions. Place the completed template in the `time_formats` directory.

The template contains comments explaining every section. Pay particular attention to the `casual` mode, which is the most language-specific. In particular, note that some languages (including Dutch and German) express the half hour relative to the upcoming hour rather than the past hour. "Half drie" in Dutch means 2:30, not 3:30.

For complex languages or if you are not a native speaker, use the LLM-assisted workflow described below.

### 3. Validate the configuration

```bash
tca validate --yaml time_phrases_de_DE.yaml
```

Work through any warnings until all modes report `Examples: OK`.

### 4. Generate the audio package

```bash
tca generate --yaml time_phrases_de_DE.yaml --model ./models/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
```

### 5. Deploy to the clock

```bash
tca deploy
```

## Building a YAML configuration with an LLM

To help build the YAML file, the repository includes a system prompt that coaches an LLM through collecting the information needed to produce a valid YAML file.

The prompt is in [`LOCALE_BUILDER_PROMPT.md`](./LOCALE_BUILDER_PROMPT.md). It walks the LLM through:

- vocabulary collection
- time-telling conventions for each mode
- casual mode minute boundaries
- the `examples:` block needed for `tca validate`

The prompt is designed to be set as a **system prompt** rather than pasted as a regular message. See `LOCALE_BUILDER_PROMPT.md` for setup instructions for ChatGPT, Claude, and local LLMs.

After the LLM produces a YAML file, always run:

```bash
tca validate --yaml time_phrases_LOCALE.yaml
```

LLMs occasionally make errors in the `minute_map` or get casual mode conventions wrong for languages with non-obvious conventions. The validate command will catch these before you generate audio.

## Deploying to the Clock

The `tca deploy` command copies generated voice packages to a mounted SD card and manages what is already on the card.

### Prepare the SD card

Format the SD card as FAT32. Set the volume label to `TALK-CLOCK`. The label is not required but makes it easier to identify the card in the volume list. Any SD card with at least 1GB of storage is sufficient.

### Run tca deploy

Insert and mount the SD card, then run:

```bash
tca deploy
```

**Step 1: Select a volume**

The command lists all mounted volumes and asks you to pick one:

```text
? Select SD card volume:
  /Volumes/TALK-CLOCK
  /Volumes/Backup Drive
  /Volumes/CIRCUITPY
```

**Step 2: Review the summary**

After selecting a volume, a summary shows what is available locally and what is already on the card:

```text
Source:  /Users/aaron/talking-clock-audio/audio
Target:  /Volumes/TALK-CLOCK

LOCAL PACKAGES                                   ON SD CARD
--------------------------------------------------------------------------------
en_US_lessac_medium      (lessac, medium, 2026-04-04)   (not present)
en_US_amy_medium         (amy, medium, 2026-04-04)      (amy, medium, 2026-03-12)
nl_NL_pim_medium         (pim, medium, 2026-04-04)      (pim, medium, 2026-04-04)
```

Colour coding:

- Cyan: present locally only, not yet on the card
- Yellow: present both locally and on the card
- Green: present on the card only, not in the local audio directory

**Step 3: Select packages to copy**

A checkbox menu lists all local packages. Use the arrow keys to move and space to select. Press enter to confirm:

```text
? Select packages to copy to SD card:
  [ ] en_US_lessac_medium    (lessac, medium, 2026-04-04)
  [x] en_US_amy_medium       (amy, medium, 2026-04-04)
  [ ] nl_NL_pim_medium       (pim, medium, 2026-04-04)
```

If a selected package already exists on the card you will be asked to confirm before it is overwritten.

**Step 4: Delete packages from the card**

After copying, the command asks whether you want to delete anything from the card:

```text
? Would you like to delete any packages from the SD card?
```

If you answer yes, a checkbox menu lists everything currently on the card. Each selected package requires a separate confirmation before it is deleted:

```text
? Permanently delete 'nl_NL_rdh_medium' from SD card? (y/N)
```

Only directories that are valid voice packages can be deleted through this command.

### Expert mode

If you already know the target path, skip the volume selection prompt:

```bash
tca deploy --target /Volumes/TALK-CLOCK
```

To scan a different local audio directory:

```bash
tca deploy --source-dir ./my_audio --target /Volumes/TALK-CLOCK
```

To skip overwrite confirmation when copying:

```bash
tca deploy --target /Volumes/TALK-CLOCK --force
```

Full expert mode:

```bash
tca deploy --source-dir ./audio --target /Volumes/TALK-CLOCK --force
```

## CLI Reference

All commands support interactive mode (prompts for missing options) and expert mode (all options supplied as flags). Running any command without flags will prompt for required inputs. Every command prints the full expert-mode command at the end of a successful run for easy repetition.

Global flags apply to all commands:

```bash
tca --verbose <command>    # show debug logging
tca --quiet <command>      # suppress all output except errors
tca <command> --help       # show full help for a command
```

### list-models

Lists available voice models. Defaults to showing locally downloaded models.

```bash
tca list-models                              # list local models
tca list-models --remote                     # list all models on Hugging Face
tca list-models --local --model-dir ./models # specify model directory
```

### get-model

Downloads a voice model from Hugging Face and caches it in `./models/`.

```bash
tca get-model                                              # interactive
tca get-model --locale en_US --voice lessac --quality medium
tca get-model --locale nl_NL --voice pim --quality medium
tca get-model --model-dir /path/to/models --locale en_US --voice lessac --quality medium
```

### validate

Compiles the rules from a YAML file, generates sample phrases for ten representative times, and checks them against the `examples:` block. Optionally plays the generated audio sequences if a matching package exists in `./audio/`.

```bash
tca validate                                 # interactive
tca validate --yaml time_phrases_en_US.yaml
```

### generate

Generates a complete voice package from a YAML phrase file and a downloaded voice model. All modes are generated in a single run and share one set of WAV files.

```bash
tca generate                                 # interactive
tca generate --yaml time_phrases_en_US.yaml --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
tca generate --yaml time_phrases_en_US.yaml --model <path> --output-dir ./my_output
tca generate --yaml time_phrases_en_US.yaml --model <path> --force
tca generate --yaml time_phrases_en_US.yaml --model <path> --highpass-cutoff 500
tca generate --yaml time_phrases_en_US.yaml --model <path> --speaker-threshold 24000
tca generate --yaml time_phrases_en_US.yaml --model <path> --highpass-cutoff 0 --speaker-threshold 32767
```

| Flag | Default | Description |
|------|---------|-------------|
| `--yaml` | prompt | Path to locale YAML file |
| `--model` | prompt | Path to `.onnx` voice model |
| `--output-dir` | `audio/<locale>_<voice>_<quality>` | Output directory |
| `--force` | off | Overwrite existing files without confirmation |
| `--highpass-cutoff` | 300 | High-pass filter cutoff in Hz. Set to 0 to disable |
| `--speaker-threshold` | 16000 | Soft limiter threshold (0-32767). Set to 32767 to disable |

### deploy

Copies generated voice packages to a mounted SD card and manages packages already on the card. See the Deploying to the Clock section for a full walkthrough.

```bash
tca deploy                                               # interactive
tca deploy --target /Volumes/TALK-CLOCK
tca deploy --source-dir ./audio --target /Volumes/TALK-CLOCK
tca deploy --source-dir ./audio --target /Volumes/TALK-CLOCK --force
```

| Flag | Default | Description |
|------|---------|-------------|
| `--source-dir` | `./audio` | Local directory to scan for voice packages |
| `--target` | prompt | Path to mounted SD card volume |
| `--force` | off | Skip overwrite confirmation when copying |

### debug

Generates speaker test audio from a debug YAML configuration. Produces one subdirectory per variant, each containing a label file and one WAV per test sentence. All sentences are normalized to a fixed peak before processing so that filter and limiter variants can be compared fairly on the hardware.

```bash
tca debug --model <path>                                 # uses tests/speaker_test.yaml
tca debug --yaml tests/speaker_test.yaml --model <path>
tca debug --yaml tests/speaker_test.yaml --model <path> --output-dir ./audio/debug
tca debug --yaml tests/speaker_test.yaml --model <path> --force
```

| Flag | Default | Description |
|------|---------|-------------|
| `--yaml` | `tests/speaker_test.yaml` | Path to debug configuration YAML |
| `--model` | prompt | Path to `.onnx` voice model |
| `--output-dir` | `./audio/debug` | Output directory for test audio |
| `--force` | off | Overwrite existing files without confirmation |

## Project Structure

```text
talking-clock-audio/
  src/
    talking_clock_audio/
      __init__.py              # package initialisation and logging setup
      cli.py                   # command-line interface (tca commands)
      deploy.py                # SD card deployment logic
      tts_generator.py         # Piper TTS audio generation and speaker processing
      rules_generator.py       # compiles locale YAML into runtime JSON rule files
      phrase_generator.py      # evaluates compiled rules to produce audio sequences
      pico_rules.py            # on-device rule evaluation (also used by validate)
      debug_generator.py       # speaker test audio generation
      voice_manager.py         # Hugging Face voice model listing and download
  tests/
    speaker_test.yaml          # default debug configuration
    test_phrase_generator.py
    test_rules.py
    test_voice_manager.py
    test_voice_scan.py
  time_formats/
    time_phrases_en_GB.yaml    # British English locale configuration
    time_phrases_en_US.yaml    # American English locale configuration
    time_phrases_nl_NL.yaml    # Dutch locale configuration
  time_phrases_template.yaml   # template for adding a new language
  LOCALE_BUILDER_PROMPT.md     # LLM system prompt for building locale YAML files
  pyproject.toml               # package configuration and dependencies
  README.md                    # this file
```

## Audio Debug Mode

The clock has a built-in speaker test mode for comparing audio processing variants directly on the hardware. This is the most reliable way to tune the high-pass filter and soft limiter settings for a specific speaker, since the clock enclosure and amplifier circuit both affect the final sound.

### Generate test audio

The `tca debug` command generates a set of WAV files from a [debug YAML](./tests/speaker_test.yaml) configuration. Each variant produces a label file followed by one WAV per test sentence, all processed with the variant's filter and limiter settings.

```bash
tca debug --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

This uses `tests/speaker_test.yaml` by default and writes output to `./audio/debug/`.

### Copy debug audio to the SD card

Copy the entire `debug/` directory to the root of the SD. The clock expects the debug audio at `/sd/debug/` on the mounted filesystem.

Using the Finder, File Manager, or command line:

```bash
cp -r ./audio/debug /Volumes/TALK-CLOCK/debug
```

Eject and insert the SD card into the clock.

### Enter debug mode

Debug mode is entered by holding the ANNOUNCE button during a cold boot or soft boot from `mpremote`. A reboot can be triggered in two ways.

**Power cycle:** disconnect and reconnect power to the clock while holding ANNOUNCE.

**Using mpremote:** [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) is a command-line tool for interacting with MicroPython and CircuitPython devices over USB. Connect the Pico via USB, then run:

```bash
mpremote connect auto
```

Once connected, press `Ctrl+D` to perform a soft reboot while holding the ANNOUNCE button on the clock.

### Navigating debug mode

In debug mode the clock loads variant directories from `/sd/debug/` in alphabetical order.

| Button   | Action                                         |
| -------- | ---------------------------------------------- |
| ANNOUNCE | play all files in the current variant in order |
| PLUS     | next variant                                   |
| MINUS    | previous variant                               |

Each variant plays its label file first so you can identify which settings you are hearing, followed by the test sentences. Press PLUS or MINUS at any point to interrupt playback and move to another variant.

To exit debug mode, reboot by unplugging or using ctrl+D in `mpremote`. Do not hold down the ANNOUNCE button during reboot.

## License

GPL-3.0-or-later

## Contributing

Contributions welcome! Especially:

- New language configurations
- Voice model recommendations
- Bug fixes and improvements
- Documentation improvements

## Acknowledgments

- [Piper TTS](https://github.com/rhasspy/piper) for high-quality offline text-to-speech
- [Hugging Face](https://huggingface.co/rhasspy/piper-voices) for hosting voice models
- The broader maker community for hardware designs and CircuitPython libraries

## Support

For issues, questions, or contributions, please open an issue on GitHub.
