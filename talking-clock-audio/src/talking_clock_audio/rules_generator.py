"""Compile time phrase YAML into compact runtime JSON files.

This module reads one locale YAML source file and produces compact JSON files
that can be loaded directly by the runtime phrase generator.

The generated files are designed for a small runtime that:
1. loads one locale vocabulary file
2. loads one mode rules file
3. computes a small context for the requested time
4. expands symbolic token templates into vocabulary keys

Supported runtime substitution keys
-----------------------------------
The compiler emits compact token templates that the runtime can expand:

- {h24}
    Hour in 24 hour format, from 0 to 23.

- {h12}
    Hour in 12 hour format, from 1 to 12.

- {next_h12}
    Next hour in 12 hour format, from 1 to 12.

- {m}
    Minute value, from 0 to 59.

- {m_to}
    Minutes to the next hour, from 1 to 60.

- {period}
    Locale specific day period suffix, such as 'am' or 'pm'.

Examples
--------
A YAML token such as '{hour_12_word}' becomes:
    'number_words.{h12}'

A YAML token such as '{day_period_word}' becomes:
    'words.{period}'

A YAML token such as '{quarter}' becomes:
    'words.quarter'
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)



_NUMBER_FIELDS = {
    'hour_24_word': 'h24',
    'hour_12_word': 'h12',
    'next_hour_12_word': 'next_h12',
    'minute_word': 'm',
    'minute_to_next_word': 'm_to',
}

_PLACEHOLDER_ALIASES = {
    'hour_24': 'h24',
    'hour_12': 'h12',
    'next_hour_12': 'next_h12',
    'minute': 'm',
    'minute_to_next': 'm_to',
    'day_period': 'period',
}


def _compact_token(template: str) -> str:
    """
    Convert one YAML token template into a compact runtime token.

    The source YAML uses token references such as:
    - '{hour_12_word}'
    - '{minute_word}'
    - '{quarter}'
    - '{day_period_word}'

    The compiled runtime format uses dotted vocabulary keys and a small
    placeholder vocabulary:
    - 'number_words.{h12}'
    - 'number_words.{m}'
    - 'words.quarter'
    - 'words.{period}'

    Already-qualified tokens such as 'number_words.{minute}' or
    'words.{day_period}' are passed through, but known placeholder names are
    normalized to the runtime field names used on the Pico.

    Parameters
    ----------
    template : str
        The source token string from YAML.

    Returns
    -------
    str
        The compact runtime token string.
    """
def _compact_token(template: str) -> str:
    if template.startswith('words.') or template.startswith('number_words.'):
        compact = template
        for source_name, target_name in _PLACEHOLDER_ALIASES.items():
            compact = compact.replace(f'{{{source_name}}}', f'{{{target_name}}}')
        return compact

    if not template.startswith('{'):
        return f'words.{template}'

    field_name = template.strip('{}')

    if field_name in _NUMBER_FIELDS:
        return f'number_words.{{{_NUMBER_FIELDS[field_name]}}}'

    if field_name == 'day_period_word':
        return 'words.{period}'

    if field_name in _PLACEHOLDER_ALIASES:
        return f'words.{{{_PLACEHOLDER_ALIASES[field_name]}}}'

    return f'words.{field_name}'


def _extract_day_period(config: dict[str, Any]) -> list[list[Any]]:
    """
    Extract the locale day period rules from the YAML configuration.

    The YAML source may define day periods inside:
        fields.computed.day_period

    Example source form:
        day_period:
          when_hour_24_lt_12: 'am'
          otherwise: 'pm'

    This is compiled into an ordered threshold list:
        [[12, 'am'], [None, 'pm']]

    The runtime interprets this list in order. The first matching threshold
    wins. A threshold of None acts as the fallback case.

    Parameters
    ----------
    config : dict[str, Any]
        Parsed YAML configuration.

    Returns
    -------
    list[list[Any]]
        Ordered threshold rules for runtime day period selection.
        Returns an empty list if the locale does not define day periods.
    """
    day_period_def = config.get('fields', {}).get('computed', {}).get('day_period')
    if not isinstance(day_period_def, dict):
        return []

    result: list[list[Any]] = []

    for condition, value in day_period_def.items():
        if condition == 'otherwise':
            result.append([None, value])
            continue

        if condition.startswith('when_hour_24_lt_'):
            threshold = int(condition.removeprefix('when_hour_24_lt_'))
            result.append([threshold, value])

    result.sort(key=lambda item: (item[0] is None, item[0]))
    return result


def _compile_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """
    Compile one YAML rule into the compact runtime rule format.

    Supported source rule formats are:

    1. Direct token form:
       {
           'when': {...},
           'tokens': ['{hour_12_word}', '{oclock}']
       }

    2. Pattern reference form:
       {
           'when': {...},
           'pattern': 'oclock'
       }

       In this case, the caller must resolve the pattern name before calling
       this function.

    The runtime only needs:
    - the 'when' condition object
    - the list of compact token templates

    Parameters
    ----------
    rule : dict[str, Any]
        One rule definition from the YAML mode section.

    Returns
    -------
    dict[str, Any]
        Compiled runtime rule.
    """
    if 'tokens' not in rule:
        raise KeyError("Compiled rule source must contain 'tokens'.")

    return {
        'when': dict(rule['when']),
        'tokens': [_compact_token(token) for token in rule['tokens']],
    }


def _resolve_mode_rules(mode_config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Resolve one mode configuration into an ordered list of source rules.

    Supported mode schemas are:

    1. Legacy schema:
       {
           'rule_order': ['midnight', 'noon', ...],
           'rules': {
               'midnight': {'when': ..., 'tokens': [...]},
               'noon': {'when': ..., 'tokens': [...]},
           }
       }

    2. Pattern schema with explicit ordered rule list:
       {
           'patterns': {
               'midnight': ['{midnight}'],
               'oclock': ['{hour_12_word}', '{oclock}'],
           },
           'rules': [
               {'when': {...}, 'pattern': 'midnight'},
               {'when': {...}, 'pattern': 'oclock'},
           ]
       }

    3. Direct ordered rule list:
       {
           'rules': [
               {'when': {...}, 'tokens': [...]},
               ...
           ]
       }

    Parameters
    ----------
    mode_config : dict[str, Any]
        One mode configuration from the YAML source.

    Returns
    -------
    list[dict[str, Any]]
        Ordered list of source rules, each with a concrete 'tokens' list.
    """
    source_rules = mode_config.get('rules')
    patterns = mode_config.get('patterns', {})

    if isinstance(source_rules, dict):
        rule_order = mode_config.get('rule_order')
        if rule_order is None:
            raise KeyError("Mode with dict-based 'rules' must also define 'rule_order'.")

        ordered_rules: list[dict[str, Any]] = []
        for rule_name in rule_order:
            ordered_rules.append(source_rules[rule_name])
        return ordered_rules

    if isinstance(source_rules, list):
        resolved_rules: list[dict[str, Any]] = []

        for rule in source_rules:
            if 'tokens' in rule:
                resolved_rules.append(rule)
                continue

            if 'pattern' in rule:
                pattern_name = rule['pattern']
                if pattern_name not in patterns:
                    raise KeyError(f"Unknown pattern '{pattern_name}' in mode configuration.")

                resolved_rule = {
                    'when': rule['when'],
                    'tokens': patterns[pattern_name],
                }
                resolved_rules.append(resolved_rule)
                continue

            raise KeyError("Each rule in a list-based mode schema must contain either 'tokens' or 'pattern'.")

        return resolved_rules

    if 'minute_map' in mode_config and 'patterns' in mode_config:
        return _resolve_minute_map_mode(mode_config)

    raise KeyError("Mode configuration must define 'rules' as either a dict or a list, or define 'minute_map' with 'patterns'.")


def generate_rules(config: dict[str, Any]) -> dict[str, Any]:
    """
    Compile all mode rules for one locale.

    The returned structure contains:
    - locale
    - day_period
    - modes

    Each mode contains an ordered list of compiled runtime rules.

    Parameters
    ----------
    config : dict[str, Any]
        Parsed locale YAML configuration.

    Returns
    -------
    dict[str, Any]
        Fully compiled rules structure for all modes in the locale.
    """
    modes_out: dict[str, list[dict[str, Any]]] = {}

    for mode_name, mode_config in config['modes'].items():
        source_rules = _resolve_mode_rules(mode_config)
        compiled_rules: list[dict[str, Any]] = []

        for rule in source_rules:
            compiled_rules.append(_compile_rule(rule))

        modes_out[mode_name] = compiled_rules

    return {
        'locale': config['locale'],
        'day_period': _extract_day_period(config),
        'modes': modes_out,
    }



def _resolve_minute_map_mode(mode_config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Resolve a minute-map mode configuration into an ordered list of source rules.

    Supported schema:
        {
            'patterns': {...},
            'special_cases': {
                '00:00': 'midnight',
                '12:00': 'noon',
            },
            'minute_map': {
                0: 'oclock',
                1: 'oclock',
                ...
                59: 'almost',
            },
        }

    The result is expanded into:
    - exact special-case rules first
    - exact minute rules for 0 through 59 after that

    Parameters
    ----------
    mode_config : dict[str, Any]
        One mode configuration from the YAML source.

    Returns
    -------
    list[dict[str, Any]]
        Ordered list of source rules with concrete token lists.
    """
    patterns = mode_config.get('patterns', {})
    special_cases = mode_config.get('special_cases', {})
    minute_map = mode_config.get('minute_map')

    if not isinstance(minute_map, dict):
        raise KeyError("Minute-map mode must define 'minute_map' as a dict.")

    resolved_rules: list[dict[str, Any]] = []

    for time_key, pattern_name in special_cases.items():
        hour_text, minute_text = time_key.split(':')
        hour_24 = int(hour_text)
        minute = int(minute_text)

        if pattern_name not in patterns:
            raise KeyError(f"Unknown pattern '{pattern_name}' in special_cases.")

        resolved_rules.append({
            'when': {
                'hour_24_eq': hour_24,
                'minute_eq': minute,
            },
            'tokens': patterns[pattern_name],
        })

    for minute in range(60):
        if minute not in minute_map:
            if str(minute) in minute_map:
                pattern_name = minute_map[str(minute)]
            else:
                raise KeyError(f"Minute-map mode is missing minute {minute}.")
        else:
            pattern_name = minute_map[minute]

        if pattern_name not in patterns:
            raise KeyError(f"Unknown pattern '{pattern_name}' in minute_map.")

        resolved_rules.append({
            'when': {
                'minute_eq': minute,
            },
            'tokens': patterns[pattern_name],
        })

    return resolved_rules


def generate_vocab(config: dict[str, Any]) -> dict[str, str]:
    """
    Flatten locale vocabulary into the runtime vocab.json format.

    The runtime vocabulary is a flat mapping from symbolic token key to
    audio filename.

    Expected source sections may include:
    - vocab.words
    - vocab.menu
    - vocab.toggle
    - vocab.interval
    - vocab.voice
    - vocab.mode
    - vocab.number_words

    Example output keys:
    - 'words.midnight'
    - 'menu.enter'
    - 'toggle.on'
    - 'number_words.12'

    Parameters
    ----------
    config : dict[str, Any]
        Parsed locale YAML configuration.

    Returns
    -------
    dict[str, str]
        Flat vocabulary mapping suitable for vocab.json.
    """
    vocab = config.get('vocab', {})
    flat_vocab: dict[str, str] = {}

    for section_name, section_data in vocab.items():
        if not isinstance(section_data, dict):
            continue

        for key in section_data.keys():
            symbolic_key = f'{section_name}.{key}'

            if section_name == 'number_words':
                filename = f'number_{key}.wav'
            else:
                filename = f'{section_name}_{key}.wav'

            flat_vocab[symbolic_key] = filename

    return flat_vocab


def load_yaml(yaml_path: Path | str) -> dict[str, Any]:
    """
    Load one locale YAML file.

    Parameters
    ----------
    yaml_path : Path | str
        Path to the locale YAML file.

    Returns
    -------
    dict[str, Any]
        Parsed YAML content.
    """
    with open(yaml_path, 'r', encoding='utf-8') as file_handle:
        return yaml.safe_load(file_handle)


def write_rules_json(config: dict[str, Any], output_path: Path | str) -> int:
    """
    Compile all locale rules and write them to one JSON file.

    This helper is mainly useful for debugging or inspection. The preferred
    deployment format is one rules file per mode, written by write_all_rules().

    Parameters
    ----------
    config : dict[str, Any]
        Parsed locale YAML configuration.
    output_path : Path | str
        Destination path for the combined rules JSON file.

    Returns
    -------
    int
        File size in bytes.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rules = generate_rules(config)
    content = json.dumps(rules, ensure_ascii=False, separators=(',', ':'))

    with open(output_path, 'w', encoding='utf-8') as file_handle:
        file_handle.write(content)

    return len(content.encode('utf-8'))


def write_vocab_json(config: dict[str, Any], output_path: Path | str) -> int:
    """
    Compile and write vocab.json for one locale.

    Parameters
    ----------
    config : dict[str, Any]
        Parsed locale YAML configuration.
    output_path : Path | str
        Destination path for vocab.json.

    Returns
    -------
    int
        File size in bytes.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vocab = generate_vocab(config)
    content = json.dumps(vocab, ensure_ascii=False, separators=(',', ':'))

    with open(output_path, 'w', encoding='utf-8') as file_handle:
        file_handle.write(content)

    return len(content.encode('utf-8'))


def write_all_rules(config: dict[str, Any], output_dir: Path | str) -> dict[str, int]:
    """
    Write one compact rules JSON file per mode.

    Files are written to:
        <output_dir>/rules/<mode>_rules.json

    Each file contains exactly one mode, which matches the expectation of
    the runtime phrase generator.

    Parameters
    ----------
    config : dict[str, Any]
        Parsed locale YAML configuration.
    output_dir : Path | str
        Root output directory for the locale package.

    Returns
    -------
    dict[str, int]
        Mapping from mode name to output file size in bytes.
    """
    output_dir = Path(output_dir)
    rules_dir = output_dir / 'rules'
    rules_dir.mkdir(parents=True, exist_ok=True)

    all_rules = generate_rules(config)
    sizes: dict[str, int] = {}

    for mode_name, mode_rules in all_rules['modes'].items():
        mode_document = {
            'locale': all_rules['locale'],
            'day_period': all_rules['day_period'],
            'modes': {
                mode_name: mode_rules,
            },
        }

        content = json.dumps(mode_document, ensure_ascii=False, separators=(',', ':'))
        destination = rules_dir / f'{mode_name}_rules.json'

        with open(destination, 'w', encoding='utf-8') as file_handle:
            file_handle.write(content)

        sizes[mode_name] = len(content.encode('utf-8'))
        logger.info('Wrote %s (%s bytes)', destination, sizes[mode_name])

    return sizes


def write_locale_package(config: dict[str, Any], output_dir: Path | str) -> dict[str, int]:
    """
    Write the full compiled locale package.

    The package consists of:
    - vocab.json
    - rules/operational_rules.json
    - rules/broadcast_rules.json
    - rules/standard_rules.json
    - rules/casual_rules.json

    Parameters
    ----------
    config : dict[str, Any]
        Parsed locale YAML configuration.
    output_dir : Path | str
        Output directory for the locale package.

    Returns
    -------
    dict[str, int]
        File sizes in bytes. Includes a 'vocab' entry plus one entry per mode.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sizes = {
        'vocab': write_vocab_json(config, output_dir / 'vocab.json'),
    }
    sizes.update(write_all_rules(config, output_dir))
    return sizes