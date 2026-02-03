"""Embedding provider port (interface)."""

import abc


class EmbeddingProviderPort(abc.ABC):
    """Abstract interface for embedding generation."""

    @abc.abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            List of float values representing the embedding.

        Raises:
            ExternalServiceError: If embedding generation fails.
        """
        ...

    @abc.abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings, one per input text.

        Raises:
            ExternalServiceError: If embedding generation fails.
        """
        ...

    @property
    @abc.abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        ...
