#!/usr/bin/env python3
"""
SQL Server Vector Client for Vector Search Benchmarking

This client implements vector search capabilities using SQL Server 2025:
- Dense vector search (VARBINARY storage with manual cosine similarity)
- Keyword search (LIKE-based fallback)
- Hybrid search (RRF fusion of dense + keyword)

Note: Native VECTOR type support is not yet available in SQL Server 2025.
      Using VARBINARY storage with client-side cosine similarity calculation.

Author: SQL Server Integration
Date: 2025-12-11
"""

import pyodbc
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import struct

from config import config


class SQLServerVectorClient:
    """
    SQL Server 2025 client for vector similarity search.

    Features:
    - Dense vector search using VARBINARY storage with manual cosine similarity
    - LIKE-based keyword search (fallback)
    - Hybrid search using Reciprocal Rank Fusion (RRF)
    - Client-side vector operations (native VECTOR type not yet available)
    """

    def __init__(self, server: str = None, port: int = None,
                 user: str = None, password: str = None,
                 database: str = None):
        """
        Initialize SQL Server client.

        Args:
            server: SQL Server host (default: from config/environment)
            port: SQL Server port (default: from config/environment)
            user: Database user (default: from config/environment)
            password: Database password (default: from config/environment)
            database: Database name (default: from config/environment)
        """
        self.server = server or config.sqlserver.host
        self.port = port or config.sqlserver.port
        self.user = user or config.sqlserver.user
        self.password = password or config.sqlserver.password
        self.database = database or config.sqlserver.database
        self.driver = config.sqlserver.driver
        self.trust_cert = config.sqlserver.trust_cert
        self.conn = None

    def connect(self):
        """Connect to SQL Server and create database if needed."""
        # First connect to master to create database (without specifying database)
        conn_str_no_db = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server},{self.port};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate={self.trust_cert};"
        )

        temp_conn = pyodbc.connect(conn_str_no_db, autocommit=True)
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
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate={self.trust_cert};"
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
        Create a table with VARBINARY column for vector storage.

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
        # Each float32 is 4 bytes, so vector_dim * 4 bytes needed
        max_bytes = vector_dim * 4
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                filename NVARCHAR(500) NOT NULL,
                text NVARCHAR(MAX),
                policy_id NVARCHAR(100),
                policy_type NVARCHAR(50),
                embedding VARBINARY({max_bytes}) NOT NULL
            );
        """)

        self.conn.commit()
        cursor.close()
        print(f"✓ Created table '{table_name}' with VARBINARY vector storage ({vector_dim} dimensions)")

    def create_fulltext_index(self, table_name: str):
        """
        Create full-text catalog and index for keyword search.

        Note: Full-Text Search is not available in basic SQL Server Docker images.
        We'll skip this and use LIKE-based search as a fallback.

        Args:
            table_name: Name of the table
        """
        print(f"⚠ Full-Text Search not available in SQL Server container, using LIKE-based keyword search for '{table_name}'")

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
                # Convert to numpy array if needed
                if not isinstance(emb, np.ndarray):
                    emb = np.array(emb, dtype=np.float32)
                elif emb.dtype != np.float32:
                    emb = emb.astype(np.float32)

                # Convert to bytes for VARBINARY storage
                vector_bytes = emb.tobytes()

                text = doc.get("text", "")

                cursor.execute(f"""
                    INSERT INTO {table_name}
                    (filename, text, policy_id, policy_type, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    doc.get("filename", ""),
                    text,
                    doc.get("policy_id", ""),
                    doc.get("policy_type", ""),
                    vector_bytes
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
        Dense vector search using VARBINARY storage with client-side cosine similarity.

        Args:
            table_name: Name of the table
            query_vector: Query embedding vector
            limit: Number of results to return

        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()

        # Convert query vector to numpy array
        if not isinstance(query_vector, np.ndarray):
            query_vector = np.array(query_vector, dtype=np.float32)
        elif query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        cursor = self.conn.cursor()

        # Fetch all embeddings and metadata
        cursor.execute(f"""
            SELECT id, filename, text, policy_id, policy_type, embedding
            FROM {table_name}
        """)

        rows = cursor.fetchall()
        cursor.close()

        # Calculate cosine similarity for each document
        similarities = []
        for row in rows:
            doc_vector = self._bytes_to_vector(row[5])
            similarity = self._cosine_similarity(query_vector, doc_vector)
            similarities.append({
                "id": row[0],
                "filename": row[1],
                "text": row[2],
                "policy_id": row[3],
                "policy_type": row[4],
                "similarity": float(similarity)
            })

        # Sort by similarity and return top K
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        results = similarities[:limit]

        elapsed = (time.time() - start_time) * 1000  # ms

        return results, elapsed

    def keyword_search(self, table_name: str, query_text: str,
                      limit: int = 5) -> Tuple[List[Dict[str, Any]], float]:
        """
        Keyword search using basic LIKE matching (fallback since FTS not available).

        Args:
            table_name: Name of the table
            query_text: Query text
            limit: Number of results to return

        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()

        cursor = self.conn.cursor()

        # Simple keyword search using LIKE (not as good as full-text, but works)
        # Split query into words and search for any of them
        words = query_text.split()[:5]  # Limit to first 5 words for performance

        if not words:
            return [], 0.0

        # Build WHERE clause with OR conditions
        where_conditions = " OR ".join([f"text LIKE ?" for _ in words])
        like_params = [f"%{word}%" for word in words]

        cursor.execute(f"""
            SELECT TOP (?)
                id, filename, text, policy_id, policy_type
            FROM {table_name}
            WHERE {where_conditions}
        """, (limit, *like_params))

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
                "rank": 1.0  # Simple ranking (all results equal)
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
    print("  ✓ Dense vector search (VARBINARY storage, client-side cosine similarity)")
    print("  ✓ Keyword search (LIKE-based search)")
    print("  ✓ Hybrid search (RRF fusion)")
    print("\nNote: Native VECTOR type not yet available in SQL Server 2025")
    print("Ready to use in benchmarks!\n")
