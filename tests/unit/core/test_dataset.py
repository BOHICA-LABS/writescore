"""
Unit tests for validation dataset infrastructure.

Tests Story 2.5 Task 2: Dataset loading, validation, and versioning.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from writescore.core.dataset import (
    Document,
    ValidationDataset,
    DatasetLoader
)


class TestDocument:
    """Test Document dataclass."""

    def test_create_human_document(self):
        """Test creating a human-written document."""
        doc = Document(
            id="doc_001",
            text="This is a human-written document with sufficient content for testing.",
            label="human",
            domain="academic",
            word_count=10,
            source="test",
            timestamp="2025-11-24T10:00:00Z"
        )
        doc.validate()
        assert doc.label == "human"
        assert doc.ai_model is None

    def test_create_ai_document(self):
        """Test creating an AI-generated document."""
        doc = Document(
            id="doc_002",
            text="This is an AI-generated document with sufficient content.",
            label="ai",
            ai_model="gpt-4",
            domain="social",
            word_count=8,
            source="OpenAI API"
        )
        doc.validate()
        assert doc.label == "ai"
        assert doc.ai_model == "gpt-4"

    def test_invalid_label_rejected(self):
        """Test that invalid labels are rejected."""
        doc = Document(
            id="doc_003",
            text="Test content",
            label="robot"  # Invalid
        )
        with pytest.raises(ValueError, match="Label must be"):
            doc.validate()

    def test_ai_document_requires_model(self):
        """Test that AI documents must specify model."""
        doc = Document(
            id="doc_004",
            text="Test content",
            label="ai"
            # Missing ai_model
        )
        with pytest.raises(ValueError, match="must have ai_model"):
            doc.validate()

    def test_human_document_cannot_have_model(self):
        """Test that human documents should not have ai_model."""
        doc = Document(
            id="doc_005",
            text="Test content",
            label="human",
            ai_model="gpt-4"  # Should not be set
        )
        with pytest.raises(ValueError, match="should not have ai_model"):
            doc.validate()

    def test_empty_text_rejected(self):
        """Test that empty text is rejected."""
        doc = Document(
            id="doc_006",
            text="   ",  # Whitespace only
            label="human"
        )
        with pytest.raises(ValueError, match="empty text"):
            doc.validate()

    def test_auto_compute_word_count(self):
        """Test automatic word count computation."""
        doc = Document(
            id="doc_007",
            text="This document has exactly seven words here.",
            label="human",
            word_count=0  # Will be auto-computed
        )
        doc.validate()
        assert doc.word_count == 7

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        doc = Document(
            id="doc_008",
            text="Test content",
            label="human",
            domain="business",
            word_count=2,
            metadata={"custom": "value"}
        )
        data = doc.to_dict()
        assert data["id"] == "doc_008"
        assert data["label"] == "human"
        assert data["metadata"]["custom"] == "value"

    def test_from_dict_conversion(self):
        """Test creation from dictionary."""
        data = {
            "id": "doc_009",
            "text": "Test content",
            "label": "ai",
            "ai_model": "claude-3",
            "domain": "technical",
            "word_count": 2
        }
        doc = Document.from_dict(data)
        assert doc.id == "doc_009"
        assert doc.ai_model == "claude-3"
        assert doc.domain == "technical"


class TestValidationDataset:
    """Test ValidationDataset container."""

    def test_create_empty_dataset(self):
        """Test creating an empty dataset."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )
        assert dataset.version == "v1.0"
        assert len(dataset.documents) == 0

    def test_add_document(self):
        """Test adding documents to dataset."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        doc = Document(
            id="doc_001",
            text="Test content",
            label="human",
            word_count=2
        )

        dataset.add_document(doc)
        assert len(dataset.documents) == 1
        assert dataset.documents[0].id == "doc_001"

    def test_get_statistics(self):
        """Test computing dataset statistics."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        # Add human documents
        for i in range(3):
            dataset.add_document(Document(
                id=f"human_{i}",
                text="Test content " * 10,
                label="human",
                domain="academic",
                word_count=20
            ))

        # Add AI documents
        for i in range(2):
            dataset.add_document(Document(
                id=f"ai_{i}",
                text="Test content " * 15,
                label="ai",
                ai_model="gpt-4",
                domain="social",
                word_count=30
            ))

        stats = dataset.get_statistics()
        assert stats["total_documents"] == 5
        assert stats["human_documents"] == 3
        assert stats["ai_documents"] == 2
        assert stats["domains"]["academic"] == 3
        assert stats["domains"]["social"] == 2
        assert stats["ai_models"]["gpt-4"] == 2
        assert stats["word_count_stats"]["average"] == 24.0

    def test_get_documents_by_label(self):
        """Test filtering documents by label."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="human_1", text="Test", label="human", word_count=1
        ))
        dataset.add_document(Document(
            id="ai_1", text="Test", label="ai", ai_model="gpt-4", word_count=1
        ))
        dataset.add_document(Document(
            id="human_2", text="Test", label="human", word_count=1
        ))

        human_docs = dataset.get_documents_by_label("human")
        ai_docs = dataset.get_documents_by_label("ai")

        assert len(human_docs) == 2
        assert len(ai_docs) == 1

    def test_get_documents_by_domain(self):
        """Test filtering documents by domain."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="doc_1", text="Test", label="human", domain="academic", word_count=1
        ))
        dataset.add_document(Document(
            id="doc_2", text="Test", label="human", domain="social", word_count=1
        ))
        dataset.add_document(Document(
            id="doc_3", text="Test", label="human", domain="academic", word_count=1
        ))

        academic_docs = dataset.get_documents_by_domain("academic")
        assert len(academic_docs) == 2

    def test_get_documents_by_model(self):
        """Test filtering documents by AI model."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="doc_1", text="Test", label="ai", ai_model="gpt-4", word_count=1
        ))
        dataset.add_document(Document(
            id="doc_2", text="Test", label="ai", ai_model="claude-3", word_count=1
        ))
        dataset.add_document(Document(
            id="doc_3", text="Test", label="ai", ai_model="gpt-4", word_count=1
        ))

        gpt4_docs = dataset.get_documents_by_model("gpt-4")
        assert len(gpt4_docs) == 2

    def test_split_train_test(self):
        """Test splitting dataset into train and test sets."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        # Add 100 documents
        for i in range(100):
            dataset.add_document(Document(
                id=f"doc_{i}",
                text="Test content",
                label="human" if i % 2 == 0 else "ai",
                ai_model="gpt-4" if i % 2 == 1 else None,
                word_count=2
            ))

        train, test = dataset.split_train_test(test_ratio=0.2, seed=42)

        assert len(train.documents) == 80
        assert len(test.documents) == 20
        assert train.version == "v1.0-train"
        assert test.version == "v1.0-test"

    def test_validate_duplicate_ids_rejected(self):
        """Test that duplicate document IDs are rejected."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="duplicate", text="Test", label="human", word_count=1
        ))
        dataset.add_document(Document(
            id="duplicate", text="Test", label="human", word_count=1
        ))

        with pytest.raises(ValueError, match="Duplicate document IDs"):
            dataset.validate()


class TestDatasetLoader:
    """Test DatasetLoader class."""

    def test_save_and_load_jsonl_file(self):
        """Test saving and loading dataset as JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_dataset.jsonl"

            # Create dataset
            original = ValidationDataset(
                version="v1.0",
                created="2025-11-24T10:00:00Z"
            )

            for i in range(5):
                original.add_document(Document(
                    id=f"doc_{i}",
                    text=f"Test content {i}",
                    label="human",
                    domain="academic",
                    word_count=3
                ))

            # Save
            DatasetLoader.save_jsonl(original, file_path, save_metadata=False)
            assert file_path.exists()

            # Load
            loaded = DatasetLoader.load_jsonl(file_path)
            assert len(loaded.documents) == 5
            assert loaded.documents[0].id == "doc_0"
            assert loaded.documents[0].text == "Test content 0"

    def test_save_and_load_directory(self):
        """Test saving and loading dataset as directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir) / "v1.0"

            # Create dataset
            original = ValidationDataset(
                version="v1.0",
                created="2025-11-24T10:00:00Z",
                metadata={"description": "Test dataset"}
            )

            for i in range(5):
                original.add_document(Document(
                    id=f"doc_{i}",
                    text=f"Test content {i}",
                    label="ai",
                    ai_model="gpt-4",
                    word_count=3
                ))

            # Save
            DatasetLoader.save_jsonl(original, dir_path, save_metadata=True)
            assert (dir_path / "documents.jsonl").exists()
            assert (dir_path / "metadata.json").exists()

            # Load
            loaded = DatasetLoader.load_jsonl(dir_path)
            assert len(loaded.documents) == 5
            assert loaded.version == "v1.0"
            # Metadata is nested inside statistics when saved with save_metadata=True
            assert loaded.metadata.get("metadata", {}).get("description") == "Test dataset"

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            DatasetLoader.load_jsonl(Path("/nonexistent/file.jsonl"))

    def test_load_invalid_json_raises_error(self):
        """Test that invalid JSON raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "invalid.jsonl"

            # Write invalid JSON syntax
            with open(file_path, 'w') as f:
                f.write('{"id": "doc_1", "text": "test", "label": "human", "word_count": 2}\n')
                f.write('{ invalid json syntax here }\n')  # Invalid JSON syntax

            with pytest.raises(json.JSONDecodeError):
                DatasetLoader.load_jsonl(file_path)

    def test_compute_dataset_hash(self):
        """Test computing dataset hash."""
        dataset = ValidationDataset(
            version="v1.0",
            created="2025-11-24T10:00:00Z"
        )

        dataset.add_document(Document(
            id="doc_1", text="Test content", label="human", word_count=2
        ))
        dataset.add_document(Document(
            id="doc_2", text="More content", label="human", word_count=2
        ))

        hash1 = DatasetLoader.compute_dataset_hash(dataset)
        assert len(hash1) == 16
        assert isinstance(hash1, str)

        # Same dataset should produce same hash
        hash2 = DatasetLoader.compute_dataset_hash(dataset)
        assert hash1 == hash2

        # Different dataset should produce different hash
        dataset.add_document(Document(
            id="doc_3", text="New content", label="human", word_count=2
        ))
        hash3 = DatasetLoader.compute_dataset_hash(dataset)
        assert hash1 != hash3

    def test_load_empty_jsonl_file(self):
        """Test loading empty JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "empty.jsonl"

            # Create empty file
            file_path.touch()

            # Should load but have no documents
            dataset = DatasetLoader.load_jsonl(file_path)
            assert len(dataset.documents) == 0

    def test_roundtrip_preserves_data(self):
        """Test that save/load roundtrip preserves all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir) / "v1.0"

            # Create dataset with various document types
            original = ValidationDataset(
                version="v1.0",
                created="2025-11-24T10:00:00Z",
                metadata={"test": "value"}
            )

            original.add_document(Document(
                id="human_1",
                text="Human content",
                label="human",
                domain="academic",
                word_count=2,
                source="test_source",
                metadata={"custom": "field"}
            ))

            original.add_document(Document(
                id="ai_1",
                text="AI content",
                label="ai",
                ai_model="gpt-4",
                domain="social",
                word_count=2
            ))

            # Save and load
            DatasetLoader.save_jsonl(original, dir_path, save_metadata=True)
            loaded = DatasetLoader.load_jsonl(dir_path)

            # Verify preservation
            assert len(loaded.documents) == 2
            human_doc = loaded.documents[0]
            assert human_doc.id == "human_1"
            assert human_doc.label == "human"
            assert human_doc.domain == "academic"
            assert human_doc.source == "test_source"
            assert human_doc.metadata.get("custom") == "field"

            ai_doc = loaded.documents[1]
            assert ai_doc.id == "ai_1"
            assert ai_doc.label == "ai"
            assert ai_doc.ai_model == "gpt-4"
