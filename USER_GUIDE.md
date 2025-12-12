# User Guide: Vector Database Benchmark

This guide provides step-by-step instructions for setting up, running, and analyzing benchmarks between Milvus 2.5, Weaviate, PostgreSQL (pgvector), and SQL Server.

## Table of Contents
1.  [Prerequisites & Setup](#1-prerequisites--setup)
2.  [Configuration](#2-configuration)
3.  [Data Generation](#3-data-generation)
4.  [Running Benchmarks](#4-running-benchmarks)
5.  [Persistent Data Workflow](#5-persistent-data-workflow-recommended)
6.  [Generating Reports](#6-generating-reports)
7.  [Data Cleanup](#7-data-cleanup)
8.  [Troubleshooting](#8-troubleshooting)

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
    *   **PostgreSQL**: Port `5432`
    *   **SQL Server**: Port `1433`
    *   **MinIO**: Ports `9000`, `9001`

    > **Verify**: Run `python scripts/check_db_status.py` to confirm services are healthy.

---

## 2. Configuration

The benchmark suite uses a centralized configuration system via environment variables. This allows the same code to run against local Docker containers or cloud-hosted databases.

### Configuration File

All settings are managed through environment variables. A template is provided:

```bash
# Copy the template
cp .env.example .env

# Edit with your settings (optional for local Docker)
nano .env
```

### Available Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MILVUS_HOST` | `localhost` | Milvus server hostname |
| `MILVUS_PORT` | `19530` | Milvus gRPC port |
| `WEAVIATE_HOST` | `localhost` | Weaviate server hostname |
| `WEAVIATE_PORT` | `8080` | Weaviate HTTP port |
| `POSTGRES_HOST` | `localhost` | PostgreSQL server hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | `vectordb` | PostgreSQL database name |
| `SQLSERVER_HOST` | `localhost` | SQL Server hostname |
| `SQLSERVER_PORT` | `1433` | SQL Server port |
| `SQLSERVER_USER` | `sa` | SQL Server username |
| `SQLSERVER_PASSWORD` | `YourStrong@Passw0rd` | SQL Server password |
| `DATA_OUTPUT_DIR` | `./data/multimodal` | Data directory path |

### View Current Configuration

```bash
python scripts/config.py
```

This displays all current settings (passwords hidden by default).

### Cloud Deployment Example

For Azure or AWS deployments, create a `.env` file:

```bash
# Azure Example
MILVUS_HOST=milvus.eastus.azure.com
WEAVIATE_HOST=weaviate.eastus.azure.com
POSTGRES_HOST=mypostgres.postgres.database.azure.com
POSTGRES_USER=admin@mypostgres
POSTGRES_PASSWORD=SecurePassword123!
SQLSERVER_HOST=mysqlserver.database.windows.net
SQLSERVER_USER=sqladmin
SQLSERVER_PASSWORD=SecurePassword123!
```

---

## 3. Data Generation

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

## 4. Running Benchmarks

### Standard Benchmark (Load & Run)
This mode creates temporary collections, loads data, runs tests, and deletes collections.
```bash
python scripts/benchmark.py
```
*   **Pros**: Clean state every time.
*   **Cons**: Slow (reloads data every run).

### Skip Specific Databases
```bash
# Skip SQL Server benchmarks
python scripts/benchmark.py --skip-sqlserver

# Skip PostgreSQL benchmarks
python scripts/benchmark.py --skip-postgresql
```

---

## 5. Persistent Data Workflow (Recommended)

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

## 6. Generating Reports

After benchmarking, generate HTML and Markdown reports.

```bash
python scripts/generate_report.py
```

### Outputs
*   **`BENCHMARK_REPORT.html`**: Interactive HTML report with charts.
*   **`BENCHMARK_REPORT.md`**: Markdown summary for GitHub/documentation.

### Understanding Results
*   **Latency**: Lower is better (ms).
*   **Speedup**: How many times faster Milvus is compared to others (e.g., "2.5x").
*   **Quality**: Precision@5, NDCG@5 (should be ~1.0 for all databases).

---

## 7. Data Cleanup

### Clean Persistent Collections
To remove the `persistent_*` collections from all four databases:
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

## 8. Troubleshooting

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
*   Verify configuration: `python scripts/config.py`

### SQL Server ODBC Driver Issues
If SQL Server connection fails:
*   Ensure ODBC Driver 18 is installed
*   Check the driver name in `.env`: `SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server`
*   For older drivers: `SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server`

### PostgreSQL pgvector Extension
If PostgreSQL vector operations fail:
*   Ensure pgvector extension is enabled: The client auto-enables it on connect
*   Check PostgreSQL version supports pgvector (v14+)
