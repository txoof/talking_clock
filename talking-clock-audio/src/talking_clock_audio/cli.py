# src/talking_clock_audio/cli.py

"""Command-line interface for talking-clock-audio."""

import logging
import click
import questionary
from pathlib import Path

from .tts_generator import (
    generate_audio_package_with_tts,
    DEFAULT_SPEAKER_THRESHOLD,
    DEFAULT_HIGHPASS_CUTOFF,
)
from .rules_generator import load_yaml, write_locale_package
from .voice_manager import get_available_voices


def find_yaml_files(search_dir='.'):
    """Find all time phrase YAML files in directory."""
    search_path = Path(search_dir)
    yaml_files = []

    for pattern in ['time_phrases_*.yaml', 'time_formats/time_phrases_*.yaml', '*/time_phrases_*.yaml']:
        yaml_files.extend(search_path.glob(pattern))

    return sorted(set(yaml_files))


def find_model_files(model_dir='./models'):
    """Find all .onnx model files in directory."""
    model_path = Path(model_dir)
    if not model_path.exists():
        return []

    return [f for f in model_path.rglob('*.onnx')
            if not f.name.endswith('.onnx.json')]


def find_audio_dirs(locale, base_dir='./audio'):
    """Find all generated audio directories for a given locale."""
    base = Path(base_dir)
    if not base.exists():
        return []
    return sorted(d for d in base.iterdir()
                  if d.is_dir() and d.name.startswith(locale + '_'))


def play_wav_sequence(audio_dir, filenames):
    """Play a list of WAV filenames from audio_dir in sequence.

    Args:
        audio_dir: Path to the audio/ subdirectory containing WAV files.
        filenames: Ordered list of WAV filenames to play.
    """
    import sounddevice as sd
    import soundfile as sf

    audio_dir = Path(audio_dir)
    for filename in filenames:
        path = audio_dir / filename
        if not path.exists():
            click.echo(f"  [missing: {filename}]")
            continue
        data, samplerate = sf.read(str(path), dtype='int16')
        sd.play(data, samplerate)
        sd.wait()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except errors')
def cli(verbose, quiet):
    """Generate multilingual time phrase audio files.

    \b
    Common commands:
      tca list-models --remote              List available voice models
      tca get-model --locale en_US --voice lessac --quality medium
      tca validate --yaml <file>
      tca generate --yaml <file> --model <path>
      tca debug --yaml speaker_test.yaml --model <path>

    \b
    Interactive mode (prompts for missing options):
      tca generate
      tca validate
      tca get-model
      tca debug

    \b
    For detailed help:
      tca <command> --help
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)


@cli.command('list-models')
@click.option('--local', 'source', flag_value='local', default=True,
              help='List locally downloaded models (default)')
@click.option('--remote', 'source', flag_value='remote',
              help='List available models from Hugging Face')
@click.option('--model-dir', default='./models',
              help='Directory containing local models (default: ./models)')
def list_models(source, model_dir):
    """List available voice models."""
    if source == 'remote':
        import pycountry

        def get_locale_name(locale_code):
            """Convert locale code to readable name."""
            try:
                parts = locale_code.split('_')
                if len(parts) == 2:
                    lang_code, country_code = parts
                    language = pycountry.languages.get(alpha_2=lang_code)
                    country = pycountry.countries.get(alpha_2=country_code)
                    if language and country:
                        return f"{language.name} ({country.name})"
                return locale_code
            except:
                return locale_code

        click.echo("Fetching available models from Hugging Face...")
        voices = get_available_voices()

        by_locale = {}
        for v in voices:
            if v.locale not in by_locale:
                by_locale[v.locale] = []
            by_locale[v.locale].append(v)

        click.echo(f"\nFound {len(voices)} voices in {len(by_locale)} locales:\n")

        for locale in sorted(by_locale.keys()):
            locale_name = get_locale_name(locale)
            click.echo(f"{locale} - {locale_name}:")
            for v in sorted(by_locale[locale], key=lambda x: (x.voice_name, x.quality)):
                path = f"  {v.locale}/{v.voice_name}/{v.quality}"
                click.echo(path)
            click.echo()

    else:
        model_path = Path(model_dir)
        if not model_path.exists():
            click.echo(f"Model directory not found: {model_dir}")
            return

        onnx_files = find_model_files(model_dir)

        if not onnx_files:
            click.echo(f"No models found in {model_dir}")
            click.echo("\nTo download models:")
            click.echo("  tca get-model --locale en_US --voice lessac --quality medium")
            return

        click.echo(f"Found {len(onnx_files)} local models in {model_dir}:\n")

        for onnx_file in sorted(onnx_files):
            click.echo(f"  {onnx_file}")


@cli.command('get-model')
@click.option('--locale', help='Locale code (e.g., en_US, nl_NL)')
@click.option('--voice', help='Voice name (e.g., lessac, thorsten)')
@click.option('--quality', help='Quality level (low, medium, high)')
@click.option('--model-dir', default='./models',
              help='Directory to download to (default: ./models)')
def get_model(locale, voice, quality, model_dir):
    """Download a voice model from Hugging Face.

    \b
    Interactive mode (prompts for missing options):
      tca get-model

    \b
    Expert mode (all options specified):
      tca get-model --locale en_US --voice lessac --quality medium
    """
    from huggingface_hub import hf_hub_download

    try:
        if not locale or not voice or not quality:
            click.echo("Fetching available models...")
            voices = get_available_voices()

            if not locale:
                locales = sorted(set(v.locale for v in voices))
                locale = questionary.select(
                    "Select locale:",
                    choices=locales
                ).ask()

                if not locale:
                    click.echo("Cancelled.")
                    return

            locale_voices = [v for v in voices if v.locale == locale]

            if not voice:
                voice_names = sorted(set(v.voice_name for v in locale_voices))
                voice = questionary.select(
                    "Select voice:",
                    choices=voice_names
                ).ask()

                if not voice:
                    click.echo("Cancelled.")
                    return

            voice_options = [v for v in locale_voices if v.voice_name == voice]

            if not quality:
                qualities = sorted(set(v.quality for v in voice_options))
                quality = questionary.select(
                    "Select quality:",
                    choices=qualities
                ).ask()

                if not quality:
                    click.echo("Cancelled.")
                    return

        language = locale.split('_')[0]
        base_path = f"{language}/{locale}/{voice}/{quality}"
        model_filename = f"{locale}-{voice}-{quality}.onnx"
        config_filename = f"{model_filename}.json"

        onnx_path = f"{base_path}/{model_filename}"
        config_path = f"{base_path}/{config_filename}"

        click.echo(f"\nDownloading model: {locale}/{voice}/{quality}")
        click.echo(f"Destination: {model_dir}")

        repo_id = "rhasspy/piper-voices"

        click.echo(f"\nDownloading {model_filename}...")
        onnx_file = hf_hub_download(
            repo_id=repo_id,
            filename=onnx_path,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )

        click.echo(f"Downloading {config_filename}...")
        config_file = hf_hub_download(
            repo_id=repo_id,
            filename=config_path,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )

        click.echo("\nDownload complete!")
        click.echo(f"Model file: {onnx_file}")

        click.echo("\nTo repeat this operation:")
        click.echo(f"  tca get-model --locale {locale} --voice {voice} --quality {quality}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('validate')
@click.option('--yaml', 'yaml_path', type=click.Path(exists=True),
              help='Path to time phrase configuration file')
def validate_config(yaml_path):
    """Validate a time phrase configuration and show sample outputs.

    Compiles rules from the YAML, generates phrases for a set of sample
    times using the same logic as the Pico, and checks the examples block.
    Mismatches in the examples block are reported as warnings.

    Optionally plays the generated audio sequences if a matching audio
    directory exists.

    \b
    Interactive mode (prompts for missing options):
      tca validate

    \b
    Expert mode:
      tca validate --yaml time_phrases_en_US.yaml
    """
    from .rules_generator import load_yaml, generate_rules, generate_vocab
    from . import pico_rules

    SAMPLE_TIMES = [
        (0,  0,  "midnight"),
        (6,  0,  "06:00"),
        (8,  9,  "08:09"),
        (8,  12, "08:12"),
        (9,  30, "09:30"),
        (12, 0,  "noon"),
        (13, 45, "13:45"),
        (14, 30, "14:30"),
        (20, 48, "20:48"),
        (23, 0,  "23:00"),
    ]

    try:
        if not yaml_path:
            yaml_files = find_yaml_files()
            if not yaml_files:
                click.echo("No YAML configuration files found.")
                return
            yaml_path = questionary.select(
                "Select configuration file:",
                choices=[str(f) for f in yaml_files]
            ).ask()
            if not yaml_path:
                click.echo("Cancelled.")
                return

        config = load_yaml(yaml_path)
        locale = config['locale']
        all_modes = list(config['modes'].keys())

        # Compile rules and vocab
        rules_doc = generate_rules(config)
        vocab_map = generate_vocab(config)  # symbolic key -> filename

        # Build filename -> spoken text from YAML vocab for display
        filename_to_text = {}
        for section_name, section_data in config.get('vocab', {}).items():
            if not isinstance(section_data, dict):
                continue
            for key, value in section_data.items():
                if section_name == 'number_words':
                    filename = f'number_{key}.wav'
                else:
                    filename = f'{section_name}_{key}.wav'
                filename_to_text[filename] = str(value)

        def files_to_spoken(filenames):
            if not filenames:
                return '[NO MATCH]'
            return ' '.join(filename_to_text.get(f, f'[{f}]') for f in filenames)

        click.echo(f"\nLocale: {locale}")
        click.echo(f"Modes:  {', '.join(all_modes)}")

        total_warnings = 0

        # Parse examples block - keys are "HH:MM" strings
        raw_examples = config.get('examples', {})
        parsed_examples = {}
        for time_key, mode_phrases in raw_examples.items():
            h, m = (int(x) for x in str(time_key).split(':'))
            parsed_examples[(h, m)] = mode_phrases

        # Collect per-mode sample results for optional playback
        # { mode_name: [(h, m, label, phrase, [filenames]), ...] }
        mode_samples = {}

        for check_mode in all_modes:
            mode_rules_doc = {
                'locale': rules_doc['locale'],
                'day_period': rules_doc['day_period'],
                'modes': {check_mode: rules_doc['modes'][check_mode]},
            }

            click.echo(f"\n{'='*56}")
            click.echo(f"Mode: {check_mode}")
            click.echo(f"{'='*56}")
            click.echo(f"  {'Time':<8} {'Label':<12} {'Phrase'}")
            click.echo(f"  {'-'*7} {'-'*11} {'-'*35}")

            samples = []
            for h, m, label in SAMPLE_TIMES:
                files = pico_rules.get_audio_files(mode_rules_doc, vocab_map, check_mode, h, m)
                phrase = files_to_spoken(files)
                click.echo(f"  {h:02d}:{m:02d}  {label:<12} {phrase}")
                samples.append((h, m, label, phrase, files or []))
            mode_samples[check_mode] = samples

            # Check examples
            mode_warnings = 0
            example_results = []
            for (h, m), mode_phrases in parsed_examples.items():
                if check_mode not in mode_phrases:
                    continue
                expected = mode_phrases[check_mode]
                files = pico_rules.get_audio_files(mode_rules_doc, vocab_map, check_mode, h, m)
                got = files_to_spoken(files)
                if got != expected:
                    example_results.append((h, m, expected, got))
                    mode_warnings += 1

            if example_results:
                click.echo(f"\n  Examples: WARN ({mode_warnings} mismatch(es))")
                for h, m, expected, got in example_results:
                    click.echo(f"    {h:02d}:{m:02d}  expected: {expected!r}")
                    click.echo(f"           got:      {got!r}")
            else:
                example_count = sum(
                    1 for mp in parsed_examples.values() if check_mode in mp
                )
                click.echo(f"\n  Examples: OK ({example_count} checked)")

            total_warnings += mode_warnings

        click.echo(f"\n{'='*56}")
        if total_warnings:
            click.echo(f"Result: WARN ({total_warnings} total mismatch(es))")
        else:
            click.echo(f"Result: OK")
        click.echo(f"{'='*56}")

        click.echo("\nTo repeat this operation:")
        click.echo(f"  tca validate --yaml {yaml_path}")

        # --- Optional playback ---

        if not questionary.confirm("\nPlay samples?", default=False).ask():
            return

        audio_dirs = find_audio_dirs(locale)
        if not audio_dirs:
            click.echo(f"No generated audio directories found for locale '{locale}'.")
            click.echo("Run 'tca generate' first.")
            return

        if len(audio_dirs) == 1:
            selected_dir = audio_dirs[0]
        else:
            selected_dir = questionary.select(
                "Select audio directory:",
                choices=[str(d) for d in audio_dirs]
            ).ask()
            if not selected_dir:
                return
            selected_dir = Path(selected_dir)

        audio_wav_dir = Path(selected_dir) / 'audio'
        click.echo(f"\nUsing: {selected_dir.name}")

        while True:
            mode_choice = questionary.select(
                "Select mode to play:",
                choices=all_modes + ["quit"]
            ).ask()

            if not mode_choice or mode_choice == "quit":
                break

            samples = mode_samples[mode_choice]
            click.echo(f"\nPlaying mode: {mode_choice}")
            click.echo("Press Ctrl-C to skip to next sample.\n")

            for h, m, label, phrase, filenames in samples:
                click.echo(f"  {h:02d}:{m:02d}  {label:<12} {phrase}")
                if filenames:
                    try:
                        play_wav_sequence(audio_wav_dir, filenames)
                    except KeyboardInterrupt:
                        click.echo("  (skipped)")
                        continue
                else:
                    click.echo("  (no audio files)")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('generate')
@click.option('--yaml', 'yaml_path', type=click.Path(exists=True),
              help='Path to time phrase configuration file')
@click.option('--model', help='Path to voice model .onnx file')
@click.option('--output-dir', default=None,
              help='Output directory (default: audio/<locale>_<voice>_<quality>)')
@click.option('--force', is_flag=True,
              help='Overwrite existing files without warning')
@click.option('--speaker-threshold', default=DEFAULT_SPEAKER_THRESHOLD,
              type=click.IntRange(0, 32767),
              help='Soft limiter threshold (0-32767, default: 16000). Use 32767 to disable.')
@click.option('--highpass-cutoff', default=DEFAULT_HIGHPASS_CUTOFF,
              type=click.IntRange(0, 22050),
              help='High-pass filter cutoff in Hz (default: 300). Set to 0 to disable.')
def generate_audio(yaml_path, model, output_dir, force, speaker_threshold, highpass_cutoff):
    """Generate audio files for a time phrase configuration.

    Generates audio for all modes defined in the YAML in a single run.
    All modes share one set of WAV files. Per-mode rules are written to
    a rules/ subdirectory.

    \b
    Interactive mode (prompts for missing options):
      tca generate

    \b
    Expert mode (all options specified):
      tca generate --yaml time_phrases_en_US.yaml --model ./models/.../model.onnx
    """
    try:
        if not yaml_path:
            yaml_files = find_yaml_files()

            if not yaml_files:
                click.echo("No YAML configuration files found.")
                click.echo("Looking in: ., time_formats/, */")
                return

            choices = [str(f) for f in yaml_files]
            yaml_path = questionary.select(
                "Select configuration file:",
                choices=choices
            ).ask()

            if not yaml_path:
                click.echo("Cancelled.")
                return

        config = load_yaml(yaml_path)
        locale = config['locale']
        modes = list(config['modes'].keys())

        if not modes:
            click.echo("Error: no modes defined in YAML", err=True)
            return

        if not model:
            model_files = find_model_files()

            if not model_files:
                click.echo("\nNo local models found.")
                click.echo("Download a model first:")
                click.echo("  tca get-model")
                return

            choices = [str(f) for f in model_files]
            model = questionary.select(
                "Select voice model:",
                choices=choices
            ).ask()

            if not model:
                click.echo("Cancelled.")
                return

        model_path = Path(model)
        if not model_path.exists():
            click.echo(f"Error: Model file not found: {model}", err=True)
            return

        model_filename = model_path.stem
        try:
            parts = model_filename.split('-')
            if len(parts) >= 3:
                voice_name = parts[1]
                quality = parts[2]
                default_output_dir = f"audio/{locale}_{voice_name}_{quality}"
            else:
                default_output_dir = f"audio/{locale}_unknown_unknown"
        except Exception:
            default_output_dir = f"audio/{locale}_unknown_unknown"

        if output_dir is None:
            output_dir = default_output_dir

        output_path = Path(output_dir)

        if output_path.exists() and not force:
            audio_dir = output_path / 'audio'
            if audio_dir.exists() and list(audio_dir.glob('*.wav')):
                click.echo(f"\nWarning: Output directory already exists: {output_dir}")
                if not questionary.confirm("Overwrite existing files?").ask():
                    click.echo("Aborted.")
                    return

        click.echo(f"\nLocale: {locale}")
        click.echo(f"Modes: {', '.join(modes)}")
        click.echo(f"Voice model: {model}")
        click.echo(f"Output directory: {output_dir}")

        effective_threshold = None if speaker_threshold == 32767 else speaker_threshold
        effective_cutoff = None if highpass_cutoff == 0 else highpass_cutoff

        click.echo(f"High-pass filter: {f'{effective_cutoff}Hz' if effective_cutoff else 'disabled'}")
        click.echo(f"Soft limiter: {effective_threshold if effective_threshold else 'disabled'}")

        click.echo("\nGenerating audio files...")

        stats = generate_audio_package_with_tts(
            config, str(model_path), output_dir,
            speaker_threshold=effective_threshold,
            highpass_cutoff=effective_cutoff
        )

        click.echo("\nWriting locale package...")
        package_sizes = write_locale_package(config, output_dir)

        click.echo(f"  vocab.json: {package_sizes['vocab']} bytes")
        for key, size in package_sizes.items():
            if key == 'vocab':
                continue
            click.echo(f"  {key}_rules.json: {size} bytes")

        click.echo("\n" + "="*60)
        click.echo("Generation complete!")
        click.echo("="*60)
        click.echo(f"Vocab file:  {stats['vocab_file']}")
        click.echo(f"Audio files: {stats['audio_dir']}")
        click.echo(f"Rules:       {output_dir}/rules/")
        click.echo(f"Success: {stats['success_count']}/{stats['total_audio_files']} audio files")

        if stats['failed_files']:
            click.echo(f"Failed: {stats['failure_count']}")
            for filename, text in stats['failed_files'][:3]:
                click.echo(f"  {filename}: '{text}'")
            if len(stats['failed_files']) > 3:
                click.echo(f"  ... and {len(stats['failed_files']) - 3} more")

        click.echo("\nTo repeat this operation:")
        cmd = f"  tca generate --yaml {yaml_path} --model {model}"
        if output_dir != default_output_dir:
            cmd += f" --output-dir {output_dir}"
        if force:
            cmd += " --force"
        if speaker_threshold != DEFAULT_SPEAKER_THRESHOLD:
            cmd += f" --speaker-threshold {speaker_threshold}"
        if highpass_cutoff != DEFAULT_HIGHPASS_CUTOFF:
            cmd += f" --highpass-cutoff {highpass_cutoff}"
        click.echo(cmd)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('debug')
@click.option('--yaml', 'yaml_path', type=click.Path(exists=True),
              help='Path to debug configuration YAML file')
@click.option('--model', help='Path to voice model .onnx file')
@click.option('--output-dir', default='./audio/debug',
              help='Output directory (default: ./audio/debug)')
@click.option('--force', is_flag=True,
              help='Overwrite existing files without warning')
def generate_debug(yaml_path, model, output_dir, force):
    """Generate speaker test audio from a debug configuration.

    Produces one subdirectory per variant under the output directory.
    Each subdirectory contains a label file and one WAV per sentence,
    processed with the variant's filter and limiter settings.
    Sentences are normalized to a fixed peak before processing so that
    filter and limiter comparisons are not confounded by volume differences.

    \b
    Interactive mode (prompts for missing options):
      tca debug

    \b
    Expert mode:
      tca debug --yaml speaker_test.yaml --model ./models/.../model.onnx
    """
    from .debug_generator import load_debug_yaml, generate_debug_package

    try:
        if not yaml_path:
            debug_yamls = sorted(set(
                list(Path('.').glob('*debug*.yaml')) +
                list(Path('.').glob('*speaker*.yaml')) +
                list(Path('.').glob('*test*.yaml'))
            ))

            if not debug_yamls:
                click.echo("No debug YAML files found in current directory.")
                click.echo("Expected filenames matching: *debug*.yaml, *speaker*.yaml, *test*.yaml")
                return

            choices = [str(f) for f in debug_yamls]
            yaml_path = questionary.select(
                "Select debug configuration file:",
                choices=choices
            ).ask()

            if not yaml_path:
                click.echo("Cancelled.")
                return

        config = load_debug_yaml(yaml_path)
        sentences = config["sentences"]
        variants = config["variants"]

        if not model:
            model_files = find_model_files()

            if not model_files:
                click.echo("\nNo local models found.")
                click.echo("Download a model first:")
                click.echo("  tca get-model")
                return

            choices = [str(f) for f in model_files]
            model = questionary.select(
                "Select voice model:",
                choices=choices
            ).ask()

            if not model:
                click.echo("Cancelled.")
                return

        model_path = Path(model)
        if not model_path.exists():
            click.echo(f"Error: Model file not found: {model}", err=True)
            return

        output_path = Path(output_dir)
        if output_path.exists() and not force:
            existing = list(output_path.iterdir())
            if existing:
                click.echo(f"\nWarning: Output directory already exists: {output_dir}")
                if not questionary.confirm("Overwrite existing files?").ask():
                    click.echo("Aborted.")
                    return

        click.echo(f"\nSentences: {len(sentences)}")
        for i, s in enumerate(sentences, start=1):
            click.echo(f"  {i}. {s}")
        click.echo(f"\nVariants: {len(variants)}")
        for v in variants:
            cutoff = v.get('highpass_cutoff')
            threshold = v.get('speaker_threshold')
            click.echo(
                f"  {v['name']:<24} "
                f"highpass={f'{cutoff}Hz' if cutoff else 'off':<12} "
                f"threshold={threshold if threshold else 'off'}"
            )
        click.echo(f"\nVoice model: {model}")
        click.echo(f"Output: {output_dir}")
        click.echo("\nGenerating...")

        stats = generate_debug_package(config, model_path, output_dir)

        click.echo("\n" + "="*60)
        click.echo("Done!")
        click.echo("="*60)
        click.echo(f"Output:  {stats['output_dir']}")
        click.echo(f"Success: {stats['total_success']} files")
        if stats['total_failure']:
            click.echo(f"Failed:  {stats['total_failure']} files")
            for vr in stats['variants']:
                for err in vr['errors']:
                    click.echo(f"  {err}")

        click.echo("\nTo repeat this operation:")
        cmd = f"  tca debug --yaml {yaml_path} --model {model}"
        if output_dir != './audio/debug':
            cmd += f" --output-dir {output_dir}"
        if force:
            cmd += " --force"
        click.echo(cmd)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()