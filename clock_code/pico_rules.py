# pico_rules.py
# CircuitPython-compatible rule evaluator for talking clock.
#
# Usage:
#   rules = load_rules("/sd/en_US_lessac_medium/rules.json")
#   vocab = load_vocab("/sd/en_US_lessac_medium/vocab.json")
#   files = get_audio_files(rules, vocab, "casual", hour_24, minute)

import json


def load_rules(path):
    """Load rules.json from disk.

    Args:
        path: String path to rules.json.

    Returns:
        Parsed dict from rules.json.
    """
    with open(path, "r") as f:
        return json.load(f)


def load_vocab(path):
    """Load vocab.json from disk.

    Args:
        path: String path to vocab.json.

    Returns:
        Parsed dict mapping vocab keys to filenames.
    """
    with open(path, "r") as f:
        return json.load(f)


def _resolve_period(day_period_table, hour_24):
    """Resolve the day period vocab key suffix for the given hour.

    The day_period_table is a list of [threshold_or_null, key] pairs,
    sorted by threshold ascending with null last. The first entry where
    hour_24 < threshold wins. The null-threshold entry is the fallback.

    Args:
        day_period_table: List of [threshold_or_null, key_string] pairs.
        hour_24: Current hour (0-23).

    Returns:
        Vocab key suffix string (e.g. 'ochtends', 'am'), or None if table empty.
    """
    for entry in day_period_table:
        threshold, key = entry[0], entry[1]
        if threshold is None:
            return key
        if hour_24 < threshold:
            return key
    return None


def _compute_fields(hour_24, minute, day_period_table):
    """Compute all runtime substitution fields from raw hour and minute.

    Args:
        hour_24: Integer hour in 24h format (0-23).
        minute: Integer minute (0-59).
        day_period_table: List of [threshold_or_null, key] pairs from rules.json.

    Returns:
        Dict of substitution keys to values.
    """
    h12 = ((hour_24 + 11) % 12) + 1
    next_h12 = (h12 % 12) + 1
    m_to = 60 - minute
    period = _resolve_period(day_period_table, hour_24)

    return {
        "h24": hour_24,
        "h12": h12,
        "next_h12": next_h12,
        "m": minute,
        "m_to": m_to,
        "minutes_from_half": abs(minute - 30),
        "period": period,
    }


def _eval_condition(key, value, hour_24, minute):
    """Evaluate a single when-condition.

    Args:
        key: Condition key string (e.g. 'minute_eq', 'hour_24_lt', 'any').
        value: Condition value (integer or True).
        hour_24: Current hour (0-23).
        minute: Current minute (0-59).

    Returns:
        Boolean result.
    """
    if key == "any":
        return value is True

    last = key.rfind("_")
    field = key[:last]
    op = key[last + 1:]

    if field == "minute":
        current = minute
    elif field == "hour_24":
        current = hour_24
    else:
        return False

    if op == "eq":
        return current == value
    if op == "lt":
        return current < value
    if op == "gt":
        return current > value
    if op == "lte":
        return current <= value
    if op == "gte":
        return current >= value
    return False


def _matches_rule(rule, hour_24, minute):
    """Check if all when-conditions match.

    Args:
        rule: Dict with 'when' and 'tokens'.
        hour_24: Current hour (0-23).
        minute: Current minute (0-59).

    Returns:
        Boolean.
    """
    for key, value in rule["when"].items():
        if not _eval_condition(key, value, hour_24, minute):
            return False
    return True


def _resolve_token(token, fields, vocab):
    """Resolve a compact token string to an audio filename.

    Token format examples:
        'words.midnight'          -> vocab['words.midnight']
        'number_words.{h12}'     -> vocab['number_words.11']  (for h12=11)
        'words.{period}'         -> vocab['words.ochtends']

    Args:
        token: Compact token string from rules.json.
        fields: Dict of computed field values from _compute_fields().
        vocab: Dict mapping vocab keys to filenames.

    Returns:
        Filename string, or None if vocab key not found.
    """
    if "{" in token:
        start = token.index("{") + 1
        end = token.index("}")
        field_key = token[start:end]
        value = fields.get(field_key)
        if value is None:
            return None
        vocab_key = token[:start - 1] + str(value) + token[end + 1:]
    else:
        vocab_key = token

    return vocab.get(vocab_key)


def get_audio_files(rules, vocab, mode, hour_24, minute):
    """Get ordered list of audio filenames for a given time and mode.

    Args:
        rules: Loaded rules dict from load_rules().
        vocab: Loaded vocab dict from load_vocab().
        mode: Mode name string (e.g. 'casual', 'standard').
        hour_24: Current hour in 24h format (0-23).
        minute: Current minute (0-59).

    Returns:
        List of filename strings to play in order, or None if no rule matched.
    """
    mode_rules = rules["modes"].get(mode)
    if mode_rules is None:
        return None

    day_period_table = rules.get("day_period", [])
    fields = _compute_fields(hour_24, minute, day_period_table)

    for rule in mode_rules:
        if _matches_rule(rule, hour_24, minute):
            files = []
            for token in rule["tokens"]:
                filename = _resolve_token(token, fields, vocab)
                if filename is not None:
                    files.append(filename)
            return files

    return None
