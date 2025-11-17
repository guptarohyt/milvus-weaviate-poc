#!/usr/bin/env python3
"""
Generate custom-sized dataset with configurable splits.

Usage examples:
  # Default 10K dataset
  python generate_custom_dataset.py

  # Custom split
  python generate_custom_dataset.py --pdfs 8000 --word 5000 --images 3000

  # Just PDFs
  python generate_custom_dataset.py --pdfs 50000 --word 0 --images 0

  # Proportional scaling (e.g., 100K total with same ratios)
  python generate_custom_dataset.py --total 100000 --pdf-ratio 0.5 --word-ratio 0.3 --image-ratio 0.2
"""

import sys
import os
import argparse

# Change to scripts directory so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add parent directory to path to import generate_multimodal_data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_multimodal_data import generate_all_pdfs, generate_all_word_docs, generate_all_images


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate custom-sized multi-modal dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10K dataset (default)
  %(prog)s

  # Generate 100K dataset with same ratios
  %(prog)s --total 100000

  # Custom split
  %(prog)s --pdfs 8000 --word 5000 --images 3000

  # Only PDFs (for large-scale testing)
  %(prog)s --pdfs 50000 --word 0 --images 0

  # Custom ratios
  %(prog)s --total 50000 --pdf-ratio 0.6 --word-ratio 0.3 --image-ratio 0.1
        """
    )

    # Method 1: Specify exact counts
    parser.add_argument('--pdfs', type=int, help='Number of PDF documents to generate')
    parser.add_argument('--word', type=int, help='Number of Word documents to generate')
    parser.add_argument('--images', type=int, help='Number of images to generate')

    # Method 2: Specify total + ratios
    parser.add_argument('--total', type=int, help='Total number of documents')
    parser.add_argument('--pdf-ratio', type=float, default=0.5,
                       help='Ratio of PDFs (default: 0.5 = 50%%)')
    parser.add_argument('--word-ratio', type=float, default=0.3,
                       help='Ratio of Word docs (default: 0.3 = 30%%)')
    parser.add_argument('--image-ratio', type=float, default=0.2,
                       help='Ratio of Images (default: 0.2 = 20%%)')

    # Options
    parser.add_argument('--skip-confirmation', action='store_true',
                       help='Skip confirmation prompt')

    return parser.parse_args()


def calculate_counts(args):
    """Calculate document counts based on arguments."""

    # Method 1: Exact counts specified
    if args.pdfs is not None or args.word is not None or args.images is not None:
        pdf_count = args.pdfs if args.pdfs is not None else 5000
        word_count = args.word if args.word is not None else 3000
        image_count = args.images if args.images is not None else 2000
        return pdf_count, word_count, image_count

    # Method 2: Total + ratios
    if args.total is not None:
        total = args.total
        # Validate ratios sum to ~1.0
        ratio_sum = args.pdf_ratio + args.word_ratio + args.image_ratio
        if abs(ratio_sum - 1.0) > 0.01:
            print(f"⚠️  Warning: Ratios sum to {ratio_sum:.2f}, not 1.0. Normalizing...")
            pdf_ratio = args.pdf_ratio / ratio_sum
            word_ratio = args.word_ratio / ratio_sum
            image_ratio = args.image_ratio / ratio_sum
        else:
            pdf_ratio = args.pdf_ratio
            word_ratio = args.word_ratio
            image_ratio = args.image_ratio

        pdf_count = int(total * pdf_ratio)
        word_count = int(total * word_ratio)
        image_count = int(total * image_ratio)

        return pdf_count, word_count, image_count

    # Default: 10K dataset
    return 5000, 3000, 2000


def estimate_resources(pdf_count, word_count, image_count):
    """Estimate time and disk space needed."""
    total = pdf_count + word_count + image_count

    # Time estimates (based on benchmarks)
    pdf_time = pdf_count / 30  # ~30 PDFs/second
    word_time = word_count / 50  # ~50 Word docs/second
    image_time = image_count / 100  # ~100 images/second
    total_time_min = (pdf_time + word_time + image_time) / 60

    # Size estimates
    pdf_size_mb = (pdf_count * 10) / 1024  # ~10 KB per PDF
    word_size_mb = (word_count * 13) / 1024  # ~13 KB per Word
    image_size_mb = (image_count * 100) / 1024  # ~100 KB per image
    embedding_size_mb = total * 0.002  # ~2 KB per doc for embeddings
    total_size_mb = pdf_size_mb + word_size_mb + image_size_mb + embedding_size_mb

    return total_time_min, total_size_mb


def main():
    args = parse_args()

    pdf_count, word_count, image_count = calculate_counts(args)
    total_count = pdf_count + word_count + image_count

    print("="*70)
    print(f"Generating {total_count:,} Document Dataset")
    print("="*70)
    print()
    print("Distribution:")
    print(f"  • {pdf_count:,} PDFs ({pdf_count/total_count*100:.1f}%)")
    print(f"  • {word_count:,} Word documents ({word_count/total_count*100:.1f}%)")
    print(f"  • {image_count:,} Images ({image_count/total_count*100:.1f}%)")
    print()

    time_min, size_mb = estimate_resources(pdf_count, word_count, image_count)
    print(f"Estimated time: ~{time_min:.0f} minutes")
    print(f"Estimated size: ~{size_mb:.0f} MB (including embeddings)")
    print()

    if not args.skip_confirmation:
        response = input("Proceed with generation? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Aborted.")
            return

    print("Starting generation...")

    # Generate PDFs
    if pdf_count > 0:
        print("\n" + "="*70)
        print(f"STEP 1/3: Generating {pdf_count:,} PDF documents...")
        print("="*70)
        generate_all_pdfs(count=pdf_count)

    # Generate Word docs
    if word_count > 0:
        print("\n" + "="*70)
        print(f"STEP 2/3: Generating {word_count:,} Word documents...")
        print("="*70)
        generate_all_word_docs(count=word_count)

    # Generate Images
    if image_count > 0:
        print("\n" + "="*70)
        print(f"STEP 3/3: Generating {image_count:,} Images...")
        print("="*70)
        generate_all_images(count=image_count)

    print("\n" + "="*70)
    print(f"✓ {total_count:,} Documents Generated Successfully!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Run: python scripts/process_multimodal_data.py")
    print("  2. Load into databases and run benchmarks")
    print()


if __name__ == "__main__":
    main()
