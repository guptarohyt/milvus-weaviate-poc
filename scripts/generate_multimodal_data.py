"""
Generate multi-modal test data for Phase 2 POC.
Creates PDFs, Word documents, images, and audio files for testing.
"""

import json
import os
import random
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Image as RLImage, Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# Set style for charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (8, 5)


def load_phase1_data():
    """Load existing Phase 1 data."""
    data_dir = Path("./data")

    try:
        with open(data_dir / "policies.json") as f:
            policies = json.load(f)
        with open(data_dir / "claims.json") as f:
            claims = json.load(f)
        with open(data_dir / "knowledge_base.json") as f:
            knowledge = json.load(f)

        return policies, claims, knowledge
    except FileNotFoundError:
        print("❌ Phase 1 data not found. Please run generate_data.py first.")
        return None, None, None


def generate_loss_curve_chart(policy_id, output_dir):
    """Generate realistic loss exceedance curve."""
    return_periods = [1, 2, 5, 10, 25, 50, 100, 250, 500]
    # Generate realistic loss curve with some randomness
    base_losses = [5, 12, 28, 45, 75, 105, 145, 210, 280]
    losses = [l * random.uniform(0.8, 1.2) for l in base_losses]

    plt.figure(figsize=(7, 4.5))
    plt.plot(return_periods, losses, marker='o', linewidth=2, markersize=8, color='#2E86AB')
    plt.xscale('log')
    plt.xlabel('Return Period (Years)', fontsize=11, fontweight='bold')
    plt.ylabel('Loss ($M)', fontsize=11, fontweight='bold')
    plt.title(f'Expected Loss Exceedance Curve - {policy_id}', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()

    filename = output_dir / f'loss_curve_{policy_id}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    return filename


def generate_premium_chart(policy, output_dir):
    """Generate premium breakdown bar chart."""
    categories = ['Base Premium', 'Cat Load', 'Expenses', 'Profit Margin']
    premium = policy['premium'] / 1000  # Convert to thousands
    values = [
        premium * 0.60,  # Base
        premium * 0.20,  # Cat load
        premium * 0.12,  # Expenses
        premium * 0.08   # Profit
    ]

    plt.figure(figsize=(7, 4))
    colors_list = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    plt.bar(categories, values, color=colors_list, edgecolor='black', linewidth=1.2)
    plt.ylabel('Amount ($K)', fontsize=11, fontweight='bold')
    plt.title(f'Premium Breakdown - {policy["id"]}', fontsize=12, fontweight='bold')
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()

    filename = output_dir / f'premium_{policy["id"]}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    return filename


def create_coverage_table(policy):
    """Create formatted coverage table."""
    limit_m = policy['limit'] // 1000000
    premium_k = policy['premium'] // 1000

    data = [
        ['Coverage Layer', 'Limit ($M)', 'Attachment ($M)', 'Rate on Line (%)', 'Premium ($K)'],
        ['Primary Layer', f'{limit_m}', '0', '4.5%', f'{int(premium_k * 0.45)}'],
        ['First Excess', f'{limit_m // 2}', f'{limit_m}', '3.2%', f'{int(premium_k * 0.32)}'],
        ['Second Excess', f'{limit_m // 4}', f'{limit_m + limit_m // 2}', '2.3%', f'{int(premium_k * 0.23)}'],
    ]

    table = Table(data, colWidths=[140, 80, 100, 90, 85])
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightgrey]),
    ]))

    return table


def generate_policy_terms(policy):
    """Generate realistic policy terms and conditions."""
    terms = [
        f"<b>1. Coverage Scope:</b> This treaty provides {policy['policy_type']} coverage "
        f"for the territory of {policy['territory']}. The coverage limit is "
        f"${policy['limit']:,} excess of the applicable retention.",

        "<b>2. Covered Perils:</b> This treaty covers losses arising from:",
        "• Hurricane and Named Storm events",
        "• Severe Convective Storms (tornado, hail, straight-line winds)",
        "• Winter Storms and Freeze",
        "• Earthquake and Volcanic Eruption (if specifically included)",

        "<b>3. Exclusions:</b> The following perils and circumstances are excluded:",
        "• Nuclear events and radioactive contamination",
        "• War, terrorism, and civil commotion",
        "• Pollution and environmental damage (unless specifically covered)",
        "• Cyber attacks and electronic data compromise",
        "• Intentional acts and fraud",

        "<b>4. Claims Notification:</b> The Cedent must notify the Reinsurer of:",
        "• Any loss expected to exceed 50% of the attachment point within 72 hours",
        "• Full loss details including estimates within 30 days of the event",
        "• Updated loss estimates every 90 days until final settlement",

        "<b>5. Premium Payment:</b> Premium is payable as follows:",
        f"• Deposit premium: ${policy['premium']:,} payable at inception",
        "• Adjustment premium based on actual exposure, calculated quarterly",
        "• Final adjustment within 90 days of policy expiration",
        "• Payment terms: Net 30 days from invoice date",

        "<b>6. Reinstatement Provisions:</b>",
        "• Automatic reinstatement for the first event at 100% of additional premium",
        "• Second and subsequent reinstatements subject to mutual agreement",
        "• Pro-rata reinstatement premium calculation based on remaining term",

        "<b>7. Territory Definition:</b>",
        f"Coverage applies to risks located within {policy['territory']} as defined by:",
        "• Property location for direct physical damage",
        "• Insured's principal place of business for liability coverages",
        "• Place of loss occurrence for casualty coverages",

        "<b>8. Loss Settlement:</b>",
        "• Reinsurer follows the fortunes of the Cedent",
        "• Losses settled on occurrence basis",
        "• Payment within 30 days of receipt of complete documentation",
        "• Interest accrues on overdue payments at LIBOR + 2%",

        "<b>9. Commutation Clause:</b>",
        "Either party may request commutation after policy expiration, subject to:",
        "• All known losses fully reserved and documented",
        "• IBNR provision calculated by independent actuary",
        "• Mutual agreement on commutation amount and terms",

        "<b>10. Dispute Resolution:</b>",
        "• Good faith negotiations for 60 days",
        "• Mediation if negotiations fail",
        "• Binding arbitration in New York under AAA rules",
        "• Governing law: New York State",
    ]

    return terms


def generate_policy_pdf(policy, policies_dir, charts_dir):
    """Generate complete policy PDF with charts, tables, and multi-page content."""
    output_path = policies_dir / f"policy_{policy['id']}.pdf"

    # Create document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2E86AB'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2E86AB'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    )

    # Build document content
    story = []

    # Title Page
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"REINSURANCE TREATY", title_style))
    story.append(Paragraph(f"{policy['policy_type']}", title_style))
    story.append(Spacer(1, 0.3*inch))

    # Policy details box
    details_data = [
        ['Policy Number:', policy['id']],
        ['Cedent:', policy['cedent']],
        ['Territory:', policy['territory']],
        ['Inception Date:', policy.get('inception_date', '2024-01-01')],
        ['Expiry Date:', policy.get('expiry_date', '2024-12-31')],
    ]
    details_table = Table(details_data, colWidths=[150, 300])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.5*inch))

    # Executive Summary
    story.append(PageBreak())
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(policy['description'], body_style))
    story.append(Spacer(1, 0.2*inch))

    summary_points = [
        f"Limit of Coverage: ${policy['limit']:,}",
        f"Annual Premium: ${policy['premium']:,}",
        f"Rate on Line: {(policy['premium'] / policy['limit'] * 100):.2f}%",
        "Coverage Basis: Occurrence",
        "Loss Settlement: Claims-Made or Losses Occurring",
    ]
    for point in summary_points:
        story.append(Paragraph(f"• {point}", body_style))
    story.append(Spacer(1, 0.3*inch))

    # Coverage Details Table
    story.append(Paragraph("Coverage Structure", heading_style))
    story.append(create_coverage_table(policy))
    story.append(Spacer(1, 0.3*inch))

    # Premium Analysis Chart
    story.append(PageBreak())
    story.append(Paragraph("Premium Analysis", heading_style))
    premium_chart = generate_premium_chart(policy, charts_dir)
    story.append(RLImage(str(premium_chart), width=5*inch, height=3*inch))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("<i>Figure 1: Premium component breakdown showing allocation across "
                          "base premium, catastrophe load, expenses, and profit margin.</i>", body_style))
    story.append(Spacer(1, 0.3*inch))

    # Loss Analysis
    story.append(PageBreak())
    story.append(Paragraph("Loss Analysis", heading_style))
    loss_chart = generate_loss_curve_chart(policy['id'], charts_dir)
    story.append(RLImage(str(loss_chart), width=5.5*inch, height=3.5*inch))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("<i>Figure 2: Expected loss exceedance probability curve based on "
                          "catastrophe modeling and historical loss experience.</i>", body_style))
    story.append(Spacer(1, 0.3*inch))

    # Terms and Conditions
    story.append(PageBreak())
    story.append(Paragraph("Terms and Conditions", heading_style))
    story.append(Spacer(1, 0.1*inch))

    terms = generate_policy_terms(policy)
    for term in terms:
        story.append(Paragraph(term, body_style))
        story.append(Spacer(1, 0.05*inch))

    # Build PDF
    doc.build(story)

    return output_path


def generate_all_pdfs(count=100):
    """Generate PDF documents."""
    print(f"\n{'='*60}")
    print("GENERATING PDF DOCUMENTS")
    print(f"{'='*60}\n")

    # Load Phase 1 data
    policies, _, _ = load_phase1_data()
    if policies is None:
        return

    # Setup directories
    data_dir = Path("./data/multimodal")
    pdfs_dir = data_dir / "pdfs"
    charts_dir = data_dir / "pdfs" / "charts"
    charts_dir.mkdir(exist_ok=True)

    # Generate PDFs
    generated = 0
    for i, policy in enumerate(policies[:count]):
        try:
            pdf_path = generate_policy_pdf(policy, pdfs_dir, charts_dir)
            generated += 1
            if (i + 1) % 10 == 0:
                print(f"✓ Generated {i + 1}/{count} PDFs")
        except Exception as e:
            print(f"✗ Error generating PDF for {policy['id']}: {str(e)}")

    print(f"\n✓ Successfully generated {generated} PDF documents")
    print(f"  Location: {pdfs_dir}")
    print(f"  Charts: {charts_dir}")


def generate_damage_image(damage_type, severity, image_id, output_dir):
    """Generate synthetic damage assessment image."""
    # Image size
    width, height = 1200, 800

    # Color schemes for different damage types
    color_schemes = {
        'hurricane': {'base': (100, 120, 140), 'damage': (80, 90, 100), 'highlight': (200, 210, 220)},
        'flood': {'base': (90, 110, 140), 'damage': (70, 90, 120), 'highlight': (180, 200, 230)},
        'fire': {'base': (140, 100, 80), 'damage': (100, 60, 40), 'highlight': (220, 180, 140)},
        'structural': {'base': (120, 120, 120), 'damage': (90, 90, 90), 'highlight': (200, 200, 200)},
    }

    colors = color_schemes.get(damage_type, color_schemes['structural'])

    # Create base image with gradient
    img = Image.new('RGB', (width, height), colors['base'])
    draw = ImageDraw.Draw(img)

    # Add gradient effect
    for y in range(height):
        factor = y / height
        r = int(colors['base'][0] + (colors['damage'][0] - colors['base'][0]) * factor)
        g = int(colors['base'][1] + (colors['damage'][1] - colors['base'][1]) * factor)
        b = int(colors['base'][2] + (colors['damage'][2] - colors['base'][2]) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add damage patterns based on type and severity
    np.random.seed(int(image_id.split('-')[1]))

    if damage_type == 'hurricane':
        # Debris patterns
        for _ in range(int(20 * severity)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(20, 80)
            draw.ellipse([x, y, x + size, y + size//2], fill=colors['damage'])

    elif damage_type == 'flood':
        # Water line and staining
        water_line = int(height * (0.3 + 0.4 * severity))
        draw.rectangle([0, water_line, width, height], fill=(70, 90, 120, 180))
        # Watermarks
        for _ in range(10):
            y = random.randint(water_line - 100, height)
            draw.line([(0, y), (width, y)], fill=colors['highlight'], width=2)

    elif damage_type == 'fire':
        # Char marks and smoke damage
        for _ in range(int(15 * severity)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(40, 120)
            draw.ellipse([x, y, x + size, y + size], fill=(40, 30, 20), outline=(80, 60, 40))

    elif damage_type == 'structural':
        # Cracks and damage lines
        for _ in range(int(10 * severity)):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = x1 + random.randint(-200, 200)
            y2 = y1 + random.randint(50, 300)
            draw.line([(x1, y1), (x2, y2)], fill=(60, 60, 60), width=random.randint(2, 5))

    # Add severity indicator boxes
    severity_text = f"Severity: {int(severity * 100)}%"
    type_text = f"Type: {damage_type.upper()}"
    id_text = f"ID: {image_id}"

    # Draw info boxes
    box_height = 40
    draw.rectangle([0, 0, width, box_height], fill=(0, 0, 0, 180))
    draw.rectangle([0, height - box_height, width, height], fill=(0, 0, 0, 180))

    # Try to use a better font, fallback to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font = ImageFont.load_default()
        small_font = font

    # Add text
    draw.text((20, 10), type_text, fill=(255, 255, 255), font=font)
    draw.text((width - 300, 10), severity_text, fill=(255, 200, 100), font=font)
    draw.text((20, height - 30), id_text, fill=(200, 200, 200), font=small_font)

    # Add some noise for realism
    noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
    noise_img = Image.fromarray(noise)
    img = Image.blend(img, noise_img, 0.1)

    # Apply slight blur for realism
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # Save
    filename = output_dir / f"{damage_type}_{image_id}.jpg"
    img.save(filename, 'JPEG', quality=85)

    return filename


def generate_all_images(count=200):
    """Generate synthetic damage assessment images."""
    print(f"\n{'='*60}")
    print("GENERATING DAMAGE ASSESSMENT IMAGES")
    print(f"{'='*60}\n")

    # Load Phase 1 data to link images to claims
    _, claims, _ = load_phase1_data()
    if claims is None:
        return

    # Setup directories
    data_dir = Path("./data/multimodal")
    images_dir = data_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # Damage type distribution
    damage_types = {
        'hurricane': 80,   # 40%
        'flood': 60,       # 30%
        'fire': 40,        # 20%
        'structural': 20,  # 10%
    }

    # Generate images
    generated = 0
    image_metadata = []

    for damage_type, type_count in damage_types.items():
        type_dir = images_dir / damage_type
        type_dir.mkdir(exist_ok=True)

        for i in range(type_count):
            try:
                # Create image ID
                image_id = f"IMG-{generated + 1:06d}"

                # Random severity (0.3 to 1.0)
                severity = random.uniform(0.3, 1.0)

                # Generate image
                image_path = generate_damage_image(damage_type, severity, image_id, type_dir)

                # Link to a random claim
                linked_claim = random.choice(claims[:min(len(claims), 500)])

                # Create metadata
                metadata = {
                    'image_id': image_id,
                    'filename': str(image_path.name),
                    'path': str(image_path.relative_to(Path("./data"))),
                    'damage_type': damage_type,
                    'severity': round(severity, 2),
                    'claim_id': linked_claim['id'],
                    'policy_id': linked_claim['policy_id'],
                    'location': linked_claim['location'],
                    'timestamp': linked_claim['loss_date'],
                    'peril': linked_claim.get('peril', damage_type),
                    'loss_amount': linked_claim.get('loss_amount', 0),
                    'description': f"{damage_type.title()} damage assessment photo. "
                                 f"Severity: {int(severity * 100)}%. "
                                 f"Associated with claim {linked_claim['id']}. "
                                 f"Location: {linked_claim['location']}.",
                }
                image_metadata.append(metadata)

                generated += 1

                if generated % 50 == 0:
                    print(f"✓ Generated {generated}/{count} images")

            except Exception as e:
                print(f"✗ Error generating image {image_id}: {str(e)}")

    # Save metadata
    metadata_file = images_dir / "image_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(image_metadata, f, indent=2)

    print(f"\n✓ Successfully generated {generated} damage assessment images")
    print(f"  Location: {images_dir}")
    print(f"  Hurricane: {damage_types['hurricane']} images")
    print(f"  Flood: {damage_types['flood']} images")
    print(f"  Fire: {damage_types['fire']} images")
    print(f"  Structural: {damage_types['structural']} images")
    print(f"  Metadata: {metadata_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate multi-modal test data')
    parser.add_argument('--type', choices=['pdf', 'word', 'images', 'audio', 'all'],
                       default='all', help='Type of data to generate')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of files to generate (for PDFs/Word)')

    args = parser.parse_args()

    if args.type in ['pdf', 'all']:
        generate_all_pdfs(args.count)

    if args.type in ['images', 'all']:
        generate_all_images(args.count if args.type == 'images' else 200)

    if args.type in ['word', 'all']:
        print("\n⚠️  Word document generation not yet implemented")

    if args.type in ['audio', 'all']:
        print("\n⚠️  Audio generation not yet implemented")


if __name__ == "__main__":
    main()
