# How the Benchmark Works (Simple Explanation)

## The Setup
We have **100 insurance documents** stored in two databases (Milvus and Weaviate):
- 50 PDF policies
- 30 Word claim reports  
- 20 damage photos

## The Test
We pick **10 sample documents** from each type and use them to search the database.

## The Searches

**For each sample document, we try 3 different search methods:**

1. **Semantic Search** - "Find documents with similar meaning"
2. **Keyword Search** - "Find documents with similar words"
3. **Hybrid Search** - "Combine both methods"

## The Math

**Per document type:**
- 10 sample documents × 3 search methods = **30 searches**

**Total for one database:**
- PDFs: 30 searches
- Word docs: 30 searches
- Images: 30 searches
- **Total: 90 searches**

**For both databases:**
- Milvus: 90 searches
- Weaviate: 90 searches
- **Grand Total: 180 searches**

## What We Measure

**Performance (Speed):**
- How fast can each database complete these 90 searches?
- Measured in milliseconds

**Quality (Accuracy):**
- Did the database return the right documents?
- For example: If we search with a car insurance policy, did it find other car insurance policies?

---

## Simple Table Summary

| Document Type | Sample Queries | Search Methods | Total Searches |
|---------------|----------------|----------------|----------------|
| PDFs          | 10             | 3              | 30             |
| Word Docs     | 10             | 3              | 30             |
| Images        | 10             | 3              | 30             |
| **Per Database** | **30**     | **3**          | **90**         |
| **Both Databases** | **30**  | **3**          | **180**        |

---

## One-Sentence Summary

**"We use 10 sample documents from each type (PDFs, Word docs, Images) to search the database in 3 different ways, measuring how fast and accurate each database is - that's 90 searches per database, 180 total."**
