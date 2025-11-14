"""
Main script to run the complete Milvus vs Weaviate comparison.
Orchestrates data generation, loading, and benchmarking.
"""

import sys
import time
import os
from pathlib import Path
import subprocess


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_docker_containers():
    """Check if Docker containers are running."""
    print_header("Checking Docker Containers")

    # Try docker compose (V2) first, then docker-compose (V1)
    docker_cmd = None
    for cmd in [["docker", "compose"], ["docker-compose"]]:
        try:
            result = subprocess.run(
                cmd + ["version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                docker_cmd = cmd
                break
        except FileNotFoundError:
            continue

    if docker_cmd is None:
        print("❌ Docker Compose not found. Please install Docker Compose.")
        print("   Visit: https://docs.docker.com/compose/install/")
        return False

    try:
        # Check if containers are running
        result = subprocess.run(
            docker_cmd + ["ps"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if "milvus-standalone" not in result.stdout or "weaviate-standalone" not in result.stdout:
            print("⚠️  Containers not running. Starting Docker containers...")
            print("   This may take a few minutes on first run...\n")

            # Start containers
            start_result = subprocess.run(
                docker_cmd + ["up", "-d"],
                capture_output=True,
                text=True,
                timeout=180
            )

            if start_result.returncode != 0:
                print(f"❌ Failed to start containers:\n{start_result.stderr}")
                return False

            print("   Waiting for services to be ready (30 seconds)...")
            time.sleep(30)

        print("✓ Docker containers are running")
        return True

    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def generate_data():
    """Generate synthetic reinsurance data."""
    print_header("Generating Synthetic Data")

    data_dir = Path("data")

    # Check if data already exists
    if (data_dir / "policies.json").exists():
        print("⚠️  Data files already exist.")
        if os.environ.get('AUTO_RUN') == '1':
            print("   Auto-run mode: Skipping data generation...")
            return True
        response = input("   Regenerate data? (y/N): ").strip().lower()
        if response != 'y':
            print("   Skipping data generation...")
            return True

    try:
        from generate_data import main as generate_main
        generate_main()
        return True
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_benchmark():
    """Run the benchmark comparison."""
    print_header("Running Benchmark Comparison")
    print("This will test both Milvus and Weaviate across multiple dimensions:")
    print("  • Query Performance")
    print("  • Filtered Search")
    print("  • Hybrid Search (Weaviate)")
    print("  • Feature Comparison")
    print("  • Ease of Use Evaluation")
    print()

    try:
        from benchmark import main as benchmark_main
        benchmark_main()
        return True
    except Exception as e:
        print(f"❌ Error running benchmark: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution flow."""
    print("\n" + "="*70)
    print("  MILVUS vs WEAVIATE - Reinsurance AI POC")
    print("="*70)
    print()
    print("This POC compares Milvus and Weaviate for reinsurance use cases:")
    print("  1. Document/Policy Search")
    print("  2. Claims Similarity")
    print("  3. Knowledge Retrieval")
    print()

    # Step 1: Check Docker
    if not check_docker_containers():
        print("\n❌ Cannot proceed without Docker containers running.")
        print("   Please ensure Docker is installed and running, then execute:")
        print("   docker compose up -d")
        sys.exit(1)

    # Step 2: Generate data
    if not generate_data():
        print("\n❌ Cannot proceed without data.")
        sys.exit(1)

    # Step 3: Run benchmark
    print("\nReady to run benchmarks!")
    if os.environ.get('AUTO_RUN') != '1':
        response = input("Continue? (Y/n): ").strip().lower()
        if response == 'n':
            print("\nBenchmark cancelled.")
            sys.exit(0)
    else:
        print("Auto-run mode: Proceeding with benchmarks...")

    if not run_benchmark():
        print("\n❌ Benchmark failed.")
        sys.exit(1)

    # Success
    print("\n" + "="*70)
    print("  ✓ COMPARISON COMPLETE")
    print("="*70)
    print("\nResults saved to: results/benchmark_results.json")
    print("\nNext steps:")
    print("  • Review the benchmark summary above")
    print("  • Check detailed results in results/benchmark_results.json")
    print("  • Explore the client implementations in scripts/")
    print("  • Modify scripts to test additional scenarios")
    print()


if __name__ == "__main__":
    main()
