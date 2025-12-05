#!/usr/bin/env python3
"""
Phase 3 FAIR Benchmarks: Milvus 2.5 vs Weaviate (Same Features Tested)

This script provides a FAIR comparison by testing the same features on both systems:
- Dense vector search (semantic similarity)
- Sparse/keyword search (BM25)
- Hybrid search (dense + sparse combined)

Both Milvus 2.5 and Weaviate 1.27.5 support all three search types.
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import statistics
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Helper to get project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

def get_data_dir():
    """Get data directory, resolving DATA_OUTPUT_DIR relative to project root."""
    data_output = os.getenv("DATA_OUTPUT_DIR", "./data/multimodal")
    if not Path(data_output).is_absolute():
        return PROJECT_ROOT / data_output
    return Path(data_output)

from milvus_25_hybrid_client import Milvus25HybridClient
import weaviate


def load_processed_data():
    """Load all processed multi-modal data."""
    data_dir = get_data_dir() / "processed"

    print(f"DEBUG: Loading from: {data_dir.resolve()}")

    pdf_file = data_dir / "pdfs_processed.json"
    print(f"DEBUG: PDF file: {pdf_file}, exists: {pdf_file.exists()}")
    with open(pdf_file, "r") as f:
        pdfs = json.load(f)
    print(f"DEBUG: Loaded {len(pdfs)} PDFs from file")

    with open(data_dir / "word_docs_processed.json", "r") as f:
        word_docs = json.load(f)
    print(f"DEBUG: Loaded {len(word_docs)} Word docs from file")

    with open(data_dir / "images_processed.json", "r") as f:
        images = json.load(f)
    print(f"DEBUG: Loaded {len(images)} images from file")

    return pdfs, word_docs, images


def setup_milvus_25(pdfs, word_docs, images, use_persistent=False):
    """Setup Milvus 2.5 with hybrid search collections."""
    from pymilvus import Collection
    
    client = Milvus25HybridClient(host="localhost", port="19530")
    client.connect()

    if use_persistent:
        print("\n[Milvus 2.5] Using existing persistent collections...")
        pdf_collection = Collection("persistent_pdfs")
        word_collection = Collection("persistent_word")
        image_collection = Collection("persistent_images")
        
        # Fit BM25 encoder on the corpus (needed for sparse search)
        print("[Milvus 2.5] Fitting BM25 encoder on corpus...")
        all_texts = [p["text"] for p in pdfs] + [w["text"] for w in word_docs] + [img.get("description", "") for img in images]
        client.bm25_encoder.fit(all_texts)
        
        print("✓ Connected to persistent collections\n")
    else:
        print("\n[Milvus 2.5] Creating hybrid collections...")

        # Create collections for each data type
        pdf_collection = client.create_hybrid_collection("phase3_fair_pdfs", dense_dim=384)
        word_collection = client.create_hybrid_collection("phase3_fair_word", dense_dim=384)
        image_collection = client.create_hybrid_collection("phase3_fair_images", dense_dim=512)

        # Create indexes
        print("[Milvus 2.5] Creating indexes...")
        client.create_indexes(pdf_collection)
        client.create_indexes(word_collection)
        client.create_indexes(image_collection)

        # Insert data
        print("[Milvus 2.5] Inserting PDFs...")
        pdf_docs = [{"filename": p["filename"], "text": p["text"],
                     "policy_id": p.get("id", "UNKNOWN"),
                     "policy_type": p.get("type", "pdf")}
                    for p in pdfs]
        pdf_embeddings = [p["embedding"] for p in pdfs]
        client.insert_documents(pdf_collection, pdf_docs, pdf_embeddings)

        print("[Milvus 2.5] Inserting Word docs...")
        word_docs_list = [{"filename": w["filename"], "text": w["text"],
                           "policy_id": w.get("id", "UNKNOWN"),
                           "policy_type": w.get("type", "word")}
                          for w in word_docs]
        word_embeddings = [w["embedding"] for w in word_docs]
        client.insert_documents(word_collection, word_docs_list, word_embeddings)

        print("[Milvus 2.5] Inserting Images...")
        image_docs = [{"filename": img["filename"], "text": img.get("description", ""),
                       "policy_id": img.get("claim_id", "UNKNOWN"),
                       "policy_type": img.get("damage_type", "unknown")}
                      for img in images]
        # Use image_embedding field (CLIP visual)
        image_embeddings = [img["image_embedding"] for img in images]
        client.insert_documents(image_collection, image_docs, image_embeddings)

        # Load collections
        print("[Milvus 2.5] Loading collections to memory...")
        pdf_collection.load()
        word_collection.load()
        image_collection.load()

        print("✓ Milvus 2.5 setup complete\n")

    return client, pdf_collection, word_collection, image_collection


def setup_weaviate(pdfs, word_docs, images, use_persistent=False):
    """Setup Weaviate with collections supporting hybrid search."""
    client = weaviate.Client("http://localhost:8080")

    if use_persistent:
        print("\n[Weaviate] Using existing persistent collections...")
        print("✓ Connected to persistent collections\n")
        return client
    
    print("\n[Weaviate] Creating collections with hybrid search support...")

    # Create PDF collection
    # Note: Weaviate automatically supports hybrid search on text properties
    # No special schema configuration required
    pdf_schema = {
        "class": "Phase3FairPDFs",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "policy_id", "dataType": ["text"]},
            {"name": "policy_type", "dataType": ["text"]}
        ]
    }

    # Delete if exists
    try:
        client.schema.delete_class("Phase3FairPDFs")
    except:
        pass

    client.schema.create_class(pdf_schema)

    # Insert PDFs
    print("[Weaviate] Inserting PDFs...")
    with client.batch as batch:
        for pdf in pdfs:
            properties = {
                "filename": pdf["filename"],
                "text": pdf["text"],
                "policy_id": pdf.get("id", "UNKNOWN"),
                "policy_type": pdf.get("type", "pdf")
            }
            batch.add_data_object(properties, "Phase3FairPDFs", vector=pdf["embedding"])

    # Create Word collection
    word_schema = {
        "class": "Phase3FairWordDocs",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "doc_id", "dataType": ["text"]},
            {"name": "doc_type", "dataType": ["text"]}
        ]
    }

    try:
        client.schema.delete_class("Phase3FairWordDocs")
    except:
        pass

    client.schema.create_class(word_schema)

    # Insert Word docs
    print("[Weaviate] Inserting Word docs...")
    with client.batch as batch:
        for word in word_docs:
            properties = {
                "filename": word["filename"],
                "text": word["text"],
                "doc_id": word.get("id", "UNKNOWN"),
                "doc_type": word.get("type", "word")
            }
            batch.add_data_object(properties, "Phase3FairWordDocs", vector=word["embedding"])

    # Create Image collection
    image_schema = {
        "class": "Phase3FairImages",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "description", "dataType": ["text"]},
            {"name": "claim_id", "dataType": ["text"]},
            {"name": "damage_type", "dataType": ["text"]}
        ]
    }

    try:
        client.schema.delete_class("Phase3FairImages")
    except:
        pass

    client.schema.create_class(image_schema)

    # Insert Images
    print("[Weaviate] Inserting Images...")
    with client.batch as batch:
        for img in images:
            properties = {
                "filename": img["filename"],
                "description": img.get("description", ""),
                "claim_id": img.get("claim_id", "UNKNOWN"),
                "damage_type": img.get("damage_type", "unknown")
            }
            batch.add_data_object(properties, "Phase3FairImages", vector=img["image_embedding"])

    print("✓ Weaviate setup complete\n")

    return client


def benchmark_milvus_pdfs(client, collection, pdfs, num_queries=10):
    """Benchmark Milvus 2.5 PDF search (dense, sparse, hybrid)."""
    results = {
        "dense": [],
        "sparse": [],
        "hybrid": []
    }

    print(f"\n[Milvus 2.5] Benchmarking PDF search ({num_queries} queries)...")

    for i in range(num_queries):
        query_vector = pdfs[i]["embedding"]
        query_text = pdfs[i]["text"]

        # Dense search
        _, elapsed = client.dense_search(collection, query_vector, limit=5)
        results["dense"].append(elapsed)

        # Sparse search
        _, elapsed = client.sparse_search(collection, query_text, limit=5)
        results["sparse"].append(elapsed)

        # Hybrid search
        _, elapsed = client.hybrid_search(collection, query_vector, query_text, limit=5)
        results["hybrid"].append(elapsed)

    return results


def benchmark_milvus_word(client, collection, word_docs, num_queries=10):
    """Benchmark Milvus 2.5 Word doc search."""
    results = {
        "dense": [],
        "sparse": [],
        "hybrid": []
    }

    print(f"[Milvus 2.5] Benchmarking Word doc search ({num_queries} queries)...")

    for i in range(num_queries):
        query_vector = word_docs[i]["embedding"]
        query_text = word_docs[i]["text"]

        # Dense search
        _, elapsed = client.dense_search(collection, query_vector, limit=5)
        results["dense"].append(elapsed)

        # Sparse search
        _, elapsed = client.sparse_search(collection, query_text, limit=5)
        results["sparse"].append(elapsed)

        # Hybrid search
        _, elapsed = client.hybrid_search(collection, query_vector, query_text, limit=5)
        results["hybrid"].append(elapsed)

    return results


def benchmark_milvus_images(client, collection, images, num_queries=10):
    """Benchmark Milvus 2.5 image search (dense only - images don't have meaningful text)."""
    results = {"dense": []}

    print(f"[Milvus 2.5] Benchmarking image search ({num_queries} queries)...")

    for i in range(num_queries):
        query_vector = images[i]["image_embedding"]

        # Dense search only (images use CLIP visual embeddings)
        _, elapsed = client.dense_search(collection, query_vector, limit=5)
        results["dense"].append(elapsed)

    return results


def benchmark_weaviate_pdfs(client, pdfs, num_queries=10, collection_name="Phase3FairPDFs"):
    """Benchmark Weaviate PDF search (dense, keyword, hybrid)."""
    results = {
        "dense": [],
        "keyword": [],  # Pure BM25 (alpha=0)
        "hybrid": []    # Balanced hybrid (alpha=0.5)
    }

    print(f"\n[Weaviate] Benchmarking PDF search ({num_queries} queries)...")

    for i in range(num_queries):
        query_vector = pdfs[i]["embedding"]
        query_text = pdfs[i]["text"][:200]  # Limit text length for keyword search

        # Dense search (vector only)
        start_time = time.time()
        client.query.get(collection_name, ["filename", "policy_id", "policy_type"]) \
            .with_near_vector({"vector": query_vector}) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["dense"].append(elapsed)

        # Keyword search (BM25 only, alpha=0)
        start_time = time.time()
        client.query.get(collection_name, ["filename", "policy_id", "policy_type"]) \
            .with_hybrid(query=query_text, alpha=0.0) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["keyword"].append(elapsed)

        # Hybrid search (balanced, alpha=0.5)
        start_time = time.time()
        client.query.get(collection_name, ["filename", "policy_id", "policy_type"]) \
            .with_hybrid(query=query_text, alpha=0.5, vector=query_vector) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["hybrid"].append(elapsed)

    return results


def benchmark_weaviate_word(client, word_docs, num_queries=10, collection_name="Phase3FairWordDocs"):
    """Benchmark Weaviate Word doc search (dense, keyword, hybrid)."""
    results = {
        "dense": [],
        "keyword": [],
        "hybrid": []
    }

    print(f"[Weaviate] Benchmarking Word doc search ({num_queries} queries)...")

    for i in range(num_queries):
        query_vector = word_docs[i]["embedding"]
        query_text = word_docs[i]["text"][:200]

        # Dense search
        start_time = time.time()
        client.query.get(collection_name, ["filename", "doc_id", "doc_type"]) \
            .with_near_vector({"vector": query_vector}) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["dense"].append(elapsed)

        # Keyword search (alpha=0)
        start_time = time.time()
        client.query.get(collection_name, ["filename", "doc_id", "doc_type"]) \
            .with_hybrid(query=query_text, alpha=0.0) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["keyword"].append(elapsed)

        # Hybrid search (alpha=0.5)
        start_time = time.time()
        client.query.get(collection_name, ["filename", "doc_id", "doc_type"]) \
            .with_hybrid(query=query_text, alpha=0.5, vector=query_vector) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["hybrid"].append(elapsed)

    return results


def benchmark_weaviate_images(client, images, num_queries=10, collection_name="Phase3FairImages"):
    """Benchmark Weaviate image search (dense only - no text for keyword search)."""
    results = {"dense": []}

    print(f"[Weaviate] Benchmarking image search ({num_queries} queries)...")

    for i in range(num_queries):
        query_vector = images[i]["image_embedding"]

        # Dense search only (images don't have meaningful text for BM25)
        start_time = time.time()
        client.query.get(collection_name, ["filename", "claim_id", "damage_type"]) \
            .with_near_vector({"vector": query_vector}) \
            .with_limit(5) \
            .do()
        elapsed = (time.time() - start_time) * 1000
        results["dense"].append(elapsed)

    return results


def calculate_stats(times):
    """Calculate statistics from timing results."""
    return {
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "p95": np.percentile(times, 95),
        "p99": np.percentile(times, 99)
    }


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Benchmark Milvus 2.5 vs Weaviate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Create temporary collections, benchmark, cleanup
  %(prog)s
  
  # Use existing persistent collections (no data loading or cleanup)
  %(prog)s --use-persistent
"""
    )
    parser.add_argument('--use-persistent', action='store_true',
                       help='Use existing persistent_* collections instead of creating new ones (skips data loading and cleanup)')
    args = parser.parse_args()
    
    print("="*70)
    print("Phase 3 FAIR Benchmarks: Milvus 2.5 vs Weaviate")
    print("Testing same features on both systems: Dense, Sparse/Keyword, Hybrid")
    if args.use_persistent:
        print("Mode: Using existing persistent collections")
    else:
        print("Mode: Creating temporary collections")
    print("="*70)

    # Load data (needed for queries even with persistent collections)
    if not args.use_persistent:
        print("\nLoading processed data...")
        pdfs, word_docs, images = load_processed_data()
        print(f"✓ Loaded {len(pdfs)} PDFs, {len(word_docs)} Word docs, {len(images)} images")
    else:
        print("\nLoading processed data for queries...")
        pdfs, word_docs, images = load_processed_data()
        print(f"✓ Loaded {len(pdfs)} PDFs, {len(word_docs)} Word docs, {len(images)} images")

    # Setup databases
    milvus_client, pdf_coll, word_coll, image_coll = setup_milvus_25(pdfs, word_docs, images, use_persistent=args.use_persistent)
    weaviate_client = setup_weaviate(pdfs, word_docs, images, use_persistent=args.use_persistent)

    # Run benchmarks
    print("\n" + "="*70)
    print("RUNNING FAIR BENCHMARKS")
    print("="*70)

    num_queries = 10

    # Milvus 2.5 benchmarks
    milvus_pdf_results = benchmark_milvus_pdfs(milvus_client, pdf_coll, pdfs, num_queries)
    milvus_word_results = benchmark_milvus_word(milvus_client, word_coll, word_docs, num_queries)
    milvus_image_results = benchmark_milvus_images(milvus_client, image_coll, images, num_queries)

    # Weaviate benchmarks - use appropriate collection names
    if args.use_persistent:
        weaviate_pdf_results = benchmark_weaviate_pdfs(weaviate_client, pdfs, num_queries, collection_name="PersistentPDFs")
        weaviate_word_results = benchmark_weaviate_word(weaviate_client, word_docs, num_queries, collection_name="PersistentWordDocs")
        weaviate_image_results = benchmark_weaviate_images(weaviate_client, images, num_queries, collection_name="PersistentImages")
    else:
        weaviate_pdf_results = benchmark_weaviate_pdfs(weaviate_client, pdfs, num_queries)
        weaviate_word_results = benchmark_weaviate_word(weaviate_client, word_docs, num_queries)
        weaviate_image_results = benchmark_weaviate_images(weaviate_client, images, num_queries)

    # Calculate statistics
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    results = {
        "metadata": {
            "description": "Fair comparison - same features tested on both systems",
            "num_queries": num_queries,
            "use_persistent": args.use_persistent,
            "dataset_size": {
                "pdfs": len(pdfs),
                "word_docs": len(word_docs),
                "images": len(images)
            }
        },
        "milvus_25": {
            "pdf_dense": calculate_stats(milvus_pdf_results["dense"]),
            "pdf_sparse": calculate_stats(milvus_pdf_results["sparse"]),
            "pdf_hybrid": calculate_stats(milvus_pdf_results["hybrid"]),
            "word_dense": calculate_stats(milvus_word_results["dense"]),
            "word_sparse": calculate_stats(milvus_word_results["sparse"]),
            "word_hybrid": calculate_stats(milvus_word_results["hybrid"]),
            "image_dense": calculate_stats(milvus_image_results["dense"])
        },
        "weaviate": {
            "pdf_dense": calculate_stats(weaviate_pdf_results["dense"]),
            "pdf_keyword": calculate_stats(weaviate_pdf_results["keyword"]),
            "pdf_hybrid": calculate_stats(weaviate_pdf_results["hybrid"]),
            "word_dense": calculate_stats(weaviate_word_results["dense"]),
            "word_keyword": calculate_stats(weaviate_word_results["keyword"]),
            "word_hybrid": calculate_stats(weaviate_word_results["hybrid"]),
            "image_dense": calculate_stats(weaviate_image_results["dense"])
        }
    }

    # Print results
    print("\nMilvus 2.5 Results:")
    print(f"  PDF Dense:   {results['milvus_25']['pdf_dense']['avg']:.2f}ms avg")
    print(f"  PDF Sparse:  {results['milvus_25']['pdf_sparse']['avg']:.2f}ms avg")
    print(f"  PDF Hybrid:  {results['milvus_25']['pdf_hybrid']['avg']:.2f}ms avg")
    print(f"  Word Dense:  {results['milvus_25']['word_dense']['avg']:.2f}ms avg")
    print(f"  Word Sparse: {results['milvus_25']['word_sparse']['avg']:.2f}ms avg")
    print(f"  Word Hybrid: {results['milvus_25']['word_hybrid']['avg']:.2f}ms avg")
    print(f"  Image Dense: {results['milvus_25']['image_dense']['avg']:.2f}ms avg")

    print("\nWeaviate Results:")
    print(f"  PDF Dense:   {results['weaviate']['pdf_dense']['avg']:.2f}ms avg")
    print(f"  PDF Keyword: {results['weaviate']['pdf_keyword']['avg']:.2f}ms avg")
    print(f"  PDF Hybrid:  {results['weaviate']['pdf_hybrid']['avg']:.2f}ms avg")
    print(f"  Word Dense:  {results['weaviate']['word_dense']['avg']:.2f}ms avg")
    print(f"  Word Keyword:{results['weaviate']['word_keyword']['avg']:.2f}ms avg")
    print(f"  Word Hybrid: {results['weaviate']['word_hybrid']['avg']:.2f}ms avg")
    print(f"  Image Dense: {results['weaviate']['image_dense']['avg']:.2f}ms avg")

    # Save results
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = Path(os.path.join(script_dir, "..", "results", "benchmark_results.json"))
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")

    # Cleanup (only if not using persistent collections)
    if not args.use_persistent:
        print("\nCleaning up temporary collections...")
        pdf_coll.release()
        word_coll.release()
        image_coll.release()

        from pymilvus import utility
        utility.drop_collection("phase3_fair_pdfs")
        utility.drop_collection("phase3_fair_word")
        utility.drop_collection("phase3_fair_images")

        weaviate_client.schema.delete_class("Phase3FairPDFs")
        weaviate_client.schema.delete_class("Phase3FairWordDocs")
        weaviate_client.schema.delete_class("Phase3FairImages")

        print("✓ Cleanup complete")
    else:
        print("\nSkipping cleanup (using persistent collections)")

    milvus_client.disconnect()

    print("\n" + "="*70)
    print("✓ Phase 3 FAIR Benchmarks Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
