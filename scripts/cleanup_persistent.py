#!/usr/bin/env python3
"""
Clean up persistent collections from all four databases (Milvus, Weaviate, PostgreSQL, SQL Server).
"""

from pymilvus import connections, utility
import weaviate
import psycopg2
import pyodbc

from config import config


def cleanup_milvus():
    """Remove persistent collections from Milvus."""
    print("\n[Milvus] Cleaning up persistent collections...")
    connections.connect(host=config.milvus.host, port=str(config.milvus.port))

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
    client = weaviate.Client(config.weaviate.url)

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
            host=config.postgresql.host,
            port=config.postgresql.port,
            user=config.postgresql.user,
            password=config.postgresql.password,
            database=config.postgresql.database
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


def cleanup_sqlserver():
    """Remove persistent tables from SQL Server."""
    print("\n[SQL Server] Cleaning up persistent tables...")

    try:
        conn_str = config.sqlserver.connection_string
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()

        tables = ["persistent_pdfs", "persistent_word_docs", "persistent_images"]
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table};")
                print(f"✓ Dropped table: {table}")
            except Exception as e:
                print(f"✗ Error dropping {table}: {e}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✗ Error connecting to SQL Server: {e}")


def main():
    print("=" * 70)
    print("CLEANING UP PERSISTENT DATA FROM ALL FOUR DATABASES")
    print("=" * 70)

    cleanup_milvus()
    cleanup_weaviate()
    cleanup_postgresql()
    cleanup_sqlserver()

    print("\n" + "=" * 70)
    print("✓ CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nAll persistent collections/tables have been removed.")
    print("The databases are now clean.")
    print()


if __name__ == "__main__":
    main()
