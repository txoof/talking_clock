# src/talking_clock_audio/debug_generator.py

"""Speaker test audio generation.

Generates triplets of WAV files from a debug YAML configuration.
Each variant produces:
  001_label.wav        - spoken label, normalized + processed per variant
  002_a.wav            - sentence A, normalized then processed per variant
  003_b.wav ...        - additional sentences, same processing

Normalization (peak target 28000) is applied before the soft limiter so
that filter/limiter comparisons are not confounded by differences in raw
Piper output level. All files including the label go through the same
processing so the label sounds consistent with the sentences that follow.
"""

import logging
import struct
import wave
from pathlib import Path
from typing import Any, Optional

import yaml
from piper import PiperVoice

from .tts_generator import generate_audio_file, apply_speaker_processing

logger = logging.getLogger(__name__)

NORMALIZE_TARGET = 28000


def load_debug_yaml(yaml_path: Path | str) -> dict[str, Any]:
    """Load and validate a debug YAML file.

    Args:
        yaml_path: Path to the debug YAML file.

    Returns:
        Parsed YAML dict.

    Raises:
        ValueError: If required keys are missing or malformed.
    """
    with open(yaml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if "sentences" not in config or not isinstance(config["sentences"], list):
        raise ValueError("debug YAML must contain a 'sentences' list")
    if len(config["sentences"]) < 1:
        raise ValueError("'sentences' must contain at least one entry")
    if "variants" not in config or not isinstance(config["variants"], list):
        raise ValueError("debug YAML must contain a 'variants' list")
    for v in config["variants"]:
        if "name" not in v:
            raise ValueError(f"variant missing 'name': {v}")
        if "label" not in v:
            raise ValueError(f"variant '{v['name']}' missing 'label'")

    return config


def normalize_wav(wav_path: Path, target_peak: int = NORMALIZE_TARGET) -> None:
    """Scale WAV samples so the peak amplitude reaches target_peak.

    Applied in place. If the file is silent (all zeros), no change is made.

    Args:
        wav_path: Path to a 16-bit mono WAV file.
        target_peak: Desired peak sample value (0-32767). Default 28000.
    """
    with wave.open(str(wav_path), "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())

    samples = list(struct.unpack("<" + "h" * (len(frames) // 2), frames))

    peak = max(abs(s) for s in samples)
    if peak == 0:
        return

    scale = target_peak / peak
    samples = [max(-32768, min(32767, int(s * scale))) for s in samples]

    with wave.open(str(wav_path), "wb") as w:
        w.setparams(params)
        w.writeframes(struct.pack("<" + "h" * len(samples), *samples))


def generate_debug_package(
    config: dict[str, Any],
    voice_model_path: Path | str,
    output_dir: Path | str = "./audio/debug",
) -> dict[str, Any]:
    """Generate speaker test audio for all variants in a debug config.

    For each variant, creates a subdirectory under output_dir containing:
      001_label.wav       - label, normalized + variant processing
      002_a.wav           - first sentence, normalized + variant processing
      003_b.wav           - second sentence, normalized + variant processing
      ...

    Args:
        config: Parsed debug YAML dict from load_debug_yaml().
        voice_model_path: Path to .onnx Piper voice model.
        output_dir: Root output directory. Default ./audio/debug.

    Returns:
        Dict with per-variant stats and overall success/failure counts.
    """
    voice_model_path = Path(voice_model_path)
    output_path = Path(output_dir)

    logger.info(f"Loading voice model: {voice_model_path}")
    voice = PiperVoice.load(str(voice_model_path))

    sentences = config["sentences"]
    variants = config["variants"]
    letter_names = [chr(ord("a") + i) for i in range(len(sentences))]

    total_success = 0
    total_failure = 0
    variant_results = []

    for variant in variants:
        name = variant["name"]
        label = variant["label"]
        cutoff = variant.get("highpass_cutoff")
        threshold = variant.get("speaker_threshold")

        variant_dir = output_path / name
        variant_dir.mkdir(parents=True, exist_ok=True)

        results = {"name": name, "files": [], "errors": []}

        # 001 - label, normalized + processed same as sentences
        label_path = variant_dir / "001_label.wav"
        ok = generate_audio_file(
            label, label_path, voice,
            speaker_threshold=None,
            highpass_cutoff=None,
        )
        if ok:
            normalize_wav(label_path)
            if cutoff is not None or threshold is not None:
                apply_speaker_processing(label_path, threshold, cutoff)
            results["files"].append(str(label_path))
            total_success += 1
        else:
            results["errors"].append(str(label_path))
            total_failure += 1

        # 002... - sentences, normalized then processed
        for i, (sentence, letter) in enumerate(zip(sentences, letter_names), start=2):
            filename = f"{i:03d}_{letter}.wav"
            sentence_path = variant_dir / filename

            ok = generate_audio_file(
                sentence, sentence_path, voice,
                speaker_threshold=None,
                highpass_cutoff=None,
            )
            if not ok:
                results["errors"].append(str(sentence_path))
                total_failure += 1
                continue

            normalize_wav(sentence_path)

            if cutoff is not None or threshold is not None:
                apply_speaker_processing(sentence_path, threshold, cutoff)

            results["files"].append(str(sentence_path))
            total_success += 1

        variant_results.append(results)
        logger.info(
            f"Variant '{name}': {len(results['files'])} files, "
            f"{len(results['errors'])} errors"
        )

    return {
        "output_dir": str(output_path),
        "variants": variant_results,
        "total_success": total_success,
        "total_failure": total_failure,
    }