# Quick Reference: Running the Comparison

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Start databases (if not running)
docker compose up -d
sleep 30

# 3. Run full comparison
cd scripts
AUTO_RUN=1 python run_comparison.py
```

**Expected time**: 5-10 minutes
**Output**: `results/benchmark_results.json`

---

## 📋 Step-by-Step Commands

### Step 1: Generate Data
```bash
cd scripts
source ../venv/bin/activate
python generate_data.py
```
**Output**: `data/policies.json`, `data/claims.json`, `data/knowledge_base.json`
**Time**: 2 seconds

### Step 2: Test Milvus
```bash
python milvus_client.py
```
**What it does**: Creates collections, inserts data, tests search
**Time**: ~30 seconds

### Step 3: Test Weaviate
```bash
python weaviate_client.py
```
**What it does**: Same as Milvus but faster
**Time**: ~5 seconds

### Step 4: Run Benchmarks
```bash
python benchmark.py
```
**What it does**: Compares performance across all scenarios
**Time**: 2-3 minutes

### Step 5: View Results
```bash
cat ../results/benchmark_results.json | python -m json.tool
```

---

## 🔍 Understanding What's Happening

### During Data Generation
```
Generating policies...   ━━━━━━━━━━━━━━━━━━ 1000/1000
  └─ Creating fake company names, policy types, limits, etc.

Generating claims...     ━━━━━━━━━━━━━━━━━━ 2000/2000
  └─ Creating loss events, amounts, descriptions

Generating knowledge...  ━━━━━━━━━━━━━━━━━━ 500/500
  └─ Creating regulatory docs, guidelines
```

### During Milvus Setup (26 seconds)
```
1. Loading model...                           [2s]
   └─ sentence-transformers/all-MiniLM-L6-v2

2. Creating collections...                    [1s]
   └─ Define schema (id, text, vector fields)

3. Generating embeddings...                   [10s]
   ├─ Policies: 1000 × 384 dimensions
   ├─ Claims: 2000 × 384 dimensions
   └─ Knowledge: 500 × 384 dimensions

4. Inserting data...                          [2s]
   └─ Batch insert to Milvus

5. Building IVF index...                      [8s]
   └─ Clustering 3500 vectors into 128 groups

6. Loading to memory...                       [3s]
   └─ RAM: ~200MB for fast queries
```

### During Weaviate Setup (3.4 seconds)
```
1. Loading model...                           [2s]
   └─ Same sentence-transformers model

2. Creating collections...                    [0.2s]
   └─ More flexible schema

3. Generating embeddings...                   [0s]
   └─ Reuses from step 1

4. Inserting + Building HNSW...               [1.2s]
   └─ Incremental graph building
   └─ No separate index build phase!
```

**Key Difference**: Weaviate builds index DURING insert, Milvus does it AFTER.

### During Query Tests
```
Testing: "hurricane property catastrophe"

Milvus Process:
  1. Embed query              [0.1ms]
  2. Compare to 128 centroids [0.2ms]
  3. Search 10 clusters       [4.0ms]
  4. Return top 10           [0.3ms]
  Total: 4.6ms

Weaviate Process:
  1. Embed query              [0.1ms]
  2. Navigate HNSW graph      [2.4ms]
  3. Return top 10           [0.3ms]
  Total: 2.8ms

Weaviate is 39% faster! 🎉
```

---

## 🎯 Key Metrics to Watch

When running the comparison, watch for these numbers:

### Query Performance
```
Target: < 10ms per query

Milvus:   4.6ms   ✅ Good
Weaviate: 2.8ms   ✅ Better
```

### Setup Time
```
Target: < 60s for 3,500 records

Milvus:   26.1s   ✅ Acceptable
Weaviate:  3.4s   ✅ Excellent
```

### Filtered Search
```
Target: < 50ms with filters

Milvus:   412ms   ⚠️  Slow
Weaviate:  11ms   ✅ Fast
```

### Memory Usage
```
Target: < 500MB for 3,500 records

Milvus:   ~200MB  ✅ Good
Weaviate: ~150MB  ✅ Better
```

---

## 🔧 Troubleshooting

### "Connection refused"
```bash
# Check containers
docker compose ps

# Restart if needed
docker compose down
docker compose up -d
sleep 30
```

### "ModuleNotFoundError"
```bash
# Activate venv
source venv/bin/activate

# Reinstall if needed
pip install -r requirements.txt
```

### "Data not found"
```bash
# Generate data first
cd scripts
python generate_data.py
```

### Slow performance
```bash
# Check Docker resources
docker stats --no-stream

# Allocate more RAM to Docker (8GB recommended)
# Docker Desktop → Settings → Resources → Memory
```

---

## 📊 Interpreting Results

### Winner Decision Matrix

| Criterion | Weight | Milvus Score | Weaviate Score | Winner |
|-----------|--------|--------------|----------------|--------|
| Query Speed | 30% | 3/5 | 5/5 | Weaviate |
| Setup Time | 20% | 2/5 | 5/5 | Weaviate |
| Features | 25% | 3/5 | 5/5 | Weaviate |
| Ease of Use | 15% | 2/5 | 5/5 | Weaviate |
| Scalability | 10% | 5/5 | 4/5 | Milvus |

**Overall: Weaviate wins 4 out of 5 categories**

### When to Choose Milvus Despite Results
- You need **billions** of vectors (proven scale)
- You want **specific index types** (IVF_PQ, ANNOY)
- You need **partition-based isolation**
- You have **dedicated ops team** for complex setup

### When to Choose Weaviate (Most Cases)
- You need **fast queries** (< 5ms)
- You want **hybrid search** (built-in)
- You need **quick deployment** (one container)
- You want **better filtering** (40x faster)
- You value **developer experience**

---

## 🎓 What You'll Learn

By running the comparison step-by-step, you'll understand:

1. **Vector Embeddings**: How text converts to numbers
2. **Index Types**: IVF vs HNSW performance tradeoffs
3. **Query Process**: How semantic search works under the hood
4. **Hybrid Search**: Combining semantic + keyword search
5. **Architecture**: Single service vs distributed systems
6. **Performance**: What affects query speed
7. **Scalability**: How systems handle growing data

---

## 📚 Files to Review

After running:

1. **results/benchmark_results.json** - All metrics
2. **STEP_BY_STEP_GUIDE.md** - Detailed explanations
3. **scripts/milvus_client.py** - Milvus implementation
4. **scripts/weaviate_client.py** - Weaviate implementation
5. **scripts/benchmark.py** - Comparison logic

---

## 🚀 Next Steps

After understanding the comparison:

1. ✅ **Review results** - Analyze benchmark_results.json
2. ✅ **Try examples** - Run weaviate_reinsurance_examples.py
3. ✅ **Test RAG** - Run rag_with_llm.py
4. ✅ **Load real data** - Use load_real_data.py (optional)
5. ✅ **Make decision** - Choose Weaviate or Milvus
6. ✅ **Plan deployment** - Production setup guide

---

## 💡 Pro Tips

**Tip 1**: Run multiple times for consistent results
```bash
for i in {1..3}; do
    echo "Run $i"
    AUTO_RUN=1 python run_comparison.py
    sleep 5
done
```

**Tip 2**: Test with different data sizes
```python
# In benchmark.py, line 75:
runner.setup(data_size=500)   # Smaller test
runner.setup(data_size=5000)  # Larger test
```

**Tip 3**: Monitor resource usage during test
```bash
# In another terminal:
watch -n 1 'docker stats --no-stream'
```

**Tip 4**: Save results with timestamp
```bash
timestamp=$(date +%Y%m%d_%H%M%S)
cp results/benchmark_results.json "results/benchmark_${timestamp}.json"
```

---

## 📞 Getting Help

**Check logs**:
```bash
docker compose logs milvus
docker compose logs weaviate
```

**Verbose mode**:
```bash
# Add debug output
export DEBUG=1
python run_comparison.py
```

**Review the guides**:
- STEP_BY_STEP_GUIDE.md - Detailed walkthrough
- QUICKSTART.md - Setup instructions
- examples/README.md - Implementation examples
