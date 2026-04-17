import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException, ConnectionError, Timeout

from database import check_ollama_health

def test_check_ollama_health_success():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        assert check_ollama_health() == True
        mock_get.assert_called_once()

def test_check_ollama_health_non_200_503():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_get.return_value = mock_response
        
        with pytest.raises(SystemExit) as exc_info:
            check_ollama_health()
        assert exc_info.value.code == 1
        mock_get.assert_called_once()

def test_check_ollama_health_non_200_404():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        with pytest.raises(SystemExit) as exc_info:
            check_ollama_health()
        assert exc_info.value.code == 1
        mock_get.assert_called_once()

def test_check_ollama_health_connection_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("Connection Refused")
        
        with pytest.raises(SystemExit) as exc_info:
            check_ollama_health()
        assert exc_info.value.code == 1
        mock_get.assert_called_once()

def test_check_ollama_health_timeout():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Timeout("Timeout")
        
        with pytest.raises(SystemExit) as exc_info:
            check_ollama_health()
        assert exc_info.value.code == 1
        mock_get.assert_called_once()

def test_check_ollama_health_request_exception():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = RequestException("Generic error")
        
        with pytest.raises(SystemExit) as exc_info:
            check_ollama_health()
        assert exc_info.value.code == 1
        mock_get.assert_called_once()

def test_check_ollama_health_timeout_kwarg_forwarded():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        assert check_ollama_health(timeout=10) == True
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs.get('timeout') == 10

def test_check_ollama_health_ollama_host_env_var(monkeypatch):
    import importlib
    import database
    
    # Temporarily set the env var
    monkeypatch.setenv("OLLAMA_HOST", "http://custom-host:8080/")
    # Reload the module so _OLLAMA_BASE picks up the env var
    importlib.reload(database)
    
    with patch('database.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        assert database.check_ollama_health() == True
        mock_get.assert_called_once()
        args, _ = mock_get.call_args
        assert args[0] == "http://custom-host:8080/api/tags"

    # Reload again to clean up environment state for other tests
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    importlib.reload(database)
