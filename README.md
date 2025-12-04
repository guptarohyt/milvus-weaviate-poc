# Milvus 2.5 vs Weaviate Benchmark POC

A comprehensive benchmarking suite comparing **Milvus 2.5** and **Weaviate** for multi-modal search (Text + Image) using Dense, Sparse, and Hybrid search strategies.

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

# Start Infrastructure (Milvus, Weaviate, MinIO)
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
├── data/                   # Generated synthetic data
├── results/                # Benchmark results (JSON)
├── scripts/                # Python scripts
│   ├── generate_data.py    # Data generation
│   ├── process_data.py     # Embedding generation
│   ├── benchmark.py        # Main benchmark script
│   └── generate_report.py  # HTML/Markdown reporting
├── docker-compose.yml      # Infrastructure definition
└── requirements.txt        # Python dependencies
```

## ⚡ Key Features Tested

*   **Multi-Modal Data**: PDFs (Text), Word Docs (Text), Images (Visual).
*   **Search Methods**:
    *   **Dense**: Semantic search (Sentence Transformers / CLIP).
    *   **Sparse**: Keyword search (BM25).
    *   **Hybrid**: RRF Fusion of Dense + Sparse.
*   **Scale**: Verified up to 50,000 documents.

## 🛠️ Development

### Persistent Mode (Faster Iteration)
To avoid reloading data every time:
1.  Load data once: `python scripts/load_data_persistent.py`
2.  Run benchmark repeatedly: `python scripts/benchmark.py --use-persistent`

### Environment Variables
Create a `.env` file to customize paths:
```bash
DATA_OUTPUT_DIR=./data/custom_location
```

## 🤝 Contributing
Please read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design before making changes.
