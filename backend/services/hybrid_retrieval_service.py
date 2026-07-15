"""
Hybrid retrieval: vector search on Document chunks + graph expansion + full-text fallback.
"""
from __future__ import annotations

from typing import Any

from langchain_neo4j import Neo4jGraph
from config import get_settings
from services.embeddings import LocalEmbeddings

settings = get_settings()

VECTOR_INDEX_NAME = "document_embeddings"
FULLTEXT_INDEX_NAME = "document_text"
EMBED_BATCH_SIZE = 16


class HybridRetrievalService:
    """Vector + full-text + graph expansion retrieval over Neo4j."""

    def __init__(self) -> None:
        self.graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        # Local IBM Granite embedding model (downloaded on first use, runs on CPU).
        # Normalizing embeddings pairs with the index's cosine similarity function.
        self.embeddings = LocalEmbeddings(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
            normalize=settings.embedding_normalize,
        )
        self._embedding_dimensions: int | None = None

    @property
    def embedding_dimensions(self) -> int:
        if self._embedding_dimensions is None:
            probe = self.embeddings.embed_query("dimension probe")
            self._embedding_dimensions = len(probe)
        return self._embedding_dimensions

    def _existing_vector_dimensions(self) -> int | None:
        """Return the dimensionality of the existing vector index, or None if absent."""
        try:
            rows = self.graph.query(
                f"""
                SHOW VECTOR INDEXES YIELD name, options
                WHERE name = '{VECTOR_INDEX_NAME}'
                RETURN options AS options
                """
            )
        except Exception:
            return None
        if not rows:
            return None
        options = rows[0].get("options") or {}
        index_config = options.get("indexConfig") or {}
        dims = index_config.get("vector.dimensions")
        return int(dims) if dims is not None else None

    def ensure_indexes(self) -> None:
        """Create vector and full-text indexes for Document nodes.

        If the embedding model changed (different vector dimensionality than the
        existing index), the old index and any stored embeddings are incompatible,
        so we drop the index and clear stale vectors — they get re-embedded below.
        """
        dims = self.embedding_dimensions

        existing_dims = self._existing_vector_dimensions()
        if existing_dims is not None and existing_dims != dims:
            self.graph.query(f"DROP INDEX {VECTOR_INDEX_NAME} IF EXISTS")
            self.graph.query(
                "MATCH (d:Document) WHERE d.embedding IS NOT NULL SET d.embedding = NULL"
            )

        self.graph.query(
            f"""
            CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
            FOR (d:Document) ON (d.embedding)
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: {dims},
                `vector.similarity_function`: 'cosine'
              }}
            }}
            """
        )
        self.graph.query(
            f"""
            CREATE FULLTEXT INDEX {FULLTEXT_INDEX_NAME} IF NOT EXISTS
            FOR (d:Document) ON EACH [d.text]
            """
        )

    def embed_all_documents(self) -> int:
        """
        Embed all Document nodes that have text but no embedding yet.
        Returns the number of documents embedded.
        """
        self.ensure_indexes()

        rows = self.graph.query(
            """
            MATCH (d:Document)
            WHERE d.text IS NOT NULL AND d.embedding IS NULL
            RETURN elementId(d) AS element_id, d.text AS text
            """
        )
        if not rows:
            return 0

        embedded = 0
        for i in range(0, len(rows), EMBED_BATCH_SIZE):
            batch = rows[i : i + EMBED_BATCH_SIZE]
            texts = [row["text"] for row in batch]
            vectors = self.embeddings.embed_documents(texts)

            for row, vector in zip(batch, vectors):
                self.graph.query(
                    """
                    MATCH (d:Document)
                    WHERE elementId(d) = $element_id
                    SET d.embedding = $embedding
                    """,
                    params={"element_id": row["element_id"], "embedding": vector},
                )
                embedded += 1

        return embedded

    def _vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        query_vector = self.embeddings.embed_query(query)
        return self.graph.query(
            f"""
            CALL db.index.vector.queryNodes($index_name, $top_k, $query_vector)
            YIELD node, score
            WHERE node.text IS NOT NULL
            RETURN elementId(node) AS element_id, node.text AS text, score
            ORDER BY score DESC
            """,
            params={
                "index_name": VECTOR_INDEX_NAME,
                "top_k": top_k,
                "query_vector": query_vector,
            },
        )

    def _fulltext_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        try:
            return self.graph.query(
                f"""
                CALL db.index.fulltext.queryNodes($index_name, $query_text, {{limit: $top_k}})
                YIELD node, score
                WHERE node.text IS NOT NULL
                RETURN elementId(node) AS element_id, node.text AS text, score
                ORDER BY score DESC
                """,
                params={
                    "index_name": FULLTEXT_INDEX_NAME,
                    "query_text": query,
                    "top_k": top_k,
                },
            )
        except Exception:
            return []

    def _expand_linked_entities(self, element_ids: list[str], limit: int = 25) -> list[dict[str, Any]]:
        if not element_ids:
            return []
        return self.graph.query(
            """
            MATCH (d:Document)-[:MENTIONS]->(e)
            WHERE elementId(d) IN $element_ids AND NOT e:Document
            RETURN DISTINCT
                labels(e)[0] AS type,
                e.id AS id,
                e.name AS name,
                e.status AS status,
                e.role AS role,
                e.description AS description,
                e.budget AS budget
            LIMIT $limit
            """,
            params={"element_ids": element_ids, "limit": limit},
        )

    def retrieve(self, query: str, top_k: int | None = None) -> dict[str, Any]:
        """
        Hybrid retrieval pipeline:
        1. Vector search on Document chunks
        2. Full-text search fallback / supplement
        3. Graph expansion via MENTIONS relationships
        """
        top_k = top_k or settings.vector_top_k
        sources: list[dict[str, Any]] = []

        # Reconcile the vector index with the current embedding model. If the model
        # changed (e.g. switched embedding models), this rebuilds the index at the
        # new dimensionality and clears now-incompatible vectors so they re-embed.
        self.ensure_indexes()

        # Ensure any newly ingested (or just-cleared) docs are embedded
        pending = self.graph.query(
            """
            MATCH (d:Document)
            WHERE d.text IS NOT NULL AND d.embedding IS NULL
            RETURN count(d) AS count
            """
        )
        if pending and pending[0].get("count", 0) > 0:
            self.embed_all_documents()

        vector_hits: list[dict[str, Any]] = []
        try:
            vector_hits = self._vector_search(query, top_k)
            if vector_hits:
                sources.append({"type": "vector_search", "results": vector_hits})
        except Exception as exc:
            sources.append({"type": "vector_search", "error": str(exc)})

        fulltext_hits = self._fulltext_search(query, top_k)
        if fulltext_hits:
            sources.append({"type": "fulltext_search", "results": fulltext_hits})

        # Merge chunk hits (dedupe by element_id, prefer higher vector score)
        chunk_map: dict[str, dict[str, Any]] = {}
        for hit in vector_hits + fulltext_hits:
            eid = hit["element_id"]
            if eid not in chunk_map or hit.get("score", 0) > chunk_map[eid].get("score", 0):
                chunk_map[eid] = hit

        chunks = list(chunk_map.values())[:top_k]
        element_ids = [c["element_id"] for c in chunks]

        linked_entities = self._expand_linked_entities(
            element_ids, limit=settings.graph_expansion_limit
        )
        if linked_entities:
            sources.append({"type": "graph_expansion", "results": linked_entities})

        vector_context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = (chunk.get("text") or "")[:1200]
            score = chunk.get("score")
            score_label = f" (score: {score:.3f})" if isinstance(score, (int, float)) else ""
            vector_context_parts.append(f"[Chunk {i}{score_label}]\n{text}")

        graph_context_parts = []
        for entity in linked_entities:
            parts = [f"{entity.get('type', 'Entity')}: {entity.get('id') or entity.get('name')}"]
            for key in ("status", "role", "description", "budget"):
                if entity.get(key):
                    parts.append(f"  {key}: {entity[key]}")
            graph_context_parts.append("\n".join(parts))

        return {
            "vector_context": "\n\n".join(vector_context_parts),
            "graph_context": "\n".join(graph_context_parts),
            "sources": sources,
            "chunk_count": len(chunks),
            "entity_count": len(linked_entities),
        }

# Made with Bob
