# src/talking_clock_audio/cli.py

"""Command-line interface for talking-clock-audio."""

import logging
import click
import questionary
from pathlib import Path

from .phrase_generator import load_time_phrases
from .tts_generator import (generate_audio_package_with_tts,
                             DEFAULT_SPEAKER_THRESHOLD,
                             DEFAULT_HIGHPASS_CUTOFF)
from .voice_manager import get_available_voices


def find_yaml_files(search_dir='.'):
    """Find all time phrase YAML files in directory."""
    search_path = Path(search_dir)
    yaml_files = []
    
    # Check common locations
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
    
    \b
    Interactive mode (prompts for missing options):
      tca generate
      tca validate
      tca get-model
    
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
        # Interactive prompts for missing options
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
            
            # Filter by locale
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
            
            # Filter by voice
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
        
        # Construct paths
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
        
        # Show command to repeat
        click.echo("\nTo repeat this operation:")
        click.echo(f"  tca get-model --locale {locale} --voice {voice} --quality {quality}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('validate')
@click.option('--yaml', 'yaml_path', type=click.Path(exists=True), 
              help='Path to time phrase configuration file')
@click.option('--mode', help='Speaking style (operational/broadcast/standard/casual)')
@click.option('--samples', default=7, help='Number of sample times to show (default: 7)')
def validate_config(yaml_path, mode, samples):
    """Validate a time phrase configuration and show sample outputs.
    
    \b
    Interactive mode (prompts for missing options):
      tca validate
    
    \b
    Expert mode:
      tca validate --yaml time_phrases_en_US.yaml --mode casual
    """
    from .phrase_generator import generate_phrase_tokens, get_all_vocab_with_dedup
    
    try:
        # Interactive prompts for missing options
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
        
        if not mode:
            modes = list(config['modes'].keys())
            mode = questionary.select(
                "Select mode:",
                choices=modes
            ).ask()
            
            if not mode:
                click.echo("Cancelled.")
                return
        
        click.echo(f"\nConfiguration: {config['locale']}")
        click.echo(f"Mode: {mode}")
        
        if mode not in config['modes']:
            click.echo(f"Error: Mode '{mode}' not found", err=True)
            click.echo(f"Available: {', '.join(config['modes'].keys())}")
            return
        
        vocab_map, audio_files = get_all_vocab_with_dedup(config)
        click.echo(f"Vocabulary: {len(audio_files)} unique audio files\n")
        
        click.echo(f"Sample phrases:")
        
        test_times = [
            (0, 0, "midnight"),
            (6, 0, "early morning"),
            (11, 30, "late morning"),
            (12, 0, "noon"),
            (13, 45, "afternoon"),
            (18, 30, "evening"),
            (23, 0, "late night"),
        ]
        
        for hour, minute, description in test_times[:samples]:
            tokens = generate_phrase_tokens(config, mode, hour, minute)
            if tokens:
                words = []
                for token in tokens:
                    if token in vocab_map:
                        filename = vocab_map[token]
                        text = audio_files[filename]
                        words.append(text)
                
                phrase = ' '.join(words)
                click.echo(f"  {hour:02d}:{minute:02d} ({description:12s}): {phrase}")
        
        click.echo("\nConfiguration is valid!")
        
        # Show command to repeat
        click.echo("\nTo repeat this operation:")
        click.echo(f"  tca validate --yaml {yaml_path} --mode {mode}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('generate')
@click.option('--yaml', 'yaml_path', type=click.Path(exists=True),
              help='Path to time phrase configuration file')
@click.option('--mode', help='Speaking style (operational/broadcast/standard/casual)')
@click.option('--model', help='Path to voice model .onnx file')
@click.option('--output-dir', default=None,
              help='Output directory (default: audio/<locale>_<voice>_<quality>_<mode>)')
@click.option('--force', is_flag=True,
              help='Overwrite existing files without warning')
@click.option('--speaker-threshold', default=DEFAULT_SPEAKER_THRESHOLD,
              type=click.IntRange(0, 32767),
              help='Soft limiter threshold (0-32767, default: 16000). Use 32767 to disable.')
@click.option('--highpass-cutoff', default=DEFAULT_HIGHPASS_CUTOFF,
              type=click.IntRange(0, 22050),
              help='High-pass filter cutoff in Hz (default: 300). Set to 0 to disable.')
def generate_audio(yaml_path, mode, model, output_dir, force, speaker_threshold, highpass_cutoff):
    """Generate audio files for a time phrase configuration.
    
    \b
    Interactive mode (prompts for missing options):
      tca generate
    
    \b
    Expert mode (all options specified):
      tca generate --yaml time_phrases_en_US.yaml --mode casual --model ./models/.../model.onnx
    
    \b
    Mixed mode:
      tca generate --yaml time_phrases_en_US.yaml
      (prompts for --mode and --model)
    """
    try:
        # Interactive prompt for YAML
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
        
        # Load config
        config = load_time_phrases(yaml_path)
        locale = config['locale']
        
        # Interactive prompt for mode
        if not mode:
            modes = list(config['modes'].keys())
            
            # Show mode descriptions
            mode_descriptions = {
                'operational': 'Military/radio precision (e.g., "thirteen hundred hours")',
                'broadcast': 'News/announcements (e.g., "one thirty p.m.")',
                'standard': 'Professional/office (e.g., "one thirty")',
                'casual': 'Conversational (e.g., "half past one")',
            }
            
            choices = [
                questionary.Choice(
                    title=f"{m} - {mode_descriptions.get(m, 'Custom mode')}",
                    value=m
                )
                for m in modes
            ]
            
            mode = questionary.select(
                "Select mode:",
                choices=choices
            ).ask()
            
            if not mode:
                click.echo("Cancelled.")
                return
        
        if mode not in config['modes']:
            click.echo(f"Error: Mode '{mode}' not found", err=True)
            return
        
        # Interactive prompt for model
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
        
        # Determine output directory
        model_filename = model_path.stem
        try:
            parts = model_filename.split('-')
            if len(parts) >= 3:
                voice_name = parts[1]
                quality = parts[2]
                default_output_dir = f"audio/{locale}_{voice_name}_{quality}_{mode}"
            else:
                voice_name = 'unknown'
                quality = 'unknown'
                default_output_dir = f"audio/{locale}_unknown_unknown_{mode}"
        except:
            voice_name = 'unknown'
            quality = 'unknown'
            default_output_dir = f"audio/{locale}_unknown_unknown_{mode}"
        
        if output_dir is None:
            output_dir = default_output_dir
        
        output_path = Path(output_dir)
        
        # Check for existing files
        if output_path.exists() and not force:
            audio_dir = output_path / 'audio'
            if audio_dir.exists() and list(audio_dir.glob('*.wav')):
                click.echo(f"\nWarning: Output directory already exists: {output_dir}")
                if not questionary.confirm("Overwrite existing files?").ask():
                    click.echo("Aborted.")
                    return
        
        # Show configuration
        click.echo(f"\nConfiguration: {locale}")
        click.echo(f"Mode: {mode}")
        click.echo(f"Voice model: {model}")
        click.echo(f"Output directory: {output_dir}")
        
        effective_threshold = None if speaker_threshold == 32767 else speaker_threshold
        effective_cutoff = None if highpass_cutoff == 0 else highpass_cutoff
        
        if effective_cutoff is not None:
            click.echo(f"High-pass filter: {effective_cutoff}Hz")
        else:
            click.echo("High-pass filter: disabled")
        
        if effective_threshold is not None:
            click.echo(f"Soft limiter: {effective_threshold}")
        else:
            click.echo("Soft limiter: disabled")
        
        click.echo("\nGenerating audio files...")
        
        # Generate
        stats = generate_audio_package_with_tts(
            config, mode, str(model_path), output_dir,
            speaker_threshold=effective_threshold,
            highpass_cutoff=effective_cutoff
        )
        
        # Report results
        click.echo("\n" + "="*60)
        click.echo("Generation complete!")
        click.echo("="*60)
        click.echo(f"Vocab file: {stats['vocab_file']}")
        click.echo(f"Audio files: {stats['audio_dir']}")
        click.echo(f"Success: {stats['success_count']}/{stats['total_audio_files']}")
        
        if stats['failed_files']:
            click.echo(f"Failed: {stats['failure_count']}")
            for filename, text in stats['failed_files'][:3]:
                click.echo(f"  {filename}: '{text}'")
            if len(stats['failed_files']) > 3:
                click.echo(f"  ... and {len(stats['failed_files']) - 3} more")
        
        # Show command to repeat
        click.echo("\nTo repeat this operation:")
        cmd = f"  tca generate --yaml {yaml_path} --mode {mode} --model {model}"
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


if __name__ == '__main__':
    cli()
