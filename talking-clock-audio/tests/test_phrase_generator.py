import json
from pathlib import Path

import pytest

from talking_clock_audio.phrase_generator import (
    build_context,
    expand_tokens,
    generate_audio_sequence,
    generate_phrase_tokens,
    get_mode_name,
    resolve_audio_files,
    rule_matches,
    token_to_vocab_key,
)


@pytest.fixture
def vocab_data() -> dict[str, str]:
    """Return a small vocabulary mapping for test cases."""
    return {
        'words.midnight': 'word_midnight.wav',
        'words.noon': 'word_noon.wav',
        'words.oclock': 'word_o_clock.wav',
        'words.oh': 'word_oh.wav',
        'words.am': 'word_a_m.wav',
        'words.pm': 'word_p_m.wav',
        'number_words.1': 'number_one.wav',
        'number_words.8': 'number_eight.wav',
        'number_words.9': 'number_nine.wav',
        'number_words.12': 'number_twelve.wav',
    }


@pytest.fixture
def standard_rules_data() -> dict:
    """Return a compiled standard mode ruleset for testing."""
    return {
        'locale': 'en_US',
        'day_period': [
            [12, 'am'],
            [None, 'pm'],
        ],
        'modes': {
            'standard': [
                {
                    'when': {
                        'hour_24_eq': 0,
                        'minute_eq': 0,
                    },
                    'tokens': ['words.midnight'],
                },
                {
                    'when': {
                        'hour_24_eq': 12,
                        'minute_eq': 0,
                    },
                    'tokens': ['words.noon'],
                },
                {
                    'when': {
                        'minute_eq': 0,
                    },
                    'tokens': ['number_words.{h12}', 'words.oclock'],
                },
                {
                    'when': {
                        'minute_gt': 0,
                        'minute_lt': 10,
                    },
                    'tokens': ['number_words.{h12}', 'words.oh', 'number_words.{m}'],
                },
                {
                    'when': {
                        'any': True,
                    },
                    'tokens': ['number_words.{h12}', 'number_words.{m}'],
                },
            ]
        },
    }


@pytest.fixture
def broadcast_rules_data() -> dict:
    """Return a compiled broadcast mode ruleset for testing."""
    return {
        'locale': 'en_US',
        'day_period': [
            [12, 'am'],
            [None, 'pm'],
        ],
        'modes': {
            'broadcast': [
                {
                    'when': {
                        'hour_24_eq': 0,
                        'minute_eq': 0,
                    },
                    'tokens': ['words.midnight'],
                },
                {
                    'when': {
                        'hour_24_eq': 12,
                        'minute_eq': 0,
                    },
                    'tokens': ['words.noon'],
                },
                {
                    'when': {
                        'minute_eq': 0,
                    },
                    'tokens': ['number_words.{h12}', 'words.oclock', 'words.{period}'],
                },
                {
                    'when': {
                        'minute_gt': 0,
                        'minute_lt': 10,
                    },
                    'tokens': ['number_words.{h12}', 'words.oh', 'number_words.{m}', 'words.{period}'],
                },
                {
                    'when': {
                        'any': True,
                    },
                    'tokens': ['number_words.{h12}', 'number_words.{m}', 'words.{period}'],
                },
            ]
        },
    }


@pytest.fixture
def temp_json_files(
    tmp_path: Path,
    vocab_data: dict[str, str],
    standard_rules_data: dict,
    broadcast_rules_data: dict,
) -> dict[str, Path]:
    """Write test JSON files to a temporary directory and return their paths."""
    vocab_path = tmp_path / 'vocab.json'
    standard_path = tmp_path / 'standard_rules.json'
    broadcast_path = tmp_path / 'broadcast_rules.json'

    vocab_path.write_text(json.dumps(vocab_data), encoding='utf8')
    standard_path.write_text(json.dumps(standard_rules_data), encoding='utf8')
    broadcast_path.write_text(json.dumps(broadcast_rules_data), encoding='utf8')

    return {
        'vocab': vocab_path,
        'standard': standard_path,
        'broadcast': broadcast_path,
    }


def test_build_context_am() -> None:
    """build_context should compute derived values correctly for morning times."""
    context = build_context(8, 9, [[12, 'am'], [None, 'pm']])

    assert context == {
        'h24': 8,
        'h12': 8,
        'next_h12': 9,
        'm': 9,
        'm_to': 51,
        'period': 'am',
    }


def test_build_context_pm() -> None:
    """build_context should compute derived values correctly for evening times."""
    context = build_context(20, 9, [[12, 'am'], [None, 'pm']])

    assert context == {
        'h24': 20,
        'h12': 8,
        'next_h12': 9,
        'm': 9,
        'm_to': 51,
        'period': 'pm',
    }


def test_token_to_vocab_key_expands_placeholders() -> None:
    """token_to_vocab_key should replace placeholders using the runtime context."""
    context = {
        'h24': 20,
        'h12': 8,
        'next_h12': 9,
        'm': 9,
        'm_to': 51,
        'period': 'pm',
    }

    assert token_to_vocab_key('number_words.{h12}', context) == 'number_words.8'
    assert token_to_vocab_key('number_words.{m}', context) == 'number_words.9'
    assert token_to_vocab_key('words.{period}', context) == 'words.pm'
    assert token_to_vocab_key('words.noon', context) == 'words.noon'


def test_expand_tokens() -> None:
    """expand_tokens should expand every token in the provided list."""
    context = {
        'h24': 20,
        'h12': 8,
        'next_h12': 9,
        'm': 9,
        'm_to': 51,
        'period': 'pm',
    }

    tokens = ['number_words.{h12}', 'words.oh', 'number_words.{m}', 'words.{period}']

    assert expand_tokens(tokens, context) == [
        'number_words.8',
        'words.oh',
        'number_words.9',
        'words.pm',
    ]


def test_rule_matches_exact_hour_and_minute() -> None:
    """rule_matches should support exact hour and minute checks."""
    rule = {
        'when': {
            'hour_24_eq': 12,
            'minute_eq': 0,
        }
    }

    assert rule_matches(rule, 12, 0) is True
    assert rule_matches(rule, 12, 1) is False
    assert rule_matches(rule, 11, 0) is False


def test_rule_matches_minute_range() -> None:
    """rule_matches should support strict minute range comparisons."""
    rule = {
        'when': {
            'minute_gt': 0,
            'minute_lt': 10,
        }
    }

    assert rule_matches(rule, 8, 1) is True
    assert rule_matches(rule, 8, 9) is True
    assert rule_matches(rule, 8, 0) is False
    assert rule_matches(rule, 8, 10) is False


def test_get_mode_name_returns_single_mode(standard_rules_data: dict) -> None:
    """get_mode_name should return the only mode defined in a rules file."""
    assert get_mode_name(standard_rules_data) == 'standard'


def test_get_mode_name_raises_for_multiple_modes() -> None:
    """get_mode_name should fail if the rules file contains multiple modes."""
    mode_rules = {
        'modes': {
            'standard': [],
            'broadcast': [],
        }
    }

    with pytest.raises(ValueError, match='Expected exactly one mode'):
        get_mode_name(mode_rules)


def test_generate_phrase_tokens_midnight(standard_rules_data: dict) -> None:
    """generate_phrase_tokens should return the midnight token sequence."""
    tokens = generate_phrase_tokens(standard_rules_data, 0, 0)
    assert tokens == ['words.midnight']


def test_generate_phrase_tokens_noon(standard_rules_data: dict) -> None:
    """generate_phrase_tokens should return the noon token sequence."""
    tokens = generate_phrase_tokens(standard_rules_data, 12, 0)
    assert tokens == ['words.noon']


def test_generate_phrase_tokens_standard_oclock(standard_rules_data: dict) -> None:
    """generate_phrase_tokens should expand the oclock pattern correctly."""
    tokens = generate_phrase_tokens(standard_rules_data, 8, 0)
    assert tokens == ['number_words.8', 'words.oclock']


def test_generate_phrase_tokens_standard_oh_minute(standard_rules_data: dict) -> None:
    """generate_phrase_tokens should expand the low minute pattern correctly."""
    tokens = generate_phrase_tokens(standard_rules_data, 8, 9)
    assert tokens == ['number_words.8', 'words.oh', 'number_words.9']


def test_generate_phrase_tokens_broadcast_pm(broadcast_rules_data: dict) -> None:
    """generate_phrase_tokens should expand the broadcast pattern with pm."""
    tokens = generate_phrase_tokens(broadcast_rules_data, 20, 9)
    assert tokens == ['number_words.8', 'words.oh', 'number_words.9', 'words.pm']


def test_resolve_audio_files(vocab_data: dict[str, str]) -> None:
    """resolve_audio_files should map expanded token keys to filenames."""
    tokens = ['number_words.8', 'words.oh', 'number_words.9']
    assert resolve_audio_files(vocab_data, tokens) == [
        'number_eight.wav',
        'word_oh.wav',
        'number_nine.wav',
    ]


def test_resolve_audio_files_raises_for_unknown_token(vocab_data: dict[str, str]) -> None:
    """resolve_audio_files should raise KeyError for missing vocabulary tokens."""
    with pytest.raises(KeyError):
        resolve_audio_files(vocab_data, ['words.does_not_exist'])


def test_generate_audio_sequence_standard_midnight(temp_json_files: dict[str, Path]) -> None:
    """generate_audio_sequence should produce the correct files for midnight."""
    result = generate_audio_sequence(
        temp_json_files['vocab'],
        temp_json_files['standard'],
        0,
        0,
    )

    assert result == ['word_midnight.wav']


def test_generate_audio_sequence_standard_noon(temp_json_files: dict[str, Path]) -> None:
    """generate_audio_sequence should produce the correct files for noon."""
    result = generate_audio_sequence(
        temp_json_files['vocab'],
        temp_json_files['standard'],
        12,
        0,
    )

    assert result == ['word_noon.wav']


def test_generate_audio_sequence_standard_oclock(temp_json_files: dict[str, Path]) -> None:
    """generate_audio_sequence should produce the correct files for an exact hour."""
    result = generate_audio_sequence(
        temp_json_files['vocab'],
        temp_json_files['standard'],
        8,
        0,
    )

    assert result == ['number_eight.wav', 'word_o_clock.wav']


def test_generate_audio_sequence_standard_oh_minute(temp_json_files: dict[str, Path]) -> None:
    """generate_audio_sequence should produce the correct files for a low minute value."""
    result = generate_audio_sequence(
        temp_json_files['vocab'],
        temp_json_files['standard'],
        8,
        9,
    )

    assert result == ['number_eight.wav', 'word_oh.wav', 'number_nine.wav']


def test_generate_audio_sequence_broadcast_pm(temp_json_files: dict[str, Path]) -> None:
    """generate_audio_sequence should include the correct day period in broadcast mode."""
    result = generate_audio_sequence(
        temp_json_files['vocab'],
        temp_json_files['broadcast'],
        20,
        9,
    )

    assert result == [
        'number_eight.wav',
        'word_oh.wav',
        'number_nine.wav',
        'word_p_m.wav',
    ]