"""
Extended Milvus client for Phase 2 multi-modal data.
Handles PDFs, Word documents, and images with different embedding dimensions.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)


class MilvusMultiModalClient:
    """Milvus client for multi-modal document search."""

    def __init__(self, host="localhost", port="19530"):
        """Initialize Milvus connection."""
        self.host = host
        self.port = port
        connections.connect(alias="default", host=host, port=port)
        print(f"✓ Connected to Milvus at {host}:{port}")

        # Collection references
        self.pdf_collection = None
        self.word_collection = None
        self.image_collection = None

    def create_pdf_collection(self, collection_name="pdfs_phase2"):
        """Create collection for PDF documents (384-dim text embeddings)."""
        # Drop if exists
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"  Dropped existing collection: {collection_name}")

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="num_pages", dtype=DataType.INT64),
            FieldSchema(name="has_tables", dtype=DataType.BOOL),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="PDF documents with text embeddings"
        )

        # Create collection
        collection = Collection(name=collection_name, schema=schema)
        print(f"✓ Created collection: {collection_name}")

        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print(f"✓ Created IVF_FLAT index on {collection_name}")

        self.pdf_collection = collection
        return collection

    def create_word_collection(self, collection_name="word_docs_phase2"):
        """Create collection for Word documents (384-dim text embeddings)."""
        # Drop if exists
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"  Dropped existing collection: {collection_name}")

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="num_paragraphs", dtype=DataType.INT64),
            FieldSchema(name="num_tables", dtype=DataType.INT64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Word documents with text embeddings"
        )

        # Create collection
        collection = Collection(name=collection_name, schema=schema)
        print(f"✓ Created collection: {collection_name}")

        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print(f"✓ Created IVF_FLAT index on {collection_name}")

        self.word_collection = collection
        return collection

    def create_image_collection(self, collection_name="images_phase2"):
        """Create collection for images (512-dim CLIP embeddings)."""
        # Drop if exists
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"  Dropped existing collection: {collection_name}")

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="damage_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="severity", dtype=DataType.FLOAT),
            FieldSchema(name="claim_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="policy_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="location", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="image_embedding", dtype=DataType.FLOAT_VECTOR, dim=512),
            FieldSchema(name="text_embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Images with CLIP embeddings"
        )

        # Create collection
        collection = Collection(name=collection_name, schema=schema)
        print(f"✓ Created collection: {collection_name}")

        # Create index on image embeddings
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="image_embedding", index_params=index_params)
        print(f"✓ Created IVF_FLAT index on {collection_name}.image_embedding")

        # Create index on text embeddings
        collection.create_index(field_name="text_embedding", index_params=index_params)
        print(f"✓ Created IVF_FLAT index on {collection_name}.text_embedding")

        self.image_collection = collection
        return collection

    def load_pdf_data(self, data_file: str):
        """Load PDF documents into Milvus."""
        print(f"\nLoading PDF documents from {data_file}...")

        with open(data_file) as f:
            documents = json.load(f)

        # Prepare data for insertion
        ids = []
        filenames = []
        texts = []
        num_pages = []
        has_tables = []
        embeddings = []

        for doc in documents:
            ids.append(doc['id'])
            filenames.append(doc['filename'])
            texts.append(doc['text'][:5000])  # Truncate to max length
            num_pages.append(doc['num_pages'])
            has_tables.append(doc['has_tables'])
            embeddings.append(doc['embedding'])

        # Insert data
        data = [ids, filenames, texts, num_pages, has_tables, embeddings]
        mr = self.pdf_collection.insert(data)
        print(f"✓ Inserted {len(ids)} PDF documents")

        return len(ids)

    def load_word_data(self, data_file: str):
        """Load Word documents into Milvus."""
        print(f"\nLoading Word documents from {data_file}...")

        with open(data_file) as f:
            documents = json.load(f)

        # Prepare data for insertion
        ids = []
        filenames = []
        texts = []
        num_paragraphs = []
        num_tables = []
        embeddings = []

        for doc in documents:
            ids.append(doc['id'])
            filenames.append(doc['filename'])
            texts.append(doc['text'][:5000])  # Truncate to max length
            num_paragraphs.append(doc['num_paragraphs'])
            num_tables.append(doc['num_tables'])
            embeddings.append(doc['embedding'])

        # Insert data
        data = [ids, filenames, texts, num_paragraphs, num_tables, embeddings]
        mr = self.word_collection.insert(data)
        print(f"✓ Inserted {len(ids)} Word documents")

        return len(ids)

    def load_image_data(self, data_file: str):
        """Load images into Milvus."""
        print(f"\nLoading images from {data_file}...")

        with open(data_file) as f:
            images = json.load(f)

        # Prepare data for insertion
        ids = []
        filenames = []
        damage_types = []
        severities = []
        claim_ids = []
        policy_ids = []
        locations = []
        descriptions = []
        image_embeddings = []
        text_embeddings = []

        for img in images:
            ids.append(img['id'])
            filenames.append(img['filename'])
            damage_types.append(img['damage_type'])
            severities.append(float(img['severity']))
            claim_ids.append(img['claim_id'])
            policy_ids.append(img['policy_id'])
            locations.append(img['location'][:200])  # Truncate
            descriptions.append(img['description'][:1000])  # Truncate
            image_embeddings.append(img['image_embedding'])
            text_embeddings.append(img['text_embedding'])

        # Insert data
        data = [ids, filenames, damage_types, severities, claim_ids,
                policy_ids, locations, descriptions, image_embeddings, text_embeddings]
        mr = self.image_collection.insert(data)
        print(f"✓ Inserted {len(ids)} images")

        return len(ids)

    def load_collections(self):
        """Load all collections to memory."""
        print("\nLoading collections to memory...")

        if self.pdf_collection:
            self.pdf_collection.load()
            print("✓ Loaded PDF collection")

        if self.word_collection:
            self.word_collection.load()
            print("✓ Loaded Word collection")

        if self.image_collection:
            self.image_collection.load()
            print("✓ Loaded image collection")

    def search_pdfs(self, query_embedding: List[float], top_k: int = 5):
        """Search PDF documents."""
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        start = time.time()
        results = self.pdf_collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "filename", "text", "num_pages"]
        )
        elapsed = (time.time() - start) * 1000

        return results[0], elapsed

    def search_word_docs(self, query_embedding: List[float], top_k: int = 5):
        """Search Word documents."""
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        start = time.time()
        results = self.word_collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "filename", "text", "num_paragraphs"]
        )
        elapsed = (time.time() - start) * 1000

        return results[0], elapsed

    def search_images_by_image(self, query_embedding: List[float], top_k: int = 5):
        """Search images using CLIP image embedding (image-to-image search)."""
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        start = time.time()
        results = self.image_collection.search(
            data=[query_embedding],
            anns_field="image_embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "filename", "damage_type", "severity", "description"]
        )
        elapsed = (time.time() - start) * 1000

        return results[0], elapsed

    def search_images_by_text(self, query_embedding: List[float], top_k: int = 5):
        """Search images using text embedding (text-to-image search)."""
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        start = time.time()
        results = self.image_collection.search(
            data=[query_embedding],
            anns_field="text_embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "filename", "damage_type", "severity", "description"]
        )
        elapsed = (time.time() - start) * 1000

        return results[0], elapsed

    def get_stats(self):
        """Get statistics for all collections."""
        stats = {}

        if self.pdf_collection:
            self.pdf_collection.flush()
            stats['pdfs'] = self.pdf_collection.num_entities

        if self.word_collection:
            self.word_collection.flush()
            stats['word_docs'] = self.word_collection.num_entities

        if self.image_collection:
            self.image_collection.flush()
            stats['images'] = self.image_collection.num_entities

        return stats

    def close(self):
        """Close connection."""
        connections.disconnect(alias="default")
        print("✓ Disconnected from Milvus")


def main():
    """Test multi-modal Milvus client."""
    client = MilvusMultiModalClient()

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

    # Load collections
    client.load_collections()

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
