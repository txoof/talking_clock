# src/talking_clock_audio/cli.py

"""Command-line interface for talking-clock-audio."""

import logging
import click
from pathlib import Path

from .phrase_generator import load_time_phrases, generate_audio_package
from .tts_generator import generate_audio_package_with_tts
from .voice_manager import get_available_voices


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except errors')
def cli(verbose, quiet):
    """Generate multilingual time phrase audio files.
    
    \b
    Common commands:
      tca list-models --remote              List available voice models
      tca get-model en_US/lessac/medium     Download a voice model
      tca validate <yaml> <mode>            Preview generated phrases
      tca generate <yaml> <mode> --model <path>  Generate audio files
    
    \b
    For detailed help on any command:
      tca <command> --help
    
    \b
    Examples:
      tca list-models --help
      tca generate --help
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
            """Convert locale code to readable name (e.g., en_US -> English (United States))."""
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
        
        # Group by locale
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
                # Show path in format expected by get-model command
                path = f"  {v.locale}/{v.voice_name}/{v.quality}"
                click.echo(path)
            click.echo()
    
    else:  # local
        model_path = Path(model_dir)
        if not model_path.exists():
            click.echo(f"Model directory not found: {model_dir}")
            click.echo("Use --model-dir to specify a different location")
            return
        
        # Find .onnx files (exclude .onnx.json files)
        onnx_files = [f for f in model_path.rglob('*.onnx') 
                      if not f.name.endswith('.onnx.json')]
        
        if not onnx_files:
            click.echo(f"No models found in {model_dir}")
            click.echo("\nTo download models, use:")
            click.echo("  tca list-models --remote")
            return
        
        click.echo(f"Found {len(onnx_files)} local models in {model_dir}:\n")
        
        for onnx_file in sorted(onnx_files):
            # Show full path from model_dir
            click.echo(f"  {onnx_file}")


@cli.command('get-model')
@click.argument('model_path')
@click.option('--model-dir', default='./models',
              help='Directory to download model to (default: ./models)')
def get_model(model_path, model_dir):
    """Download a voice model from Hugging Face.
    
    MODEL_PATH should be in format: locale/voice/quality
    
    Examples:
      tca get-model en_US/lessac/medium
      tca get-model nl_NL/rdh/medium
      tca get-model de_DE/thorsten/high
    """
    from huggingface_hub import hf_hub_download
    
    try:
        # Parse model path
        parts = model_path.split('/')
        if len(parts) != 3:
            click.echo("Error: Model path must be in format: locale/voice/quality", err=True)
            click.echo("Example: en_US/lessac/medium")
            click.echo("\nTo see available models:")
            click.echo("  tca list-models --remote")
            raise click.Abort()
        
        locale, voice_name, quality = parts
        language = locale.split('_')[0]  # Extract language from locale (e.g., 'en' from 'en_US')
        
        # Construct Hugging Face paths
        base_path = f"{language}/{locale}/{voice_name}/{quality}"
        model_filename = f"{locale}-{voice_name}-{quality}.onnx"
        config_filename = f"{model_filename}.json"
        
        onnx_path = f"{base_path}/{model_filename}"
        config_path = f"{base_path}/{config_filename}"
        
        click.echo(f"Downloading model: {locale}/{voice_name}/{quality}")
        click.echo(f"Destination: {model_dir}")
        
        repo_id = "rhasspy/piper-voices"
        
        # Download .onnx file
        click.echo(f"\nDownloading {model_filename}...")
        onnx_file = hf_hub_download(
            repo_id=repo_id,
            filename=onnx_path,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        
        # Download .onnx.json config file
        click.echo(f"Downloading {config_filename}...")
        config_file = hf_hub_download(
            repo_id=repo_id,
            filename=config_path,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        
        click.echo("\nDownload complete!")
        click.echo(f"Model file: {onnx_file}")
        click.echo(f"Config file: {config_file}")
        
        click.echo("\nTo use this model:")
        click.echo(f"  tca generate <yaml> <mode> --model {onnx_file}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('validate')
@click.argument('yaml_path', type=click.Path(exists=True))
@click.argument('mode')
@click.option('--samples', default=5, help='Number of sample times to show (default: 5)')
def validate_config(yaml_path, mode, samples):
    """Validate a time phrase configuration and show sample outputs.
    
    \b
    YAML_PATH: Path to time phrase configuration file (e.g., time_phrases_en_US.yaml)
    MODE: Speaking style - one of: operational, broadcast, standard, casual
    
    \b
    Modes explained:
      operational - Military/radio precision (e.g., "thirteen hundred hours")
      broadcast   - News/announcements (e.g., "one thirty p.m.")
      standard    - Professional/office (e.g., "one thirty")
      casual      - Conversational (e.g., "half past one")
    
    \b
    Example:
      tca validate time_phrases_en_US.yaml casual
    """
    from .phrase_generator import generate_phrase_tokens, get_all_vocab_with_dedup
    
    try:
        config = load_time_phrases(yaml_path)
        click.echo(f"Loaded configuration: {config['locale']}")
        click.echo(f"Available modes: {', '.join(config['modes'].keys())}")
        
        if mode not in config['modes']:
            click.echo(f"\nError: Mode '{mode}' not found in configuration")
            click.echo(f"Available modes: {', '.join(config['modes'].keys())}")
            return
        
        # Get vocab info
        vocab_map, audio_files = get_all_vocab_with_dedup(config)
        click.echo(f"\nVocabulary: {len(audio_files)} unique audio files needed")
        
        # Show sample times
        click.echo(f"\nSample phrases for mode '{mode}':")
        
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
                # Convert tokens to text
                words = []
                for token in tokens:
                    if token in vocab_map:
                        filename = vocab_map[token]
                        text = audio_files[filename]
                        words.append(text)
                
                phrase = ' '.join(words)
                click.echo(f"  {hour:02d}:{minute:02d} ({description:12s}): {phrase}")
        
        click.echo("\nConfiguration is valid!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command('generate')
@click.argument('yaml_path', type=click.Path(exists=True))
@click.argument('mode')
@click.option('--model', required=True, 
              help='Path to voice model .onnx file (e.g., ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx)')
@click.option('--output-dir', default=None,
              help='Output directory (default: audio/<locale>_<mode>)')
@click.option('--force', is_flag=True,
              help='Overwrite existing files without warning')
def generate_audio(yaml_path, mode, model, output_dir, force):
    """Generate audio files for a time phrase configuration.
    
    \b
    YAML_PATH: Path to time phrase configuration file
    MODE: Speaking style - one of: operational, broadcast, standard, casual
    
    \b
    Modes explained:
      operational - Military/radio precision (e.g., "thirteen hundred hours")
      broadcast   - News/announcements (e.g., "one thirty p.m.")
      standard    - Professional/office (e.g., "one thirty")
      casual      - Conversational (e.g., "half past one")
    
    \b
    Example:
      tca generate time_phrases_en_US.yaml casual --model ./models/en/en_US/lessac/medium/en_US-lessac-medium.onnx
    """
    try:
        # Load configuration
        config = load_time_phrases(yaml_path)
        locale = config['locale']
        
        click.echo(f"Configuration: {locale}")
        click.echo(f"Mode: {mode}")
        
        # Validate mode
        if mode not in config['modes']:
            click.echo(f"Error: Mode '{mode}' not found in configuration", err=True)
            click.echo(f"Available modes: {', '.join(config['modes'].keys())}")
            raise click.Abort()
        
        # Check model file exists
        model_path = Path(model)
        if not model_path.exists():
            click.echo(f"Error: Model file not found: {model}", err=True)
            click.echo("\nTo list available models:")
            click.echo("  tca list-models --local")
            click.echo("  tca list-models --remote")
            raise click.Abort()
        
        # Determine output directory
        if output_dir is None:
            output_dir = f"audio/{locale}_{mode}"
        
        output_path = Path(output_dir)
        
        # Check if output exists
        if output_path.exists() and not force:
            audio_dir = output_path / 'audio'
            if audio_dir.exists() and list(audio_dir.glob('*.wav')):
                click.echo(f"\nWarning: Output directory already exists: {output_dir}")
                click.echo("Existing audio files will be overwritten.")
                if not click.confirm("Continue?"):
                    click.echo("Aborted.")
                    return
        
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"Voice model: {model}")
        click.echo("\nGenerating audio files...")
        
        # Generate
        stats = generate_audio_package_with_tts(config, mode, str(model_path), output_dir)
        
        # Report results
        click.echo("\n" + "="*60)
        click.echo("Generation complete!")
        click.echo("="*60)
        click.echo(f"Config file: {stats['config_file']}")
        click.echo(f"Audio files: {stats['audio_dir']}")
        click.echo(f"Time rules: {stats['rules_count']}")
        click.echo(f"\nAudio generation:")
        click.echo(f"  Success: {stats['success_count']}/{stats['total_audio_files']}")
        click.echo(f"  Failed: {stats['failure_count']}")
        
        if stats['failed_files']:
            click.echo(f"\nFailed files:")
            for filename, text in stats['failed_files'][:5]:  # Show first 5
                click.echo(f"  {filename}: '{text}'")
            if len(stats['failed_files']) > 5:
                click.echo(f"  ... and {len(stats['failed_files']) - 5} more")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
