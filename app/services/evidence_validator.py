"""
Evidence validation service for GitHub repos and screenshots.
"""

import re
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.core.logging import log


# Constants
GITHUB_API_BASE = "https://api.github.com"
GITHUB_REPO_PATTERN = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/?.*$")
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_SCREENSHOT_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
REQUEST_TIMEOUT = 10.0  # seconds


class EvidenceValidationError(Exception):
    """Raised when evidence validation fails."""
    def __init__(self, message: str, evidence_type: str, url: str):
        self.message = message
        self.evidence_type = evidence_type
        self.url = url
        super().__init__(message)


def validate_github_url(url: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a GitHub repository URL.
    
    Args:
        url: GitHub URL (e.g., https://github.com/user/repo)
        
    Returns:
        Tuple of (is_valid, metadata, error_message)
        - is_valid: True if repo exists and is accessible
        - metadata: Repo info (full_name, stars, forks, etc.) if valid
        - error_message: Error description if invalid
    """
    log.info("evidence_validation: GitHub validation started", extra={"url": url})
    
    # Parse URL to extract user and repo
    match = GITHUB_REPO_PATTERN.match(url)
    if not match:
        error = f"Invalid GitHub URL format. Expected: https://github.com/user/repo"
        log.warning("evidence_validation: GitHub URL invalid format", extra={"url": url, "error": error})
        return False, None, error
    
    user, repo = match.groups()
    # Remove any trailing path segments or .git suffix
    repo = repo.rstrip("/").removesuffix(".git")
    
    api_url = f"{GITHUB_API_BASE}/repos/{user}/{repo}"
    
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        
        if response.status_code == 200:
            data = response.json()
            metadata = {
                "full_name": data.get("full_name"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "pushed_at": data.get("pushed_at"),
                "default_branch": data.get("default_branch"),
                "description": data.get("description"),
                "private": data.get("private", False),
            }
            log.info(
                "evidence_validation: GitHub validation success",
                extra={"url": url, "full_name": metadata["full_name"]}
            )
            return True, metadata, None
        
        elif response.status_code == 404:
            error = f"GitHub repository not found: {user}/{repo}"
            log.warning("evidence_validation: GitHub repo not found", extra={"url": url})
            return False, None, error
        
        elif response.status_code == 403:
            # Rate limited or forbidden - keep evidence but mark as not validated
            log.warning(
                "evidence_validation: GitHub API rate limited or forbidden",
                extra={"url": url, "status": response.status_code}
            )
            return False, {"rate_limited": True}, "GitHub API rate limited, validation deferred"
        
        else:
            error = f"GitHub API returned status {response.status_code}"
            log.warning("evidence_validation: GitHub API error", extra={"url": url, "status": response.status_code})
            return False, None, error
            
    except httpx.TimeoutException:
        log.warning("evidence_validation: GitHub API timeout", extra={"url": url})
        return False, {"timeout": True}, "GitHub API timeout, validation deferred"
    
    except Exception as e:
        log.error("evidence_validation: GitHub validation exception", extra={"url": url, "error": str(e)})
        return False, None, f"Validation error: {str(e)}"


def validate_screenshot_url(url: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a screenshot/image URL.
    
    Args:
        url: URL to an image file
        
    Returns:
        Tuple of (is_valid, metadata, error_message)
    """
    log.info("evidence_validation: Screenshot validation started", extra={"url": url})
    
    # Check file extension
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    extension = path_lower.split(".")[-1] if "." in path_lower else ""
    
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        error = f"Invalid image extension '{extension}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        log.warning("evidence_validation: Invalid image extension", extra={"url": url, "extension": extension})
        return False, None, error
    
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            response = client.head(url)
        
        if response.status_code != 200:
            error = f"Image URL returned status {response.status_code}"
            log.warning("evidence_validation: Screenshot HEAD failed", extra={"url": url, "status": response.status_code})
            return False, None, error
        
        content_type = response.headers.get("content-type", "")
        content_length = response.headers.get("content-length")
        
        # Validate content type
        if not content_type.startswith("image/"):
            error = f"Invalid content type '{content_type}'. Expected image/*"
            log.warning("evidence_validation: Invalid content type", extra={"url": url, "content_type": content_type})
            return False, None, error
        
        # Validate size
        if content_length:
            size = int(content_length)
            if size > MAX_SCREENSHOT_SIZE_BYTES:
                error = f"Image too large ({size / 1024 / 1024:.1f}MB). Max allowed: 5MB"
                log.warning("evidence_validation: Image too large", extra={"url": url, "size": size})
                return False, None, error
        
        metadata = {
            "content_type": content_type,
            "content_length": int(content_length) if content_length else None,
            "host": parsed.netloc,
        }
        
        log.info("evidence_validation: Screenshot validation success", extra={"url": url, "metadata": metadata})
        return True, metadata, None
        
    except httpx.TimeoutException:
        log.warning("evidence_validation: Screenshot validation timeout", extra={"url": url})
        return False, {"timeout": True}, "Image URL timeout, validation deferred"
    
    except Exception as e:
        log.error("evidence_validation: Screenshot validation exception", extra={"url": url, "error": str(e)})
        return False, None, f"Validation error: {str(e)}"


def validate_evidence(evidence_type: str, url: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a single evidence item.
    
    Args:
        evidence_type: Type of evidence (github | screenshot)
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, metadata, error_message)
    """
    if evidence_type == "github":
        return validate_github_url(url)
    elif evidence_type == "screenshot":
        return validate_screenshot_url(url)
    else:
        return False, None, f"Unknown evidence type: {evidence_type}"
