# tests/test_phrase_generator.py

"""Unit tests for phrase_generator module."""
import pytest
import json
import tempfile
from pathlib import Path
from talking_clock_audio.phrase_generator import (
    slugify,
    load_time_phrases,
    evaluate_condition,
    matches_rule,
    find_matching_rule,
    evaluate_computed_field,
    compute_all_fields,
    expand_token,
    generate_phrase_tokens,
    get_all_vocab_with_dedup,
    generate_audio_package,  # Add this line
)


# Fixtures

@pytest.fixture
def sample_config():
    """Minimal config for testing."""
    return {
        'locale': 'en_TEST',
        'vocab': {
            'words': {
                'am': 'a.m.',
                'pm': 'p.m.',
                'oclock': "o'clock",
                'past': 'past',
            },
            'number_words': {
                0: 'zero',
                1: 'one',
                11: 'eleven',
                30: 'thirty',
            }
        },
        'fields': {
            'computed': {
                'hour_12': '((hour_24 + 11) mod 12) + 1',
                'hour_12_word': 'number_words[hour_12]',
                'minute_word': 'number_words[minute]',
                'day_period': {
                    'when_hour_24_lt_12': 'am',
                    'otherwise': 'pm'
                },
                'day_period_word': 'words[day_period]',
            }
        },
        'modes': {
            'test_mode': {
                'rule_order': ['on_hour', 'default'],
                'rules': {
                    'on_hour': {
                        'when': {'minute_eq': 0},
                        'tokens': ['{hour_12_word}', '{oclock}', '{day_period_word}']
                    },
                    'default': {
                        'when': {'any': True},
                        'tokens': ['{hour_12_word}', '{minute_word}', '{day_period_word}']
                    }
                }
            }
        }
    }


# Tests for slugify

def test_slugify_apostrophe():
    """Test slugify converts apostrophes to underscores."""
    assert slugify("o'clock") == "o_clock"
    assert slugify("'s avonds") == "s_avonds"


def test_slugify_spaces():
    """Test slugify converts spaces to underscores."""
    assert slugify("twenty one") == "twenty_one"
    assert slugify("half past") == "half_past"


def test_slugify_periods():
    """Test slugify handles periods."""
    assert slugify("a.m.") == "a_m"
    assert slugify("p.m.") == "p_m"


def test_slugify_multiple_underscores():
    """Test slugify removes consecutive underscores."""
    assert slugify("test  __  value") == "test_value"


def test_slugify_case():
    """Test slugify converts to lowercase."""
    assert slugify("Hello World") == "hello_world"
    assert slugify("UPPERCASE") == "uppercase"


# Tests for evaluate_condition

def test_evaluate_condition_any():
    """Test 'any' condition always returns True."""
    assert evaluate_condition('any', True, 11, 30) is True


def test_evaluate_condition_minute_eq():
    """Test minute equality condition."""
    assert evaluate_condition('minute_eq', 30, 11, 30) is True
    assert evaluate_condition('minute_eq', 0, 11, 30) is False


def test_evaluate_condition_minute_lt():
    """Test minute less than condition."""
    assert evaluate_condition('minute_lt', 10, 11, 5) is True
    assert evaluate_condition('minute_lt', 10, 11, 15) is False


def test_evaluate_condition_minute_gt():
    """Test minute greater than condition."""
    assert evaluate_condition('minute_gt', 30, 11, 45) is True
    assert evaluate_condition('minute_gt', 30, 11, 15) is False


def test_evaluate_condition_hour_24_eq():
    """Test hour equality condition."""
    assert evaluate_condition('hour_24_eq', 0, 0, 0) is True
    assert evaluate_condition('hour_24_eq', 12, 11, 0) is False


def test_evaluate_condition_invalid_field():
    """Test invalid field raises ValueError."""
    with pytest.raises(ValueError, match="Unknown field"):
        evaluate_condition('invalid_field_eq', 0, 11, 30)


def test_evaluate_condition_invalid_operator():
    """Test invalid operator raises ValueError."""
    with pytest.raises(ValueError, match="Unknown operator"):
        evaluate_condition('minute_invalid', 0, 11, 30)


# Tests for matches_rule

def test_matches_rule_single_condition():
    """Test rule matching with single condition."""
    rule = {'when': {'minute_eq': 0}, 'tokens': []}
    assert matches_rule(rule, 11, 0) is True
    assert matches_rule(rule, 11, 30) is False


def test_matches_rule_multiple_conditions():
    """Test rule matching with multiple conditions (AND logic)."""
    rule = {'when': {'hour_24_eq': 0, 'minute_eq': 0}, 'tokens': []}
    assert matches_rule(rule, 0, 0) is True
    assert matches_rule(rule, 0, 30) is False
    assert matches_rule(rule, 11, 0) is False


def test_matches_rule_any_condition():
    """Test rule matching with 'any' condition."""
    rule = {'when': {'any': True}, 'tokens': []}
    assert matches_rule(rule, 11, 30) is True
    assert matches_rule(rule, 0, 0) is True


# Tests for find_matching_rule

def test_find_matching_rule_first_match(sample_config):
    """Test finding first matching rule."""
    mode_config = sample_config['modes']['test_mode']
    rule_name, rule = find_matching_rule(mode_config, 11, 0)
    
    assert rule_name == 'on_hour'
    assert rule is not None


def test_find_matching_rule_fallback(sample_config):
    """Test finding fallback rule when first doesn't match."""
    mode_config = sample_config['modes']['test_mode']
    rule_name, rule = find_matching_rule(mode_config, 11, 30)
    
    assert rule_name == 'default'
    assert rule is not None


def test_find_matching_rule_no_match():
    """Test when no rule matches."""
    mode_config = {
        'rule_order': ['impossible'],
        'rules': {
            'impossible': {
                'when': {'hour_24_eq': 99},
                'tokens': []
            }
        }
    }
    rule_name, rule = find_matching_rule(mode_config, 11, 30)
    
    assert rule_name is None
    assert rule is None


# Tests for compute_all_fields

def test_compute_all_fields_simple(sample_config):
    """Test computing fields for a simple time."""
    computed = compute_all_fields(sample_config, 11, 30)
    
    assert computed['hour_24'] == 11
    assert computed['minute'] == 30
    assert computed['hour_12'] == 11
    assert 'hour_12_word' in computed


def test_compute_all_fields_midnight(sample_config):
    """Test computing fields for midnight."""
    computed = compute_all_fields(sample_config, 0, 0)
    
    assert computed['hour_24'] == 0
    assert computed['minute'] == 0
    assert computed['hour_12'] == 12  # Midnight is 12 in 12h format


def test_compute_all_fields_afternoon(sample_config):
    """Test computing fields for afternoon time."""
    computed = compute_all_fields(sample_config, 13, 30)
    
    assert computed['hour_24'] == 13
    assert computed['hour_12'] == 1
    assert computed['day_period'] == 'pm'


def test_compute_all_fields_day_period_morning(sample_config):
    """Test day period computation for morning."""
    computed = compute_all_fields(sample_config, 6, 0)
    assert computed['day_period'] == 'am'


def test_compute_all_fields_day_period_afternoon(sample_config):
    """Test day period computation for afternoon."""
    computed = compute_all_fields(sample_config, 18, 0)
    assert computed['day_period'] == 'pm'


# Tests for expand_token

def test_expand_token_literal_word(sample_config):
    """Test expanding a literal word token."""
    computed = {}
    token = expand_token('past', computed, sample_config)
    assert token == 'words.past'


def test_expand_token_computed_field(sample_config):
    """Test expanding a computed field token."""
    computed = {'hour_12_word': 'number_words[11]'}
    token = expand_token('{hour_12_word}', computed, sample_config)
    assert token == 'number_words.11'


def test_expand_token_direct_word_reference(sample_config):
    """Test expanding a direct word reference."""
    computed = compute_all_fields(sample_config, 11, 0)
    token = expand_token('{day_period_word}', computed, sample_config)
    assert token == 'words.am'

# Tests for generate_phrase_tokens

def test_generate_phrase_tokens_on_hour(sample_config):
    """Test generating tokens for on-the-hour time."""
    tokens = generate_phrase_tokens(sample_config, 'test_mode', 11, 0)
    
    assert tokens is not None
    assert len(tokens) == 3
    assert 'number_words.11' in tokens
    assert 'words.oclock' in tokens
    assert 'words.am' in tokens


def test_generate_phrase_tokens_with_minutes(sample_config):
    """Test generating tokens for time with minutes."""
    tokens = generate_phrase_tokens(sample_config, 'test_mode', 11, 30)
    
    assert tokens is not None
    assert len(tokens) == 3
    assert 'number_words.11' in tokens
    assert 'number_words.30' in tokens
    assert 'words.am' in tokens


def test_generate_phrase_tokens_afternoon(sample_config):
    """Test generating tokens for afternoon time."""
    tokens = generate_phrase_tokens(sample_config, 'test_mode', 13, 30)
    
    assert tokens is not None
    assert 'words.pm' in tokens


# Tests for get_all_vocab_with_dedup

def test_get_all_vocab_basic(sample_config):
    """Test basic vocab extraction."""
    vocab_map, audio_files = get_all_vocab_with_dedup(sample_config)
    
    assert len(vocab_map) > 0
    assert len(audio_files) > 0
    assert 'words.am' in vocab_map
    assert 'number_words.0' in vocab_map


def test_get_all_vocab_filenames(sample_config):
    """Test vocab filenames are properly formatted."""
    vocab_map, audio_files = get_all_vocab_with_dedup(sample_config)
    
    # Check word filenames
    am_file = vocab_map['words.am']
    assert am_file.startswith('word_')
    assert am_file.endswith('.wav')
    
    # Check number filenames
    zero_file = vocab_map['number_words.0']
    assert zero_file.startswith('number_')
    assert zero_file.endswith('.wav')


def test_get_all_vocab_deduplication():
    """Test that duplicate text produces single audio file."""
    config = {
        'vocab': {
            'words': {
                'word1': 'duplicate',
                'word2': 'duplicate',  # Same text, different key
                'word3': 'unique',
            },
            'number_words': {}
        }
    }
    
    vocab_map, audio_files = get_all_vocab_with_dedup(config)
    
    # Both keys should map to same file
    assert vocab_map['words.word1'] == vocab_map['words.word2']
    
    # Should only have 2 unique audio files
    assert len(audio_files) == 2


def test_get_all_vocab_case_insensitive():
    """Test that deduplication is case-insensitive."""
    config = {
        'vocab': {
            'words': {
                'word1': 'Hello',
                'word2': 'hello',  # Different case
            },
            'number_words': {}
        }
    }
    
    vocab_map, audio_files = get_all_vocab_with_dedup(config)
    
    # Both keys should map to same file (case-insensitive dedup)
    assert vocab_map['words.word1'] == vocab_map['words.word2']
    assert len(audio_files) == 1


def test_get_all_vocab_preserves_punctuation():
    """Test that whitespace and punctuation differences create separate files."""
    config = {
        'vocab': {
            'words': {
                'word1': "o'clock",
                'word2': "oclock",  # No apostrophe
            },
            'number_words': {}
        }
    }
    
    vocab_map, audio_files = get_all_vocab_with_dedup(config)
    
    # Different punctuation should create different files
    assert vocab_map['words.word1'] != vocab_map['words.word2']
    assert len(audio_files) == 2


# Integration tests

def test_end_to_end_phrase_generation(sample_config):
    """Test complete flow from time to phrase text."""
    # Generate tokens
    tokens = generate_phrase_tokens(sample_config, 'test_mode', 11, 30)
    
    # Get vocab mapping
    vocab_map, audio_files = get_all_vocab_with_dedup(sample_config)
    
    # Convert tokens to text
    phrase = []
    for token in tokens:
        filename = vocab_map[token]
        text = audio_files[filename]
        phrase.append(text)
    
    # Check result
    assert len(phrase) == 3
    assert 'eleven' in phrase
    assert 'thirty' in phrase
    assert 'a.m.' in phrase

# Add to tests/test_phrase_generator.py




def test_generate_audio_package_creates_structure(sample_config):
    """Test that generate_audio_package creates correct directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        stats = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        # Check directories exist
        assert Path(stats['output_dir']).exists()
        assert Path(stats['audio_dir']).exists()
        assert Path(stats['config_file']).exists()


def test_generate_audio_package_creates_config_json(sample_config):
    """Test that config.json is created with correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        stats = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        # Load and verify config.json
        with open(stats['config_file'], 'r') as f:
            config = json.load(f)
        
        assert config['locale'] == 'en_TEST'
        assert config['mode'] == 'test_mode'
        assert 'vocab_files' in config
        assert 'rules' in config


def test_generate_audio_package_creates_audio_files(sample_config):
    """Test that audio files are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        stats = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        audio_dir = Path(stats['audio_dir'])
        
        # Check that audio files exist
        assert stats['audio_files_count'] > 0
        
        # Verify files actually exist on disk
        for filename in stats['audio_files']:
            assert (audio_dir / filename).exists()


def test_generate_audio_package_generates_all_rules(sample_config):
    """Test that rules are generated for all time combinations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        stats = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        # Should generate rules for 24 * 60 = 1440 time combinations
        assert stats['rules_count'] == 1440


def test_generate_audio_package_rules_are_valid(sample_config):
    """Test that generated rules have correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        stats = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        with open(stats['config_file'], 'r') as f:
            config = json.load(f)
        
        # Check first rule structure
        rule = config['rules'][0]
        assert 'when' in rule
        assert 'tokens' in rule
        assert 'hour_24' in rule['when']
        assert 'minute' in rule['when']
        assert isinstance(rule['tokens'], list)


def test_generate_audio_package_stats_accuracy(sample_config):
    """Test that returned statistics are accurate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        stats = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        # Count actual files
        audio_dir = Path(stats['audio_dir'])
        actual_files = list(audio_dir.glob('*.wav'))
        
        assert len(actual_files) == stats['audio_files_count']
        assert stats['rules_count'] > 0
        assert stats['vocab_entries_count'] > 0


def test_generate_audio_package_idempotent(sample_config):
    """Test that running generate_audio_package twice doesn't break."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'test_package'
        
        # First run
        stats1 = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        # Second run (should overwrite)
        stats2 = generate_audio_package(sample_config, 'test_mode', output_dir)
        
        # Stats should be identical
        assert stats1['rules_count'] == stats2['rules_count']
        assert stats1['audio_files_count'] == stats2['audio_files_count']