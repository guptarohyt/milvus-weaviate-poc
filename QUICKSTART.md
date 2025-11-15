# Phase 2 Quick Start Guide - Multi-Modal Vector Search

This guide will help you get the Phase 2 multi-modal POC up and running quickly.

## What You'll Build

A complete multi-modal vector search system that handles:
- 📄 100 PDF documents (insurance policies with tables/charts)
- 📝 50 Word documents (claims reports and guidelines)
- 🖼️ 200 images (damage assessment photos)

## Architecture Overview

This POC uses a **hybrid approach**:
- **Vector Databases** (Milvus & Weaviate): Run in Docker containers
- **Python Scripts** (data generation, processing, benchmarking): Run on your host machine
- **CLIP Model**: Downloads automatically (~600MB) for image embeddings

This approach allows easy development and debugging while keeping the databases isolated in containers.

---

## Prerequisites

- Docker and Docker Compose installed
- **Python 3.8 or higher** (for running scripts on your machine)
- **8GB+ RAM recommended** (CLIP model + databases)
- **2GB free disk space** (for models + generated data)
- Stable internet connection (for downloading CLIP model on first run)

---

## Step 1: Create Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Install Phase 2 dependencies
pip install -r requirements.txt
```

### What Gets Installed:

**Phase 1 dependencies**:
- pymilvus, weaviate-client - Database clients
- sentence-transformers - Text embeddings

**Phase 2 additions**:
- `reportlab` - PDF generation
- `pdfplumber` - PDF text extraction
- `python-docx` - Word document handling
- `Pillow` - Image generation and manipulation
- `transformers` + `torch` - CLIP model for image embeddings
- `matplotlib` + `seaborn` - Chart generation

**Why virtual environment?** Isolates dependencies from your system Python and prevents version conflicts.

**Expected install time**: 2-3 minutes

---

## Step 2: Start Vector Databases (Docker)

```bash
docker compose up -d
```

This starts:
- **Milvus** (port 19530) with supporting services (etcd, MinIO)
- **Weaviate** (port 8080)
- **Attu UI** (port 8000) - Optional Milvus web interface

Wait ~30 seconds for services to be ready.

Check container status:
```bash
docker compose ps
```

All services should show as "Up" (some may show "unhealthy" initially, give them time).

---

## Step 3: Generate Multi-Modal Data

**Important:** Make sure your virtual environment is activated!

```bash
# If not already activated:
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

cd scripts
python generate_multimodal_data.py --type all
```

### What This Does:

1. **Loads Phase 1 data** (policies, claims, knowledge base)
2. **Generates 100 PDFs**:
   - Policy documents with professional formatting
   - Tables with coverage limits and premiums
   - Charts showing loss ratios
   - ~5MB total
3. **Generates 50 Word documents**:
   - 30 Claims Investigation Reports
   - 20 Underwriting Guidelines
   - Professional formatting with headers, tables, bullet points
   - ~1.5MB total
4. **Generates 200 images**:
   - Damage assessment photos (fire, flood, hurricane, wind, earthquake, structural)
   - Synthetic but realistic appearance
   - Metadata: damage type, severity (0.0-1.0), location
   - ~2MB total

**Output directory**: `data/multimodal/`
```
data/multimodal/
├── pdfs/         # 100 PDF files
├── word/         # 50 Word documents
├── images/       # 200 PNG images
├── csv/          # (empty for now)
└── audio/        # (empty for now)
```

**Expected runtime**: 30-60 seconds

**Tip**: You can generate specific types only:
```bash
python generate_multimodal_data.py --type pdfs    # PDFs only
python generate_multimodal_data.py --type word    # Word docs only
python generate_multimodal_data.py --type images  # Images only
```

---

## Step 4: Process Data & Generate Embeddings

```bash
python process_multimodal_data.py
```

### What This Does:

1. **Loads embedding models**:
   - Sentence Transformers (all-MiniLM-L6-v2) for text - ~90MB
   - CLIP (openai/clip-vit-base-patch32) for images - ~600MB
   - Models download automatically on first run

2. **Processes PDFs**:
   - Extracts text from all pages using pdfplumber
   - Extracts tables
   - Generates 384-dim text embeddings
   - Saves to `data/multimodal/processed/pdfs_processed.json`

3. **Processes Word documents**:
   - Extracts text content
   - Generates 384-dim text embeddings
   - Saves to `data/multimodal/processed/word_docs_processed.json`

4. **Processes Images**:
   - Generates 512-dim visual embeddings using CLIP
   - Generates 384-dim text embeddings for descriptions
   - Dual embeddings enable both image-to-image and text-to-image search
   - Saves to `data/multimodal/processed/images_processed.json`

**Output**: Processed JSON files with embeddings in `data/multimodal/processed/`

**Expected runtime**:
- First run: 5-8 minutes (includes CLIP model download)
- Subsequent runs: 2-3 minutes

**Progress indicators**: You'll see progress bars for each stage.

---

## Step 5: Load Data into Milvus

The processing script automatically offers to load data. If you skipped it, run:

```bash
python milvus_multimodal_client.py
```

### What This Does:

1. **Connects to Milvus** at localhost:19530
2. **Creates 3 collections**:
   - `pdfs_phase2` - 384-dim vectors for PDF text
   - `word_docs_phase2` - 384-dim vectors for Word text
   - `images_phase2` - 512-dim vectors for CLIP visual embeddings
3. **Loads processed data**:
   - Inserts documents with metadata
   - Builds IVF_FLAT indexes
   - Loads collections into memory
4. **Verifies** collection counts

**Expected runtime**: 15-20 seconds

**Output**:
```
✓ Connected to Milvus at localhost:19530
✓ Created collection: pdfs_phase2
✓ Loaded 100 PDF documents
✓ Created collection: word_docs_phase2
✓ Loaded 50 Word documents
✓ Created collection: images_phase2
✓ Loaded 200 images
✓ All collections ready!
```

---

## Step 6: Load Data into Weaviate

```bash
python weaviate_multimodal_client.py
```

### What This Does:

1. **Connects to Weaviate** at localhost:8080
2. **Creates 3 collections**:
   - `PDFsPhase2` - 384-dim vectors for PDF text
   - `WordDocsPhase2` - 384-dim vectors for Word text
   - `ImagesPhase2` - 512-dim vectors for CLIP visual embeddings
3. **Loads processed data**:
   - Inserts documents with metadata
   - HNSW index builds automatically during insert
4. **Verifies** collection counts

**Expected runtime**: 10-15 seconds (faster than Milvus!)

**Output**:
```
✓ Connected to Weaviate at localhost:8080
✓ Created collection: PDFsPhase2
✓ Loaded 100 PDF documents in 3.2s
✓ Created collection: WordDocsPhase2
✓ Loaded 50 Word documents in 1.8s
✓ Created collection: ImagesPhase2
✓ Loaded 200 images in 4.5s
✓ All collections ready!
```

---

## Step 7: Run Phase 2 Benchmarks

```bash
python benchmark_multimodal.py
```

### What This Does:

Runs 4 comprehensive benchmark categories:

1. **PDF Search** (10 queries)
   - "property damage insurance policy"
   - "catastrophe reinsurance treaty"
   - "coverage limits and deductibles"
   - etc.

2. **Word Document Search** (10 queries)
   - "claims investigation report"
   - "underwriting risk assessment"
   - "settlement procedures"
   - etc.

3. **Image-to-Image Similarity** (10 queries)
   - Find visually similar damage photos
   - Tests CLIP visual embeddings

4. **Text-to-Image Search** (10 queries)
   - "severe storm damage photos"
   - "property damage inspection"
   - "catastrophic loss images"
   - etc.

5. **Filtered Image Search** (5 queries, Weaviate only)
   - Combines vector search with metadata filters
   - Example: Find "flood damage" with severity >= 0.7

**Expected runtime**: 1-2 minutes

**Output**:
- Real-time progress for each query
- Summary statistics
- Results saved to `results/phase2_benchmark_results.json`

---

## Step 8: View Results

```bash
# Pretty-print results
cat ../results/phase2_benchmark_results.json | python -m json.tool

# Or use Python to see summary
python -c "
import json
with open('../results/phase2_benchmark_results.json') as f:
    results = json.load(f)

print('PHASE 2 BENCHMARK RESULTS\n')
for category, data in results['comparison'].items():
    print(f'{category.replace(\"_\", \" \").title()}:')
    print(f'  Winner: {data[\"faster\"]} ({data[\"speedup_percent\"]:.1f}% faster)')
    print(f'  Milvus: {data[\"milvus_avg_ms\"]:.2f}ms')
    print(f'  Weaviate: {data[\"weaviate_avg_ms\"]:.2f}ms\n')
"
```

### Expected Results:

| Test Category | Milvus | Weaviate | Winner | Advantage |
|--------------|--------|----------|--------|-----------|
| PDF Search | ~2.9ms | ~3.2ms | Milvus | 7% faster |
| Word Search | ~3.2ms | ~2.8ms | Weaviate | 13% faster |
| Image-to-Image | ~1.0ms | ~1.7ms | Milvus | 38% faster |
| Text-to-Image | ~2.7ms | ~2.9ms | Milvus | 7% faster |

**Winner: Milvus (3 out of 4 categories)**

**Key Insight**: Milvus significantly outperforms on image search with CLIP embeddings!

---

## Alternative: Run Everything at Once

If you want to run all steps automatically:

```bash
cd scripts
source ../venv/bin/activate

# Generate, process, load, and benchmark
python generate_multimodal_data.py --type all && \
python process_multimodal_data.py && \
python benchmark_multimodal.py
```

**Total runtime**: 15-20 minutes (includes CLIP download on first run)

---

## Understanding What's Happening

### During PDF Generation
```
Generating PDFs...  ━━━━━━━━━━━━━━━━━━ 100/100
  ├─ Creating policy documents with ReportLab
  ├─ Adding coverage tables
  ├─ Embedding loss ratio charts (matplotlib)
  └─ Saving to data/multimodal/pdfs/
```

### During CLIP Model Load (First Time)
```
Downloading CLIP model...
  ├─ openai/clip-vit-base-patch32
  ├─ Size: ~600MB
  ├─ Location: ~/.cache/huggingface/
  └─ One-time download, cached for future use
```

### During Image Processing
```
Processing images with CLIP...  ━━━━━━━━━━━━━━━━━━ 200/200
  ├─ Loading image with PIL
  ├─ Generating 512-dim visual embedding (CLIP)
  ├─ Generating 384-dim text embedding (description)
  └─ Dual embeddings enable cross-modal search
```

### During Milvus Index Building
```
Building IVF_FLAT index...
  ├─ Clustering 200 vectors into 16 groups
  ├─ Creating inverted file structure
  ├─ Loading to memory for fast search
  └─ Index build time: ~5s
```

### During Weaviate Insert
```
Inserting to Weaviate...
  ├─ Batch insert (100 documents/batch)
  ├─ HNSW index builds incrementally
  ├─ No separate index build phase
  └─ Insert time: ~2s (faster than Milvus!)
```

---

## Key Metrics to Watch

When running the comparison, watch for these numbers:

### Query Performance
```
Target: < 5ms per query

PDF Search:
  Milvus:   2.9ms   ✅ Excellent
  Weaviate: 3.2ms   ✅ Excellent

Image Search:
  Milvus:   1.0ms   ✅ Outstanding (38% faster!)
  Weaviate: 1.7ms   ✅ Good
```

### Setup Time
```
Target: < 60s for 350 documents

Milvus:
  - Collection creation: 1s
  - Data insertion: 8s
  - Index building: 12s
  - Total: ~21s

Weaviate:
  - Collection creation: 0.3s
  - Data insertion + indexing: 9s
  - Total: ~9.3s (2x faster setup!)
```

### Memory Usage
```
Target: < 1GB for 350 documents

Milvus:   ~300MB  ✅ Good
Weaviate: ~250MB  ✅ Better

(CLIP model uses additional ~600MB in RAM)
```

---

## Troubleshooting

### "Connection refused" Error
```bash
# Check if containers are running
docker compose ps

# If not running, start them
docker compose up -d

# Wait 30 seconds
sleep 30

# Try again
python milvus_multimodal_client.py
```

### "ModuleNotFoundError: No module named 'torch'"
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Out of memory" During CLIP Loading
```bash
# CLIP model requires ~2GB RAM (600MB model + 1.4GB processing)
# Close other applications
# Or reduce batch size in process_multimodal_data.py:

# Edit line ~150:
batch_size = 16  # Reduce from 32 to 16
```

### Slow Image Processing
```bash
# Check if CUDA is available
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# If False but you have GPU, install CUDA-enabled PyTorch
# See: https://pytorch.org/get-started/locally/

# Otherwise, reduce number of images:
python generate_multimodal_data.py --num-images 50  # Instead of 200
```

### PDF Generation Fails
```bash
# Check permissions
ls -la data/multimodal/

# Create directory if missing
mkdir -p data/multimodal/{pdfs,word,images,processed}

# Check reportlab installation
pip install --upgrade reportlab pdfplumber
```

### "Data not found" Error
```bash
# Make sure you generated data first
cd scripts
python generate_multimodal_data.py --type all

# Then process it
python process_multimodal_data.py
```

---

## Viewing Your Data

### Browse Collections Interactively
```bash
# Milvus browser (text-based UI)
python database_browser.py

# Weaviate status check
python check_db_status.py
```

### Visualize Embeddings
```bash
# Quick visualization demo
python quick_viz_demo.py

# Full visualization guide
python visualize_embeddings.py
```

### Access Milvus Web UI
Open browser to: `http://localhost:8000`
- Attu web interface for Milvus
- Browse collections, run queries visually
- View collection statistics

---

## Example Queries

After loading data, you can test individual queries:

### PDF Search
```python
from milvus_multimodal_client import MilvusMultiModalClient
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
client = MilvusMultiModalClient(load_existing=True)

query = "property damage insurance policy"
embedding = model.encode(query).tolist()

results, time = client.search_pdfs(embedding, top_k=5)
print(f"Found {len(results)} results in {time:.2f}ms")
```

### Image Search (Text-to-Image)
```python
query = "severe flood damage"
embedding = model.encode(query).tolist()

results, time = client.search_images_by_text(embedding, top_k=5)
for result in results:
    print(f"  - {result.entity.get('filename')}")
    print(f"    Type: {result.entity.get('damage_type')}")
    print(f"    Severity: {result.entity.get('severity'):.2f}")
```

---

## Cleanup

### Remove generated data (keep code)
```bash
cd ..
rm -rf data/multimodal/
```

### Stop containers (keep data)
```bash
docker compose stop
```

### Remove everything (including volumes)
```bash
docker compose down -v
rm -rf data/multimodal/ results/phase2_*.json
```

---

## Next Steps

After running Phase 2:

1. ✅ **Review STEP_BY_STEP_GUIDE.md** - Understand what's happening under the hood
2. ✅ **Check QUICK_REFERENCE.md** - Commands cheat sheet
3. ✅ **Read SESSION_SUMMARY.md** - Implementation details and decisions
4. ✅ **Try real documents** - Replace synthetic data with actual PDFs/images
5. ✅ **Scale test** - Increase to 1000+ documents per type
6. ✅ **Visualize** - Use embedding visualization tools

---

## Common Workflows

### Regenerate Data with Different Parameters
```bash
cd scripts

# More images, fewer documents
python generate_multimodal_data.py --num-images 500 --num-pdfs 50

# Reprocess
python process_multimodal_data.py

# Reload and benchmark
python benchmark_multimodal.py
```

### Test Only Specific Database
```bash
# Test only Milvus
python milvus_multimodal_client.py

# Test only Weaviate
python weaviate_multimodal_client.py
```

### Run Benchmarks Multiple Times
```bash
# Get more consistent results
for i in {1..3}; do
    echo "Run $i"
    python benchmark_multimodal.py
    sleep 5
done
```

---

## Performance Tips

**Optimize CLIP Processing**:
```python
# In process_multimodal_data.py
# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
```

**Batch Processing**:
```python
# Process images in larger batches if you have RAM
batch_size = 64  # Instead of 32
```

**Reduce Data for Testing**:
```bash
# Quick test with small dataset
python generate_multimodal_data.py --num-pdfs 10 --num-word 5 --num-images 20
```

---

## Additional Resources

- [Milvus Documentation](https://milvus.io/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [CLIP Paper](https://arxiv.org/abs/2103.00020)
- [Sentence Transformers](https://www.sbert.net/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)

---

## Support

For issues or questions:
- Check STEP_BY_STEP_GUIDE.md for detailed explanations
- Review script source code for implementation details
- Check Docker logs: `docker compose logs milvus` or `docker compose logs weaviate`
- Verify data files exist: `ls -R data/multimodal/`

---

**Phase**: 2 (Multi-Modal)
**Estimated Total Time**: 15-20 minutes (first run with CLIP download)
**Subsequent Runs**: 5-10 minutes
