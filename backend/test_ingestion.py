"""
Test script for ingestion service.
Run this to test the Knowledge Graph ingestion with mock data.
"""
import asyncio
from mock_data import get_mock_documents
from services.ingestion_service import IngestionService
from database import neo4j_connection


async def main():
    """Test the ingestion pipeline."""
    print("🧪 Testing Knowledge Graph Ingestion...")
    print("=" * 60)
    
    # Verify Neo4j connection
    print("\n1. Verifying Neo4j connection...")
    if neo4j_connection.verify_connectivity():
        print("   ✅ Neo4j connection successful")
    else:
        print("   ❌ Neo4j connection failed")
        return
    
    # Create ingestion service
    print("\n2. Creating ingestion service...")
    service = IngestionService()
    print("   ✅ Service created")
    
    # Get mock documents
    print("\n3. Loading mock company documents...")
    documents = get_mock_documents()
    print(f"   ✅ Loaded {len(documents)} documents")
    for doc in documents:
        print(f"     - {doc['title']}")
    
    # Ingest data
    print("\n4. Ingesting documents into Knowledge Graph...")
    print("   (This may take a few minutes...)")
    result = await service.ingest_documents(documents, clear_existing=True)
    
    print(f"\n   Status: {result.status}")
    print(f"   Message: {result.message}")
    print(f"   Nodes created: {result.nodes_created}")
    print(f"   Relationships created: {result.relationships_created}")
    
    # Get graph status
    print("\n5. Checking graph status...")
    status = await service.get_graph_status()
    
    if status['status'] == 'success':
        print(f"   Total nodes: {status['total_nodes']}")
        print(f"   Total relationships: {status['total_relationships']}")
        if status.get('documents'):
            print(f"   Documents embedded: {status['documents']}")
        
        print("\n   Nodes by type:")
        for node in status['nodes_by_type']:
            print(f"     - {node['label']}: {node['count']}")
        
        print("\n   Relationships by type:")
        for rel in status['relationships_by_type']:
            print(f"     - {rel['type']}: {rel['count']}")
    
    print("\n" + "=" * 60)
    print("✅ Ingestion test complete!")
    print("\nYou can now:")
    print("  1. Query the data using the Librarian")
    print("  2. Start debates using the Boardroom")
    print("  3. Add more documents from the Atlas tab")
    
    # Close connection
    neo4j_connection.close()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
