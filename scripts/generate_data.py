"""
Generate synthetic reinsurance data for POC testing.
Creates policies, claims, and knowledge base articles.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# Reinsurance-specific data
POLICY_TYPES = [
    "Property Catastrophe", "Casualty Excess of Loss", "Marine & Aviation",
    "Professional Liability", "Workers Compensation", "Cyber Risk",
    "Life & Health", "Agriculture", "Political Risk", "Terrorism"
]

PERILS = [
    "Hurricane", "Earthquake", "Flood", "Wildfire", "Tornado",
    "Hail", "Wind", "Freeze", "Cyber Attack", "Professional Error"
]

TERRITORIES = [
    "United States", "European Union", "United Kingdom", "Japan",
    "Australia", "Canada", "Asia Pacific", "Latin America", "Worldwide"
]

CLAIM_CATEGORIES = [
    "Natural Catastrophe", "Liability", "Professional Indemnity",
    "Property Damage", "Business Interruption", "Cyber Incident",
    "Medical Malpractice", "Product Liability", "Environmental"
]

KNOWLEDGE_TOPICS = [
    "Underwriting Guidelines", "Regulatory Compliance", "Claims Handling",
    "Risk Assessment", "Premium Calculation", "Policy Wording",
    "Reinsurance Treaties", "Catastrophe Modeling", "Loss Reserves",
    "Actuarial Standards"
]


def generate_policies(count: int = 1000) -> List[Dict]:
    """Generate synthetic reinsurance policies."""
    policies = []

    for i in range(count):
        policy_type = random.choice(POLICY_TYPES)
        inception_date = fake.date_between(start_date='-5y', end_date='today')
        expiry_date = inception_date + timedelta(days=365)

        policy = {
            "id": f"POL-{i+1:06d}",
            "policy_type": policy_type,
            "cedent": fake.company(),
            "inception_date": inception_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "limit": random.randint(1, 100) * 1000000,
            "premium": random.randint(100, 10000) * 1000,
            "attachment_point": random.randint(1, 50) * 1000000,
            "territory": random.choice(TERRITORIES),
            "perils_covered": random.sample(PERILS, k=random.randint(1, 4)),
            "layers": random.randint(1, 5),
            "description": f"{policy_type} reinsurance policy providing coverage for "
                          f"{fake.company()} across {random.choice(TERRITORIES)}. "
                          f"The policy covers catastrophic losses exceeding the attachment point "
                          f"with a maximum limit defined. Risk premium calculated based on "
                          f"historical loss data and catastrophe modeling.",
            "metadata": {
                "broker": fake.company(),
                "rating": random.choice(["A++", "A+", "A", "A-", "BBB+"]),
                "renewable": random.choice([True, False])
            }
        }
        policies.append(policy)

    return policies


def generate_claims(count: int = 2000) -> List[Dict]:
    """Generate synthetic insurance claims."""
    claims = []

    for i in range(count):
        loss_date = fake.date_between(start_date='-3y', end_date='today')
        report_date = loss_date + timedelta(days=random.randint(1, 90))
        category = random.choice(CLAIM_CATEGORIES)

        claim = {
            "id": f"CLM-{i+1:06d}",
            "policy_id": f"POL-{random.randint(1, 1000):06d}",
            "category": category,
            "loss_date": loss_date.isoformat(),
            "report_date": report_date.isoformat(),
            "loss_amount": random.randint(100, 50000) * 1000,
            "paid_amount": random.randint(50, 45000) * 1000,
            "reserve_amount": random.randint(0, 10000) * 1000,
            "status": random.choice(["Open", "Closed", "Pending", "In Review"]),
            "location": fake.city() + ", " + fake.country(),
            "peril": random.choice(PERILS),
            "description": f"{category} claim arising from {random.choice(PERILS)} event "
                          f"occurring on {loss_date.strftime('%B %d, %Y')}. "
                          f"The insured reported significant damage to property and subsequent "
                          f"business interruption. Detailed investigation conducted by loss adjuster. "
                          f"Settlement negotiations ongoing with consideration of policy terms, "
                          f"exclusions, and applicable deductibles.",
            "metadata": {
                "adjuster": fake.name(),
                "complexity": random.choice(["Low", "Medium", "High", "Very High"]),
                "fraud_score": round(random.uniform(0, 1), 3),
                "num_claimants": random.randint(1, 50)
            }
        }
        claims.append(claim)

    return claims


def generate_knowledge_base(count: int = 500) -> List[Dict]:
    """Generate synthetic knowledge base articles."""
    articles = []

    for i in range(count):
        topic = random.choice(KNOWLEDGE_TOPICS)

        article = {
            "id": f"KB-{i+1:06d}",
            "title": f"{topic}: {fake.catch_phrase()}",
            "topic": topic,
            "content": generate_article_content(topic),
            "created_date": fake.date_between(start_date='-2y', end_date='today').isoformat(),
            "author": fake.name(),
            "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}",
            "tags": random.sample(KNOWLEDGE_TOPICS, k=random.randint(2, 4)),
            "metadata": {
                "department": random.choice(["Underwriting", "Claims", "Actuarial", "Legal", "Risk Management"]),
                "views": random.randint(10, 5000),
                "helpful_votes": random.randint(0, 500)
            }
        }
        articles.append(article)

    return articles


def generate_article_content(topic: str) -> str:
    """Generate realistic article content based on topic."""
    intros = {
        "Underwriting Guidelines": "Underwriting guidelines establish the framework for assessing and accepting reinsurance risks. "
                                   "These guidelines ensure consistent evaluation of cedent relationships, loss histories, and "
                                   "pricing adequacy across all territories and lines of business.",

        "Regulatory Compliance": "Regulatory compliance in reinsurance requires adherence to international standards including "
                                "Solvency II, IFRS 17, and local insurance regulations. Organizations must maintain proper "
                                "documentation, capital requirements, and reporting procedures.",

        "Claims Handling": "Effective claims handling processes are critical for maintaining cedent relationships and "
                          "accurate loss reserves. This includes prompt investigation, fair evaluation, and timely "
                          "settlement of valid claims while identifying potentially fraudulent submissions.",

        "Risk Assessment": "Risk assessment in reinsurance involves evaluating catastrophe exposure, accumulation risk, "
                          "and portfolio optimization. Actuarial models, historical loss data, and forward-looking "
                          "scenarios inform pricing and capacity decisions.",

        "Premium Calculation": "Premium calculation methodology considers expected losses, loss adjustment expenses, "
                              "operational costs, cost of capital, and profit margin. Technical pricing uses exposure "
                              "rating, experience rating, and catastrophe modeling approaches.",
    }

    intro = intros.get(topic, "This article provides guidance on reinsurance best practices and industry standards. ")

    body = (
        f"{intro} "
        f"Key considerations include maintaining accurate records, following established procedures, "
        f"and ensuring compliance with applicable regulations. Regular reviews and updates ensure "
        f"practices remain current with evolving market conditions and regulatory requirements. "
        f"Collaboration between underwriting, claims, actuarial, and legal departments is essential "
        f"for comprehensive risk management. Documentation should be thorough and readily accessible "
        f"for audit purposes and internal reference."
    )

    return body


def main():
    """Generate all synthetic data and save to files."""
    print("Generating synthetic reinsurance data...")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Generate data
    print("  - Generating policies...")
    policies = generate_policies(1000)

    print("  - Generating claims...")
    claims = generate_claims(2000)

    print("  - Generating knowledge base...")
    knowledge_base = generate_knowledge_base(500)

    # Save to JSON files
    print("\nSaving data to files...")

    with open(data_dir / "policies.json", "w") as f:
        json.dump(policies, f, indent=2)
    print(f"  ✓ Saved {len(policies)} policies")

    with open(data_dir / "claims.json", "w") as f:
        json.dump(claims, f, indent=2)
    print(f"  ✓ Saved {len(claims)} claims")

    with open(data_dir / "knowledge_base.json", "w") as f:
        json.dump(knowledge_base, f, indent=2)
    print(f"  ✓ Saved {len(knowledge_base)} knowledge base articles")

    # Print statistics
    print("\n" + "="*50)
    print("Data Generation Summary")
    print("="*50)
    print(f"Total policies: {len(policies)}")
    print(f"Total claims: {len(claims)}")
    print(f"Total knowledge articles: {len(knowledge_base)}")
    print(f"Total records: {len(policies) + len(claims) + len(knowledge_base)}")
    print("\nData saved to ./data/ directory")


if __name__ == "__main__":
    main()
