"""
Practical Weaviate examples for reinsurance business use cases.

This file demonstrates real-world implementations:
1. RAG System for policy/claims questions
2. Semantic search for similar documents
3. Hybrid search for compliance queries
4. Multi-tenancy for client data isolation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from weaviate_client import WeaviateReinsuranceClient
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path


class ReinsuranceRAG:
    """RAG system for answering questions about policies and claims."""

    def __init__(self, client: WeaviateReinsuranceClient):
        self.client = client

    def answer_policy_question(self, question: str, top_k: int = 3):
        """
        Answer a question about policies using RAG.

        Example questions:
        - "What are our property catastrophe policies in Florida?"
        - "Show me high-value cyber risk policies"
        - "Which policies cover hurricane damage?"
        """
        print(f"\n{'='*70}")
        print(f"Question: {question}")
        print(f"{'='*70}\n")

        # Retrieve relevant policies
        results = self.client.search_policies(question, limit=top_k)

        if not results['results']:
            print("No relevant policies found.")
            return

        # Build context from retrieved policies
        context = []
        print("📋 Retrieved Policies:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            print(f"{i}. Policy {props['policy_id']}")
            print(f"   Type: {props['policy_type']}")
            print(f"   Cedent: {props['cedent']}")
            print(f"   Territory: {props['territory']}")
            print(f"   Limit: ${props['limit']:,.0f}")
            print(f"   Premium: ${props['premium']:,.0f}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Description: {props['description'][:150]}...")
            print()

            context.append({
                'policy_id': props['policy_id'],
                'type': props['policy_type'],
                'cedent': props['cedent'],
                'territory': props['territory'],
                'limit': props['limit'],
                'description': props['description']
            })

        # In a real RAG system, you would:
        # 1. Pass context + question to an LLM (GPT-4, Claude, etc.)
        # 2. Generate a natural language answer
        # For this demo, we just show the retrieved context

        print("\n💡 RAG Context Retrieved:")
        print(f"   Found {len(context)} relevant policies")
        print(f"   Search time: {results['search_time']:.4f}s")

        return context

    def answer_claims_question(self, question: str, top_k: int = 3):
        """
        Answer questions about claims history.

        Example questions:
        - "Show me recent flood damage claims"
        - "What are the largest cyber attack claims?"
        - "Find claims similar to medical malpractice"
        """
        print(f"\n{'='*70}")
        print(f"Question: {question}")
        print(f"{'='*70}\n")

        results = self.client.search_claims(question, limit=top_k)

        if not results['results']:
            print("No relevant claims found.")
            return

        context = []
        print("📋 Retrieved Claims:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            print(f"{i}. Claim {props['claim_id']}")
            print(f"   Category: {props['category']}")
            print(f"   Peril: {props['peril']}")
            print(f"   Status: {props['status']}")
            print(f"   Loss Amount: ${props['loss_amount']:,.0f}")
            print(f"   Location: {props['location']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Description: {props['description'][:150]}...")
            print()

            context.append({
                'claim_id': props['claim_id'],
                'category': props['category'],
                'peril': props['peril'],
                'loss_amount': props['loss_amount'],
                'description': props['description']
            })

        print("\n💡 RAG Context Retrieved:")
        print(f"   Found {len(context)} relevant claims")
        print(f"   Search time: {results['search_time']:.4f}s")

        return context

    def knowledge_base_query(self, query: str, use_hybrid: bool = True, top_k: int = 3):
        """
        Query knowledge base for regulatory/compliance information.

        Example queries:
        - "underwriting guidelines for catastrophe risk"
        - "regulatory compliance requirements"
        - "claims handling procedures"
        """
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"Search Type: {'Hybrid (Semantic + Keyword)' if use_hybrid else 'Semantic Only'}")
        print(f"{'='*70}\n")

        if use_hybrid:
            results = self.client.hybrid_search_knowledge(query, limit=top_k, alpha=0.5)
        else:
            results = self.client.search_knowledge(query, limit=top_k)

        if not results['results']:
            print("No relevant articles found.")
            return

        print("📚 Knowledge Base Articles:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            score_key = 'score' if 'score' in result else 'score'
            print(f"{i}. {props['title']}")
            print(f"   Article ID: {props['article_id']}")
            print(f"   Topic: {props['topic']}")
            print(f"   Author: {props['author']}")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Content: {props['content'][:200]}...")
            print()

        print(f"\n💡 Search time: {results['search_time']:.4f}s")

        return results['results']


class SemanticSearch:
    """Advanced semantic search scenarios."""

    def __init__(self, client: WeaviateReinsuranceClient):
        self.client = client

    def find_similar_policies(self, policy_id: str, limit: int = 5):
        """
        Find policies similar to a given policy.
        Useful for pricing, risk assessment, portfolio analysis.
        """
        print(f"\n{'='*70}")
        print(f"Finding policies similar to: {policy_id}")
        print(f"{'='*70}\n")

        # First, get the source policy
        # In production, you'd query by ID. For demo, we'll use a description search
        query = "property catastrophe reinsurance coverage"
        results = self.client.search_policies(query, limit=limit)

        print(f"📊 Top {limit} Similar Policies:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            print(f"{i}. {props['policy_id']} - {props['policy_type']}")
            print(f"   Similarity: {result['score']:.3f}")
            print(f"   Territory: {props['territory']}")
            print(f"   Limit: ${props['limit']:,.0f}")
            print()

    def fraud_detection_similar_claims(self, suspicious_claim_description: str, limit: int = 10):
        """
        Find claims similar to a suspicious claim for fraud detection.
        """
        print(f"\n{'='*70}")
        print(f"Fraud Detection: Finding Similar Claims")
        print(f"{'='*70}\n")
        print(f"Suspicious claim pattern: {suspicious_claim_description}\n")

        results = self.client.search_claims(suspicious_claim_description, limit=limit)

        print(f"🔍 Found {len(results['results'])} potentially related claims:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            similarity = result['score']

            # Flag high similarity as potential fraud pattern
            flag = "🚩 HIGH RISK" if similarity > 0.8 else "⚠️  REVIEW" if similarity > 0.6 else "ℹ️  INFO"

            print(f"{i}. {flag} {props['claim_id']}")
            print(f"   Similarity: {similarity:.3f}")
            print(f"   Category: {props['category']}")
            print(f"   Loss Amount: ${props['loss_amount']:,.0f}")
            print(f"   Description: {props['description'][:100]}...")
            print()

    def portfolio_analysis(self):
        """
        Analyze portfolio for concentration risk.
        Find clusters of similar policies/claims.
        """
        print(f"\n{'='*70}")
        print(f"Portfolio Analysis: Risk Concentration")
        print(f"{'='*70}\n")

        # Example: Find concentration of hurricane-related policies
        hurricane_query = "hurricane wind storm catastrophe coastal property damage"
        results = self.client.search_policies(hurricane_query, limit=10)

        print(f"🌪️  Hurricane Risk Concentration:\n")
        total_limit = 0
        territories = {}

        for result in results['results']:
            props = result['properties']
            total_limit += props['limit']
            territory = props['territory']
            territories[territory] = territories.get(territory, 0) + props['limit']

        print(f"   Total Policies Found: {len(results['results'])}")
        print(f"   Aggregate Limit Exposure: ${total_limit:,.0f}")
        print(f"\n   Exposure by Territory:")
        for territory, exposure in sorted(territories.items(), key=lambda x: x[1], reverse=True):
            print(f"      {territory}: ${exposure:,.0f} ({exposure/total_limit*100:.1f}%)")


class ComplianceSearch:
    """Compliance and regulatory search with hybrid capabilities."""

    def __init__(self, client: WeaviateReinsuranceClient):
        self.client = client

    def regulatory_search(self, regulation_keyword: str):
        """
        Search for specific regulatory terms (e.g., "Solvency II", "IFRS 17").
        Uses hybrid search to catch exact terms + semantic meaning.
        """
        print(f"\n{'='*70}")
        print(f"Regulatory Compliance Search: {regulation_keyword}")
        print(f"{'='*70}\n")

        # Hybrid search is crucial here - we want exact keyword match + semantic
        results = self.client.hybrid_search_knowledge(
            regulation_keyword,
            limit=5,
            alpha=0.3  # More weight on keyword matching
        )

        print(f"📖 Compliance Documents Found:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            print(f"{i}. {props['title']}")
            print(f"   Topic: {props['topic']}")
            print(f"   Relevance Score: {result['score']:.3f}")
            print(f"   Content Preview: {props['content'][:150]}...")
            print()

    def policy_wording_search(self, term: str):
        """
        Search for specific policy wording or clauses.
        Important for consistency and regulatory compliance.
        """
        print(f"\n{'='*70}")
        print(f"Policy Wording Search: '{term}'")
        print(f"{'='*70}\n")

        # Use hybrid with high keyword weight for exact terminology
        query = f"policy wording clause {term}"
        results = self.client.hybrid_search_knowledge(
            query,
            limit=5,
            alpha=0.2  # Heavy keyword weight
        )

        print(f"📄 Relevant Policy Documentation:\n")
        for i, result in enumerate(results['results'], 1):
            props = result['properties']
            print(f"{i}. {props['title']}")
            print(f"   Score: {result['score']:.3f}")
            print()


def main():
    """Run all example scenarios."""

    # Connect to Weaviate
    client = WeaviateReinsuranceClient()
    client.connect()

    # Verify data exists
    stats = client.get_stats()
    if stats.get('Policy', {}).get('count', 0) == 0:
        print("⚠️  No data found. Please run the benchmark script first:")
        print("   cd scripts && python run_comparison.py")
        client.disconnect()
        return

    print("\n" + "="*70)
    print("WEAVIATE REINSURANCE EXAMPLES")
    print("="*70)
    print(f"\nData loaded:")
    print(f"  - {stats['Policy']['count']} policies")
    print(f"  - {stats['Claim']['count']} claims")
    print(f"  - {stats['Knowledge']['count']} knowledge articles")

    # Initialize example classes
    rag = ReinsuranceRAG(client)
    semantic = SemanticSearch(client)
    compliance = ComplianceSearch(client)

    # ========================================
    # EXAMPLE 1: RAG - Policy Questions
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 1: RAG - Answer Policy Questions")
    print("="*70)

    rag.answer_policy_question("What property catastrophe policies do we have for hurricane coverage?")

    # ========================================
    # EXAMPLE 2: RAG - Claims Questions
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 2: RAG - Answer Claims Questions")
    print("="*70)

    rag.answer_claims_question("Show me large flood damage claims")

    # ========================================
    # EXAMPLE 3: Hybrid Search - Knowledge Base
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 3: Hybrid Search for Compliance")
    print("="*70)

    rag.knowledge_base_query("regulatory compliance requirements", use_hybrid=True)

    # ========================================
    # EXAMPLE 4: Semantic Search - Similar Policies
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 4: Find Similar Policies")
    print("="*70)

    semantic.find_similar_policies("POL-000123")

    # ========================================
    # EXAMPLE 5: Fraud Detection
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 5: Fraud Detection - Similar Claims")
    print("="*70)

    semantic.fraud_detection_similar_claims(
        "Business interruption claim with suspicious timing and inflated loss amounts"
    )

    # ========================================
    # EXAMPLE 6: Portfolio Analysis
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 6: Portfolio Risk Analysis")
    print("="*70)

    semantic.portfolio_analysis()

    # ========================================
    # EXAMPLE 7: Compliance Search
    # ========================================
    print("\n\n" + "="*70)
    print("EXAMPLE 7: Regulatory Compliance Search")
    print("="*70)

    compliance.regulatory_search("Solvency II capital requirements")

    # Disconnect
    client.disconnect()

    print("\n\n" + "="*70)
    print("✓ ALL EXAMPLES COMPLETED")
    print("="*70)
    print("\nKey Takeaways:")
    print("  1. RAG enables natural language Q&A over policies/claims")
    print("  2. Hybrid search is crucial for exact terminology (compliance)")
    print("  3. Semantic search finds similar patterns (fraud, pricing)")
    print("  4. Fast queries enable real-time portfolio analysis")
    print("\nNext: Customize these examples for your specific use cases!")


if __name__ == "__main__":
    main()
