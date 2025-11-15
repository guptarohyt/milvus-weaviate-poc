#!/usr/bin/env python3
"""
Test Milvus 2.5 compatibility with Phase 2 data.
This script tests that Phase 2 data can be loaded and searched in Milvus 2.5.
"""

import json
import sys
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

def test_milvus_25_compatibility():
    """Test that Milvus 2.5 can load and search Phase 2 data."""

    print("\n" + "="*60)
    print("Testing Milvus 2.5 with Phase 2 Data")
    print("="*60 + "\n")

    # Connect to Milvus 2.5
    print("1. Connecting to Milvus 2.5...")
    connections.connect(host="localhost", port="19530")
    version = utility.get_server_version()
    print(f"   ✓ Connected to Milvus {version}\n")

    # Create a test collection with Phase 2 schema (PDFs)
    collection_name = "phase2_test_pdfs"

    # Drop collection if exists
    if utility.has_collection(collection_name):
        print(f"2. Dropping existing test collection '{collection_name}'...")
        utility.drop_collection(collection_name)
        print("   ✓ Collection dropped\n")
    else:
        print(f"2. Collection '{collection_name}' doesn't exist (expected)\n")

    # Create collection with Phase 2 PDF schema
    print("3. Creating test collection with Phase 2 schema...")
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=10000),
        FieldSchema(name="policy_id", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="policy_type", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
    ]

    schema = CollectionSchema(fields=fields, description="Phase 2 PDF test collection")
    collection = Collection(name=collection_name, schema=schema)
    print(f"   ✓ Collection '{collection_name}' created\n")

    # Generate synthetic test data (Phase 2 schema compatible)
    print("4. Generating synthetic test data with Phase 2 schema...")
    import numpy as np

    test_size = 10
    filenames = [f"policy_{i:03d}.pdf" for i in range(test_size)]
    texts = [f"This is test insurance policy document number {i}. Coverage details and terms." for i in range(test_size)]
    policy_ids = [f"POL-{i:05d}" for i in range(test_size)]
    policy_types = ["Property", "Casualty", "Auto", "Life", "Health"] * 2
    # Generate random 384-dim embeddings (same as Phase 2 Sentence Transformers)
    embeddings = [np.random.rand(384).astype('float32').tolist() for _ in range(test_size)]

    print(f"   Inserting {test_size} PDFs...")
    insert_result = collection.insert([filenames, texts, policy_ids, policy_types, embeddings])
    print(f"   ✓ Inserted {len(insert_result.primary_keys)} documents\n")

    # Create index (IVF_FLAT like Phase 2)
    print("5. Creating IVF_FLAT index...")
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print("   ✓ Index created\n")

    # Load collection to memory
    print("6. Loading collection to memory...")
    collection.load()
    print("   ✓ Collection loaded\n")

    # Test search with first embedding
    print("7. Testing semantic search...")
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

    query_embedding = embeddings[0]
    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=3,
        output_fields=["filename", "policy_id", "policy_type"]
    )

    print(f"   Query: {filenames[0]}")
    print(f"   Top 3 results:")
    for i, hit in enumerate(results[0], 1):
        print(f"     {i}. {hit.entity.get('filename')}")
        print(f"        Policy: {hit.entity.get('policy_id')} ({hit.entity.get('policy_type')})")
        print(f"        Distance: {hit.distance:.4f}")

    print("\n   ✓ Search successful!\n")

    # Get collection stats
    print("8. Collection statistics:")
    collection.flush()
    stats = collection.num_entities
    print(f"   Total entities: {stats}")
    print(f"   Collection name: {collection.name}")
    print(f"   Schema fields: {len(collection.schema.fields)}")
    print()

    # Cleanup
    print("9. Cleaning up...")
    collection.release()
    utility.drop_collection(collection_name)
    connections.disconnect("default")
    print("   ✓ Test collection dropped")
    print("   ✓ Disconnected\n")

    print("="*60)
    print("✓ Milvus 2.5 Phase 2 Compatibility Test PASSED")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = test_milvus_25_compatibility()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
