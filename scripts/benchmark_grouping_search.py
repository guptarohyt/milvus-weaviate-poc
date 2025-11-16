#!/usr/bin/env python3
"""
Benchmark Milvus 2.5 Grouping Search Performance

This script benchmarks the new grouping search feature in Milvus 2.5,
which allows grouping results by a specific field (e.g., policy_id, claim_id).

Use Cases:
1. Find all documents related to a specific claim (PDFs, images, reports)
2. Group search results by policy type
3. Get one representative document per policy

Comparison:
- Regular search: Returns top N similar documents (may have duplicates from same policy)
- Grouping search: Returns top N groups, one document per group
"""

import json
import time
import random
from typing import List, Dict, Any
from pathlib import Path
from pymilvus import MilvusClient, connections
from sentence_transformers import SentenceTransformer

# Configuration
MILVUS_URI = "http://localhost:19530"
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# Embedding model
print("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("✓ Model loaded")


def benchmark_regular_search(client: MilvusClient, collection: str, queries: List[str], limit: int = 10) -> Dict[str, Any]:
    """Benchmark regular dense search (no grouping)"""
    times = []
    results_counts = []

    for query in queries:
        # Generate query vector
        query_vector = model.encode(query).tolist()

        # Search
        start = time.time()
        results = client.search(
            collection_name=collection,
            data=[query_vector],
            limit=limit,
            output_fields=["filename", "policy_type", "content"]
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        times.append(elapsed)
        results_counts.append(len(results[0]) if results else 0)

    return {
        "avg_time_ms": sum(times) / len(times),
        "median_time_ms": sorted(times)[len(times) // 2],
        "min_time_ms": min(times),
        "max_time_ms": max(times),
        "avg_results": sum(results_counts) / len(results_counts),
        "queries": len(queries),
        "times": times
    }


def benchmark_grouping_search(client: MilvusClient, collection: str, queries: List[str],
                              group_by_field: str, limit: int = 10) -> Dict[str, Any]:
    """Benchmark grouping search (Milvus 2.5 feature)"""
    times = []
    results_counts = []
    unique_groups_counts = []

    for query in queries:
        # Generate query vector
        query_vector = model.encode(query).tolist()

        # Grouping search
        start = time.time()
        try:
            results = client.search(
                collection_name=collection,
                data=[query_vector],
                limit=limit,
                output_fields=["filename", "policy_type", "content", group_by_field],
                search_params={
                    "metric_type": "COSINE",
                    "params": {}
                },
                group_by_field=group_by_field,
                group_size=1  # One result per group
            )
            elapsed = (time.time() - start) * 1000

            # Count unique groups
            if results and len(results) > 0:
                groups = set()
                for hit in results[0]:
                    if hasattr(hit, 'entity') and group_by_field in hit.entity:
                        groups.add(hit.entity.get(group_by_field))
                unique_groups_counts.append(len(groups))
                results_counts.append(len(results[0]))
            else:
                unique_groups_counts.append(0)
                results_counts.append(0)

        except Exception as e:
            print(f"  ⚠ Grouping search failed: {e}")
            # Fall back to regular search timing
            elapsed = 0
            unique_groups_counts.append(0)
            results_counts.append(0)

        times.append(elapsed)

    # Filter out failed queries (0 time)
    valid_times = [t for t in times if t > 0]

    if not valid_times:
        return {
            "error": "All grouping searches failed",
            "avg_time_ms": 0,
            "queries": len(queries)
        }

    return {
        "avg_time_ms": sum(valid_times) / len(valid_times),
        "median_time_ms": sorted(valid_times)[len(valid_times) // 2],
        "min_time_ms": min(valid_times),
        "max_time_ms": max(valid_times),
        "avg_results": sum(results_counts) / len(results_counts),
        "avg_unique_groups": sum(unique_groups_counts) / len(unique_groups_counts),
        "queries": len(queries),
        "successful_queries": len(valid_times),
        "times": valid_times
    }


def calculate_overhead(regular_time: float, grouping_time: float) -> Dict[str, Any]:
    """Calculate the performance overhead of grouping"""
    overhead_ms = grouping_time - regular_time
    overhead_percent = (overhead_ms / regular_time) * 100 if regular_time > 0 else 0

    return {
        "overhead_ms": overhead_ms,
        "overhead_percent": overhead_percent,
        "regular_time_ms": regular_time,
        "grouping_time_ms": grouping_time,
        "slower_by_factor": grouping_time / regular_time if regular_time > 0 else 0
    }


def main():
    print("\n" + "="*70)
    print("Milvus 2.5 Grouping Search Benchmark")
    print("="*70)

    # Connect to Milvus
    print(f"\nConnecting to Milvus at {MILVUS_URI}...")
    client = MilvusClient(uri=MILVUS_URI)
    print("✓ Connected")

    # List collections
    collections = client.list_collections()
    print(f"\nAvailable collections: {collections}")

    # Test queries
    test_queries = [
        "auto insurance policy for sedan vehicle",
        "home insurance with fire coverage",
        "life insurance policy with beneficiary",
        "vehicle damage claim investigation",
        "property damage assessment report",
        "insurance premium calculation",
        "policy renewal documentation",
        "claim settlement process",
        "underwriting risk assessment",
        "coverage limits and deductibles"
    ]

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "milvus_uri": MILVUS_URI,
        "queries": test_queries,
        "benchmarks": {}
    }

    # Benchmark PDF collections
    pdf_collections = [col for col in collections if 'pdf' in col.lower()]

    for collection in pdf_collections:
        print(f"\n{'='*70}")
        print(f"Benchmarking: {collection}")
        print(f"{'='*70}")

        # Get collection info
        try:
            stats = client.get_collection_stats(collection)
            print(f"Collection stats: {stats}")
        except:
            print("Could not get collection stats")

        # Check if collection has policy_type field for grouping
        try:
            # Describe collection to get schema
            schema_info = client.describe_collection(collection)
            print(f"Schema: {schema_info}")

            # Try to find a groupable field
            groupable_fields = ["policy_type", "type", "category"]
            group_field = None

            # For this benchmark, we'll assume policy_type exists
            group_field = "policy_type"

            print(f"\n1. Regular Search (no grouping)")
            print("-" * 50)
            regular_results = benchmark_regular_search(client, collection, test_queries, limit=10)
            print(f"   Avg time: {regular_results['avg_time_ms']:.2f}ms")
            print(f"   Median time: {regular_results['median_time_ms']:.2f}ms")
            print(f"   Avg results: {regular_results['avg_results']:.1f}")

            print(f"\n2. Grouping Search (group by {group_field})")
            print("-" * 50)
            grouping_results = benchmark_grouping_search(
                client, collection, test_queries,
                group_by_field=group_field,
                limit=10
            )

            if "error" not in grouping_results:
                print(f"   Avg time: {grouping_results['avg_time_ms']:.2f}ms")
                print(f"   Median time: {grouping_results['median_time_ms']:.2f}ms")
                print(f"   Avg results: {grouping_results['avg_results']:.1f}")
                print(f"   Avg unique groups: {grouping_results['avg_unique_groups']:.1f}")
                print(f"   Successful queries: {grouping_results['successful_queries']}/{grouping_results['queries']}")

                # Calculate overhead
                overhead = calculate_overhead(
                    regular_results['avg_time_ms'],
                    grouping_results['avg_time_ms']
                )

                print(f"\n3. Grouping Overhead Analysis")
                print("-" * 50)
                print(f"   Overhead: +{overhead['overhead_ms']:.2f}ms ({overhead['overhead_percent']:.1f}%)")
                print(f"   Slower by factor: {overhead['slower_by_factor']:.2f}x")

                results["benchmarks"][collection] = {
                    "regular_search": regular_results,
                    "grouping_search": grouping_results,
                    "overhead": overhead,
                    "group_field": group_field
                }
            else:
                print(f"   ✗ {grouping_results['error']}")
                results["benchmarks"][collection] = {
                    "regular_search": regular_results,
                    "grouping_search": grouping_results,
                    "note": "Grouping search not supported or failed"
                }

        except Exception as e:
            print(f"✗ Error benchmarking {collection}: {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_file = RESULTS_DIR / "grouping_search_benchmark.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for collection, data in results["benchmarks"].items():
        if "overhead" in data:
            print(f"\n{collection}:")
            print(f"  Regular search:  {data['regular_search']['avg_time_ms']:.2f}ms")
            print(f"  Grouping search: {data['grouping_search']['avg_time_ms']:.2f}ms")
            print(f"  Overhead:        +{data['overhead']['overhead_percent']:.1f}%")
            print(f"  Unique groups:   {data['grouping_search']['avg_unique_groups']:.1f}")


if __name__ == "__main__":
    main()
