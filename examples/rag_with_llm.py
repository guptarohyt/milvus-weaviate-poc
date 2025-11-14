"""
Complete RAG System with LLM Integration for Reinsurance.

This example shows how to build a production-ready RAG system that:
1. Retrieves relevant context from Weaviate
2. Passes context + question to an LLM (OpenAI/Claude/local)
3. Generates natural language answers

NOTE: This uses a mock LLM response. In production, uncomment the
OpenAI/Anthropic integration code.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from weaviate_client import WeaviateReinsuranceClient
from typing import List, Dict
import json

# Uncomment for real LLM integration:
# import openai
# from anthropic import Anthropic


class ReinsuranceRAGSystem:
    """Production RAG system for reinsurance questions."""

    def __init__(self, weaviate_client: WeaviateReinsuranceClient, llm_provider: str = "mock"):
        """
        Initialize RAG system.

        Args:
            weaviate_client: Connected Weaviate client
            llm_provider: "openai", "anthropic", or "mock" (for demo)
        """
        self.client = weaviate_client
        self.llm_provider = llm_provider

        # Uncomment for real LLM:
        # if llm_provider == "openai":
        #     self.llm_client = openai.OpenAI(api_key="your-api-key")
        # elif llm_provider == "anthropic":
        #     self.llm_client = Anthropic(api_key="your-api-key")

    def answer_question(self, question: str, context_type: str = "policy", top_k: int = 5) -> Dict:
        """
        Answer a question using RAG.

        Args:
            question: User's question
            context_type: "policy", "claim", or "knowledge"
            top_k: Number of documents to retrieve

        Returns:
            Dict with answer, sources, and metadata
        """
        # Step 1: Retrieve relevant context
        print(f"\n🔍 Retrieving context for: '{question}'")

        if context_type == "policy":
            results = self.client.search_policies(question, limit=top_k)
        elif context_type == "claim":
            results = self.client.search_claims(question, limit=top_k)
        elif context_type == "knowledge":
            results = self.client.search_knowledge(question, limit=top_k)
        else:
            raise ValueError(f"Unknown context type: {context_type}")

        if not results['results']:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "confidence": 0.0
            }

        # Step 2: Format context for LLM
        context_text = self._format_context(results['results'], context_type)

        print(f"✓ Retrieved {len(results['results'])} relevant documents ({results['search_time']:.4f}s)")

        # Step 3: Generate answer with LLM
        print(f"🤖 Generating answer with {self.llm_provider}...")

        answer = self._generate_answer(question, context_text)

        # Step 4: Return structured response
        return {
            "answer": answer,
            "sources": self._extract_sources(results['results'], context_type),
            "confidence": self._calculate_confidence(results['results']),
            "retrieval_time": results['search_time']
        }

    def _format_context(self, results: List[Dict], context_type: str) -> str:
        """Format retrieved documents into context for LLM."""
        context_parts = []

        for i, result in enumerate(results, 1):
            props = result['properties']

            if context_type == "policy":
                context_parts.append(
                    f"[Policy {i}]\n"
                    f"ID: {props['policy_id']}\n"
                    f"Type: {props['policy_type']}\n"
                    f"Cedent: {props['cedent']}\n"
                    f"Territory: {props['territory']}\n"
                    f"Limit: ${props['limit']:,.0f}\n"
                    f"Premium: ${props['premium']:,.0f}\n"
                    f"Description: {props['description']}\n"
                )
            elif context_type == "claim":
                context_parts.append(
                    f"[Claim {i}]\n"
                    f"ID: {props['claim_id']}\n"
                    f"Category: {props['category']}\n"
                    f"Peril: {props['peril']}\n"
                    f"Status: {props['status']}\n"
                    f"Loss Amount: ${props['loss_amount']:,.0f}\n"
                    f"Location: {props['location']}\n"
                    f"Description: {props['description']}\n"
                )
            elif context_type == "knowledge":
                context_parts.append(
                    f"[Document {i}]\n"
                    f"Title: {props['title']}\n"
                    f"Topic: {props['topic']}\n"
                    f"Content: {props['content']}\n"
                )

        return "\n\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM."""

        # Build prompt
        prompt = self._build_prompt(question, context)

        if self.llm_provider == "mock":
            # Mock response for demo
            return self._mock_llm_response(question, context)

        # Uncomment for OpenAI:
        # elif self.llm_provider == "openai":
        #     response = self.llm_client.chat.completions.create(
        #         model="gpt-4",
        #         messages=[
        #             {"role": "system", "content": "You are a reinsurance expert assistant."},
        #             {"role": "user", "content": prompt}
        #         ],
        #         temperature=0.3
        #     )
        #     return response.choices[0].message.content

        # Uncomment for Anthropic:
        # elif self.llm_provider == "anthropic":
        #     response = self.llm_client.messages.create(
        #         model="claude-3-sonnet-20240229",
        #         max_tokens=1024,
        #         messages=[
        #             {"role": "user", "content": prompt}
        #         ]
        #     )
        #     return response.content[0].text

    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt for LLM."""
        return f"""You are a reinsurance expert assistant. Answer the question based ONLY on the provided context.

Context:
{context}

Question: {question}

Instructions:
- Provide a clear, concise answer based on the context
- Cite specific policy/claim IDs when relevant
- If the context doesn't contain enough information, say so
- Use professional reinsurance terminology

Answer:"""

    def _mock_llm_response(self, question: str, context: str) -> str:
        """Generate a mock response for demonstration."""
        # Simple keyword-based mock response
        context_lower = context.lower()

        if "flood" in question.lower():
            return ("Based on the retrieved claims, we have multiple significant flood damage claims "
                    "ranging from $17M to $37M in loss amounts. These claims show property damage "
                    "across various locations with some still pending resolution. This indicates "
                    "substantial flood risk exposure in our portfolio that may warrant review of "
                    "underwriting guidelines and pricing strategies.")

        elif "hurricane" in question.lower() or "catastrophe" in question.lower():
            return ("Our Property Catastrophe policies show significant exposure to hurricane risk, "
                    "with policies covering territories including the United States, European Union, "
                    "and Asia Pacific. Total aggregate limits exceed $400M across these regions. "
                    "The US represents the largest concentration at approximately 22% of total exposure.")

        elif "compliance" in question.lower() or "regulatory" in question.lower():
            return ("The knowledge base articles indicate that regulatory compliance in reinsurance "
                    "requires adherence to international standards including Solvency II and IFRS 17. "
                    "Organizations must maintain proper documentation, capital requirements, and "
                    "reporting procedures to ensure compliance with these regulations.")

        else:
            return ("Based on the retrieved documents, I found relevant information matching your query. "
                    "The context shows multiple related entries in our system. For detailed specifics, "
                    "please refer to the source documents listed below.")

    def _extract_sources(self, results: List[Dict], context_type: str) -> List[Dict]:
        """Extract source citations."""
        sources = []

        for result in results:
            props = result['properties']

            if context_type == "policy":
                sources.append({
                    "id": props['policy_id'],
                    "type": "Policy",
                    "title": f"{props['policy_type']} - {props['cedent']}",
                    "relevance": result['score']
                })
            elif context_type == "claim":
                sources.append({
                    "id": props['claim_id'],
                    "type": "Claim",
                    "title": f"{props['category']} - {props['peril']}",
                    "relevance": result['score']
                })
            elif context_type == "knowledge":
                sources.append({
                    "id": props['article_id'],
                    "type": "Knowledge",
                    "title": props['title'],
                    "relevance": result['score']
                })

        return sources

    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calculate confidence score based on retrieval results."""
        if not results:
            return 0.0

        # Average of top 3 scores
        scores = [r['score'] for r in results[:3]]
        return sum(scores) / len(scores)


def main():
    """Demo the RAG system."""

    # Connect to Weaviate
    client = WeaviateReinsuranceClient()
    client.connect()

    # Initialize RAG system
    rag = ReinsuranceRAGSystem(client, llm_provider="mock")

    print("="*70)
    print("REINSURANCE RAG SYSTEM - DEMO")
    print("="*70)

    # Example 1: Policy question
    print("\n" + "="*70)
    print("EXAMPLE 1: Policy Question")
    print("="*70)

    result = rag.answer_question(
        "What hurricane catastrophe policies do we have?",
        context_type="policy",
        top_k=5
    )

    print(f"\n📝 Answer:\n{result['answer']}\n")
    print(f"📚 Sources ({len(result['sources'])}):")
    for source in result['sources'][:3]:
        print(f"  - {source['type']} {source['id']}: {source['title']} (relevance: {source['relevance']:.3f})")
    print(f"\n🎯 Confidence: {result['confidence']:.3f}")
    print(f"⚡ Retrieval time: {result['retrieval_time']:.4f}s")

    # Example 2: Claims question
    print("\n" + "="*70)
    print("EXAMPLE 2: Claims Question")
    print("="*70)

    result = rag.answer_question(
        "Show me information about flood damage claims",
        context_type="claim",
        top_k=5
    )

    print(f"\n📝 Answer:\n{result['answer']}\n")
    print(f"📚 Sources ({len(result['sources'])}):")
    for source in result['sources'][:3]:
        print(f"  - {source['type']} {source['id']}: {source['title']} (relevance: {source['relevance']:.3f})")
    print(f"\n🎯 Confidence: {result['confidence']:.3f}")
    print(f"⚡ Retrieval time: {result['retrieval_time']:.4f}s")

    # Example 3: Compliance question
    print("\n" + "="*70)
    print("EXAMPLE 3: Compliance Question")
    print("="*70)

    result = rag.answer_question(
        "What are the regulatory compliance requirements?",
        context_type="knowledge",
        top_k=3
    )

    print(f"\n📝 Answer:\n{result['answer']}\n")
    print(f"📚 Sources ({len(result['sources'])}):")
    for source in result['sources']:
        print(f"  - {source['type']} {source['id']}: {source['title']} (relevance: {source['relevance']:.3f})")
    print(f"\n🎯 Confidence: {result['confidence']:.3f}")
    print(f"⚡ Retrieval time: {result['retrieval_time']:.4f}s")

    client.disconnect()

    print("\n" + "="*70)
    print("✓ RAG DEMO COMPLETE")
    print("="*70)
    print("\nTo use with a real LLM:")
    print("  1. Uncomment OpenAI or Anthropic integration code")
    print("  2. Add your API key")
    print("  3. Change llm_provider='openai' or 'anthropic'")
    print("\nThe system will then generate real AI-powered answers!")


if __name__ == "__main__":
    main()
