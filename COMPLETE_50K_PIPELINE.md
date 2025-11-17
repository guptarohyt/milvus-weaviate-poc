# Complete 50K Multi-Modal Benchmark Pipeline

## Overview

This document explains the complete pipeline for scaling from 10K to 50K documents in our multi-modal vector database benchmark comparing Milvus 2.5 vs Weaviate.

## Pipeline Summary

The complete pipeline consists of 5 major steps:

1. **Generate** 50,000 documents (25K PDFs + 15K Word docs + 10K images)
2. **Process** them to create embeddings
3. **Load** into both Milvus 2.5 and Weaviate databases
4. **Run benchmarks** to measure performance
5. **Generate HTML report** with results

## What We're Trying to Achieve

Scale up the benchmark from 10,000 documents to 50,000 documents while keeping everything else the same as the 10K benchmark:
- Same technology stack (Milvus 2.5, Weaviate)
- Same embedding models (all-MiniLM-L6-v2 for text, CLIP for images)
- Same search types (dense, sparse/keyword, hybrid)
- Same quality metrics (Precision@5, NDCG@5, MRR)
- Just 5x more data

## Step-by-Step Pipeline

### Step 1: Generate 50K Documents

**Command:**
```bash
cd scripts
python generate_data.py --pdfs 25000 --word 15000 --images 10000 --skip-confirmation
```

**What it does:**
- Generates 25,000 PDF insurance policies using `reportlab`
- Generates 15,000 Word documents (claims + underwriting) using `python-docx`
- Generates 10,000 damage assessment images using `Pillow`

**Technology used:**
- NO LLMs - pure Python libraries
- reportlab for PDFs
- python-docx for Word documents
- Pillow (PIL) for images
- Faker library for realistic synthetic data

**Output:**
- `scripts/data/multimodal/pdfs/*.pdf` (25,000 files)
- `scripts/data/multimodal/word/*.docx` (15,000 files)
- `scripts/data/multimodal/images/*.png` (10,000 files)

**Key fix applied:**
Added `--skip-confirmation` flag to avoid blocking when run in background.

### Step 2: Process Documents to Create Embeddings

**Command:**
```bash
cd scripts
python process_data.py
```

**What it does:**
- Extracts text from PDFs using `pdfplumber`
- Extracts text from Word docs using `python-docx`
- Creates dense embeddings for text using `sentence-transformers` (all-MiniLM-L6-v2, 384 dims)
- Creates image embeddings using `transformers` CLIP model (512 dims)
- Saves processed data with embeddings to JSON files

**Output:**
- `data/multimodal/processed/pdfs_processed.json` (383MB, 25,000 PDFs)
- `data/multimodal/processed/word_docs_processed.json` (188MB, 15,000 Word docs)
- `data/multimodal/processed/images_processed.json` (245MB, 10,000 images)
- Total: 816MB of processed data with embeddings

**Key fix applied:**
Ensured output goes to `/data/multimodal/processed/` (not `/scripts/data/multimodal/processed/`) to match where benchmark loads from.

### Step 3: Load Data into Databases

**IMPORTANT NOTE:** There are TWO ways data gets loaded:

#### Option A: Load During Benchmark (Temporary)
**Command:**
```bash
cd scripts
python benchmark.py
```

**What happens:**
1. Loads all 50K documents into BOTH Milvus and Weaviate
2. Runs all performance tests
3. **AUTOMATICALLY DELETES all data** after testing (cleanup)

**Use this when:** Running the actual benchmark to measure performance.

**Result:** Data is NOT persistent - you cannot browse it afterwards.

#### Option B: Load Persistently (No Cleanup)
**Command:**
```bash
cd scripts
python load_data_persistent.py
```

**What happens:**
1. Loads all 50K documents into BOTH Milvus and Weaviate
2. Does NOT run any tests
3. **Leaves data in the databases** - no cleanup

**Use this when:** You want to browse/explore the actual 50K documents.

**Result:** Data stays in databases, you can use `database_browser.py` to explore it.

---

**Loading details (both scripts do this):**

**Milvus 2.5:**
- Creates 3 hybrid collections (pdfs, word, images)
- Each collection has dense vectors + sparse vectors (BM25)
- Uses IVF_FLAT index for dense, SPARSE_INVERTED_INDEX for sparse
- Inserts in batches of 5000 to avoid gRPC message size limit

**Weaviate:**
- Creates 3 classes (PDFs, WordDocs, Images)
- Configures text2vec-transformers module for dense vectors
- Configures BM25 for keyword search
- Inserts all documents

**Key fix applied:**
Modified `milvus_25_hybrid_client.py` to insert in batches of 5000 documents instead of all at once, avoiding gRPC 67MB message size limit.

### Step 4: Run Benchmarks

**Command:**
```bash
cd scripts
python benchmark.py
```

**What it tests:**

For PDFs (25,000 docs):
- Dense search (semantic similarity)
- Sparse search (BM25 keyword)
- Hybrid search (RRF fusion)

For Word docs (15,000 docs):
- Dense search
- Sparse search
- Hybrid search

For Images (10,000 docs):
- Dense search (CLIP embeddings)

**Metrics measured:**
- Average query latency (milliseconds)
- Standard deviation
- Min/max latency

**Output:**
- `results/phase3_fair_benchmark_results.json` - Performance metrics
- `results/phase3_quality_results.json` - Quality metrics (Precision@5, NDCG@5, MRR)

**Cleanup:**
After benchmarking, the script automatically drops all collections to free up resources.

### Step 5: Generate HTML Report

**Command:**
```bash
cd scripts
python generate_50k_report.py
```

**What it does:**
- Reads actual benchmark results from `results/phase3_fair_benchmark_results.json`
- Reads quality metrics from `results/phase3_quality_results.json`
- Generates beautiful HTML report with actual performance numbers
- NO hardcoded values - everything comes from actual benchmark data

**Output:**
- `BENCHMARK_50K_REPORT.html` - Professional HTML report with results

**Key fix applied:**
Created entirely new `generate_50k_report.py` that reads actual data from JSON instead of using hardcoded values.

## Key Results (50K Benchmark)

### Performance (Lower is Better)

**PDF Search (25,000 documents):**
- Milvus Dense: 1.22 ms vs Weaviate: 3.71 ms (3.0x faster)
- Milvus Sparse: 2.76 ms vs Weaviate: 20.15 ms (7.3x faster)
- Milvus Hybrid: 3.94 ms vs Weaviate: 23.68 ms (6.0x faster)

**Word Document Search (15,000 documents):**
- Milvus Dense: 1.15 ms vs Weaviate: 4.06 ms (3.5x faster)
- Milvus Sparse: 1.43 ms vs Weaviate: 11.71 ms (8.2x faster)
- Milvus Hybrid: 2.53 ms vs Weaviate: 10.67 ms (4.2x faster)

**Image Search (10,000 documents):**
- Milvus Dense: 1.04 ms vs Weaviate: 2.90 ms (2.8x faster)

### Quality (Perfect Scores for Both)

Both Milvus and Weaviate achieved perfect quality scores:
- Precision@5: 1.000
- NDCG@5: 1.000
- MRR: 1.000

## Technical Details

### Dataset Composition
- 25,000 PDF insurance policies
- 15,000 Word documents (claims investigation + underwriting guidelines)
- 10,000 damage assessment images
- Total: 50,000 multi-modal documents

### Embedding Models
- Text: all-MiniLM-L6-v2 (384 dimensions)
- Images: CLIP openai/clip-vit-base-patch32 (512 dimensions)
- Sparse: BM25 (implemented for both systems)

### Vector Database Versions
- Milvus: 2.5.0 (with sparse vector support)
- Weaviate: 1.27.5

### Search Configurations
- Dense: Cosine similarity on embedding vectors
- Sparse: BM25 keyword search
- Hybrid: Reciprocal Rank Fusion (RRF) for Milvus, native for Weaviate

## Key Challenges and Solutions

### Challenge 1: Confirmation Prompt Blocking
**Problem:** `generate_data.py` had interactive confirmation that blocked background execution.
**Solution:** Added `--skip-confirmation` flag.

### Challenge 2: Directory Mismatch
**Problem:** `process_data.py` saved to different location than `benchmark.py` loaded from.
**Solution:** Copied processed data to correct location, verified file counts.

### Challenge 3: gRPC Message Size Limit
**Problem:** Trying to insert 25K PDFs at once exceeded 67MB gRPC limit.
**Solution:** Modified insertion to use batches of 5000 documents.

### Challenge 4: Hardcoded Report Values
**Problem:** Initial report had hardcoded "10,000" values instead of reading actual data.
**Solution:** Created new `generate_50k_report.py` that reads from actual JSON results.

### Challenge 5: Image Field Names
**Problem:** Images use "image_embedding" instead of "embedding", and "description" instead of "text".
**Solution:** Updated loading scripts to handle image-specific field names correctly.

## Verification

### Verify Data is in Database
```bash
python -c "from pymilvus import *; connections.connect(); \
  print('PDFs:', Collection('persistent_pdfs').num_entities); \
  print('Word:', Collection('persistent_word').num_entities); \
  print('Images:', Collection('persistent_images').num_entities)"
```

Expected output:
```
PDFs: 25000
Word: 15000
Images: 10000
```

### Verify Benchmark Results
```bash
cat results/phase3_fair_benchmark_results.json | python -m json.tool | head -40
```

### Browse Data Interactively
```bash
python scripts/database_browser.py
```

## File Locations

### Source Data
- Raw PDFs: `scripts/data/multimodal/pdfs/*.pdf`
- Raw Word: `scripts/data/multimodal/word/*.docx`
- Raw Images: `scripts/data/multimodal/images/*.png`

### Processed Data (with embeddings)
- PDFs: `data/multimodal/processed/pdfs_processed.json`
- Word: `data/multimodal/processed/word_docs_processed.json`
- Images: `data/multimodal/processed/images_processed.json`

### Results
- Performance: `results/phase3_fair_benchmark_results.json`
- Quality: `results/phase3_quality_results.json`
- HTML Report: `BENCHMARK_50K_REPORT.html`

### Scripts
- Generation: `scripts/generate_data.py`
- Processing: `scripts/process_data.py`
- Benchmarking: `scripts/benchmark.py`
- Quality Evaluation: `scripts/evaluate_quality.py`
- Report Generation: `scripts/generate_50k_report.py`
- Persistent Loading: `scripts/load_data_persistent.py`

## Comparison: 10K vs 50K

| Aspect | 10K Benchmark | 50K Benchmark |
|--------|---------------|---------------|
| PDFs | 5,000 | 25,000 |
| Word Docs | 3,000 | 15,000 |
| Images | 2,000 | 10,000 |
| Total Docs | 10,000 | 50,000 |
| Scale Factor | 1x | 5x |
| Milvus Dense Speed | ~1.2ms | ~1.2ms |
| Batch Size | Single batch | 5000/batch |
| gRPC Issues | None | Needed batching |

## Cost Analysis

**Total Cost: $0**

All data generation used free, open-source Python libraries:
- reportlab (free)
- python-docx (free)
- Pillow (free)
- Faker (free)

Compared to using LLMs which would have cost $500-1000 for 50K documents.

## Time Estimates

- Generation: ~3-4 hours for 50K documents
- Processing: ~2-3 hours for embeddings
- Benchmark: ~20 minutes for all tests
- Total: ~6-7 hours for complete pipeline

## Reproducibility

To reproduce the entire 50K benchmark:

```bash
# 1. Generate
cd scripts
python generate_data.py --pdfs 25000 --word 15000 --images 10000 --skip-confirmation

# 2. Process
python process_data.py

# 3. Benchmark
python benchmark.py

# 4. Quality evaluation
python evaluate_quality.py

# 5. Generate report
python generate_50k_report.py

# 6. Open report
open ../BENCHMARK_50K_REPORT.html
```

## Conclusion

We successfully scaled the multi-modal vector database benchmark from 10,000 to 50,000 documents, maintaining the same methodology and technology stack. The results show that Milvus 2.5 maintains its performance advantage (2-8x faster) even at larger scale, while both systems achieve perfect quality scores.

The benchmark proves that both vector databases can handle production-scale workloads with excellent search quality, but Milvus 2.5 delivers significantly better query performance, especially for keyword and hybrid search.
