#!/usr/bin/env python3
"""
Load processed data into PostgreSQL with pgvector for benchmarking.

This script loads the processed multi-modal data (PDFs, Word docs, Images)
into PostgreSQL tables with vector embeddings for similarity search.
"""

import json
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from postgresql_client import PostgreSQLVectorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Helper to get project root
PROJECT_ROOT = Path(__file__).parent.parent

def get_data_dir():
    """Get data directory, resolving DATA_OUTPUT_DIR relative to project root."""
    data_output = os.getenv("DATA_OUTPUT_DIR", "./data/multimodal")
    if not Path(data_output).is_absolute():
        return PROJECT_ROOT / data_output
    return Path(data_output)


def load_processed_data():
    """Load all processed multi-modal data."""
    data_dir = get_data_dir() / "processed"
    
    with open(data_dir / "pdfs_processed.json", "r") as f:
        pdfs = json.load(f)
    
    with open(data_dir / "word_docs_processed.json", "r") as f:
        word_docs = json.load(f)
    
    with open(data_dir / "images_processed.json", "r") as f:
        images = json.load(f)
    
    return pdfs, word_docs, images


def main():
    print("=" * 70)
    print("LOADING PROCESSED DOCUMENTS INTO POSTGRESQL")
    print("Data will REMAIN loaded so you can verify it")
    print("=" * 70)
    
    # Load processed data
    print("\nLoading processed data...")
    pdfs, word_docs, images = load_processed_data()
    total_docs = len(pdfs) + len(word_docs) + len(images)
    print(f"✓ Loaded {len(pdfs):,} PDFs, {len(word_docs):,} Word docs, {len(images):,} images")
    
    # Connect to PostgreSQL
    client = PostgreSQLVectorClient()
    client.connect()
    
    # Create tables
    print("\n[PostgreSQL] Creating tables...")
    client.create_table("pdfs", vector_dim=384)
    client.create_table("word_docs", vector_dim=384)
    client.create_table("images", vector_dim=512)
    
    # Create vector indexes
    print("\n[PostgreSQL] Creating vector indexes...")
    client.create_vector_index("pdfs", index_type="ivfflat")
    client.create_vector_index("word_docs", index_type="ivfflat")
    client.create_vector_index("images", index_type="ivfflat")
    
    # Insert PDFs
    print(f"\n[PostgreSQL] Inserting {len(pdfs):,} PDFs...")
    pdf_docs = [{
        "filename": pdf["filename"],
        "text": pdf["text"],
        "policy_id": pdf.get("id", "UNKNOWN"),
        "policy_type": pdf.get("type", "pdf")
    } for pdf in pdfs]
    pdf_embeddings = [pdf["embedding"] for pdf in pdfs]
    client.insert_documents("pdfs", pdf_docs, pdf_embeddings)
    
    # Insert Word docs
    print(f"\n[PostgreSQL] Inserting {len(word_docs):,} Word docs...")
    word_doc_objs = [{
        "filename": doc["filename"],
        "text": doc["text"],
        "policy_id": doc.get("id", "UNKNOWN"),
        "policy_type": doc.get("type", "word")
    } for doc in word_docs]
    word_embeddings = [doc["embedding"] for doc in word_docs]
    client.insert_documents("word_docs", word_doc_objs, word_embeddings)
    
    # Insert Images
    print(f"\n[PostgreSQL] Inserting {len(images):,} Images...")
    image_docs = [{
        "filename": img["filename"],
        "text": img.get("description", ""),
        "policy_id": img.get("claim_id", "UNKNOWN"),
        "policy_type": img.get("damage_type", "unknown")
    } for img in images]
    image_embeddings = [img["image_embedding"] for img in images]
    client.insert_documents("images", image_docs, image_embeddings)
    
    print("\n" + "=" * 70)
    print(f"✓ ALL {total_docs:,} DOCUMENTS LOADED INTO POSTGRESQL!")
    print("=" * 70)
    
    print("\nYou can now verify the data in PostgreSQL:")
    print("\nPostgreSQL verification:")
    print("  docker exec -it postgres-standalone psql -U postgres -d vectordb -c \"SELECT COUNT(*) FROM pdfs;\"")
    print("  docker exec -it postgres-standalone psql -U postgres -d vectordb -c \"SELECT COUNT(*) FROM word_docs;\"")
    print("  docker exec -it postgres-standalone psql -U postgres -d vectordb -c \"SELECT COUNT(*) FROM images;\"")
    
    print("\nTables created in PostgreSQL:")
    print(f"  - pdfs: {len(pdfs):,} documents")
    print(f"  - word_docs: {len(word_docs):,} documents")
    print(f"  - images: {len(images):,} documents")
    
    print("\nTo clean up later, run:")
    print("  docker exec -it postgres-standalone psql -U postgres -d vectordb -c \"DROP TABLE IF EXISTS pdfs, word_docs, images;\"")
    print()
    
    client.disconnect()


if __name__ == "__main__":
    main()
