"""
Tests for spacy model loader utility.
"""

import json
from unittest.mock import MagicMock, patch


class TestLoadSpacyModel:
    """Tests for load_spacy_model function."""

    def test_load_spacy_model_already_installed(self):
        """Test loading a model that is already installed."""
        from writescore.utils.spacy_loader import load_spacy_model

        nlp = load_spacy_model("en_core_web_sm")
        assert nlp is not None
        assert hasattr(nlp, "meta")
        assert "name" in nlp.meta

    def test_load_spacy_model_returns_language_object(self):
        """Test that the loader returns a proper spacy Language object."""
        from writescore.utils.spacy_loader import load_spacy_model

        nlp = load_spacy_model("en_core_web_sm")
        # Test it can process text
        doc = nlp("This is a test sentence.")
        assert len(doc) > 0
        assert doc[0].text == "This"

    @patch("writescore.utils.spacy_loader.spacy.load")
    @patch("writescore.utils.spacy_loader._download_model")
    def test_load_spacy_model_downloads_if_missing(self, mock_download, mock_load):
        """Test that the loader downloads the model if not found."""
        # First call raises OSError (model not found), second call succeeds
        mock_nlp = MagicMock()
        mock_load.side_effect = [OSError("Model not found"), mock_nlp]

        from writescore.utils.spacy_loader import load_spacy_model

        result = load_spacy_model("en_core_web_sm")

        mock_download.assert_called_once_with("en_core_web_sm")
        assert result == mock_nlp
        assert mock_load.call_count == 2

    @patch("writescore.utils.spacy_loader._get_model_url")
    @patch("writescore.utils.spacy_loader.subprocess.run")
    @patch("writescore.utils.spacy_loader.shutil.which")
    def test_download_model_uses_uv_when_available(self, mock_which, mock_run, mock_get_url):
        """Test that _download_model uses uv when available."""
        mock_which.return_value = "/usr/bin/uv"
        mock_get_url.return_value = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"

        from writescore.utils.spacy_loader import _download_model

        _download_model("en_core_web_sm")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "uv"
        assert cmd[1] == "pip"
        assert cmd[2] == "install"
        assert "github.com" in cmd[3]  # URL instead of model name

    @patch("writescore.utils.spacy_loader._get_model_url")
    @patch("writescore.utils.spacy_loader.subprocess.run")
    @patch("writescore.utils.spacy_loader.shutil.which")
    def test_download_model_falls_back_to_pip(self, mock_which, mock_run, mock_get_url):
        """Test that _download_model falls back to pip when uv not available."""
        mock_which.return_value = None
        mock_get_url.return_value = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"

        from writescore.utils.spacy_loader import _download_model

        _download_model("en_core_web_sm")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[1] == "-m"
        assert cmd[2] == "pip"
        assert cmd[3] == "install"
        assert "github.com" in cmd[4]  # URL instead of model name

    def test_load_spacy_model_default_model(self):
        """Test that the default model is en_core_web_sm."""
        from writescore.utils.spacy_loader import load_spacy_model

        nlp = load_spacy_model()
        assert "core_web_sm" in nlp.meta["name"]


class TestGetModelUrl:
    """Tests for _get_model_url function."""

    @patch("writescore.utils.spacy_loader.urllib.request.urlopen")
    @patch("writescore.utils.spacy_loader.spacy.__version__", "3.8.0")
    def test_get_model_url_returns_github_url(self, mock_urlopen):
        """Test that _get_model_url returns a GitHub releases URL."""
        # Mock the compatibility data response
        compat_data = {"spacy": {"v3.8": {"en_core_web_sm": ["3.8.0", "3.7.1"]}}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(compat_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from writescore.utils.spacy_loader import _get_model_url

        url = _get_model_url("en_core_web_sm")

        assert "github.com/explosion/spacy-models" in url
        assert "en_core_web_sm-3.8.0" in url
        assert url.endswith(".whl")

    @patch("writescore.utils.spacy_loader.urllib.request.urlopen")
    @patch("writescore.utils.spacy_loader.spacy.__version__", "3.8.0")
    def test_get_model_url_raises_for_unknown_model(self, mock_urlopen):
        """Test that _get_model_url raises RuntimeError for unknown models."""
        compat_data = {"spacy": {"v3.8": {"en_core_web_sm": ["3.8.0"]}}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(compat_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        import pytest

        from writescore.utils.spacy_loader import _get_model_url

        with pytest.raises(RuntimeError, match="Could not find compatible version"):
            _get_model_url("nonexistent_model")
