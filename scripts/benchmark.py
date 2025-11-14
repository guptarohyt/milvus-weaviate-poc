"""
Benchmark script to compare Milvus and Weaviate performance.
Tests query performance, scalability, and features.
"""

import json
import time
import statistics
from pathlib import Path
from typing import Dict, List, Callable
import psutil
from milvus_client import MilvusReinsuranceClient
from weaviate_client import WeaviateReinsuranceClient


class BenchmarkRunner:
    """Run benchmarks comparing Milvus and Weaviate."""

    def __init__(self):
        self.milvus_client = None
        self.weaviate_client = None
        self.results = {
            "milvus": {},
            "weaviate": {}
        }

    def setup(self, data_size: int = 1000):
        """Setup both clients and load data."""
        print("="*60)
        print("BENCHMARK SETUP")
        print("="*60)

        # Load data
        data_dir = Path("data")
        with open(data_dir / "policies.json") as f:
            policies = json.load(f)
        with open(data_dir / "claims.json") as f:
            claims = json.load(f)
        with open(data_dir / "knowledge_base.json") as f:
            knowledge = json.load(f)

        # Limit data size
        policies = policies[:min(data_size, len(policies))]
        claims = claims[:min(data_size * 2, len(claims))]
        knowledge = knowledge[:min(data_size // 2, len(knowledge))]

        print(f"\nData size: {len(policies)} policies, {len(claims)} claims, {len(knowledge)} knowledge articles")

        # Setup Milvus
        print("\n--- Setting up Milvus ---")
        self.milvus_client = MilvusReinsuranceClient()
        start_time = time.time()
        self.milvus_client.connect()
        self.milvus_client.insert_policies(policies)
        self.milvus_client.insert_claims(claims)
        self.milvus_client.insert_knowledge(knowledge)
        self.milvus_client.load_collections()
        milvus_setup_time = time.time() - start_time

        # Setup Weaviate
        print("\n--- Setting up Weaviate ---")
        self.weaviate_client = WeaviateReinsuranceClient()
        start_time = time.time()
        self.weaviate_client.connect()
        self.weaviate_client.create_collections()
        self.weaviate_client.insert_policies(policies)
        self.weaviate_client.insert_claims(claims)
        self.weaviate_client.insert_knowledge(knowledge)
        weaviate_setup_time = time.time() - start_time

        # Record setup times
        self.results["milvus"]["setup_time"] = milvus_setup_time
        self.results["weaviate"]["setup_time"] = weaviate_setup_time

        print(f"\n✓ Milvus setup time: {milvus_setup_time:.2f}s")
        print(f"✓ Weaviate setup time: {weaviate_setup_time:.2f}s")

    def benchmark_query_performance(self):
        """Benchmark query performance for both systems."""
        print("\n" + "="*60)
        print("QUERY PERFORMANCE BENCHMARK")
        print("="*60)

        # Test queries for each use case
        policy_queries = [
            "property catastrophe coverage for hurricane events",
            "cyber risk reinsurance for financial institutions",
            "professional liability coverage for healthcare providers"
        ]

        claim_queries = [
            "flood damage to commercial property",
            "cyber attack data breach incident",
            "professional negligence medical malpractice"
        ]

        knowledge_queries = [
            "underwriting guidelines for catastrophe risk assessment",
            "regulatory compliance requirements for reinsurance",
            "claims handling procedures for large losses"
        ]

        # Run benchmarks
        print("\n--- Policy Search Performance ---")
        milvus_policy_times = self._run_search_benchmark(
            self.milvus_client.search_policies,
            policy_queries,
            "Milvus"
        )

        weaviate_policy_times = self._run_search_benchmark(
            self.weaviate_client.search_policies,
            policy_queries,
            "Weaviate"
        )

        print("\n--- Claims Search Performance ---")
        milvus_claim_times = self._run_search_benchmark(
            self.milvus_client.search_claims,
            claim_queries,
            "Milvus"
        )

        weaviate_claim_times = self._run_search_benchmark(
            self.weaviate_client.search_claims,
            claim_queries,
            "Weaviate"
        )

        print("\n--- Knowledge Base Search Performance ---")
        milvus_kb_times = self._run_search_benchmark(
            self.milvus_client.search_knowledge,
            knowledge_queries,
            "Milvus"
        )

        weaviate_kb_times = self._run_search_benchmark(
            self.weaviate_client.search_knowledge,
            knowledge_queries,
            "Weaviate"
        )

        # Store results
        self.results["milvus"]["query_performance"] = {
            "policy_avg": statistics.mean(milvus_policy_times),
            "claim_avg": statistics.mean(milvus_claim_times),
            "knowledge_avg": statistics.mean(milvus_kb_times),
            "overall_avg": statistics.mean(milvus_policy_times + milvus_claim_times + milvus_kb_times)
        }

        self.results["weaviate"]["query_performance"] = {
            "policy_avg": statistics.mean(weaviate_policy_times),
            "claim_avg": statistics.mean(weaviate_claim_times),
            "knowledge_avg": statistics.mean(weaviate_kb_times),
            "overall_avg": statistics.mean(weaviate_policy_times + weaviate_claim_times + weaviate_kb_times)
        }

    def _run_search_benchmark(self, search_func: Callable, queries: List[str], system: str) -> List[float]:
        """Run search benchmark for a specific function."""
        times = []

        for query in queries:
            result = search_func(query, limit=10)
            times.append(result["search_time"])
            print(f"  {system} - '{query[:50]}...': {result['search_time']:.4f}s")

        avg_time = statistics.mean(times)
        print(f"  {system} average: {avg_time:.4f}s")

        return times

    def benchmark_filtered_search(self):
        """Benchmark filtered search capabilities."""
        print("\n" + "="*60)
        print("FILTERED SEARCH BENCHMARK")
        print("="*60)

        # Milvus filtered search (using expression filters)
        print("\n--- Milvus Filtered Search ---")
        start = time.time()
        result = self.milvus_client.search_policies(
            "catastrophe coverage",
            limit=10,
            filters='limit > 5000000'  # Policies with limit > $5M
        )
        milvus_time = time.time() - start
        print(f"  Search with filter (limit > $5M): {milvus_time:.4f}s")
        print(f"  Results found: {len(result['results'])}")

        # Weaviate filtered search
        print("\n--- Weaviate Filtered Search ---")
        start = time.time()
        result = self.weaviate_client.search_policies(
            "catastrophe coverage",
            limit=10,
            filters={"field": "limit", "operator": "greater_than", "value": 5000000}
        )
        weaviate_time = time.time() - start
        print(f"  Search with filter (limit > $5M): {weaviate_time:.4f}s")
        print(f"  Results found: {len(result['results'])}")

        self.results["milvus"]["filtered_search_time"] = milvus_time
        self.results["weaviate"]["filtered_search_time"] = weaviate_time

    def benchmark_hybrid_search(self):
        """Benchmark hybrid search (vector + keyword) - Weaviate feature."""
        print("\n" + "="*60)
        print("HYBRID SEARCH BENCHMARK (Weaviate Feature)")
        print("="*60)

        queries = [
            "regulatory compliance",
            "underwriting guidelines",
            "claims procedures"
        ]

        print("\n--- Weaviate Hybrid Search ---")
        hybrid_times = []

        for query in queries:
            result = self.weaviate_client.hybrid_search_knowledge(query, limit=10, alpha=0.5)
            hybrid_times.append(result["search_time"])
            print(f"  '{query}': {result['search_time']:.4f}s")

        avg_time = statistics.mean(hybrid_times)
        print(f"  Average: {avg_time:.4f}s")

        self.results["weaviate"]["hybrid_search_avg"] = avg_time
        self.results["milvus"]["hybrid_search_support"] = False
        self.results["weaviate"]["hybrid_search_support"] = True

        print("\n  Note: Milvus does not have built-in hybrid search.")
        print("        Would require custom implementation combining vector + BM25.")

    def benchmark_resource_usage(self):
        """Benchmark memory and CPU usage."""
        print("\n" + "="*60)
        print("RESOURCE USAGE")
        print("="*60)

        # Get current process memory
        process = psutil.Process()
        memory_info = process.memory_info()

        print(f"\nCurrent process memory: {memory_info.rss / 1024 / 1024:.2f} MB")

        # Note: Would need separate monitoring for Docker containers
        print("\n  Note: For accurate Docker container resource usage,")
        print("        run: docker stats --no-stream")

    def evaluate_features(self):
        """Evaluate feature richness."""
        print("\n" + "="*60)
        print("FEATURE COMPARISON")
        print("="*60)

        features = {
            "milvus": {
                "vector_search": True,
                "filtered_search": True,
                "hybrid_search": False,
                "multi_tenancy": True,
                "collection_aliases": True,
                "dynamic_schema": False,
                "index_types": ["IVF_FLAT", "IVF_SQ8", "IVF_PQ", "HNSW", "ANNOY"],
                "distance_metrics": ["L2", "IP", "COSINE"],
                "partition_support": True,
                "query_result_caching": True,
                "bulk_insert": True,
                "time_travel": True
            },
            "weaviate": {
                "vector_search": True,
                "filtered_search": True,
                "hybrid_search": True,
                "multi_tenancy": True,
                "collection_aliases": False,
                "dynamic_schema": True,
                "index_types": ["HNSW"],
                "distance_metrics": ["cosine", "dot", "l2-squared", "hamming", "manhattan"],
                "partition_support": False,
                "query_result_caching": False,
                "bulk_insert": True,
                "graphql_api": True,
                "restful_api": True,
                "module_system": True
            }
        }

        self.results["milvus"]["features"] = features["milvus"]
        self.results["weaviate"]["features"] = features["weaviate"]

        print("\nMilvus Features:")
        for key, value in features["milvus"].items():
            print(f"  - {key}: {value}")

        print("\nWeaviate Features:")
        for key, value in features["weaviate"].items():
            print(f"  - {key}: {value}")

    def evaluate_ease_of_use(self):
        """Evaluate developer experience and ease of use."""
        print("\n" + "="*60)
        print("EASE OF USE EVALUATION")
        print("="*60)

        ease_of_use = {
            "milvus": {
                "setup_complexity": "Medium - Requires etcd, MinIO, and Milvus services",
                "api_intuitiveness": "Good - Python SDK is comprehensive",
                "documentation": "Good - Extensive docs and examples",
                "schema_definition": "Explicit schema required upfront",
                "error_messages": "Generally clear",
                "learning_curve": "Medium - Need to understand collections, partitions, indexes"
            },
            "weaviate": {
                "setup_complexity": "Easy - Single container deployment",
                "api_intuitiveness": "Excellent - Clean, intuitive Python client",
                "documentation": "Excellent - Well-organized with many examples",
                "schema_definition": "Flexible - Can be defined dynamically",
                "error_messages": "Very clear and helpful",
                "learning_curve": "Low - Quick to get started, intuitive concepts"
            }
        }

        self.results["milvus"]["ease_of_use"] = ease_of_use["milvus"]
        self.results["weaviate"]["ease_of_use"] = ease_of_use["weaviate"]

        print("\nMilvus:")
        for key, value in ease_of_use["milvus"].items():
            print(f"  - {key}: {value}")

        print("\nWeaviate:")
        for key, value in ease_of_use["weaviate"].items():
            print(f"  - {key}: {value}")

    def generate_report(self):
        """Generate final comparison report."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)

        # Performance summary
        print("\n1. QUERY PERFORMANCE")
        print("-" * 40)
        milvus_avg = self.results["milvus"]["query_performance"]["overall_avg"]
        weaviate_avg = self.results["weaviate"]["query_performance"]["overall_avg"]

        print(f"Milvus average query time:   {milvus_avg:.4f}s")
        print(f"Weaviate average query time: {weaviate_avg:.4f}s")

        if milvus_avg < weaviate_avg:
            diff = ((weaviate_avg - milvus_avg) / weaviate_avg) * 100
            print(f"→ Milvus is {diff:.1f}% faster")
        else:
            diff = ((milvus_avg - weaviate_avg) / milvus_avg) * 100
            print(f"→ Weaviate is {diff:.1f}% faster")

        # Setup time
        print("\n2. SETUP & INDEXING TIME")
        print("-" * 40)
        print(f"Milvus setup time:   {self.results['milvus']['setup_time']:.2f}s")
        print(f"Weaviate setup time: {self.results['weaviate']['setup_time']:.2f}s")

        # Features
        print("\n3. FEATURE HIGHLIGHTS")
        print("-" * 40)
        print("Milvus:")
        print("  ✓ Multiple index types (IVF_FLAT, HNSW, etc.)")
        print("  ✓ Partition support for data organization")
        print("  ✓ Time travel queries")
        print("  ✗ No built-in hybrid search")

        print("\nWeaviate:")
        print("  ✓ Built-in hybrid search (vector + keyword)")
        print("  ✓ Dynamic schema support")
        print("  ✓ GraphQL API")
        print("  ✓ Modular architecture with plugins")

        # Recommendations
        print("\n4. RECOMMENDATIONS FOR REINSURANCE USE CASES")
        print("-" * 40)

        print("\nChoose Milvus if:")
        print("  • You need maximum query performance")
        print("  • You have large-scale data (billions of vectors)")
        print("  • You want fine-grained control over indexing strategies")
        print("  • You need partition-based data isolation (e.g., per client)")
        print("  • You're comfortable with more complex setup")

        print("\nChoose Weaviate if:")
        print("  • You want hybrid search (semantic + keyword)")
        print("  • You need quick setup and easy deployment")
        print("  • You prefer intuitive APIs and excellent documentation")
        print("  • You want to leverage pre-built modules (vectorizers, etc.)")
        print("  • Developer experience is a priority")

        print("\n" + "="*60)

        # Save results to file
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)

        with open(results_dir / "benchmark_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ Full results saved to: results/benchmark_results.json")

    def cleanup(self):
        """Cleanup connections."""
        if self.milvus_client:
            self.milvus_client.disconnect()
        if self.weaviate_client:
            self.weaviate_client.disconnect()


def main():
    """Run full benchmark suite."""
    runner = BenchmarkRunner()

    try:
        # Setup
        runner.setup(data_size=1000)

        # Run benchmarks
        runner.benchmark_query_performance()
        runner.benchmark_filtered_search()
        runner.benchmark_hybrid_search()
        runner.benchmark_resource_usage()

        # Evaluate
        runner.evaluate_features()
        runner.evaluate_ease_of_use()

        # Generate report
        runner.generate_report()

    except Exception as e:
        print(f"\n❌ Error during benchmark: {e}")
        import traceback
        traceback.print_exc()

    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()
