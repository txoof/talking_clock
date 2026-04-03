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


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except errors')
def cli(verbose, quiet):
    """Generate multilingual time phrase audio files.

    \b
    Common commands:
      tca list-models --remote              List available voice models
      tca get-model --locale en_US --voice lessac --quality medium
      tca validate --yaml <file> --mode casual
      tca generate --yaml <file> --mode casual --model <path>
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
@click.option('--mode', help='Validate a specific mode only (default: all modes)')
@click.option('--samples', default=7, help='Number of sample times to show per mode (default: 7)')
def validate_config(yaml_path, mode, samples):
    """Validate a time phrase configuration and show sample outputs.

    For each mode, runs both the phrase_generator (reference) and the
    pico_rules evaluator and compares their output. Also checks every
    rendered_example in the YAML. Reports any disagreements.

    \b
    Interactive mode (prompts for missing options):
      tca validate

    \b
    Expert mode:
      tca validate --yaml time_phrases_en_US.yaml
      tca validate --yaml time_phrases_en_US.yaml --mode casual
    """
    import sys
    from pathlib import Path as _Path
    from .phrase_generator import generate_phrase_tokens, get_all_vocab_with_dedup

    _pkg_dir = _Path(__file__).parent
    _src_dir = _pkg_dir.parent
    _repo_root = _src_dir.parent
    _clock_code = _repo_root.parent / "clock_code"
    if str(_clock_code) not in sys.path:
        sys.path.insert(0, str(_clock_code))

    try:
        import pico_rules as _pico_rules
    except ImportError:
        click.echo(
            "Warning: pico_rules not found in clock_code/. "
            "Pico-side validation will be skipped.", err=True
        )
        _pico_rules = None

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

        config = load_time_phrases(yaml_path)
        locale = config['locale']
        all_modes = list(config['modes'].keys())

        if mode and mode not in config['modes']:
            click.echo(f"Error: Mode '{mode}' not found. Available: {', '.join(all_modes)}", err=True)
            return

        modes_to_check = [mode] if mode else all_modes

        vocab_map, audio_files = get_all_vocab_with_dedup(config)
        file_to_key = {v: k for k, v in vocab_map.items()}

        if _pico_rules:
            pico_rules_data = generate_rules(config)
        else:
            pico_rules_data = None

        def tokens_to_text(token_keys):
            """Reconstruct spoken text from a list of vocab keys."""
            words = []
            for key in token_keys:
                section, entry = key.split(".", 1)
                try:
                    entry = int(entry)
                except ValueError:
                    pass
                text = config["vocab"].get(section, {}).get(entry)
                if text:
                    words.append(text)
            return " ".join(words)

        def files_to_text(filenames):
            """Reconstruct spoken text from a list of audio filenames."""
            keys = [file_to_key.get(f) for f in filenames if file_to_key.get(f)]
            return tokens_to_text(keys)

        sample_times = [
            (0, 0, "midnight"),
            (6, 0, "early morning"),
            (11, 7, "mid morning"),
            (11, 30, "late morning"),
            (12, 0, "noon"),
            (13, 45, "afternoon"),
            (18, 30, "evening"),
            (23, 0, "late night"),
        ]

        total_errors = 0

        click.echo(f"\nLocale: {locale}")
        click.echo(f"Vocab: {len(audio_files)} unique audio files")

        for check_mode in modes_to_check:
            click.echo(f"\n{'='*60}")
            click.echo(f"Mode: {check_mode}")
            click.echo(f"{'='*60}")

            mode_errors = 0

            click.echo(f"\nSample phrases:")
            click.echo(f"  {'Time':<8} {'Description':<14} {'Generated'}")
            click.echo(f"  {'-'*7} {'-'*13} {'-'*35}")

            for hour, minute, description in sample_times[:samples]:
                ref_tokens = generate_phrase_tokens(config, check_mode, hour, minute)
                if ref_tokens:
                    phrase = tokens_to_text(ref_tokens)
                    click.echo(f"  {hour:02d}:{minute:02d}  {description:<14} {phrase}")
                else:
                    click.echo(f"  {hour:02d}:{minute:02d}  {description:<14} [NO MATCH]")
                    mode_errors += 1

            rendered = config.get("rendered_examples", {})
            if rendered:
                click.echo(f"\nChecking rendered_examples:")
                example_errors = []

                for _group, times in rendered.items():
                    for time_val, mode_phrases in times.items():
                        if check_mode not in mode_phrases:
                            continue

                        if isinstance(time_val, int):
                            h, m = time_val // 60, time_val % 60
                        else:
                            h, m = (int(x) for x in str(time_val).split(":"))

                        expected = mode_phrases[check_mode]
                        ref_tokens = generate_phrase_tokens(config, check_mode, h, m)
                        got = tokens_to_text(ref_tokens) if ref_tokens else "[NO MATCH]"

                        if got != expected:
                            example_errors.append(
                                f"  {h:02d}:{m:02d}  expected: {expected!r}\n"
                                f"         got:      {got!r}"
                            )

                        if pico_rules_data:
                            pico_files = _pico_rules.get_audio_files(
                                pico_rules_data, vocab_map, check_mode, h, m
                            )
                            pico_text = files_to_text(pico_files) if pico_files else "[NO MATCH]"
                            if pico_text != expected:
                                example_errors.append(
                                    f"  {h:02d}:{m:02d}  pico expected: {expected!r}\n"
                                    f"         pico got:      {pico_text!r}"
                                )

                if example_errors:
                    click.echo(f"  FAIL: {len(example_errors)} example(s) did not match:")
                    for err in example_errors:
                        click.echo(err)
                    mode_errors += len(example_errors)
                else:
                    example_count = sum(
                        1 for times in rendered.values()
                        for mode_phrases in times.values()
                        if check_mode in mode_phrases
                    )
                    click.echo(f"  OK: all {example_count} examples matched")

            coverage_failures = []
            for h in range(24):
                for m in range(60):
                    if not generate_phrase_tokens(config, check_mode, h, m):
                        coverage_failures.append(f"{h:02d}:{m:02d}")

            if coverage_failures:
                click.echo(f"\nCoverage: FAIL - {len(coverage_failures)} times produce no output")
                for t in coverage_failures[:10]:
                    click.echo(f"  {t}")
                if len(coverage_failures) > 10:
                    click.echo(f"  ... and {len(coverage_failures) - 10} more")
                mode_errors += len(coverage_failures)
            else:
                click.echo(f"\nCoverage: OK - all 1440 times matched")

            total_errors += mode_errors
            if mode_errors:
                click.echo(f"\nMode result: FAIL ({mode_errors} error(s))")
            else:
                click.echo(f"\nMode result: OK")

        click.echo(f"\n{'='*60}")
        if total_errors:
            click.echo(f"Validation FAILED: {total_errors} total error(s)")
        else:
            click.echo(f"Validation PASSED")
        click.echo(f"{'='*60}")

        click.echo("\nTo repeat this operation:")
        cmd = f"  tca validate --yaml {yaml_path}"
        if mode:
            cmd += f" --mode {mode}"
        click.echo(cmd)

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
