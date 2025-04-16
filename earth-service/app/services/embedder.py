"""Embedder service for generating vector embeddings from text.

This module provides a service for embedding text using Sentence Transformers,
with caching to improve performance.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import torch
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger
from app.models.endpoint import Endpoint

logger = get_logger(__name__)

# Constants
CACHE_SAVE_THRESHOLD = 100
PROGRESS_BAR_THRESHOLD = 10


class Embedder:
    """Text embedding service using Sentence Transformers.

    This class provides methods to embed text using the specified model,
    with optional caching and device selection.
    """

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        device: str = settings.EMBEDDING_DEVICE,
        cache_dir: str = settings.EMBEDDING_CACHE_DIR,
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    ):
        """Initialize the embedder with the specified model and settings.

        Args:
            model_name: Name of the Sentence Transformers model to use
            device: Device to run the model on ('cpu', 'cuda', 'mps', or 'auto')
            cache_dir: Directory to cache embeddings
            batch_size: Batch size for embedding multiple texts
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.cache_dir = cache_dir

        # Determine device
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device
        logger.info(f"Using device: {self.device} for embeddings")

        # Create cache directory if it doesn't exist
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            cache_path.mkdir(parents=True)

        # Define the local model path
        model_local_path = Path(cache_dir) / model_name.replace('/', '_')

        # First try to load from the local saved model
        if model_local_path.exists():
            try:
                logger.info(f"Loading model from local cache: {model_local_path}")
                self.model = SentenceTransformer(str(model_local_path), device=device)
                logger.info("Successfully loaded model from local cache")
            except Exception as e:
                logger.warning(f"Failed to load model from local cache: {e}. Will download from hub.")
                self.model = SentenceTransformer(model_name, device=device, cache_folder=cache_dir)
                # Save the model after downloading
                logger.info(f"Saving model to: {model_local_path}")
                self.model.save(str(model_local_path))
        else:
            # Model doesn't exist locally, download it
            logger.info(f"Model not found in local cache, downloading: {model_name}")
            self.model = SentenceTransformer(model_name, device=device, cache_folder=cache_dir)
            # Save the model for future use
            logger.info(f"Saving model to: {model_local_path}")
            self.model.save(str(model_local_path))

        # Initialize memory cache
        self._cache = {}

        # Load disk cache
        self.cache_file = (
            Path(cache_dir) / f"{model_name.replace('/', '_')}_cache.joblib"
        )
        self._load_cache()

        # Log model info
        self.embedding_dimension = self.model.get_sentence_embedding_dimension() or 0
        logger.info(
            f"Initialized embedder with model: {model_name}",
            extra={
                "embedding_dimension": self.embedding_dimension,
                "device": self.device,
                "batch_size": self.batch_size,
            },
        )

    def _load_cache(self) -> None:
        """Load the embedding cache from disk if it exists."""
        try:
            if self.cache_file.exists():
                self._cache = joblib.load(self.cache_file)
                logger.info(f"Loaded {len(self._cache)} cached embeddings")
        except OSError as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save the embedding cache to disk."""
        try:
            joblib.dump(self._cache, self.cache_file)
            logger.info(f"Saved {len(self._cache)} embeddings to cache")
        except OSError as e:
            logger.warning(f"Failed to save embedding cache: {e}")

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: The text to embed

        Returns:
            List of embedding values (vector)
        """
        # Check cache first
        if text in self._cache:
            return self._cache[text]

        # Generate embedding
        embedding = self.model.encode(text, show_progress_bar=False)

        # Convert to Python list for serialization
        embedding_list = embedding.tolist()

        # Cache the result
        self._cache[text] = embedding_list

        # Periodically save cache (every CACHE_SAVE_THRESHOLD new embeddings)
        if len(self._cache) % CACHE_SAVE_THRESHOLD == 0:
            self._save_cache()

        return embedding_list

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Filter out texts that are already cached
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            if text not in self._cache:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Prepare result list with cached embeddings
        result = []
        # If there are uncached texts, embed them
        if uncached_texts:
            # Generate embeddings for uncached texts
            embeddings = self.model.encode(
                uncached_texts,
                batch_size=self.batch_size,
                show_progress_bar=len(uncached_texts) > PROGRESS_BAR_THRESHOLD,
            )

            # Update results and cache
            for i, idx in enumerate(uncached_indices):
                embedding_list: list[float] = embeddings[i].tolist()
                result[idx] = embedding_list

        return result

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query.

        This is a convenience method that may apply query-specific preprocessing.

        Args:
            query: The search query text

        Returns:
            Query embedding vector
        """
        return self.embed_text(query)

    def get_dimension(self) -> int:
        """Get the dimension of the embeddings produced by this model."""
        return self.embedding_dimension


@lru_cache(maxsize=1000)
def get_embedder() -> Embedder:
    """Get a singleton instance of the Embedder.

    Returns:
        Embedder instance
    """
    return Embedder()

def embed_endpoint(
    service_name: str | None,
    endpoint_summary: str | None,
    endpoint_description: str | None,
    endpoint_tags: list[str] | str | None,
    endpoint_path: str | None,
) -> list[float]:
    """Embed an endpoint's vector data.

    Args:
        service_name: Name of the service the endpoint belongs to
        endpoint_summary: Summary of the endpoint
        endpoint_description: Description of the endpoint
        endpoint_tags: Tags associated with the endpoint
        endpoint_path: Path of the endpoint

    Returns:
        List of embedding values (vector)
    """
    if isinstance(endpoint_tags, str):
        endpoint_tags = endpoint_tags.split(",")
    text = f"{service_name} - {endpoint_summary or endpoint_description} {', '.join(endpoint_tags) if endpoint_tags else ''} {endpoint_path}"

    logger.debug(f"Embedding text: {text}")
    return get_embedder().embed_text(text)
