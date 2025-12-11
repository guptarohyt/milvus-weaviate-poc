#!/usr/bin/env python3
"""Quick script to check what data exists in databases."""

from pymilvus import connections, utility, Collection
import weaviate

print("=" * 60)
print("DATABASE STATUS CHECK")
print("=" * 60)

# Check Milvus
print("\n🔷 MILVUS:")
try:
    connections.connect(alias="default", host="localhost", port="19530")
    collections = utility.list_collections()

    if collections:
        print(f"  ✓ Connected")
        print(f"  Collections found: {len(collections)}")
        for coll_name in collections:
            coll = Collection(coll_name)
            coll.flush()
            print(f"    • {coll_name}: {coll.num_entities} entities")
    else:
        print("  ✓ Connected")
        print("  ⚠️  No collections found (database is empty)")

    connections.disconnect(alias="default")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Check Weaviate
print("\n🔶 WEAVIATE:")
try:
    client = weaviate.connect_to_local(host="localhost", port=8080)
    collections = client.collections.list_all()

    if collections:
        print(f"  ✓ Connected")
        print(f"  Collections found: {len(collections)}")
        for name in collections.keys():
            try:
                coll = client.collections.get(name)
                agg = coll.aggregate.over_all()
                print(f"    • {name}: {agg.total_count} objects")
            except:
                print(f"    • {name}: Unknown count")
    else:
        print("  ✓ Connected")
        print("  ⚠️  No collections found (database is empty)")

    client.close()
except Exception as e:
    print(f"  ✗ Error: {e}")

# Check PostgreSQL
print("\n🐘 POSTGRESQL:")
try:
    import psycopg2
    conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="postgres", database="vectordb")
    cur = conn.cursor()
    
    # Check for tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    
    if tables:
        print(f"  ✓ Connected")
        print(f"  Tables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            cur.execute(f"SELECT count(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"    • {table_name}: {count} rows")
    else:
        print("  ✓ Connected")
        print("  ⚠️  No tables found (database is empty)")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
