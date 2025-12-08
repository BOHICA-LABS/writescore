"""
Tests for spacy model loader utility.
"""

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

    @patch("writescore.utils.spacy_loader.subprocess.run")
    @patch("writescore.utils.spacy_loader.shutil.which")
    def test_download_model_uses_uv_when_available(self, mock_which, mock_run):
        """Test that _download_model uses uv when available."""
        mock_which.return_value = "/usr/bin/uv"

        from writescore.utils.spacy_loader import _download_model

        _download_model("test_model")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "uv"
        assert cmd[1] == "pip"
        assert cmd[2] == "install"
        assert cmd[3] == "test_model"

    @patch("writescore.utils.spacy_loader.subprocess.run")
    @patch("writescore.utils.spacy_loader.shutil.which")
    def test_download_model_falls_back_to_pip(self, mock_which, mock_run):
        """Test that _download_model falls back to pip when uv not available."""
        mock_which.return_value = None

        from writescore.utils.spacy_loader import _download_model

        _download_model("test_model")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[1] == "-m"
        assert cmd[2] == "pip"
        assert cmd[3] == "install"
        assert cmd[4] == "test_model"

    def test_load_spacy_model_default_model(self):
        """Test that the default model is en_core_web_sm."""
        from writescore.utils.spacy_loader import load_spacy_model

        nlp = load_spacy_model()
        assert "core_web_sm" in nlp.meta["name"]
