"""
Extended Weaviate client for Phase 2 multi-modal data.
Handles PDFs, Word documents, and images with different embedding dimensions.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter, MetadataQuery


class WeaviateMultiModalClient:
    """Weaviate client for multi-modal document search."""

    def __init__(self, host="localhost", port="8080", load_existing=True):
        """Initialize Weaviate connection."""
        self.host = host
        self.port = port

        # Connect to Weaviate
        self.client = weaviate.connect_to_local(
            host=host,
            port=int(port)
        )
        print(f"✓ Connected to Weaviate at {host}:{port}")

        # Check existing collections
        if load_existing:
            if self.client.collections.exists("PDFsPhase2"):
                print("✓ Found existing PDFsPhase2 collection")
            if self.client.collections.exists("WordDocsPhase2"):
                print("✓ Found existing WordDocsPhase2 collection")
            if self.client.collections.exists("ImagesPhase2"):
                print("✓ Found existing ImagesPhase2 collection")

    def create_pdf_collection(self, collection_name="PDFsPhase2"):
        """Create collection for PDF documents."""
        # Delete if exists
        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

        # Create collection
        collection = self.client.collections.create(
            name=collection_name,
            properties=[
                Property(name="doc_id", data_type=DataType.TEXT),
                Property(name="filename", data_type=DataType.TEXT),
                Property(name="text", data_type=DataType.TEXT),
                Property(name="num_pages", data_type=DataType.INT),
                Property(name="has_tables", data_type=DataType.BOOL),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
        )
        print(f"✓ Created collection: {collection_name}")

        return collection

    def create_word_collection(self, collection_name="WordDocsPhase2"):
        """Create collection for Word documents."""
        # Delete if exists
        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

        # Create collection
        collection = self.client.collections.create(
            name=collection_name,
            properties=[
                Property(name="doc_id", data_type=DataType.TEXT),
                Property(name="filename", data_type=DataType.TEXT),
                Property(name="text", data_type=DataType.TEXT),
                Property(name="num_paragraphs", data_type=DataType.INT),
                Property(name="num_tables", data_type=DataType.INT),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
        )
        print(f"✓ Created collection: {collection_name}")

        return collection

    def create_image_collection(self, collection_name="ImagesPhase2"):
        """Create collection for images with dual embeddings."""
        # Delete if exists
        if self.client.collections.exists(collection_name):
            self.client.collections.delete(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

        # Create collection with named vectors
        collection = self.client.collections.create(
            name=collection_name,
            properties=[
                Property(name="image_id", data_type=DataType.TEXT),
                Property(name="filename", data_type=DataType.TEXT),
                Property(name="damage_type", data_type=DataType.TEXT),
                Property(name="severity", data_type=DataType.NUMBER),
                Property(name="claim_id", data_type=DataType.TEXT),
                Property(name="policy_id", data_type=DataType.TEXT),
                Property(name="location", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
            ],
            vectorizer_config=[
                Configure.NamedVectors.none(name="image_vector"),
                Configure.NamedVectors.none(name="text_vector")
            ]
        )
        print(f"✓ Created collection: {collection_name} with dual vectors")

        return collection

    def load_pdf_data(self, data_file: str, collection_name="PDFsPhase2"):
        """Load PDF documents into Weaviate."""
        print(f"\nLoading PDF documents from {data_file}...")

        with open(data_file) as f:
            documents = json.load(f)

        collection = self.client.collections.get(collection_name)

        # Batch insert
        with collection.batch.dynamic() as batch:
            for doc in documents:
                batch.add_object(
                    properties={
                        "doc_id": doc['id'],
                        "filename": doc['filename'],
                        "text": doc['text'][:5000],  # Truncate
                        "num_pages": doc['num_pages'],
                        "has_tables": doc['has_tables'],
                    },
                    vector=doc['embedding']
                )

        print(f"✓ Inserted {len(documents)} PDF documents")
        return len(documents)

    def load_word_data(self, data_file: str, collection_name="WordDocsPhase2"):
        """Load Word documents into Weaviate."""
        print(f"\nLoading Word documents from {data_file}...")

        with open(data_file) as f:
            documents = json.load(f)

        collection = self.client.collections.get(collection_name)

        # Batch insert
        with collection.batch.dynamic() as batch:
            for doc in documents:
                batch.add_object(
                    properties={
                        "doc_id": doc['id'],
                        "filename": doc['filename'],
                        "text": doc['text'][:5000],  # Truncate
                        "num_paragraphs": doc['num_paragraphs'],
                        "num_tables": doc['num_tables'],
                    },
                    vector=doc['embedding']
                )

        print(f"✓ Inserted {len(documents)} Word documents")
        return len(documents)

    def load_image_data(self, data_file: str, collection_name="ImagesPhase2"):
        """Load images into Weaviate."""
        print(f"\nLoading images from {data_file}...")

        with open(data_file) as f:
            images = json.load(f)

        collection = self.client.collections.get(collection_name)

        # Batch insert with named vectors
        with collection.batch.dynamic() as batch:
            for img in images:
                batch.add_object(
                    properties={
                        "image_id": img['id'],
                        "filename": img['filename'],
                        "damage_type": img['damage_type'],
                        "severity": float(img['severity']),
                        "claim_id": img['claim_id'],
                        "policy_id": img['policy_id'],
                        "location": img['location'][:200],  # Truncate
                        "description": img['description'][:1000],  # Truncate
                    },
                    vector={
                        "image_vector": img['image_embedding'],
                        "text_vector": img['text_embedding']
                    }
                )

        print(f"✓ Inserted {len(images)} images")
        return len(images)

    def search_pdfs(self, query_embedding: List[float], top_k: int = 5):
        """Search PDF documents."""
        collection = self.client.collections.get("PDFsPhase2")

        start = time.time()
        response = collection.query.near_vector(
            near_vector=query_embedding,
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        elapsed = (time.time() - start) * 1000

        return response.objects, elapsed

    def search_word_docs(self, query_embedding: List[float], top_k: int = 5):
        """Search Word documents."""
        collection = self.client.collections.get("WordDocsPhase2")

        start = time.time()
        response = collection.query.near_vector(
            near_vector=query_embedding,
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        elapsed = (time.time() - start) * 1000

        return response.objects, elapsed

    def search_images_by_image(self, query_embedding: List[float], top_k: int = 5):
        """Search images using CLIP image embedding (image-to-image search)."""
        collection = self.client.collections.get("ImagesPhase2")

        start = time.time()
        response = collection.query.near_vector(
            near_vector=query_embedding,
            target_vector="image_vector",  # Use CLIP embeddings
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        elapsed = (time.time() - start) * 1000

        return response.objects, elapsed

    def search_images_by_text(self, query_embedding: List[float], top_k: int = 5):
        """Search images using text embedding (text-to-image search)."""
        collection = self.client.collections.get("ImagesPhase2")

        start = time.time()
        response = collection.query.near_vector(
            near_vector=query_embedding,
            target_vector="text_vector",  # Use text embeddings
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        elapsed = (time.time() - start) * 1000

        return response.objects, elapsed

    def search_images_filtered(self, query_embedding: List[float],
                               damage_type: str = None,
                               min_severity: float = None,
                               top_k: int = 5):
        """Search images with filters (uses text embeddings)."""
        collection = self.client.collections.get("ImagesPhase2")

        # Build filters
        filters = []
        if damage_type:
            filters.append(Filter.by_property("damage_type").equal(damage_type))
        if min_severity is not None:
            filters.append(Filter.by_property("severity").greater_or_equal(min_severity))

        combined_filter = Filter.all_of(filters) if len(filters) > 1 else (filters[0] if filters else None)

        start = time.time()
        if combined_filter:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                target_vector="text_vector",  # Use text embeddings (384 dims)
                limit=top_k,
                filters=combined_filter,
                return_metadata=MetadataQuery(distance=True)
            )
        else:
            response = collection.query.near_vector(
                near_vector=query_embedding,
                target_vector="text_vector",  # Use text embeddings (384 dims)
                limit=top_k,
                return_metadata=MetadataQuery(distance=True)
            )
        elapsed = (time.time() - start) * 1000

        return response.objects, elapsed

    def get_stats(self):
        """Get statistics for all collections."""
        stats = {}

        if self.client.collections.exists("PDFsPhase2"):
            collection = self.client.collections.get("PDFsPhase2")
            agg = collection.aggregate.over_all()
            stats['pdfs'] = agg.total_count

        if self.client.collections.exists("WordDocsPhase2"):
            collection = self.client.collections.get("WordDocsPhase2")
            agg = collection.aggregate.over_all()
            stats['word_docs'] = agg.total_count

        if self.client.collections.exists("ImagesPhase2"):
            collection = self.client.collections.get("ImagesPhase2")
            agg = collection.aggregate.over_all()
            stats['images'] = agg.total_count

        return stats

    def close(self):
        """Close connection."""
        self.client.close()
        print("✓ Disconnected from Weaviate")


def main():
    """Test multi-modal Weaviate client."""
    client = WeaviateMultiModalClient()

    # Create collections
    print("\n" + "="*60)
    print("CREATING COLLECTIONS")
    print("="*60)
    client.create_pdf_collection()
    client.create_word_collection()
    client.create_image_collection()

    # Load processed data
    data_dir = Path("./data/multimodal/processed")

    if (data_dir / "pdfs_processed.json").exists():
        client.load_pdf_data(str(data_dir / "pdfs_processed.json"))

    if (data_dir / "word_docs_processed.json").exists():
        client.load_word_data(str(data_dir / "word_docs_processed.json"))

    if (data_dir / "images_processed.json").exists():
        client.load_image_data(str(data_dir / "images_processed.json"))

    # Get stats
    print("\n" + "="*60)
    print("COLLECTION STATISTICS")
    print("="*60)
    stats = client.get_stats()
    for collection, count in stats.items():
        print(f"{collection:15s}: {count:6d} documents")

    client.close()


if __name__ == "__main__":
    main()
