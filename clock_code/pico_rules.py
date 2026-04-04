import json


"""Helpers for resolving compiled talking-clock rule files on the Pico.

This module is intentionally small and avoids dynamic expression evaluation.
It supports both:
1. rule-list mode files, where a mode is an ordered list of rules
2. minute-map mode files, where a mode defines patterns, special_cases,
   and minute_map
"""


def load_rules(path):
    """Load one compiled rules JSON file from disk."""
    with open(path, 'r') as f:
        return json.load(f)


def load_vocab(path):
    """Load one compiled vocab JSON file from disk."""
    with open(path, 'r') as f:
        return json.load(f)


def _resolve_period(day_period_table, hour_24):
    """Resolve the locale day-period key for the given 24-hour value."""
    for entry in day_period_table:
        threshold, key = entry[0], entry[1]
        if threshold is None:
            return key
        if hour_24 < threshold:
            return key
    return None


def _compute_fields(hour_24, minute, day_period_table):
    """Compute the small set of runtime substitution fields."""
    h12 = ((hour_24 + 11) % 12) + 1
    next_h12 = (h12 % 12) + 1
    m_to = 60 - minute
    period = _resolve_period(day_period_table, hour_24)

    return {
        'h24': hour_24,
        'h12': h12,
        'next_h12': next_h12,
        'm': minute,
        'm_to': m_to,
        'period': period,
    }


def _eval_condition(key, value, hour_24, minute):
    """Evaluate a single compiled condition against a time value."""
    if key == 'any':
        return value is True

    last = key.rfind('_')
    if last == -1:
        return False

    field = key[:last]
    op = key[last + 1:]

    if field == 'minute':
        current = minute
    elif field == 'hour_24':
        current = hour_24
    else:
        return False

    if op == 'eq':
        return current == value
    if op == 'lt':
        return current < value
    if op == 'gt':
        return current > value
    if op == 'lte':
        return current <= value
    if op == 'gte':
        return current >= value

    return False


def _matches_rule(rule, hour_24, minute):
    """Return True if all conditions in a rule match the provided time."""
    when = rule.get('when', {})
    for key, value in when.items():
        if not _eval_condition(key, value, hour_24, minute):
            return False
    return True


def _resolve_token(token, fields, vocab):
    """Resolve one compiled token into a vocab filename."""
    if '{' in token:
        start = token.index('{') + 1
        end = token.index('}')
        field_key = token[start:end]
        value = fields.get(field_key)
        if value is None:
            return None
        vocab_key = token[:start - 1] + str(value) + token[end + 1:]
    else:
        vocab_key = token

    return vocab.get(vocab_key)


def _get_single_mode_config(rules_doc, requested_mode):
    """Return the config for the requested mode from a compiled rules file."""
    modes = rules_doc.get('modes', {})
    if requested_mode in modes:
        return modes[requested_mode]

    if len(modes) == 1:
        only_mode = next(iter(modes))
        return modes[only_mode]

    return None


def _resolve_rule_list_mode(mode_config, fields, vocab, hour_24, minute):
    """Resolve audio files for a mode stored as an ordered list of rules."""
    for rule in mode_config:
        if _matches_rule(rule, hour_24, minute):
            files = []
            for token in rule['tokens']:
                filename = _resolve_token(token, fields, vocab)
                if filename is not None:
                    files.append(filename)
            return files
    return None


def _resolve_minute_map_mode(mode_config, fields, vocab, hour_24, minute):
    """Resolve audio files for a mode stored as patterns plus a minute map."""
    patterns = mode_config.get('patterns', {})
    special_cases = mode_config.get('special_cases', {})
    minute_map = mode_config.get('minute_map', {})

    time_key = '{:02d}:{:02d}'.format(hour_24, minute)
    pattern_name = special_cases.get(time_key)
    if pattern_name is None:
        pattern_name = minute_map.get(minute)
        if pattern_name is None:
            pattern_name = minute_map.get(str(minute))

    if pattern_name is None:
        return None

    tokens = patterns.get(pattern_name)
    if tokens is None:
        return None

    files = []
    for token in tokens:
        filename = _resolve_token(token, fields, vocab)
        if filename is not None:
            files.append(filename)
    return files


def get_audio_files(rules_doc, vocab, mode, hour_24, minute):
    """Resolve the ordered list of audio filenames for one time phrase.

    Parameters
    ----------
    rules_doc : dict
        Parsed JSON document for one compiled rules file.
    vocab : dict
        Parsed vocab.json mapping symbolic tokens to wav filenames.
    mode : str
        Requested mode name such as 'standard' or 'casual'.
    hour_24 : int
        Hour in 24-hour format.
    minute : int
        Minute value.

    Returns
    -------
    list[str] | None
        Ordered wav filenames, or None if no rule matched.
    """
    mode_config = _get_single_mode_config(rules_doc, mode)
    if mode_config is None:
        return None

    day_period_table = rules_doc.get('day_period', [])
    fields = _compute_fields(hour_24, minute, day_period_table)

    if isinstance(mode_config, list):
        return _resolve_rule_list_mode(mode_config, fields, vocab, hour_24, minute)

    if isinstance(mode_config, dict) and 'minute_map' in mode_config and 'patterns' in mode_config:
        return _resolve_minute_map_mode(mode_config, fields, vocab, hour_24, minute)

    return None