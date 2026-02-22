# src/talking_clock_audio/tts_generator.py

"""TTS audio generation using Piper.

Generates audio files from text using Piper TTS voices.
"""

import json
import logging
import math
import struct
import wave
from pathlib import Path
from typing import Dict, Any, Optional

from piper import PiperVoice

from .phrase_generator import get_all_vocab_with_dedup

logger = logging.getLogger(__name__)

DEFAULT_SPEAKER_THRESHOLD = 16000
DEFAULT_HIGHPASS_CUTOFF = 300


def highpass(samples: list[int], rate: int, cutoff: int) -> list[int]:
    """Apply a first-order high-pass filter to audio samples.

    Attenuates frequencies below the cutoff, leaving higher frequencies
    unchanged. Used to remove low-frequency content that small speakers
    cannot reproduce cleanly.

    Args:
        samples: List of signed 16-bit integer samples.
        rate: Sample rate in Hz.
        cutoff: Filter cutoff frequency in Hz.

    Returns:
        List of filtered signed 16-bit integer samples.
    """
    rc = 1.0 / (2.0 * math.pi * cutoff)
    dt = 1.0 / rate
    alpha = rc / (rc + dt)
    out = []
    prev_out = 0.0
    prev_in = float(samples[0])
    for s in samples:
        y = alpha * (prev_out + s - prev_in)
        out.append(max(-32768, min(32767, int(y))))
        prev_out = y
        prev_in = float(s)
    return out


def soft_limit(samples: list[int], threshold: int) -> list[int]:
    """Apply a soft limiter to audio samples.

    Samples below the threshold are passed through unchanged. Samples
    above the threshold are compressed using an exponential curve so
    that peaks are rounded rather than hard-clipped.

    Args:
        samples: List of signed 16-bit integer samples.
        threshold: Level above which compression begins (0-32767).

    Returns:
        List of compressed signed 16-bit integer samples.
    """
    headroom = 32767 - threshold
    out = []
    for s in samples:
        if abs(s) <= threshold:
            out.append(s)
        else:
            sign = 1 if s > 0 else -1
            excess = abs(s) - threshold
            compressed = threshold + headroom * (1 - math.exp(-excess / headroom))
            out.append(sign * int(compressed))
    return out


def apply_speaker_processing(wav_path: Path, threshold: Optional[int],
                              cutoff: Optional[int]) -> None:
    """Apply high-pass filter and soft limiting to a WAV file in place.

    The high-pass filter is applied first, then the soft limiter.

    Args:
        wav_path: Path to the WAV file to process.
        threshold: Soft limit threshold (0-32767), or None to skip.
        cutoff: High-pass filter cutoff in Hz, or None to skip.
    """
    with wave.open(str(wav_path), 'rb') as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())

    samples = list(struct.unpack('<' + 'h' * (len(frames) // 2), frames))

    if cutoff is not None:
        samples = highpass(samples, params.framerate, cutoff)

    if threshold is not None:
        samples = soft_limit(samples, threshold)

    with wave.open(str(wav_path), 'wb') as w:
        w.setparams(params)
        w.writeframes(struct.pack('<' + 'h' * len(samples), *samples))


def generate_audio_file(text: str, output_path: Path | str,
                        voice: PiperVoice,
                        speaker_threshold: Optional[int] = DEFAULT_SPEAKER_THRESHOLD,
                        highpass_cutoff: Optional[int] = DEFAULT_HIGHPASS_CUTOFF) -> bool:
    """Generate audio file from text using Piper TTS.

    Args:
        text: Text to convert to speech.
        output_path: Path where .wav file should be saved.
        voice: Loaded PiperVoice object.
        speaker_threshold: Soft limit threshold (0-32767). Set to None to
            disable. Default is 16000, tuned for small 4-ohm speakers.
        highpass_cutoff: High-pass filter cutoff in Hz. Set to None to
            disable. Default is 300Hz, tuned for small 4-ohm speakers.

    Returns:
        True if successful, False if failed.
    """
    try:
        output_path = Path(output_path)
        with wave.open(str(output_path), 'wb') as wav_file:
            voice.synthesize_wav(text, wav_file)

        if speaker_threshold is not None or highpass_cutoff is not None:
            apply_speaker_processing(output_path, speaker_threshold, highpass_cutoff)
            logger.debug(
                f"Applied speaker processing "
                f"(highpass={highpass_cutoff}Hz, threshold={speaker_threshold}): "
                f"{output_path}"
            )

        logger.debug(f"Generated audio: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate audio for '{text}': {e}")
        return False


def generate_audio_package_with_tts(config: Dict[str, Any],
                                     voice_model_path: Path | str,
                                     output_dir: Path | str = None,
                                     speaker_threshold: Optional[int] = DEFAULT_SPEAKER_THRESHOLD,
                                     highpass_cutoff: Optional[int] = DEFAULT_HIGHPASS_CUTOFF) -> Dict[str, Any]:
    """Generate audio package with real TTS-generated audio files.

    Creates a directory structure with:
    - vocab.json: Key-to-filename mapping covering all modes
    - audio/: Directory with real .wav files generated by Piper TTS
    - rules/: Written separately by write_all_rules() in rules_generator

    Vocab is mode-independent: all modes for a given locale share the same
    word list, so this function generates audio for the full vocab once.

    Args:
        config: Loaded YAML configuration.
        voice_model_path: Path to .onnx voice model file.
        output_dir: Output directory path. If None, derives from model filename
            as audio/{locale}_{voice}_{quality}.
        speaker_threshold: Soft limit threshold (0-32767). Set to None to
            disable. Default is 16000, tuned for small 4-ohm speakers.
        highpass_cutoff: High-pass filter cutoff in Hz. Set to None to
            disable. Default is 300Hz, tuned for small 4-ohm speakers.

    Returns:
        Dict with statistics including success/failure counts and output paths.
    """
    voice_model_path = Path(voice_model_path)
    locale = config['locale']

    model_filename = voice_model_path.stem

    try:
        parts = model_filename.split('-')
        if len(parts) >= 3:
            voice_name = parts[1]
            quality = parts[2]
        else:
            voice_name = 'unknown'
            quality = 'unknown'
    except:
        voice_name = 'unknown'
        quality = 'unknown'

    if output_dir is None:
        output_dir = f"audio/{locale}_{voice_name}_{quality}"

    output_path = Path(output_dir)
    audio_path = output_path / 'audio'

    output_path.mkdir(parents=True, exist_ok=True)
    audio_path.mkdir(exist_ok=True)

    logger.info(f"Loading voice model: {voice_model_path}")
    voice = PiperVoice.load(str(voice_model_path))

    vocab_map, audio_files = get_all_vocab_with_dedup(config)

    success_count = 0
    failure_count = 0
    failed_files = []

    if highpass_cutoff is not None:
        logger.info(f"High-pass filter enabled (cutoff={highpass_cutoff}Hz)")
    else:
        logger.info("High-pass filter disabled")

    if speaker_threshold is not None:
        logger.info(f"Soft limiter enabled (threshold={speaker_threshold})")
    else:
        logger.info("Soft limiter disabled")

    logger.info(f"Generating {len(audio_files)} audio files with TTS...")

    for filename, text in audio_files.items():
        audio_file_path = audio_path / filename

        success = generate_audio_file(
            text, audio_file_path, voice,
            speaker_threshold=speaker_threshold,
            highpass_cutoff=highpass_cutoff
        )

        if success:
            success_count += 1
        else:
            failure_count += 1
            failed_files.append((filename, text))
            audio_file_path.touch()

    vocab_file_path = output_path / 'vocab.json'
    with open(vocab_file_path, 'w') as f:
        json.dump(vocab_map, f, separators=(',', ':'))

    stats = {
        'output_dir': str(output_path),
        'vocab_file': str(vocab_file_path),
        'audio_dir': str(audio_path),
        'total_audio_files': len(audio_files),
        'success_count': success_count,
        'failure_count': failure_count,
        'failed_files': failed_files,
        'speaker_threshold': speaker_threshold,
        'highpass_cutoff': highpass_cutoff,
    }

    if failure_count > 0:
        logger.warning(f"Failed to generate {failure_count} audio files")
        for filename, text in failed_files:
            logger.warning(f"  {filename}: '{text}'")

    logger.info(f"Successfully generated {success_count}/{len(audio_files)} audio files")

    return stats
