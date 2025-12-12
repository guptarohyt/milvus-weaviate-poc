"""
Milvus client implementation for reinsurance POC.
Handles connection, indexing, and search operations.
"""

import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)
from sentence_transformers import SentenceTransformer

from config import config


class MilvusReinsuranceClient:
    """Milvus client for reinsurance use cases."""

    def __init__(self, host: str = None, port: str = None):
        """Initialize Milvus client.

        Args:
            host: Milvus server host (default: from config/environment)
            port: Milvus server port (default: from config/environment)
        """
        self.host = host or config.milvus.host
        self.port = str(port) if port else str(config.milvus.port)
        self.connection_alias = "default"
        self.model = SentenceTransformer(config.embedding.text_model)
        self.embedding_dim = config.embedding.text_dim
        self.collections = {}

    def connect(self):
        """Connect to Milvus server."""
        print(f"Connecting to Milvus at {self.host}:{self.port}...")
        connections.connect(
            alias=self.connection_alias,
            host=self.host,
            port=self.port
        )
        print("✓ Connected to Milvus")

    def disconnect(self):
        """Disconnect from Milvus server."""
        connections.disconnect(alias=self.connection_alias)
        print("✓ Disconnected from Milvus")

    def create_collection(self, collection_name: str, schema_type: str):
        """Create a collection with appropriate schema."""
        # Drop if exists
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"  Dropped existing collection: {collection_name}")

        # Define schema based on type
        if schema_type == "policy":
            schema = self._get_policy_schema()
        elif schema_type == "claim":
            schema = self._get_claim_schema()
        elif schema_type == "knowledge":
            schema = self._get_knowledge_schema()
        else:
            raise ValueError(f"Unknown schema type: {schema_type}")

        # Create collection
        collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.connection_alias
        )

        # Create index on embedding field
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        self.collections[collection_name] = collection
        print(f"✓ Created collection: {collection_name}")

        return collection

    def _get_policy_schema(self) -> CollectionSchema:
        """Get schema for policy collection."""
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="policy_type", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="cedent", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="territory", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="limit", dtype=DataType.INT64),
            FieldSchema(name="premium", dtype=DataType.INT64),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        ]
        return CollectionSchema(fields=fields, description="Reinsurance policies")

    def _get_claim_schema(self) -> CollectionSchema:
        """Get schema for claim collection."""
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="peril", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="loss_amount", dtype=DataType.INT64),
            FieldSchema(name="location", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        ]
        return CollectionSchema(fields=fields, description="Insurance claims")

    def _get_knowledge_schema(self) -> CollectionSchema:
        """Get schema for knowledge base collection."""
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="topic", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
        ]
        return CollectionSchema(fields=fields, description="Knowledge base articles")

    def insert_policies(self, policies: List[Dict]):
        """Insert policies into Milvus."""
        collection_name = "policies"
        collection = self.collections.get(collection_name)
        if not collection:
            collection = self.create_collection(collection_name, "policy")

        # Prepare data
        texts = [p["description"] for p in policies]
        embeddings = self.model.encode(texts, show_progress_bar=True).tolist()

        data = [
            [p["id"] for p in policies],
            [p["policy_type"] for p in policies],
            [p["cedent"] for p in policies],
            [p["territory"] for p in policies],
            [p["limit"] for p in policies],
            [p["premium"] for p in policies],
            [p["description"] for p in policies],
            embeddings
        ]

        collection.insert(data)
        collection.flush()
        print(f"✓ Inserted {len(policies)} policies")

    def insert_claims(self, claims: List[Dict]):
        """Insert claims into Milvus."""
        collection_name = "claims"
        collection = self.collections.get(collection_name)
        if not collection:
            collection = self.create_collection(collection_name, "claim")

        # Prepare data
        texts = [c["description"] for c in claims]
        embeddings = self.model.encode(texts, show_progress_bar=True).tolist()

        data = [
            [c["id"] for c in claims],
            [c["category"] for c in claims],
            [c["status"] for c in claims],
            [c["peril"] for c in claims],
            [c["loss_amount"] for c in claims],
            [c["location"] for c in claims],
            [c["description"] for c in claims],
            embeddings
        ]

        collection.insert(data)
        collection.flush()
        print(f"✓ Inserted {len(claims)} claims")

    def insert_knowledge(self, articles: List[Dict]):
        """Insert knowledge base articles into Milvus."""
        collection_name = "knowledge"
        collection = self.collections.get(collection_name)
        if not collection:
            collection = self.create_collection(collection_name, "knowledge")

        # Prepare data
        texts = [f"{a['title']} {a['content']}" for a in articles]
        embeddings = self.model.encode(texts, show_progress_bar=True).tolist()

        data = [
            [a["id"] for a in articles],
            [a["title"] for a in articles],
            [a["topic"] for a in articles],
            [a["content"] for a in articles],
            [a["author"] for a in articles],
            embeddings
        ]

        collection.insert(data)
        collection.flush()
        print(f"✓ Inserted {len(articles)} knowledge base articles")

    def load_collections(self):
        """Load all collections into memory."""
        for name, collection in self.collections.items():
            collection.load()
            print(f"✓ Loaded collection: {name}")

    def search_policies(self, query: str, limit: int = 10, filters: Optional[str] = None) -> List[Dict]:
        """Search for similar policies."""
        collection = self.collections.get("policies")
        if not collection:
            raise ValueError("Policies collection not found")

        # Generate query embedding
        query_embedding = self.model.encode([query]).tolist()

        # Search parameters
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        # Execute search
        start_time = time.time()
        results = collection.search(
            data=query_embedding,
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=filters,
            output_fields=["id", "policy_type", "cedent", "territory", "limit", "description"]
        )
        search_time = time.time() - start_time

        return {
            "results": self._format_results(results[0]),
            "search_time": search_time
        }

    def search_claims(self, query: str, limit: int = 10, filters: Optional[str] = None) -> List[Dict]:
        """Search for similar claims."""
        collection = self.collections.get("claims")
        if not collection:
            raise ValueError("Claims collection not found")

        query_embedding = self.model.encode([query]).tolist()
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        start_time = time.time()
        results = collection.search(
            data=query_embedding,
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=filters,
            output_fields=["id", "category", "status", "peril", "loss_amount", "description"]
        )
        search_time = time.time() - start_time

        return {
            "results": self._format_results(results[0]),
            "search_time": search_time
        }

    def search_knowledge(self, query: str, limit: int = 10, filters: Optional[str] = None) -> List[Dict]:
        """Search knowledge base."""
        collection = self.collections.get("knowledge")
        if not collection:
            raise ValueError("Knowledge collection not found")

        query_embedding = self.model.encode([query]).tolist()
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        start_time = time.time()
        results = collection.search(
            data=query_embedding,
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=filters,
            output_fields=["id", "title", "topic", "content", "author"]
        )
        search_time = time.time() - start_time

        return {
            "results": self._format_results(results[0]),
            "search_time": search_time
        }

    def _format_results(self, results) -> List[Dict]:
        """Format search results."""
        formatted = []
        for hit in results:
            result = {
                "id": hit.id,
                "distance": hit.distance,
                "score": 1 / (1 + hit.distance)  # Convert distance to similarity score
            }
            # Add all entity fields
            # In pymilvus 2.4.0, entity is a dict-like object
            if hasattr(hit, 'entity'):
                # Access entity fields using get() method
                entity = hit.entity
                # Get all field names that were requested in output_fields
                for field in ['policy_type', 'cedent', 'territory', 'limit', 'description',
                             'category', 'status', 'peril', 'loss_amount', 'location',
                             'title', 'topic', 'content', 'author']:
                    try:
                        value = entity.get(field)
                        if value is not None:
                            result[field] = value
                    except:
                        pass
            formatted.append(result)
        return formatted

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = {
                "num_entities": collection.num_entities
            }
        return stats


def main():
    """Example usage of Milvus client."""
    client = MilvusReinsuranceClient()

    try:
        # Connect
        client.connect()

        # Load data
        data_dir = Path("data")
        with open(data_dir / "policies.json") as f:
            policies = json.load(f)
        with open(data_dir / "claims.json") as f:
            claims = json.load(f)
        with open(data_dir / "knowledge_base.json") as f:
            knowledge = json.load(f)

        # Insert data
        print("\nInserting data into Milvus...")
        client.insert_policies(policies[:100])  # Insert subset for testing
        client.insert_claims(claims[:100])
        client.insert_knowledge(knowledge[:100])

        # Load collections
        print("\nLoading collections...")
        client.load_collections()

        # Example searches
        print("\n" + "="*50)
        print("Example Searches")
        print("="*50)

        print("\n1. Policy Search:")
        results = client.search_policies("hurricane coverage in Florida", limit=3)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['id']}: {r['policy_type']} (score: {r['score']:.3f})")

        print("\n2. Claims Search:")
        results = client.search_claims("water damage from flooding", limit=3)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['id']}: {r['category']} (score: {r['score']:.3f})")

        print("\n3. Knowledge Base Search:")
        results = client.search_knowledge("underwriting guidelines for catastrophe risk", limit=3)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['id']}: {r['title']} (score: {r['score']:.3f})")

        # Stats
        print("\n" + "="*50)
        print("Collection Statistics")
        print("="*50)
        stats = client.get_stats()
        for name, stat in stats.items():
            print(f"{name}: {stat['num_entities']} entities, loaded: {stat['loaded']}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
