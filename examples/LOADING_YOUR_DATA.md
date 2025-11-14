# Step-by-Step Guide: Loading Your Real Reinsurance Data

This guide walks you through loading your actual data into Weaviate.

## 🎯 Quick Start (5 Minutes)

### Step 1: Prepare Your Data File

Export your data to CSV with these columns:

**For Policies:**
```csv
policy_id,policy_type,cedent,territory,limit,premium,inception_date,expiry_date,description
```

**For Claims:**
```csv
claim_id,category,status,peril,loss_amount,location,loss_date,description
```

### Step 2: Run the Loader

```bash
cd examples
python load_real_data.py
```

The script will:
1. Create sample CSV (for testing)
2. Load it into Weaviate
3. Verify the data

### Step 3: Test Search

```bash
python weaviate_reinsurance_examples.py
```

This tests all search scenarios with your data!

## 📋 Detailed Process

### Option A: You Have CSV/Excel Files

1. **Place your file in the examples directory:**
   ```bash
   cp /path/to/your/policies.csv examples/
   ```

2. **Create a custom loader script:**
   ```python
   # my_data_loader.py
   import sys
   sys.path.insert(0, '../scripts')
   from load_real_data import RealDataLoader
   from weaviate_client import WeaviateReinsuranceClient

   # Connect
   client = WeaviateReinsuranceClient()
   client.connect()
   client.create_collections()

   # Load
   loader = RealDataLoader(client)
   loader.load_policies_from_csv('policies.csv')
   loader.load_claims_from_excel('claims.xlsx', sheet_name='Claims')

   client.disconnect()
   ```

3. **Run it:**
   ```bash
   python my_data_loader.py
   ```

### Option B: You Have a SQL Database

1. **Install SQLAlchemy:**
   ```bash
   pip install sqlalchemy pyodbc  # For SQL Server
   # or
   pip install sqlalchemy psycopg2  # For PostgreSQL
   ```

2. **Create loader with your connection string:**
   ```python
   # database_loader.py
   from load_real_data import RealDataLoader
   from weaviate_client import WeaviateReinsuranceClient

   client = WeaviateReinsuranceClient()
   client.connect()
   client.create_collections()

   loader = RealDataLoader(client)

   # Your database connection
   connection_string = "postgresql://user:pass@localhost:5432/reinsurance"

   # Your SQL query
   query = """
       SELECT
           policy_number as policy_id,
           product_line as policy_type,
           client_name as cedent,
           coverage_territory as territory,
           policy_limit as limit,
           annual_premium as premium,
           effective_date as inception_date,
           expiration_date as expiry_date,
           coverage_notes as description
       FROM policies
       WHERE status = 'Active'
   """

   loader.load_policies_from_database(connection_string, query)

   client.disconnect()
   ```

### Option C: You Have a REST API

```python
# api_loader.py
from load_real_data import RealDataLoader
from weaviate_client import WeaviateReinsuranceClient

client = WeaviateReinsuranceClient()
client.connect()
client.create_collections()

loader = RealDataLoader(client)

# Your API endpoint
api_url = "https://your-system.com/api/policies"

# Your auth headers
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

loader.load_policies_from_api(api_url, headers)

client.disconnect()
```

## 🔧 Field Mapping

If your field names don't match exactly, create a transformation function:

```python
def transform_your_data(row):
    """Map your fields to Weaviate schema."""
    return {
        "id": row['YourPolicyID'],           # Map to 'id'
        "policy_type": row['LineOfBusiness'], # Map to 'policy_type'
        "cedent": row['ClientName'],          # Map to 'cedent'
        "territory": row['Region'],           # Map to 'territory'
        "limit": float(row['SumInsured']),    # Map to 'limit'
        "premium": float(row['Premium']),     # Map to 'premium'
        "inception_date": row['StartDate'],   # Map to 'inception_date'
        "expiry_date": row['EndDate'],        # Map to 'expiry_date'
        "description": f"{row['Notes']} {row['Coverage']}"  # Combine fields
    }

# Apply transformation
df = pd.read_csv('your_data.csv')
policies = [transform_your_data(row) for _, row in df.iterrows()]

# Load
loader = RealDataLoader(client)
loader.load_in_batches(policies, data_type="policy", batch_size=1000)
```

See [FIELD_MAPPING.md](FIELD_MAPPING.md) for complete mapping guide.

## ✅ Validation & Testing

### 1. Start Small

Always test with a small sample first:

```python
# Load only first 100 records
df = pd.read_csv('policies.csv').head(100)
policies = [transform_policy(row) for _, row in df.iterrows()]
loader.load_in_batches(policies, batch_size=100)
```

### 2. Verify Data Quality

```python
# Check what got loaded
stats = client.get_stats()
print(f"Policies loaded: {stats['Policy']['count']}")

# Test a search
results = client.search_policies("test query", limit=5)
for r in results['results']:
    print(r['properties'])
```

### 3. Test Search Quality

```python
# Try real queries your users would ask
test_queries = [
    "property catastrophe policies",
    "cyber risk coverage",
    "large flood claims"
]

for query in test_queries:
    results = client.search_policies(query, limit=3)
    print(f"\nQuery: {query}")
    print(f"Found: {len(results['results'])} results")
    for r in results['results'][:2]:
        print(f"  - {r['properties']['policy_id']}: {r['score']:.3f}")
```

## 📊 Loading Large Datasets

### For 10,000+ Records

Use batch loading with progress:

```python
from tqdm import tqdm
import pandas as pd

# Read in chunks
chunk_size = 5000
total_loaded = 0

for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    print(f"\nProcessing chunk: {len(chunk)} records")

    # Transform
    policies = [transform_policy(row) for _, row in chunk.iterrows()]

    # Load in batches
    loader.load_in_batches(policies, batch_size=1000)

    total_loaded += len(policies)
    print(f"Total loaded so far: {total_loaded}")

print(f"\n✓ Loaded {total_loaded} total records")
```

### For 100,000+ Records

Consider parallel processing:

```python
from multiprocessing import Pool
import numpy as np

def process_chunk(chunk_data):
    """Process one chunk (runs in parallel)."""
    policies = []
    for row in chunk_data:
        policies.append(transform_policy(row))
    return policies

# Read all data
df = pd.read_csv('very_large_file.csv')

# Split into chunks for parallel processing
num_workers = 4
chunks = np.array_split(df.to_dict('records'), num_workers)

# Process in parallel
with Pool(num_workers) as pool:
    results = pool.map(process_chunk, chunks)

# Flatten results
all_policies = [p for chunk in results for p in chunk]

# Load in batches
loader.load_in_batches(all_policies, batch_size=1000)
```

## 🚨 Common Issues & Solutions

### Issue 1: Missing Required Fields

**Error**: `KeyError: 'policy_id'`

**Solution**: Ensure all required fields are mapped:
```python
required_fields = ['id', 'policy_type', 'cedent', 'description', 'limit', 'premium']

for field in required_fields:
    if field not in policy:
        print(f"Missing field: {field}")
        # Add default or map from your data
```

### Issue 2: Slow Loading

**Problem**: Loading 10,000 records takes too long

**Solution**: Use batch loading:
```python
# Instead of:
for policy in policies:
    client.insert_policies([policy])  # ❌ Slow

# Do:
loader.load_in_batches(policies, batch_size=1000)  # ✅ Fast
```

### Issue 3: Bad Search Results

**Problem**: Search doesn't find relevant policies

**Solution**: Improve your descriptions:
```python
# ❌ Bad: Just the ID
description = row['policy_id']

# ✅ Good: Rich, descriptive text
description = (
    f"{row['policy_type']} reinsurance for {row['cedent']} "
    f"covering {row['territory']}. "
    f"Limit: ${row['limit']:,.0f}. "
    f"Perils: {', '.join(row['perils'])}. "
    f"{row['notes']}"
)
```

### Issue 4: Duplicate IDs

**Error**: `Duplicate key error`

**Solution**: Ensure IDs are unique:
```python
# Check for duplicates before loading
df = pd.read_csv('policies.csv')
duplicates = df[df.duplicated(subset=['policy_id'], keep=False)]

if len(duplicates) > 0:
    print(f"Found {len(duplicates)} duplicates:")
    print(duplicates[['policy_id']])

    # Option 1: Remove duplicates
    df = df.drop_duplicates(subset=['policy_id'], keep='first')

    # Option 2: Add suffix to make unique
    df['policy_id'] = df['policy_id'] + '_' + df.groupby('policy_id').cumcount().astype(str)
```

## 🎓 Complete Example

Here's a complete working example:

```python
#!/usr/bin/env python3
"""
Complete example: Load your reinsurance data into Weaviate
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pandas as pd
from weaviate_client import WeaviateReinsuranceClient
from load_real_data import RealDataLoader


def transform_policy(row):
    """Transform your data format to Weaviate format."""
    return {
        "id": str(row['PolicyNumber']),
        "policy_type": str(row['LineOfBusiness']),
        "cedent": str(row['InsuredName']),
        "territory": str(row['Territory']),
        "limit": float(row['CoverageLimit']),
        "premium": float(row['AnnualPremium']),
        "inception_date": str(row['EffectiveDate']),
        "expiry_date": str(row['ExpirationDate']),
        "description": (
            f"{row['LineOfBusiness']} policy for {row['InsuredName']}. "
            f"Coverage: {row['CoverageNotes']}"
        )
    }


def main():
    print("="*70)
    print("LOAD YOUR REINSURANCE DATA")
    print("="*70)

    # 1. Connect to Weaviate
    print("\n1. Connecting to Weaviate...")
    client = WeaviateReinsuranceClient()
    client.connect()

    # 2. Create collections
    print("2. Creating collections...")
    client.create_collections()

    # 3. Load your data
    print("3. Loading data from CSV...")
    df = pd.read_csv('YOUR_DATA.csv')

    print(f"   Found {len(df)} records")

    # 4. Transform
    print("4. Transforming data...")
    policies = []
    for _, row in df.iterrows():
        try:
            policy = transform_policy(row)
            policies.append(policy)
        except Exception as e:
            print(f"   Error transforming row: {e}")

    print(f"   Successfully transformed {len(policies)} policies")

    # 5. Load into Weaviate
    print("5. Loading into Weaviate...")
    loader = RealDataLoader(client)
    loader.load_in_batches(policies, batch_size=1000)

    # 6. Verify
    print("6. Verifying...")
    stats = client.get_stats()
    print(f"   Loaded {stats['Policy']['count']} policies")

    # 7. Test search
    print("7. Testing search...")
    results = client.search_policies("property catastrophe", limit=3)
    print(f"   Search returned {len(results['results'])} results")

    # 8. Done!
    client.disconnect()

    print("\n" + "="*70)
    print("✓ SUCCESS!")
    print("="*70)
    print(f"\nYour data is now in Weaviate!")
    print(f"\nNext: Run examples to search your data:")
    print(f"  python weaviate_reinsurance_examples.py")


if __name__ == "__main__":
    main()
```

## 📚 Reference

- **load_real_data.py** - Data loading utilities
- **FIELD_MAPPING.md** - Complete field mapping reference
- **weaviate_client.py** - Weaviate client implementation
- **weaviate_reinsurance_examples.py** - Search examples

## 🆘 Need Help?

1. Check [FIELD_MAPPING.md](FIELD_MAPPING.md) for field mapping
2. Review examples in `load_real_data.py`
3. Start with small sample (100 records)
4. Test search quality before loading full dataset

## Next Steps

After loading your data:

1. ✅ **Test searches** - Run `weaviate_reinsurance_examples.py`
2. ✅ **Try RAG** - Run `rag_with_llm.py`
3. ✅ **Build UI** - Create a web interface for your team
4. ✅ **Deploy** - Move to production (see main README)
