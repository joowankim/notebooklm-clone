"""OpenAI embedding provider."""

import openai

from src import exceptions
from src.chunk.adapter.embedding.port import EmbeddingProviderPort
from src.settings import settings


class OpenAIEmbeddingProvider(EmbeddingProviderPort):
    """Embedding provider using OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ):
        self._api_key = api_key or settings.openai_api_key
        self._model = model or settings.embedding_model
        self._dimensions = dimensions or settings.embedding_dimensions
        self._client = openai.AsyncOpenAI(api_key=self._api_key)

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
            )

            # Sort by index to ensure order matches input
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        except openai.AuthenticationError:
            raise exceptions.ExternalServiceError("OpenAI authentication failed")
        except openai.RateLimitError:
            raise exceptions.ExternalServiceError("OpenAI rate limit exceeded")
        except openai.APIError as e:
            raise exceptions.ExternalServiceError(f"OpenAI API error: {e}")

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions
