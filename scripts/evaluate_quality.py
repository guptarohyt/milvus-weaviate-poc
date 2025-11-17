#!/usr/bin/env python3
"""
Retrieval Quality Evaluation for Phase 3

Evaluates the QUALITY of search results (not just speed):
- Precision@K (accuracy of top K results)
- Recall@K (coverage of relevant docs in top K)
- NDCG@K (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)

Compares:
- Milvus 2.5 dense search
- Milvus 2.5 sparse search
- Milvus 2.5 hybrid search
- Weaviate dense search
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from milvus_25_hybrid_client import Milvus25HybridClient
import weaviate


def load_processed_data():
    """Load all processed multi-modal data."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = Path(os.path.join(script_dir, "..", "data", "multimodal", "processed"))

    with open(data_dir / "pdfs_processed.json", "r") as f:
        pdfs = json.load(f)

    with open(data_dir / "word_docs_processed.json", "r") as f:
        word_docs = json.load(f)

    with open(data_dir / "images_processed.json", "r") as f:
        images = json.load(f)

    return pdfs, word_docs, images


def create_ground_truth_pdfs(pdfs):
    """
    Create ground truth for PDF search.

    For synthetic data, we can define relevance based on:
    - Same policy type
    - Similar policy structure
    - Overlapping terminology

    For each query (first doc), relevant docs are:
    - Itself (100% relevant)
    - Same policy type (75% relevant)
    - Different policy type (25% relevant)
    """
    ground_truth = {}

    # Extract policy types from document IDs
    # Format: policy_POL-000001.pdf
    doc_types = {}
    for i, pdf in enumerate(pdfs):
        # Try to infer type from content (simplified)
        text = pdf.get("text", "").lower()
        if "property" in text:
            doc_types[i] = "property"
        elif "casualty" in text or "liability" in text:
            doc_types[i] = "casualty"
        elif "workers" in text or "compensation" in text:
            doc_types[i] = "workers_comp"
        elif "auto" in text or "vehicle" in text:
            doc_types[i] = "auto"
        else:
            doc_types[i] = "other"

    # Create ground truth for first 10 queries
    for query_idx in range(10):
        query_type = doc_types.get(query_idx, "other")

        # Relevance scores (graded relevance)
        relevance = {}
        for doc_idx in range(len(pdfs)):
            if doc_idx == query_idx:
                relevance[doc_idx] = 3  # Perfect match (self)
            elif doc_types.get(doc_idx) == query_type:
                relevance[doc_idx] = 2  # Highly relevant (same type)
            else:
                relevance[doc_idx] = 1  # Somewhat relevant (different type)

        ground_truth[query_idx] = relevance

    return ground_truth


def create_ground_truth_images(images):
    """
    Create ground truth for image search.

    Relevant images are:
    - Same damage type (highly relevant)
    - Same claim ID (highly relevant)
    - Same policy ID (somewhat relevant)
    """
    ground_truth = {}

    for query_idx in range(min(10, len(images))):
        query_img = images[query_idx]
        query_damage = query_img.get("damage_type", "unknown")
        query_claim = query_img.get("claim_id", "")
        query_policy = query_img.get("policy_id", "")

        relevance = {}
        for doc_idx, img in enumerate(images):
            doc_damage = img.get("damage_type", "unknown")
            doc_claim = img.get("claim_id", "")
            doc_policy = img.get("policy_id", "")

            if doc_idx == query_idx:
                relevance[doc_idx] = 3  # Perfect match (self)
            elif doc_claim == query_claim and doc_claim != "":
                relevance[doc_idx] = 3  # Same claim (perfect)
            elif doc_damage == query_damage:
                relevance[doc_idx] = 2  # Same damage type (highly relevant)
            elif doc_policy == query_policy and doc_policy != "":
                relevance[doc_idx] = 1  # Same policy (somewhat relevant)
            else:
                relevance[doc_idx] = 0  # Not relevant

        ground_truth[query_idx] = relevance

    return ground_truth


def precision_at_k(retrieved_docs: List[int], relevant_docs: Dict[int, int], k: int) -> float:
    """
    Calculate Precision@K.

    Precision@K = (# relevant docs in top K) / K
    """
    if k == 0:
        return 0.0

    top_k = retrieved_docs[:k]
    relevant_count = sum(1 for doc_id in top_k if relevant_docs.get(doc_id, 0) >= 2)  # Score >= 2 = relevant

    return relevant_count / k


def recall_at_k(retrieved_docs: List[int], relevant_docs: Dict[int, int], k: int) -> float:
    """
    Calculate Recall@K.

    Recall@K = (# relevant docs in top K) / (total # relevant docs)
    """
    total_relevant = sum(1 for score in relevant_docs.values() if score >= 2)
    if total_relevant == 0:
        return 0.0

    top_k = retrieved_docs[:k]
    relevant_in_k = sum(1 for doc_id in top_k if relevant_docs.get(doc_id, 0) >= 2)

    return relevant_in_k / total_relevant


def ndcg_at_k(retrieved_docs: List[int], relevant_docs: Dict[int, int], k: int) -> float:
    """
    Calculate NDCG@K (Normalized Discounted Cumulative Gain).

    NDCG accounts for graded relevance and position.
    Higher scores = more relevant docs ranked higher.
    """
    if k == 0:
        return 0.0

    # DCG: sum of (relevance / log2(position + 1))
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_docs[:k], 1):
        relevance = relevant_docs.get(doc_id, 0)
        dcg += relevance / np.log2(i + 1)

    # IDCG: DCG of perfect ranking
    ideal_relevances = sorted(relevant_docs.values(), reverse=True)[:k]
    idcg = sum(rel / np.log2(i + 1) for i, rel in enumerate(ideal_relevances, 1))

    if idcg == 0:
        return 0.0

    return dcg / idcg


def mean_reciprocal_rank(retrieved_docs: List[int], relevant_docs: Dict[int, int]) -> float:
    """
    Calculate MRR (Mean Reciprocal Rank).

    MRR = 1 / (position of first relevant doc)
    """
    for i, doc_id in enumerate(retrieved_docs, 1):
        if relevant_docs.get(doc_id, 0) >= 2:  # First relevant doc
            return 1.0 / i

    return 0.0  # No relevant docs found


def setup_milvus_collections(pdfs, images):
    """Setup Milvus 2.5 collections for quality eval."""
    client = Milvus25HybridClient(host="localhost", port="19530")
    client.connect()

    print("[Milvus 2.5] Creating collections for quality evaluation...")

    # PDF collection
    pdf_collection = client.create_hybrid_collection("quality_eval_pdfs", dense_dim=384)
    client.create_indexes(pdf_collection)

    pdf_docs = [{"filename": p["filename"], "text": p["text"],
                 "policy_id": p.get("id", "UNKNOWN"),
                 "policy_type": p.get("type", "pdf")}
                for p in pdfs]
    pdf_embeddings = [p["embedding"] for p in pdfs]
    client.insert_documents(pdf_collection, pdf_docs, pdf_embeddings)
    pdf_collection.load()

    # Image collection
    image_collection = client.create_hybrid_collection("quality_eval_images", dense_dim=512)
    client.create_indexes(image_collection)

    image_docs = [{"filename": img["filename"], "text": img.get("description", ""),
                   "policy_id": img.get("claim_id", "UNKNOWN"),
                   "policy_type": img.get("damage_type", "unknown")}
                  for img in images]
    image_embeddings = [img["image_embedding"] for img in images]
    client.insert_documents(image_collection, image_docs, image_embeddings)
    image_collection.load()

    print("✓ Milvus 2.5 collections ready\n")

    return client, pdf_collection, image_collection


def setup_weaviate_collections(pdfs, images):
    """Setup Weaviate collections for quality eval."""
    client = weaviate.Client("http://localhost:8080")

    print("[Weaviate] Creating collections for quality evaluation...")

    # PDF collection
    pdf_schema = {
        "class": "QualityEvalPDFs",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "policy_id", "dataType": ["text"]},
            {"name": "policy_type", "dataType": ["text"]},
            {"name": "doc_index", "dataType": ["int"]}
        ]
    }

    try:
        client.schema.delete_class("QualityEvalPDFs")
    except:
        pass

    client.schema.create_class(pdf_schema)

    with client.batch as batch:
        for i, pdf in enumerate(pdfs):
            properties = {
                "filename": pdf["filename"],
                "text": pdf["text"],
                "policy_id": pdf.get("id", "UNKNOWN"),
                "policy_type": pdf.get("type", "pdf"),
                "doc_index": i
            }
            batch.add_data_object(properties, "QualityEvalPDFs", vector=pdf["embedding"])

    # Image collection
    image_schema = {
        "class": "QualityEvalImages",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "description", "dataType": ["text"]},
            {"name": "claim_id", "dataType": ["text"]},
            {"name": "damage_type", "dataType": ["text"]},
            {"name": "doc_index", "dataType": ["int"]}
        ]
    }

    try:
        client.schema.delete_class("QualityEvalImages")
    except:
        pass

    client.schema.create_class(image_schema)

    with client.batch as batch:
        for i, img in enumerate(images):
            properties = {
                "filename": img["filename"],
                "description": img.get("description", ""),
                "claim_id": img.get("claim_id", "UNKNOWN"),
                "damage_type": img.get("damage_type", "unknown"),
                "doc_index": i
            }
            batch.add_data_object(properties, "QualityEvalImages", vector=img["image_embedding"])

    print("✓ Weaviate collections ready\n")

    return client


def evaluate_milvus_pdfs(client, collection, pdfs, ground_truth, filename_to_idx, num_queries=10):
    """Evaluate Milvus PDF search quality."""
    results = {
        "dense": {"precision@5": [], "recall@5": [], "ndcg@5": [], "mrr": []},
        "sparse": {"precision@5": [], "recall@5": [], "ndcg@5": [], "mrr": []},
        "hybrid": {"precision@5": [], "recall@5": [], "ndcg@5": [], "mrr": []}
    }

    print(f"[Milvus 2.5] Evaluating PDF search quality ({num_queries} queries)...")

    for query_idx in range(num_queries):
        query_vector = pdfs[query_idx]["embedding"]
        query_text = pdfs[query_idx]["text"]
        relevance = ground_truth[query_idx]

        # Dense search
        dense_results, _ = client.dense_search(collection, query_vector, limit=100, output_fields=["filename"])
        # Map filenames back to document indices
        dense_ids = [filename_to_idx.get(r["filename"], -1) for r in dense_results if r.get("filename") in filename_to_idx]

        results["dense"]["precision@5"].append(precision_at_k(dense_ids, relevance, 5))
        results["dense"]["recall@5"].append(recall_at_k(dense_ids, relevance, 5))
        results["dense"]["ndcg@5"].append(ndcg_at_k(dense_ids, relevance, 5))
        results["dense"]["mrr"].append(mean_reciprocal_rank(dense_ids, relevance))

        # Sparse search
        sparse_results, _ = client.sparse_search(collection, query_text, limit=100, output_fields=["filename"])
        sparse_ids = [filename_to_idx.get(r["filename"], -1) for r in sparse_results if r.get("filename") in filename_to_idx]

        results["sparse"]["precision@5"].append(precision_at_k(sparse_ids, relevance, 5))
        results["sparse"]["recall@5"].append(recall_at_k(sparse_ids, relevance, 5))
        results["sparse"]["ndcg@5"].append(ndcg_at_k(sparse_ids, relevance, 5))
        results["sparse"]["mrr"].append(mean_reciprocal_rank(sparse_ids, relevance))

        # Hybrid search
        hybrid_results, _ = client.hybrid_search(collection, query_vector, query_text, limit=100, output_fields=["filename"])
        hybrid_ids = [filename_to_idx.get(r["filename"], -1) for r in hybrid_results if r.get("filename") in filename_to_idx]

        results["hybrid"]["precision@5"].append(precision_at_k(hybrid_ids, relevance, 5))
        results["hybrid"]["recall@5"].append(recall_at_k(hybrid_ids, relevance, 5))
        results["hybrid"]["ndcg@5"].append(ndcg_at_k(hybrid_ids, relevance, 5))
        results["hybrid"]["mrr"].append(mean_reciprocal_rank(hybrid_ids, relevance))

    # Calculate averages
    for search_type in ["dense", "sparse", "hybrid"]:
        for metric in ["precision@5", "recall@5", "ndcg@5", "mrr"]:
            avg = np.mean(results[search_type][metric])
            results[search_type][f"{metric}_avg"] = avg

    return results


def evaluate_weaviate_pdfs(client, pdfs, ground_truth, num_queries=10):
    """Evaluate Weaviate PDF search quality."""
    results = {"precision@5": [], "recall@5": [], "ndcg@5": [], "mrr": []}

    print(f"[Weaviate] Evaluating PDF search quality ({num_queries} queries)...")

    for query_idx in range(num_queries):
        query_vector = pdfs[query_idx]["embedding"]
        relevance = ground_truth[query_idx]

        # Dense search
        response = client.query.get("QualityEvalPDFs", ["doc_index"]) \
            .with_near_vector({"vector": query_vector}) \
            .with_limit(100) \
            .do()

        retrieved_ids = [obj["doc_index"] for obj in response["data"]["Get"]["QualityEvalPDFs"]]

        results["precision@5"].append(precision_at_k(retrieved_ids, relevance, 5))
        results["recall@5"].append(recall_at_k(retrieved_ids, relevance, 5))
        results["ndcg@5"].append(ndcg_at_k(retrieved_ids, relevance, 5))
        results["mrr"].append(mean_reciprocal_rank(retrieved_ids, relevance))

    # Calculate averages
    for metric in ["precision@5", "recall@5", "ndcg@5", "mrr"]:
        results[f"{metric}_avg"] = np.mean(results[metric])

    return results


def main():
    print("="*70)
    print("Retrieval Quality Evaluation - Phase 3")
    print("="*70)
    print("\nThis evaluates QUALITY (not speed) of search results.")
    print("Metrics: Precision@5, Recall@5, NDCG@5, MRR\n")

    # Load data
    print("Loading processed data...")
    pdfs, word_docs, images = load_processed_data()
    print(f"✓ Loaded {len(pdfs)} PDFs, {len(word_docs)} Word docs, {len(images)} images\n")

    # Create ground truth
    print("Creating ground truth relevance judgments...")
    pdf_ground_truth = create_ground_truth_pdfs(pdfs)
    image_ground_truth = create_ground_truth_images(images)
    print("✓ Ground truth created\n")

    # Create filename to index mapping
    pdf_filename_to_idx = {pdf["filename"]: i for i, pdf in enumerate(pdfs)}

    # Setup databases
    milvus_client, pdf_coll, image_coll = setup_milvus_collections(pdfs, images)
    weaviate_client = setup_weaviate_collections(pdfs, images)

    # Evaluate PDF search
    print("\n" + "="*70)
    print("EVALUATING PDF SEARCH QUALITY")
    print("="*70 + "\n")

    milvus_pdf_quality = evaluate_milvus_pdfs(milvus_client, pdf_coll, pdfs, pdf_ground_truth, pdf_filename_to_idx)
    weaviate_pdf_quality = evaluate_weaviate_pdfs(weaviate_client, pdfs, pdf_ground_truth)

    # Print results
    print("\n" + "="*70)
    print("QUALITY RESULTS")
    print("="*70)

    print("\nMilvus 2.5 PDF Search Quality:")
    for search_type in ["dense", "sparse", "hybrid"]:
        print(f"\n  {search_type.upper()}:")
        print(f"    Precision@5: {milvus_pdf_quality[search_type]['precision@5_avg']:.3f}")
        print(f"    Recall@5:    {milvus_pdf_quality[search_type]['recall@5_avg']:.3f}")
        print(f"    NDCG@5:      {milvus_pdf_quality[search_type]['ndcg@5_avg']:.3f}")
        print(f"    MRR:         {milvus_pdf_quality[search_type]['mrr_avg']:.3f}")

    print("\nWeaviate PDF Search Quality:")
    print(f"    Precision@5: {weaviate_pdf_quality['precision@5_avg']:.3f}")
    print(f"    Recall@5:    {weaviate_pdf_quality['recall@5_avg']:.3f}")
    print(f"    NDCG@5:      {weaviate_pdf_quality['ndcg@5_avg']:.3f}")
    print(f"    MRR:         {weaviate_pdf_quality['mrr_avg']:.3f}")

    # Save results
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = Path(os.path.join(script_dir, "..", "results", "phase3_quality_results.json"))

    quality_results = {
        "milvus_25_pdfs": milvus_pdf_quality,
        "weaviate_pdfs": weaviate_pdf_quality,
        "ground_truth_notes": {
            "relevance_scale": "0 (not relevant) to 3 (perfect match)",
            "threshold": "Score >= 2 considered relevant for precision/recall",
            "queries": "First 10 documents used as queries",
            "judgments": "Based on policy type similarity (synthetic data)"
        }
    }

    with open(output_file, "w") as f:
        json.dump(quality_results, f, indent=2)

    print(f"\n✓ Quality results saved to {output_file}")

    # Cleanup
    print("\nCleaning up...")
    pdf_coll.release()
    image_coll.release()

    from pymilvus import utility
    utility.drop_collection("quality_eval_pdfs")
    utility.drop_collection("quality_eval_images")

    weaviate_client.schema.delete_class("QualityEvalPDFs")
    weaviate_client.schema.delete_class("QualityEvalImages")

    milvus_client.disconnect()

    print("✓ Cleanup complete\n")
    print("="*70)
    print("✓ Quality Evaluation Complete!")
    print("="*70)
    print("\nKey Takeaway:")
    print("  Higher scores = better retrieval quality")
    print("  Perfect score = 1.0 for all metrics")
    print()


if __name__ == "__main__":
    main()
