"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class IngestRequest(BaseModel):
    """Request model for data ingestion."""
    text: str = Field(..., description="Raw text to ingest into the Knowledge Graph")
    title: Optional[str] = Field(
        default=None,
        description="Optional document title stored on ingested Document nodes",
    )
    clear_existing: bool = Field(
        default=False,
        description="Whether to clear existing data before ingestion",
    )


class IngestResponse(BaseModel):
    """Response model for data ingestion."""
    status: str
    message: str
    nodes_created: int
    relationships_created: int


class DocumentSummary(BaseModel):
    """Summary of one ingested document (grouped from its chunk nodes)."""
    title: str
    chunk_count: int
    entity_count: int
    embedded_count: int


class DocumentListResponse(BaseModel):
    """Response model listing ingested documents."""
    documents: List[DocumentSummary] = Field(default_factory=list)


class DeleteDocumentResponse(BaseModel):
    """Response model for deleting a single document and its unique entities."""
    status: str
    message: str
    deleted_documents: int
    deleted_entities: int


class LibrarianQueryRequest(BaseModel):
    """Request model for Librarian queries."""
    query: str = Field(..., description="User's question to query the Knowledge Graph")


class LibrarianQueryResponse(BaseModel):
    """Response model for Librarian queries."""
    query: str
    answer: str
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Source nodes and relationships used to generate the answer"
    )


class BoardroomDebateRequest(BaseModel):
    """Request model for Boardroom debates."""
    idea: str = Field(..., description="User's idea to be debated")
    rounds: Optional[int] = Field(
        default=3,
        description="Number of debate rounds between agents"
    )


class AgentMessage(BaseModel):
    """Model for individual agent messages in the debate."""
    agent: str = Field(..., description="Name of the agent (Strategist, Risk Analyst, etc.)")
    message: str = Field(..., description="The agent's message")
    timestamp: str = Field(..., description="ISO timestamp of the message")


class BoardroomDebateResponse(BaseModel):
    """Response model for Boardroom debates."""
    idea: str
    debate_transcript: List[AgentMessage]
    final_verdict: str
    data_sources: List[str] = Field(
        default_factory=list,
        description="Neo4j data points referenced in the debate"
    )


class NodeType(str, Enum):
    """Enumeration of supported node types in the Knowledge Graph."""
    EMPLOYEE = "Employee"
    PROJECT = "Project"
    DEPARTMENT = "Department"
    CLIENT = "Client"
    OKR = "OKR"
    BUDGET = "Budget"


class RelationshipType(str, Enum):
    """Enumeration of supported relationship types in the Knowledge Graph."""
    WORKS_ON = "WORKS_ON"
    MANAGES = "MANAGES"
    FOCUSED_ON = "FOCUSED_ON"
    REPORTS_TO = "REPORTS_TO"
    ALLOCATED_TO = "ALLOCATED_TO"
    DEPENDS_ON = "DEPENDS_ON"
    SERVES = "SERVES"


class GraphNode(BaseModel):
    """Node for graph visualization."""
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphLink(BaseModel):
    """Relationship for graph visualization."""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphVisualizationResponse(BaseModel):
    """Full graph payload for frontend visualization."""
    nodes: List[GraphNode]
    links: List[GraphLink]
    total_nodes: int
    total_relationships: int

# Made with Bob
