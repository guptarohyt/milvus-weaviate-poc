# Phase 2: Multi-Modal Vector Search POC

A comprehensive comparison of Milvus and Weaviate for **multi-modal vector search** in reinsurance AI use cases.

## What is Phase 2?

Phase 2 extends our vector database comparison to handle **multiple data modalities**:
- 📄 **PDF Documents** - Insurance policies with tables and charts
- 📝 **Word Documents** - Claims reports and underwriting guidelines
- 🖼️ **Images** - Damage assessment photos with CLIP embeddings

This POC evaluates how Milvus and Weaviate handle different embedding types, cross-modal search, and real-world document processing.

---

## Architecture

```
┌─────────────────────────────────────────┐
│        Your Local Machine               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Phase 2 Python Scripts        │   │
│  │  - generate_multimodal_data.py  │   │
│  │  - process_multimodal_data.py   │   │
│  │  - milvus_multimodal_client.py  │   │
│  │  - weaviate_multimodal_client.py│   │
│  │  - benchmark_multimodal.py      │   │
│  └──────────┬──────────────────────┘   │
│             │ Connects via              │
│             │ localhost:19530 (Milvus)  │
│             │ localhost:8080 (Weaviate) │
└─────────────┼─────────────────────────┘
              │
┌─────────────┼─────────────────────────┐
│        Docker Containers              │
│             │                           │
│  ┌──────────▼──────────┐               │
│  │   Milvus :19530     │               │
│  │   + etcd + MinIO    │               │
│  │   + Attu UI :8000   │               │
│  └─────────────────────┘               │
│                                         │
│  ┌─────────────────────┐               │
│  │   Weaviate :8080    │               │
│  └─────────────────────┘               │
└───────────────────────────────────────┘
```

**Hybrid Approach**: Databases run in Docker, Python scripts run locally for easy development.

---

## Multi-Modal Data Types

### 📄 PDF Documents (100 documents)
- **Source**: Phase 1 policy data
- **Processing**: ReportLab generation → pdfplumber extraction
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2, 384 dims)
- **Metadata**: Filename, page count, has_tables flag
- **Use Case**: Semantic search across insurance policies

### 📝 Word Documents (50 documents)
- **Types**:
  - Claims Investigation Reports (30 docs)
  - Underwriting Guidelines (20 docs)
- **Processing**: python-docx generation → text extraction
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2, 384 dims)
- **Format**: Professional styling with tables, headings, bullet points
- **Use Case**: Document similarity and retrieval

### 🖼️ Images (200 images)
- **Types**: Damage assessment photos (fire, flood, hurricane, etc.)
- **Processing**: PIL/Pillow generation → CLIP encoding
- **Embeddings**:
  - **Visual**: CLIP (openai/clip-vit-base-patch32, 512 dims)
  - **Text**: Sentence Transformers (384 dims) for descriptions
- **Metadata**: Damage type, severity, location
- **Use Cases**:
  - Image-to-image similarity
  - Text-to-image search (find photos from text query)

---

## Use Cases Tested

### 1. **PDF Document Search**
Semantic search across insurance policy documents
```python
Query: "property damage insurance policy"
→ Find relevant policy PDFs based on content
```

### 2. **Word Document Retrieval**
Finding similar claims reports and guidelines
```python
Query: "catastrophe reinsurance treaty"
→ Retrieve matching Word documents
```

### 3. **Image-to-Image Similarity**
Finding visually similar damage photos
```python
Query: [hurricane_damage_001.png]
→ Find photos with similar visual patterns
```

### 4. **Text-to-Image Search (Cross-Modal)**
Finding images from text descriptions
```python
Query: "severe storm damage photos"
→ Find matching damage assessment images
```

### 5. **Filtered Image Search** (Weaviate-specific)
Combining semantic search with metadata filters
```python
Query: "flood damage" + filters(damage_type="flood", severity>=0.7)
→ Filtered multi-modal search
```

---

## Comparison Criteria

- **Query Performance**: Speed across different modalities (PDF, Word, Image)
- **Embedding Handling**: Support for different embedding dimensions (384 vs 512)
- **Cross-Modal Search**: Text-to-image search capabilities
- **Filtered Search**: Vector search + metadata filtering
- **Ease of Setup**: Integration with CLIP, document processing libraries
- **Collection Management**: Handling multiple collections with different schemas

---

## Quick Setup

### 🚀 5-Minute Start

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start databases
docker compose up -d

# 3. Generate multi-modal data
cd scripts
python generate_multimodal_data.py --type all

# 4. Process and create embeddings
python process_multimodal_data.py

# 5. Run Phase 2 comparison
python benchmark_multimodal.py
```

**Expected runtime**: 15-20 minutes (includes CLIP model download)

---

## 📖 Guides Available

- **[QUICKSTART.md](QUICKSTART.md)** - Complete Phase 2 setup guide
- **[STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md)** - Detailed walkthrough with explanations
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commands & metrics cheat sheet
- **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** - Implementation summary and results

---

## Project Structure

```
.
├── docker-compose.yml          # Run Milvus and Weaviate
├── requirements.txt            # Python dependencies (includes Phase 2 libs)
├── README.md                   # This file (Phase 2)
├── QUICKSTART.md               # Phase 2 setup guide
├── STEP_BY_STEP_GUIDE.md       # Phase 2 detailed walkthrough
├── QUICK_REFERENCE.md          # Phase 2 commands reference
├── SESSION_SUMMARY.md          # Phase 2 implementation summary
├── data/
│   └── multimodal/             # Generated multi-modal data
│       ├── pdfs/               # 100 PDF files
│       ├── word/               # 50 Word documents
│       ├── images/             # 200 damage photos
│       └── processed/          # Processed data with embeddings
├── scripts/
│   ├── generate_multimodal_data.py      # Generate PDFs, Word docs, images
│   ├── process_multimodal_data.py       # Extract text, generate embeddings
│   ├── milvus_multimodal_client.py      # Milvus multi-modal operations
│   ├── weaviate_multimodal_client.py    # Weaviate multi-modal operations
│   └── benchmark_multimodal.py          # Phase 2 benchmarking
└── results/
    └── phase2_benchmark_results.json    # Benchmark results
```

---

## Phase 2 Results

After running the comparison, you'll get comprehensive metrics:

### 🏆 Winner Summary (Milvus wins 3 out of 4 categories)

| Test Category | Milvus | Weaviate | Winner | Advantage |
|--------------|--------|----------|--------|-----------|
| **PDF Search** | 2.92ms | 3.16ms | **Milvus** | 7.4% faster |
| **Word Search** | 3.16ms | 2.79ms | **Weaviate** | 13.4% faster |
| **Image-to-Image** | 1.03ms | 1.66ms | **Milvus** | 37.6% faster |
| **Text-to-Image** | 2.67ms | 2.87ms | **Milvus** | 6.9% faster |

**Key Insights**:
- **Milvus** excels at image search (CLIP embeddings) - 37.6% faster
- **Weaviate** better for text documents with filtering
- Both handle multi-modal data efficiently (all queries < 5ms)
- Collection management easier in Weaviate

See [SESSION_SUMMARY.md](SESSION_SUMMARY.md) for detailed analysis.

---

## Key Technologies

### Embedding Models
- **Sentence Transformers**: `all-MiniLM-L6-v2` (384 dims) - Text embeddings
- **CLIP**: `openai/clip-vit-base-patch32` (512 dims) - Image embeddings

### Document Processing
- **ReportLab**: PDF generation with tables and charts
- **pdfplumber**: PDF text and table extraction
- **python-docx**: Word document generation and reading
- **PIL/Pillow**: Image generation and manipulation

### Data Generation
- **matplotlib + seaborn**: Chart generation for documents
- **Faker**: Realistic business data
- **NumPy**: Random data generation

---

## Data Volume

- **100 PDF documents** (~50KB each, with tables and charts)
- **50 Word documents** (~30KB each, professionally formatted)
- **200 images** (~10KB each, synthetic damage photos)
- **Total**: 350 multi-modal documents
- **Total embeddings**: 350 documents × (384 or 512 dims)

---

## Viewing Your Data

Phase 2 includes interactive data viewers:

```bash
# Browse Milvus collections interactively
cd scripts
python database_browser.py

# Browse Weaviate collections
python check_db_status.py

# Quick visualization demo
python quick_viz_demo.py
```

See [VIEW_DATA_GUIDE.md](VIEW_DATA_GUIDE.md) for detailed instructions.

---

## Troubleshooting

### Out of Memory During CLIP Loading
```bash
# CLIP model is ~600MB, ensure enough RAM
# Reduce batch size in process_multimodal_data.py if needed
```

### PDF/Word Generation Issues
```bash
# Ensure all dependencies installed
pip install reportlab pdfplumber python-docx pillow

# Check write permissions
ls -la data/multimodal/
```

### Port Conflicts
If ports 8080, 19530, or 8000 are in use, edit `docker-compose.yml`.

### Slow Image Processing
```bash
# Use GPU if available (CLIP will auto-detect CUDA)
# Otherwise, reduce number of images in generate_multimodal_data.py
```

---

## Cleanup

### Remove generated data (keep code)
```bash
rm -rf data/multimodal/
```

### Stop containers (keep data)
```bash
docker compose stop
```

### Remove everything
```bash
docker compose down -v
rm -rf data/multimodal/ results/phase2_*.json
```

---

## Differences from Phase 1

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| **Data Types** | Text only (JSON) | PDFs, Word docs, Images |
| **Embeddings** | Single type (384 dims) | Multiple types (384 + 512 dims) |
| **Collections** | 3 collections (same schema) | 3 collections (different schemas) |
| **Search Types** | Text semantic search | Multi-modal + cross-modal |
| **Models** | Sentence Transformers | Sentence Transformers + CLIP |
| **File Size** | ~2MB (JSON) | ~10MB (documents + images) |
| **Complexity** | Basic | Advanced |

---

## Next Steps

After running Phase 2:

1. ✅ **Analyze results** - Review `results/phase2_benchmark_results.json`
2. ✅ **Compare with Phase 1** - See how multi-modal affects performance
3. ✅ **Visualize embeddings** - Use visualization tools to see clusters
4. ✅ **Test real documents** - Replace synthetic data with actual files
5. ✅ **Scale testing** - Increase to 1000+ documents per type
6. ✅ **Deploy** - Choose winner and plan production deployment

---

## Additional Resources

- [Milvus Multi-Modal Documentation](https://milvus.io/docs/image_similarity_search.md)
- [Weaviate Multi-Modal Guide](https://weaviate.io/developers/weaviate/modules/retriever-vectorizer-modules/multi2vec-clip)
- [CLIP Paper](https://arxiv.org/abs/2103.00020)
- [Sentence Transformers](https://www.sbert.net/)

---

## Support

For issues or questions:
- Check the guides: QUICKSTART.md, STEP_BY_STEP_GUIDE.md
- Review script source code for implementation details
- Check Docker logs: `docker compose logs milvus` or `docker compose logs weaviate`
- Examine processed data: `data/multimodal/processed/*.json`

---

**Phase**: 2 (Multi-Modal)
**Status**: ✅ Complete
**Branch**: `phase2`
**Last Updated**: 2025-11-15
