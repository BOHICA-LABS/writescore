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
    @patch("writescore.utils.spacy_loader.subprocess.check_call")
    def test_load_spacy_model_downloads_if_missing(self, mock_check_call, mock_load):
        """Test that the loader downloads the model if not found."""
        # First call raises OSError (model not found), second call succeeds
        mock_nlp = MagicMock()
        mock_load.side_effect = [OSError("Model not found"), mock_nlp]

        from writescore.utils.spacy_loader import load_spacy_model

        result = load_spacy_model("en_core_web_sm")

        assert mock_check_call.called
        assert result == mock_nlp
        assert mock_load.call_count == 2

    @patch("writescore.utils.spacy_loader.spacy.load")
    @patch("writescore.utils.spacy_loader.subprocess.check_call")
    def test_load_spacy_model_download_command(self, mock_check_call, mock_load):
        """Test that the download command uses correct arguments."""
        import sys

        mock_load.side_effect = [OSError("Model not found"), MagicMock()]

        from writescore.utils.spacy_loader import load_spacy_model

        load_spacy_model("test_model")

        mock_check_call.assert_called_once()
        call_args = mock_check_call.call_args[0][0]
        assert call_args[0] == sys.executable
        assert call_args[1] == "-m"
        assert call_args[2] == "spacy"
        assert call_args[3] == "download"
        assert call_args[4] == "test_model"

    def test_load_spacy_model_default_model(self):
        """Test that the default model is en_core_web_sm."""
        from writescore.utils.spacy_loader import load_spacy_model

        nlp = load_spacy_model()
        assert "core_web_sm" in nlp.meta["name"]
