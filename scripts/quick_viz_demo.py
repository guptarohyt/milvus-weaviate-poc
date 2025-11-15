"""
Quick visualization demo - shows how to visualize embeddings in just a few lines.
Run this after generating and processing data.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from pathlib import Path


def quick_viz():
    """Create a quick 2D PCA visualization of image embeddings."""

    # Check if data exists
    data_file = Path("./data/multimodal/processed/images_processed.json")
    if not data_file.exists():
        print("❌ Data not found!")
        print("\nPlease run these commands first:")
        print("  1. python generate_multimodal_data.py --type images --count 200")
        print("  2. python process_multimodal_data.py --type images")
        return

    # Load data
    print("Loading image embeddings...")
    with open(data_file) as f:
        images = json.load(f)

    # Extract embeddings and labels
    embeddings = np.array([img['text_embedding'] for img in images])
    damage_types = [img['damage_type'] for img in images]

    print(f"✓ Loaded {len(embeddings)} images")
    print(f"  Embedding dimension: {embeddings.shape[1]}")
    print(f"  Damage types: {set(damage_types)}")

    # Reduce to 2D with PCA
    print("\nReducing 384 dimensions to 2D with PCA...")
    pca = PCA(n_components=2, random_state=42)
    embeddings_2d = pca.fit_transform(embeddings)

    print(f"✓ Reduced to 2D")
    print(f"  Explained variance: {pca.explained_variance_ratio_.sum():.2%}")

    # Plot
    print("\nCreating visualization...")
    fig, ax = plt.subplots(figsize=(12, 8))

    # Color by damage type
    unique_types = list(set(damage_types))
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
    color_map = dict(zip(unique_types, colors))

    for damage_type in unique_types:
        mask = np.array([dt == damage_type for dt in damage_types])
        ax.scatter(
            embeddings_2d[mask, 0],
            embeddings_2d[mask, 1],
            c=[color_map[damage_type]],
            label=damage_type,
            alpha=0.7,
            s=100,
            edgecolors='white',
            linewidth=0.5
        )

    ax.set_xlabel('Principal Component 1', fontsize=12)
    ax.set_ylabel('Principal Component 2', fontsize=12)
    ax.set_title('Insurance Damage Images - 2D PCA Projection',
                 fontsize=14, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save
    output_dir = Path("./visualizations")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "quick_demo.png"

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved visualization to: {output_file}")

    # Show interpretation
    print("\n" + "="*60)
    print("INTERPRETATION")
    print("="*60)
    print("\nWhat you're seeing:")
    print("  • Each point = one damage assessment image")
    print("  • Colors = different damage types (hurricane, flood, fire, etc.)")
    print("  • Proximity = semantic similarity in the embedding space")
    print("  • Clusters = groups of similar damage types")
    print("\nKey insights:")
    print(f"  • PCA explains {pca.explained_variance_ratio_.sum():.1%} of variance")
    print("  • Similar damage types should cluster together")
    print("  • Overlaps = ambiguous or multi-type damage")

    print("\n💡 Tip: Try running the full visualization tool for more:")
    print("   python visualize_embeddings.py")


if __name__ == "__main__":
    quick_viz()
