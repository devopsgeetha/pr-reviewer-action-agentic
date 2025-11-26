"""
API Routes for the PR Reviewer Bot
"""
import os
from dotenv import load_dotenv
from flask import request, jsonify
from app.api import api_bp
from app.services.github_service import GitHubService
from app.services.gitlab_service import GitLabService
from app.services.review_service import ReviewService
from app.utils.validators import validate_webhook_signature

# Load environment variables
load_dotenv()

# Initialize RAG service (optional - only if dependencies installed)
try:
    from app.services.rag_service import RAGService
    _rag_service = RAGService()
except ImportError:
    print("Warning: RAG dependencies not installed. Running without RAG enhancement.")
    _rag_service = None
except Exception as e:
    print(f"Warning: Could not initialize RAG service: {str(e)}")
    _rag_service = None


@api_bp.route("/webhooks/github", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook events"""
    try:
        # Validate webhook signature
        signature = request.headers.get("X-Hub-Signature-256")
        if not validate_webhook_signature(request.data, signature, "github"):
            return jsonify({"error": "Invalid signature"}), 401

        event_type = request.headers.get("X-GitHub-Event")
        payload = request.json

        # Only process pull request events
        if event_type == "pull_request":
            action = payload.get("action")
            if action in ["opened", "synchronize", "reopened", "review_requested"]:
                pr_data = payload.get("pull_request")

                # Trigger code review
                github_service = GitHubService()
                review_service = ReviewService(rag_service=_rag_service, use_agentic=True)

                # Get PR diff and files
                diff_data = github_service.get_pr_diff(pr_data)

                # Analyze with Agentic AI (or fallback to traditional)
                review_result = review_service.analyze_code(diff_data, github_service=github_service)

                # Post comments to PR
                github_service.post_review_comments(pr_data, review_result)

                return (
                    jsonify({"status": "success", "message": "Review completed"}),
                    200,
                )

        return (
            jsonify(
                {"status": "ignored", "message": f"Event {event_type} not processed"}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/webhooks/gitlab", methods=["POST"])
def gitlab_webhook():
    """Handle GitLab webhook events"""
    try:
        # Validate webhook token
        token = request.headers.get("X-Gitlab-Token")
        if not validate_webhook_signature(None, token, "gitlab"):
            return jsonify({"error": "Invalid token"}), 401

        event_type = request.headers.get("X-Gitlab-Event")
        payload = request.json

        # Only process merge request events
        if event_type == "Merge Request Hook":
            action = payload.get("object_attributes", {}).get("action")
            if action in ["open", "update", "reopen"]:
                mr_data = payload.get("object_attributes")

                # Trigger code review
                gitlab_service = GitLabService()
                review_service = ReviewService(rag_service=_rag_service, use_agentic=True)

                # Get MR diff and files
                diff_data = gitlab_service.get_mr_diff(mr_data)

                # Analyze with Agentic AI (or fallback to traditional)
                review_result = review_service.analyze_code(diff_data)

                # Post comments to MR
                gitlab_service.post_review_comments(mr_data, review_result)

                return (
                    jsonify({"status": "success", "message": "Review completed"}),
                    200,
                )

        return (
            jsonify(
                {"status": "ignored", "message": f"Event {event_type} not processed"}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/reviews", methods=["GET"])
def get_reviews():
    """Get all reviews"""
    try:
        review_service = ReviewService(rag_service=_rag_service)
        reviews = review_service.get_all_reviews()
        return jsonify({"reviews": reviews}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/reviews/<review_id>", methods=["GET"])
def get_review(review_id):
    """Get a specific review by ID"""
    try:
        review_service = ReviewService(rag_service=_rag_service)
        review = review_service.get_review_by_id(review_id)
        if review:
            return jsonify(review), 200
        return jsonify({"error": "Review not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analyze", methods=["POST"])
def analyze_code():
    """Manually trigger code analysis"""
    try:
        data = request.json
        code = data.get("code")
        language = data.get("language", "python")

        if not code:
            return jsonify({"error": "Code is required"}), 400

        review_service = ReviewService(rag_service=_rag_service)
        result = review_service.analyze_code_snippet(code, language)

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """Get or update application settings"""
    try:
        if request.method == "GET":
            # Return current settings (sanitized)
            return (
                jsonify(
                    {
                        "model": "gpt-4-turbo-preview",
                        "temperature": 0.3,
                        "features": {
                            "security_check": True,
                            "code_style": True,
                            "best_practices": True,
                            "performance": True,
                        },
                    }
                ),
                200,
            )
        else:
            # Update settings
            # TODO: Implement settings update logic
            return jsonify({"status": "success", "message": "Settings updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
