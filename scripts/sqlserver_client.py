#!/usr/bin/env python3
"""
SQL Server Vector Client for Vector Search Benchmarking

This client implements vector search capabilities using SQL Server 2022:
- Dense vector search (cosine similarity with VARBINARY storage)
- Keyword search (full-text search with CONTAINS)
- Hybrid search (RRF fusion of dense + keyword)

Author: SQL Server Integration
Date: 2025-12-11
"""

import pyodbc
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import struct


class SQLServerVectorClient:
    """
    SQL Server 2022 client for vector similarity search.

    Features:
    - Dense vector search using cosine similarity (custom implementation)
    - Full-text keyword search using CONTAINS
    - Hybrid search using Reciprocal Rank Fusion (RRF)
    - Vector storage using VARBINARY(MAX)
    - Full-text catalog and index support
    """

    def __init__(self, server: str = "localhost", port: int = 1433,
                 user: str = "sa", password: str = "YourStrong@Passw0rd",
                 database: str = "vectordb"):
        """
        Initialize SQL Server client.

        Args:
            server: SQL Server host
            port: SQL Server port
            user: Database user (default: sa)
            password: Database password
            database: Database name
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    def connect(self):
        """Connect to SQL Server and create database if needed."""
        # First connect to master to create database
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server},{self.port};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )

        temp_conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = temp_conn.cursor()

        # Create database if not exists
        cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}')
            BEGIN
                CREATE DATABASE {self.database};
            END
        """)
        cursor.close()
        temp_conn.close()

        # Now connect to the actual database
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )

        self.conn = pyodbc.connect(conn_str, autocommit=False)

        print(f"✓ Connected to SQL Server {self._get_version()}")
        print(f"✓ Using database: {self.database}")

    def _get_version(self) -> str:
        """Get SQL Server version."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT @@VERSION;")
        version = cursor.fetchone()[0]
        cursor.close()
        # Extract version number (e.g., "2022")
        if "2022" in version:
            return "2022"
        elif "2019" in version:
            return "2019"
        else:
            return "Unknown"

    def disconnect(self):
        """Disconnect from SQL Server."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("✓ Disconnected from SQL Server")

    def create_table(self, table_name: str, vector_dim: int):
        """
        Create a table with vector column (VARBINARY) and full-text support.

        Args:
            table_name: Name of the table
            vector_dim: Dimension of the vector embeddings
        """
        cursor = self.conn.cursor()

        # Drop table if exists
        cursor.execute(f"""
            IF OBJECT_ID(N'{table_name}', N'U') IS NOT NULL
            DROP TABLE {table_name};
        """)

        # Create table with VARBINARY for vector storage
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                filename NVARCHAR(500) NOT NULL,
                text NVARCHAR(MAX),
                policy_id NVARCHAR(100),
                policy_type NVARCHAR(50),
                embedding VARBINARY(MAX),
                vector_dim INT
            );
        """)

        self.conn.commit()
        cursor.close()
        print(f"✓ Created table '{table_name}' with VARBINARY vector storage (dim={vector_dim})")

    def create_fulltext_index(self, table_name: str):
        """
        Create full-text catalog and index for keyword search.

        Args:
            table_name: Name of the table
        """
        cursor = self.conn.cursor()

        # Create full-text catalog if not exists
        catalog_name = f"{table_name}_catalog"
        cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = '{catalog_name}')
            BEGIN
                CREATE FULLTEXT CATALOG {catalog_name};
            END
        """)

        # Create full-text index on text column
        cursor.execute(f"""
            CREATE FULLTEXT INDEX ON {table_name}(text)
            KEY INDEX PK__{table_name}__*
            ON {catalog_name};
        """)

        self.conn.commit()
        cursor.close()
        print(f"✓ Created full-text index for '{table_name}'")

    def insert_documents(self, table_name: str, documents: List[Dict[str, Any]],
                        embeddings: List[List[float]]):
        """
        Insert documents with embeddings in batches.

        Args:
            table_name: Name of the table
            documents: List of document metadata dicts
            embeddings: List of embedding vectors
        """
        batch_size = 1000
        total_inserted = 0

        print(f"  Inserting {len(documents)} documents in batches of {batch_size}...")

        cursor = self.conn.cursor()

        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            batch_docs = documents[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]

            # Prepare batch insert
            for doc, emb in zip(batch_docs, batch_embeddings):
                # Convert numpy array to bytes
                if isinstance(emb, np.ndarray):
                    emb_list = emb.tolist()
                else:
                    emb_list = emb

                # Store as binary (float32 for efficiency)
                emb_array = np.array(emb_list, dtype=np.float32)
                emb_bytes = emb_array.tobytes()

                text = doc.get("text", "")

                cursor.execute(f"""
                    INSERT INTO {table_name}
                    (filename, text, policy_id, policy_type, embedding, vector_dim)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc.get("filename", ""),
                    text,
                    doc.get("policy_id", ""),
                    doc.get("policy_type", ""),
                    emb_bytes,
                    len(emb_list)
                ))

            self.conn.commit()
            total_inserted += len(batch_docs)
            print(f"    Batch {i//batch_size + 1}: Inserted {len(batch_docs)} documents")

        cursor.close()
        print(f"✓ Inserted {total_inserted} documents total")

    def _bytes_to_vector(self, vector_bytes: bytes) -> np.ndarray:
        """Convert VARBINARY bytes back to numpy array."""
        return np.frombuffer(vector_bytes, dtype=np.float32)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def dense_search(self, table_name: str, query_vector: List[float],
                    limit: int = 5) -> Tuple[List[Dict[str, Any]], float]:
        """
        Dense vector search using cosine similarity.

        Note: SQL Server 2022 doesn't have native vector distance functions,
        so we fetch all vectors and compute similarity in Python.

        Args:
            table_name: Name of the table
            query_vector: Query embedding vector
            limit: Number of results to return

        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()

        cursor = self.conn.cursor()

        # Fetch all documents (for small datasets this is acceptable)
        # For large datasets, consider adding approximate indexing
        cursor.execute(f"""
            SELECT id, filename, text, policy_id, policy_type, embedding
            FROM {table_name}
        """)

        rows = cursor.fetchall()
        cursor.close()

        # Convert query to numpy
        query_vec = np.array(query_vector, dtype=np.float32)

        # Calculate similarities
        results_with_scores = []
        for row in rows:
            doc_vec = self._bytes_to_vector(row[5])
            similarity = self._cosine_similarity(query_vec, doc_vec)

            results_with_scores.append({
                "id": row[0],
                "filename": row[1],
                "text": row[2],
                "policy_id": row[3],
                "policy_type": row[4],
                "similarity": float(similarity)
            })

        # Sort by similarity (descending) and take top K
        results_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
        results = results_with_scores[:limit]

        elapsed = (time.time() - start_time) * 1000  # ms

        return results, elapsed

    def keyword_search(self, table_name: str, query_text: str,
                      limit: int = 5) -> Tuple[List[Dict[str, Any]], float]:
        """
        Keyword search using SQL Server full-text search.

        Args:
            table_name: Name of the table
            query_text: Query text
            limit: Number of results to return

        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()

        cursor = self.conn.cursor()

        # Use FREETEXT for natural language queries
        # For exact phrase matching, use CONTAINS instead
        cursor.execute(f"""
            SELECT TOP (?)
                t.id, t.filename, t.text, t.policy_id, t.policy_type,
                KEY_TBL.RANK
            FROM {table_name} AS t
            INNER JOIN FREETEXTTABLE({table_name}, text, ?) AS KEY_TBL
                ON t.id = KEY_TBL.[KEY]
            ORDER BY KEY_TBL.RANK DESC
        """, (limit, query_text))

        rows = cursor.fetchall()
        cursor.close()

        elapsed = (time.time() - start_time) * 1000  # ms

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "filename": row[1],
                "text": row[2],
                "policy_id": row[3],
                "policy_type": row[4],
                "rank": float(row[5])
            })

        return results, elapsed

    def hybrid_search(self, table_name: str, query_vector: List[float],
                     query_text: str, limit: int = 5,
                     dense_weight: float = 0.5) -> Tuple[List[Dict[str, Any]], float]:
        """
        Hybrid search using RRF (Reciprocal Rank Fusion).

        Combines dense vector search and keyword search results.

        Args:
            table_name: Name of the table
            query_vector: Query embedding vector
            query_text: Query text
            limit: Number of results to return
            dense_weight: Weight for dense results (0-1)

        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()

        # Get results from both searches (fetch more for better fusion)
        dense_results, _ = self.dense_search(table_name, query_vector, limit * 2)
        keyword_results, _ = self.keyword_search(table_name, query_text, limit * 2)

        # RRF fusion
        k = 60  # RRF constant
        scores = {}

        # Score dense results
        for rank, result in enumerate(dense_results, 1):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + dense_weight * (1 / (k + rank))

        # Score keyword results
        keyword_weight = 1 - dense_weight
        for rank, result in enumerate(keyword_results, 1):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + keyword_weight * (1 / (k + rank))

        # Combine results
        all_results = {**{r["id"]: r for r in dense_results},
                      **{r["id"]: r for r in keyword_results}}

        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:limit]

        hybrid_results = []
        for doc_id in sorted_ids:
            result = all_results[doc_id].copy()
            result["hybrid_score"] = scores[doc_id]
            hybrid_results.append(result)

        elapsed = (time.time() - start_time) * 1000  # ms

        return hybrid_results, elapsed


if __name__ == "__main__":
    print("\nSQL Server Vector Client")
    print("=" * 50)
    print("\nThis client implements:")
    print("  ✓ Dense vector search (cosine similarity)")
    print("  ✓ Keyword search (full-text search)")
    print("  ✓ Hybrid search (RRF fusion)")
    print("\nReady to use in benchmarks!\n")
