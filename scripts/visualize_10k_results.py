#!/usr/bin/env python3
"""
Generate visualizations for 10K document benchmark results.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def load_results():
    """Load benchmark results."""
    with open("results/phase3_benchmark_results.json") as f:
        return json.load(f)

def create_speed_comparison():
    """Create comprehensive speed comparison chart."""
    results = load_results()

    # Prepare data
    categories = ['PDF\nDense', 'PDF\nSparse', 'PDF\nHybrid',
                  'Word\nDense', 'Word\nSparse', 'Word\nHybrid',
                  'Image']

    milvus_times = [
        results['milvus_25']['pdf_dense']['avg'],
        results['milvus_25']['pdf_sparse']['avg'],
        results['milvus_25']['pdf_hybrid']['avg'],
        results['milvus_25']['word_dense']['avg'],
        results['milvus_25']['word_sparse']['avg'],
        results['milvus_25']['word_hybrid']['avg'],
        results['milvus_25']['image_dense']['avg']
    ]

    weaviate_times = [
        results['weaviate']['pdf']['avg'],
        results['weaviate']['pdf']['avg'],  # Weaviate doesn't separate sparse/hybrid
        results['weaviate']['pdf']['avg'],
        results['weaviate']['word']['avg'],
        results['weaviate']['word']['avg'],
        results['weaviate']['word']['avg'],
        results['weaviate']['image']['avg']
    ]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))

    bars1 = ax.bar(x - width/2, milvus_times, width, label='Milvus 2.5',
                   color='#2E86AB', edgecolor='black', linewidth=1.2)
    bars2 = ax.bar(x + width/2, weaviate_times, width, label='Weaviate',
                   color='#A23B72', edgecolor='black', linewidth=1.2)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}ms',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Search Type', fontsize=13, fontweight='bold')
    ax.set_ylabel('Average Query Time (ms)', fontsize=13, fontweight='bold')
    ax.set_title('10K Document Benchmark: Milvus 2.5 vs Weaviate\nQuery Speed Comparison',
                fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig('results/10k_speed_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: results/10k_speed_comparison.png")
    plt.close()

def create_speedup_chart():
    """Create speedup/improvement chart."""
    results = load_results()

    categories = ['PDF Dense', 'Word Dense', 'Image']
    milvus_times = [
        results['milvus_25']['pdf_dense']['avg'],
        results['milvus_25']['word_dense']['avg'],
        results['milvus_25']['image_dense']['avg']
    ]
    weaviate_times = [
        results['weaviate']['pdf']['avg'],
        results['weaviate']['word']['avg'],
        results['weaviate']['image']['avg']
    ]

    speedups = [(w / m) for m, w in zip(milvus_times, weaviate_times)]
    improvements = [(w - m) / w * 100 for m, w in zip(milvus_times, weaviate_times)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Speedup chart
    bars1 = ax1.bar(categories, speedups, color='#2E86AB', edgecolor='black', linewidth=1.2)
    ax1.axhline(y=1, color='red', linestyle='--', linewidth=2, label='Baseline (1x)')

    for i, (bar, speedup) in enumerate(zip(bars1, speedups)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{speedup:.2f}x',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax1.set_ylabel('Speedup Factor', fontsize=13, fontweight='bold')
    ax1.set_title('Milvus 2.5 Speedup vs Weaviate\n(10K Documents)',
                 fontsize=14, fontweight='bold', pad=15)
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Improvement percentage chart
    bars2 = ax2.bar(categories, improvements, color='#F18F01', edgecolor='black', linewidth=1.2)

    for i, (bar, imp) in enumerate(zip(bars2, improvements)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{imp:.1f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax2.set_ylabel('Performance Improvement (%)', fontsize=13, fontweight='bold')
    ax2.set_title('Milvus 2.5 Performance Improvement\n(10K Documents)',
                 fontsize=14, fontweight='bold', pad=15)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig('results/10k_speedup_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: results/10k_speedup_comparison.png")
    plt.close()

def create_hybrid_search_chart():
    """Create hybrid search comparison."""
    results = load_results()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # PDF Hybrid Search
    pdf_types = ['Dense', 'Sparse', 'Hybrid']
    pdf_times = [
        results['milvus_25']['pdf_dense']['avg'],
        results['milvus_25']['pdf_sparse']['avg'],
        results['milvus_25']['pdf_hybrid']['avg']
    ]

    bars1 = ax1.bar(pdf_types, pdf_times, color=['#2E86AB', '#A23B72', '#F18F01'],
                   edgecolor='black', linewidth=1.2)

    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}ms',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax1.set_ylabel('Average Query Time (ms)', fontsize=13, fontweight='bold')
    ax1.set_title('PDF Search: Dense vs Sparse vs Hybrid\n(Milvus 2.5, 10K Docs)',
                 fontsize=14, fontweight='bold', pad=15)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Word Hybrid Search
    word_types = ['Dense', 'Sparse', 'Hybrid']
    word_times = [
        results['milvus_25']['word_dense']['avg'],
        results['milvus_25']['word_sparse']['avg'],
        results['milvus_25']['word_hybrid']['avg']
    ]

    bars2 = ax2.bar(word_types, word_times, color=['#2E86AB', '#A23B72', '#F18F01'],
                   edgecolor='black', linewidth=1.2)

    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}ms',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax2.set_ylabel('Average Query Time (ms)', fontsize=13, fontweight='bold')
    ax2.set_title('Word Doc Search: Dense vs Sparse vs Hybrid\n(Milvus 2.5, 10K Docs)',
                 fontsize=14, fontweight='bold', pad=15)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig('results/10k_hybrid_search_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: results/10k_hybrid_search_comparison.png")
    plt.close()

def main():
    print("\n" + "="*60)
    print("Generating 10K Benchmark Visualizations")
    print("="*60 + "\n")

    create_speed_comparison()
    create_speedup_chart()
    create_hybrid_search_chart()

    print("\n" + "="*60)
    print("✓ All visualizations generated successfully!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
