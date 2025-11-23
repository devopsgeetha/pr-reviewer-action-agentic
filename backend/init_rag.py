"""Initialize RAG service and seed with best practices."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import RAGService


def main():
    """Initialize RAG and seed with default best practices"""
    print("Initializing RAG service...")
    rag_service = RAGService()

    print("Seeding Python best practices...")
    rag_service.seed_best_practices("python")

    print("Seeding JavaScript best practices...")
    rag_service.seed_best_practices("javascript")

    print("\nRAG service initialized successfully!")
    print(
        "The knowledge base is located at: backend/data/chroma_db"
    )
    print("\nYou can now use RAG-enhanced code reviews.")


if __name__ == "__main__":
    main()
