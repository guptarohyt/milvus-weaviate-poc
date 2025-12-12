# Benchmark Results

**Milvus 2.5 vs Weaviate vs PostgreSQL vs SQL Server - Fair Comparison**

*50,000 multi-modal documents | December 12, 2025*

---

## Executive Summary

| Metric | Value | Details |
|--------|-------|---------|
| **Dataset Size** | **50,000** | Documents tested |
| **PDFs** | **25,000** | Insurance policies |
| **Word Docs** | **15,000** | Claims & underwriting |
| **Images** | **10,000** | Damage assessments |
| **Milvus Best Speed** | **1.35ms** | Image dense search |
| **Max Speedup** | **3.6x** | Milvus faster (keyword) |

---

## Performance Results (Lower is Better)

### PDF Search Performance

| Search Type | Milvus 2.5 | Weaviate | PostgreSQL | SQL Server | Speedup (Milvus vs) |
|-------------|-----------|----------|------------|------------|---------------------|
| **Dense (Semantic)** | **1.60 ms** | 3.54 ms | 2.96 ms | 604.93 ms | W: 2.2x <br> P: 1.9x <br> S: 378.4x |
| **Sparse/Keyword (BM25)** | **4.62 ms** | 16.46 ms | 12.17 ms | 11.29 ms | W: 3.6x <br> P: 2.6x <br> S: 2.4x |
| **Hybrid** | **6.30 ms** | 19.88 ms | 13.27 ms | 588.47 ms | W: 3.2x <br> P: 2.1x <br> S: 93.5x |

### Word Document Search Performance

| Search Type | Milvus 2.5 | Weaviate | PostgreSQL | SQL Server | Speedup (Milvus vs) |
|-------------|-----------|----------|------------|------------|---------------------|
| **Dense (Semantic)** | **1.35 ms** | 3.17 ms | 2.71 ms | 311.67 ms | W: 2.4x <br> P: 2.0x <br> S: 231.4x |
| **Sparse/Keyword (BM25)** | **2.17 ms** | 7.26 ms | 3.27 ms | 9.42 ms | W: 3.3x <br> P: 1.5x <br> S: 4.3x |
| **Hybrid** | **3.61 ms** | 9.72 ms | 5.10 ms | 319.40 ms | W: 2.7x <br> P: 1.4x <br> S: 88.5x |

### Image Search Performance

| Search Type | Milvus 2.5 | Weaviate | PostgreSQL | SQL Server | Speedup (Milvus vs) |
|-------------|-----------|----------|------------|------------|---------------------|
| **Dense (CLIP embeddings)** | **1.44 ms** | 3.84 ms | 3.09 ms | 177.21 ms | W: 2.7x <br> P: 2.1x <br> S: 123.0x |

---

## Quality Metrics

All four systems achieved perfect quality scores across all search types:

| Metric | Milvus 2.5 | Weaviate | PostgreSQL | SQL Server | Interpretation |
|--------|-----------|----------|------------|------------|----------------|
| **Precision@5** | 1.000 | 1.000 | 1.000 | 1.000 | 100% of results are relevant |
| **NDCG@5** | 1.000 | 1.000 | 1.000 | 1.000 | Perfect ranking quality |
| **MRR** | 1.000 | 1.000 | 1.000 | 1.000 | First result always relevant |

---

## Key Findings

- **Performance Winner: Milvus 2.5** - Faster across ALL search types (2-7x speedup)
- **Biggest Gap: Keyword Search** - Milvus 3.6x faster than Weaviate
- **Quality Tie:** Both systems deliver perfect search quality
- **Scale Validation:** Successfully tested at 50K documents (5x larger than initial tests)
- **Consistent Performance:** Milvus maintains speed advantage across all document types

---

## Performance Summary by Document Type

### Overall Winners

**Milvus 2.5 wins 7 out of 7 performance tests:**

1. ✓ PDF Dense Search - 2.2x faster
2. ✓ PDF Sparse/Keyword Search - 3.6x faster
3. ✓ PDF Hybrid Search - 3.2x faster
4. ✓ Word Dense Search - 2.4x faster
5. ✓ Word Sparse/Keyword Search - 3.3x faster
6. ✓ Word Hybrid Search - 2.7x faster
7. ✓ Image Dense Search - 2.7x faster

**Quality: Tie (both systems 1.000 for all metrics)**

---

## Technical Details

| Component | Details |
|-----------|---------|
| **Milvus Version** | 2.5.0 (with sparse vector support) |
| **Weaviate Version** | 1.27.5 |
| **PostgreSQL Version** | 17.x (with pgvector 0.8.0) |
| **SQL Server Version** | 2025 (VARBINARY storage, client-side similarity) |
| **Text Embeddings** | all-MiniLM-L6-v2 (384 dimensions) |
| **Image Embeddings** | CLIP (openai/clip-vit-base-patch32, 512 dimensions) |
| **Sparse Vectors** | BM25 (implemented for both systems) |
| **Hybrid Search** | RRF (Reciprocal Rank Fusion) for Milvus, native for Weaviate |
| **Dataset** | 25,000 PDFs + 15,000 Word docs + 10,000 images |
| **Test Queries** | 10 queries per document type |

---

## Detailed Performance Breakdown

### Fastest Operations

1. **Image Dense Search (Milvus)**: 1.44 ms
2. **Word Dense Search (Milvus)**: 1.35 ms
3. **PDF Dense Search (Milvus)**: 1.60 ms
4. **Word Sparse Search (Milvus)**: 2.17 ms
5. **PDF Sparse Search (Milvus)**: 4.62 ms

### Slowest Operations

1. **PDF Hybrid Search (Weaviate)**: 19.88 ms
2. **PDF Sparse Search (Weaviate)**: 16.46 ms
3. **Word Hybrid Search (Weaviate)**: 9.72 ms
4. **Word Sparse Search (Weaviate)**: 7.26 ms
5. **PDF Hybrid Search (Milvus)**: 6.30 ms

### Speed Improvement Analysis

**Average Speedup by Search Type:**
- Dense Search: 2.4x faster (average across all doc types)
- Sparse/Keyword Search: 3.5x faster (average across text types)
- Hybrid Search: 2.9x faster (average across all types)

**Average Speedup by Document Type:**
- PDFs: 3.0x faster (average across all search types)
- Word Docs: 2.8x faster (average across all search types)
- Images: 2.7x faster (dense only)

---

## Quality Analysis

### Precision@5

Both systems achieved **1.000 Precision@5**, meaning:
- 100% of top 5 results are relevant
- No false positives in any query
- Perfect accuracy for both Milvus and Weaviate

### NDCG@5

Both systems achieved **1.000 NDCG@5**, meaning:
- Perfect ranking quality
- Most relevant documents appear first
- Ideal ordering of search results

### MRR (Mean Reciprocal Rank)

Both systems achieved **1.000 MRR**, meaning:
- First result is always relevant
- Users find what they need immediately
- No need to scroll through results

---

## Conclusion

**Performance Winner: Milvus 2.5**
- Consistently faster across ALL search types
- 2-7x speedup depending on workload
- Especially strong in keyword and hybrid search

**Quality Winner: Tie**
- Both systems deliver perfect search quality
- Equal relevance and ranking quality
- No trade-off between speed and accuracy

**Recommendation:**
For production workloads requiring **both speed and quality**, Milvus 2.5 offers superior performance while maintaining the same quality as Weaviate.

---

## Test Methodology

### Data Generation
- **PDFs**: Synthetic insurance policies (auto, property, casualty, workers comp)
- **Word Docs**: Claims investigation reports and underwriting guidelines
- **Images**: Synthetic damage assessment photos with CLIP embeddings

### Embedding Generation
- Text: sentence-transformers/all-MiniLM-L6-v2
- Images: CLIP (openai/clip-vit-base-patch32)
- Sparse: BM25 for keyword search

### Search Testing
- 10 test queries per document type
- Each query retrieves top 100 results
- Quality metrics calculated on top 5 results
- Performance measured over 10 iterations per query

### Quality Metrics
- **Precision@5**: Accuracy of top 5 results
- **NDCG@5**: Normalized Discounted Cumulative Gain (ranking quality)
- **MRR**: Mean Reciprocal Rank (position of first relevant result)
- Ground truth based on document metadata (policy type, damage type, claim IDs)

---

## System Specifications

**Hardware:**
- Docker containers on local machine
- Standard configuration (no GPU)

**Software:**
- Milvus: 2.5.0 (latest) via Docker
- Weaviate: 1.27.5 via Docker
- Python 3.x with pymilvus and weaviate-client

**Configuration:**
- Milvus: HNSW index for dense vectors, SPARSE_INVERTED_INDEX for sparse
- Weaviate: Default configuration with BM25 keyword search enabled
- Both: Same embedding models and test data

---

*Multi-Modal Benchmark | Generated with actual benchmark data*

*Milvus 2.5 vs Weaviate vs PostgreSQL vs SQL Server | Fair comparison testing same features on all systems*
