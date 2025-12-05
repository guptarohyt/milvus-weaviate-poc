#!/usr/bin/env python3
"""
PostgreSQL with pgvector Client for Vector Search Benchmarking

This client implements vector search capabilities using PostgreSQL with the pgvector extension:
- Dense vector search (cosine similarity)
- Keyword search (full-text search with tsvector)
- Hybrid search (RRF fusion of dense + keyword)

Author: PostgreSQL Integration
Date: 2025-12-05
"""

import psycopg2
from psycopg2.extras import execute_values
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


class PostgreSQLVectorClient:
    """
    PostgreSQL client with pgvector extension for vector similarity search.
    
    Features:
    - Dense vector search using cosine similarity (<=> operator)
    - Full-text keyword search using tsvector
    - Hybrid search using Reciprocal Rank Fusion (RRF)
    - IVF indexing for vector columns
    - GIN indexing for full-text search
    """
    
    def __init__(self, host: str = "localhost", port: int = 5432, 
                 user: str = "postgres", password: str = "postgres", 
                 database: str = "vectordb"):
        """
        Initialize PostgreSQL client.
        
        Args:
            host: PostgreSQL server host
            port: PostgreSQL server port
            user: Database user
            password: Database password
            database: Database name
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        
    def connect(self):
        """Connect to PostgreSQL and enable pgvector extension."""
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
        
        # Enable pgvector extension
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.conn.commit()
            
        print(f"✓ Connected to PostgreSQL {self._get_version()}")
        print("✓ pgvector extension enabled")
    
    def _get_version(self) -> str:
        """Get PostgreSQL version."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            # Extract version number (e.g., "PostgreSQL 17.0")
            return version.split()[1]
    
    def disconnect(self):
        """Disconnect from PostgreSQL."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("✓ Disconnected from PostgreSQL")
    
    def create_table(self, table_name: str, vector_dim: int):
        """
        Create a table with vector column and full-text search support.
        
        Args:
            table_name: Name of the table
            vector_dim: Dimension of the vector embeddings
        """
        with self.conn.cursor() as cur:
            # Drop table if exists
            cur.execute(f"DROP TABLE IF EXISTS {table_name};")
            
            # Create table with vector column
            cur.execute(f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    text TEXT,
                    policy_id TEXT,
                    policy_type TEXT,
                    embedding vector({vector_dim}),
                    text_search tsvector
                );
            """)
            
            # Create GIN index for full-text search
            cur.execute(f"""
                CREATE INDEX {table_name}_text_search_idx 
                ON {table_name} USING GIN(text_search);
            """)
            
            self.conn.commit()
            print(f"✓ Created table '{table_name}' with vector({vector_dim}) column")
    
    def create_vector_index(self, table_name: str, index_type: str = "ivfflat"):
        """
        Create vector index for faster similarity search.
        
        Args:
            table_name: Name of the table
            index_type: Type of index ('ivfflat' or 'hnsw')
        """
        with self.conn.cursor() as cur:
            if index_type == "ivfflat":
                # IVF index (similar to Milvus IVF_FLAT)
                # lists = rows / 1000 is a good rule of thumb
                cur.execute(f"""
                    CREATE INDEX {table_name}_embedding_idx 
                    ON {table_name} 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
            elif index_type == "hnsw":
                # HNSW index (hierarchical navigable small world)
                cur.execute(f"""
                    CREATE INDEX {table_name}_embedding_idx 
                    ON {table_name} 
                    USING hnsw (embedding vector_cosine_ops);
                """)
            
            self.conn.commit()
            print(f"✓ Created {index_type.upper()} index for '{table_name}'")
    
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
        
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            batch_docs = documents[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]
            
            # Prepare data for batch insert
            data = []
            for doc, emb in zip(batch_docs, batch_embeddings):
                # Create tsvector for full-text search
                text = doc.get("text", "")
                data.append((
                    doc.get("filename", ""),
                    text,
                    doc.get("policy_id", ""),
                    doc.get("policy_type", ""),
                    emb,
                    text  # Will be converted to tsvector
                ))
            
            with self.conn.cursor() as cur:
                execute_values(
                    cur,
                    f"""
                    INSERT INTO {table_name} 
                    (filename, text, policy_id, policy_type, embedding, text_search)
                    VALUES %s
                    """,
                    data,
                    template="(%s, %s, %s, %s, %s, to_tsvector('english', %s))"
                )
            
            self.conn.commit()
            total_inserted += len(batch_docs)
            print(f"    Batch {i//batch_size + 1}: Inserted {len(batch_docs)} documents")
        
        print(f"✓ Inserted {total_inserted} documents total")
    
    def dense_search(self, table_name: str, query_vector: List[float], 
                    limit: int = 5) -> Tuple[List[Dict[str, Any]], float]:
        """
        Dense vector search using cosine similarity.
        
        Args:
            table_name: Name of the table
            query_vector: Query embedding vector
            limit: Number of results to return
            
        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()
        
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, filename, text, policy_id, policy_type,
                       1 - (embedding <=> %s::vector) as similarity
                FROM {table_name}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (query_vector, query_vector, limit))
            
            rows = cur.fetchall()
        
        elapsed = (time.time() - start_time) * 1000  # ms
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "filename": row[1],
                "text": row[2],
                "policy_id": row[3],
                "policy_type": row[4],
                "similarity": float(row[5])
            })
        
        return results, elapsed
    
    def keyword_search(self, table_name: str, query_text: str, 
                      limit: int = 5) -> Tuple[List[Dict[str, Any]], float]:
        """
        Keyword search using PostgreSQL full-text search.
        
        Args:
            table_name: Name of the table
            query_text: Query text
            limit: Number of results to return
            
        Returns:
            Tuple of (results list, elapsed time in ms)
        """
        start_time = time.time()
        
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, filename, text, policy_id, policy_type,
                       ts_rank(text_search, query) as rank
                FROM {table_name}, 
                     to_tsquery('english', %s) query
                WHERE text_search @@ query
                ORDER BY rank DESC
                LIMIT %s;
            """, (query_text.replace(" ", " & "), limit))
            
            rows = cur.fetchall()
        
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
    print("\nPostgreSQL with pgvector Client")
    print("=" * 50)
    print("\nThis client implements:")
    print("  ✓ Dense vector search (cosine similarity)")
    print("  ✓ Keyword search (full-text search)")
    print("  ✓ Hybrid search (RRF fusion)")
    print("\nReady to use in benchmarks!\n")
