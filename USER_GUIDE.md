# User Guide: Multi-Modal Vector Database Benchmark

## 1. Objective

This benchmark compares the performance and quality of two vector database systems:
- **Milvus 2.5** (with sparse vector support for hybrid search)
- **Weaviate 1.27.5** (with built-in hybrid search)

The benchmark tests three types of search operations across multi-modal data:
- **Dense (Semantic) Search**: Vector similarity using embeddings
- **Sparse/Keyword (BM25) Search**: Traditional keyword-based retrieval
- **Hybrid Search**: Combination of dense and sparse using Reciprocal Rank Fusion (RRF)

**Document Types Tested:**
- PDF insurance policies
- Word documents (claims investigation reports and underwriting guidelines)
- Images (damage assessment photos)

**Metrics Measured:**
- Query latency (milliseconds)
- Search quality (Precision@5, NDCG@5, MRR)

---

## 2. Running Infrastructure on Docker

### Prerequisites
- Docker and Docker Compose installed
- At least 8GB RAM available for Docker
- At least 20GB free disk space

### Services Included

The `docker-compose.yml` file runs the following services:

**Milvus 2.5 (Primary Benchmark Target):**
- `etcd` - Metadata storage (port: none exposed)
- `minio` - Object storage (ports: 9000, 9001)
- `milvus` - Milvus 2.5.0 standalone (ports: 19530, 9091)
- `attu` - Milvus web UI (port: 8000)

**Milvus 2.4 (Optional Comparison):**
- `etcd-24` - Metadata storage for Milvus 2.4
- `minio-24` - Object storage for Milvus 2.4 (ports: 9002, 9003)
- `milvus-24` - Milvus 2.4.0 standalone (ports: 19531, 9094)

**Weaviate:**
- `weaviate` - Weaviate 1.27.5 (ports: 8080, 50051)

### Start All Services

```bash
docker-compose up -d
```

This command:
- Downloads all required Docker images (if not already present)
- Creates persistent volumes for data storage
- Starts all containers in detached mode

### Verify Services Are Running

```bash
docker-compose ps
```

All services should show status as "Up" or "Up (healthy)".

### Check Service Health

**Milvus 2.5:**
```bash
curl http://localhost:9091/healthz
```

**Weaviate:**
```bash
curl http://localhost:8080/v1/.well-known/ready
```

### Access Web Interfaces

- **Attu (Milvus UI)**: http://localhost:8000
- **MinIO Console**: http://localhost:9001 (credentials: minioadmin/minioadmin)

### Stop All Services

```bash
docker-compose down
```

To completely remove all data (WARNING: destructive):
```bash
docker-compose down -v
```

---

## 3. Generating Data

### What Data Generation Does

The `generate_data.py` script creates synthetic multi-modal documents using Python libraries (NO LLMs):

**PDF Generation (using `reportlab`):**
- Creates insurance policy documents
- Includes policy details, coverage information, and premium calculations
- Adds tables and structured content
- File size: ~15-20KB per PDF

**Word Document Generation (using `python-docx`):**
- Creates claims investigation reports (60%)
- Creates underwriting guidelines (40%)
- Includes formatted text, headings, and tables
- File size: ~10-15KB per document

**Image Generation (using `Pillow/PIL`):**
- Creates damage assessment images
- Shows simulated damage types (water, fire, collision, etc.)
- Adds labels and severity indicators
- File size: ~25-30KB per image
- Image dimensions: 800x600 pixels

### Generation Command Syntax

**Script Location:** `scripts/generate_data.py`

**Method 1: Specify Exact Counts**
```bash
cd scripts
python generate_data.py --pdfs <count> --word <count> --images <count> [--skip-confirmation]
```

**Method 2: Specify Total with Ratios**
```bash
python generate_data.py --total <count> [--pdf-ratio 0.5] [--word-ratio 0.3] [--image-ratio 0.2] [--skip-confirmation]
```

### Generation Examples

**Default 10K dataset (5K PDFs, 3K Word, 2K images):**
```bash
python generate_data.py
```

**Custom 50K dataset:**
```bash
python generate_data.py --pdfs 25000 --word 15000 --images 10000 --skip-confirmation
```

**100K dataset with same ratios:**
```bash
python generate_data.py --total 100000 --skip-confirmation
```

**Only PDFs (for testing):**
```bash
python generate_data.py --pdfs 50000 --word 0 --images 0 --skip-confirmation
```

**Custom ratios (60% PDF, 30% Word, 10% Images):**
```bash
python generate_data.py --total 50000 --pdf-ratio 0.6 --word-ratio 0.3 --image-ratio 0.1 --skip-confirmation
```

### Output Location

Generated files are saved to:
```
scripts/data/multimodal/
├── pdfs/          # PDF files: policy_001.pdf, policy_002.pdf, ...
├── word/          # Word files: claim_001.docx, underwriting_001.docx, ...
└── images/        # Image files: damage_001.png, damage_002.png, ...
```

### Parameters Explained

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--pdfs` | Exact number of PDF documents to generate | - |
| `--word` | Exact number of Word documents to generate | - |
| `--images` | Exact number of images to generate | - |
| `--total` | Total documents to generate (used with ratios) | 10000 |
| `--pdf-ratio` | Percentage of total as PDFs (0.0-1.0) | 0.5 |
| `--word-ratio` | Percentage of total as Word docs (0.0-1.0) | 0.3 |
| `--image-ratio` | Percentage of total as images (0.0-1.0) | 0.2 |
| `--skip-confirmation` | Skip the "Proceed?" prompt | False |

### Generation Time Estimates

Based on typical hardware:
- **10K documents**: ~20-30 minutes
- **50K documents**: ~2-3 hours
- **100K documents**: ~5-6 hours

---

## 4. Processing Data

### What Processing Does

The `process_data.py` script performs the following operations:

**For PDFs:**
1. Extract text content from all pages using `pdfplumber`
2. Extract tables and convert to structured text
3. Generate dense embeddings (384 dimensions) using `sentence-transformers` (all-MiniLM-L6-v2)
4. Store metadata: filename, text, number of pages, policy details

**For Word Documents:**
1. Extract paragraphs and formatted text using `python-docx`
2. Extract tables and convert to structured text
3. Generate dense embeddings (384 dimensions) using `sentence-transformers` (all-MiniLM-L6-v2)
4. Store metadata: filename, text, document type, claim/policy IDs

**For Images:**
1. Load image files using `PIL/Pillow`
2. Generate image embeddings (512 dimensions) using `CLIP` (openai/clip-vit-base-patch32)
3. Generate text embeddings (384 dimensions) from image descriptions
4. Store metadata: filename, description, damage type, severity, claim ID

### Processing Command

```bash
cd scripts
python process_data.py
```

**Note:** Processing requires the generated data to exist in `scripts/data/multimodal/`.

### What Happens During Processing

1. **Model Loading**: Downloads and loads embedding models (one-time download, cached afterwards):
   - `all-MiniLM-L6-v2` (~90MB) for text embeddings
   - `openai/clip-vit-base-patch32` (~600MB) for image embeddings

2. **Text Extraction**:
   - Reads each PDF and Word document
   - Extracts all text content and tables
   - Handles encoding and formatting issues

3. **Embedding Generation**:
   - Processes text through transformer models
   - Creates vector representations of content
   - Uses GPU if available, otherwise CPU
   - **Document-level embeddings** (one embedding per document, NOT chunked)
   - For PDFs/Word: Uses first 2000 characters for embedding generation
   - For Images: Entire image gets one 512-dim embedding

4. **Data Serialization**:
   - Saves processed data with embeddings to JSON files
   - Stores first 1000 chars in `text` field, full content in `full_text` field
   - Compresses and optimizes storage

### Important: No Chunking

**This benchmark uses document-level embeddings, NOT chunk-level embeddings.**

- Each document (PDF or Word) = 1 embedding vector (384 dimensions)
- Each image = 1 embedding vector (512 dimensions)
- Long documents: Only first 2000 characters used for embedding
- No sliding windows, no overlapping chunks, no chunk retrieval

**Implication:** For very long documents, the embedding only represents the first 2000 characters of content. This is a deliberate design choice to keep the benchmark simple and focused on database performance rather than retrieval strategies.

### Output Location

Processed files are saved to:
```
data/multimodal/processed/
├── pdfs_processed.json         # ~380MB for 25K PDFs
├── word_docs_processed.json    # ~190MB for 15K Word docs
└── images_processed.json       # ~245MB for 10K images
```

### Output Format

Each JSON file contains an array of objects with the following structure:

**PDFs and Word documents:**
```json
{
  "id": "unique_id",
  "filename": "policy_001.pdf",
  "text": "Full extracted text content...",
  "type": "auto",
  "policy_id": "POL-123456",
  "embedding": [0.123, -0.456, ...],  // 384 dimensions
  "embedding_dim": 384
}
```

**Images:**
```json
{
  "id": "unique_id",
  "filename": "damage_001.png",
  "type": "water_damage",
  "damage_type": "water",
  "severity": "moderate",
  "claim_id": "CLM-123456",
  "description": "Water damage to ceiling and walls",
  "image_embedding": [0.789, -0.234, ...],  // 512 dimensions
  "text_embedding": [0.345, -0.678, ...],   // 384 dimensions
  "image_embedding_dim": 512,
  "text_embedding_dim": 384
}
```

### Processing Time Estimates

Based on typical hardware (with GPU):
- **10K documents**: ~15-20 minutes
- **50K documents**: ~1.5-2 hours
- **100K documents**: ~3-4 hours

**Without GPU (CPU only):** Processing takes approximately 3-5x longer.

### Outcome

After processing completes, you have:
- ✅ All text extracted from documents
- ✅ Vector embeddings generated for semantic search
- ✅ Metadata preserved and structured
- ✅ Data ready to load into vector databases

---

## 5. Loading Data

### Loading Options

There are TWO ways to load data into the databases:

#### Option A: Load During Benchmark (Temporary)

**Script:** `scripts/benchmark.py`

**What it does:**
1. Loads all processed documents into BOTH Milvus 2.5 and Weaviate
2. Creates collections/classes with proper schema and indexes
3. Runs all benchmark tests
4. **Automatically deletes all data** after testing (cleanup)

**When to use:** When running the actual performance benchmark.

**Command:**
```bash
cd scripts
python benchmark.py
```

**Result:** You get benchmark results, but data is NOT persistent.

#### Option B: Load Persistently (No Cleanup)

**Script:** `scripts/load_data_persistent.py`

**What it does:**
1. Loads all processed documents into BOTH Milvus 2.5 and Weaviate
2. Creates persistent collections/classes with proper schema and indexes
3. Does NOT run any tests
4. **Leaves data in databases** - no cleanup

**When to use:** When you want to browse/explore the documents in the databases.

**Command:**
```bash
cd scripts
python load_data_persistent.py
```

**Result:** Data persists in databases for exploration.

### What Happens During Loading

**Milvus 2.5:**
1. Creates hybrid collections with:
   - Dense vector field (384 or 512 dimensions)
   - Sparse vector field (for BM25)
   - Metadata fields (filename, text, policy_id, etc.)
2. Creates indexes:
   - IVF_FLAT for dense vectors
   - SPARSE_INVERTED_INDEX for sparse vectors
3. Inserts documents in batches of 5000 (to avoid gRPC limits)
4. Loads collections into memory

**Weaviate:**
1. Creates classes with schema:
   - Vector field for dense embeddings
   - Text properties with BM25 enabled
   - Metadata properties
2. Configures hybrid search (automatic)
3. Inserts all documents using batch API (batch size: 1000)

### Collection/Class Names

**Temporary (benchmark.py):**
- Milvus: `phase3_fair_pdfs`, `phase3_fair_word`, `phase3_fair_images`
- Weaviate: `Phase3FairPDFs`, `Phase3FairWordDocs`, `Phase3FairImages`

**Persistent (load_data_persistent.py):**
- Milvus: `persistent_pdfs`, `persistent_word`, `persistent_images`
- Weaviate: `PersistentPDFs`, `PersistentWordDocs`, `PersistentImages`

### Verify Data is Loaded

**Check Milvus:**
```bash
python -c "from pymilvus import *; connections.connect(); print('PDFs:', Collection('persistent_pdfs').num_entities)"
```

**Check Weaviate:**
```bash
python -c "import weaviate; c = weaviate.connect_to_local(); print('PDFs:', c.collections.get('PersistentPDFs').aggregate.over_all(total_count=True).total_count); c.close()"
```

### Browse Data Interactively

```bash
python scripts/database_browser.py
```

Then select:
- Option 3 to browse Milvus collections
- Option 4 to browse Weaviate collections

### Loading Time Estimates

- **10K documents**: ~5-10 minutes
- **50K documents**: ~15-20 minutes
- **100K documents**: ~30-40 minutes

### Clean Up Persistent Data

To remove persistent data from databases:

```bash
cd scripts
python cleanup_persistent.py
```

This removes ONLY the persistent collections, leaving temporary benchmark data untouched.

---

## 6. Benchmarking Data

### What Benchmarking Does

The `benchmark.py` script measures query performance across different search types:

**Performance Tests:**
- Measures average query latency (milliseconds)
- Tests 10 different queries per document type
- Records min, max, and standard deviation
- Compares dense, sparse, and hybrid search

**Quality Tests:**
- Run separately via `evaluate_quality.py`
- Measures Precision@5, Recall@5, NDCG@5, and MRR
- Uses synthetic ground truth based on document metadata
- Tests first 10 documents as queries

### Benchmark Command

```bash
cd scripts
python benchmark.py
```

### What Gets Tested

**Search Types:**

1. **Dense (Semantic) Search:**
   - Uses vector similarity (cosine distance)
   - Finds semantically similar content
   - Tests: PDF, Word, Image collections

2. **Sparse/Keyword (BM25) Search:**
   - Uses traditional keyword matching
   - Scores based on term frequency
   - Tests: PDF, Word collections (not images)

3. **Hybrid Search:**
   - Combines dense + sparse results
   - Uses Reciprocal Rank Fusion (RRF)
   - Tests: PDF, Word collections

**Test Queries:**

PDFs (10 queries):
- "comprehensive auto insurance coverage"
- "liability coverage limits"
- "collision damage waiver"
- etc.

Word Documents (10 queries):
- "claim investigation findings"
- "underwriting guidelines"
- "risk assessment criteria"
- etc.

Images (10 queries):
- "water damage to ceiling"
- "fire damage to structure"
- "collision damage to vehicle"
- etc.

### Benchmark Process

1. **Setup Phase (~5 min):**
   - Loads data into both Milvus and Weaviate
   - Creates collections and indexes
   - Warms up connections

2. **Milvus Testing (~10 min):**
   - Runs dense search queries
   - Runs sparse search queries
   - Runs hybrid search queries
   - Records latencies

3. **Weaviate Testing (~10 min):**
   - Runs dense search queries
   - Runs keyword search queries
   - Runs hybrid search queries
   - Records latencies

4. **Cleanup:**
   - Drops all collections
   - Saves results to JSON

### Output Files

**Benchmark results:**
```
results/phase3_fair_benchmark_results.json
```

Contains:
```json
{
  "metadata": {
    "dataset_size": {"pdfs": 25000, "word_docs": 15000, "images": 10000},
    "timestamp": "2025-11-17T..."
  },
  "milvus_25": {
    "pdf_dense": {"avg": 1.22, "std": 0.15, "min": 0.98, "max": 1.45},
    "pdf_sparse": {"avg": 2.76, ...},
    ...
  },
  "weaviate": {
    "pdf_dense": {"avg": 3.71, ...},
    ...
  }
}
```

**Quality results:**
```
results/phase3_quality_results.json
```

Contains precision, NDCG, and MRR scores for each search type.

### Generate HTML Report

After benchmarking, generate a beautiful HTML report:

```bash
cd scripts
python generate_50k_report.py
```

This creates `BENCHMARK_50K_REPORT.html` in the root directory with:
- Executive summary with key metrics
- Performance comparison tables
- Quality metrics
- Visualizations

### Benchmark Time Estimates

- **10K documents**: ~25-30 minutes total
- **50K documents**: ~30-40 minutes total
- **100K documents**: ~45-60 minutes total

### Interpreting Results

**Lower latency = Better performance**
- Sub-millisecond: Excellent
- 1-5 ms: Good
- 5-10 ms: Acceptable
- 10+ ms: Needs optimization

**Quality scores (0.0 - 1.0):**
- 1.0: Perfect
- 0.8+: Excellent
- 0.6-0.8: Good
- <0.6: Needs improvement

### Quality Metrics Explained

**How Quality is Measured:**

The `evaluate_quality.py` script uses **synthetic ground truth** to measure retrieval quality. Since the data is generated programmatically, relevance is determined automatically based on document metadata rather than human judgments.

**Ground Truth Generation:**

For each test query (first 10 documents are used as queries):

**PDFs:**
- Documents are assigned **graded relevance scores** (0-3) based on policy type similarity:
  - **3** = Perfect match (the document itself, or same claim ID)
  - **2** = Highly relevant (same policy type: auto, property, casualty, etc.)
  - **1** = Somewhat relevant (different policy type)
  - **0** = Not relevant

**Images:**
- Similar graded relevance based on:
  - Same damage type (water, fire, collision, etc.)
  - Same claim ID
  - Same policy ID

**Relevance Threshold:** A document is considered "relevant" for Precision/Recall if its score is **≥ 2**.

**Metrics Calculated:**

1. **Precision@5**
   - Formula: `(# of relevant docs in top 5 results) / 5`
   - Example: If 3 out of top 5 results have score ≥ 2, Precision@5 = 0.60
   - Measures: Accuracy of top results

2. **Recall@5**
   - Formula: `(# of relevant docs in top 5) / (total # of relevant docs in collection)`
   - Example: If 3 relevant docs found in top 5, but 20 total relevant docs exist, Recall@5 = 0.15
   - Measures: Coverage of relevant documents

3. **NDCG@5** (Normalized Discounted Cumulative Gain)
   - Accounts for both relevance and ranking position
   - Higher scores for more relevant docs ranked higher
   - Uses graded relevance (0-3 scale)
   - Penalizes relevant docs appearing lower in results

4. **MRR** (Mean Reciprocal Rank)
   - Formula: `1 / (position of first relevant document)`
   - Example: If first relevant doc is at position 2, MRR = 0.50
   - Measures: How quickly users find a relevant result

**Test Setup:**
- **10 test queries** per document type (PDFs, Images)
- Retrieves **top 100 results** per query for evaluation
- Evaluates **top 5** for Precision/Recall/NDCG
- All metrics averaged across 10 queries

**Command to run quality evaluation:**
```bash
cd scripts
python evaluate_quality.py
```

Output saved to: `results/phase3_quality_results.json`

---

## Complete Workflow Example

### Benchmark 50K Documents

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Wait for services to be healthy (~2 minutes)
sleep 120

# 3. Generate 50K documents
cd scripts
python generate_data.py --pdfs 25000 --word 15000 --images 10000 --skip-confirmation

# 4. Process documents (creates embeddings)
python process_data.py

# 5. Run benchmark
python benchmark.py

# 6. Evaluate quality (optional)
python evaluate_quality.py

# 7. Generate HTML report
python generate_50k_report.py

# 8. View report
open ../BENCHMARK_50K_REPORT.html
```

### Explore Data (Without Benchmark)

```bash
# Load data persistently
cd scripts
python load_data_persistent.py

# Browse data
python database_browser.py

# Clean up when done
python cleanup_persistent.py
```

---

## Troubleshooting

### Docker Services Won't Start

```bash
# Check logs
docker-compose logs milvus
docker-compose logs weaviate

# Restart services
docker-compose restart
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a --volumes

# Remove old data
rm -rf scripts/data/multimodal/*
rm -rf data/multimodal/processed/*
```

### Processing is Slow

- Check if GPU is being used: `nvidia-smi` (if NVIDIA GPU)
- Close other applications to free RAM
- Process smaller batches (split data)

### Benchmark Crashes

- Ensure enough RAM (8GB+ recommended)
- Check Docker has enough resources
- Verify all services are healthy

---

## Additional Resources

- **COMPLETE_50K_PIPELINE.md**: Detailed pipeline documentation
- **DATA_GENERATION_EXPLAINED.md**: How data generation works
- **BENCHMARK_50K_REPORT.html**: Example benchmark report
