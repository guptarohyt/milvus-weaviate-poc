"""
Load your actual reinsurance data into Weaviate.

This script shows how to:
1. Load data from various sources (CSV, Excel, Database, JSON, API)
2. Transform to the required format
3. Insert into Weaviate
4. Verify the data

Supports:
- CSV/Excel files
- SQL databases
- REST APIs
- JSON files
- Pandas DataFrames
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from weaviate_client import WeaviateReinsuranceClient
from typing import List, Dict, Any
import pandas as pd
import json
from pathlib import Path


class RealDataLoader:
    """Load real reinsurance data into Weaviate."""

    def __init__(self, client: WeaviateReinsuranceClient):
        self.client = client

    # ========================================
    # Method 1: Load from CSV/Excel
    # ========================================

    def load_policies_from_csv(self, csv_path: str):
        """
        Load policies from CSV file.

        Expected CSV columns:
        - policy_id: Unique identifier
        - policy_type: Type of policy
        - cedent: Cedent/client name
        - territory: Geographic territory
        - limit: Coverage limit (numeric)
        - premium: Premium amount (numeric)
        - inception_date: Policy start date
        - expiry_date: Policy end date
        - description: Text description
        """
        print(f"\n📂 Loading policies from: {csv_path}")

        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"   Found {len(df)} rows")

        # Transform to required format
        policies = []
        for _, row in df.iterrows():
            policy = {
                "id": str(row['policy_id']),
                "policy_type": str(row['policy_type']),
                "cedent": str(row['cedent']),
                "territory": str(row['territory']),
                "limit": float(row['limit']),
                "premium": float(row['premium']),
                "inception_date": str(row['inception_date']),
                "expiry_date": str(row['expiry_date']),
                "description": str(row['description'])
            }
            policies.append(policy)

        # Insert into Weaviate
        print(f"   Inserting {len(policies)} policies into Weaviate...")
        self.client.insert_policies(policies)
        print(f"   ✓ Successfully loaded {len(policies)} policies")

        return len(policies)

    def load_claims_from_excel(self, excel_path: str, sheet_name: str = "Claims"):
        """
        Load claims from Excel file.

        Expected Excel columns:
        - claim_id: Unique identifier
        - category: Claim category
        - status: Claim status
        - peril: Type of peril
        - loss_amount: Loss amount (numeric)
        - location: Loss location
        - loss_date: Date of loss
        - description: Text description
        """
        print(f"\n📊 Loading claims from: {excel_path}, sheet: {sheet_name}")

        # Read Excel
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"   Found {len(df)} rows")

        # Transform to required format
        claims = []
        for _, row in df.iterrows():
            claim = {
                "id": str(row['claim_id']),
                "category": str(row['category']),
                "status": str(row['status']),
                "peril": str(row['peril']),
                "loss_amount": float(row['loss_amount']),
                "location": str(row['location']),
                "loss_date": str(row['loss_date']),
                "description": str(row['description'])
            }
            claims.append(claim)

        # Insert into Weaviate
        print(f"   Inserting {len(claims)} claims into Weaviate...")
        self.client.insert_claims(claims)
        print(f"   ✓ Successfully loaded {len(claims)} claims")

        return len(claims)

    # ========================================
    # Method 2: Load from SQL Database
    # ========================================

    def load_policies_from_database(self, connection_string: str, query: str = None):
        """
        Load policies from SQL database.

        Example connection strings:
        - PostgreSQL: "postgresql://user:password@localhost:5432/dbname"
        - MySQL: "mysql://user:password@localhost:3306/dbname"
        - SQL Server: "mssql+pyodbc://user:password@server/database"

        Example query:
        SELECT
            policy_id, policy_type, cedent, territory,
            limit, premium, inception_date, expiry_date,
            description
        FROM policies
        WHERE status = 'Active'
        """
        print(f"\n🗄️  Loading policies from database...")

        # Import SQLAlchemy (install: pip install sqlalchemy)
        try:
            from sqlalchemy import create_engine
        except ImportError:
            print("   ❌ SQLAlchemy not installed. Run: pip install sqlalchemy")
            return 0

        # Default query if none provided
        if query is None:
            query = """
                SELECT
                    policy_id, policy_type, cedent, territory,
                    limit, premium, inception_date, expiry_date,
                    description
                FROM policies
            """

        # Connect and query
        engine = create_engine(connection_string)
        df = pd.read_sql(query, engine)
        print(f"   Found {len(df)} rows")

        # Transform and insert (same as CSV method)
        policies = []
        for _, row in df.iterrows():
            policy = {
                "id": str(row['policy_id']),
                "policy_type": str(row['policy_type']),
                "cedent": str(row['cedent']),
                "territory": str(row['territory']),
                "limit": float(row['limit']),
                "premium": float(row['premium']),
                "inception_date": str(row['inception_date']),
                "expiry_date": str(row['expiry_date']),
                "description": str(row['description'])
            }
            policies.append(policy)

        print(f"   Inserting {len(policies)} policies into Weaviate...")
        self.client.insert_policies(policies)
        print(f"   ✓ Successfully loaded {len(policies)} policies")

        return len(policies)

    # ========================================
    # Method 3: Load from REST API
    # ========================================

    def load_policies_from_api(self, api_url: str, headers: Dict = None):
        """
        Load policies from REST API.

        Example API response format:
        {
            "policies": [
                {
                    "policy_id": "POL-123",
                    "policy_type": "Property Catastrophe",
                    "cedent": "Company Name",
                    ...
                }
            ]
        }
        """
        print(f"\n🌐 Loading policies from API: {api_url}")

        import requests

        # Make API request
        response = requests.get(api_url, headers=headers or {})
        response.raise_for_status()

        data = response.json()
        print(f"   Found {len(data.get('policies', []))} policies")

        # Transform to required format
        policies = []
        for item in data.get('policies', []):
            policy = {
                "id": str(item['policy_id']),
                "policy_type": str(item['policy_type']),
                "cedent": str(item['cedent']),
                "territory": str(item['territory']),
                "limit": float(item['limit']),
                "premium": float(item['premium']),
                "inception_date": str(item['inception_date']),
                "expiry_date": str(item['expiry_date']),
                "description": str(item['description'])
            }
            policies.append(policy)

        # Insert into Weaviate
        print(f"   Inserting {len(policies)} policies into Weaviate...")
        self.client.insert_policies(policies)
        print(f"   ✓ Successfully loaded {len(policies)} policies")

        return len(policies)

    # ========================================
    # Method 4: Load from JSON Files
    # ========================================

    def load_from_json(self, json_path: str, data_type: str = "policy"):
        """
        Load data from JSON file.

        JSON format:
        [
            {"policy_id": "POL-123", ...},
            {"policy_id": "POL-456", ...}
        ]
        """
        print(f"\n📄 Loading {data_type}s from: {json_path}")

        with open(json_path, 'r') as f:
            data = json.load(f)

        print(f"   Found {len(data)} records")

        # Insert based on type
        if data_type == "policy":
            self.client.insert_policies(data)
        elif data_type == "claim":
            self.client.insert_claims(data)
        elif data_type == "knowledge":
            self.client.insert_knowledge(data)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

        print(f"   ✓ Successfully loaded {len(data)} {data_type}s")
        return len(data)

    # ========================================
    # Method 5: Batch Loading with Progress
    # ========================================

    def load_in_batches(self, data: List[Dict], data_type: str = "policy", batch_size: int = 1000):
        """
        Load large datasets in batches to avoid memory issues.

        Args:
            data: List of dictionaries
            data_type: "policy", "claim", or "knowledge"
            batch_size: Number of records per batch
        """
        print(f"\n📦 Loading {len(data)} {data_type}s in batches of {batch_size}")

        total_batches = (len(data) + batch_size - 1) // batch_size

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_num = i // batch_size + 1

            print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")

            if data_type == "policy":
                self.client.insert_policies(batch)
            elif data_type == "claim":
                self.client.insert_claims(batch)
            elif data_type == "knowledge":
                self.client.insert_knowledge(batch)

        print(f"   ✓ Successfully loaded all {len(data)} {data_type}s")
        return len(data)

    # ========================================
    # Data Validation
    # ========================================

    def validate_and_clean(self, df: pd.DataFrame, data_type: str = "policy") -> pd.DataFrame:
        """
        Validate and clean data before loading.

        Checks:
        - Required fields present
        - No duplicates
        - Valid data types
        - No null critical fields
        """
        print(f"\n🔍 Validating {data_type} data...")

        original_count = len(df)

        # Define required fields
        required_fields = {
            "policy": ['policy_id', 'policy_type', 'cedent', 'description', 'limit', 'premium'],
            "claim": ['claim_id', 'category', 'status', 'description', 'loss_amount'],
            "knowledge": ['article_id', 'title', 'content']
        }

        fields = required_fields.get(data_type, [])

        # Check required fields
        missing_fields = [f for f in fields if f not in df.columns]
        if missing_fields:
            print(f"   ❌ Missing required fields: {missing_fields}")
            return None

        # Remove duplicates
        df = df.drop_duplicates(subset=[fields[0]])  # First field is ID
        if len(df) < original_count:
            print(f"   ⚠️  Removed {original_count - len(df)} duplicates")

        # Remove rows with null critical fields
        before = len(df)
        df = df.dropna(subset=fields)
        if len(df) < before:
            print(f"   ⚠️  Removed {before - len(df)} rows with null critical fields")

        # Fill optional null fields with defaults
        if data_type == "policy":
            df['territory'] = df['territory'].fillna('Unknown')
            df['inception_date'] = df['inception_date'].fillna('1900-01-01')
            df['expiry_date'] = df['expiry_date'].fillna('2099-12-31')

        print(f"   ✓ Validation complete: {len(df)} valid records")
        return df


def create_sample_csv():
    """Create a sample CSV for testing."""
    print("\n📝 Creating sample CSV file: sample_policies.csv")

    data = {
        'policy_id': ['POL-001', 'POL-002', 'POL-003'],
        'policy_type': ['Property Catastrophe', 'Cyber Risk', 'Marine'],
        'cedent': ['ABC Insurance', 'XYZ Re', 'Global Underwriters'],
        'territory': ['United States', 'European Union', 'Worldwide'],
        'limit': [50000000, 25000000, 100000000],
        'premium': [2500000, 1500000, 5000000],
        'inception_date': ['2024-01-01', '2024-06-01', '2024-03-15'],
        'expiry_date': ['2025-01-01', '2025-06-01', '2025-03-15'],
        'description': [
            'Property catastrophe reinsurance covering hurricane and earthquake perils',
            'Cyber risk coverage for data breaches and network security incidents',
            'Marine cargo and hull insurance for international shipping operations'
        ]
    }

    df = pd.DataFrame(data)
    df.to_csv('sample_policies.csv', index=False)
    print("   ✓ Created sample_policies.csv")

    return 'sample_policies.csv'


def main():
    """Example usage of the data loader."""

    print("="*70)
    print("LOAD REAL REINSURANCE DATA INTO WEAVIATE")
    print("="*70)

    # Connect to Weaviate
    client = WeaviateReinsuranceClient()
    client.connect()

    # Create collections if they don't exist
    print("\n📋 Setting up collections...")
    client.create_collections()

    # Initialize loader
    loader = RealDataLoader(client)

    # Example 1: Load from CSV
    print("\n" + "="*70)
    print("EXAMPLE 1: Load from CSV")
    print("="*70)

    # Create sample CSV for demo
    csv_file = create_sample_csv()

    # Load the data
    loader.load_policies_from_csv(csv_file)

    # Verify
    stats = client.get_stats()
    print(f"\n✓ Current data in Weaviate:")
    for collection, stat in stats.items():
        print(f"   - {collection}: {stat['count']} records")

    # Example 2: Load from JSON (using existing data)
    print("\n" + "="*70)
    print("EXAMPLE 2: Load from JSON")
    print("="*70)

    data_dir = Path("../data")
    if (data_dir / "policies.json").exists():
        print("   Found existing synthetic data, loading first 10 records...")
        with open(data_dir / "policies.json") as f:
            policies = json.load(f)[:10]

        # Transform keys to match expected format
        for p in policies:
            p['policy_id'] = p.pop('id')

        loader.load_in_batches(policies, data_type="policy", batch_size=5)
    else:
        print("   No existing data found. Run benchmark first or provide your own JSON.")

    # Disconnect
    client.disconnect()

    print("\n" + "="*70)
    print("✓ DATA LOADING COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Replace sample data with your actual data sources")
    print("2. Adjust field mappings to match your schema")
    print("3. Run validation before loading large datasets")
    print("4. Use batch loading for files with 10,000+ records")


if __name__ == "__main__":
    main()
