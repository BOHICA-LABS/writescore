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
    @patch("writescore.utils.spacy_loader.download")
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

    @patch("writescore.utils.spacy_loader.spacy.load")
    @patch("writescore.utils.spacy_loader.download")
    def test_load_spacy_model_download_calls_spacy_cli(self, mock_download, mock_load):
        """Test that the download uses spacy.cli.download."""
        mock_load.side_effect = [OSError("Model not found"), MagicMock()]

        from writescore.utils.spacy_loader import load_spacy_model

        load_spacy_model("test_model")

        mock_download.assert_called_once_with("test_model")

    def test_load_spacy_model_default_model(self):
        """Test that the default model is en_core_web_sm."""
        from writescore.utils.spacy_loader import load_spacy_model

        nlp = load_spacy_model()
        assert "core_web_sm" in nlp.meta["name"]
