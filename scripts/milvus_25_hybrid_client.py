#!/usr/bin/env python3
"""
Milvus 2.5 Hybrid Search Client for Phase 3

This client implements the new Milvus 2.5 features:
- Sparse vectors (BM25 for keyword search)
- Hybrid search (dense + sparse vector fusion)
- Grouping search (group results by field)

Author: Phase 3 Implementation
Date: 2025-11-15
"""

import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import re

from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)

from config import config


class BM25Encoder:
    """
    Simple BM25 encoder for generating sparse vectors.

    BM25 (Best Matching 25) is a ranking function used in information retrieval.
    It generates sparse vectors where non-zero dimensions correspond to terms
    and values represent TF-IDF-like scores.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 encoder.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.vocab = {}  # term -> term_id mapping
        self.idf = {}    # term -> IDF score
        self.avgdl = 0   # average document length
        self.doc_count = 0

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms."""
        # Simple tokenization: lowercase, split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def fit(self, documents: List[str]):
        """
        Fit the BM25 model on a corpus of documents.

        Args:
            documents: List of text documents
        """
        self.doc_count = len(documents)
        doc_lengths = []
        term_doc_freq = Counter()  # term -> number of documents containing it

        # Build vocabulary and calculate document frequencies
        for doc in documents:
            tokens = self._tokenize(doc)
            doc_lengths.append(len(tokens))
            unique_tokens = set(tokens)

            for token in unique_tokens:
                if token not in self.vocab:
                    self.vocab[token] = len(self.vocab)
                term_doc_freq[token] += 1

        # Calculate average document length
        self.avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0

        # Calculate IDF scores
        for term, df in term_doc_freq.items():
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            # where N is total number of documents
            self.idf[term] = np.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

    def encode(self, text: str) -> Dict[int, float]:
        """
        Encode text into a sparse vector (BM25 scores).

        Args:
            text: Input text

        Returns:
            Dictionary mapping term_id -> BM25 score
        """
        tokens = self._tokenize(text)
        doc_len = len(tokens)
        term_freq = Counter(tokens)

        sparse_vector = {}

        for term, tf in term_freq.items():
            if term in self.vocab:
                term_id = self.vocab[term]
                idf = self.idf.get(term, 0)

                # BM25 score = IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score = idf * (numerator / denominator)

                sparse_vector[term_id] = float(score)

        return sparse_vector


class Milvus25HybridClient:
    """
    Milvus 2.5 client with hybrid search capabilities.

    Features:
    - Dense vector search (semantic)
    - Sparse vector search (keyword/BM25)
    - Hybrid search (dense + sparse fusion)
    - Grouping search
    """

    def __init__(self, host: str = None, port: str = None):
        """
        Initialize Milvus 2.5 client.

        Args:
            host: Milvus server host (default: from config/environment)
            port: Milvus server port (default: from config/environment)
        """
        self.host = host or config.milvus.host
        self.port = str(port) if port else str(config.milvus.port)
        self.connection = None
        self.bm25_encoder = BM25Encoder()

    def connect(self):
        """Connect to Milvus server."""
        connections.connect(host=self.host, port=self.port)
        self.connection = "default"
        print(f"✓ Connected to Milvus {utility.get_server_version()}")

    def disconnect(self):
        """Disconnect from Milvus server."""
        if self.connection:
            connections.disconnect(self.connection)
            self.connection = None
            print("✓ Disconnected from Milvus")

    def create_hybrid_collection(
        self,
        collection_name: str,
        dense_dim: int = 384,
        description: str = "Hybrid search collection"
    ) -> Collection:
        """
        Create a collection with both dense and sparse vector fields.

        Args:
            collection_name: Name of the collection
            dense_dim: Dimension of dense vectors (default: 384 for Sentence Transformers)
            description: Collection description

        Returns:
            Created Collection object
        """
        # Drop collection if exists
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"✓ Dropped existing collection '{collection_name}'")

        # Define schema with both dense and sparse vectors
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=10000),
            FieldSchema(name="policy_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="policy_type", dtype=DataType.VARCHAR, max_length=100),
            # Dense vector for semantic search
            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=dense_dim),
            # Sparse vector for keyword search (NEW in Milvus 2.5!)
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR)
        ]

        schema = CollectionSchema(fields=fields, description=description)
        collection = Collection(name=collection_name, schema=schema)

        print(f"✓ Created hybrid collection '{collection_name}' with dense ({dense_dim}d) and sparse vectors")

        return collection

    def create_indexes(self, collection: Collection):
        """
        Create indexes for both dense and sparse vectors.

        Args:
            collection: Collection to create indexes for
        """
        # Dense vector index (IVF_FLAT like Phase 2)
        dense_index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="dense_vector", index_params=dense_index_params)
        print("✓ Created IVF_FLAT index for dense_vector")

        # Sparse vector index (IP for inner product)
        sparse_index_params = {
            "index_type": "SPARSE_INVERTED_INDEX",
            "metric_type": "IP",  # Inner Product for sparse vectors
            "params": {"drop_ratio_build": 0.2}
        }
        collection.create_index(field_name="sparse_vector", index_params=sparse_index_params)
        print("✓ Created SPARSE_INVERTED_INDEX for sparse_vector")

    def insert_documents(
        self,
        collection: Collection,
        documents: List[Dict[str, Any]],
        dense_embeddings: List[List[float]]
    ):
        """
        Insert documents with both dense and sparse vectors.

        Args:
            collection: Target collection
            documents: List of document metadata dicts
            dense_embeddings: List of dense vector embeddings
        """
        # Fit BM25 on the corpus
        texts = [doc["text"] for doc in documents]
        print(f"  Fitting BM25 on {len(texts)} documents...")
        self.bm25_encoder.fit(texts)

        # Generate sparse vectors
        print(f"  Generating sparse vectors...")
        sparse_embeddings = [self.bm25_encoder.encode(text) for text in texts]

        # Prepare data for insertion
        filenames = [doc["filename"] for doc in documents]
        texts_truncated = [doc["text"][:10000] for doc in documents]
        policy_ids = [doc.get("policy_id", "UNKNOWN") for doc in documents]
        policy_types = [doc.get("policy_type", "UNKNOWN") for doc in documents]

        # Insert in batches to avoid gRPC message size limit
        batch_size = 5000
        total_inserted = 0

        print(f"  Inserting {len(documents)} documents in batches of {batch_size}...")
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))

            insert_result = collection.insert([
                filenames[i:end_idx],
                texts_truncated[i:end_idx],
                policy_ids[i:end_idx],
                policy_types[i:end_idx],
                dense_embeddings[i:end_idx],
                sparse_embeddings[i:end_idx]
            ])

            total_inserted += len(insert_result.primary_keys)
            print(f"    Batch {i//batch_size + 1}: Inserted {len(insert_result.primary_keys)} documents")

        collection.flush()
        print(f"✓ Inserted {total_inserted} documents total")

    def dense_search(
        self,
        collection: Collection,
        query_vector: List[float],
        limit: int = 5,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Pure dense vector search (semantic).

        Args:
            collection: Collection to search
            query_vector: Dense query vector
            limit: Number of results
            output_fields: Fields to return

        Returns:
            List of search results
        """
        if output_fields is None:
            output_fields = ["filename", "text", "policy_id", "policy_type"]

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        start_time = time.time()
        results = collection.search(
            data=[query_vector],
            anns_field="dense_vector",
            param=search_params,
            limit=limit,
            output_fields=output_fields
        )
        elapsed = (time.time() - start_time) * 1000  # ms

        formatted_results = []
        for hit in results[0]:
            formatted_results.append({
                "id": hit.id,
                "distance": hit.distance,
                **{field: hit.entity.get(field) for field in output_fields}
            })

        return formatted_results, elapsed

    def sparse_search(
        self,
        collection: Collection,
        query_text: str,
        limit: int = 5,
        output_fields: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Pure sparse vector search (keyword/BM25).

        Args:
            collection: Collection to search
            query_text: Query text
            limit: Number of results
            output_fields: Fields to return

        Returns:
            Tuple of (search results, elapsed time in ms)
        """
        if output_fields is None:
            output_fields = ["filename", "text", "policy_id", "policy_type"]

        # Encode query to sparse vector
        query_sparse = self.bm25_encoder.encode(query_text)

        search_params = {"metric_type": "IP", "params": {}}

        start_time = time.time()
        results = collection.search(
            data=[query_sparse],
            anns_field="sparse_vector",
            param=search_params,
            limit=limit,
            output_fields=output_fields
        )
        elapsed = (time.time() - start_time) * 1000  # ms

        formatted_results = []
        for hit in results[0]:
            formatted_results.append({
                "id": hit.id,
                "distance": hit.distance,
                **{field: hit.entity.get(field) for field in output_fields}
            })

        return formatted_results, elapsed

    def hybrid_search(
        self,
        collection: Collection,
        query_vector: List[float],
        query_text: str,
        limit: int = 5,
        dense_weight: float = 0.5,
        output_fields: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Hybrid search combining dense and sparse vectors.

        Uses RRF (Reciprocal Rank Fusion) to combine results.

        Args:
            collection: Collection to search
            query_vector: Dense query vector
            query_text: Query text for sparse search
            limit: Number of results
            dense_weight: Weight for dense results (0-1, sparse = 1 - dense_weight)
            output_fields: Fields to return

        Returns:
            Tuple of (search results, elapsed time in ms)
        """
        if output_fields is None:
            output_fields = ["filename", "text", "policy_id", "policy_type"]

        start_time = time.time()

        # Get results from both searches
        dense_results, _ = self.dense_search(collection, query_vector, limit * 2, output_fields)
        sparse_results, _ = self.sparse_search(collection, query_text, limit * 2, output_fields)

        # RRF fusion: score = 1 / (k + rank)
        k = 60  # RRF constant
        scores = {}

        # Score dense results
        for rank, result in enumerate(dense_results, 1):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + dense_weight * (1 / (k + rank))

        # Score sparse results
        sparse_weight = 1 - dense_weight
        for rank, result in enumerate(sparse_results, 1):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + sparse_weight * (1 / (k + rank))

        # Combine and sort by score
        all_results = {**{r["id"]: r for r in dense_results}, **{r["id"]: r for r in sparse_results}}
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:limit]

        hybrid_results = []
        for doc_id in sorted_ids:
            result = all_results[doc_id].copy()
            result["hybrid_score"] = scores[doc_id]
            hybrid_results.append(result)

        elapsed = (time.time() - start_time) * 1000  # ms

        return hybrid_results, elapsed

    def grouping_search(
        self,
        collection: Collection,
        query_vector: List[float],
        group_by_field: str,
        group_size: int = 3,
        limit: int = 30,
        output_fields: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Grouping search - NEW in Milvus 2.5!

        Groups results by a field and returns top N results per group.

        Args:
            collection: Collection to search
            query_vector: Dense query vector
            group_by_field: Field to group by (e.g., "policy_id")
            group_size: Number of results per group
            limit: Total number of results to fetch before grouping
            output_fields: Fields to return

        Returns:
            Tuple of (grouped search results, elapsed time in ms)
        """
        if output_fields is None:
            output_fields = ["filename", "text", "policy_id", "policy_type"]

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }

        start_time = time.time()
        results = collection.search(
            data=[query_vector],
            anns_field="dense_vector",
            param=search_params,
            limit=limit,
            group_by_field=group_by_field,
            group_size=group_size,
            output_fields=output_fields
        )
        elapsed = (time.time() - start_time) * 1000  # ms

        formatted_results = []
        for hit in results[0]:
            formatted_results.append({
                "id": hit.id,
                "distance": hit.distance,
                "group": hit.entity.get(group_by_field),
                **{field: hit.entity.get(field) for field in output_fields}
            })

        return formatted_results, elapsed


if __name__ == "__main__":
    print("\nMilvus 2.5 Hybrid Search Client")
    print("================================\n")
    print("This client implements:")
    print("  ✓ Sparse vectors (BM25)")
    print("  ✓ Hybrid search (dense + sparse)")
    print("  ✓ Grouping search")
    print("\nReady to use in Phase 3 benchmarks!\n")
