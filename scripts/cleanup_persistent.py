#!/usr/bin/env python3
"""
Clean up persistent collections from both Milvus and Weaviate databases.
"""

from pymilvus import connections, utility
import weaviate

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

def main():
    print("=" * 70)
    print("CLEANING UP PERSISTENT 50K DATA FROM BOTH DATABASES")
    print("=" * 70)

    cleanup_milvus()
    cleanup_weaviate()

    print("\n" + "=" * 70)
    print("✓ CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nAll persistent collections have been removed.")
    print("The databases are now clean.")
    print()

if __name__ == "__main__":
    main()
