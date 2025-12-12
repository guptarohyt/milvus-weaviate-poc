"""
Weaviate client implementation for reinsurance POC.
Handles connection, indexing, and search operations.
"""

import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter, MetadataQuery
from sentence_transformers import SentenceTransformer

from config import config


class WeaviateReinsuranceClient:
    """Weaviate client for reinsurance use cases."""

    def __init__(self, host: str = None, port: str = None):
        """Initialize Weaviate client.

        Args:
            host: Weaviate server host (default: from config/environment)
            port: Weaviate server port (default: from config/environment)
        """
        self.host = host or config.weaviate.host
        self.port = str(port) if port else str(config.weaviate.port)
        self.url = f"http://{self.host}:{self.port}"
        self.client = None
        self.model = SentenceTransformer(config.embedding.text_model)

    def connect(self):
        """Connect to Weaviate server."""
        print(f"Connecting to Weaviate at {self.url}...")
        self.client = weaviate.connect_to_local(
            host=self.host,
            port=int(self.port)
        )
        print("✓ Connected to Weaviate")

    def disconnect(self):
        """Disconnect from Weaviate server."""
        if self.client:
            self.client.close()
            print("✓ Disconnected from Weaviate")

    def create_collections(self):
        """Create all required collections."""
        self._create_policy_collection()
        self._create_claim_collection()
        self._create_knowledge_collection()

    def _create_policy_collection(self):
        """Create policy collection."""
        collection_name = "Policy"

        # Delete if exists
        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

        # Create collection
        self.client.collections.create(
            name=collection_name,
            properties=[
                Property(name="policy_id", data_type=DataType.TEXT),
                Property(name="policy_type", data_type=DataType.TEXT),
                Property(name="cedent", data_type=DataType.TEXT),
                Property(name="territory", data_type=DataType.TEXT),
                Property(name="limit", data_type=DataType.NUMBER),
                Property(name="premium", data_type=DataType.NUMBER),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="inception_date", data_type=DataType.TEXT),
                Property(name="expiry_date", data_type=DataType.TEXT),
            ],
            vectorizer_config=Configure.Vectorizer.none()
        )
        print(f"✓ Created collection: {collection_name}")

    def _create_claim_collection(self):
        """Create claim collection."""
        collection_name = "Claim"

        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

        self.client.collections.create(
            name=collection_name,
            properties=[
                Property(name="claim_id", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
                Property(name="status", data_type=DataType.TEXT),
                Property(name="peril", data_type=DataType.TEXT),
                Property(name="loss_amount", data_type=DataType.NUMBER),
                Property(name="location", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="loss_date", data_type=DataType.TEXT),
            ],
            vectorizer_config=Configure.Vectorizer.none()
        )
        print(f"✓ Created collection: {collection_name}")

    def _create_knowledge_collection(self):
        """Create knowledge base collection."""
        collection_name = "Knowledge"

        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

        self.client.collections.create(
            name=collection_name,
            properties=[
                Property(name="article_id", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="topic", data_type=DataType.TEXT),
                Property(name="content", data_type=DataType.TEXT),
                Property(name="author", data_type=DataType.TEXT),
                Property(name="created_date", data_type=DataType.TEXT),
            ],
            vectorizer_config=Configure.Vectorizer.none()
        )
        print(f"✓ Created collection: {collection_name}")

    def insert_policies(self, policies: List[Dict]):
        """Insert policies into Weaviate."""
        collection = self.client.collections.get("Policy")

        # Generate embeddings
        texts = [p["description"] for p in policies]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        # Prepare data objects
        data_objects = []
        for i, policy in enumerate(policies):
            data_objects.append({
                "policy_id": policy["id"],
                "policy_type": policy["policy_type"],
                "cedent": policy["cedent"],
                "territory": policy["territory"],
                "limit": policy["limit"],
                "premium": policy["premium"],
                "description": policy["description"],
                "inception_date": policy["inception_date"],
                "expiry_date": policy["expiry_date"],
            })

        # Batch insert
        with collection.batch.dynamic() as batch:
            for i, obj in enumerate(data_objects):
                batch.add_object(
                    properties=obj,
                    vector=embeddings[i].tolist()
                )

        print(f"✓ Inserted {len(policies)} policies")

    def insert_claims(self, claims: List[Dict]):
        """Insert claims into Weaviate."""
        collection = self.client.collections.get("Claim")

        texts = [c["description"] for c in claims]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        data_objects = []
        for claim in claims:
            data_objects.append({
                "claim_id": claim["id"],
                "category": claim["category"],
                "status": claim["status"],
                "peril": claim["peril"],
                "loss_amount": claim["loss_amount"],
                "location": claim["location"],
                "description": claim["description"],
                "loss_date": claim["loss_date"],
            })

        with collection.batch.dynamic() as batch:
            for i, obj in enumerate(data_objects):
                batch.add_object(
                    properties=obj,
                    vector=embeddings[i].tolist()
                )

        print(f"✓ Inserted {len(claims)} claims")

    def insert_knowledge(self, articles: List[Dict]):
        """Insert knowledge base articles into Weaviate."""
        collection = self.client.collections.get("Knowledge")

        texts = [f"{a['title']} {a['content']}" for a in articles]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        data_objects = []
        for article in articles:
            data_objects.append({
                "article_id": article["id"],
                "title": article["title"],
                "topic": article["topic"],
                "content": article["content"],
                "author": article["author"],
                "created_date": article["created_date"],
            })

        with collection.batch.dynamic() as batch:
            for i, obj in enumerate(data_objects):
                batch.add_object(
                    properties=obj,
                    vector=embeddings[i].tolist()
                )

        print(f"✓ Inserted {len(articles)} knowledge base articles")

    def search_policies(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> Dict:
        """Search for similar policies."""
        collection = self.client.collections.get("Policy")

        # Generate query embedding
        query_embedding = self.model.encode([query])[0].tolist()

        # Execute search
        start_time = time.time()

        if filters:
            # Build filter
            weaviate_filter = self._build_filter(filters)
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                filters=weaviate_filter,
                return_metadata=MetadataQuery(distance=True)
            )
        else:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )

        search_time = time.time() - start_time

        return {
            "results": self._format_results(response.objects),
            "search_time": search_time
        }

    def search_claims(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> Dict:
        """Search for similar claims."""
        collection = self.client.collections.get("Claim")

        query_embedding = self.model.encode([query])[0].tolist()

        start_time = time.time()

        if filters:
            weaviate_filter = self._build_filter(filters)
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                filters=weaviate_filter,
                return_metadata=MetadataQuery(distance=True)
            )
        else:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )

        search_time = time.time() - start_time

        return {
            "results": self._format_results(response.objects),
            "search_time": search_time
        }

    def search_knowledge(self, query: str, limit: int = 10, filters: Optional[Dict] = None) -> Dict:
        """Search knowledge base."""
        collection = self.client.collections.get("Knowledge")

        query_embedding = self.model.encode([query])[0].tolist()

        start_time = time.time()

        if filters:
            weaviate_filter = self._build_filter(filters)
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                filters=weaviate_filter,
                return_metadata=MetadataQuery(distance=True)
            )
        else:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )

        search_time = time.time() - start_time

        return {
            "results": self._format_results(response.objects),
            "search_time": search_time
        }

    def _build_filter(self, filters: Dict) -> Filter:
        """Build Weaviate filter from dict."""
        # Simple implementation - can be extended
        field = filters.get("field")
        operator = filters.get("operator")
        value = filters.get("value")

        if operator == "equal":
            return Filter.by_property(field).equal(value)
        elif operator == "greater_than":
            return Filter.by_property(field).greater_than(value)
        elif operator == "less_than":
            return Filter.by_property(field).less_than(value)
        else:
            return None

    def _format_results(self, objects) -> List[Dict]:
        """Format search results."""
        formatted = []
        for obj in objects:
            result = {
                "uuid": str(obj.uuid),
                "distance": obj.metadata.distance if hasattr(obj.metadata, 'distance') else None,
                "score": 1 / (1 + obj.metadata.distance) if hasattr(obj.metadata, 'distance') else None,
                "properties": obj.properties
            }
            formatted.append(result)
        return formatted

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        stats = {}
        for collection_name in ["Policy", "Claim", "Knowledge"]:
            collection = self.client.collections.get(collection_name)
            stats[collection_name] = {
                "count": len(collection)
            }
        return stats

    def hybrid_search_knowledge(self, query: str, limit: int = 10, alpha: float = 0.5) -> Dict:
        """
        Perform hybrid search (vector + keyword) on knowledge base.
        alpha: 0 = pure keyword, 1 = pure vector, 0.5 = balanced
        """
        collection = self.client.collections.get("Knowledge")

        query_embedding = self.model.encode([query])[0].tolist()

        start_time = time.time()
        response = collection.query.hybrid(
            query=query,
            vector=query_embedding,
            alpha=alpha,
            limit=limit,
            return_metadata=MetadataQuery(score=True)
        )
        search_time = time.time() - start_time

        formatted_results = []
        for obj in response.objects:
            result = {
                "uuid": str(obj.uuid),
                "score": obj.metadata.score if hasattr(obj.metadata, 'score') else None,
                "properties": obj.properties
            }
            formatted_results.append(result)

        return {
            "results": formatted_results,
            "search_time": search_time
        }


def main():
    """Example usage of Weaviate client."""
    client = WeaviateReinsuranceClient()

    try:
        # Connect
        client.connect()

        # Create collections
        print("\nCreating collections...")
        client.create_collections()

        # Load data
        data_dir = Path("data")
        with open(data_dir / "policies.json") as f:
            policies = json.load(f)
        with open(data_dir / "claims.json") as f:
            claims = json.load(f)
        with open(data_dir / "knowledge_base.json") as f:
            knowledge = json.load(f)

        # Insert data
        print("\nInserting data into Weaviate...")
        client.insert_policies(policies[:100])  # Insert subset for testing
        client.insert_claims(claims[:100])
        client.insert_knowledge(knowledge[:100])

        # Example searches
        print("\n" + "="*50)
        print("Example Searches")
        print("="*50)

        print("\n1. Policy Search:")
        results = client.search_policies("hurricane coverage in Florida", limit=3)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['properties']['policy_id']}: {r['properties']['policy_type']} (score: {r['score']:.3f})")

        print("\n2. Claims Search:")
        results = client.search_claims("water damage from flooding", limit=3)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['properties']['claim_id']}: {r['properties']['category']} (score: {r['score']:.3f})")

        print("\n3. Knowledge Base Search:")
        results = client.search_knowledge("underwriting guidelines for catastrophe risk", limit=3)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['properties']['article_id']}: {r['properties']['title']} (score: {r['score']:.3f})")

        print("\n4. Hybrid Search (Knowledge Base):")
        results = client.hybrid_search_knowledge("regulatory compliance requirements", limit=3, alpha=0.5)
        print(f"   Search time: {results['search_time']:.4f}s")
        for r in results['results']:
            print(f"   - {r['properties']['article_id']}: {r['properties']['title']} (score: {r['score']:.3f})")

        # Stats
        print("\n" + "="*50)
        print("Collection Statistics")
        print("="*50)
        stats = client.get_stats()
        for name, stat in stats.items():
            print(f"{name}: {stat['count']} entities")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
