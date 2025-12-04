# Architecture & Technical Deep Dive

## 1. Technology Stack

### Vector Databases
*   **Milvus 2.5 (Docker)**: High-performance, cloud-native vector database. Used for dense, sparse, and hybrid search.
    *   *Key Features*: HNSW indexing, Sparse vector support (beta in 2.5), Grouping search.
*   **Weaviate (Docker)**: Open-source vector database. Used for comparison.
    *   *Key Features*: Native hybrid search, modular architecture.

### Storage & Infrastructure
*   **MinIO (Docker)**: S3-compatible object storage. Used by Milvus for persistent storage of vector data and logs.
*   **Etcd (Docker)**: Distributed key-value store. Used by Milvus for metadata management and service discovery.
*   **Docker Compose**: Orchestrates the entire stack (Milvus, Weaviate, MinIO, Etcd).

### Machine Learning Models
*   **Text Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
    *   *Dimensions*: 384
    *   *Purpose*: Semantic search on policy text and descriptions.
*   **Image Embeddings**: `openai/clip-vit-base-patch32`
    *   *Dimensions*: 512
    *   *Purpose*: Visual search on damage assessment photos.
*   **Sparse Vectors**: `BM25` (Best Matching 25)
    *   *Purpose*: Keyword-based search, used for hybrid search fusion.

## 2. Infrastructure Architecture

The system runs entirely in Docker containers defined in `docker-compose.yml`.

| Service | Internal Port | Host Port | Purpose |
| :--- | :--- | :--- | :--- |
| **milvus-standalone** | 19530 | 19530 | Main Milvus 2.5 service (gRPC/HTTP) |
| **milvus-standalone** | 9091 | 9095 | Milvus Health Check (Remapped to avoid conflict) |
| **weaviate** | 8080 | 8080 | Weaviate HTTP API |
| **weaviate** | 50051 | 50051 | Weaviate gRPC API |
| **minio** | 9000 | 9000 | S3 API for Milvus storage |
| **minio** | 9001 | 9001 | MinIO Console |
| **etcd** | 2379 | 2379 | Metadata storage |

> **Note**: Milvus 2.4 (legacy comparison) runs on port 19531 and health check 9096 if enabled.

## 3. Data Generation Mechanism

The project uses a sophisticated synthetic data generation pipeline (`scripts/generate_multimodal_data.py`) to create a realistic insurance dataset.

### Document Types
1.  **PDFs (Insurance Policies)**:
    *   Generated using `reportlab`.
    *   Contains structured text: Policy ID, Coverage Limits, Premiums, Legal text.
    *   *Metadata*: Policy Type (Auto, Home, Life), State, Date.
2.  **Word Docs (Claims Reports)**:
    *   Generated using `python-docx`.
    *   Contains narrative text: Incident descriptions, adjuster notes.
    *   *Metadata*: Claim ID, Status, Adjuster Name.
3.  **Images (Damage Assessments)**:
    *   Generated using `Pillow` (synthetic patterns/colors representing damage).
    *   *Metadata*: Damage Type (Collision, Fire, Water), Severity.

### Data Cycling
To simulate large datasets (e.g., 50k documents) from limited seed templates, the generator uses a "cycling" strategy:
*   Base templates are permuted with randomized fields (names, dates, amounts).
*   Unique IDs are guaranteed for every document.
*   Content is varied enough to produce distinct embeddings.

## 4. Embedding & Processing Pipeline

The `scripts/process_data.py` script handles the transformation of raw documents into vectors.

1.  **Text Extraction**:
    *   PDFs: `pdfplumber` extracts text.
    *   Word: `python-docx` extracts paragraphs.
2.  **Text Embedding**:
    *   Text is truncated to 2000 characters (model limit/performance trade-off).
    *   Encoded into 384-dim dense vectors.
    *   BM25 encoder fits on the corpus to generate sparse vectors.
3.  **Image Embedding**:
    *   Images are resized and normalized.
    *   Encoded into 512-dim dense vectors using CLIP.

## 5. Benchmarking Methodology

The `scripts/benchmark.py` script performs a fair, side-by-side comparison.

### Search Types Tested
1.  **Dense Search**: Pure vector similarity (Cosine).
    *   *Milvus*: HNSW Index (`IVF_FLAT` equivalent config).
    *   *Weaviate*: HNSW Index (native).
2.  **Sparse/Keyword Search**: BM25.
    *   *Milvus*: `SPARSE_INVERTED_INDEX` (New in 2.5).
    *   *Weaviate*: Native BM25.
3.  **Hybrid Search**: Combination of Dense + Sparse.
    *   *Milvus*: Weighted RRF (Reciprocal Rank Fusion).
    *   *Weaviate*: Native Hybrid fusion.

### Metrics
*   **Latency**: End-to-end response time (ms). Measured over 10 iterations per query.
*   **Precision@k**: Relevance of top-k results.
*   **NDCG**: Ranking quality.

### Persistence Strategy
*   **Standard Mode**: Creates temporary collections (`phase3_fair_*`), loads data, benchmarks, deletes collections.
*   **Persistent Mode** (`--use-persistent`): Connects to existing pre-loaded collections (`persistent_*`), skips loading/cleanup. Ideal for repeated testing.

## 6. Scalability Considerations

*   **Current Scale**: Verified up to 50,000 documents.
*   **Bottlenecks**:
    *   *Data Loading*: Python client insertion speed is the primary bottleneck.
    *   *Memory*: 50k documents fit comfortably in 8GB RAM.
*   **Production Recommendations**:
    *   Use bulk insert APIs (MinIO/S3 import) for >1M documents.
    *   Deploy Milvus Cluster (vs Standalone) for high availability.
    *   Enable GPU indexing for >10M vectors.
