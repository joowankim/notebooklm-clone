"""OpenAI embedding provider."""

import openai

from src import exceptions
from src.chunk.adapter.embedding import port as embedding_port
from src import settings as settings_module


class OpenAIEmbeddingProvider(embedding_port.EmbeddingProviderPort):
    """Embedding provider using OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self._api_key = api_key or settings_module.settings.openai_api_key
        self._model = model or settings_module.settings.embedding_model
        self._dimensions = dimensions or settings_module.settings.embedding_dimensions
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

        except openai.AuthenticationError as exc:
            raise exceptions.ExternalServiceError("OpenAI authentication failed") from exc
        except openai.RateLimitError as exc:
            raise exceptions.ExternalServiceError("OpenAI rate limit exceeded") from exc
        except openai.APIError as exc:
            raise exceptions.ExternalServiceError(f"OpenAI API error: {exc}") from exc

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions
