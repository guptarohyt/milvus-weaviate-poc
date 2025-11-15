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

print("\n" + "=" * 60)
