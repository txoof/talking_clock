import json
from pathlib import Path

import pytest

from talking_clock_audio.rules_generator import (
    _compact_token,
    _compile_rule,
    _extract_day_period,
    generate_rules,
    generate_vocab,
    load_yaml,
    write_all_rules,
    write_locale_package,
    write_rules_json,
    write_vocab_json,
)


@pytest.fixture
def sample_config() -> dict:
    """Return a small locale configuration for compiler tests."""
    return {
        'locale': 'en_US',
        'vocab': {
            'words': {
                'midnight': 'word_midnight.wav',
                'noon': 'word_noon.wav',
                'oclock': 'word_o_clock.wav',
                'oh': 'word_oh.wav',
                'am': 'word_a_m.wav',
                'pm': 'word_p_m.wav',
                'quarter': 'word_quarter.wav',
                'past': 'word_past.wav',
                'to': 'word_to.wav',
                'half': 'word_half.wav',
                'zero': 'word_zero.wav',
                'hundred': 'word_hundred.wav',
                'hours': 'word_hours.wav',
            },
            'mode': {
                'standard': 'word_standard.wav',
                'broadcast': 'word_broadcast.wav',
            },
            'number_words': {
                0: 'word_zero.wav',
                1: 'number_one.wav',
                8: 'number_eight.wav',
                9: 'number_nine.wav',
                12: 'number_twelve.wav',
                20: 'number_twenty.wav',
            },
        },
        'fields': {
            'computed': {
                'day_period': {
                    'when_hour_24_lt_12': 'am',
                    'otherwise': 'pm',
                }
            }
        },
        'modes': {
            'standard': {
                'rule_order': [
                    'midnight',
                    'noon',
                    'oclock',
                    'minute_lt_10',
                    'hour_minute',
                ],
                'rules': {
                    'midnight': {
                        'when': {
                            'hour_24_eq': 0,
                            'minute_eq': 0,
                        },
                        'tokens': ['{midnight}'],
                    },
                    'noon': {
                        'when': {
                            'hour_24_eq': 12,
                            'minute_eq': 0,
                        },
                        'tokens': ['{noon}'],
                    },
                    'oclock': {
                        'when': {
                            'minute_eq': 0,
                        },
                        'tokens': ['{hour_12_word}', '{oclock}'],
                    },
                    'minute_lt_10': {
                        'when': {
                            'minute_lt': 10,
                            'minute_gt': 0,
                        },
                        'tokens': ['{hour_12_word}', '{oh}', '{minute_word}'],
                    },
                    'hour_minute': {
                        'when': {
                            'any': True,
                        },
                        'tokens': ['{hour_12_word}', '{minute_word}'],
                    },
                },
            },
            'broadcast': {
                'rule_order': [
                    'midnight',
                    'noon',
                    'oclock',
                    'minute_lt_10',
                    'hour_minute',
                ],
                'rules': {
                    'midnight': {
                        'when': {
                            'hour_24_eq': 0,
                            'minute_eq': 0,
                        },
                        'tokens': ['{midnight}'],
                    },
                    'noon': {
                        'when': {
                            'hour_24_eq': 12,
                            'minute_eq': 0,
                        },
                        'tokens': ['{noon}'],
                    },
                    'oclock': {
                        'when': {
                            'minute_eq': 0,
                        },
                        'tokens': ['{hour_12_word}', '{oclock}', '{day_period_word}'],
                    },
                    'minute_lt_10': {
                        'when': {
                            'minute_lt': 10,
                            'minute_gt': 0,
                        },
                        'tokens': ['{hour_12_word}', '{oh}', '{minute_word}', '{day_period_word}'],
                    },
                    'hour_minute': {
                        'when': {
                            'any': True,
                        },
                        'tokens': ['{hour_12_word}', '{minute_word}', '{day_period_word}'],
                    },
                },
            },
        },
    }


def test_compact_token_maps_number_fields() -> None:
    """_compact_token should map computed number fields to runtime placeholders."""
    assert _compact_token('{hour_24_word}') == 'number_words.{h24}'
    assert _compact_token('{hour_12_word}') == 'number_words.{h12}'
    assert _compact_token('{next_hour_12_word}') == 'number_words.{next_h12}'
    assert _compact_token('{minute_word}') == 'number_words.{m}'
    assert _compact_token('{minute_to_next_word}') == 'number_words.{m_to}'


def test_compact_token_maps_day_period_word() -> None:
    """_compact_token should map day period references to the runtime period placeholder."""
    assert _compact_token('{day_period_word}') == 'words.{period}'


def test_compact_token_maps_literal_word_references() -> None:
    """_compact_token should map literal word references into the words namespace."""
    assert _compact_token('{midnight}') == 'words.midnight'
    assert _compact_token('{quarter}') == 'words.quarter'
    assert _compact_token('oclock') == 'words.oclock'


def test_extract_day_period_returns_compiled_thresholds(sample_config: dict) -> None:
    """_extract_day_period should compile YAML day period rules into threshold form."""
    result = _extract_day_period(sample_config)
    assert result == [
        [12, 'am'],
        [None, 'pm'],
    ]


def test_extract_day_period_returns_empty_list_when_missing() -> None:
    """_extract_day_period should return an empty list when no day period exists."""
    assert _extract_day_period({'locale': 'en_US'}) == []


def test_compile_rule_converts_tokens_and_preserves_conditions() -> None:
    """_compile_rule should preserve conditions and compact token templates."""
    source_rule = {
        'when': {
            'minute_gt': 0,
            'minute_lt': 10,
        },
        'tokens': ['{hour_12_word}', '{oh}', '{minute_word}'],
    }

    compiled = _compile_rule(source_rule)

    assert compiled == {
        'when': {
            'minute_gt': 0,
            'minute_lt': 10,
        },
        'tokens': [
            'number_words.{h12}',
            'words.oh',
            'number_words.{m}',
        ],
    }


def test_generate_vocab_flattens_sections(sample_config: dict) -> None:
    """generate_vocab should flatten nested vocab sections into dotted keys."""
    vocab = generate_vocab(sample_config)

    assert vocab['words.midnight'] == 'word_midnight.wav'
    assert vocab['words.oclock'] == 'word_o_clock.wav'
    assert vocab['mode.standard'] == 'word_standard.wav'
    assert vocab['number_words.8'] == 'number_eight.wav'
    assert vocab['number_words.20'] == 'number_twenty.wav'


def test_generate_rules_compiles_all_modes(sample_config: dict) -> None:
    """generate_rules should compile all configured modes into runtime format."""
    compiled = generate_rules(sample_config)

    assert compiled['locale'] == 'en_US'
    assert compiled['day_period'] == [
        [12, 'am'],
        [None, 'pm'],
    ]
    assert set(compiled['modes'].keys()) == {'standard', 'broadcast'}

    standard_rules = compiled['modes']['standard']
    broadcast_rules = compiled['modes']['broadcast']

    assert standard_rules[0] == {
        'when': {
            'hour_24_eq': 0,
            'minute_eq': 0,
        },
        'tokens': ['words.midnight'],
    }

    assert standard_rules[2] == {
        'when': {
            'minute_eq': 0,
        },
        'tokens': ['number_words.{h12}', 'words.oclock'],
    }

    assert broadcast_rules[3] == {
        'when': {
            'minute_lt': 10,
            'minute_gt': 0,
        },
        'tokens': [
            'number_words.{h12}',
            'words.oh',
            'number_words.{m}',
            'words.{period}',
        ],
    }


def test_write_vocab_json_writes_expected_file(sample_config: dict, tmp_path: Path) -> None:
    """write_vocab_json should write a compact vocab file."""
    output_path = tmp_path / 'vocab.json'

    size = write_vocab_json(sample_config, output_path)

    assert output_path.exists()
    assert size > 0

    loaded = json.loads(output_path.read_text(encoding='utf8'))
    assert loaded['words.midnight'] == 'word_midnight.wav'
    assert loaded['number_words.12'] == 'number_twelve.wav'


def test_write_rules_json_writes_combined_rules_file(sample_config: dict, tmp_path: Path) -> None:
    """write_rules_json should write one combined rules file containing all modes."""
    output_path = tmp_path / 'rules.json'

    size = write_rules_json(sample_config, output_path)

    assert output_path.exists()
    assert size > 0

    loaded = json.loads(output_path.read_text(encoding='utf8'))
    assert loaded['locale'] == 'en_US'
    assert 'standard' in loaded['modes']
    assert 'broadcast' in loaded['modes']


def test_write_all_rules_writes_one_file_per_mode(sample_config: dict, tmp_path: Path) -> None:
    """write_all_rules should create one rules file per mode under the rules directory."""
    sizes = write_all_rules(sample_config, tmp_path)

    assert set(sizes.keys()) == {'standard', 'broadcast'}
    assert all(value > 0 for value in sizes.values())

    standard_path = tmp_path / 'rules' / 'standard_rules.json'
    broadcast_path = tmp_path / 'rules' / 'broadcast_rules.json'

    assert standard_path.exists()
    assert broadcast_path.exists()

    standard_data = json.loads(standard_path.read_text(encoding='utf8'))
    broadcast_data = json.loads(broadcast_path.read_text(encoding='utf8'))

    assert list(standard_data['modes'].keys()) == ['standard']
    assert list(broadcast_data['modes'].keys()) == ['broadcast']

    assert standard_data['day_period'] == [
        [12, 'am'],
        [None, 'pm'],
    ]
    assert broadcast_data['day_period'] == [
        [12, 'am'],
        [None, 'pm'],
    ]


def test_write_locale_package_writes_vocab_and_rules(sample_config: dict, tmp_path: Path) -> None:
    """write_locale_package should create a complete locale package."""
    sizes = write_locale_package(sample_config, tmp_path)

    assert 'vocab' in sizes
    assert 'standard' in sizes
    assert 'broadcast' in sizes
    assert all(value > 0 for value in sizes.values())

    assert (tmp_path / 'vocab.json').exists()
    assert (tmp_path / 'rules' / 'standard_rules.json').exists()
    assert (tmp_path / 'rules' / 'broadcast_rules.json').exists()


def test_load_yaml_reads_yaml_file(tmp_path: Path) -> None:
    """load_yaml should read and parse a YAML file."""
    yaml_path = tmp_path / 'en_US.yaml'
    yaml_path.write_text(
        '\n'.join([
            'locale: en_US',
            'vocab:',
            '  words:',
            '    midnight: word_midnight.wav',
            'modes: {}',
        ]),
        encoding='utf8',
    )

    loaded = load_yaml(yaml_path)

    assert loaded['locale'] == 'en_US'
    assert loaded['vocab']['words']['midnight'] == 'word_midnight.wav'
    assert loaded['modes'] == {}