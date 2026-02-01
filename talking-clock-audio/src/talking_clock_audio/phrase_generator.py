# src/talking_clock_audio/phrase_generator.py

"""Phrase generation from time phrase YAML configurations.

This module loads YAML configurations defining time phrases in various languages
and modes, evaluates rules and computed fields, and generates token sequences
representing the audio files needed to speak any given time.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


def slugify(text: str) -> str:
    """Convert text to a safe filename slug.
    
    Args:
        text: Text to slugify.
        
    Returns:
        Slugified text suitable for filename.
        
    Examples:
        >>> slugify("o'clock")
        'o_clock'
        >>> slugify("twenty one")
        'twenty_one'
    """
    slug = text.lower()
    
    # Replace apostrophes with underscores (before removing them)
    slug = slug.replace("'", '_')
    
    # Replace spaces with underscores
    slug = slug.replace(' ', '_')
    
    # Remove quotes
    slug = slug.replace('"', '')
    
    # Replace periods and other non-alphanumeric with underscores
    slug = re.sub(r'[^a-z0-9_]', '_', slug)
    
    # Remove multiple consecutive underscores
    slug = re.sub(r'_+', '_', slug)
    
    # Remove leading/trailing underscores
    slug = slug.strip('_')
    
    return slug


def load_time_phrases(yaml_path: Path | str) -> Dict[str, Any]:
    """Load time phrases YAML file.
    
    Args:
        yaml_path: Path to the YAML file.
        
    Returns:
        Dict with the complete YAML structure.
        
    Raises:
        FileNotFoundError: If YAML file doesn't exist.
        yaml.YAMLError: If YAML is malformed.
    """
    yaml_path = Path(yaml_path)
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def evaluate_condition(condition_key: str, condition_value: Any, 
                       hour_24: int, minute: int) -> bool:
    """Evaluate a single condition against the current time.
    
    Args:
        condition_key: The condition type (e.g., 'minute_eq', 'hour_24_lt').
        condition_value: The value to compare against.
        hour_24: Current hour in 24h format (0-23).
        minute: Current minute (0-59).
    
    Returns:
        True if condition matches, False otherwise.
        
    Raises:
        ValueError: If condition format is invalid.
    """
    if condition_key == 'any':
        return condition_value is True
    
    parts = condition_key.split('_')
    if len(parts) < 2:
        raise ValueError(f"Invalid condition key: {condition_key}")
    
    op = parts[-1]
    field = '_'.join(parts[:-1])
    
    if field == 'minute':
        current_value = minute
    elif field == 'hour_24':
        current_value = hour_24
    else:
        raise ValueError(f"Unknown field in condition: {field}")
    
    if op == 'eq':
        return current_value == condition_value
    elif op == 'lt':
        return current_value < condition_value
    elif op == 'gt':
        return current_value > condition_value
    elif op == 'lte':
        return current_value <= condition_value
    elif op == 'gte':
        return current_value >= condition_value
    else:
        raise ValueError(f"Unknown operator: {op}")


def matches_rule(rule: Dict[str, Any], hour_24: int, minute: int) -> bool:
    """Check if a rule matches the given time.
    
    Args:
        rule: Dict with 'when' conditions and 'tokens'.
        hour_24: Current hour in 24h format (0-23).
        minute: Current minute (0-59).
    
    Returns:
        True if all conditions match, False otherwise.
    """
    when_conditions = rule['when']
    
    for condition_key, condition_value in when_conditions.items():
        if not evaluate_condition(condition_key, condition_value, hour_24, minute):
            return False
    
    return True


def find_matching_rule(mode_config: Dict[str, Any], hour_24: int, 
                       minute: int) -> Tuple[Optional[str], Optional[Dict]]:
    """Find the first matching rule for a given time.
    
    Args:
        mode_config: Dict with 'rule_order' and 'rules'.
        hour_24: Current hour in 24h format (0-23).
        minute: Current minute (0-59).
    
    Returns:
        Tuple of (rule_name, rule_dict) or (None, None) if no match.
    """
    rule_order = mode_config['rule_order']
    rules = mode_config['rules']
    
    for rule_name in rule_order:
        rule = rules[rule_name]
        if matches_rule(rule, hour_24, minute):
            return rule_name, rule
    
    return None, None


def evaluate_computed_field(field_def: Any, hour_24: int, minute: int, 
                            computed_values: Dict[str, Any]) -> Any:
    """Evaluate a computed field definition.
    
    Args:
        field_def: Field definition (string expression or dict with conditions).
        hour_24: Current hour (0-23).
        minute: Current minute (0-59).
        computed_values: Dict of already computed values.
        
    Returns:
        Computed value.
    """
    if isinstance(field_def, dict):
        for condition, value in field_def.items():
            if condition == 'otherwise':
                continue
            
            if condition.startswith('when_'):
                condition_str = condition[5:]
                
                if '_lt_' in condition_str:
                    field, threshold = condition_str.split('_lt_')
                    if field == 'hour_24' and hour_24 < int(threshold):
                        return value
                elif '_eq_' in condition_str:
                    parts = condition_str.split('_eq_')
                    if len(parts) == 2:
                        field, expected = parts
                        if field == 'hour_24' and hour_24 == int(expected):
                            return value
                    elif '_and_' in condition_str:
                        if 'hour_24_eq_0_and_minute_eq_0' in condition_str:
                            if hour_24 == 0 and minute == 0:
                                return value
        
        if 'otherwise' in field_def:
            return field_def['otherwise']
    
    if isinstance(field_def, str):
        if '[' in field_def and ']' in field_def:
            parts = field_def.split('[')
            dict_name = parts[0]
            key_expr = parts[1].rstrip(']')
            
            if key_expr in computed_values:
                key = computed_values[key_expr]
            elif key_expr == 'hour_24':
                key = hour_24
            elif key_expr == 'minute':
                key = minute
            else:
                key = key_expr
            
            return f"{dict_name}[{key}]"
        
        expr = field_def.replace('mod', '%')
        expr = expr.replace('hour_24', str(hour_24))
        expr = expr.replace('minute', str(minute))
        
        for comp_key, comp_val in computed_values.items():
            if comp_key in expr:
                expr = expr.replace(comp_key, str(comp_val))
        
        try:
            return eval(expr)
        except:
            return field_def
    
    return field_def


def compute_all_fields(config: Dict[str, Any], hour_24: int, 
                       minute: int) -> Dict[str, Any]:
    """Compute all field values for a given time.
    
    Args:
        config: Loaded YAML configuration.
        hour_24: Current hour (0-23).
        minute: Current minute (0-59).
        
    Returns:
        Dict of computed field values.
    """
    computed_fields = config['fields']['computed']
    computed_values = {}
    
    computed_values['hour_24'] = hour_24
    computed_values['minute'] = minute
    
    max_iterations = 3
    for iteration in range(max_iterations):
        for field_name, field_def in computed_fields.items():
            if field_name not in computed_values:
                computed_values[field_name] = evaluate_computed_field(
                    field_def, hour_24, minute, computed_values
                )
    
    return computed_values


def expand_token(token: str, computed_values: Dict[str, Any], 
                 config: Dict[str, Any]) -> str:
    """Expand a token template to actual vocab word reference.
    
    Args:
        token: Token template (e.g., "{hour_12_word}" or "past").
        computed_values: Dict of computed values.
        config: Loaded YAML configuration.
        
    Returns:
        Vocab key reference (e.g., "number_words.11").
    """
    if not token.startswith('{'):
        return f"words.{token}"
    
    field_name = token.strip('{}')
    
    if field_name in computed_values:
        value = computed_values[field_name]
        
        if isinstance(value, str) and '[' in value:
            dict_name, key = value.replace(']', '').split('[')
            return f"{dict_name}.{key}"
        
        if field_name.endswith('_word'):
            return f"words.{value}"
        
        return f"words.{value}"
    
    return f"words.{field_name}"


def generate_phrase_tokens(config: Dict[str, Any], mode: str, 
                           hour_24: int, minute: int) -> Optional[List[str]]:
    """Generate phrase tokens for a given time and mode.
    
    Args:
        config: Loaded YAML configuration.
        mode: Mode name (e.g., 'casual', 'broadcast').
        hour_24: Current hour (0-23).
        minute: Current minute (0-59).
        
    Returns:
        List of vocab keys (e.g., ["number_words.11", "words.thirty"])
        or None if no matching rule found.
    """
    computed_values = compute_all_fields(config, hour_24, minute)
    mode_config = config['modes'][mode]
    rule_name, rule = find_matching_rule(mode_config, hour_24, minute)
    
    if not rule:
        return None
    
    tokens = []
    for token_template in rule['tokens']:
        vocab_key = expand_token(token_template, computed_values, config)
        tokens.append(vocab_key)
    
    return tokens


def get_all_vocab_with_dedup(config: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Get all unique vocab entries with human-readable filenames.
    
    Deduplicates vocab entries using case-insensitive comparison while
    preserving whitespace and punctuation as specified in the YAML.
    
    Args:
        config: Loaded YAML configuration.
        
    Returns:
        Tuple of (vocab_map, audio_files) where:
        - vocab_map: Dict mapping vocab keys to audio filenames.
        - audio_files: Dict mapping audio filenames to text content.
    """
    normalized_to_file = {}
    vocab_to_file = {}
    audio_files = {}
    
    for key, value in config['vocab']['words'].items():
        if isinstance(value, list):
            for i, variant in enumerate(value):
                normalized = variant.lower()
                
                if normalized not in normalized_to_file:
                    slug = slugify(variant)
                    filename = f"word_{slug}.wav"
                    normalized_to_file[normalized] = filename
                    audio_files[filename] = variant
                
                vocab_key = f"words.{key}"
                vocab_to_file[vocab_key] = normalized_to_file[normalized]
                break
        else:
            normalized = value.lower()
            
            if normalized not in normalized_to_file:
                slug = slugify(value)
                filename = f"word_{slug}.wav"
                normalized_to_file[normalized] = filename
                audio_files[filename] = value
            
            vocab_key = f"words.{key}"
            vocab_to_file[vocab_key] = normalized_to_file[normalized]
    
    for key, value in config['vocab']['number_words'].items():
        normalized = value.lower()
        
        if normalized not in normalized_to_file:
            slug = slugify(value)
            filename = f"number_{slug}.wav"
            normalized_to_file[normalized] = filename
            audio_files[filename] = value
        
        vocab_key = f"number_words.{key}"
        vocab_to_file[vocab_key] = normalized_to_file[normalized]
    
    return vocab_to_file, audio_files


def generate_audio_package(config: Dict[str, Any], mode: str, 
                           output_dir: Path | str) -> Dict[str, Any]:
    """Generate audio package with config JSON and placeholder audio files.
    
    Creates a directory structure with:
    - config.json: Pico-compatible configuration with pre-computed rules
    - audio/: Directory with empty .wav placeholder files
    
    Args:
        config: Loaded YAML configuration.
        mode: Mode name (e.g., 'casual', 'broadcast').
        output_dir: Output directory path (will be created if doesn't exist).
        
    Returns:
        Dict with statistics about generated package including:
        - output_dir: Path to output directory
        - config_file: Path to config.json
        - audio_dir: Path to audio directory
        - rules_count: Number of time rules generated
        - audio_files_count: Number of unique audio files
        - vocab_entries_count: Number of vocab entries
        - audio_files: List of audio filenames
    """
    import json
    
    output_path = Path(output_dir)
    audio_path = output_path / 'audio'
    
    # Create directories
    output_path.mkdir(parents=True, exist_ok=True)
    audio_path.mkdir(exist_ok=True)
    
    # Get vocab mapping
    vocab_map, audio_files = get_all_vocab_with_dedup(config)
    
    # Generate rules for all 1440 time combinations (24h x 60m)
    rules = []
    for hour in range(24):
        for minute in range(60):
            tokens = generate_phrase_tokens(config, mode, hour, minute)
            if tokens:
                rules.append({
                    'when': {'hour_24': hour, 'minute': minute},
                    'tokens': tokens
                })
    
    # Build JSON structure
    package_config = {
        'locale': config['locale'],
        'mode': mode,
        'vocab_files': vocab_map,
        'rules': rules
    }
    
    # Write config.json
    config_file = output_path / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(package_config, f, indent=2)
    
    # Create empty audio files
    audio_files_created = []
    for filename in set(vocab_map.values()):
        audio_file = audio_path / filename
        audio_file.touch()  # Create empty file
        audio_files_created.append(filename)
    
    # Return statistics
    return {
        'output_dir': str(output_path),
        'config_file': str(config_file),
        'audio_dir': str(audio_path),
        'rules_count': len(rules),
        'audio_files_count': len(audio_files_created),
        'vocab_entries_count': len(vocab_map),
        'audio_files': sorted(audio_files_created)
    }
