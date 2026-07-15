"""
Neo4j database connection and utilities.
Manages the connection to Neo4j AuraDB and provides helper functions.
"""
from neo4j import GraphDatabase
from typing import Optional
from config import get_settings

settings = get_settings()


class Neo4jConnection:
    """Manages Neo4j database connection."""
    
    def __init__(self):
        self._driver: Optional[GraphDatabase.driver] = None
    
    def connect(self):
        """Establish connection to Neo4j AuraDB."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password)
            )
        return self._driver
    
    def close(self):
        """Close the Neo4j connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
    
    def verify_connectivity(self) -> bool:
        """
        Verify that the connection to Neo4j is working.
        Returns True if connection is successful, False otherwise.
        """
        try:
            driver = self.connect()
            driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Neo4j connectivity check failed: {e}")
            return False
    
    def get_driver(self):
        """Get the Neo4j driver instance."""
        return self.connect()


# Global connection instance
neo4j_connection = Neo4jConnection()


def get_neo4j_driver():
    """Dependency injection for Neo4j driver."""
    return neo4j_connection.get_driver()


from services.hybrid_retrieval_service import HybridRetrievalService

_hybrid_retrieval: HybridRetrievalService | None = None


def get_hybrid_retrieval_service() -> HybridRetrievalService:
    global _hybrid_retrieval
    if _hybrid_retrieval is None:
        _hybrid_retrieval = HybridRetrievalService()
    return _hybrid_retrieval


def init_vector_indexes() -> None:
    """Ensure Neo4j vector and full-text indexes exist for Document nodes."""
    try:
        get_hybrid_retrieval_service().ensure_indexes()
    except Exception as e:
        print(f"Vector index initialization note: {e}")


def init_neo4j_schema():
    """
    Initialize Neo4j schema with constraints and indexes.
    This ensures data integrity and query performance.
    """
    driver = neo4j_connection.get_driver()
    
    constraints_and_indexes = [
        # Unique constraints
        "CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT department_id IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT client_id IF NOT EXISTS FOR (c:Client) REQUIRE c.id IS UNIQUE",
        
        # Indexes for common queries
        "CREATE INDEX employee_id_idx IF NOT EXISTS FOR (e:Employee) ON (e.id)",
        "CREATE INDEX project_id_idx IF NOT EXISTS FOR (p:Project) ON (p.id)",
        "CREATE INDEX department_id_idx IF NOT EXISTS FOR (d:Department) ON (d.id)",
        "CREATE INDEX employee_name IF NOT EXISTS FOR (e:Employee) ON (e.name)",
        "CREATE INDEX project_name IF NOT EXISTS FOR (p:Project) ON (p.name)",
        "CREATE INDEX department_name IF NOT EXISTS FOR (d:Department) ON (d.name)",
    ]
    
    with driver.session(database=settings.neo4j_database) as session:
        for query in constraints_and_indexes:
            try:
                session.run(query)
            except Exception as e:
                # Constraint/index might already exist
                print(f"Schema initialization note: {e}")

        # Backfill name from id for graphs ingested before normalization
        session.run(
            "MATCH (n) WHERE n.id IS NOT NULL AND n.name IS NULL SET n.name = n.id"
        )

    init_vector_indexes()


def clear_database():
    """
    Clear all nodes and relationships from the database.
    USE WITH CAUTION - This deletes all data!
    """
    driver = neo4j_connection.get_driver()
    with driver.session(database=settings.neo4j_database) as session:
        session.run("MATCH (n) DETACH DELETE n")

# Made with Bob
