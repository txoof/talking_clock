# src/talking_clock_audio/rules_generator.py

"""Generate compact rules.json files from time phrase YAML configurations.

Token templates use dotted vocab keys: 'number_words.{h12}', 'words.half', etc.

Supported runtime substitution keys:
    h24      - hour in 24h format (0-23)
    h12      - 12h hour (1-12)
    next_h12 - next 12h hour (1-12), wraps at 12
    m        - minute (0-59)
    m_to     - minutes to next hour (1-60)
    period   - day period vocab key suffix, resolved via locale's day_period table

The day_period is encoded as an ordered threshold list in rules.json:
    [[6, "nachts"], [12, "ochtends"], [18, "middags"], [null, "avonds"]]
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


_NUMBER_FIELDS = {
    "hour_24_word":        "h24",
    "hour_12_word":        "h12",
    "next_hour_12_word":   "next_h12",
    "minute_word":         "m",
    "minute_to_next_word": "m_to",
    "minutes_from_half_word": "minutes_from_half",
}


def _compact_token(template: str) -> str:
    """Convert a YAML token template to compact runtime format.

    Args:
        template: Token template string from YAML (e.g. '{hour_12_word}').

    Returns:
        Compact token string for rules.json (e.g. 'number_words.{h12}').
    """
    if not template.startswith("{"):
        return f"words.{template}"

    field_name = template.strip("{}")

    if field_name in _NUMBER_FIELDS:
        return f"number_words.{{{_NUMBER_FIELDS[field_name]}}}"

    if field_name == "day_period_word":
        return "words.{period}"

    return f"words.{field_name}"


def _extract_day_period(config: dict[str, Any]) -> list:
    """Extract day_period conditional as an ordered threshold list.

    Args:
        config: Loaded YAML configuration dict.

    Returns:
        List of [threshold_or_null, vocab_key_suffix] pairs, sorted by threshold.
        Returns empty list if no day_period field is defined.
    """
    day_period_def = config.get("fields", {}).get("computed", {}).get("day_period")
    if not isinstance(day_period_def, dict):
        return []

    result = []
    for condition, value in day_period_def.items():
        if condition == "otherwise":
            result.append([None, value])
        elif condition.startswith("when_hour_24_lt_"):
            threshold = int(condition.removeprefix("when_hour_24_lt_"))
            result.append([threshold, value])

    result.sort(key=lambda x: (x[0] is None, x[0]))
    return result


def generate_rules(config: dict[str, Any]) -> dict[str, Any]:
    """Generate compact rules structure from a loaded YAML config.

    Args:
        config: Loaded YAML configuration dict.

    Returns:
        Dict with locale, day_period table, and modes with ordered rule lists.
    """
    modes_out: dict[str, list] = {}

    for mode_name, mode_config in config["modes"].items():
        rule_order = mode_config["rule_order"]
        rules = mode_config["rules"]
        rules_out = []

        for rule_name in rule_order:
            rule = rules[rule_name]
            rules_out.append({
                "when": dict(rule["when"]),
                "tokens": [_compact_token(t) for t in rule["tokens"]],
            })

        modes_out[mode_name] = rules_out

    return {
        "locale": config["locale"],
        "day_period": _extract_day_period(config),
        "modes": modes_out,
    }


def write_rules_json(config: dict[str, Any], output_path: Path | str) -> int:
    """Generate and write rules.json from a YAML config.

    Args:
        config: Loaded YAML configuration dict.
        output_path: Destination file path for rules.json.

    Returns:
        File size in bytes.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rules = generate_rules(config)
    content = json.dumps(rules, ensure_ascii=False, separators=(",", ":"))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return len(content.encode("utf-8"))


def load_yaml(yaml_path: Path | str) -> dict[str, Any]:
    """Load a time phrases YAML file."""
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_all_rules(config: dict[str, Any], output_dir: Path | str) -> dict[str, int]:
    """Write one rules.json file per mode into output_dir/rules/.

    Args:
        config: Loaded YAML configuration dict.
        output_dir: Root output directory (e.g. audio/en_US_lessac_medium).
            A rules/ subdirectory will be created inside it.

    Returns:
        Dict mapping mode name to file size in bytes for each file written.
    """
    rules_dir = Path(output_dir) / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    all_rules = generate_rules(config)
    sizes = {}

    for mode_name, mode_rules in all_rules["modes"].items():
        mode_doc = {
            "locale": all_rules["locale"],
            "day_period": all_rules["day_period"],
            "modes": {mode_name: mode_rules},
        }
        content = json.dumps(mode_doc, ensure_ascii=False, separators=(",", ":"))
        dest = rules_dir / f"{mode_name}_rules.json"
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        sizes[mode_name] = len(content.encode("utf-8"))
        logger.info(f"Wrote {dest} ({sizes[mode_name]} bytes)")

    return sizes
