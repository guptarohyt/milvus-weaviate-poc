#!/usr/bin/env python3
"""
Demo: Milvus 2.5 Hybrid Search Features

This script demonstrates:
1. Dense vector search (semantic)
2. Sparse vector search (BM25/keyword)
3. Hybrid search (dense + sparse fusion)
4. Grouping search
"""

import numpy as np
from milvus_25_hybrid_client import Milvus25HybridClient


def generate_test_data(num_docs=20):
    """Generate test insurance documents."""
    documents = []
    embeddings = []

    policy_types = ["Property", "Casualty", "Auto", "Life", "Health"]
    damage_types = ["fire", "water", "theft", "collision", "storm"]

    for i in range(num_docs):
        policy_id = f"POL-{i // 4:05d}"  # 4 docs per policy
        policy_type = policy_types[i % len(policy_types)]
        damage = damage_types[i % len(damage_types)]

        # Create documents with varying content
        if i % 4 == 0:
            text = f"Insurance policy {policy_id} for {policy_type} coverage. This policy covers {damage} damage and related incidents."
            filename = f"{policy_id}_policy.pdf"
        elif i % 4 == 1:
            text = f"Claim report for policy {policy_id}. The insured property sustained {damage} damage requiring assessment."
            filename = f"{policy_id}_claim_report.docx"
        elif i % 4 == 2:
            text = f"Damage assessment photo for {policy_id} showing {damage} damage to the property."
            filename = f"{policy_id}_damage_photo.jpg"
        else:
            text = f"Additional documentation for policy {policy_id}. Evidence of {damage} incident and repair estimates."
            filename = f"{policy_id}_additional_docs.pdf"

        documents.append({
            "filename": filename,
            "text": text,
            "policy_id": policy_id,
            "policy_type": policy_type
        })

        # Generate random 384-dim embedding (simulating Sentence Transformers)
        # In production, use actual Sentence Transformer model
        embeddings.append(np.random.rand(384).astype('float32').tolist())

    return documents, embeddings


def main():
    print("\n" + "="*70)
    print("Milvus 2.5 Hybrid Search Demo")
    print("="*70 + "\n")

    # Initialize client
    client = Milvus25HybridClient(host="localhost", port="19530")
    client.connect()

    # Create hybrid collection
    print("\n[1] Creating Hybrid Collection")
    print("-" * 70)
    collection = client.create_hybrid_collection(
        collection_name="demo_hybrid_search",
        dense_dim=384,
        description="Demo collection for hybrid search"
    )

    # Create indexes
    print("\n[2] Creating Indexes")
    print("-" * 70)
    client.create_indexes(collection)

    # Generate and insert test data
    print("\n[3] Generating and Inserting Test Data")
    print("-" * 70)
    documents, embeddings = generate_test_data(num_docs=20)
    client.insert_documents(collection, documents, embeddings)

    # Load collection
    print("\n[4] Loading Collection to Memory")
    print("-" * 70)
    collection.load()
    print("✓ Collection loaded and ready for search\n")

    # Test query
    query_idx = 0
    query_text = documents[query_idx]["text"]
    query_vector = embeddings[query_idx]

    print("\n[5] Search Demonstrations")
    print("-" * 70)
    print(f"\nQuery Document: {documents[query_idx]['filename']}")
    print(f"Query Text: {query_text[:80]}...")
    print()

    # ========================================
    # Demo 1: Dense Vector Search (Semantic)
    # ========================================
    print("\n" + "─" * 70)
    print("Demo 1: Dense Vector Search (Semantic)")
    print("─" * 70)
    print("Searches using only semantic embeddings (cosine similarity)\n")

    results, elapsed = client.dense_search(
        collection=collection,
        query_vector=query_vector,
        limit=3
    )

    print(f"Results ({elapsed:.2f}ms):")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result['filename']}")
        print(f"     Policy: {result['policy_id']} ({result['policy_type']})")
        print(f"     Similarity: {result['distance']:.4f}")
        print(f"     Text: {result['text'][:60]}...")

    # ========================================
    # Demo 2: Sparse Vector Search (BM25)
    # ========================================
    print("\n" + "─" * 70)
    print("Demo 2: Sparse Vector Search (BM25 Keyword)")
    print("─" * 70)
    print("Searches using BM25 keyword matching (sparse vectors)\n")

    # Try a keyword query
    keyword_query = "fire damage property"
    print(f"Keyword Query: '{keyword_query}'\n")

    results, elapsed = client.sparse_search(
        collection=collection,
        query_text=keyword_query,
        limit=3
    )

    print(f"Results ({elapsed:.2f}ms):")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result['filename']}")
        print(f"     Policy: {result['policy_id']} ({result['policy_type']})")
        print(f"     BM25 Score: {result['distance']:.4f}")
        print(f"     Text: {result['text'][:60]}...")

    # ========================================
    # Demo 3: Hybrid Search (Dense + Sparse)
    # ========================================
    print("\n" + "─" * 70)
    print("Demo 3: Hybrid Search (Dense + Sparse Fusion)")
    print("─" * 70)
    print("Combines semantic similarity AND keyword matching using RRF\n")

    results, elapsed = client.hybrid_search(
        collection=collection,
        query_vector=query_vector,
        query_text=query_text,
        limit=3,
        dense_weight=0.7  # 70% semantic, 30% keyword
    )

    print(f"Results ({elapsed:.2f}ms):")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result['filename']}")
        print(f"     Policy: {result['policy_id']} ({result['policy_type']})")
        print(f"     Hybrid Score: {result['hybrid_score']:.4f}")
        print(f"     Text: {result['text'][:60]}...")

    # ========================================
    # Demo 4: Grouping Search
    # ========================================
    print("\n" + "─" * 70)
    print("Demo 4: Grouping Search (Group by Policy ID)")
    print("─" * 70)
    print("Returns top N results per policy (useful for multi-doc entities)\n")

    results, elapsed = client.grouping_search(
        collection=collection,
        query_vector=query_vector,
        group_by_field="policy_id",
        group_size=2,  # Top 2 docs per policy
        limit=20
    )

    print(f"Results ({elapsed:.2f}ms):")

    # Group results for display
    grouped = {}
    for result in results:
        policy = result['group']
        if policy not in grouped:
            grouped[policy] = []
        grouped[policy].append(result)

    for policy_id, group_results in grouped.items():
        print(f"\n  Policy: {policy_id}")
        for j, result in enumerate(group_results, 1):
            print(f"    {j}. {result['filename']} (similarity: {result['distance']:.4f})")

    # Cleanup
    print("\n" + "─" * 70)
    print("\n[6] Cleanup")
    print("-" * 70)
    collection.release()
    print("✓ Collection released")

    from pymilvus import utility
    utility.drop_collection("demo_hybrid_search")
    print("✓ Demo collection dropped")

    client.disconnect()

    print("\n" + "="*70)
    print("✓ Demo Complete!")
    print("="*70)
    print("\nKey Takeaways:")
    print("  • Dense search: Best for semantic similarity")
    print("  • Sparse search: Best for keyword matching")
    print("  • Hybrid search: Combines both for balanced results")
    print("  • Grouping search: Groups results by entity (policy, claim, etc.)")
    print()


if __name__ == "__main__":
    main()
