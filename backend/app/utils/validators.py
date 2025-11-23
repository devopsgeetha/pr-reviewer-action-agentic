"""
Utility functions for webhook validation
"""
import os
import hmac
import hashlib


def validate_webhook_signature(payload: bytes, signature: str, platform: str) -> bool:
    """
    Validate webhook signature from GitHub or GitLab

    Args:
        payload: Request payload
        signature: Signature from request headers
        platform: 'github' or 'gitlab'

    Returns:
        True if signature is valid, False otherwise
    """
    if platform == "github":
        return _validate_github_signature(payload, signature)
    elif platform == "gitlab":
        return _validate_gitlab_token(signature)
    return False


def _validate_github_signature(payload: bytes, signature: str) -> bool:
    """Validate GitHub webhook signature"""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret or not signature:
        return False

    # GitHub sends signature as: sha256=<hash>
    if not signature.startswith("sha256="):
        return False

    expected_signature = (
        "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    )

    return hmac.compare_digest(expected_signature, signature)


def _validate_gitlab_token(token: str) -> bool:
    """Validate GitLab webhook token"""
    secret = os.getenv("GITLAB_WEBHOOK_SECRET")
    if not secret or not token:
        return False

    return hmac.compare_digest(secret, token)
