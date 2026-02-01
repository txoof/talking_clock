# src/talking_clock_audio/voice_manager.py

"""Voice model management for Piper TTS.

Handles fetching voice model information from Hugging Face, caching,
and parsing voice model paths into structured data.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from huggingface_hub import list_repo_files

logger = logging.getLogger(__name__)

CACHE_FILE = Path("./models/.cache/repo_files.json")
REPO_ID = "rhasspy/piper-voices"


@dataclass
class VoiceModel:
    """Represents a Piper TTS voice model.
    
    Attributes:
        language: Two-letter language code (e.g., 'en', 'de', 'fr').
        locale: Full locale code including country (e.g., 'en_US', 'de_DE').
        voice_name: Name of the voice/speaker (e.g., 'lessac', 'thorsten').
        quality: Quality level of the model ('low', 'medium', 'high').
        onnx_path: Path to the .onnx model file in the repository.
        config_path: Path to the .onnx.json config file in the repository.
    """
    language: str
    locale: str
    voice_name: str
    quality: str
    onnx_path: str
    config_path: str


# Cache management functions

def _is_cache_valid(cache_data: dict[str, Any], cache_duration_hours: int) -> bool:
    """Check if cached data is within valid time window.
    
    Args:
        cache_data: Dictionary containing 'timestamp' and 'files' keys.
        cache_duration_hours: Maximum age of cache in hours.
        
    Returns:
        True if cache is still valid, False if expired.
    """
    timestamp_str = cache_data.get('timestamp')
    if not timestamp_str:
        return False
    
    cache_time = datetime.fromisoformat(timestamp_str)
    age = datetime.now() - cache_time
    
    return age < timedelta(hours=cache_duration_hours)


def _load_cache() -> dict[str, Any] | None:
    """Load cache from disk if it exists.
    
    Returns:
        Dictionary with 'timestamp' and 'files', or None if cache doesn't exist
        or is invalid.
    """
    if not CACHE_FILE.exists():
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_cache(files: list[str]) -> None:
    """Save file list to cache with current timestamp.
    
    Args:
        files: List of file paths from Hugging Face repository.
    """
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'files': files
    }
    
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Cached {len(files)} files to {CACHE_FILE}")
    except IOError as e:
        logger.error(f"Failed to save cache: {e}")


def get_voice_paths(cache_duration_hours: int = 24) -> list[str]:
    """Get list of voice model paths from Hugging Face repository.
    
    Fetches file list from rhasspy/piper-voices repository with caching.
    Cache is stored at ./models/.cache/repo_files.json relative to current
    working directory.
    
    If cached data exists and is fresh (within cache_duration_hours), returns
    cached data. Otherwise fetches fresh data from Hugging Face and updates cache.
    
    If network is unavailable but stale cache exists, logs warning and returns
    stale cached data.
    
    Args:
        cache_duration_hours: Maximum age of cache in hours before refresh.
            Defaults to 24 hours.
            
    Returns:
        List of file paths in the Hugging Face repository.
        
    Raises:
        Exception: If network is unavailable and no cache exists.
        
    Example:
        >>> paths = get_voice_paths()
        >>> print(f"Found {len(paths)} files")
    """
    # Check for valid cached data
    cache_data = _load_cache()
    if cache_data and _is_cache_valid(cache_data, cache_duration_hours):
        logger.info(f"Using cached data from {CACHE_FILE}")
        return cache_data['files']
    
    # Try to fetch fresh data
    try:
        logger.info(f"Fetching file list from {REPO_ID}...")
        files = list(list_repo_files(REPO_ID))
        _save_cache(files)
        return files
    except Exception as e:
        # Network failed - fall back to stale cache if available
        if cache_data:
            logger.warning(
                f"Hugging Face endpoint unreachable: {e}. "
                f"Using stale cached data from {cache_data.get('timestamp')}"
            )
            return cache_data['files']
        
        # No cache available and network failed
        logger.error(f"Failed to fetch from Hugging Face and no cache available: {e}")
        raise Exception(
            f"Cannot reach Hugging Face repository and no cached data exists. "
            f"Check your internet connection."
        ) from e


# Voice parsing functions

def parse_voice_paths(paths: list[str]) -> list[VoiceModel]:
    """Parse Hugging Face repository paths and extract valid voice models.
    
    Only includes models where both .onnx and .onnx.json files exist.
    Logs warnings for paths that don't match expected structure.
    
    Expected path format: lang/locale/name/quality/file.onnx
    Example: en/en_US/lessac/high/en_US-lessac-high.onnx
    
    Args:
        paths: List of file paths from Hugging Face repository.
        
    Returns:
        List of VoiceModel objects for valid voice models that have
        both .onnx and .onnx.json files present.
        
    Example:
        >>> paths = [
        ...     'en/en_US/lessac/high/en_US-lessac-high.onnx',
        ...     'en/en_US/lessac/high/en_US-lessac-high.onnx.json',
        ... ]
        >>> models = parse_voice_paths(paths)
        >>> models[0].locale
        'en_US'
    """
    onnx_files = [p for p in paths if p.endswith('.onnx') and not p.endswith('.onnx.json')]
    
    models = []
    
    for onnx_path in onnx_files:
        config_path = f"{onnx_path}.json"
        if config_path not in paths:
            logger.warning(f"Missing config file for {onnx_path}")
            continue
        
        parts = onnx_path.split('/')
        
        if len(parts) != 5:
            logger.warning(f"Unexpected path structure: {onnx_path}")
            continue
        
        language, locale, voice_name, quality, filename = parts
        
        models.append(VoiceModel(
            language=language,
            locale=locale,
            voice_name=voice_name,
            quality=quality,
            onnx_path=onnx_path,
            config_path=config_path
        ))
    
    return models


# High-level API functions

def get_available_voices(cache_duration_hours: int = 24) -> list[VoiceModel]:
    """Get all available voice models from Hugging Face repository.
    
    Combines fetching, caching, and parsing into a single convenient function.
    
    Args:
        cache_duration_hours: Maximum age of cache in hours before refresh.
            Defaults to 24 hours.
            
    Returns:
        List of VoiceModel objects for all available voices.
        
    Example:
        >>> voices = get_available_voices()
        >>> print(f"Found {len(voices)} voices")
        >>> english_voices = [v for v in voices if v.language == 'en']
    """
    paths = get_voice_paths(cache_duration_hours)
    return parse_voice_paths(paths)
