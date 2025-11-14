# Field Mapping Guide for Real Reinsurance Data

This guide helps you map your existing data fields to Weaviate's schema.

## Required vs Optional Fields

### Policies

| Weaviate Field | Required | Type | Description | Common Source Fields |
|----------------|----------|------|-------------|---------------------|
| `id` | ✅ Yes | String | Unique policy identifier | `policy_id`, `policy_number`, `contract_id` |
| `policy_type` | ✅ Yes | String | Type of policy | `line_of_business`, `coverage_type`, `class` |
| `cedent` | ✅ Yes | String | Client/cedent name | `insured`, `client_name`, `cedent_name` |
| `description` | ✅ Yes | String | Policy description (for semantic search) | `notes`, `coverage_details`, `description` |
| `limit` | ✅ Yes | Number | Coverage limit | `policy_limit`, `sum_insured`, `coverage_amount` |
| `premium` | ✅ Yes | Number | Premium amount | `premium_amount`, `written_premium`, `earned_premium` |
| `territory` | ⬜ Optional | String | Geographic territory | `region`, `country`, `jurisdiction` |
| `inception_date` | ⬜ Optional | String | Policy start date | `effective_date`, `start_date`, `from_date` |
| `expiry_date` | ⬜ Optional | String | Policy end date | `termination_date`, `end_date`, `to_date` |

### Claims

| Weaviate Field | Required | Type | Description | Common Source Fields |
|----------------|----------|------|-------------|---------------------|
| `id` | ✅ Yes | String | Unique claim identifier | `claim_id`, `claim_number`, `loss_id` |
| `category` | ✅ Yes | String | Claim category | `loss_type`, `claim_type`, `category` |
| `status` | ✅ Yes | String | Claim status | `claim_status`, `state`, `current_status` |
| `description` | ✅ Yes | String | Claim description (for semantic search) | `loss_description`, `notes`, `details` |
| `loss_amount` | ✅ Yes | Number | Loss amount | `incurred_loss`, `paid_amount`, `claim_amount` |
| `peril` | ⬜ Optional | String | Type of peril | `cause_of_loss`, `peril_code`, `event_type` |
| `location` | ⬜ Optional | String | Loss location | `loss_location`, `city_state`, `address` |
| `loss_date` | ⬜ Optional | String | Date of loss | `date_of_loss`, `occurrence_date`, `event_date` |

### Knowledge Base

| Weaviate Field | Required | Type | Description | Common Source Fields |
|----------------|----------|------|-------------|---------------------|
| `id` | ✅ Yes | String | Unique article identifier | `document_id`, `article_id`, `kb_id` |
| `title` | ✅ Yes | String | Article title | `document_name`, `subject`, `title` |
| `content` | ✅ Yes | String | Article content (for semantic search) | `body`, `text`, `content`, `description` |
| `topic` | ⬜ Optional | String | Topic/category | `category`, `department`, `subject_area` |
| `author` | ⬜ Optional | String | Author name | `created_by`, `owner`, `author_name` |
| `created_date` | ⬜ Optional | String | Creation date | `date_created`, `publish_date`, `timestamp` |

## Example Transformations

### Example 1: Mapping from Legacy System

**Your Data**:
```python
{
    "contract_number": "RE-2024-001",
    "line": "Property",
    "insured_name": "ABC Corp",
    "sum_insured": 50000000,
    "premium": 2500000,
    "from_date": "01/01/2024",
    "to_date": "12/31/2024",
    "coverage": "Covers property damage from natural disasters..."
}
```

**Transformation Code**:
```python
def transform_legacy_policy(legacy_data):
    return {
        "id": legacy_data["contract_number"],
        "policy_type": legacy_data["line"],
        "cedent": legacy_data["insured_name"],
        "limit": legacy_data["sum_insured"],
        "premium": legacy_data["premium"],
        "inception_date": legacy_data["from_date"],
        "expiry_date": legacy_data["to_date"],
        "description": legacy_data["coverage"],
        "territory": "United States"  # Default if not in source
    }
```

### Example 2: Combining Multiple Fields

If your description is split across multiple fields:

```python
def create_rich_description(data):
    """Build comprehensive description from multiple fields."""
    parts = []

    # Add policy type and cedent
    parts.append(f"{data['policy_type']} reinsurance for {data['cedent']}")

    # Add coverage details
    if 'perils' in data:
        parts.append(f"Covering: {', '.join(data['perils'])}")

    # Add territory
    if 'territory' in data:
        parts.append(f"Territory: {data['territory']}")

    # Add limits
    parts.append(f"Limit: ${data['limit']:,.0f}")

    # Add original notes if available
    if 'notes' in data:
        parts.append(data['notes'])

    return ". ".join(parts)

# Use it:
policy["description"] = create_rich_description(legacy_data)
```

### Example 3: Handling Missing Fields

```python
def safe_transform(data, field_mappings):
    """Safely transform with defaults for missing fields."""
    result = {}

    for weaviate_field, (source_field, default) in field_mappings.items():
        if source_field in data:
            result[weaviate_field] = data[source_field]
        else:
            result[weaviate_field] = default

    return result

# Define mappings
mappings = {
    "id": ("policy_id", None),  # Required, no default
    "policy_type": ("class", "Unknown"),
    "territory": ("region", "Global"),
    "inception_date": ("start_date", "1900-01-01"),
}

policy = safe_transform(your_data, mappings)
```

## Data Type Conversions

### Dates

```python
from datetime import datetime

# Convert various date formats
def normalize_date(date_value):
    """Convert any date format to ISO string."""
    if isinstance(date_value, str):
        # Try common formats
        formats = [
            "%m/%d/%Y",  # 01/15/2024
            "%Y-%m-%d",  # 2024-01-15
            "%d-%b-%Y",  # 15-Jan-2024
            "%Y%m%d",    # 20240115
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_value, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    elif hasattr(date_value, 'strftime'):  # datetime object
        return date_value.strftime("%Y-%m-%d")

    return str(date_value)
```

### Numbers

```python
def normalize_amount(value):
    """Convert currency strings to numbers."""
    if isinstance(value, str):
        # Remove currency symbols and commas
        value = value.replace('$', '').replace(',', '').replace(' ', '')
    return float(value)
```

### Enumerations

```python
# Map your codes to readable names
STATUS_MAP = {
    "O": "Open",
    "C": "Closed",
    "P": "Pending",
    "R": "In Review"
}

def map_status(code):
    return STATUS_MAP.get(code, code)
```

## Common Data Sources

### 1. Excel with Multiple Sheets

```python
import pandas as pd

# Read specific sheets
excel_file = "reinsurance_data.xlsx"
policies_df = pd.read_excel(excel_file, sheet_name="Policies")
claims_df = pd.read_excel(excel_file, sheet_name="Claims")

# Load into Weaviate
loader.load_policies_from_csv(policies_df)  # Works with DataFrames too
```

### 2. SQL Server Database

```python
# Install: pip install pyodbc
connection_string = (
    "mssql+pyodbc://username:password@server/database"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)

query = """
    SELECT
        p.PolicyID as policy_id,
        p.LineOfBusiness as policy_type,
        c.ClientName as cedent,
        p.Territory as territory,
        p.Limit as limit,
        p.Premium as premium,
        p.InceptionDate as inception_date,
        p.ExpiryDate as expiry_date,
        CONCAT(p.Notes, ' ', p.CoverageDetails) as description
    FROM Policies p
    JOIN Clients c ON p.ClientID = c.ClientID
    WHERE p.Status = 'Active'
"""

loader.load_policies_from_database(connection_string, query)
```

### 3. REST API

```python
# If your system has a REST API
api_url = "https://your-system.com/api/v1/policies"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

# Custom transformation for API response
def transform_api_response(api_data):
    policies = []
    for item in api_data['results']:
        policy = {
            "id": item['policyNumber'],
            "policy_type": item['productLine'],
            "cedent": item['insuredName'],
            "limit": item['coverageLimit'],
            "premium": item['totalPremium'],
            "description": item['fullDescription'],
            # ... map other fields
        }
        policies.append(policy)
    return policies
```

### 4. CSV with Custom Delimiter

```python
# If your CSV uses semicolons or tabs
df = pd.read_csv('policies.csv', delimiter=';')
# or
df = pd.read_csv('policies.tsv', delimiter='\t')
```

## Performance Tips

### Batch Loading

For large datasets (10,000+ records):

```python
# Process in chunks to avoid memory issues
chunk_size = 1000

for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    policies = [transform_row(row) for _, row in chunk.iterrows()]
    loader.load_in_batches(policies, batch_size=1000)
```

### Parallel Processing

For very large datasets:

```python
from multiprocessing import Pool
import numpy as np

def process_chunk(chunk):
    """Process a chunk of data in parallel."""
    return [transform_row(row) for _, row in chunk.iterrows()]

# Split data into chunks
chunks = np.array_split(df, 4)  # 4 cores

# Process in parallel
with Pool(4) as pool:
    results = pool.map(process_chunk, chunks)

# Flatten and load
all_policies = [p for chunk in results for p in chunk]
loader.load_in_batches(all_policies)
```

## Validation Checklist

Before loading production data:

- [ ] All required fields are mapped
- [ ] IDs are unique
- [ ] Numeric fields are valid numbers (no strings)
- [ ] Dates are in consistent format
- [ ] Descriptions are meaningful (not just IDs)
- [ ] Test with small sample first (100 records)
- [ ] Verify data in Weaviate after loading
- [ ] Check search quality with real queries

## Testing Your Mapping

```python
# Load a small sample first
sample_df = pd.read_csv('your_data.csv').head(10)

# Transform
policies = [transform_policy(row) for _, row in sample_df.iterrows()]

# Validate
for policy in policies:
    assert 'id' in policy
    assert 'description' in policy
    assert isinstance(policy['limit'], (int, float))
    print(f"✓ Policy {policy['id']} valid")

# Load into Weaviate
loader.load_in_batches(policies, batch_size=10)

# Test search
client = WeaviateReinsuranceClient()
client.connect()
results = client.search_policies("test query", limit=5)
print(f"Found {len(results['results'])} results")
```

## Next Steps

1. **Identify your data source** (CSV, database, API)
2. **Map your fields** using the tables above
3. **Write transformation code** (see examples)
4. **Test with sample data** (10-100 records)
5. **Validate search quality** (try real queries)
6. **Load full dataset** in batches
7. **Monitor and optimize** as needed

For more examples, see `load_real_data.py`.
