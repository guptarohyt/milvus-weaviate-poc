# How to View Data in Your Vector Databases

## Quick Start - View Data Right Now!

### Method 1: Interactive CLI Browser (Easiest) ⭐

```bash
cd scripts
source ../venv/bin/activate
python database_browser.py
```

Then follow the interactive prompts:
1. Choose "1" to list Milvus collections
2. Choose "3" to browse a collection (e.g., `images_phase2`)
3. View records, see vectors, explore metadata

### Method 2: Quick Status Check

```bash
cd scripts
source ../venv/bin/activate
python check_db_status.py
```

Shows what collections exist and how many records.

---

## Current Data in Your Databases

### Milvus Collections

| Collection | Records | Description |
|------------|---------|-------------|
| knowledge | 500 | Knowledge base articles |
| policies | 1000 | Insurance policies |
| claims | 2000 | Insurance claims |
| pdfs_phase2 | 100 | PDF documents with embeddings |
| word_docs_phase2 | 50 | Word documents with embeddings |
| images_phase2 | 200 | Images with dual embeddings (CLIP + text) |

### Weaviate Collections

| Collection | Records | Description |
|------------|---------|-------------|
| Knowledge | 500 | Knowledge base articles |
| Policy | 1000 | Insurance policies |
| Claim | 2000 | Insurance claims |
| PDFsPhase2 | 100 | PDF documents with embeddings |
| WordDocsPhase2 | 50 | Word documents with embeddings |
| ImagesPhase2 | 200 | Images with dual embeddings (CLIP + text) |

---

## Detailed Viewing Methods

### 1. Interactive CLI Browser

**File:** `scripts/database_browser.py`

**Features:**
- ✅ Browse all collections
- ✅ View individual records
- ✅ Inspect vector embeddings (first/last 5 values)
- ✅ Search by ID
- ✅ Beautiful formatted tables
- ✅ No additional installation needed

**Example Session:**
```bash
$ python database_browser.py

┌─────────────────────────────────────────┐
│    Database Browser                      │
└─────────────────────────────────────────┘

Main Menu:
1. List Milvus collections
2. List Weaviate collections
3. Browse Milvus collection
4. Browse Weaviate collection
5. Exit

Select option: 3
Enter collection name: images_phase2
How many records to show? [10]: 5

┌──────────────────────────────────────────────────────────┐
│ Collection: images_phase2                                 │
│ Total Entities: 200                                       │
│ Fields: id, filename, damage_type, severity, ...         │
└──────────────────────────────────────────────────────────┘

First 5 Records:
┌────────────┬─────────────────┬──────────────┬──────────┐
│ id         │ filename        │ damage_type  │ severity │
├────────────┼─────────────────┼──────────────┼──────────┤
│ IMG_001    │ hurricane_01... │ hurricane    │ 0.85     │
│ IMG_002    │ flood_01.png    │ flood        │ 0.72     │
│ IMG_003    │ fire_01.png     │ fire         │ 0.91     │
│ IMG_004    │ structural_0... │ structural   │ 0.68     │
│ IMG_005    │ hurricane_02... │ hurricane    │ 0.79     │
└────────────┴─────────────────┴──────────────┴──────────┘

View details of a specific record? [y/n]: y
Enter record ID: IMG_001

┌─────────────────────────────────────────┐
│ Record Details: IMG_001                  │
└─────────────────────────────────────────┘

id: IMG_001
filename: hurricane_01.png
damage_type: hurricane
severity: 0.85
claim_id: CLM_1234
policy_id: POL_5678
location: Miami, FL
description: Severe hurricane damage to residential property...

image_embedding: Vector with 512 dimensions
  First 5 values: [0.234, -0.567, 0.891, -0.123, 0.456]
  Last 5 values: [0.789, -0.234, 0.567, -0.891, 0.123]

text_embedding: Vector with 384 dimensions
  First 5 values: [0.123, -0.456, 0.789, -0.234, 0.567]
  Last 5 values: [0.891, -0.123, 0.456, -0.789, 0.234]
```

---

### 2. Attu (Milvus Web UI)

**Official Milvus administration tool with full GUI.**

#### Installation

**Option A: Docker (Recommended)**
```bash
docker run -d \
  --name attu \
  -p 8000:3000 \
  -e MILVUS_URL=host.docker.internal:19530 \
  zilliz/attu:latest
```

**Option B: Docker on Mac (use special hostname)**
```bash
docker run -d \
  --name attu \
  -p 8000:3000 \
  -e MILVUS_URL=host.docker.internal:19530 \
  zilliz/attu:latest
```

**Option C: Standalone Binary**
Download from: https://github.com/zilliztech/attu/releases

#### Usage

1. Open http://localhost:8000
2. Connect to Milvus:
   - Host: `localhost` (or `host.docker.internal` if in Docker)
   - Port: `19530`
   - Click "Connect"

3. You'll see:
   - **Collections Tab**: List all collections
   - **Data Tab**: Browse records with pagination
   - **Schema Tab**: View field definitions
   - **Search Tab**: Run vector searches
   - **Indexes Tab**: Manage indexes

#### Features

- ✅ Browse collections visually
- ✅ View records in table format
- ✅ See vector dimensions
- ✅ Run similarity searches
- ✅ Manage schemas and indexes
- ✅ Monitor performance
- ✅ Execute queries

**Screenshot Description:**
```
┌─────────────────────────────────────────────────────────┐
│ Attu - Milvus Administration Tool                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Collections (6)                                         │
│  ┌────────────────────┬──────────┬─────────────┐       │
│  │ Name               │ Entities │ Dimension   │       │
│  ├────────────────────┼──────────┼─────────────┤       │
│  │ images_phase2      │ 200      │ 512, 384    │       │
│  │ pdfs_phase2        │ 100      │ 384         │       │
│  │ word_docs_phase2   │ 50       │ 384         │       │
│  └────────────────────┴──────────┴─────────────┘       │
│                                                          │
│  [View Data] [Schema] [Search] [Indexes]                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### 3. Weaviate Console

**Built-in GraphQL interface for Weaviate.**

#### Access

**Option A: Local Console (Simple)**
```
URL: http://localhost:8080/v1/console
```

**Option B: Weaviate Cloud Console (Better UI)**
```
URL: https://console.weaviate.cloud/
Connection: http://localhost:8080
```

#### GraphQL Examples

**List all collections:**
```graphql
{
  __schema {
    types {
      name
    }
  }
}
```

**View PDF documents:**
```graphql
{
  Get {
    PDFsPhase2(limit: 10) {
      doc_id
      filename
      text
      num_pages
      has_tables
      _additional {
        id
        distance
      }
    }
  }
}
```

**View images with vectors:**
```graphql
{
  Get {
    ImagesPhase2(limit: 5) {
      image_id
      filename
      damage_type
      severity
      claim_id
      description
      _additional {
        id
        vector
      }
    }
  }
}
```

**Search for similar images (vector search):**
```graphql
{
  Get {
    ImagesPhase2(
      nearVector: {
        vector: [0.1, 0.2, 0.3, ...]  # 384-dim vector
        targetVectors: ["text_vector"]
      }
      limit: 5
    ) {
      damage_type
      description
      _additional {
        distance
      }
    }
  }
}
```

**Filter by damage type:**
```graphql
{
  Get {
    ImagesPhase2(
      where: {
        path: ["damage_type"]
        operator: Equal
        valueText: "hurricane"
      }
      limit: 10
    ) {
      image_id
      filename
      severity
      description
    }
  }
}
```

#### Features

- ✅ GraphQL query interface
- ✅ Schema browser
- ✅ Object explorer
- ✅ Vector search testing
- ✅ Filter testing
- ✅ Export results

---

### 4. MinIO Console (Storage Layer)

**View the underlying storage for Milvus data.**

#### Access

```
URL: http://localhost:9001
Username: minioadmin
Password: minioadmin
```

#### What You'll See

```
milvus-bucket/
├── delta_log/
│   └── 446290870058913833/  <- Collection ID
│       └── 446290870058913834/  <- Partition
│           └── binlog files
│
├── insert_log/
│   └── 446290870058913833/  <- Collection ID
│       └── 446290870058913834/  <- Partition
│           ├── 446290870058913835/  <- Field: id
│           │   └── segment_*.binlog
│           ├── 446290870058913836/  <- Field: embedding
│           │   └── segment_*.binlog
│           └── ...
│
└── index/
    └── 446290870058913833/
        └── index files
```

#### Understanding the Files

- **Binlog Files**: Binary logs containing actual data (vectors, metadata)
- **Segment Files**: Collections split into segments for efficiency
- **Index Files**: Pre-computed search structures (IVF_FLAT, etc.)

**Note:** These are binary files - you can't read them directly, but you can:
- See file sizes (understand storage usage)
- Download for backup
- Verify data persistence
- Monitor storage growth

---

## Quick Command Reference

### Check Database Status
```bash
cd scripts
source ../venv/bin/activate
python check_db_status.py
```

### Browse Data Interactively
```bash
cd scripts
source ../venv/bin/activate
python database_browser.py
```

### Extract Vectors to JSON
```bash
cd scripts
source ../venv/bin/activate
python extract_vectors_from_dbs.py
```

### View Attu (Web UI)
```bash
# Start Attu
docker run -d --name attu -p 8000:3000 \
  -e MILVUS_URL=host.docker.internal:19530 \
  zilliz/attu:latest

# Access
open http://localhost:8000
```

### View Weaviate Console
```bash
open http://localhost:8080/v1/console
# or
open https://console.weaviate.cloud/
```

### View MinIO
```bash
open http://localhost:9001
# Login: minioadmin / minioadmin
```

---

## Comparison of Viewing Methods

| Method | Ease of Use | Features | Best For |
|--------|-------------|----------|----------|
| **CLI Browser** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Quick browsing, command-line fans |
| **Attu** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Milvus power users, visual exploration |
| **Weaviate Console** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Weaviate users, GraphQL developers |
| **MinIO Console** | ⭐⭐⭐ | ⭐⭐ | Storage debugging, backups |

---

## Troubleshooting

### "Connection refused" errors

**Check if databases are running:**
```bash
docker ps | grep -E "milvus|weaviate"
```

**Restart if needed:**
```bash
docker-compose restart
```

### "No collections found"

**Re-run setup to load data:**
```bash
cd scripts
python milvus_multimodal_client.py
python weaviate_multimodal_client.py
```

### Attu can't connect

**For Mac/Linux, use:**
```bash
docker run -d --name attu -p 8000:3000 \
  -e MILVUS_URL=host.docker.internal:19530 \
  zilliz/attu:latest
```

**For custom networks:**
```bash
# Find Milvus container IP
docker inspect milvus-standalone | grep IPAddress

# Use that IP in Attu
docker run -d --name attu -p 8000:3000 \
  -e MILVUS_URL=<MILVUS_IP>:19530 \
  zilliz/attu:latest
```

---

## Next Steps

1. **Try the CLI browser:**
   ```bash
   cd scripts
   python database_browser.py
   ```

2. **Install Attu for visual exploration:**
   ```bash
   docker run -d --name attu -p 8000:3000 \
     -e MILVUS_URL=host.docker.internal:19530 \
     zilliz/attu:latest
   ```

3. **Explore Weaviate Console:**
   ```bash
   open https://console.weaviate.cloud/
   # Connect to: http://localhost:8080
   ```

4. **Browse MinIO storage:**
   ```bash
   open http://localhost:9001
   ```

---

## Summary

You now have **4 ways** to view your vector database data:

1. ✅ **CLI Browser** - Interactive terminal UI (ready now!)
2. ✅ **Attu** - Full-featured Milvus web UI
3. ✅ **Weaviate Console** - GraphQL query interface
4. ✅ **MinIO Console** - Storage layer browser

Your databases already contain:
- **3,500 Phase 1 records** (knowledge, policies, claims)
- **350 Phase 2 records** (100 PDFs, 50 Word docs, 200 images)

**Start browsing now:**
```bash
cd scripts && python database_browser.py
```
