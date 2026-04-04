import json
from pathlib import Path
from typing import Any


def load_vocab(vocab_path: str | Path) -> dict[str, str]:
    """
    Load a locale vocabulary file.

    The vocabulary file maps symbolic token names to audio filenames.
    Example token keys include:
    - 'words.midnight'
    - 'words.oclock'
    - 'number_words.12'

    Parameters
    ----------
    vocab_path : str | Path
        Path to the JSON vocabulary file.

    Returns
    -------
    dict[str, str]
        A mapping from symbolic token keys to audio filenames.
    """
    with open(vocab_path, 'r', encoding='utf8') as file_handle:
        return json.load(file_handle)


def load_mode_rules(rules_path: str | Path) -> dict[str, Any]:
    """
    Load one compiled mode rules file.

    A mode rules file contains the rules for one locale and one mode,
    such as broadcast, standard, operational, or casual.

    Parameters
    ----------
    rules_path : str | Path
        Path to the JSON rules file.

    Returns
    -------
    dict[str, Any]
        The parsed JSON content for the selected rules file.
    """
    with open(rules_path, 'r', encoding='utf8') as file_handle:
        return json.load(file_handle)


def build_context(hour_24: int, minute: int, day_period: list[list[Any]] | None = None) -> dict[str, Any]:
    """
    Build the computed values needed to expand rule tokens.

    The runtime only needs a very small set of derived values in order
    to expand placeholders found in compiled rule tokens.

    Supported computed values are:
    - h24: the 24 hour value
    - h12: the 12 hour value
    - next_h12: the next 12 hour value
    - m: the minute value
    - m_to: minutes until the next hour
    - period: a locale specific period such as 'am' or 'pm'

    The day_period input is expected to be a list of pairs in the form:
    [[threshold, value], [threshold, value], ...]

    Example:
    [[12, 'am'], [None, 'pm']]

    This means:
    - if hour_24 < 12, use 'am'
    - otherwise use 'pm'

    Parameters
    ----------
    hour_24 : int
        Hour in 24 hour time, from 0 to 23.
    minute : int
        Minute value, from 0 to 59.
    day_period : list[list[Any]] | None
        Optional day period mapping rules.

    Returns
    -------
    dict[str, Any]
        A dictionary containing the computed context values.
    """
    h12 = ((hour_24 + 11) % 12) + 1
    next_h12 = (h12 % 12) + 1
    m_to = 60 - minute

    period = None
    if day_period:
        for threshold, value in day_period:
            if threshold is None or hour_24 < threshold:
                period = value
                break

    return {
        'h24': hour_24,
        'h12': h12,
        'next_h12': next_h12,
        'm': minute,
        'm_to': m_to,
        'period': period,
    }


def token_to_vocab_key(token: str, context: dict[str, Any]) -> str:
    """
    Expand one token template into a concrete vocabulary key.

    Tokens may contain placeholders such as:
    - 'number_words.{h12}'
    - 'number_words.{m}'
    - 'number_words.{next_h12}'
    - 'words.{period}'

    If the token contains no placeholders, it is returned unchanged.

    Parameters
    ----------
    token : str
        A symbolic token or token template.
    context : dict[str, Any]
        Context values used to replace placeholders.

    Returns
    -------
    str
        The expanded vocabulary key.
    """
    if '{' not in token:
        return token

    result = token
    for key, value in context.items():
        result = result.replace(f'{{{key}}}', str(value))
    return result


def rule_matches(rule: dict[str, Any], hour_24: int, minute: int) -> bool:
    """
    Determine whether a compiled rule matches the provided time.

    Supported rule conditions are:
    - any
    - hour_24_eq
    - minute_eq
    - minute_lt
    - minute_gt
    - minute_lte
    - minute_gte

    Examples:
    {'when': {'minute_eq': 0}}
    {'when': {'minute_gt': 0, 'minute_lt': 10}}
    {'when': {'hour_24_eq': 12, 'minute_eq': 0}}
    {'when': {'any': True}}

    Parameters
    ----------
    rule : dict[str, Any]
        One compiled rule dictionary.
    hour_24 : int
        Hour in 24 hour time, from 0 to 23.
    minute : int
        Minute value, from 0 to 59.

    Returns
    -------
    bool
        True if the rule matches, otherwise False.
    """
    when = rule.get('when', {})

    if when.get('any') is True:
        return True

    if 'hour_24_eq' in when and hour_24 != when['hour_24_eq']:
        return False
    if 'minute_eq' in when and minute != when['minute_eq']:
        return False
    if 'minute_lt' in when and not (minute < when['minute_lt']):
        return False
    if 'minute_gt' in when and not (minute > when['minute_gt']):
        return False
    if 'minute_lte' in when and not (minute <= when['minute_lte']):
        return False
    if 'minute_gte' in when and not (minute >= when['minute_gte']):
        return False

    return True


def expand_tokens(tokens: list[str], context: dict[str, Any]) -> list[str]:
    """
    Expand a list of token templates into concrete vocabulary keys.

    Parameters
    ----------
    tokens : list[str]
        A list of symbolic token templates from a matched rule.
    context : dict[str, Any]
        Context values used to replace placeholders.

    Returns
    -------
    list[str]
        A list of expanded vocabulary keys.
    """
    return [token_to_vocab_key(token, context) for token in tokens]


def get_mode_name(mode_rules: dict[str, Any]) -> str:
    """
    Extract the single mode name from a compiled rules file.

    The expected structure is:

        {
            'locale': 'en_US',
            'modes': {
                'standard': [...]
            }
        }

    Parameters
    ----------
    mode_rules : dict[str, Any]
        Parsed compiled rules data.

    Returns
    -------
    str
        The name of the contained mode.

    Raises
    ------
    ValueError
        If the rules file does not contain exactly one mode.
    """
    modes = mode_rules.get('modes', {})
    mode_names = list(modes.keys())

    if len(mode_names) != 1:
        raise ValueError('Expected exactly one mode in the rules file.')

    return mode_names[0]


def generate_phrase_tokens(mode_rules: dict[str, Any], hour_24: int, minute: int) -> list[str] | None:
    """
    Generate expanded vocabulary keys for a given time and compiled rules file.

    This function:
    1. builds the runtime context
    2. selects the single mode contained in the rules file
    3. scans the rules in order
    4. expands the matched rule's tokens

    Parameters
    ----------
    mode_rules : dict[str, Any]
        Parsed compiled rules data for one locale and one mode.
    hour_24 : int
        Hour in 24 hour time, from 0 to 23.
    minute : int
        Minute value, from 0 to 59.

    Returns
    -------
    list[str] | None
        A list of expanded vocabulary keys if a rule matches,
        otherwise None.
    """
    day_period = mode_rules.get('day_period', [])
    context = build_context(hour_24, minute, day_period)

    mode_name = get_mode_name(mode_rules)
    rules = mode_rules['modes'][mode_name]

    for rule in rules:
        if rule_matches(rule, hour_24, minute):
            return expand_tokens(rule['tokens'], context)

    return None


def resolve_audio_files(vocab: dict[str, str], tokens: list[str]) -> list[str]:
    """
    Resolve expanded vocabulary keys to audio filenames.

    Parameters
    ----------
    vocab : dict[str, str]
        Vocabulary mapping from symbolic token keys to filenames.
    tokens : list[str]
        Expanded vocabulary keys.

    Returns
    -------
    list[str]
        Audio filenames corresponding to the provided tokens.

    Raises
    ------
    KeyError
        If any expanded token is missing from the vocabulary.
    """
    return [vocab[token] for token in tokens]


def generate_audio_sequence(
    vocab_path: str | Path,
    rules_path: str | Path,
    hour_24: int,
    minute: int,
) -> list[str]:
    """
    Load the selected locale assets and generate the audio sequence for a time.

    This is a convenience wrapper that:
    1. loads the vocabulary file
    2. loads the selected mode rules file
    3. generates the expanded tokens
    4. resolves those tokens to audio filenames

    Parameters
    ----------
    vocab_path : str | Path
        Path to the locale vocabulary JSON file.
    rules_path : str | Path
        Path to the selected mode rules JSON file.
    hour_24 : int
        Hour in 24 hour time, from 0 to 23.
    minute : int
        Minute value, from 0 to 59.

    Returns
    -------
    list[str]
        Ordered list of audio filenames to play.

    Raises
    ------
    ValueError
        If no rule matches the given time.
    """
    vocab = load_vocab(vocab_path)
    mode_rules = load_mode_rules(rules_path)

    tokens = generate_phrase_tokens(mode_rules, hour_24, minute)
    if tokens is None:
        raise ValueError(f'No matching rule found for {hour_24:02d}:{minute:02d}.')

    return resolve_audio_files(vocab, tokens)