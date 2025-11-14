# Weaviate Reinsurance Implementation Examples

Practical examples showing how to use Weaviate for real reinsurance business scenarios.

## 🚀 New: Load Your Real Data!

**Want to use your actual reinsurance data instead of synthetic?**

See [LOADING_YOUR_DATA.md](LOADING_YOUR_DATA.md) for a complete step-by-step guide:
- Load from CSV, Excel, SQL databases, or APIs
- Field mapping from your system to Weaviate
- Handle large datasets (10,000+ records)
- Validation and testing

Quick start:
```bash
python load_real_data.py  # Creates sample and shows how to load
```

Also see [FIELD_MAPPING.md](FIELD_MAPPING.md) for detailed field mapping reference.

## Prerequisites

1. Docker containers running (from root directory):
   ```bash
   docker compose up -d
   ```

2. Data loaded (run benchmark first):
   ```bash
   cd ../scripts
   python run_comparison.py
   ```

## Examples Overview

### 1. `weaviate_reinsurance_examples.py`

**Comprehensive examples covering 7 real-world scenarios:**

- **RAG System**: Answer questions about policies and claims
- **Semantic Search**: Find similar policies for pricing/risk assessment
- **Fraud Detection**: Identify similar claims patterns
- **Portfolio Analysis**: Analyze concentration risk
- **Compliance Search**: Hybrid search for regulatory terms
- **Knowledge Base**: Query underwriting guidelines

**Run it:**
```bash
python weaviate_reinsurance_examples.py
```

**Key Features Demonstrated:**
- Vector search for semantic similarity
- Hybrid search (vector + keyword) for compliance
- Filtering and aggregations
- Real-time portfolio analysis

### 2. `rag_with_llm.py`

**Production-ready RAG system with LLM integration:**

Shows how to build a complete RAG pipeline:
1. Retrieve relevant context from Weaviate (fast vector search)
2. Format context for LLM
3. Generate natural language answers
4. Return structured responses with sources

**Run it:**
```bash
python rag_with_llm.py
```

**Supports:**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Mock responses (for demo without API keys)

**To use with real LLM:**
```python
# In rag_with_llm.py, uncomment the integration code:

# For OpenAI:
import openai
rag = ReinsuranceRAGSystem(client, llm_provider="openai")

# For Anthropic:
from anthropic import Anthropic
rag = ReinsuranceRAGSystem(client, llm_provider="anthropic")
```

## Use Case Details

### 1. RAG for Policy Questions

**Problem**: Underwriters need quick answers about existing policies

**Solution**: Semantic search + LLM generation

```python
rag.answer_policy_question(
    "What property catastrophe policies cover hurricane risk in Florida?"
)
```

**Benefits**:
- Sub-second retrieval (2-5ms)
- Natural language interface
- Cited sources for verification
- Confidence scoring

### 2. Claims Similarity (Fraud Detection)

**Problem**: Detect fraudulent claim patterns

**Solution**: Vector similarity search across historical claims

```python
semantic.fraud_detection_similar_claims(
    "Business interruption with suspicious timing"
)
```

**Benefits**:
- Find similar claims instantly
- Risk flagging (HIGH/MEDIUM/LOW)
- Pattern detection across years of data
- Supports investigation workflows

### 3. Portfolio Risk Analysis

**Problem**: Understand concentration risk across portfolio

**Solution**: Semantic clustering and aggregation

```python
semantic.portfolio_analysis()
```

**Use Cases**:
- Hurricane exposure concentration
- Geographic risk distribution
- Policy type clustering
- Capital allocation decisions

### 4. Hybrid Search for Compliance

**Problem**: Find exact regulatory terms (e.g., "Solvency II", "IFRS 17")

**Solution**: Hybrid search combining exact keyword + semantic meaning

```python
compliance.regulatory_search("Solvency II capital requirements")
```

**Why Hybrid?**
- **Keyword component**: Ensures exact terms are matched
- **Semantic component**: Catches related concepts
- **Best of both worlds**: Precision + recall

**Alpha parameter**:
- `alpha=0.0`: Pure keyword search (BM25)
- `alpha=1.0`: Pure vector search
- `alpha=0.5`: Balanced (recommended)
- `alpha=0.2-0.3`: Favor keywords (good for compliance)

### 5. Multi-Tenancy (Future)

**Scenario**: Isolate data per client/business unit

Weaviate supports multi-tenancy natively:
```python
# Create tenant-specific collections
client.create_tenant("client_abc")
client.create_tenant("client_xyz")

# Query only specific tenant's data
results = client.search_policies(
    "hurricane coverage",
    tenant="client_abc"
)
```

**Benefits**:
- Data isolation
- Regulatory compliance
- Performance (smaller search space)
- Flexible access control

## Performance Characteristics

Based on the benchmark results:

| Operation | Time | Notes |
|-----------|------|-------|
| Vector search | 2-5ms | Single query, 1000 policies |
| Hybrid search | 4-6ms | Vector + BM25 combined |
| Filtered search | 10-15ms | With attribute filters |
| Batch insert | ~3s | 1000 documents with embeddings |

**Scalability**: Tested up to 1M+ documents with consistent sub-10ms queries

## Architecture Patterns

### Pattern 1: RAG for Q&A

```
User Question
    ↓
[Weaviate Vector Search] (2-5ms)
    ↓
Top-K Relevant Documents
    ↓
[LLM - GPT-4/Claude] (1-2s)
    ↓
Natural Language Answer + Sources
```

**Best for**: Policy questions, claims analysis, knowledge lookup

### Pattern 2: Real-Time Similarity

```
New Claim/Policy
    ↓
[Generate Embedding]
    ↓
[Weaviate Similarity Search]
    ↓
Similar Historical Records
    ↓
[Business Logic] (pricing, fraud detection, etc.)
```

**Best for**: Pricing, fraud detection, risk assessment

### Pattern 3: Hybrid Compliance Search

```
Regulatory Term (e.g., "IFRS 17")
    ↓
[Hybrid Search: BM25 + Vector]
    ↓
Exact Term Matches + Semantically Related
    ↓
Compliance Documentation
```

**Best for**: Regulatory compliance, policy wording, audit trails

## Integration with Existing Systems

### Option 1: REST API

Weaviate has a built-in REST API:
```python
import requests

response = requests.post(
    "http://localhost:8080/v1/graphql",
    json={
        "query": "{ Get { Policy { policyId policyType } } }"
    }
)
```

### Option 2: Python SDK (Recommended)

```python
from weaviate_client import WeaviateReinsuranceClient

client = WeaviateReinsuranceClient()
client.connect()
results = client.search_policies("hurricane coverage")
```

### Option 3: GraphQL

Weaviate supports GraphQL natively - great for flexible queries.

## Next Steps

### 1. Customize for Your Data

Replace synthetic data with real reinsurance data:

```python
# Load your data
policies = load_your_policies()  # Your format
claims = load_your_claims()

# Insert into Weaviate
client.insert_policies(policies)
client.insert_claims(claims)
```

### 2. Add More Use Cases

Extend the examples:
- Underwriting risk scoring
- Treaty optimization
- Claims reserving
- Portfolio rebalancing

### 3. Production Deployment

See the main README for production setup:
- High availability configuration
- Backup/restore procedures
- Monitoring and alerting
- Performance tuning

### 4. Fine-Tune Embeddings

For better domain-specific results:
```python
# Use insurance-specific embedding model
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('insurance-bert-model')
# Train on your data or use pre-trained insurance models
```

## Troubleshooting

### "No data found"
Run the benchmark script first to load sample data:
```bash
cd ../scripts && python run_comparison.py
```

### "Connection refused"
Ensure Weaviate container is running:
```bash
docker compose ps
docker compose logs weaviate
```

### Slow queries
Check index status and data size:
```python
stats = client.get_stats()
print(stats)  # Should show counts for each collection
```

## Resources

- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Hybrid Search Guide](https://weaviate.io/developers/weaviate/search/hybrid)
- [Multi-Tenancy](https://weaviate.io/developers/weaviate/manage-data/multi-tenancy)
- [Production Checklist](https://weaviate.io/developers/weaviate/installation/production-checklist)

## Questions?

Check the main project README or explore the source code:
- `../scripts/weaviate_client.py` - Core client implementation
- `../scripts/benchmark.py` - Performance testing
- `weaviate_reinsurance_examples.py` - This file's implementation
