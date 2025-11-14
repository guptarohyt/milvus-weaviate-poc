# Quick Start Guide

This guide will help you get the Milvus vs Weaviate POC up and running quickly.

## Architecture Overview

This POC uses a **hybrid approach**:
- **Vector Databases** (Milvus & Weaviate): Run in Docker containers
- **Python Scripts** (data generation, benchmarking): Run on your host machine

This approach allows easy development and debugging while keeping the databases isolated in containers.

## Prerequisites

- Docker and Docker Compose installed
- **Python 3.8 or higher** (for running the comparison scripts on your machine)
- 8GB+ RAM recommended

## Step 1: Create Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

This installs Python packages in an isolated environment:
- **Milvus and Weaviate clients** - Connect to databases running in Docker
- **Sentence transformers** - Generate embeddings for semantic search
- **Data generation utilities** - Create synthetic reinsurance data

**Why virtual environment?** Isolates dependencies from your system Python and other projects, preventing version conflicts.

**Why local install?** The Python scripts run on your machine and connect to the databases in Docker (like connecting to a remote database). This makes it easy to modify scripts and re-run tests without rebuilding containers.

## Step 2: Start Vector Databases (Docker)

```bash
docker compose up -d
```

This starts:
- **Milvus** (port 19530) with supporting services (etcd, MinIO)
- **Weaviate** (port 8080)

Wait ~30 seconds for services to be ready.

Check container status:
```bash
docker compose ps
```

## Step 3: Run the Complete Comparison (Local Python)

**Important:** Make sure your virtual environment is activated before running scripts!
```bash
# If not already activated:
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

cd scripts
python run_comparison.py
```

This Python script (running on your machine) will:
1. Check if Docker containers are running
2. Generate synthetic reinsurance data (policies, claims, knowledge base)
3. Connect to Milvus and Weaviate containers to load data
4. Run comprehensive benchmarks against both databases
5. Generate comparison report

**Expected runtime**: 5-10 minutes depending on your machine

**What's happening:** Your local Python script connects to `localhost:19530` (Milvus) and `localhost:8080` (Weaviate) to perform all operations.

## Alternative: Run Steps Individually

### Generate Data Only
```bash
cd scripts
python generate_data.py
```

### Test Milvus Only
```bash
python milvus_client.py
```

### Test Weaviate Only
```bash
python weaviate_client.py
```

### Run Benchmarks Only (after data is loaded)
```bash
python benchmark.py
```

## Understanding the Results

After running the comparison, check:

1. **Console output** - Summary comparison printed at the end
2. **results/benchmark_results.json** - Detailed metrics in JSON format

### Key Metrics Compared

- **Query Performance**: Average search time across use cases
- **Setup Time**: Time to create collections and insert data
- **Filtered Search**: Performance with attribute filters
- **Hybrid Search**: Weaviate's vector + keyword search
- **Feature Richness**: Supported capabilities
- **Ease of Use**: Developer experience evaluation

## Example Queries

The POC tests these reinsurance-specific scenarios:

**Policy Search**:
- "property catastrophe coverage for hurricane events"
- "cyber risk reinsurance for financial institutions"
- "professional liability coverage for healthcare providers"

**Claims Similarity**:
- "flood damage to commercial property"
- "cyber attack data breach incident"
- "professional negligence medical malpractice"

**Knowledge Retrieval**:
- "underwriting guidelines for catastrophe risk assessment"
- "regulatory compliance requirements for reinsurance"
- "claims handling procedures for large losses"

## Troubleshooting

### Containers won't start
```bash
# Check Docker is running
docker info

# Check logs
docker compose logs milvus
docker compose logs weaviate

# Restart containers
docker compose down
docker compose up -d
```

### Port conflicts
If ports 8080 or 19530 are already in use, edit `docker-compose.yml` to use different ports.

### Out of memory
Reduce data size in `benchmark.py`:
```python
runner.setup(data_size=500)  # Default is 1000
```

### Connection errors
Ensure containers are fully started:
```bash
# Check container health
docker compose ps

# Wait and retry
sleep 30
python run_comparison.py
```

## Cleanup

### Stop containers (keep data)
```bash
docker compose stop
```

### Remove everything (including data)
```bash
docker compose down -v
rm -rf data/ results/
```

## Next Steps

1. **Customize data generation** - Edit `generate_data.py` to match your domain
2. **Add new queries** - Modify `benchmark.py` to test specific scenarios
3. **Test with real data** - Replace synthetic data with actual reinsurance data
4. **Scale testing** - Increase data size to test at production scale
5. **Deploy** - Use docker compose as base for production deployment

## Want a Fully Dockerized Setup?

If you prefer not to install Python locally, you can containerize the Python scripts too:

1. Create a `Dockerfile` for the scripts
2. Add a `python-runner` service to `docker-compose.yml`
3. Mount the scripts directory as a volume
4. Run everything with `docker compose run python-runner python scripts/run_comparison.py`

This requires more Docker knowledge but eliminates local Python dependencies.

## Additional Resources

- [Milvus Documentation](https://milvus.io/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Sentence Transformers](https://www.sbert.net/)

## Support

For issues or questions:
- Check the main README.md
- Review docker-compose.yml for configuration
- Examine script source code for implementation details
