"""
Service for LLM integration using Langchain and OpenAI
"""
import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate


class LLMService:
    """Handle LLM operations for code analysis"""

    def __init__(self, rag_service=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.3))
        self.rag_service = rag_service  # Optional RAG service
        
        # Debug logging
        print(f"LLMService init - API Key present: {bool(self.api_key)}")
        if self.api_key:
            print(f"LLMService init - API Key starts with: {self.api_key[:10]}...")

        # Only initialize LLM if API key is available
        if self.api_key:
            try:
                self.llm = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    api_key=self.api_key,  # Use api_key parameter instead of openai_api_key
                )
                print(f"LLMService init - Successfully initialized ChatOpenAI with model {self.model}")
            except TypeError as exc:
                # Some environments configure unsupported kwargs (e.g. proxies).
                print(
                    "Warning: Failed to initialize OpenAI client. "
                    f"Using fallback mode. Details: {exc}"
                )
                self.llm = None
            except Exception as exc:
                print(
                    "Warning: Unexpected error initializing OpenAI client. "
                    f"Using fallback mode. Details: {exc}"
                )
                self.llm = None
        else:
            self.llm = None
            print("Warning: OPENAI_API_KEY not set. LLM features will be disabled.")

        self._init_prompts()

    def _init_prompts(self):
        """Initialize prompt templates"""

        # Code analysis prompt
        self.analysis_prompt = PromptTemplate(
            input_variables=["code", "filename", "language"],
            template="""You are an expert code reviewer.
Analyze the following code changes and provide a detailed review.

Filename: {filename}
Language: {language}

Code Changes:
```
{code}
```

Please analyze this code for:
1. **Bugs and Errors**: Identify potential bugs, logic errors, or runtime issues
2. **Security Vulnerabilities**: Check for security flaws, injection risks, or unsafe practices
3. **Code Quality**: Assess code readability, maintainability, and adherence to best practices
4. **Performance**: Identify potential performance bottlenecks or inefficiencies
5. **Style and Standards**: Check compliance with coding standards and conventions

Provide your response in the following JSON format:
{{
    "issues": [
        {{
            "severity": "high|medium|low",
            "category": "bug|security|quality|performance|style",
            "message": "Description of the issue",
            "line": line_number_if_applicable,
            "file": "{filename}"
        }}
    ],
    "suggestions": [
        "Specific improvement suggestions"
    ]
}}

Be specific and actionable in your feedback.""",
        )

        # Summary generation prompt
        self.summary_prompt = PromptTemplate(
            input_variables=["context", "issues_count", "suggestions_count"],
            template="""Generate a concise summary for a pull request review.

PR Context:
- Title: {context}
- Total Issues Found: {issues_count}
- Total Suggestions: {suggestions_count}

Provide a brief 2-3 sentence summary that:
1. Highlights the main findings
2. Mentions critical issues if any
3. Gives an overall assessment

Keep it professional and constructive.""",
        )

    def analyze_code_changes(
        self, code: str, filename: str, language: str
    ) -> Dict[str, Any]:
        """
        Analyze code changes using LLM with optional RAG context

        Args:
            code: The code diff or snippet
            filename: Name of the file
            language: Programming language

        Returns:
            Dictionary containing analysis results
        """
        if not self.llm:
            return {
                "issues": [],
                "suggestions": [
                    "OpenAI API key not configured. LLM analysis unavailable."
                ],
            }

        try:
            # Get RAG context if available
            rag_context = ""
            if self.rag_service:
                try:
                    rag_context = self.rag_service.get_relevant_context(
                        code, filename, language
                    )
                except Exception as e:
                    print(f"Warning: RAG context retrieval failed: {str(e)}")

            # Build enhanced prompt with RAG context
            enhanced_code = code
            if rag_context:
                enhanced_code = f"""# Relevant Context from Past Reviews:
{rag_context}

# Code to Review:
{code}"""

            # Use new LangChain pattern (RunnableSequence) instead of deprecated LLMChain
            # Format prompt with variables and use pipe operator
            formatted_prompt = self.analysis_prompt.format(
                code=enhanced_code, filename=filename, language=language
            )
            
            # Use pipe operator: prompt | llm (replaces deprecated chain.run)
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=formatted_prompt)
            result = self.llm.invoke([message]).content

            # Parse result (assuming JSON response)
            import json

            try:
                analysis = json.loads(result)
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                analysis = {"issues": [], "suggestions": [result]}

            return analysis

        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            return {"issues": [], "suggestions": []}

    def generate_summary(self, context: Dict, review_result: Dict) -> str:
        """
        Generate summary of the review

        Args:
            context: Context about the PR/MR
            review_result: Results from code analysis

        Returns:
            Summary text
        """
        if not self.llm:
            return "Code review completed. OpenAI API key not configured for detailed summary."

        try:
            # Use new LangChain pattern instead of deprecated LLMChain
            formatted_prompt = self.summary_prompt.format(
                context=str(context),
                issues_count=len(review_result.get("issues", [])),
                suggestions_count=len(review_result.get("suggestions", [])),
            )
            
            # Use pipe operator: prompt | llm (replaces deprecated chain.run)
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=formatted_prompt)
            summary = self.llm.invoke([message]).content

            return summary.strip()

        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "Code review completed. Please review the detailed findings below."
