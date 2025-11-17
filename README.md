# Vector Database Benchmark: Milvus 2.5 vs Weaviate

Benchmark comparing Milvus 2.5 and Weaviate vector databases on multi-modal insurance documents.

---

## Quick Start

```bash
cd /Users/guptarohyt/workspace/learning/weaviate/scripts

# 1. Generate data (30 min) - Creates 5K PDFs, 3K Word docs, 2K images
python generate_data.py

# 2. Process data (12 min) - Extract text + create embeddings
python process_data.py

# 3. Benchmark (2 min) - Test both databases
python benchmark.py

# 4. Evaluate quality (1 min) - Optional
python evaluate_quality.py

# 5. Generate report (<1 sec)
python generate_report.py

# 6. View results
open ../report.html
```

---

## Scripts

| Script | Purpose | Time |
|--------|---------|------|
| `generate_data.py` | Generate PDFs, Word docs, images | ~30 min |
| `process_data.py` | Extract text + create embeddings | ~12 min |
| `benchmark.py` | Load to DBs + run speed tests | ~2 min |
| `evaluate_quality.py` | Measure retrieval quality | ~1 min |
| `generate_report.py` | Create HTML report | <1 sec |

---

## Custom Dataset Size

```bash
# Quick test (100 docs)
python generate_data.py --pdfs 50 --word 30 --images 20

# Medium (1K docs)
python generate_data.py --pdfs 500 --word 300 --images 200

# Production (10K docs) - default
python generate_data.py --pdfs 5000 --word 3000 --images 2000
```

---

## Data Storage

```
scripts/data/multimodal/
├── pdfs/          ← Generated PDF files
├── word/          ← Generated Word docs
├── images/        ← Generated images
└── processed/     ← JSON with embeddings

results/
├── benchmark_results.json   ← Speed benchmarks
└── quality_results.json     ← Quality metrics

report.html         ← Final report
```

---

## Results (10K Documents)

**Performance:**
- Milvus 2.5: 0.90-2.38ms (2-4x faster)
- Weaviate: 2.32-6.17ms

**Quality:**
- Both: 100% precision, NDCG=1.0, MRR=1.0

**Winner:** Milvus 2.5 (better performance, same quality)

---

## Prerequisites

```bash
# Docker running
docker ps  # Should see milvus and weaviate

# Virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

---

## Project Structure

```
weaviate/
├── scripts/
│   ├── generate_data.py         # Step 1
│   ├── process_data.py           # Step 2
│   ├── benchmark.py              # Step 3
│   ├── evaluate_quality.py       # Step 4
│   ├── generate_report.py        # Step 5
│   └── data/multimodal/          # Data storage
├── results/                      # Benchmark results
├── report.html                   # Final report
└── README.md                     # This file
```

---

**Total Time:** ~45 minutes for 10K documents
