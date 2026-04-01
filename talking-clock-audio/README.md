# Talking Clock Audio

Generate multilingual time phrase audio files for accessible talking clock applications.

This package provides tools for creating audio files from text phrases using Piper TTS voices in multiple languages. This is designed specifically for creating accessible talking clock applications with clear, natural-sounding time announcements that match the common style and format for your language.

## Features

- **Multiple languages**: English (US), Dutch, with easy framework for adding more
- **Multiple speaking styles**: Operational, broadcast, standard, and casual modes
- **Flexible phrase system**: YAML-based configuration for defining time phrases
- **Voice model management**: Download and manage Piper TTS voice models
- **Optimized for hardware**: Small speaker compatibility with built-in soft limiter
- **Pico-ready output**: Generates simple JSON config for Raspberry Pi Pico runtime

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/talking-clock-audio.git
cd talking-clock-audio

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Generate Your First Audio Package

**Interactive mode (recommended for beginners):**

```bash
# Just run the command and follow the prompts
tca generate
```

The tool will interactively ask you to:
1. Select a configuration file (e.g., time_phrases_en_US.yaml)
2. Choose a speaking mode (operational/broadcast/standard/casual)
3. Select a voice model (downloads automatically if needed)

**Expert mode (all options specified):**

```bash
# List available voice models
tca list-models --remote

# Download a voice model
tca get-model --locale en_US --voice lessac --quality medium

# Generate audio package
tca generate \
  --yaml time_formats/time_phrases_en_US.yaml \
  --mode casual \
  --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

Output will be created in: `audio/en_US_lessac_medium_casual/`

### Adding New Languages

See [ADDING_LANGUAGES.md](ADDING_LANGUAGES.md) for comprehensive guide on creating new language configurations.

Quick summary:

1. Create YAML file in `time_formats/time_phrases_{locale}.yaml`
2. Define vocabulary (words and number_words)
3. Define computed fields for hour/minute transformations
4. Define rules for each speaking mode
5. Validate with `tca validate`
6. Generate audio with `tca generate`

## CLI Commands

All commands support both expert mode (all flags specified) and interactive mode (prompts for missing options).

### list-models

List available voice models from Hugging Face or locally downloaded models.

```bash
# List remote models with language names
tca list-models --remote

# List locally downloaded models
tca list-models --local

# List models in custom directory
tca list-models --local --model-dir /path/to/models
```

### get-model

Download a voice model from Hugging Face.

**Interactive mode:**
```bash
tca get-model
# Prompts for: locale, voice name, quality
```

**Expert mode:**
```bash
tca get-model --locale en_US --voice lessac --quality medium
tca get-model --locale nl_NL --voice rdh --quality medium
tca get-model --locale de_DE --voice thorsten --quality high
```

Models download to `./models/` by default. Use `--model-dir` to change location.

### validate

Validate a time phrase configuration and preview sample outputs.

**Interactive mode:**
```bash
tca validate
# Prompts for: YAML file, mode
```

**Expert mode:**
```bash
tca validate --yaml time_formats/time_phrases_en_US.yaml --mode casual
tca validate --yaml time_formats/time_phrases_nl_NL.yaml --mode standard
```

Shows:
- Configuration locale and available modes
- Number of unique audio files needed
- Sample time phrases (7 examples by default)

Use `--samples N` to show more or fewer examples.

### generate

Generate complete audio package with TTS-generated WAV files.

**Interactive mode:**
```bash
tca generate
# Prompts for: YAML file, mode, voice model
# Shows final command at end for easy repetition
```

**Expert mode:**
```bash
tca generate \
  --yaml time_formats/time_phrases_en_US.yaml \
  --mode casual \
  --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

**Mixed mode (prompts only for missing options):**
```bash
# Specify YAML, get prompted for mode and model
tca generate --yaml time_formats/time_phrases_en_US.yaml

# Specify YAML and mode, get prompted for model
tca generate --yaml time_formats/time_phrases_en_US.yaml --mode casual
```

**Additional options:**

```bash
# Custom output directory
tca generate --yaml <file> --mode casual --model <path> \
  --output-dir custom/output/path

# Force overwrite without confirmation
tca generate --yaml <file> --mode casual --model <path> --force

# Adjust speaker compatibility (see Small Speaker Compatibility below)
tca generate --yaml <file> --mode casual --model <path> \
  --speaker-threshold 24000

# Adjust high-pass filter cutoff (removes low frequencies)
tca generate --yaml <file> --mode casual --model <path> \
  --highpass-cutoff 500

# Disable soft limiter for high-quality speakers
tca generate --yaml <file> --mode casual --model <path> \
  --speaker-threshold 32767

# Disable high-pass filter
tca generate --yaml <file> --mode casual --model <path> \
  --highpass-cutoff 0

# Disable all processing (raw TTS output)
tca generate --yaml <file> --mode casual --model <path> \
  --speaker-threshold 32767 --highpass-cutoff 0
```

## Speaking Modes

All languages support up to four standardized speaking modes:

| Mode | Description | Example (English) |
|------|-------------|-------------------|
| **operational** | Military/radio precision | "thirteen hundred hours" |
| **broadcast** | News/announcements | "one thirty p.m." |
| **standard** | Professional/office | "one thirty" |
| **casual** | Conversational | "half past one" |

Not all languages need all modes. Define only the modes that make sense culturally.

## Output Structure

Generated packages follow this structure:

```
audio/
  en_US_lessac_medium_casual/
    vocab.json               # Vocabulary mapping (vocab keys to filenames)
    audio/                   # Audio files directory
      word_midnight.wav
      word_past.wav
      word_half.wav
      number_zero.wav
      number_one.wav
      ... (70-80 files typically)
```

**vocab.json format:**

```json
{
  "words.midnight": "word_midnight.wav",
  "words.past": "word_past.wav",
  "words.half": "word_half.wav",
  "number_words.0": "number_zero.wav",
  "number_words.11": "number_eleven.wav"
}
```

## Supported Languages

Currently included:

- **English (US)** - `en_US` - All four modes
- **Dutch** - `nl_NL` - All four modes

Additional languages can be added by creating YAML configuration files. See ADDING_LANGUAGES.md for details.

## Command Reference

```bash
# List available voice models
tca list-models --remote              # From Hugging Face
tca list-models --local               # Locally downloaded

# Download voice model
tca get-model --locale <locale> --voice <name> --quality <level>
tca get-model                         # Interactive mode

# Validate configuration
tca validate --yaml <file> --mode <mode>
tca validate                          # Interactive mode

# Generate audio package
tca generate --yaml <file> --mode <mode> --model <path>
tca generate                          # Interactive mode

# Global options
tca --verbose <command>               # Show debug logging
tca --quiet <command>                 # Suppress all but errors
```

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```
talking-clock-audio/
  src/
    talking_clock_audio/
      __init__.py              # Package initialization & logging
      voice_manager.py         # Hugging Face voice model management
      phrase_generator.py      # YAML parsing & phrase generation
      tts_generator.py         # Piper TTS audio generation with speaker processing
      cli.py                   # Command-line interface
  tests/
    test_voice_manager.py      # Voice management tests
    test_phrase_generator.py   # Phrase generation tests
  time_formats/
    time_phrases_en_US.yaml    # English configuration
    time_phrases_nl_NL.yaml    # Dutch configuration
  pyproject.toml               # Package configuration
  README.md                    # This file
  ADDING_LANGUAGES.md          # Language creation guide
```

## Requirements

- Python 3.11 or 3.12 (Python 3.14 not yet supported by piper-tts)
- piper-tts
- huggingface-hub
- pyyaml
- click
- questionary
- pycountry

See `pyproject.toml` for complete dependency list.

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
