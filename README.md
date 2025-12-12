# Vector Database Benchmark POC

A comprehensive benchmarking suite comparing **Milvus 2.5**, **Weaviate**, **PostgreSQL (pgvector)**, and **SQL Server** for multi-modal search (Text + Image) using Dense, Sparse, and Hybrid search strategies.

## 🚀 Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.10+
*   Git

### 2. Setup
```bash
# Clone repository
git clone <repo-url>
cd milvus-weaviate-poc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment (optional - defaults work for local Docker)
cp .env.example .env

# Start Infrastructure (Milvus, Weaviate, PostgreSQL, SQL Server, MinIO)
docker-compose up -d
```

### 3. Run Full Benchmark
```bash
# Generate data, load, benchmark, and report (approx 10-15 mins for 10k docs)
python scripts/generate_data.py --total 10000
python scripts/process_data.py
python scripts/benchmark.py
python scripts/generate_report.py
```

## 📚 Documentation

| Document | Audience | Purpose |
| :--- | :--- | :--- |
| **[USER_GUIDE.md](USER_GUIDE.md)** | **Technical Users** | Step-by-step guide to running benchmarks, persistent data, and reporting. |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | **Architects** | Deep dive into tech stack, infrastructure, and methodology. |
| **[MILVUS_2.5_IMPROVEMENTS.md](MILVUS_2.5_IMPROVEMENTS.md)** | **Developers** | Technical details on new Milvus 2.5 features (Sparse, Grouping). |
| **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)** | **Everyone** | Latest benchmark results summary. |

## 🏗️ Project Structure

```
milvus-weaviate-poc/
├── .env.example            # Environment configuration template
├── data/                   # Generated synthetic data
├── results/                # Benchmark results (JSON)
├── scripts/
│   ├── config.py           # Centralized configuration
│   ├── generate_data.py    # Data generation
│   ├── process_data.py     # Embedding generation
│   ├── benchmark.py        # Main benchmark script
│   ├── milvus_25_hybrid_client.py   # Milvus client
│   ├── weaviate_client.py           # Weaviate client
│   ├── postgresql_client.py         # PostgreSQL client
│   ├── sqlserver_client.py          # SQL Server client
│   └── generate_report.py  # HTML/Markdown reporting
├── docker-compose.yml      # Infrastructure definition
└── requirements.txt        # Python dependencies
```

## ⚡ Key Features Tested

*   **Databases**: Milvus 2.5, Weaviate, PostgreSQL (pgvector), SQL Server
*   **Multi-Modal Data**: PDFs (Text), Word Docs (Text), Images (Visual).
*   **Search Methods**:
    *   **Dense**: Semantic search (Sentence Transformers / CLIP).
    *   **Sparse**: Keyword search (BM25 / Full-Text Search).
    *   **Hybrid**: RRF Fusion of Dense + Sparse.
*   **Scale**: Verified up to 50,000 documents.

## ⚙️ Configuration

The benchmark suite uses a centralized configuration system that supports both local Docker and cloud deployments.

### Local Development (Default)
No configuration needed - defaults work with `docker-compose up -d`.

### Cloud Deployment (Azure, AWS, etc.)
1. Copy the template: `cp .env.example .env`
2. Edit `.env` with your cloud database endpoints:

```bash
# Database Hosts
MILVUS_HOST=your-milvus-server.azure.com
WEAVIATE_HOST=your-weaviate-server.azure.com
POSTGRES_HOST=your-postgres-server.azure.com
SQLSERVER_HOST=your-sqlserver-server.azure.com

# Credentials
POSTGRES_USER=admin
POSTGRES_PASSWORD=your-secure-password
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=your-secure-password
```

### View Current Configuration
```bash
python scripts/config.py
```

## 🛠️ Development

### Persistent Mode (Faster Iteration)
To avoid reloading data every time:
1.  Load data once: `python scripts/load_data_persistent.py`
2.  Run benchmark repeatedly: `python scripts/benchmark.py --use-persistent`

### Check Database Status
```bash
python scripts/check_db_status.py
```

### Clean Up Persistent Data
```bash
python scripts/cleanup_persistent.py
```

## 🤝 Contributing
Please read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design before making changes.
