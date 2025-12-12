#!/usr/bin/env python3
"""
Load processed data into databases WITHOUT cleanup - so you can verify it's there.
"""

import json
from pathlib import Path
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import weaviate
import sys
sys.path.append(str(Path(__file__).parent))
from milvus_25_hybrid_client import Milvus25HybridClient
from postgresql_client import PostgreSQLVectorClient
from sqlserver_client import SQLServerVectorClient
from config import config

def load_processed_data():
    """Load all processed multi-modal data."""
    data_dir = config.data.processed_dir

    with open(data_dir / "pdfs_processed.json", "r") as f:
        pdfs = json.load(f)

    with open(data_dir / "word_docs_processed.json", "r") as f:
        word_docs = json.load(f)

    with open(data_dir / "images_processed.json", "r") as f:
        images = json.load(f)

    return pdfs, word_docs, images

def main():
    print("=" * 70)
    print("LOADING PROCESSED DOCUMENTS INTO DATABASES")
    print("Data will REMAIN loaded so you can verify it")
    print("=" * 70)

    # Load processed data
    print("\nLoading processed data...")
    pdfs, word_docs, images = load_processed_data()
    print(f"✓ Loaded {len(pdfs):,} PDFs, {len(word_docs):,} Word docs, {len(images):,} images")

    # Connect to Milvus
    client = Milvus25HybridClient()
    client.connect()

    # Create collections
    print("\n[Milvus] Creating collections...")
    pdf_collection = client.create_hybrid_collection("persistent_pdfs", dense_dim=384)
    word_collection = client.create_hybrid_collection("persistent_word", dense_dim=384)
    image_collection = client.create_hybrid_collection("persistent_images", dense_dim=512)

    # Create indexes
    print("[Milvus] Creating indexes...")
    client.create_indexes(pdf_collection)
    client.create_indexes(word_collection)
    client.create_indexes(image_collection)

    # Insert PDFs
    print(f"\n[Milvus] Inserting {len(pdfs):,} PDFs...")
    pdf_embeddings = [doc["embedding"] for doc in pdfs]
    client.insert_documents(pdf_collection, pdfs, pdf_embeddings)

    # Insert Word docs
    print(f"[Milvus] Inserting {len(word_docs):,} Word docs...")
    word_embeddings = [doc["embedding"] for doc in word_docs]
    client.insert_documents(word_collection, word_docs, word_embeddings)

    # Insert Images
    print(f"[Milvus] Inserting {len(images):,} Images...")
    image_docs = [{"filename": img["filename"], "text": img.get("description", ""),
                   "policy_id": img.get("claim_id", "UNKNOWN"),
                   "policy_type": img.get("damage_type", "unknown")}
                  for img in images]
    image_embeddings = [img["image_embedding"] for img in images]
    client.insert_documents(image_collection, image_docs, image_embeddings)

    # Load collections to memory
    print("\n[Milvus] Loading collections to memory...")
    pdf_collection.load()
    word_collection.load()
    image_collection.load()

    # Now load into Weaviate
    print("\n[Weaviate] Setting up collections...")
    weaviate_client = weaviate.Client(config.weaviate.url)

    # Create PDF collection
    pdf_schema = {
        "class": "PersistentPDFs",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "policy_id", "dataType": ["text"]},
            {"name": "policy_type", "dataType": ["text"]}
        ]
    }

    try:
        weaviate_client.schema.delete_class("PersistentPDFs")
        print("✓ Dropped existing PersistentPDFs collection")
    except:
        pass

    weaviate_client.schema.create_class(pdf_schema)
    print("✓ Created PersistentPDFs collection")

    # Insert PDFs
    print(f"[Weaviate] Inserting {len(pdfs):,} PDFs...")
    with weaviate_client.batch as batch:
        batch.batch_size = 1000
        for pdf in pdfs:
            properties = {
                "filename": pdf["filename"],
                "text": pdf["text"],
                "policy_id": pdf.get("id", "UNKNOWN"),
                "policy_type": pdf.get("type", "pdf")
            }
            batch.add_data_object(properties, "PersistentPDFs", vector=pdf["embedding"])
    print(f"✓ Inserted {len(pdfs):,} PDFs")

    # Create Word collection
    word_schema = {
        "class": "PersistentWordDocs",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "doc_id", "dataType": ["text"]},
            {"name": "doc_type", "dataType": ["text"]}
        ]
    }

    try:
        weaviate_client.schema.delete_class("PersistentWordDocs")
        print("✓ Dropped existing PersistentWordDocs collection")
    except:
        pass

    weaviate_client.schema.create_class(word_schema)
    print("✓ Created PersistentWordDocs collection")

    # Insert Word docs
    print(f"[Weaviate] Inserting {len(word_docs):,} Word docs...")
    with weaviate_client.batch as batch:
        batch.batch_size = 1000
        for word in word_docs:
            properties = {
                "filename": word["filename"],
                "text": word["text"],
                "doc_id": word.get("id", "UNKNOWN"),
                "doc_type": word.get("type", "word")
            }
            batch.add_data_object(properties, "PersistentWordDocs", vector=word["embedding"])
    print(f"✓ Inserted {len(word_docs):,} Word docs")

    # Create Image collection
    image_schema = {
        "class": "PersistentImages",
        "vectorizer": "none",
        "properties": [
            {"name": "filename", "dataType": ["text"]},
            {"name": "description", "dataType": ["text"]},
            {"name": "claim_id", "dataType": ["text"]},
            {"name": "damage_type", "dataType": ["text"]}
        ]
    }

    try:
        weaviate_client.schema.delete_class("PersistentImages")
        print("✓ Dropped existing PersistentImages collection")
    except:
        pass

    weaviate_client.schema.create_class(image_schema)
    print("✓ Created PersistentImages collection")

    # Insert Images
    print(f"[Weaviate] Inserting {len(images):,} Images...")
    with weaviate_client.batch as batch:
        batch.batch_size = 1000
        for img in images:
            properties = {
                "filename": img["filename"],
                "description": img.get("description", ""),
                "claim_id": img.get("claim_id", "UNKNOWN"),
                "damage_type": img.get("damage_type", "unknown")
            }
            batch.add_data_object(properties, "PersistentImages", vector=img["image_embedding"])
    print(f"✓ Inserted {len(images):,} Images")

    # Now load into PostgreSQL
    print("\n[PostgreSQL] Setting up tables...")
    pg_client = PostgreSQLVectorClient()
    pg_client.connect()

    # Create tables
    print("[PostgreSQL] Creating tables...")
    pg_client.create_table("persistent_pdfs", vector_dim=384)
    pg_client.create_table("persistent_word_docs", vector_dim=384)
    pg_client.create_table("persistent_images", vector_dim=512)

    # Insert PDFs
    print(f"[PostgreSQL] Inserting {len(pdfs):,} PDFs...")
    pdf_docs = [{
        "filename": p["filename"],
        "text": p["text"],
        "policy_id": p.get("id", "UNKNOWN"),
        "policy_type": p.get("type", "pdf")
    } for p in pdfs]
    pdf_embeddings = [p["embedding"] for p in pdfs]
    pg_client.insert_documents("persistent_pdfs", pdf_docs, pdf_embeddings)

    print("[PostgreSQL] Creating PDF HNSW index...")
    pg_client.create_vector_index("persistent_pdfs", index_type="hnsw")
    print(f"✓ Inserted {len(pdfs):,} PDFs")

    # Insert Word docs
    print(f"[PostgreSQL] Inserting {len(word_docs):,} Word docs...")
    word_doc_objs = [{
        "filename": w["filename"],
        "text": w["text"],
        "policy_id": w.get("id", "UNKNOWN"),
        "policy_type": w.get("type", "word")
    } for w in word_docs]
    word_embeddings = [w["embedding"] for w in word_docs]
    pg_client.insert_documents("persistent_word_docs", word_doc_objs, word_embeddings)

    print("[PostgreSQL] Creating Word doc HNSW index...")
    pg_client.create_vector_index("persistent_word_docs", index_type="hnsw")
    print(f"✓ Inserted {len(word_docs):,} Word docs")

    # Insert Images
    print(f"[PostgreSQL] Inserting {len(images):,} Images...")
    image_docs_pg = [{
        "filename": img["filename"],
        "text": img.get("description", ""),
        "policy_id": img.get("claim_id", "UNKNOWN"),
        "policy_type": img.get("damage_type", "unknown")
    } for img in images]
    image_embeddings = [img["image_embedding"] for img in images]
    pg_client.insert_documents("persistent_images", image_docs_pg, image_embeddings)

    print("[PostgreSQL] Creating Image HNSW index...")
    pg_client.create_vector_index("persistent_images", index_type="hnsw")
    print(f"✓ Inserted {len(images):,} Images")

    # Now load into SQL Server
    print("\n[SQL Server] Setting up tables...")
    ss_client = SQLServerVectorClient()
    ss_client.connect()

    # Create tables
    print("[SQL Server] Creating tables...")
    ss_client.create_table("persistent_pdfs", vector_dim=384)
    ss_client.create_table("persistent_word_docs", vector_dim=384)
    ss_client.create_table("persistent_images", vector_dim=512)

    # Insert PDFs
    print(f"[SQL Server] Inserting {len(pdfs):,} PDFs...")
    ss_client.insert_documents("persistent_pdfs", pdf_docs, pdf_embeddings)

    print("[SQL Server] Creating PDF full-text index...")
    ss_client.create_fulltext_index("persistent_pdfs")
    print(f"✓ Inserted {len(pdfs):,} PDFs")

    # Insert Word docs
    print(f"[SQL Server] Inserting {len(word_docs):,} Word docs...")
    ss_client.insert_documents("persistent_word_docs", word_doc_objs, word_embeddings)

    print("[SQL Server] Creating Word doc full-text index...")
    ss_client.create_fulltext_index("persistent_word_docs")
    print(f"✓ Inserted {len(word_docs):,} Word docs")

    # Insert Images
    print(f"[SQL Server] Inserting {len(images):,} Images...")
    ss_client.insert_documents("persistent_images", image_docs_pg, image_embeddings)
    print(f"✓ Inserted {len(images):,} Images")

    total_docs = len(pdfs) + len(word_docs) + len(images)
    print("\n" + "=" * 70)
    print(f"✓ ALL {total_docs:,} DOCUMENTS LOADED INTO ALL FOUR DATABASES!")
    print("=" * 70)
    print("\nYou can now verify the data in all four databases:")
    print("\nMilvus verification:")
    print("  python -c \"from pymilvus import *; connections.connect(); print('PDFs:', Collection('persistent_pdfs').num_entities)\"")
    print("\nWeaviate verification:")
    print("  python -c \"import weaviate; from scripts.config import config; c = weaviate.Client(config.weaviate.url); print('PDFs:', c.query.aggregate('PersistentPDFs').with_meta_count().do())\"")
    print("\nPostgreSQL verification:")
    print("  python scripts/check_postgres.py")
    print("\nOr use the interactive browser:")
    print("  python scripts/database_browser.py")
    print("\nCollections/Tables created in ALL THREE databases:")
    print("\nMilvus:")
    print("  - persistent_pdfs: {:,} documents".format(len(pdfs)))
    print("  - persistent_word: {:,} documents".format(len(word_docs)))
    print("  - persistent_images: {:,} documents".format(len(images)))
    print("\nWeaviate:")
    print("  - PersistentPDFs: {:,} documents".format(len(pdfs)))
    print("  - PersistentWordDocs: {:,} documents".format(len(word_docs)))
    print("  - PersistentImages: {:,} documents".format(len(images)))
    print("\nPostgreSQL:")
    print("  - persistent_pdfs: {:,} documents".format(len(pdfs)))
    print("  - persistent_word_docs: {:,} documents".format(len(word_docs)))
    print("  - persistent_images: {:,} documents".format(len(images)))
    print("\nSQL Server:")
    print("  - persistent_pdfs: {:,} documents".format(len(pdfs)))
    print("  - persistent_word_docs: {:,} documents".format(len(word_docs)))
    print("  - persistent_images: {:,} documents".format(len(images)))
    print("\nTo clean up later, run:")
    print("  python scripts/cleanup_persistent.py")
    print()

if __name__ == "__main__":
    main()
