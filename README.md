# Milvus vs Weaviate POC for Reinsurance AI

A comprehensive comparison of Milvus and Weaviate vector databases for reinsurance business use cases.

## Architecture

```
┌─────────────────────────────────────────┐
│        Your Local Machine               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Python Scripts                │   │
│  │  - generate_data.py             │   │
│  │  - milvus_client.py             │   │
│  │  - weaviate_client.py           │   │
│  │  - benchmark.py                 │   │
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
│  └─────────────────────┘               │
│                                         │
│  ┌─────────────────────┐               │
│  │   Weaviate :8080    │               │
│  └─────────────────────┘               │
└───────────────────────────────────────┘
```

**Hybrid Approach**: Databases run in Docker, Python scripts run locally for easy development.

## Use Cases Tested

1. **Document/Policy Search**: Semantic search across insurance policies and contracts
2. **Claims Similarity**: Finding similar historical claims for fraud detection and pricing
3. **Knowledge Retrieval**: RAG system for regulatory compliance and underwriting guidelines

## Comparison Criteria

- **Query Performance**: Speed of semantic search and similarity queries
- **Scalability**: Handling large volumes of insurance data
- **Feature Richness**: Filtering, hybrid search, multi-tenancy capabilities
- **Ease of Setup**: Developer experience and integration complexity

## Quick Setup

### 🚀 5-Minute Start

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start databases
docker compose up -d

# 3. Run comparison
cd scripts
AUTO_RUN=1 python run_comparison.py
```

### 📖 Guides Available

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commands & metrics cheat sheet
- **[STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md)** - Detailed walkthrough explaining what happens under the hood
- **[QUICKSTART.md](QUICKSTART.md)** - Complete setup guide

## Project Structure

```
.
├── docker-compose.yml          # Run Milvus and Weaviate
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── QUICKSTART.md               # Step-by-step setup guide
├── data/                       # Generated synthetic data
├── scripts/
│   ├── generate_data.py       # Generate synthetic reinsurance data
│   ├── milvus_client.py       # Milvus operations
│   ├── weaviate_client.py     # Weaviate operations
│   ├── benchmark.py           # Performance benchmarking
│   └── run_comparison.py      # Main comparison script
├── examples/                   # 🆕 Practical Weaviate implementations
│   ├── README.md              # Examples documentation
│   ├── weaviate_reinsurance_examples.py  # 7 real-world scenarios
│   └── rag_with_llm.py        # Complete RAG system with LLM
└── results/                    # Benchmark results and reports
```

## Results

Results will be generated in the `results/` directory after running the comparison.

## Practical Examples

After running the comparison, explore the `examples/` directory for real-world Weaviate implementations:

### 🎯 `weaviate_reinsurance_examples.py`

7 production-ready scenarios:
- **RAG System**: Answer questions about policies and claims
- **Semantic Search**: Find similar policies for pricing
- **Fraud Detection**: Identify suspicious claim patterns
- **Portfolio Analysis**: Risk concentration analysis
- **Compliance Search**: Hybrid search for regulatory terms
- **Knowledge Base**: Query underwriting guidelines

```bash
python examples/weaviate_reinsurance_examples.py
```

### 🤖 `rag_with_llm.py`

Complete RAG pipeline with LLM integration:
- Retrieve context from Weaviate (2-5ms)
- Generate answers with GPT-4/Claude
- Return structured responses with sources
- Mock mode (no API key needed) or real LLM

```bash
python examples/rag_with_llm.py
```

See [examples/README.md](examples/README.md) for detailed documentation.
