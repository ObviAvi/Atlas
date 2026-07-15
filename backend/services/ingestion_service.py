"""
Ingestion service - handles data extraction and loading into Neo4j.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_text_splitters import TokenTextSplitter
from langchain_core.documents import Document
from config import get_settings
from database import get_neo4j_driver, clear_database
from services.hybrid_retrieval_service import HybridRetrievalService
from models import (
    IngestResponse,
    GraphVisualizationResponse,
    GraphNode,
    GraphLink,
    NodeType,
    RelationshipType,
)

settings = get_settings()


class IngestionService:
    """Service for ingesting data into the Knowledge Graph."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.temperature
        )
        
        self.graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        
        # Configure the graph transformer with our ontology.
        # Node and relationship types are defined once in models.py.
        self.graph_transformer = LLMGraphTransformer(
            llm=self.llm,
            allowed_nodes=[node_type.value for node_type in NodeType],
            allowed_relationships=[rel_type.value for rel_type in RelationshipType],
            node_properties=["name", "status", "description", "value"],
            relationship_properties=["since", "role", "percentage"]
        )
        
        self.text_splitter = TokenTextSplitter(
            chunk_size=512,
            chunk_overlap=50
        )

        self.hybrid_retrieval = HybridRetrievalService()
    
    async def ingest_text(
        self,
        text: str,
        clear_existing: bool = False,
        title: str | None = None,
    ) -> IngestResponse:
        """
        Ingest raw text into the Knowledge Graph.
        
        Args:
            text: Raw text to process
            clear_existing: Whether to clear existing data first
            
        Returns:
            IngestResponse with status and counts
        """
        try:
            if clear_existing:
                clear_database()

            existing_doc_ids = self._get_document_element_ids()
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            # Extract graph documents using LLM
            graph_documents = self.graph_transformer.convert_to_graph_documents(documents)
            
            # Count nodes and relationships
            total_nodes = sum(len(doc.nodes) for doc in graph_documents)
            total_relationships = sum(len(doc.relationships) for doc in graph_documents)
            
            # Load into Neo4j
            self.graph.add_graph_documents(
                graph_documents,
                baseEntityLabel=True,
                include_source=True
            )

            if title:
                self._tag_new_documents(existing_doc_ids, title)

            # LLMGraphTransformer stores display names in `id`; mirror to `name` for queries
            self.graph.query(
                "MATCH (n) WHERE n.id IS NOT NULL AND n.name IS NULL SET n.name = n.id"
            )

            embedded_count = self.hybrid_retrieval.embed_all_documents()

            # Schema evolves as new entity types/relationships are extracted
            try:
                self.graph.refresh_schema()
            except Exception:
                pass
            
            return IngestResponse(
                status="success",
                message=(
                    f"Successfully ingested {len(chunks)} chunks"
                    + (f" from '{title}'" if title else "")
                    + f"; embedded {embedded_count} document nodes for vector search"
                ),
                nodes_created=total_nodes,
                relationships_created=total_relationships
            )
            
        except Exception as e:
            return IngestResponse(
                status="error",
                message=f"Ingestion failed: {str(e)}",
                nodes_created=0,
                relationships_created=0
            )
    
    def _get_document_element_ids(self) -> set[str]:
        rows = self.graph.query(
            "MATCH (d:Document) RETURN elementId(d) AS element_id"
        )
        return {row["element_id"] for row in rows}

    def _tag_new_documents(self, existing_ids: set[str], title: str) -> None:
        rows = self.graph.query(
            "MATCH (d:Document) RETURN elementId(d) AS element_id"
        )
        new_ids = [row["element_id"] for row in rows if row["element_id"] not in existing_ids]
        for element_id in new_ids:
            self.graph.query(
                """
                MATCH (d:Document)
                WHERE elementId(d) = $element_id
                SET d.title = $title, d.source = $title
                """,
                params={"element_id": element_id, "title": title},
            )

    async def ingest_documents(
        self,
        documents: list[dict[str, str]],
        clear_existing: bool = False,
    ) -> IngestResponse:
        """Ingest multiple titled documents sequentially (append-friendly)."""
        if clear_existing:
            clear_database()

        total_nodes = 0
        total_relationships = 0
        ingested_titles: list[str] = []

        for doc in documents:
            result = await self.ingest_text(
                text=doc["text"],
                clear_existing=False,
                title=doc.get("title"),
            )
            if result.status != "success":
                return result
            total_nodes += result.nodes_created
            total_relationships += result.relationships_created
            if doc.get("title"):
                ingested_titles.append(doc["title"])

        title_summary = ", ".join(ingested_titles) if ingested_titles else "documents"
        return IngestResponse(
            status="success",
            message=f"Ingested {len(documents)} documents ({title_summary})",
            nodes_created=total_nodes,
            relationships_created=total_relationships,
        )

    async def get_graph_status(self) -> dict:
        """
        Get current status of the Knowledge Graph.
        
        Returns:
            Dictionary with node and relationship counts
        """
        try:
            # Count nodes by type
            node_query = """
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
            """
            node_results = self.graph.query(node_query)
            
            # Count relationships by type
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
            """
            rel_results = self.graph.query(rel_query)
            
            # Total counts
            total_nodes_query = "MATCH (n) RETURN count(n) as count"
            total_rels_query = "MATCH ()-[r]->() RETURN count(r) as count"
            
            total_nodes = self.graph.query(total_nodes_query)[0]["count"]
            total_rels = self.graph.query(total_rels_query)[0]["count"]

            embed_stats = self.graph.query(
                """
                MATCH (d:Document)
                RETURN
                    count(d) AS total_documents,
                    count(d.embedding) AS embedded_documents
                """
            )
            
            return {
                "status": "success",
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "nodes_by_type": node_results,
                "relationships_by_type": rel_results,
                "documents": embed_stats[0] if embed_stats else {},
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def clear_graph(self):
        """Clear all data from the Knowledge Graph."""
        clear_database()

    async def list_documents(self) -> list[dict]:
        """
        List ingested documents grouped by title.

        Each uploaded/sample document is split into several :Document chunk nodes
        that all share the same `title`/`source` tag (set by `_tag_new_documents`).
        This groups them back into one row per document with useful counts.
        Untitled raw-text ingests (no title/source) are omitted.
        """
        rows = self.graph.query(
            """
            MATCH (d:Document)
            WITH coalesce(d.title, d.source) AS title, d
            WHERE title IS NOT NULL
            OPTIONAL MATCH (d)-[:MENTIONS]->(e)
            WHERE NOT e:Document
            RETURN
                title AS title,
                count(DISTINCT d) AS chunk_count,
                count(DISTINCT e) AS entity_count,
                count(DISTINCT d.embedding) AS embedded_count
            ORDER BY title
            """
        )
        return rows

    async def delete_document(self, title: str) -> dict:
        """
        Delete a document (all of its chunks) and prune the entities it added.

        An entity is pruned only if every one of its incoming MENTIONS edges comes
        from this document's chunks — i.e. no other document mentions it. Entities
        shared with other documents are preserved. Entity-to-entity relationships
        are removed implicitly via DETACH DELETE when an endpoint is pruned.
        """
        chunk_rows = self.graph.query(
            """
            MATCH (d:Document)
            WHERE coalesce(d.title, d.source) = $title
            RETURN count(d) AS chunk_count
            """,
            params={"title": title},
        )
        chunk_count = chunk_rows[0]["chunk_count"] if chunk_rows else 0
        if chunk_count == 0:
            return {
                "status": "not_found",
                "message": f"No document found with title '{title}'",
                "deleted_documents": 0,
                "deleted_entities": 0,
            }

        # Entities mentioned exclusively by this document's chunks.
        orphan_rows = self.graph.query(
            """
            MATCH (d:Document)-[:MENTIONS]->(e)
            WHERE coalesce(d.title, d.source) = $title AND NOT e:Document
            WITH DISTINCT e
            WHERE NOT EXISTS {
                MATCH (other:Document)-[:MENTIONS]->(e)
                WHERE coalesce(other.title, other.source) <> $title
            }
            RETURN elementId(e) AS element_id
            """,
            params={"title": title},
        )
        orphan_ids = [row["element_id"] for row in orphan_rows]

        if orphan_ids:
            self.graph.query(
                """
                MATCH (e)
                WHERE elementId(e) IN $element_ids
                DETACH DELETE e
                """,
                params={"element_ids": orphan_ids},
            )

        # Delete the document chunks themselves (removes their MENTIONS edges).
        self.graph.query(
            """
            MATCH (d:Document)
            WHERE coalesce(d.title, d.source) = $title
            DETACH DELETE d
            """,
            params={"title": title},
        )

        return {
            "status": "success",
            "message": (
                f"Deleted '{title}': {chunk_count} document chunk(s) "
                f"and {len(orphan_ids)} entity node(s) it uniquely added"
            ),
            "deleted_documents": chunk_count,
            "deleted_entities": len(orphan_ids),
        }

    def _node_display_name(self, props: dict, node_type: str) -> str:
        for key in ("name", "id", "title", "description", "status"):
            if props.get(key):
                return str(props[key])[:48]
        return node_type

    async def get_graph_visualization(self, limit: int = 150) -> GraphVisualizationResponse:
        """
        Fetch nodes and relationships for frontend graph visualization.
        """
        query = """
        MATCH (n)-[r]->(m)
        RETURN
            elementId(n) AS source_id,
            coalesce(labels(n)[0], 'Entity') AS source_type,
            properties(n) AS source_props,
            type(r) AS rel_type,
            properties(r) AS rel_props,
            elementId(m) AS target_id,
            coalesce(labels(m)[0], 'Entity') AS target_type,
            properties(m) AS target_props
        LIMIT $limit
        """
        results = self.graph.query(query, params={"limit": limit})

        nodes_map: dict[str, GraphNode] = {}
        links: list[GraphLink] = []

        for row in results:
            source_id = str(row["source_id"])
            target_id = str(row["target_id"])
            source_type = row["source_type"]
            target_type = row["target_type"]
            source_props = row.get("source_props") or {}
            target_props = row.get("target_props") or {}

            if source_id not in nodes_map:
                nodes_map[source_id] = GraphNode(
                    id=source_id,
                    label=self._node_display_name(source_props, source_type),
                    type=source_type,
                    properties=source_props,
                )
            if target_id not in nodes_map:
                nodes_map[target_id] = GraphNode(
                    id=target_id,
                    label=self._node_display_name(target_props, target_type),
                    type=target_type,
                    properties=target_props,
                )

            links.append(
                GraphLink(
                    source=source_id,
                    target=target_id,
                    type=row.get("rel_type") or "RELATED_TO",
                    properties=row.get("rel_props") or {},
                )
            )

        orphan_query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN
            elementId(n) AS node_id,
            coalesce(labels(n)[0], 'Entity') AS node_type,
            properties(n) AS node_props
        LIMIT $limit
        """
        orphan_results = self.graph.query(orphan_query, params={"limit": limit})
        for row in orphan_results:
            node_id = str(row["node_id"])
            node_type = row["node_type"]
            node_props = row.get("node_props") or {}
            if node_id not in nodes_map:
                nodes_map[node_id] = GraphNode(
                    id=node_id,
                    label=self._node_display_name(node_props, node_type),
                    type=node_type,
                    properties=node_props,
                )

        status = await self.get_graph_status()
        return GraphVisualizationResponse(
            nodes=list(nodes_map.values()),
            links=links,
            total_nodes=status.get("total_nodes", len(nodes_map)),
            total_relationships=status.get("total_relationships", len(links)),
        )

# Made with Bob
