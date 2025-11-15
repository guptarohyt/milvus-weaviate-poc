# Phase 2 Quick Reference - Multi-Modal Vector Search

## 🚀 Quick Start (15 Minutes)

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start databases
docker compose up -d
sleep 30

# 3. Generate multi-modal data
cd scripts
python generate_multimodal_data.py --type all

# 4. Process and create embeddings
python process_multimodal_data.py

# 5. Run benchmarks
python benchmark_multimodal.py
```

**Expected time**: 15-20 minutes (first run with CLIP download)
**Output**: `results/phase2_benchmark_results.json`

---

## 📋 Step-by-Step Commands

### Step 1: Generate Multi-Modal Data
```bash
cd scripts
source ../venv/bin/activate

# Generate all types
python generate_multimodal_data.py --type all

# Or generate specific types
python generate_multimodal_data.py --type pdfs
python generate_multimodal_data.py --type word
python generate_multimodal_data.py --type images
```

**Output**:
- `data/multimodal/pdfs/` - 100 PDF files (~5MB)
- `data/multimodal/word/` - 50 Word documents (~1.5MB)
- `data/multimodal/images/` - 200 PNG images (~2MB)

**Time**: 30-60 seconds

---

### Step 2: Process Data & Generate Embeddings
```bash
python process_multimodal_data.py
```

**What it does**:
- Loads Sentence Transformers (all-MiniLM-L6-v2) for text - 384 dims
- Loads CLIP (openai/clip-vit-base-patch32) for images - 512 dims
- Extracts text from PDFs and Word docs
- Generates embeddings for all documents

**Output**: `data/multimodal/processed/*.json`
**Time**: 5-8 minutes (first run), 2-3 minutes (subsequent)

---

### Step 3: Load Data into Milvus
```bash
python milvus_multimodal_client.py
```

**What it does**:
- Creates 3 collections: `pdfs_phase2`, `word_docs_phase2`, `images_phase2`
- Loads 350 documents with embeddings
- Builds IVF_FLAT indexes

**Time**: 15-20 seconds

---

### Step 4: Load Data into Weaviate
```bash
python weaviate_multimodal_client.py
```

**What it does**:
- Creates 3 collections: `PDFsPhase2`, `WordDocsPhase2`, `ImagesPhase2`
- Loads 350 documents with embeddings
- HNSW index builds automatically

**Time**: 10-15 seconds (faster than Milvus!)

---

### Step 5: Run Benchmarks
```bash
python benchmark_multimodal.py
```

**What it tests**:
1. PDF search (10 queries)
2. Word document search (10 queries)
3. Image-to-image similarity (10 queries)
4. Text-to-image search (10 queries)
5. Filtered image search (5 queries, Weaviate only)

**Time**: 1-2 minutes

---

### Step 6: View Results
```bash
# Pretty-print JSON
cat ../results/phase2_benchmark_results.json | python -m json.tool

# Summary view
python -c "
import json
with open('../results/phase2_benchmark_results.json') as f:
    r = json.load(f)
for cat, data in r['comparison'].items():
    print(f'{cat}: {data[\"faster\"]} wins ({data[\"speedup_percent\"]:.1f}% faster)')
"
```

---

## 🔍 Understanding What's Happening

### During Data Generation (30-60s)
```
Generating multi-modal data...
  ├─ PDFs: ReportLab creates policy documents with tables/charts
  ├─ Word: python-docx creates claims reports and guidelines
  └─ Images: PIL creates synthetic damage assessment photos
```

### During Processing (5-8 min first run)
```
Processing with AI models...
  ├─ Loading Sentence Transformers (~90MB) - text embeddings
  ├─ Loading CLIP (~600MB) - image embeddings
  ├─ Extracting text from PDFs (pdfplumber)
  ├─ Extracting text from Word docs (python-docx)
  ├─ Generating 384-dim embeddings for text
  └─ Generating 512-dim embeddings for images (CLIP)
```

### During Milvus Setup (15-20s)
```
Milvus workflow:
  1. Create collections with schemas     [1s]
  2. Insert documents with embeddings    [8s]
  3. Build IVF_FLAT indexes             [12s]
  4. Load collections to memory          [2s]
  Total: ~23s
```

### During Weaviate Setup (10-15s)
```
Weaviate workflow:
  1. Create collections                  [0.3s]
  2. Insert + build HNSW index          [9s]
  Total: ~9s (2x faster than Milvus!)
```

**Key Difference**: Weaviate builds index DURING insert, Milvus does it AFTER.

### During Benchmarks (1-2 min)
```
Testing 4 query categories:

PDF Search (10 queries):
  Milvus:   2.92ms avg ✅
  Weaviate: 3.16ms avg
  Winner: Milvus (7.4% faster)

Word Search (10 queries):
  Milvus:   3.16ms avg
  Weaviate: 2.79ms avg ✅
  Winner: Weaviate (13.4% faster)

Image-to-Image (10 queries):
  Milvus:   1.03ms avg ✅
  Weaviate: 1.66ms avg
  Winner: Milvus (37.6% faster!) 🏆

Text-to-Image (10 queries):
  Milvus:   2.67ms avg ✅
  Weaviate: 2.87ms avg
  Winner: Milvus (6.9% faster)

Overall Winner: Milvus (3 out of 4)
```

---

## 🎯 Key Metrics to Watch

### Query Performance
```
Target: < 5ms per query

PDF Search:
  Milvus:   2.92ms   ✅ Excellent
  Weaviate: 3.16ms   ✅ Excellent

Image Search (the game changer!):
  Milvus:   1.03ms   ✅ Outstanding
  Weaviate: 1.66ms   ✅ Good

→ Milvus is 37.6% faster on image search with CLIP!
```

### Setup Time
```
Target: < 60s for 350 documents

Milvus:   ~23s   ✅ Good
Weaviate: ~9s    ✅ Excellent (2x faster)
```

### Data Volume
```
Collections:
  - PDFs: 100 documents (384-dim embeddings)
  - Word: 50 documents (384-dim embeddings)
  - Images: 200 images (512-dim CLIP embeddings)
  Total: 350 multi-modal documents
```

### Memory Usage
```
Target: < 1GB for 350 documents

Milvus:   ~300MB  ✅ Good
Weaviate: ~250MB  ✅ Better
CLIP model: ~600MB (loaded during processing)
```

---

## 🔧 Troubleshooting

### "Connection refused"
```bash
# Check containers
docker compose ps

# Restart if needed
docker compose down && docker compose up -d
sleep 30
```

### "ModuleNotFoundError"
```bash
# Activate venv
source venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### "Out of memory" (CLIP)
```bash
# CLIP needs ~2GB RAM total
# Close other apps or reduce batch size:
# Edit process_multimodal_data.py line ~150:
batch_size = 16  # Reduce from 32
```

### "Data not found"
```bash
# Generate data first
cd scripts
python generate_multimodal_data.py --type all
python process_multimodal_data.py
```

### Slow image processing
```bash
# Check GPU
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Or reduce images
python generate_multimodal_data.py --num-images 50
```

---

## 📊 Interpreting Results

### Winner Decision Matrix

| Criterion | Weight | Milvus | Weaviate | Winner |
|-----------|--------|--------|----------|--------|
| **PDF Search** | 25% | 2.92ms | 3.16ms | Milvus |
| **Word Search** | 25% | 3.16ms | 2.79ms | Weaviate |
| **Image Search** | 30% | 1.03ms | 1.66ms | **Milvus** 🏆 |
| **Text-to-Image** | 20% | 2.67ms | 2.87ms | Milvus |

**Overall: Milvus wins 3 out of 4 categories (75%)**

**Key Insight**: Milvus excels at **high-dimensional image embeddings** (CLIP's 512 dims)

### When to Choose Milvus (Phase 2)
- ✅ Heavy image search workloads
- ✅ CLIP or other high-dim visual embeddings
- ✅ Image-to-image similarity
- ✅ Cross-modal (text-to-image) search
- ✅ Mixed embedding dimensions (384 + 512)

### When to Choose Weaviate (Phase 2)
- ✅ Fast setup and deployment
- ✅ Text document search (Word/PDF)
- ✅ Need filtered searches
- ✅ Simpler operations and maintenance
- ✅ Developer experience priority

---

## 🎓 What You'll Learn

Running Phase 2 teaches you:

1. **Multi-Modal Embeddings**: Different models for different data types
2. **CLIP**: How vision-language models enable text-to-image search
3. **Cross-Modal Search**: Query images with text, find text with images
4. **Embedding Dimensions**: Handling 384-dim (text) vs 512-dim (visual)
5. **Document Processing**: PDF/Word extraction and embedding
6. **Performance**: How data type affects vector search speed
7. **Index Types**: IVF_FLAT vs HNSW on different embedding dims

---

## 📚 Files to Review

After running Phase 2:

1. **results/phase2_benchmark_results.json** - Complete metrics
2. **STEP_BY_STEP_GUIDE.md** - Detailed explanations
3. **scripts/process_multimodal_data.py** - Embedding generation
4. **scripts/benchmark_multimodal.py** - Test implementation
5. **data/multimodal/processed/*.json** - Processed data with embeddings

---

## 🚀 Next Steps

After completing Phase 2:

1. ✅ **Analyze results** - Compare with Phase 1 (text-only)
2. ✅ **Visualize embeddings** - See CLIP vs text embeddings
3. ✅ **Test real data** - Use actual insurance PDFs and damage photos
4. ✅ **Scale test** - Try 1000+ documents per type
5. ✅ **Choose winner** - Milvus for images, Weaviate for text?
6. ✅ **Plan deployment** - Production architecture

---

## 💡 Pro Tips

### Run benchmarks multiple times for consistency
```bash
for i in {1..3}; do
    echo "Run $i"
    python benchmark_multimodal.py
    sleep 5
done
```

### Generate different data sizes
```bash
# Small test
python generate_multimodal_data.py --num-pdfs 10 --num-word 5 --num-images 20

# Large test
python generate_multimodal_data.py --num-pdfs 500 --num-word 200 --num-images 1000
```

### Monitor resources during test
```bash
# In another terminal
watch -n 1 'docker stats --no-stream'
```

### Save results with timestamp
```bash
timestamp=$(date +%Y%m%d_%H%M%S)
cp ../results/phase2_benchmark_results.json "../results/phase2_${timestamp}.json"
```

### Use GPU for CLIP (if available)
```bash
# Check GPU
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Install CUDA PyTorch if needed
# See: https://pytorch.org/get-started/locally/
```

---

## 📞 Getting Help

**Check logs**:
```bash
docker compose logs milvus
docker compose logs weaviate
```

**Verbose mode** (add to scripts):
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Browse data interactively**:
```bash
python database_browser.py    # Milvus TUI
python check_db_status.py     # Weaviate status
```

**Visualize embeddings**:
```bash
python visualize_embeddings.py
```

---

## 🔄 Common Workflows

### Full regeneration
```bash
rm -rf data/multimodal/
python generate_multimodal_data.py --type all
python process_multimodal_data.py
python benchmark_multimodal.py
```

### Test only one database
```bash
# Milvus only
python milvus_multimodal_client.py

# Weaviate only
python weaviate_multimodal_client.py
```

### Quick data check
```bash
ls -lh data/multimodal/*/
ls -lh data/multimodal/processed/
```

### View collections
```bash
# Milvus UI
open http://localhost:8000  # Attu interface

# Command line
python -c "
from milvus_multimodal_client import MilvusMultiModalClient
m = MilvusMultiModalClient(load_existing=True)
print(f'PDFs: {m.pdf_collection.num_entities}')
print(f'Word: {m.word_collection.num_entities}')
print(f'Images: {m.image_collection.num_entities}')
"
```

---

## Phase 2 vs Phase 1 Comparison

| Aspect | Phase 1 | Phase 2 |
|--------|---------|---------|
| **Data Types** | JSON (text only) | PDFs, Word, Images |
| **Documents** | 3,500 text records | 350 multi-modal docs |
| **Embeddings** | 384-dim only | 384-dim + 512-dim |
| **Models** | Sentence Transformers | Sentence Transformers + CLIP |
| **Collections** | 3 (same schema) | 3 (different schemas) |
| **Search Types** | Semantic text search | Multi-modal + cross-modal |
| **Complexity** | Basic | Advanced |
| **Setup Time** | 2-5 minutes | 15-20 minutes |
| **Winner** | Weaviate | Milvus |

**Key Takeaway**: Different data modalities favor different databases!

---

**Phase**: 2 (Multi-Modal)
**Status**: ✅ Complete
**Branch**: `phase2`
**Last Updated**: 2025-11-15
