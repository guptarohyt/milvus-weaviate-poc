"""
Visualize embeddings from Milvus and Weaviate using dimensionality reduction.
Supports t-SNE, UMAP, and PCA for 2D/3D projections.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("⚠️  UMAP not installed. Install with: pip install umap-learn")


class EmbeddingVisualizer:
    """Visualize high-dimensional embeddings in 2D/3D."""

    def __init__(self):
        """Initialize visualizer."""
        self.data_dir = Path("./data/multimodal/processed")
        self.output_dir = Path("./visualizations")
        self.output_dir.mkdir(exist_ok=True)

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)

    def load_embeddings(self, data_type: str) -> Tuple[np.ndarray, List[str], List[Dict]]:
        """
        Load embeddings from processed data.

        Args:
            data_type: 'pdfs', 'word_docs', or 'images'

        Returns:
            embeddings: numpy array of shape (n_samples, embedding_dim)
            labels: list of labels for each embedding
            metadata: list of metadata dicts for each sample
        """
        file_map = {
            'pdfs': 'pdfs_processed.json',
            'word_docs': 'word_docs_processed.json',
            'images': 'images_processed.json'
        }

        data_file = self.data_dir / file_map[data_type]

        with open(data_file) as f:
            data = json.load(f)

        if data_type == 'images':
            # Images have dual embeddings - use text embeddings for consistency
            embeddings = np.array([item['text_embedding'] for item in data])
            labels = [item['damage_type'] for item in data]
            metadata = data
        else:
            embeddings = np.array([item['embedding'] for item in data])
            labels = [item['filename'] for item in data]
            metadata = data

        print(f"✓ Loaded {len(embeddings)} {data_type} embeddings")
        print(f"  Embedding dimension: {embeddings.shape[1]}")

        return embeddings, labels, metadata

    def reduce_dimensions_tsne(self, embeddings: np.ndarray,
                               n_components: int = 2,
                               perplexity: int = 30,
                               random_state: int = 42) -> np.ndarray:
        """
        Reduce dimensions using t-SNE.

        t-SNE (t-Distributed Stochastic Neighbor Embedding) preserves local structure.
        Good for visualizing clusters and patterns.

        Args:
            embeddings: High-dimensional embeddings
            n_components: 2 or 3 for 2D/3D visualization
            perplexity: Balance between local and global structure (5-50)

        Returns:
            reduced: Low-dimensional embeddings
        """
        print(f"\nReducing dimensions with t-SNE to {n_components}D...")
        print(f"  Perplexity: {perplexity}")

        tsne = TSNE(
            n_components=n_components,
            perplexity=perplexity,
            random_state=random_state,
            n_iter=1000,
            verbose=1
        )

        reduced = tsne.fit_transform(embeddings)
        print(f"✓ Reduced to shape: {reduced.shape}")

        return reduced

    def reduce_dimensions_pca(self, embeddings: np.ndarray,
                              n_components: int = 2) -> np.ndarray:
        """
        Reduce dimensions using PCA.

        PCA (Principal Component Analysis) finds directions of maximum variance.
        Fast but linear - may not capture complex patterns.

        Args:
            embeddings: High-dimensional embeddings
            n_components: 2 or 3 for 2D/3D visualization

        Returns:
            reduced: Low-dimensional embeddings
        """
        print(f"\nReducing dimensions with PCA to {n_components}D...")

        pca = PCA(n_components=n_components, random_state=42)
        reduced = pca.fit_transform(embeddings)

        print(f"✓ Reduced to shape: {reduced.shape}")
        print(f"  Explained variance: {pca.explained_variance_ratio_.sum():.2%}")

        return reduced

    def reduce_dimensions_umap(self, embeddings: np.ndarray,
                               n_components: int = 2,
                               n_neighbors: int = 15,
                               min_dist: float = 0.1) -> np.ndarray:
        """
        Reduce dimensions using UMAP.

        UMAP (Uniform Manifold Approximation and Projection) preserves both
        local and global structure. Often better than t-SNE.

        Args:
            embeddings: High-dimensional embeddings
            n_components: 2 or 3 for 2D/3D visualization
            n_neighbors: Balance between local and global structure (2-100)
            min_dist: Minimum distance between points (0.0-0.99)

        Returns:
            reduced: Low-dimensional embeddings
        """
        if not UMAP_AVAILABLE:
            raise ImportError("UMAP not installed. Install with: pip install umap-learn")

        print(f"\nReducing dimensions with UMAP to {n_components}D...")
        print(f"  n_neighbors: {n_neighbors}, min_dist: {min_dist}")

        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=42,
            verbose=True
        )

        reduced = reducer.fit_transform(embeddings)
        print(f"✓ Reduced to shape: {reduced.shape}")

        return reduced

    def plot_2d(self, embeddings_2d: np.ndarray,
                labels: List[str],
                title: str,
                output_file: str,
                color_by_category: bool = True):
        """
        Create 2D scatter plot.

        Args:
            embeddings_2d: 2D embeddings
            labels: Labels for each point
            title: Plot title
            output_file: Output filename
            color_by_category: Color points by category (for images)
        """
        fig, ax = plt.subplots(figsize=(14, 10))

        if color_by_category and any('damage_type' in str(label) for label in labels):
            # For images, color by damage type
            unique_categories = list(set(labels))
            colors = sns.color_palette("husl", len(unique_categories))
            color_map = dict(zip(unique_categories, colors))

            for category in unique_categories:
                mask = np.array([label == category for label in labels])
                ax.scatter(
                    embeddings_2d[mask, 0],
                    embeddings_2d[mask, 1],
                    c=[color_map[category]],
                    label=category,
                    alpha=0.6,
                    s=100,
                    edgecolors='white',
                    linewidth=0.5
                )

            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                     frameon=True, fancybox=True, shadow=True)
        else:
            # For documents, use gradient coloring
            scatter = ax.scatter(
                embeddings_2d[:, 0],
                embeddings_2d[:, 1],
                c=np.arange(len(embeddings_2d)),
                cmap='viridis',
                alpha=0.6,
                s=100,
                edgecolors='white',
                linewidth=0.5
            )
            plt.colorbar(scatter, ax=ax, label='Document Index')

        ax.set_xlabel('Dimension 1', fontsize=12)
        ax.set_ylabel('Dimension 2', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved 2D plot to: {self.output_dir / output_file}")
        plt.close()

    def plot_3d(self, embeddings_3d: np.ndarray,
                labels: List[str],
                title: str,
                output_file: str,
                color_by_category: bool = True):
        """
        Create 3D scatter plot.

        Args:
            embeddings_3d: 3D embeddings
            labels: Labels for each point
            title: Plot title
            output_file: Output filename
            color_by_category: Color points by category (for images)
        """
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')

        if color_by_category and any('damage_type' in str(label) for label in labels):
            # For images, color by damage type
            unique_categories = list(set(labels))
            colors = sns.color_palette("husl", len(unique_categories))
            color_map = dict(zip(unique_categories, colors))

            for category in unique_categories:
                mask = np.array([label == category for label in labels])
                ax.scatter(
                    embeddings_3d[mask, 0],
                    embeddings_3d[mask, 1],
                    embeddings_3d[mask, 2],
                    c=[color_map[category]],
                    label=category,
                    alpha=0.6,
                    s=100,
                    edgecolors='white',
                    linewidth=0.5
                )

            ax.legend(bbox_to_anchor=(1.15, 1), loc='upper left',
                     frameon=True, fancybox=True, shadow=True)
        else:
            # For documents, use gradient coloring
            scatter = ax.scatter(
                embeddings_3d[:, 0],
                embeddings_3d[:, 1],
                embeddings_3d[:, 2],
                c=np.arange(len(embeddings_3d)),
                cmap='viridis',
                alpha=0.6,
                s=100,
                edgecolors='white',
                linewidth=0.5
            )
            fig.colorbar(scatter, ax=ax, label='Document Index', shrink=0.5)

        ax.set_xlabel('Dimension 1', fontsize=12)
        ax.set_ylabel('Dimension 2', fontsize=12)
        ax.set_zlabel('Dimension 3', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()
        plt.savefig(self.output_dir / output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved 3D plot to: {self.output_dir / output_file}")
        plt.close()

    def visualize_data_type(self, data_type: str, methods: List[str] = None):
        """
        Visualize embeddings for a specific data type.

        Args:
            data_type: 'pdfs', 'word_docs', or 'images'
            methods: List of methods to use ['tsne', 'pca', 'umap']
        """
        if methods is None:
            methods = ['tsne', 'pca']
            if UMAP_AVAILABLE:
                methods.append('umap')

        print(f"\n{'='*70}")
        print(f"VISUALIZING {data_type.upper()} EMBEDDINGS")
        print(f"{'='*70}")

        # Load embeddings
        embeddings, labels, metadata = self.load_embeddings(data_type)

        # Determine if we should color by category
        color_by_category = (data_type == 'images')

        # Apply each dimensionality reduction method
        for method in methods:
            print(f"\n--- Using {method.upper()} ---")

            # 2D visualization
            if method == 'tsne':
                reduced_2d = self.reduce_dimensions_tsne(embeddings, n_components=2)
            elif method == 'pca':
                reduced_2d = self.reduce_dimensions_pca(embeddings, n_components=2)
            elif method == 'umap':
                reduced_2d = self.reduce_dimensions_umap(embeddings, n_components=2)

            self.plot_2d(
                reduced_2d,
                labels,
                f"{data_type.replace('_', ' ').title()} - {method.upper()} 2D Projection",
                f"{data_type}_{method}_2d.png",
                color_by_category=color_by_category
            )

            # 3D visualization
            if method == 'tsne':
                reduced_3d = self.reduce_dimensions_tsne(embeddings, n_components=3)
            elif method == 'pca':
                reduced_3d = self.reduce_dimensions_pca(embeddings, n_components=3)
            elif method == 'umap':
                reduced_3d = self.reduce_dimensions_umap(embeddings, n_components=3)

            self.plot_3d(
                reduced_3d,
                labels,
                f"{data_type.replace('_', ' ').title()} - {method.upper()} 3D Projection",
                f"{data_type}_{method}_3d.png",
                color_by_category=color_by_category
            )

    def create_comparison_plot(self):
        """Create side-by-side comparison of all data types."""
        print(f"\n{'='*70}")
        print("CREATING COMPARISON PLOT")
        print(f"{'='*70}")

        fig, axes = plt.subplots(1, 3, figsize=(20, 6))

        data_types = ['pdfs', 'word_docs', 'images']
        titles = ['PDF Documents', 'Word Documents', 'Images']

        for idx, (data_type, title) in enumerate(zip(data_types, titles)):
            embeddings, labels, _ = self.load_embeddings(data_type)

            # Use PCA for speed
            reduced = self.reduce_dimensions_pca(embeddings, n_components=2)

            if data_type == 'images':
                # Color by damage type
                unique_categories = list(set(labels))
                colors = sns.color_palette("husl", len(unique_categories))
                color_map = dict(zip(unique_categories, colors))

                for category in unique_categories:
                    mask = np.array([label == category for label in labels])
                    axes[idx].scatter(
                        reduced[mask, 0],
                        reduced[mask, 1],
                        c=[color_map[category]],
                        label=category,
                        alpha=0.6,
                        s=50
                    )
                axes[idx].legend(fontsize=8)
            else:
                axes[idx].scatter(
                    reduced[:, 0],
                    reduced[:, 1],
                    c=np.arange(len(reduced)),
                    cmap='viridis',
                    alpha=0.6,
                    s=50
                )

            axes[idx].set_title(title, fontsize=14, fontweight='bold')
            axes[idx].set_xlabel('PC1', fontsize=10)
            axes[idx].set_ylabel('PC2', fontsize=10)
            axes[idx].grid(True, alpha=0.3)

        plt.suptitle('Multi-Modal Embedding Comparison (PCA)',
                     fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comparison_all_types.png',
                   dpi=300, bbox_inches='tight')
        print(f"✓ Saved comparison plot to: {self.output_dir / 'comparison_all_types.png'}")
        plt.close()


def main():
    """Main entry point."""
    print("="*70)
    print("EMBEDDING VISUALIZATION TOOL")
    print("="*70)
    print("\nThis tool visualizes high-dimensional embeddings using:")
    print("  • t-SNE: Preserves local structure (good for clusters)")
    print("  • PCA: Fast linear reduction (good for variance)")
    print("  • UMAP: Preserves local + global structure (best overall)")
    print()

    visualizer = EmbeddingVisualizer()

    # Visualize each data type
    visualizer.visualize_data_type('pdfs')
    visualizer.visualize_data_type('word_docs')
    visualizer.visualize_data_type('images')

    # Create comparison plot
    visualizer.create_comparison_plot()

    print(f"\n{'='*70}")
    print("VISUALIZATION COMPLETE")
    print(f"{'='*70}")
    print(f"All visualizations saved to: {visualizer.output_dir}")
    print("\nGenerated files:")
    for file in sorted(visualizer.output_dir.glob("*.png")):
        print(f"  • {file.name}")


if __name__ == "__main__":
    main()
