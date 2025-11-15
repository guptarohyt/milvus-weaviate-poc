# Visualization Quick Start Guide

## TL;DR

**Question:** How do I visualize 384/512-dimensional embeddings?
**Answer:** Use dimensionality reduction (PCA, t-SNE, UMAP) to project to 2D/3D.

**Question:** What is MinIO's role?
**Answer:** MinIO stores all vector data for Milvus (like S3 for vectors).

---

## 5-Minute Quick Start

### 1. Install Dependencies

```bash
pip install scikit-learn umap-learn
```

### 2. Run Quick Demo (After Data is Generated)

```bash
cd scripts
python quick_viz_demo.py
```

**Output:** `visualizations/quick_demo.png` - 2D scatter plot of image embeddings

### 3. Run Full Visualization Suite

```bash
cd scripts
python visualize_embeddings.py
```

**Output:** Multiple PNG files showing PCA, t-SNE, UMAP in 2D and 3D

---

## What Each Tool Does

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `quick_viz_demo.py` | Simple demo | Processed JSON | 1 PNG (PCA 2D) |
| `visualize_embeddings.py` | Full suite | Processed JSON | 18+ PNGs (all methods) |
| `extract_vectors_from_dbs.py` | DB export | Live databases | JSON files |

---

## Dimensionality Reduction Cheat Sheet

### When to Use What?

| Need | Use | Why |
|------|-----|-----|
| Quick exploration | **PCA** | Fast, deterministic |
| Find clusters | **t-SNE** | Best local structure |
| General visualization | **UMAP** | Best overall balance |
| Interactive exploration | **UMAP → Plotly** | Can rotate/zoom |

### Parameter Guidelines

**t-SNE:**
- `perplexity=30`: Good default
- Small dataset (<500): perplexity=5-15
- Large dataset (>5000): perplexity=50

**UMAP:**
- `n_neighbors=15`: Good default
- More global structure: n_neighbors=50-100
- More local structure: n_neighbors=5-10

---

## MinIO in 60 Seconds

### What is MinIO?

S3-compatible object storage that Milvus uses to store:
- Vector data
- Index files
- Write-ahead logs

### Why MinIO?

- **Scalability**: Handle TBs of vectors
- **Cost**: Cheaper than in-memory storage
- **Compatibility**: Can swap for AWS S3

### How to Access?

**Web UI:**
```
URL: http://localhost:9001
Username: minioadmin
Password: minioadmin
```

**What You'll See:**
```
milvus-bucket/
├── delta_log/      <- Write-ahead logs
├── insert_log/     <- Inserted vectors
└── index/          <- Built indexes
```

### Do I Need to Manage It?

**No!** Milvus handles MinIO automatically. You can browse for debugging/learning.

---

## Common Visualization Patterns

### Pattern 1: Cluster Analysis

**Goal:** See if similar documents cluster together

**Code:**
```python
from visualize_embeddings import EmbeddingVisualizer

viz = EmbeddingVisualizer()
embeddings, labels, _ = viz.load_embeddings('images')
vectors_2d = viz.reduce_dimensions_umap(embeddings, n_components=2)
viz.plot_2d(vectors_2d, labels, "Image Clusters", "clusters.png")
```

**Look For:**
- Clear separation between categories
- Tight clusters = good embeddings
- Outliers = unusual documents

### Pattern 2: Document Similarity

**Goal:** Find most similar documents in 2D space

**Code:**
```python
import numpy as np
from scipy.spatial.distance import cdist

# Find nearest neighbors in 2D space
distances = cdist(vectors_2d, vectors_2d, metric='euclidean')
closest = np.argsort(distances, axis=1)[:, 1:6]  # Top 5 nearest

print(f"Documents closest to doc 0: {closest[0]}")
```

### Pattern 3: Comparison Across Data Types

**Goal:** Compare PDF, Word, and Image embeddings

**Code:**
```python
viz = EmbeddingVisualizer()
viz.create_comparison_plot()
```

**Output:** Side-by-side plots of all three data types

---

## Troubleshooting

### "Data not found"

**Solution:**
```bash
cd scripts
python generate_multimodal_data.py --type all
python process_multimodal_data.py --type all
```

### "t-SNE taking forever"

**Solution:** Use PCA first to reduce dimensions, then t-SNE:
```python
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

pca = PCA(n_components=50)
embeddings_reduced = pca.fit_transform(embeddings)

tsne = TSNE(n_components=2)
vectors_2d = tsne.fit_transform(embeddings_reduced)
```

### "UMAP not installed"

**Solution:**
```bash
pip install umap-learn
```

### "Plots look the same"

**Possible Causes:**
- Embeddings are actually very similar (expected for homogeneous data)
- Need to tune parameters (perplexity, n_neighbors)
- Try different reduction methods

---

## Example Workflow

### Complete Flow from Scratch

```bash
# 1. Start databases
docker-compose up -d

# 2. Generate data
cd scripts
python generate_multimodal_data.py --type all

# 3. Process and embed
python process_multimodal_data.py --type all

# 4. Load into databases
python milvus_multimodal_client.py
python weaviate_multimodal_client.py

# 5. Visualize
python visualize_embeddings.py

# 6. Browse results
open ../visualizations/
```

### Just Visualization (Data Already Exists)

```bash
cd scripts
python visualize_embeddings.py
open ../visualizations/
```

---

## Key Files Reference

### Data Files
```
data/
└── multimodal/
    ├── pdfs/                  <- Generated PDFs
    ├── word/                  <- Generated Word docs
    ├── images/                <- Generated images
    └── processed/
        ├── pdfs_processed.json      <- Embeddings
        ├── word_docs_processed.json <- Embeddings
        └── images_processed.json    <- Embeddings
```

### Output Files
```
visualizations/
├── pdfs_pca_2d.png
├── pdfs_pca_3d.png
├── pdfs_tsne_2d.png
├── pdfs_tsne_3d.png
├── pdfs_umap_2d.png
├── pdfs_umap_3d.png
├── (same for word_docs and images)
└── comparison_all_types.png
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR WORKFLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Documents (PDF/Word/Images)                                │
│         │                                                    │
│         ▼                                                    │
│  Extract Text/Process Images                                │
│         │                                                    │
│         ▼                                                    │
│  Generate Embeddings                                         │
│  • Text: all-MiniLM-L6-v2 → 384 dims                        │
│  • Images: CLIP vit-base → 512 dims                         │
│         │                                                    │
│         ├──────────┬──────────┐                             │
│         ▼          ▼          ▼                             │
│     Milvus     Weaviate   Visualization                     │
│         │          │          │                             │
│         ▼          │          ▼                             │
│      MinIO         │     PCA/t-SNE/UMAP                     │
│   (Storage)        │          │                             │
│                    │          ▼                             │
│                    │      2D/3D Plots                        │
│                    │                                         │
└────────────────────┴─────────────────────────────────────────┘
```

---

## Next Steps

1. ✅ Read `VISUALIZATION_GUIDE.md` for deep dive
2. ✅ Run `quick_viz_demo.py` for simple example
3. ✅ Run `visualize_embeddings.py` for full suite
4. ✅ Explore MinIO web UI at http://localhost:9001
5. ✅ Experiment with different parameters

---

## Resources

- **Full Guide:** `VISUALIZATION_GUIDE.md`
- **Scripts:** `scripts/visualize_embeddings.py`, `scripts/extract_vectors_from_dbs.py`
- **Dependencies:** `requirements.txt`
- **MinIO Console:** http://localhost:9001
- **Benchmark Results:** `results/phase2_benchmark_results.json`
