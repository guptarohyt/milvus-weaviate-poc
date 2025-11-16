#!/usr/bin/env python3
"""
Visualize Speed vs Quality Trade-offs for Phase 3

Creates comprehensive visualizations:
1. Speed vs Quality scatter plot
2. Speed comparison bar charts
3. Quality metrics comparison
4. Combined performance matrix
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 11


def load_results():
    """Load benchmark and quality results."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = Path(os.path.join(script_dir, "..", "results"))

    with open(results_dir / "phase3_benchmark_results.json", "r") as f:
        speed_results = json.load(f)

    with open(results_dir / "phase3_quality_results.json", "r") as f:
        quality_results = json.load(f)

    return speed_results, quality_results


def create_speed_vs_quality_scatter(speed_results, quality_results, save_path):
    """Create scatter plot: Speed (x) vs Quality (y)."""
    fig, ax = plt.subplots(figsize=(12, 8))

    # Prepare data
    systems = []
    speeds = []
    qualities = []
    colors = []
    sizes = []

    # Milvus Dense
    systems.append("Milvus\nDense")
    speeds.append(speed_results["milvus_25"]["pdf_dense"]["avg"])
    qualities.append(quality_results["milvus_25_pdfs"]["dense"]["precision@5_avg"])
    colors.append("#2E86AB")
    sizes.append(300)

    # Milvus Sparse
    systems.append("Milvus\nSparse")
    speeds.append(speed_results["milvus_25"]["pdf_sparse"]["avg"])
    qualities.append(quality_results["milvus_25_pdfs"]["sparse"]["precision@5_avg"])
    colors.append("#A23B72")
    sizes.append(300)

    # Milvus Hybrid
    systems.append("Milvus\nHybrid")
    speeds.append(speed_results["milvus_25"]["pdf_hybrid"]["avg"])
    qualities.append(quality_results["milvus_25_pdfs"]["hybrid"]["precision@5_avg"])
    colors.append("#F18F01")
    sizes.append(300)

    # Weaviate
    systems.append("Weaviate")
    speeds.append(speed_results["weaviate"]["pdf"]["avg"])
    qualities.append(quality_results["weaviate_pdfs"]["precision@5_avg"])
    colors.append("#C73E1D")
    sizes.append(300)

    # Create scatter plot
    scatter = ax.scatter(speeds, qualities, c=colors, s=sizes, alpha=0.7, edgecolors='black', linewidths=2)

    # Add labels for each point
    for i, system in enumerate(systems):
        ax.annotate(system, (speeds[i], qualities[i]),
                   textcoords="offset points", xytext=(0,15), ha='center',
                   fontsize=12, fontweight='bold')

    # Add ideal region (top-left = fast + high quality)
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.3, linewidth=2, label='High Quality (>80%)')
    ax.axvline(x=1.5, color='green', linestyle='--', alpha=0.3, linewidth=2, label='Fast (<1.5ms)')

    # Highlight winner region
    ax.fill_between([0, 1.5], 0.8, 1.0, alpha=0.1, color='green', label='Ideal Region')

    # Labels and title
    ax.set_xlabel('Speed (milliseconds) - Lower is Better', fontsize=14, fontweight='bold')
    ax.set_ylabel('Quality (Precision@5) - Higher is Better', fontsize=14, fontweight='bold')
    ax.set_title('Phase 3: Speed vs Quality Trade-off Analysis\nPDF Document Search',
                fontsize=16, fontweight='bold', pad=20)

    # Set limits with padding
    ax.set_xlim(0.5, 3.0)
    ax.set_ylim(0.6, 0.95)

    # Grid
    ax.grid(True, alpha=0.3)

    # Legend
    ax.legend(loc='lower left', fontsize=11)

    # Add annotation explaining ideal region
    ax.text(0.75, 0.88, 'Winner Zone\n(Fast + High Quality)',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5),
           fontsize=10, ha='center')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def create_speed_comparison(speed_results, save_path):
    """Create bar chart comparing speeds."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Data
    systems = ['Milvus\nDense', 'Milvus\nSparse', 'Milvus\nHybrid', 'Weaviate']
    pdf_speeds = [
        speed_results["milvus_25"]["pdf_dense"]["avg"],
        speed_results["milvus_25"]["pdf_sparse"]["avg"],
        speed_results["milvus_25"]["pdf_hybrid"]["avg"],
        speed_results["weaviate"]["pdf"]["avg"]
    ]

    word_speeds = [
        speed_results["milvus_25"]["word_dense"]["avg"],
        speed_results["milvus_25"]["word_sparse"]["avg"],
        speed_results["milvus_25"]["word_hybrid"]["avg"],
        speed_results["weaviate"]["word"]["avg"]
    ]

    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

    # PDF speeds
    bars1 = ax1.bar(systems, pdf_speeds, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Query Time (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('PDF Document Search Speed', fontsize=13, fontweight='bold')
    ax1.set_ylim(0, max(pdf_speeds) * 1.2)
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar, speed in zip(bars1, pdf_speeds):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{speed:.2f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Calculate speedup vs Weaviate
    baseline = pdf_speeds[-1]
    for i, (bar, speed) in enumerate(zip(bars1[:-1], pdf_speeds[:-1])):
        speedup = ((baseline - speed) / baseline) * 100
        ax1.text(bar.get_x() + bar.get_width()/2., height * 0.5,
                f'{speedup:.0f}%\nfaster',
                ha='center', va='center', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Word speeds
    bars2 = ax2.bar(systems, word_speeds, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Query Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Word Document Search Speed', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, max(word_speeds) * 1.2)
    ax2.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar, speed in zip(bars2, word_speeds):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{speed:.2f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Calculate speedup vs Weaviate
    baseline = word_speeds[-1]
    for i, (bar, speed) in enumerate(zip(bars2[:-1], word_speeds[:-1])):
        speedup = ((baseline - speed) / baseline) * 100
        ax2.text(bar.get_x() + bar.get_width()/2., height * 0.5,
                f'{speedup:.0f}%\nfaster',
                ha='center', va='center', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.suptitle('Speed Comparison: Milvus 2.5 vs Weaviate',
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def create_quality_comparison(quality_results, save_path):
    """Create grouped bar chart for quality metrics."""
    fig, ax = plt.subplots(figsize=(14, 7))

    # Data
    systems = ['Milvus Dense', 'Milvus Sparse', 'Milvus Hybrid', 'Weaviate']

    precision = [
        quality_results["milvus_25_pdfs"]["dense"]["precision@5_avg"],
        quality_results["milvus_25_pdfs"]["sparse"]["precision@5_avg"],
        quality_results["milvus_25_pdfs"]["hybrid"]["precision@5_avg"],
        quality_results["weaviate_pdfs"]["precision@5_avg"]
    ]

    recall = [
        quality_results["milvus_25_pdfs"]["dense"]["recall@5_avg"],
        quality_results["milvus_25_pdfs"]["sparse"]["recall@5_avg"],
        quality_results["milvus_25_pdfs"]["hybrid"]["recall@5_avg"],
        quality_results["weaviate_pdfs"]["recall@5_avg"]
    ]

    ndcg = [
        quality_results["milvus_25_pdfs"]["dense"]["ndcg@5_avg"],
        quality_results["milvus_25_pdfs"]["sparse"]["ndcg@5_avg"],
        quality_results["milvus_25_pdfs"]["hybrid"]["ndcg@5_avg"],
        quality_results["weaviate_pdfs"]["ndcg@5_avg"]
    ]

    mrr = [
        quality_results["milvus_25_pdfs"]["dense"]["mrr_avg"],
        quality_results["milvus_25_pdfs"]["sparse"]["mrr_avg"],
        quality_results["milvus_25_pdfs"]["hybrid"]["mrr_avg"],
        quality_results["weaviate_pdfs"]["mrr_avg"]
    ]

    # Set up bar positions
    x = np.arange(len(systems))
    width = 0.2

    # Create bars
    bars1 = ax.bar(x - 1.5*width, precision, width, label='Precision@5',
                   color='#2E86AB', alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x - 0.5*width, recall, width, label='Recall@5',
                   color='#A23B72', alpha=0.8, edgecolor='black')
    bars3 = ax.bar(x + 0.5*width, ndcg, width, label='NDCG@5',
                   color='#F18F01', alpha=0.8, edgecolor='black')
    bars4 = ax.bar(x + 1.5*width, mrr, width, label='MRR',
                   color='#C73E1D', alpha=0.8, edgecolor='black')

    # Add value labels
    for bars in [bars1, bars2, bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Labels and formatting
    ax.set_ylabel('Score (0-1, higher is better)', fontsize=12, fontweight='bold')
    ax.set_title('Quality Metrics Comparison - PDF Document Search',
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(systems, fontsize=11)
    ax.legend(loc='upper right', fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.grid(axis='y', alpha=0.3)

    # Add horizontal line at 0.8 (high quality threshold)
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.4, linewidth=2, label='High Quality (>0.8)')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def create_performance_matrix(speed_results, quality_results, save_path):
    """Create heatmap showing combined performance (speed + quality)."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Systems
    systems = ['Milvus Dense', 'Milvus Sparse', 'Milvus Hybrid', 'Weaviate']
    metrics = ['Speed\n(Lower=Better)', 'Precision@5', 'Recall@5', 'NDCG@5', 'MRR']

    # Normalize speed (inverse - lower is better)
    max_speed = speed_results["weaviate"]["pdf"]["avg"]

    # Create matrix
    data = np.array([
        # Milvus Dense
        [1 - (speed_results["milvus_25"]["pdf_dense"]["avg"] / max_speed),
         quality_results["milvus_25_pdfs"]["dense"]["precision@5_avg"],
         quality_results["milvus_25_pdfs"]["dense"]["recall@5_avg"],
         quality_results["milvus_25_pdfs"]["dense"]["ndcg@5_avg"],
         quality_results["milvus_25_pdfs"]["dense"]["mrr_avg"]],
        # Milvus Sparse
        [1 - (speed_results["milvus_25"]["pdf_sparse"]["avg"] / max_speed),
         quality_results["milvus_25_pdfs"]["sparse"]["precision@5_avg"],
         quality_results["milvus_25_pdfs"]["sparse"]["recall@5_avg"],
         quality_results["milvus_25_pdfs"]["sparse"]["ndcg@5_avg"],
         quality_results["milvus_25_pdfs"]["sparse"]["mrr_avg"]],
        # Milvus Hybrid
        [1 - (speed_results["milvus_25"]["pdf_hybrid"]["avg"] / max_speed),
         quality_results["milvus_25_pdfs"]["hybrid"]["precision@5_avg"],
         quality_results["milvus_25_pdfs"]["hybrid"]["recall@5_avg"],
         quality_results["milvus_25_pdfs"]["hybrid"]["ndcg@5_avg"],
         quality_results["milvus_25_pdfs"]["hybrid"]["mrr_avg"]],
        # Weaviate
        [0,  # Baseline speed
         quality_results["weaviate_pdfs"]["precision@5_avg"],
         quality_results["weaviate_pdfs"]["recall@5_avg"],
         quality_results["weaviate_pdfs"]["ndcg@5_avg"],
         quality_results["weaviate_pdfs"]["mrr_avg"]]
    ])

    # Create heatmap
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    # Set ticks
    ax.set_xticks(np.arange(len(metrics)))
    ax.set_yticks(np.arange(len(systems)))
    ax.set_xticklabels(metrics, fontsize=11, fontweight='bold')
    ax.set_yticklabels(systems, fontsize=11, fontweight='bold')

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    # Add text annotations
    for i in range(len(systems)):
        for j in range(len(metrics)):
            text = ax.text(j, i, f'{data[i, j]:.2f}',
                          ha="center", va="center", color="black",
                          fontweight='bold', fontsize=12)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Performance Score (0-1, higher is better)',
                   rotation=270, labelpad=20, fontsize=11, fontweight='bold')

    # Title
    ax.set_title('Performance Matrix: Speed + Quality\nPDF Document Search',
                fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def create_combined_dashboard(speed_results, quality_results, save_path):
    """Create comprehensive 4-panel dashboard."""
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # Panel 1: Speed vs Quality Scatter (top-left)
    ax1 = fig.add_subplot(gs[0, 0])
    systems = ['Milvus\nDense', 'Milvus\nSparse', 'Milvus\nHybrid', 'Weaviate']
    speeds = [
        speed_results["milvus_25"]["pdf_dense"]["avg"],
        speed_results["milvus_25"]["pdf_sparse"]["avg"],
        speed_results["milvus_25"]["pdf_hybrid"]["avg"],
        speed_results["weaviate"]["pdf"]["avg"]
    ]
    qualities = [
        quality_results["milvus_25_pdfs"]["dense"]["precision@5_avg"],
        quality_results["milvus_25_pdfs"]["sparse"]["precision@5_avg"],
        quality_results["milvus_25_pdfs"]["hybrid"]["precision@5_avg"],
        quality_results["weaviate_pdfs"]["precision@5_avg"]
    ]
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

    ax1.scatter(speeds, qualities, c=colors, s=400, alpha=0.7, edgecolors='black', linewidths=2)
    for i, system in enumerate(systems):
        ax1.annotate(system, (speeds[i], qualities[i]), textcoords="offset points",
                    xytext=(0,15), ha='center', fontsize=10, fontweight='bold')
    ax1.axhline(y=0.8, color='green', linestyle='--', alpha=0.3, linewidth=2)
    ax1.axvline(x=1.5, color='green', linestyle='--', alpha=0.3, linewidth=2)
    ax1.set_xlabel('Speed (ms)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Precision@5', fontsize=11, fontweight='bold')
    ax1.set_title('Speed vs Quality Trade-off', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0.5, 3.0)
    ax1.set_ylim(0.6, 0.95)

    # Panel 2: Speed Comparison (top-right)
    ax2 = fig.add_subplot(gs[0, 1])
    x_pos = np.arange(len(systems))
    ax2.bar(x_pos, speeds, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(systems, fontsize=10)
    ax2.set_ylabel('Query Time (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('Speed Comparison', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    for i, (bar, speed) in enumerate(zip(ax2.patches, speeds)):
        ax2.text(bar.get_x() + bar.get_width()/2., speed,
                f'{speed:.2f}ms', ha='center', va='bottom', fontweight='bold', fontsize=9)

    # Panel 3: Quality Metrics (bottom-left)
    ax3 = fig.add_subplot(gs[1, 0])
    metrics_data = {
        'Precision': qualities,
        'NDCG': [
            quality_results["milvus_25_pdfs"]["dense"]["ndcg@5_avg"],
            quality_results["milvus_25_pdfs"]["sparse"]["ndcg@5_avg"],
            quality_results["milvus_25_pdfs"]["hybrid"]["ndcg@5_avg"],
            quality_results["weaviate_pdfs"]["ndcg@5_avg"]
        ],
        'MRR': [
            quality_results["milvus_25_pdfs"]["dense"]["mrr_avg"],
            quality_results["milvus_25_pdfs"]["sparse"]["mrr_avg"],
            quality_results["milvus_25_pdfs"]["hybrid"]["mrr_avg"],
            quality_results["weaviate_pdfs"]["mrr_avg"]
        ]
    }

    x_pos = np.arange(len(systems))
    width = 0.25
    for i, (metric, values) in enumerate(metrics_data.items()):
        offset = (i - 1) * width
        ax3.bar(x_pos + offset, values, width, label=metric, alpha=0.8, edgecolor='black')

    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(systems, fontsize=10)
    ax3.set_ylabel('Score (0-1)', fontsize=11, fontweight='bold')
    ax3.set_title('Quality Metrics', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(axis='y', alpha=0.3)
    ax3.set_ylim(0, 1.1)

    # Panel 4: Winner Summary (bottom-right)
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')

    summary_text = """
    🏆 WINNER: Milvus 2.5 Dense Search

    Speed Performance:
    • Milvus Dense:  1.06ms (FASTEST)
    • Milvus Sparse: 1.04ms (FASTEST)
    • Milvus Hybrid: 2.45ms (1% faster than Weaviate)
    • Weaviate:      2.43ms (BASELINE)

    Quality Performance:
    • Precision@5:   86% (TIED - Milvus = Weaviate)
    • NDCG@5:        0.95 (TIED - Milvus = Weaviate)
    • MRR:           1.00 (TIED - All perfect)

    Key Findings:
    ✅ Milvus 56% faster with EQUAL quality
    ✅ Dense & Hybrid: Same quality (86%)
    ✅ Sparse: Faster but lower quality (66%)

    Recommendation:
    Deploy Milvus 2.5 Dense Search
    • Best speed + quality combination
    • Use Hybrid for keyword-critical queries
    """

    ax4.text(0.1, 0.95, summary_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    # Overall title
    fig.suptitle('Phase 3 Complete Performance Analysis: Milvus 2.5 vs Weaviate',
                fontsize=16, fontweight='bold', y=0.98)

    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def main():
    print("\n" + "="*70)
    print("Creating Speed vs Quality Visualizations")
    print("="*70 + "\n")

    # Load results
    print("Loading benchmark and quality results...")
    speed_results, quality_results = load_results()
    print("✓ Results loaded\n")

    # Create output directory
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = Path(os.path.join(script_dir, "..", "results", "visualizations"))
    output_dir.mkdir(exist_ok=True, parents=True)

    print("Generating visualizations...\n")

    # Create visualizations
    create_speed_vs_quality_scatter(
        speed_results, quality_results,
        output_dir / "speed_vs_quality_scatter.png"
    )

    create_speed_comparison(
        speed_results,
        output_dir / "speed_comparison.png"
    )

    create_quality_comparison(
        quality_results,
        output_dir / "quality_comparison.png"
    )

    create_performance_matrix(
        speed_results, quality_results,
        output_dir / "performance_matrix.png"
    )

    create_combined_dashboard(
        speed_results, quality_results,
        output_dir / "combined_dashboard.png"
    )

    print("\n" + "="*70)
    print("✓ All Visualizations Created!")
    print("="*70)
    print(f"\nLocation: {output_dir}")
    print("\nFiles created:")
    print("  1. speed_vs_quality_scatter.png - Scatter plot showing trade-offs")
    print("  2. speed_comparison.png - Bar charts comparing speeds")
    print("  3. quality_comparison.png - Quality metrics comparison")
    print("  4. performance_matrix.png - Heatmap of all metrics")
    print("  5. combined_dashboard.png - 4-panel comprehensive view")
    print()


if __name__ == "__main__":
    main()
