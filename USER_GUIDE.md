# User Guide: Milvus vs Weaviate Benchmark

This guide provides step-by-step instructions for setting up, running, and analyzing benchmarks between Milvus 2.5 and Weaviate.

## Table of Contents
1.  [Prerequisites & Setup](#1-prerequisites--setup)
2.  [Data Generation](#2-data-generation)
3.  [Running Benchmarks](#3-running-benchmarks)
4.  [Persistent Data Workflow](#4-persistent-data-workflow-recommended)
5.  [Generating Reports](#5-generating-reports)
6.  [Data Cleanup](#6-data-cleanup)
7.  [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites & Setup

### System Requirements
*   **OS**: Linux, macOS, or Windows (WSL2)
*   **RAM**: 8GB minimum (16GB recommended for >50k docs)
*   **Disk**: 10GB free space
*   **Software**: Docker Desktop, Python 3.10+, Git

### Installation

1.  **Clone the Repository**
    ```bash
    git clone <repo-url>
    cd milvus-weaviate-poc
    ```

2.  **Set up Python Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Start Infrastructure**
    ```bash
    docker-compose up -d
    ```
    *   **Milvus 2.5**: Ports `19530` (gRPC), `9091` (Health)
    *   **Weaviate**: Ports `8080` (HTTP), `50051` (gRPC)
    *   **MinIO**: Ports `9000`, `9001`

    > **Verify**: Run `python scripts/check_db_status.py` to confirm services are healthy.

---

## 2. Data Generation

The benchmark uses synthetic multi-modal data (PDFs, Word Docs, Images).

### Generate Raw Data
```bash
# Generate 10,000 documents (default)
python scripts/generate_data.py --total 10000

# Generate 50,000 documents
python scripts/generate_data.py --total 50000
```
*   **Output**: `./data/multimodal/raw/`

### Process Data (Embeddings)
Extracts text and generates embeddings (Dense + Sparse).
```bash
python scripts/process_data.py
```
*   **Output**: `./data/multimodal/processed/` (JSON files)
*   **Models**: `all-MiniLM-L6-v2` (Text), `CLIP` (Images), `BM25` (Sparse)

---

## 3. Running Benchmarks

### Standard Benchmark (Load & Run)
This mode creates temporary collections, loads data, runs tests, and deletes collections.
```bash
python scripts/benchmark.py
```
*   **Pros**: Clean state every time.
*   **Cons**: Slow (reloads data every run).

---

## 4. Persistent Data Workflow (Recommended)

For repeated testing, use persistent collections to skip the data loading step.

### Step 1: Load Data Persistently
Run this **once** to load data into permanent collections (`persistent_*`).
```bash
python scripts/load_data_persistent.py
```

### Step 2: Run Benchmark
Run the benchmark with the `--use-persistent` flag.
```bash
python scripts/benchmark.py --use-persistent
```
*   **Speed**: Starts benchmarking immediately (saves 5-10 mins).
*   **Safety**: Does NOT delete data after running.

---

## 5. Generating Reports

After benchmarking, generate HTML and Markdown reports.

```bash
python scripts/generate_report.py
```

### Outputs
*   **`BENCHMARK_REPORT.html`**: Interactive HTML report with charts.
*   **`BENCHMARK_REPORT.md`**: Markdown summary for GitHub/documentation.

### Understanding Results
*   **Latency**: Lower is better (ms).
*   **Speedup**: How many times faster Milvus is compared to Weaviate (e.g., "2.5x").
*   **Quality**: Precision@5, NDCG@5 (should be 1.0 for both).

---

## 6. Data Cleanup

### Clean Persistent Collections
To remove the `persistent_*` collections from the databases:
```bash
python scripts/cleanup_persistent.py
```

### Full System Reset
To delete all data (including Docker volumes):
```bash
docker-compose down -v
rm -rf data/multimodal
```

---

## 7. Troubleshooting

### Port Conflicts
If Docker fails to start, check if ports are in use.
*   **Milvus Health**: Mapped to `9095` (internal 9091) and `9096` (internal 9094) to avoid conflicts.
*   **Fix**: Edit `docker-compose.yml` if you have other services on these ports.

### "ModuleNotFoundError: No module named 'pymilvus'"
Ensure your virtual environment is active:
```bash
source venv/bin/activate
```

### "RPC error: [search] value [] is illegal"
This happens if BM25 encoder isn't fitted.
*   **Fix**: Use the latest `benchmark.py` which automatically fits BM25 when using `--use-persistent`.

### "Connection refused"
*   Wait 30-60 seconds after `docker-compose up` for services to initialize.
*   Run `docker-compose ps` to check status.
