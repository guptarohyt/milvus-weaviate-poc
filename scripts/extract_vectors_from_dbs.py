"""
Extract embeddings directly from Milvus and Weaviate databases.
Demonstrates how to retrieve vectors from the databases for analysis and visualization.
"""

import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any
from pymilvus import connections, Collection, utility
import weaviate


class VectorExtractor:
    """Extract vectors from Milvus and Weaviate for visualization."""

    def __init__(self):
        """Initialize connections to both databases."""
        self.output_dir = Path("./extracted_vectors")
        self.output_dir.mkdir(exist_ok=True)

    def extract_from_milvus(self, collection_name: str, vector_field: str = "embedding"):
        """
        Extract vectors from Milvus collection.

        Args:
            collection_name: Name of the collection
            vector_field: Name of the vector field to extract

        Returns:
            Dictionary with vectors and metadata
        """
        print(f"\n{'='*60}")
        print(f"EXTRACTING FROM MILVUS: {collection_name}")
        print(f"{'='*60}")

        # Connect to Milvus
        connections.connect(alias="default", host="localhost", port="19530")
        print("✓ Connected to Milvus")

        # Load collection
        collection = Collection(collection_name)
        collection.load()
        print(f"✓ Loaded collection: {collection_name}")

        # Get all entities
        num_entities = collection.num_entities
        print(f"  Total entities: {num_entities}")

        # Query all data (limit for large collections)
        limit = min(num_entities, 1000)
        query_result = collection.query(
            expr="id != ''",  # Match all
            output_fields=["id", vector_field],
            limit=limit
        )

        print(f"✓ Retrieved {len(query_result)} entities")

        # Extract vectors
        vectors = []
        ids = []
        for entity in query_result:
            ids.append(entity['id'])
            vectors.append(entity[vector_field])

        vectors = np.array(vectors)
        print(f"  Vector shape: {vectors.shape}")

        # Save to file
        output_file = self.output_dir / f"milvus_{collection_name}_vectors.json"
        data = {
            'collection': collection_name,
            'vector_field': vector_field,
            'num_vectors': len(vectors),
            'dimension': vectors.shape[1],
            'ids': ids,
            'vectors': vectors.tolist()
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved to: {output_file}")

        # Cleanup
        connections.disconnect(alias="default")

        return data

    def extract_from_weaviate(self, collection_name: str, vector_name: str = None):
        """
        Extract vectors from Weaviate collection.

        Args:
            collection_name: Name of the collection
            vector_name: Name of the vector (for named vectors)

        Returns:
            Dictionary with vectors and metadata
        """
        print(f"\n{'='*60}")
        print(f"EXTRACTING FROM WEAVIATE: {collection_name}")
        print(f"{'='*60}")

        # Connect to Weaviate
        client = weaviate.connect_to_local(host="localhost", port=8080)
        print("✓ Connected to Weaviate")

        # Get collection
        collection = client.collections.get(collection_name)

        # Fetch all objects with vectors
        response = collection.query.fetch_objects(
            limit=1000,
            include_vector=True
        )

        print(f"✓ Retrieved {len(response.objects)} objects")

        # Extract vectors
        vectors = []
        ids = []
        properties_list = []

        for obj in response.objects:
            ids.append(str(obj.uuid))

            # Handle named vectors vs single vector
            if vector_name:
                vectors.append(obj.vector[vector_name])
            else:
                vectors.append(obj.vector['default'] if isinstance(obj.vector, dict) else obj.vector)

            properties_list.append(obj.properties)

        vectors = np.array(vectors)
        print(f"  Vector shape: {vectors.shape}")

        # Save to file
        vector_suffix = f"_{vector_name}" if vector_name else ""
        output_file = self.output_dir / f"weaviate_{collection_name}{vector_suffix}_vectors.json"

        data = {
            'collection': collection_name,
            'vector_name': vector_name,
            'num_vectors': len(vectors),
            'dimension': vectors.shape[1],
            'ids': ids,
            'vectors': vectors.tolist(),
            'properties': properties_list[:10]  # Sample of properties
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved to: {output_file}")

        # Cleanup
        client.close()

        return data

    def compare_vectors(self, milvus_data: Dict, weaviate_data: Dict):
        """
        Compare vectors from Milvus and Weaviate.

        Args:
            milvus_data: Data from Milvus
            weaviate_data: Data from Weaviate
        """
        print(f"\n{'='*60}")
        print("VECTOR COMPARISON")
        print(f"{'='*60}")

        milvus_vectors = np.array(milvus_data['vectors'])
        weaviate_vectors = np.array(weaviate_data['vectors'])

        print(f"\nMilvus:")
        print(f"  Collection: {milvus_data['collection']}")
        print(f"  Shape: {milvus_vectors.shape}")
        print(f"  Mean: {milvus_vectors.mean():.6f}")
        print(f"  Std: {milvus_vectors.std():.6f}")

        print(f"\nWeaviate:")
        print(f"  Collection: {weaviate_data['collection']}")
        print(f"  Shape: {weaviate_vectors.shape}")
        print(f"  Mean: {weaviate_vectors.mean():.6f}")
        print(f"  Std: {weaviate_vectors.std():.6f}")

        # Check if vectors are the same (if same data was loaded)
        if milvus_vectors.shape == weaviate_vectors.shape:
            # Sort by ID to compare
            milvus_sorted_idx = np.argsort(milvus_data['ids'])
            weaviate_sorted_idx = np.argsort(weaviate_data['ids'])

            milvus_sorted = milvus_vectors[milvus_sorted_idx]
            weaviate_sorted = weaviate_vectors[weaviate_sorted_idx]

            # Compare first few vectors
            max_diff = np.abs(milvus_sorted[:10] - weaviate_sorted[:10]).max()
            print(f"\nMax difference (first 10 vectors): {max_diff:.10f}")

            if max_diff < 1e-6:
                print("✓ Vectors are identical (same data loaded)")
            else:
                print("⚠️  Vectors differ (may be different data or ordering)")


def main():
    """Main entry point."""
    print("="*70)
    print("VECTOR EXTRACTION FROM DATABASES")
    print("="*70)
    print("\nThis script demonstrates how to extract embeddings directly from")
    print("Milvus and Weaviate for analysis and visualization.")
    print()

    extractor = VectorExtractor()

    # Extract from Milvus
    print("\n" + "="*70)
    print("MILVUS EXTRACTIONS")
    print("="*70)

    try:
        pdf_milvus = extractor.extract_from_milvus("pdfs_phase2", "embedding")
    except Exception as e:
        print(f"✗ Error extracting PDFs from Milvus: {e}")
        pdf_milvus = None

    try:
        images_milvus = extractor.extract_from_milvus("images_phase2", "text_embedding")
    except Exception as e:
        print(f"✗ Error extracting images from Milvus: {e}")
        images_milvus = None

    # Extract from Weaviate
    print("\n" + "="*70)
    print("WEAVIATE EXTRACTIONS")
    print("="*70)

    try:
        pdf_weaviate = extractor.extract_from_weaviate("PDFsPhase2")
    except Exception as e:
        print(f"✗ Error extracting PDFs from Weaviate: {e}")
        pdf_weaviate = None

    try:
        images_weaviate = extractor.extract_from_weaviate("ImagesPhase2", "text_vector")
    except Exception as e:
        print(f"✗ Error extracting images from Weaviate: {e}")
        images_weaviate = None

    # Compare
    if pdf_milvus and pdf_weaviate:
        extractor.compare_vectors(pdf_milvus, pdf_weaviate)

    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Extracted vectors saved to: {extractor.output_dir}")
    print("\nYou can now use these vectors for:")
    print("  • Dimensionality reduction (t-SNE, UMAP, PCA)")
    print("  • Clustering analysis")
    print("  • Similarity analysis")
    print("  • Custom visualizations")


if __name__ == "__main__":
    main()
