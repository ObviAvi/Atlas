"""
FastAPI main application entry point.
Defines API routes and application lifecycle.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import get_settings
from database import neo4j_connection, init_neo4j_schema
from routers import ingest, librarian, boardroom

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting GraphRAG + Multi-Agent Debate System...")
    
    # Connect to Neo4j
    print("📊 Connecting to Neo4j AuraDB...")
    if neo4j_connection.verify_connectivity():
        print("✅ Neo4j connection successful")
        
        # Initialize schema
        print("🔧 Initializing Neo4j schema...")
        init_neo4j_schema()
        print("✅ Schema initialized")
    else:
        print("❌ Neo4j connection failed - check your credentials")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    neo4j_connection.close()
    print("✅ Neo4j connection closed")


# Create FastAPI app
app = FastAPI(
    title="GraphRAG + Multi-Agent Debate API",
    description="Backend API for Knowledge Graph construction and multi-agent debate system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "service": "GraphRAG + Multi-Agent Debate API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check including Neo4j connectivity."""
    neo4j_status = neo4j_connection.verify_connectivity()
    
    return {
        "status": "healthy" if neo4j_status else "degraded",
        "neo4j": "connected" if neo4j_status else "disconnected",
        "api": "operational"
    }


# Include routers
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(librarian.router, prefix="/api/librarian", tags=["Librarian"])
app.include_router(boardroom.router, prefix="/api/boardroom", tags=["Boardroom"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )

# Made with Bob
