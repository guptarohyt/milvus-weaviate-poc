# Vector Embedding Visualization Guide

## Table of Contents
1. [Understanding Vector Embeddings](#understanding-vector-embeddings)
2. [MinIO's Role in Milvus](#minios-role-in-milvus)
3. [Visualization Techniques](#visualization-techniques)
4. [Using the Visualization Tools](#using-the-visualization-tools)
5. [Interpreting Visualizations](#interpreting-visualizations)

---

## Understanding Vector Embeddings

### What are Vector Embeddings?

Vector embeddings are numerical representations of data (text, images, audio, etc.) in high-dimensional space. In our POC:

- **Text embeddings**: 384-dimensional vectors from `all-MiniLM-L6-v2`
- **Image embeddings**: 512-dimensional vectors from CLIP `vit-base-patch32`

### Example

A sentence "insurance claim for hurricane damage" might be represented as:
```
[0.123, -0.456, 0.789, ..., 0.234]  # 384 numbers
```

Similar sentences will have similar vectors (measured by distance).

### The Problem

**You can't visualize 384 or 512 dimensions!** Human perception is limited to 2D/3D space.

**Solution**: Dimensionality reduction techniques project high-dimensional data into 2D/3D while preserving relationships.

---

## MinIO's Role in Milvus

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MILVUS ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   Milvus     │◄──────►│     etcd     │                  │
│  │  Standalone  │        │              │                  │
│  │  (Query      │        │  (Metadata   │                  │
│  │   Engine)    │        │   Storage)   │                  │
│  └──────┬───────┘        └──────────────┘                  │
│         │                                                   │
│         │ Reads/Writes                                      │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │    MinIO     │                                           │
│  │              │                                           │
│  │ (S3-Compatible│                                          │
│  │   Object      │                                          │
│  │   Storage)    │                                          │
│  └──────────────┘                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### What MinIO Stores

1. **Vector Data**: The actual embedding vectors you insert
2. **Index Files**: Pre-built indexes (IVF_FLAT, HNSW, etc.)
3. **Binlogs**: Write-ahead logs for data recovery
4. **Segment Files**: Collections are divided into segments

### Example Data Flow

When you insert a vector into Milvus:

```python
collection.insert([
    ["doc_001"],                    # ID
    [[0.1, 0.2, ..., 0.384]]       # 384-dim vector
])
```

**What happens:**
1. Milvus writes to WAL (Write-Ahead Log) in MinIO
2. Data is flushed to segment files in MinIO
3. etcd stores metadata: "collection X has segment Y in MinIO bucket Z"
4. Index is built and stored in MinIO

### Why MinIO?

- **Scalability**: Can store TBs of vector data
- **S3 Compatibility**: Easy to swap for AWS S3 in production
- **Separation of Concerns**: Compute (Milvus) separate from storage (MinIO)
- **Cost-Effective**: Cheaper than storing in-memory

### Inspecting MinIO

You can browse MinIO data via:

```bash
# MinIO Console (Web UI)
http://localhost:9001

# Default credentials (from docker-compose.yml)
Username: minioadmin
Password: minioadmin
```

**Buckets you'll see:**
- `milvus-bucket`: Contains all Milvus data
  - `/delta_log/`: Write-ahead logs
  - `/insert_log/`: Inserted data segments
  - `/index/`: Built index files

---

## Visualization Techniques

### 1. PCA (Principal Component Analysis)

**How it works:**
- Finds directions of maximum variance in data
- Projects data onto top N principal components
- Linear transformation (fast but limited)

**Pros:**
- ✅ Very fast
- ✅ Deterministic (same result every time)
- ✅ Good for understanding variance

**Cons:**
- ❌ Linear only (misses non-linear patterns)
- ❌ May not preserve local structure

**Best for:**
- Quick exploratory analysis
- Understanding which dimensions matter most
- Large datasets (100k+ vectors)

**Example:**
```python
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
vectors_2d = pca.fit_transform(embeddings)

print(f"Explained variance: {pca.explained_variance_ratio_.sum():.2%}")
# Output: Explained variance: 45.23%
```

### 2. t-SNE (t-Distributed Stochastic Neighbor Embedding)

**How it works:**
- Preserves local structure (nearby points stay nearby)
- Non-linear dimensionality reduction
- Optimizes probability distributions

**Pros:**
- ✅ Excellent for finding clusters
- ✅ Preserves local neighborhood structure
- ✅ Beautiful visualizations

**Cons:**
- ❌ Slow for large datasets
- ❌ Non-deterministic (different results each run)
- ❌ Doesn't preserve global structure
- ❌ Perplexity parameter needs tuning

**Best for:**
- Finding clusters in data
- Visualizing semantic similarity
- Medium datasets (1k-10k vectors)

**Parameters:**
- `perplexity`: Balance between local/global structure (5-50)
  - Small perplexity (5-10): Focus on very local structure
  - Large perplexity (30-50): Consider broader neighborhoods

**Example:**
```python
from sklearn.manifold import TSNE

tsne = TSNE(n_components=2, perplexity=30)
vectors_2d = tsne.fit_transform(embeddings)
```

### 3. UMAP (Uniform Manifold Approximation and Projection)

**How it works:**
- Preserves both local AND global structure
- Based on manifold learning and topological data analysis
- Faster than t-SNE

**Pros:**
- ✅ Preserves local and global structure
- ✅ Faster than t-SNE
- ✅ Better separation of clusters
- ✅ Works well on large datasets

**Cons:**
- ❌ Requires additional library (`pip install umap-learn`)
- ❌ Still somewhat non-deterministic

**Best for:**
- General-purpose visualization (best overall)
- Large datasets (10k+ vectors)
- When you need both local and global structure

**Parameters:**
- `n_neighbors`: How many neighbors to consider (2-100)
  - Small (5-15): Focus on local structure
  - Large (50-100): Preserve more global structure
- `min_dist`: Minimum distance between points (0.0-0.99)
  - Small (0.0-0.1): Tight clusters
  - Large (0.5-0.99): Spread out points

**Example:**
```python
import umap

reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1)
vectors_2d = reducer.fit_transform(embeddings)
```

### Comparison Table

| Technique | Speed | Local Structure | Global Structure | Deterministic | Best For |
|-----------|-------|----------------|------------------|---------------|----------|
| PCA       | ⚡⚡⚡ | ❌ | ✅ | ✅ | Quick exploration |
| t-SNE     | 🐌    | ✅✅ | ❌ | ❌ | Finding clusters |
| UMAP      | ⚡⚡  | ✅✅ | ✅ | ~✅ | General purpose |

---

## Using the Visualization Tools

### Tool 1: Visualize from Processed Files

**File:** `scripts/visualize_embeddings.py`

**What it does:**
- Loads embeddings from processed JSON files
- Applies PCA, t-SNE, and UMAP
- Creates 2D and 3D scatter plots
- Color-codes by category (for images)

**Usage:**
```bash
cd scripts
source ../venv/bin/activate

# Visualize all data types
python visualize_embeddings.py

# Output: visualizations/*.png
```

**Generated visualizations:**
- `pdfs_pca_2d.png` / `pdfs_pca_3d.png`
- `pdfs_tsne_2d.png` / `pdfs_tsne_3d.png`
- `pdfs_umap_2d.png` / `pdfs_umap_3d.png`
- (Same for word_docs and images)
- `comparison_all_types.png`

### Tool 2: Extract from Databases

**File:** `scripts/extract_vectors_from_dbs.py`

**What it does:**
- Connects to live Milvus and Weaviate instances
- Extracts actual vectors from collections
- Saves to JSON for analysis
- Compares vectors between databases

**Usage:**
```bash
cd scripts
source ../venv/bin/activate

# Make sure databases are running
docker-compose up -d

# Extract vectors
python extract_vectors_from_dbs.py

# Output: extracted_vectors/*.json
```

**Use cases:**
- Verify data was loaded correctly
- Compare vectors between Milvus and Weaviate
- Export vectors for external analysis
- Debug embedding issues

---

## Interpreting Visualizations

### What to Look For

#### 1. Clusters

**Good clustering:**
```
    ●●●         ▲▲▲
   ●●●●●       ▲▲▲▲
    ●●●         ▲▲▲

  Cluster A   Cluster B
```

**Indicates:**
- Similar documents group together
- Embeddings capture semantic meaning
- Good separation between topics

#### 2. Outliers

```
    ●●●
   ●●●●●
    ●●●
              ●  <- Outlier
```

**Indicates:**
- Unique/unusual documents
- Potential data quality issues
- Edge cases to investigate

#### 3. Smooth Transitions

```
   ●●● ─────→ ▲▲▲
  (topic A → topic B)
```

**Indicates:**
- Gradual topic shifts
- Documents spanning multiple themes
- Good embedding continuity

### Example: Image Embeddings

For our insurance damage images, you might see:

```
      [Hurricane]
         ●●●●
        ●●●●●
         ●●●

  [Flood]              [Fire]
   ▲▲▲                  ◆◆◆
  ▲▲▲▲                 ◆◆◆◆
   ▲▲▲                  ◆◆

      [Structural]
         ■■■
        ■■■■
```

**Interpretation:**
- Each damage type forms a cluster
- Proximity = visual/semantic similarity
- Overlap = ambiguous cases (e.g., fire + structural damage)

### Example: Document Embeddings

For PDF/Word documents, you might see:

```
  [Policies]          [Claims]
     ●●●●              ▲▲▲▲
    ●●●●●●            ▲▲▲▲▲
     ●●●●      ╱      ▲▲▲▲
               ╱
              ╱    [Mixed: Policy Claims]
             ╱
```

**Interpretation:**
- Policy documents cluster together
- Claims documents cluster together
- Documents discussing both span the middle

---

## Example Workflow

### 1. Generate and Process Data

```bash
cd scripts

# Generate data
python generate_multimodal_data.py --type all

# Process and embed
python process_multimodal_data.py --type all
```

### 2. Load into Databases

```bash
# Start databases
docker-compose up -d

# Load into Milvus
python milvus_multimodal_client.py

# Load into Weaviate
python weaviate_multimodal_client.py
```

### 3. Visualize

```bash
# Option A: From processed files (faster)
python visualize_embeddings.py

# Option B: From live databases
python extract_vectors_from_dbs.py
```

### 4. Analyze Results

Open `visualizations/*.png` and look for:
- Clear clusters by document type
- Separation of damage types (for images)
- Any unexpected patterns or outliers

---

## Advanced: Custom Visualizations

### Example: Interactive 3D Plot

```python
import plotly.graph_objects as go
from visualize_embeddings import EmbeddingVisualizer

# Load and reduce
viz = EmbeddingVisualizer()
embeddings, labels, metadata = viz.load_embeddings('images')
vectors_3d = viz.reduce_dimensions_umap(embeddings, n_components=3)

# Create interactive plot
fig = go.Figure(data=[go.Scatter3d(
    x=vectors_3d[:, 0],
    y=vectors_3d[:, 1],
    z=vectors_3d[:, 2],
    mode='markers',
    marker=dict(size=5, color=labels, colorscale='Viridis'),
    text=[f"{m['damage_type']}: {m['description'][:50]}" for m in metadata],
    hoverinfo='text'
)])

fig.write_html('interactive_3d.html')
```

### Example: Distance Matrix Heatmap

```python
import seaborn as sns
from scipy.spatial.distance import pdist, squareform

# Calculate pairwise distances
distances = squareform(pdist(embeddings[:50], metric='cosine'))

# Plot heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(distances, cmap='coolwarm', square=True)
plt.title('Pairwise Cosine Distance Matrix')
plt.savefig('distance_heatmap.png')
```

---

## Troubleshooting

### Issue: "UMAP not installed"

```bash
pip install umap-learn
```

### Issue: "t-SNE is very slow"

**Solutions:**
- Reduce dataset size (sample 1000 vectors)
- Use PCA first to reduce to 50 dims, then t-SNE
- Increase `n_iter` for better results (but slower)

```python
# Fast t-SNE with PCA preprocessing
pca = PCA(n_components=50)
embeddings_pca = pca.fit_transform(embeddings)

tsne = TSNE(n_components=2, perplexity=30)
vectors_2d = tsne.fit_transform(embeddings_pca)
```

### Issue: "All points in one blob"

**Causes:**
- Perplexity too high for t-SNE
- min_dist too large for UMAP
- Embeddings very similar (expected for homogeneous data)

**Solutions:**
- Reduce perplexity (try 5-15)
- Reduce min_dist (try 0.0-0.1)
- Try UMAP instead of t-SNE

---

## References

- [t-SNE Paper](https://jmlr.org/papers/v9/vandermaaten08a.html)
- [UMAP Documentation](https://umap-learn.readthedocs.io/)
- [Understanding PCA](https://scikit-learn.org/stable/modules/decomposition.html#pca)
- [Milvus Architecture](https://milvus.io/docs/architecture_overview.md)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)

---

## Summary

**Vector Visualization:**
- Dimensionality reduction makes high-dim vectors visible
- PCA: Fast, linear
- t-SNE: Great for clusters, slow
- UMAP: Best overall, preserves structure

**MinIO in Milvus:**
- Stores all vector data and indexes
- S3-compatible object storage
- Separates compute from storage
- Accessible at http://localhost:9001

**Tools Provided:**
- `visualize_embeddings.py`: Create PCA/t-SNE/UMAP plots
- `extract_vectors_from_dbs.py`: Export vectors from databases

**Next Steps:**
1. Install dependencies: `pip install scikit-learn umap-learn`
2. Run visualizations: `python visualize_embeddings.py`
3. Explore MinIO console: http://localhost:9001
4. Analyze clustering patterns in generated plots
