"""RAG Service for retrieving relevant code review context."""

import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class RAGService:
    """Handle Retrieval Augmented Generation (RAG) operations for code review context retrieval"""

    def __init__(self):
        """Initialize ChromaDB and embedding model"""
        # Initialize ChromaDB client
        persist_directory = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "chroma_db"
        )
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_directory)

        # Create or get collections
        self.reviews_collection = self.client.get_or_create_collection(
            name="code_reviews", metadata={"description": "Past code review data"}
        )

        self.patterns_collection = self.client.get_or_create_collection(
            name="code_patterns",
            metadata={"description": "Common code patterns and best practices"},
        )

        # Initialize local embedding model (faster and free)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_review_to_knowledge_base(self, review_data: Dict[str, Any]) -> None:
        """
        Store completed review in vector DB for future reference

        Args:
            review_data: Dictionary containing review results
        """
        try:
            # Create a searchable text representation
            review_text = self._format_review_for_storage(review_data)

            # Generate embedding
            embedding = self.embedding_model.encode(review_text).tolist()

            # Store in ChromaDB
            self.reviews_collection.add(
                embeddings=[embedding],
                documents=[review_text],
                metadatas=[
                    {
                        "pr_number": str(review_data.get("pr_number", "")),
                        "repository": review_data.get("repository", ""),
                        "score": review_data.get("overall_score", 0),
                        "timestamp": str(review_data.get("timestamp", "")),
                    }
                ],
                ids=[str(review_data.get("_id", review_data.get("pr_number", "")))]
                if review_data.get("_id")
                else None,
            )
        except Exception as e:
            print(f"Warning: Could not add review to knowledge base: {str(e)}")

    def get_relevant_context(
        self, code: str, filename: str, language: str, top_k: int = 3
    ) -> str:
        """
        Retrieve relevant context for code review

        Args:
            code: Code snippet to analyze
            filename: Name of the file
            language: Programming language
            top_k: Number of relevant documents to retrieve

        Returns:
            Concatenated context string
        """
        try:
            # Create query from code context
            query = f"Code review for {language} file {filename}:\n{code[:500]}"

            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()

            # Search for similar past reviews
            results = self.reviews_collection.query(
                query_embeddings=[query_embedding], n_results=min(top_k, 3)
            )

            # Search for relevant patterns
            pattern_results = self.patterns_collection.query(
                query_embeddings=[query_embedding], n_results=min(top_k, 2)
            )

            # Combine and format results
            context_parts = []

            if results["documents"] and results["documents"][0]:
                context_parts.append("## Similar Past Reviews:")
                for doc in results["documents"][0][:2]:
                    context_parts.append(doc[:500])  # Limit context size

            if pattern_results["documents"] and pattern_results["documents"][0]:
                context_parts.append("\n## Relevant Code Patterns:")
                for doc in pattern_results["documents"][0][:2]:
                    context_parts.append(doc[:500])

            return "\n\n".join(context_parts) if context_parts else ""

        except Exception as e:
            print(f"Warning: Could not retrieve RAG context: {str(e)}")
            return ""

    def seed_best_practices(self, language: str = "python") -> None:
        """
        Seed the knowledge base with common best practices

        Args:
            language: Programming language to seed practices for
        """
        try:
            best_practices = self._get_default_best_practices(language)

            for idx, practice in enumerate(best_practices):
                embedding = self.embedding_model.encode(practice).tolist()
                self.patterns_collection.add(
                    embeddings=[embedding],
                    documents=[practice],
                    metadatas=[{"language": language, "category": "best_practice"}],
                    ids=[f"{language}_bp_{idx}"],
                )

            print(
                f"Seeded {len(best_practices)} best practices for {language}"
            )
        except Exception as e:
            print(f"Warning: Could not seed best practices: {str(e)}")

    def _format_review_for_storage(self, review_data: Dict[str, Any]) -> str:
        """Format review data as searchable text"""
        parts = [
            f"Repository: {review_data.get('repository', 'unknown')}",
            f"Score: {review_data.get('overall_score', 0)}",
            f"Summary: {review_data.get('summary', '')}",
        ]

        issues = review_data.get("issues", [])
        if issues:
            parts.append(f"Issues found: {len(issues)}")
            for issue in issues[:3]:  # Limit to top 3
                parts.append(
                    f"- {issue.get('severity', 'unknown')}: {issue.get('message', '')[:200]}"
                )

        suggestions = review_data.get("suggestions", [])
        if suggestions:
            parts.append(f"Suggestions: {len(suggestions)}")
            for suggestion in suggestions[:3]:
                if isinstance(suggestion, str):
                    parts.append(f"- {suggestion[:200]}")

        return "\n".join(parts)

    def _get_default_best_practices(self, language: str) -> List[str]:
        """Get default best practices for seeding"""
        python_practices = [
            """Python Security Best Practices:
- Never use eval() or exec() with user input
- Validate and sanitize all external inputs
- Use parameterized queries to prevent SQL injection
- Avoid pickle for untrusted data
- Use secrets module for cryptographic operations
- Set proper file permissions (not 777)
- Keep dependencies updated and scan for vulnerabilities""",
            """Python Code Quality:
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Write docstrings for all public functions and classes
- Keep functions small and focused (under 50 lines)
- Avoid deep nesting (max 3-4 levels)
- Use list comprehensions for simple transformations
- Prefer context managers (with statements) for resource handling""",
            """Python Performance:
- Use generators for large datasets
- Leverage built-in functions (map, filter, sum)
- Avoid premature optimization
- Profile before optimizing
- Use __slots__ for memory-intensive classes
- Cache expensive computations with functools.lru_cache
- Use set operations for membership tests""",
            """Python Error Handling:
- Use specific exception types, not bare except
- Raise custom exceptions for domain errors
- Include context in error messages
- Clean up resources in finally blocks
- Don't suppress exceptions silently
- Log errors with proper context
- Use logging module instead of print statements""",
        ]

        javascript_practices = [
            """JavaScript Security:
- Sanitize user input to prevent XSS
- Use Content Security Policy headers
- Avoid eval() and Function() constructor
- Validate data on server side
- Use HTTPS for all communications
- Implement CSRF protection
- Keep npm packages updated""",
            """JavaScript Best Practices:
- Use const/let instead of var
- Use strict equality (===)
- Handle Promise rejections
- Use async/await for async code
- Avoid callback hell
- Use modules (ES6 imports)
- Write pure functions when possible""",
        ]

        practices_map = {"python": python_practices, "javascript": javascript_practices}

        return practices_map.get(language.lower(), python_practices)

    def clear_knowledge_base(self) -> None:
        """Clear all data from knowledge base (for testing/reset)"""
        try:
            self.client.delete_collection("code_reviews")
            self.client.delete_collection("code_patterns")
            self.reviews_collection = self.client.create_collection("code_reviews")
            self.patterns_collection = self.client.create_collection("code_patterns")
            print("Knowledge base cleared")
        except Exception as e:
            print(f"Warning: Could not clear knowledge base: {str(e)}")
