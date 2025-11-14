"""
Phase 2 Multi-Modal Benchmark: Milvus vs Weaviate
Compares performance on PDFs, Word documents, and images.
"""

import json
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any
import random
from sentence_transformers import SentenceTransformer
from milvus_multimodal_client import MilvusMultiModalClient
from weaviate_multimodal_client import WeaviateMultiModalClient


class MultiModalBenchmark:
    """Benchmark multi-modal search performance."""

    def __init__(self):
        """Initialize benchmark."""
        print("="*70)
        print("PHASE 2 MULTI-MODAL BENCHMARK: MILVUS VS WEAVIATE")
        print("="*70)

        # Load embedding model
        print("\nLoading embedding model...")
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Loaded all-MiniLM-L6-v2")

        # Load processed data for test queries
        self.load_test_data()

    def load_test_data(self):
        """Load processed data for generating test queries."""
        data_dir = Path("./data/multimodal/processed")

        with open(data_dir / "pdfs_processed.json") as f:
            self.pdfs = json.load(f)

        with open(data_dir / "word_docs_processed.json") as f:
            self.word_docs = json.load(f)

        with open(data_dir / "images_processed.json") as f:
            self.images = json.load(f)

        print(f"✓ Loaded {len(self.pdfs)} PDFs, {len(self.word_docs)} Word docs, {len(self.images)} images")

    def generate_text_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding for text query."""
        return self.text_model.encode(query_text).tolist()

    def benchmark_pdf_search(self, client, client_name: str, num_queries: int = 10):
        """Benchmark PDF document search."""
        print(f"\n{'='*70}")
        print(f"{client_name}: PDF SEARCH BENCHMARK")
        print(f"{'='*70}")

        test_queries = [
            "property damage insurance policy",
            "catastrophe reinsurance treaty",
            "coverage limits and deductibles",
            "loss ratio and premium calculations",
            "underwriting risk assessment",
            "claims settlement procedures",
            "excess of loss reinsurance",
            "quota share treaty terms",
            "facultative reinsurance agreement",
            "retrocession coverage details"
        ]

        query_times = []

        for i, query_text in enumerate(test_queries[:num_queries], 1):
            query_embedding = self.generate_text_query_embedding(query_text)

            if isinstance(client, MilvusMultiModalClient):
                results, elapsed = client.search_pdfs(query_embedding, top_k=5)
            else:  # Weaviate
                results, elapsed = client.search_pdfs(query_embedding, top_k=5)

            query_times.append(elapsed)
            print(f"Query {i}: {elapsed:.2f}ms - '{query_text[:50]}'")

        avg_time = statistics.mean(query_times)
        median_time = statistics.median(query_times)

        print(f"\nResults:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median:  {median_time:.2f}ms")
        print(f"  Min:     {min(query_times):.2f}ms")
        print(f"  Max:     {max(query_times):.2f}ms")

        return {
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min(query_times),
            'max_time_ms': max(query_times),
            'queries': num_queries
        }

    def benchmark_word_search(self, client, client_name: str, num_queries: int = 10):
        """Benchmark Word document search."""
        print(f"\n{'='*70}")
        print(f"{client_name}: WORD DOCUMENT SEARCH BENCHMARK")
        print(f"{'='*70}")

        test_queries = [
            "claims investigation report",
            "underwriting guidelines policy",
            "fraud detection procedures",
            "loss adjuster recommendations",
            "policy coverage analysis",
            "risk assessment criteria",
            "claims approval process",
            "underwriting standards",
            "settlement negotiations",
            "compliance requirements"
        ]

        query_times = []

        for i, query_text in enumerate(test_queries[:num_queries], 1):
            query_embedding = self.generate_text_query_embedding(query_text)

            if isinstance(client, MilvusMultiModalClient):
                results, elapsed = client.search_word_docs(query_embedding, top_k=5)
            else:  # Weaviate
                results, elapsed = client.search_word_docs(query_embedding, top_k=5)

            query_times.append(elapsed)
            print(f"Query {i}: {elapsed:.2f}ms - '{query_text[:50]}'")

        avg_time = statistics.mean(query_times)
        median_time = statistics.median(query_times)

        print(f"\nResults:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median:  {median_time:.2f}ms")
        print(f"  Min:     {min(query_times):.2f}ms")
        print(f"  Max:     {max(query_times):.2f}ms")

        return {
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min(query_times),
            'max_time_ms': max(query_times),
            'queries': num_queries
        }

    def benchmark_image_to_image_search(self, client, client_name: str, num_queries: int = 10):
        """Benchmark image-to-image search (CLIP embeddings)."""
        print(f"\n{'='*70}")
        print(f"{client_name}: IMAGE-TO-IMAGE SEARCH BENCHMARK")
        print(f"{'='*70}")

        # Use random images as queries
        test_images = random.sample(self.images, num_queries)
        query_times = []

        for i, img in enumerate(test_images, 1):
            query_embedding = img['image_embedding']

            if isinstance(client, MilvusMultiModalClient):
                results, elapsed = client.search_images_by_image(query_embedding, top_k=5)
            else:  # Weaviate
                results, elapsed = client.search_images_by_image(query_embedding, top_k=5)

            query_times.append(elapsed)
            print(f"Query {i}: {elapsed:.2f}ms - {img['damage_type']} (severity: {img['severity']:.2f})")

        avg_time = statistics.mean(query_times)
        median_time = statistics.median(query_times)

        print(f"\nResults:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median:  {median_time:.2f}ms")
        print(f"  Min:     {min(query_times):.2f}ms")
        print(f"  Max:     {max(query_times):.2f}ms")

        return {
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min(query_times),
            'max_time_ms': max(query_times),
            'queries': num_queries
        }

    def benchmark_text_to_image_search(self, client, client_name: str, num_queries: int = 10):
        """Benchmark text-to-image search."""
        print(f"\n{'='*70}")
        print(f"{client_name}: TEXT-TO-IMAGE SEARCH BENCHMARK")
        print(f"{'='*70}")

        test_queries = [
            "hurricane damage to buildings",
            "flood water damage assessment",
            "fire damage to property",
            "structural damage from earthquake",
            "severe storm damage photos",
            "property damage inspection",
            "catastrophic loss images",
            "building collapse damage",
            "wind damage to structures",
            "water intrusion damage"
        ]

        query_times = []

        for i, query_text in enumerate(test_queries[:num_queries], 1):
            query_embedding = self.generate_text_query_embedding(query_text)

            if isinstance(client, MilvusMultiModalClient):
                results, elapsed = client.search_images_by_text(query_embedding, top_k=5)
            else:  # Weaviate
                results, elapsed = client.search_images_by_text(query_embedding, top_k=5)

            query_times.append(elapsed)
            print(f"Query {i}: {elapsed:.2f}ms - '{query_text[:50]}'")

        avg_time = statistics.mean(query_times)
        median_time = statistics.median(query_times)

        print(f"\nResults:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median:  {median_time:.2f}ms")
        print(f"  Min:     {min(query_times):.2f}ms")
        print(f"  Max:     {max(query_times):.2f}ms")

        return {
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min(query_times),
            'max_time_ms': max(query_times),
            'queries': num_queries
        }

    def benchmark_filtered_image_search(self, client, client_name: str, num_queries: int = 5):
        """Benchmark filtered image search (Weaviate only)."""
        if isinstance(client, MilvusMultiModalClient):
            print(f"\n{client_name}: Filtered search not implemented for Milvus in this POC")
            return None

        print(f"\n{'='*70}")
        print(f"{client_name}: FILTERED IMAGE SEARCH BENCHMARK")
        print(f"{'='*70}")

        test_cases = [
            ("hurricane damage photos", "hurricane", None),
            ("severe flood damage", "flood", 0.7),
            ("fire damage assessment", "fire", 0.5),
            ("structural damage inspection", "structural", None),
            ("high severity hurricane", "hurricane", 0.8),
        ]

        query_times = []

        for i, (query_text, damage_type, min_severity) in enumerate(test_cases[:num_queries], 1):
            query_embedding = self.generate_text_query_embedding(query_text)

            results, elapsed = client.search_images_filtered(
                query_embedding,
                damage_type=damage_type,
                min_severity=min_severity,
                top_k=5
            )

            query_times.append(elapsed)
            severity_str = f", severity>={min_severity}" if min_severity else ""
            print(f"Query {i}: {elapsed:.2f}ms - type={damage_type}{severity_str}")

        avg_time = statistics.mean(query_times)
        median_time = statistics.median(query_times)

        print(f"\nResults:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median:  {median_time:.2f}ms")
        print(f"  Min:     {min(query_times):.2f}ms")
        print(f"  Max:     {max(query_times):.2f}ms")

        return {
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min(query_times),
            'max_time_ms': max(query_times),
            'queries': num_queries
        }

    def run_full_benchmark(self):
        """Run complete benchmark suite."""
        results = {
            'milvus': {},
            'weaviate': {},
            'comparison': {}
        }

        # Initialize clients
        print("\n" + "="*70)
        print("INITIALIZING CLIENTS")
        print("="*70)

        milvus_client = MilvusMultiModalClient(load_existing=True)
        weaviate_client = WeaviateMultiModalClient()

        # Milvus benchmarks
        print("\n" + "="*70)
        print("MILVUS BENCHMARKS")
        print("="*70)

        results['milvus']['pdf_search'] = self.benchmark_pdf_search(milvus_client, "MILVUS")
        results['milvus']['word_search'] = self.benchmark_word_search(milvus_client, "MILVUS")
        results['milvus']['image_to_image'] = self.benchmark_image_to_image_search(milvus_client, "MILVUS")
        results['milvus']['text_to_image'] = self.benchmark_text_to_image_search(milvus_client, "MILVUS")

        # Weaviate benchmarks
        print("\n" + "="*70)
        print("WEAVIATE BENCHMARKS")
        print("="*70)

        results['weaviate']['pdf_search'] = self.benchmark_pdf_search(weaviate_client, "WEAVIATE")
        results['weaviate']['word_search'] = self.benchmark_word_search(weaviate_client, "WEAVIATE")
        results['weaviate']['image_to_image'] = self.benchmark_image_to_image_search(weaviate_client, "WEAVIATE")
        results['weaviate']['text_to_image'] = self.benchmark_text_to_image_search(weaviate_client, "WEAVIATE")
        results['weaviate']['filtered_search'] = self.benchmark_filtered_image_search(weaviate_client, "WEAVIATE")

        # Get collection stats
        results['milvus']['stats'] = milvus_client.get_stats()
        results['weaviate']['stats'] = weaviate_client.get_stats()

        # Comparisons
        for benchmark_type in ['pdf_search', 'word_search', 'image_to_image', 'text_to_image']:
            milvus_avg = results['milvus'][benchmark_type]['avg_time_ms']
            weaviate_avg = results['weaviate'][benchmark_type]['avg_time_ms']

            speedup = (milvus_avg / weaviate_avg - 1) * 100
            faster = "Weaviate" if speedup > 0 else "Milvus"

            results['comparison'][benchmark_type] = {
                'milvus_avg_ms': milvus_avg,
                'weaviate_avg_ms': weaviate_avg,
                'speedup_percent': abs(speedup),
                'faster': faster
            }

        # Close clients
        milvus_client.close()
        weaviate_client.close()

        return results

    def print_summary(self, results: Dict[str, Any]):
        """Print benchmark summary."""
        print("\n" + "="*70)
        print("PHASE 2 BENCHMARK SUMMARY")
        print("="*70)

        print("\n📊 COLLECTION STATISTICS:")
        print(f"  Milvus:   {results['milvus']['stats']}")
        print(f"  Weaviate: {results['weaviate']['stats']}")

        print("\n⚡ QUERY PERFORMANCE COMPARISON:")
        print(f"{'Benchmark':<25} {'Milvus':<12} {'Weaviate':<12} {'Winner':<15}")
        print("-" * 70)

        for benchmark_type, comparison in results['comparison'].items():
            name = benchmark_type.replace('_', ' ').title()
            milvus_time = comparison['milvus_avg_ms']
            weaviate_time = comparison['weaviate_avg_ms']
            faster = comparison['faster']
            speedup = comparison['speedup_percent']

            print(f"{name:<25} {milvus_time:>8.2f}ms  {weaviate_time:>8.2f}ms  {faster} (+{speedup:.1f}%)")

        print("\n🎯 KEY FINDINGS:")

        # Overall winner
        weaviate_wins = sum(1 for c in results['comparison'].values() if c['faster'] == 'Weaviate')
        milvus_wins = sum(1 for c in results['comparison'].values() if c['faster'] == 'Milvus')

        print(f"  • Weaviate wins: {weaviate_wins}/4 benchmarks")
        print(f"  • Milvus wins:   {milvus_wins}/4 benchmarks")

        # Average speedup
        avg_speedup = statistics.mean([c['speedup_percent'] for c in results['comparison'].values()])
        overall_faster = "Weaviate" if weaviate_wins > milvus_wins else "Milvus"
        print(f"  • Overall faster: {overall_faster} (avg {avg_speedup:.1f}% faster)")

        # Unique Weaviate features
        if results['weaviate']['filtered_search']:
            filtered_time = results['weaviate']['filtered_search']['avg_time_ms']
            print(f"  • Weaviate filtered search: {filtered_time:.2f}ms (not available in Milvus)")

        print("\n✅ Phase 2 Multi-Modal Benchmark Complete!")


def main():
    """Run Phase 2 benchmark."""
    benchmark = MultiModalBenchmark()
    results = benchmark.run_full_benchmark()
    benchmark.print_summary(results)

    # Save results
    output_dir = Path("../results")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "phase2_benchmark_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
