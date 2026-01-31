# tests/test_voice_manager.py

"""Unit tests for voice_manager module."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from talking_clock_audio.voice_manager import (
    VoiceModel,
    _is_cache_valid,
    _load_cache,
    _save_cache,
    parse_voice_paths,
    get_voice_paths,
    get_available_voices,
)


# Test data fixtures

@pytest.fixture
def sample_voice_paths():
    """Sample voice paths matching Hugging Face structure."""
    return [
        'en/en_US/lessac/high/en_US-lessac-high.onnx',
        'en/en_US/lessac/high/en_US-lessac-high.onnx.json',
        'en/en_GB/alan/medium/en_GB-alan-medium.onnx',
        'en/en_GB/alan/medium/en_GB-alan-medium.onnx.json',
        'de/de_DE/thorsten/low/de_DE-thorsten-low.onnx',
        'de/de_DE/thorsten/low/de_DE-thorsten-low.onnx.json',
        'is/is_IS/bui/medium/is_IS-bui-medium.onnx',
        'is/is_IS/bui/medium/is_IS-bui-medium.onnx.json',
    ]


@pytest.fixture
def sample_cache_data():
    """Sample cache data structure."""
    return {
        'timestamp': datetime.now().isoformat(),
        'files': [
            'en/en_US/lessac/high/en_US-lessac-high.onnx',
            'en/en_US/lessac/high/en_US-lessac-high.onnx.json',
        ]
    }


@pytest.fixture
def old_cache_data():
    """Cache data that is 25 hours old."""
    old_time = datetime.now() - timedelta(hours=25)
    return {
        'timestamp': old_time.isoformat(),
        'files': ['old/file.onnx']
    }


# Tests for VoiceModel dataclass

def test_voice_model_creation():
    """Test VoiceModel can be created with all required fields."""
    model = VoiceModel(
        language='en',
        locale='en_US',
        voice_name='lessac',
        quality='high',
        onnx_path='en/en_US/lessac/high/en_US-lessac-high.onnx',
        config_path='en/en_US/lessac/high/en_US-lessac-high.onnx.json'
    )
    
    assert model.language == 'en'
    assert model.locale == 'en_US'
    assert model.voice_name == 'lessac'
    assert model.quality == 'high'


# Tests for cache validation

def test_is_cache_valid_fresh_cache(sample_cache_data):
    """Test cache validation returns True for fresh cache."""
    assert _is_cache_valid(sample_cache_data, cache_duration_hours=24) is True


def test_is_cache_valid_stale_cache(old_cache_data):
    """Test cache validation returns False for expired cache."""
    assert _is_cache_valid(old_cache_data, cache_duration_hours=24) is False


def test_is_cache_valid_missing_timestamp():
    """Test cache validation returns False when timestamp is missing."""
    cache_data = {'files': ['some/file.onnx']}
    assert _is_cache_valid(cache_data, cache_duration_hours=24) is False


def test_is_cache_valid_custom_duration(sample_cache_data):
    """Test cache validation respects custom duration."""
    # Fresh cache should be valid with 48 hour window
    assert _is_cache_valid(sample_cache_data, cache_duration_hours=48) is True


# Tests for cache loading

@patch('pathlib.Path.exists')
def test_load_cache_file_not_exists(mock_exists):
    """Test loading cache when file doesn't exist."""
    mock_exists.return_value = False
    assert _load_cache() is None


@patch('pathlib.Path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='{"timestamp": "2024-01-01T12:00:00", "files": []}')
def test_load_cache_success(mock_file, mock_exists, sample_cache_data):
    """Test successful cache loading."""
    mock_exists.return_value = True
    mock_file.return_value.read.return_value = json.dumps(sample_cache_data)
    
    result = _load_cache()
    assert result is not None
    assert 'timestamp' in result
    assert 'files' in result


@patch('pathlib.Path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='invalid json')
def test_load_cache_invalid_json(mock_file, mock_exists):
    """Test cache loading handles invalid JSON gracefully."""
    mock_exists.return_value = True
    
    result = _load_cache()
    assert result is None


# Tests for cache saving

@patch('pathlib.Path.mkdir')
@patch('builtins.open', new_callable=mock_open)
def test_save_cache_success(mock_file, mock_mkdir):
    """Test successful cache saving."""
    files = ['en/en_US/lessac/high/en_US-lessac-high.onnx']
    
    _save_cache(files)
    
    mock_mkdir.assert_called_once()
    mock_file.assert_called_once()


# Tests for voice path parsing

def test_parse_voice_paths_valid_models(sample_voice_paths):
    """Test parsing valid voice paths."""
    models = parse_voice_paths(sample_voice_paths)
    
    assert len(models) == 4
    assert all(isinstance(m, VoiceModel) for m in models)
    
    # Check first model
    assert models[0].language == 'en'
    assert models[0].locale == 'en_US'
    assert models[0].voice_name == 'lessac'
    assert models[0].quality == 'high'


def test_parse_voice_paths_missing_config():
    """Test parsing handles missing config files."""
    paths = [
        'en/en_US/lessac/high/en_US-lessac-high.onnx',
        # Missing .onnx.json file
    ]
    
    models = parse_voice_paths(paths)
    assert len(models) == 0


def test_parse_voice_paths_invalid_structure():
    """Test parsing handles invalid path structure."""
    paths = [
        'invalid/path.onnx',
        'invalid/path.onnx.json',
        'en/en_US/lessac/high/en_US-lessac-high.onnx',
        'en/en_US/lessac/high/en_US-lessac-high.onnx.json',
    ]
    
    models = parse_voice_paths(paths)
    assert len(models) == 1  # Only the valid one


def test_parse_voice_paths_filters_config_files(sample_voice_paths):
    """Test parsing correctly filters out .onnx.json files."""
    # Add some noise
    paths = sample_voice_paths + ['some/other/file.txt']
    
    models = parse_voice_paths(paths)
    assert len(models) == 4
    assert all(m.onnx_path.endswith('.onnx') for m in models)
    assert all(not m.onnx_path.endswith('.onnx.json') for m in models)


def test_parse_voice_paths_empty_list():
    """Test parsing empty path list."""
    models = parse_voice_paths([])
    assert models == []


# Tests for get_voice_paths with caching

@patch('talking_clock_audio.voice_manager._load_cache')
@patch('talking_clock_audio.voice_manager._is_cache_valid')
def test_get_voice_paths_uses_valid_cache(mock_is_valid, mock_load, sample_cache_data):
    """Test get_voice_paths uses cache when valid."""
    mock_load.return_value = sample_cache_data
    mock_is_valid.return_value = True
    
    result = get_voice_paths()
    
    assert result == sample_cache_data['files']
    mock_is_valid.assert_called_once()


@patch('talking_clock_audio.voice_manager._load_cache')
@patch('talking_clock_audio.voice_manager._is_cache_valid')
@patch('talking_clock_audio.voice_manager.list_repo_files')
@patch('talking_clock_audio.voice_manager._save_cache')
def test_get_voice_paths_fetches_when_cache_stale(
    mock_save, mock_list_repo, mock_is_valid, mock_load, sample_voice_paths
):
    """Test get_voice_paths fetches fresh data when cache is stale."""
    mock_load.return_value = None  # No cache
    mock_list_repo.return_value = iter(sample_voice_paths)
    
    result = get_voice_paths()
    
    assert result == sample_voice_paths
    mock_list_repo.assert_called_once()
    mock_save.assert_called_once_with(sample_voice_paths)


@patch('talking_clock_audio.voice_manager._load_cache')
@patch('talking_clock_audio.voice_manager._is_cache_valid')
@patch('talking_clock_audio.voice_manager.list_repo_files')
def test_get_voice_paths_uses_stale_cache_on_network_error(
    mock_list_repo, mock_is_valid, mock_load, old_cache_data
):
    """Test get_voice_paths falls back to stale cache on network error."""
    mock_load.return_value = old_cache_data
    mock_is_valid.return_value = False  # Cache is stale
    mock_list_repo.side_effect = Exception("Network error")
    
    result = get_voice_paths()
    
    assert result == old_cache_data['files']


@patch('talking_clock_audio.voice_manager._load_cache')
@patch('talking_clock_audio.voice_manager.list_repo_files')
def test_get_voice_paths_raises_on_network_error_no_cache(mock_list_repo, mock_load):
    """Test get_voice_paths raises exception when network fails and no cache."""
    mock_load.return_value = None
    mock_list_repo.side_effect = Exception("Network error")
    
    with pytest.raises(Exception) as exc_info:
        get_voice_paths()
    
    assert "Cannot reach Hugging Face repository" in str(exc_info.value)


# Tests for high-level get_available_voices function

@patch('talking_clock_audio.voice_manager.get_voice_paths')
def test_get_available_voices_integration(mock_get_paths, sample_voice_paths):
    """Test get_available_voices integrates fetching and parsing."""
    mock_get_paths.return_value = sample_voice_paths
    
    voices = get_available_voices()
    
    assert len(voices) == 4
    assert all(isinstance(v, VoiceModel) for v in voices)
    mock_get_paths.assert_called_once_with(24)


@patch('talking_clock_audio.voice_manager.get_voice_paths')
def test_get_available_voices_custom_cache_duration(mock_get_paths, sample_voice_paths):
    """Test get_available_voices respects custom cache duration."""
    mock_get_paths.return_value = sample_voice_paths
    
    voices = get_available_voices(cache_duration_hours=48)
    
    mock_get_paths.assert_called_once_with(48)


@patch('talking_clock_audio.voice_manager.get_voice_paths')
def test_get_available_voices_filters_by_language(mock_get_paths, sample_voice_paths):
    """Test filtering voices by language after retrieval."""
    mock_get_paths.return_value = sample_voice_paths
    
    voices = get_available_voices()
    english_voices = [v for v in voices if v.language == 'en']
    
    assert len(english_voices) == 2
    assert all(v.language == 'en' for v in english_voices)


@patch('talking_clock_audio.voice_manager.get_voice_paths')
def test_get_available_voices_filters_by_quality(mock_get_paths, sample_voice_paths):
    """Test filtering voices by quality after retrieval."""
    mock_get_paths.return_value = sample_voice_paths
    
    voices = get_available_voices()
    high_quality = [v for v in voices if v.quality == 'high']
    
    assert len(high_quality) == 1
    assert high_quality[0].quality == 'high'
