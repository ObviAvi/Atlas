"""
Librarian service - hybrid GraphRAG: vector search + graph expansion + Cypher QA.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from config import get_settings
from models import LibrarianQueryResponse
from services.hybrid_retrieval_service import HybridRetrievalService

settings = get_settings()


def _extract_llm_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("text"):
                parts.append(str(block["text"]))
        return "\n".join(parts).strip()
    return str(content).strip()


class LibrarianService:
    """Service for querying the Knowledge Graph using hybrid GraphRAG."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.3,
        )

        self.graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )

        self.hybrid_retrieval = HybridRetrievalService()

        cypher_generation_template = """
        You are an expert at converting natural language questions into Cypher queries for Neo4j.

        CRITICAL RULES:
        1. The primary identifier property on almost all nodes is `id` (STRING), NOT `name`.
        2. Always inspect the Schema below — it is the source of truth for labels and properties.
        3. For entity lookups, prefer exact match on `id` when you know the full name:
           MATCH (p:Project {{id: 'Project Beta'}}) RETURN p
        4. When the user gives a partial or informal name, use case-insensitive CONTAINS on `id`:
           MATCH (p:Project) WHERE toLower(p.id) CONTAINS 'beta' RETURN p
        5. Employee full names are stored in `id` (e.g. {{id: 'Sarah Chen'}}).
        6. Do NOT query Document nodes — use structured entity labels only.
        7. Return enough columns to answer the question (node properties + relationship types).

        Example queries:
        - "Status of Project Beta?"
          MATCH (p:Project) WHERE toLower(p.id) CONTAINS 'project beta' RETURN p.id, p.status, p.description
        - "Who is Sarah Chen?"
          MATCH (e:Employee {{id: 'Sarah Chen'}}) RETURN e
        - "Who works on Project Alpha?"
          MATCH (e:Employee)-[:WORKS_ON]->(p:Project) WHERE toLower(p.id) CONTAINS 'project alpha' RETURN e.id, e.role, p.id

        Schema:
        {schema}

        Question: {question}

        Cypher Query (no markdown, no explanation):
        """

        cypher_prompt = PromptTemplate(
            template=cypher_generation_template,
            input_variables=["schema", "question"],
        )

        qa_generation_template = """
        You are a helpful assistant that provides factual answers based on company data.

        Use the following context to answer the question clearly and directly.
        Do not mention databases, graphs, or queries. If you don't have enough information, say so.

        Context:
        {context}

        Question: {question}

        Answer:
        """

        qa_prompt = PromptTemplate(
            template=qa_generation_template,
            input_variables=["context", "question"],
        )

        self.qa_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt,
            verbose=True,
            return_intermediate_steps=True,
            return_direct=False,
            allow_dangerous_requests=True,
            validate_cypher=True,
        )

        self.synthesis_prompt = PromptTemplate(
            template="""
You are the Librarian for a company knowledge base. Answer the user's question clearly and directly.

Rules:
- Write in plain, professional prose as if speaking to a colleague.
- Do NOT mention chunks, vectors, embeddings, Cypher, graph queries, indexes, or retrieval methods.
- Do NOT cite source types like "Chunk 1" or "Cypher Query".
- If information is missing, say so briefly.
- Use short paragraphs or bullets when helpful.

Context (for your use only — do not describe how you obtained it):

Document excerpts:
{vector_context}

Related company records:
{linked_entities}

Structured facts:
Query: {cypher_query}
Results: {cypher_context}

Question: {question}

Answer:
""",
            input_variables=[
                "vector_context",
                "linked_entities",
                "cypher_query",
                "cypher_context",
                "question",
            ],
        )

    def _extract_cypher_steps(self, intermediate_steps: list) -> tuple[str, str]:
        cypher_query = ""
        cypher_context = ""
        for step in intermediate_steps:
            if not isinstance(step, dict):
                continue
            if step.get("query"):
                cypher_query = step["query"]
            if step.get("context") is not None:
                cypher_context = str(step["context"])
        return cypher_query, cypher_context

    async def query(self, query: str) -> LibrarianQueryResponse:
        """
        Hybrid GraphRAG query:
        1. Vector + full-text search on Document chunks
        2. Graph expansion via MENTIONS
        3. Cypher QA on structured entities
        4. LLM synthesis over combined context
        """
        try:
            hybrid = self.hybrid_retrieval.retrieve(query)

            result = self.qa_chain.invoke({"query": query})
            cypher_query, cypher_context = self._extract_cypher_steps(
                result.get("intermediate_steps", [])
            )

            has_hybrid = bool(hybrid["vector_context"] or hybrid["graph_context"])
            has_cypher = bool(cypher_context and cypher_context not in ("[]", ""))

            if has_hybrid or has_cypher:
                synthesis = self.llm.invoke(
                    self.synthesis_prompt.format(
                        vector_context=hybrid["vector_context"] or "None",
                        linked_entities=hybrid["graph_context"] or "None",
                        cypher_query=cypher_query or "None",
                        cypher_context=cypher_context or "None",
                        question=query,
                    )
                )
                answer = _extract_llm_text(synthesis.content)
            else:
                answer = result.get("result", "No answer found")

            sources = list(hybrid["sources"])
            if cypher_query:
                sources.append({"type": "cypher_query", "query": cypher_query})
            if cypher_context and cypher_context not in ("[]", "", "None"):
                sources.append({"type": "cypher_results", "context": cypher_context})

            return LibrarianQueryResponse(
                query=query,
                answer=answer,
                sources=sources,
            )

        except Exception as e:
            return LibrarianQueryResponse(
                query=query,
                answer=f"Error processing query: {str(e)}",
                sources=[],
            )

# Made with Bob
