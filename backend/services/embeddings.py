"""
Local text embeddings backed by sentence-transformers.

Defaults to an IBM Granite embedding model, downloaded from HuggingFace on first
use and run on CPU — no embedding API key is required. Only `embed_query` and
`embed_documents` are needed by the retrieval pipeline, which is exactly the
interface the rest of the code (and LangChain) expects.
"""
from __future__ import annotations

from sentence_transformers import SentenceTransformer


class LocalEmbeddings:
    """Minimal embeddings wrapper exposing the standard embed_* interface."""

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        normalize: bool = True,
    ) -> None:
        self.model_name = model_name
        self._normalize = normalize
        # Loads (and downloads on first use) the model onto the requested device.
        self._model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents, returning one vector per input text."""
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        vector = self._model.encode(
            text,
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
        )
        return vector.tolist()

# Made with Bob
