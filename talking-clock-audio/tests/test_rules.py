# tests/test_rules.py
"""Test rules generation and Pico-side evaluation against YAML rendered_examples.

Run with:
    pytest tests/test_rules.py -v

The tests work in two passes:
1. rules_generator.py converts the YAML to rules.json
2. pico_rules.py (the Pico evaluator) resolves tokens to filenames
3. phrase_generator.py resolves the same tokens independently
4. Both outputs are compared against each other and against the
   rendered_examples in the YAML (via text reconstruction from vocab).
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

# talking-clock-audio/
#   src/talking_clock_audio/   <- package
#   tests/                     <- this file
#   time_formats/              <- YAML files
# clock_code/                  <- pico_rules.py lives here
ROOT = Path(__file__).parent.parent
CLOCK_CODE = ROOT.parent / "clock_code"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CLOCK_CODE))

from talking_clock_audio.rules_generator import generate_rules, load_yaml
from talking_clock_audio.phrase_generator import (
    generate_phrase_tokens,
    get_all_vocab_with_dedup,
)
import pico_rules


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

YAML_FILES = {
    "en_US": ROOT / "time_formats" / "time_phrases_en_US.yaml",
    "nl_NL": ROOT / "time_formats" / "time_phrases_nl_NL.yaml",
}


def _load(locale):
    return load_yaml(YAML_FILES[locale])


def _vocab_map(config):
    vocab_map, _ = get_all_vocab_with_dedup(config)
    return vocab_map


def _text_from_tokens(token_list, vocab_map, config):
    """Reconstruct spoken text from a list of vocab keys.

    Looks up each key in the vocab section of the config to get
    the text string. Returns words joined by spaces.
    """
    vocab = config["vocab"]
    parts = []
    for key in token_list:
        section, entry = key.split(".", 1)
        # entry may be an integer string for number_words
        try:
            entry = int(entry)
        except ValueError:
            pass
        text = vocab.get(section, {}).get(entry)
        if text is not None:
            parts.append(text)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_time(time_val):
    """Parse time to (hour_24, minute) ints.

    YAML parses unquoted HH:MM as integer seconds (11:00 -> 660).
    Handle both string 'HH:MM' and integer seconds.
    """
    if isinstance(time_val, int):
        # YAML parsed HH:MM as total seconds (actually total minutes * 60? No - as H*60+M)
        # 11:00 -> 660 means 11*60 + 0 = 660
        return time_val // 60, time_val % 60
    h, m = str(time_val).split(":")
    return int(h), int(m)


def _collect_examples(config):
    """Yield (time_str, mode, expected_text) from rendered_examples."""
    for _group, times in config.get("rendered_examples", {}).items():
        for time_str, modes in times.items():
            for mode, expected_text in modes.items():
                yield time_str, mode, expected_text


# ---------------------------------------------------------------------------
# Test 1: rules_generator produces correct token lists
#   Compare generate_rules() output (via pico_rules) against
#   phrase_generator.py for every example in rendered_examples.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["en_US", "nl_NL"])
def test_rules_match_phrase_generator(locale):
    """pico_rules and phrase_generator must agree on every rendered_example."""
    config = _load(locale)
    vocab_map = _vocab_map(config)
    rules = generate_rules(config)

    failures = []

    for time_str, mode, _expected in _collect_examples(config):
        hour_24, minute = _parse_time(time_str)

        # Reference: phrase_generator output (list of vocab keys)
        ref_tokens = generate_phrase_tokens(config, mode, hour_24, minute)

        # Pico evaluator output (list of filenames)
        pico_files = pico_rules.get_audio_files(
            rules, vocab_map, mode, hour_24, minute
        )

        if ref_tokens is None and pico_files is None:
            continue

        # Convert reference tokens to filenames for comparison
        ref_files = [vocab_map.get(k) for k in ref_tokens] if ref_tokens else []

        if ref_files != pico_files:
            failures.append(
                f"{locale} {mode} {time_str}: "
                f"phrase_generator={ref_files} pico={pico_files}"
            )

    assert not failures, "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 2: pico_rules reconstructed text matches rendered_examples
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["en_US", "nl_NL"])
def test_rendered_examples_text(locale):
    """Reconstructed text from pico_rules must match rendered_examples."""
    config = _load(locale)
    vocab_map = _vocab_map(config)
    rules = generate_rules(config)

    failures = []

    for time_str, mode, expected_text in _collect_examples(config):
        hour_24, minute = _parse_time(time_str)

        pico_files = pico_rules.get_audio_files(
            rules, vocab_map, mode, hour_24, minute
        )

        if pico_files is None:
            failures.append(
                f"{locale} {mode} {time_str}: pico returned None, expected '{expected_text}'"
            )
            continue

        # Reverse-map filenames to vocab keys for text reconstruction
        file_to_key = {v: k for k, v in vocab_map.items()}
        token_keys = [file_to_key.get(f) for f in pico_files]
        reconstructed = _text_from_tokens(
            [k for k in token_keys if k], vocab_map, config
        )

        if reconstructed != expected_text:
            failures.append(
                f"{locale} {mode} {time_str}: "
                f"got '{reconstructed}' expected '{expected_text}'"
            )

    assert not failures, "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 3: rules.json size stays within safe bounds for Pico loading
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["en_US", "nl_NL"])
def test_rules_json_size(locale):
    """rules.json must be small enough to load on Pico (under 8 KB)."""
    config = _load(locale)
    rules = generate_rules(config)
    size = len(json.dumps(rules, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    assert size < 8192, f"{locale} rules.json is {size} bytes, exceeds 8 KB limit"


# ---------------------------------------------------------------------------
# Test 4: All 1440 times produce a result for every mode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["en_US", "nl_NL"])
def test_all_times_covered(locale):
    """Every hour/minute combination must resolve to a non-empty file list."""
    config = _load(locale)
    vocab_map = _vocab_map(config)
    rules = generate_rules(config)

    missing = []
    for mode in config["modes"]:
        for h in range(24):
            for m in range(60):
                files = pico_rules.get_audio_files(rules, vocab_map, mode, h, m)
                if not files:
                    missing.append(f"{locale} {mode} {h:02d}:{m:02d}")

    assert not missing, f"{len(missing)} times produced no output:\n" + "\n".join(missing[:20])