"""
Validation dataset infrastructure for percentile-anchored parameters.

Manages loading, validation, and versioning of validation datasets used
for parameter calibration and recalibration.

Created in Story 2.5 Task 2.
"""

import hashlib
import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """
    Represents a single document in the validation dataset.

    Attributes:
        id: Unique document identifier
        text: Document content
        label: "human" or "ai"
        ai_model: AI model name (e.g., "gpt-4", "claude-3") or None for human
        domain: Content domain (e.g., "academic", "social", "business")
        word_count: Number of words in document
        source: Source information or attribution
        timestamp: When document was added to dataset
        metadata: Additional optional metadata
    """

    id: str
    text: str
    label: str  # "human" or "ai"
    ai_model: Optional[str] = None
    domain: Optional[str] = None
    word_count: int = 0
    source: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate document fields."""
        if self.label not in ("human", "ai"):
            raise ValueError(f"Label must be 'human' or 'ai', got '{self.label}'")

        if self.label == "ai" and not self.ai_model:
            raise ValueError("AI documents must have ai_model specified")

        if self.label == "human" and self.ai_model:
            raise ValueError("Human documents should not have ai_model")

        if not self.text or len(self.text.strip()) == 0:
            raise ValueError(f"Document {self.id} has empty text")

        if self.word_count <= 0:
            # Auto-compute if not set
            self.word_count = len(self.text.split())

        if self.word_count < 50:
            logger.warning(f"Document {self.id} is very short ({self.word_count} words)")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "label": self.label,
            "ai_model": self.ai_model,
            "domain": self.domain,
            "word_count": self.word_count,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create Document from dictionary."""
        return cls(
            id=data["id"],
            text=data["text"],
            label=data["label"],
            ai_model=data.get("ai_model"),
            domain=data.get("domain"),
            word_count=data.get("word_count", 0),
            source=data.get("source"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ValidationDataset:
    """
    Container for validation dataset with versioning and statistics.

    Attributes:
        version: Dataset version (e.g., "v1.0", "v2.0")
        created: Creation timestamp
        documents: List of Document objects
        metadata: Dataset-level metadata
    """

    version: str
    created: str
    documents: List[Document] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_document(self, doc: Document) -> None:
        """Add a document to the dataset."""
        doc.validate()
        self.documents.append(doc)

    def get_statistics(self) -> Dict[str, Any]:
        """Compute dataset statistics."""
        if not self.documents:
            return {
                "version": self.version,
                "total_documents": 0,
                "human_documents": 0,
                "ai_documents": 0,
            }

        # Count by label
        label_counts = Counter(doc.label for doc in self.documents)

        # Count by domain
        domain_counts = Counter(doc.domain for doc in self.documents if doc.domain)

        # Count by AI model
        ai_model_counts = Counter(
            doc.ai_model for doc in self.documents if doc.label == "ai" and doc.ai_model
        )

        # Word count statistics
        word_counts = [doc.word_count for doc in self.documents]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        min_words = min(word_counts) if word_counts else 0
        max_words = max(word_counts) if word_counts else 0

        return {
            "version": self.version,
            "created": self.created,
            "total_documents": len(self.documents),
            "human_documents": label_counts.get("human", 0),
            "ai_documents": label_counts.get("ai", 0),
            "domains": dict(domain_counts),
            "ai_models": dict(ai_model_counts),
            "word_count_stats": {
                "average": round(avg_words, 1),
                "min": min_words,
                "max": max_words,
            },
            "metadata": self.metadata,
        }

    def get_documents_by_label(self, label: str) -> List[Document]:
        """Get all documents with specified label."""
        return [doc for doc in self.documents if doc.label == label]

    def get_documents_by_domain(self, domain: str) -> List[Document]:
        """Get all documents in specified domain."""
        return [doc for doc in self.documents if doc.domain == domain]

    def get_documents_by_model(self, ai_model: str) -> List[Document]:
        """Get all documents from specified AI model."""
        return [doc for doc in self.documents if doc.ai_model == ai_model]

    def split_train_test(
        self, test_ratio: float = 0.2, seed: int = 42
    ) -> Tuple["ValidationDataset", "ValidationDataset"]:
        """
        Split dataset into train and test sets.

        Args:
            test_ratio: Fraction of data for test set (default 0.2 = 20%)
            seed: Random seed for reproducibility

        Returns:
            Tuple of (train_dataset, test_dataset)
        """
        import random

        random.seed(seed)

        # Shuffle documents
        shuffled = self.documents.copy()
        random.shuffle(shuffled)

        # Split
        split_idx = int(len(shuffled) * (1 - test_ratio))
        train_docs = shuffled[:split_idx]
        test_docs = shuffled[split_idx:]

        # Create new datasets
        train_dataset = ValidationDataset(
            version=f"{self.version}-train",
            created=datetime.now().isoformat(),
            documents=train_docs,
            metadata={**self.metadata, "split": "train", "parent_version": self.version},
        )

        test_dataset = ValidationDataset(
            version=f"{self.version}-test",
            created=datetime.now().isoformat(),
            documents=test_docs,
            metadata={**self.metadata, "split": "test", "parent_version": self.version},
        )

        logger.info(f"Split dataset: {len(train_docs)} train, {len(test_docs)} test")
        return train_dataset, test_dataset

    def validate(self) -> None:
        """Validate entire dataset."""
        if not self.version:
            raise ValueError("Dataset must have version")

        if not self.documents:
            logger.warning("Dataset is empty")
            return

        # Validate each document
        for doc in self.documents:
            doc.validate()

        # Check for duplicate IDs
        ids = [doc.id for doc in self.documents]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate document IDs found: {set(duplicates)}")

        logger.info(f"Validated {len(self.documents)} documents in dataset {self.version}")


class DatasetLoader:
    """
    Loads and saves validation datasets in JSON Lines format.

    Each line in the file is a JSON object representing one document.
    Dataset metadata is stored in a separate metadata.json file.
    """

    @staticmethod
    def load_jsonl(file_path: Path) -> ValidationDataset:
        """
        Load dataset from JSON Lines file.

        Expected format:
            documents.jsonl: One JSON object per line (Document)
            metadata.json: Dataset-level metadata

        Args:
            file_path: Path to .jsonl file or directory containing documents.jsonl

        Returns:
            ValidationDataset instance
        """
        if file_path.is_dir():
            # Load from directory structure
            return DatasetLoader._load_from_directory(file_path)
        else:
            # Load from single JSONL file
            return DatasetLoader._load_from_jsonl_file(file_path)

    @staticmethod
    def _load_from_jsonl_file(file_path: Path) -> ValidationDataset:
        """Load dataset from single JSONL file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        # Infer version from filename
        version = file_path.stem  # e.g., "v1.0" from "v1.0.jsonl"

        dataset = ValidationDataset(version=version, created=datetime.now().isoformat())

        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    doc = Document.from_dict(data)
                    dataset.add_document(doc)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON on line {line_num}: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Error loading document on line {line_num}: {e}")
                    raise

        dataset.validate()
        logger.info(f"Loaded {len(dataset.documents)} documents from {file_path}")
        return dataset

    @staticmethod
    def _load_from_directory(dir_path: Path) -> ValidationDataset:
        """Load dataset from directory with documents.jsonl and metadata.json."""
        docs_file = dir_path / "documents.jsonl"
        metadata_file = dir_path / "metadata.json"

        if not docs_file.exists():
            raise FileNotFoundError(f"documents.jsonl not found in {dir_path}")

        # Load metadata if exists
        metadata = {}
        version = dir_path.name  # Use directory name as version
        created = datetime.now().isoformat()

        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                version = metadata.get("version", version)
                created = metadata.get("created", created)

        dataset = ValidationDataset(version=version, created=created, metadata=metadata)

        # Load documents
        with open(docs_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    doc = Document.from_dict(data)
                    dataset.add_document(doc)
                except Exception as e:
                    logger.error(f"Error loading document on line {line_num}: {e}")
                    raise

        dataset.validate()
        logger.info(f"Loaded {len(dataset.documents)} documents from {dir_path}")
        return dataset

    @staticmethod
    def save_jsonl(
        dataset: ValidationDataset, output_path: Path, save_metadata: bool = True
    ) -> None:
        """
        Save dataset to JSON Lines format.

        Args:
            dataset: ValidationDataset to save
            output_path: Output path (directory or .jsonl file)
            save_metadata: If True, save metadata.json alongside documents
        """
        dataset.validate()

        if output_path.suffix == ".jsonl":
            # Save as single file
            DatasetLoader._save_to_jsonl_file(dataset, output_path)
        else:
            # Save as directory structure
            DatasetLoader._save_to_directory(dataset, output_path, save_metadata)

    @staticmethod
    def _save_to_jsonl_file(dataset: ValidationDataset, file_path: Path) -> None:
        """Save dataset to single JSONL file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            for doc in dataset.documents:
                f.write(json.dumps(doc.to_dict(), ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(dataset.documents)} documents to {file_path}")

    @staticmethod
    def _save_to_directory(dataset: ValidationDataset, dir_path: Path, save_metadata: bool) -> None:
        """Save dataset to directory with documents.jsonl and metadata.json."""
        dir_path.mkdir(parents=True, exist_ok=True)

        # Save documents
        docs_file = dir_path / "documents.jsonl"
        with open(docs_file, "w", encoding="utf-8") as f:
            for doc in dataset.documents:
                f.write(json.dumps(doc.to_dict(), ensure_ascii=False) + "\n")

        # Save metadata
        if save_metadata:
            metadata_file = dir_path / "metadata.json"
            metadata = {**dataset.get_statistics(), "saved": datetime.now().isoformat()}
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved {len(dataset.documents)} documents and metadata to {dir_path}")
        else:
            logger.info(f"Saved {len(dataset.documents)} documents to {dir_path}")

    @staticmethod
    def compute_dataset_hash(dataset: ValidationDataset) -> str:
        """
        Compute hash of dataset for version tracking.

        Uses document IDs and text to create deterministic hash.
        Useful for detecting dataset changes.
        """
        hasher = hashlib.sha256()

        # Sort documents by ID for determinism
        sorted_docs = sorted(dataset.documents, key=lambda d: d.id)

        for doc in sorted_docs:
            # Hash document ID and text
            hasher.update(doc.id.encode("utf-8"))
            hasher.update(doc.text.encode("utf-8"))

        return hasher.hexdigest()[:16]  # First 16 characters
