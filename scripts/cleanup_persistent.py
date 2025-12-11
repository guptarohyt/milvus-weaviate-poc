#!/usr/bin/env python3
"""
Clean up persistent collections from all three databases (Milvus, Weaviate, PostgreSQL).
"""

from pymilvus import connections, utility
import weaviate
import psycopg2

def cleanup_milvus():
    """Remove persistent collections from Milvus."""
    print("\n[Milvus] Cleaning up persistent collections...")
    connections.connect(host="localhost", port="19530")

    collections = ["persistent_pdfs", "persistent_word", "persistent_images"]
    for coll in collections:
        try:
            if utility.has_collection(coll):
                utility.drop_collection(coll)
                print(f"✓ Dropped collection: {coll}")
            else:
                print(f"⊘ Collection not found: {coll}")
        except Exception as e:
            print(f"✗ Error dropping {coll}: {e}")

def cleanup_weaviate():
    """Remove persistent collections from Weaviate."""
    print("\n[Weaviate] Cleaning up persistent collections...")
    client = weaviate.Client("http://localhost:8080")

    classes = ["PersistentPDFs", "PersistentWordDocs", "PersistentImages"]
    for cls in classes:
        try:
            client.schema.delete_class(cls)
            print(f"✓ Dropped class: {cls}")
        except Exception as e:
            if "could not find class" in str(e).lower():
                print(f"⊘ Class not found: {cls}")
            else:
                print(f"✗ Error dropping {cls}: {e}")

def cleanup_postgresql():
    """Remove persistent tables from PostgreSQL."""
    print("\n[PostgreSQL] Cleaning up persistent tables...")

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="vectordb"
        )
        cur = conn.cursor()

        tables = ["persistent_pdfs", "persistent_word_docs", "persistent_images"]
        for table in tables:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table};")
                conn.commit()
                print(f"✓ Dropped table: {table}")
            except Exception as e:
                print(f"✗ Error dropping {table}: {e}")
                conn.rollback()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"✗ Error connecting to PostgreSQL: {e}")

def main():
    print("=" * 70)
    print("CLEANING UP PERSISTENT DATA FROM ALL THREE DATABASES")
    print("=" * 70)

    cleanup_milvus()
    cleanup_weaviate()
    cleanup_postgresql()

    print("\n" + "=" * 70)
    print("✓ CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nAll persistent collections/tables have been removed.")
    print("The databases are now clean.")
    print()

if __name__ == "__main__":
    main()
