"""Application-wide constants used across modules."""
from __future__ import annotations

# Severity ordering used everywhere
SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]
SEVERITY_COLORS = {
    "info": "#3b82f6",
    "low": "#22c55e",
    "medium": "#eab308",
    "high": "#f97316",
    "critical": "#ef4444",
}

# Supported programming languages for analysis
SUPPORTED_LANGUAGES = [
    "python", "java", "javascript", "typescript",
    "c", "cpp", "csharp", "go", "rust",
]

LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "java": [".java"],
    "javascript": [".js", ".jsx", ".mjs"],
    "typescript": [".ts", ".tsx"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh"],
    "csharp": [".cs"],
    "go": [".go"],
    "rust": [".rs"],
}

# CVSS-inspired severity buckets
CVSS_BANDS = {
    "none": (0.0, 0.0),
    "low": (0.1, 3.9),
    "medium": (4.0, 6.9),
    "high": (7.0, 8.9),
    "critical": (9.0, 10.0),
}

# Agent identifiers
AGENT_NAMES = {
    "coordinator": "Coordinator Agent",
    "code_review": "Code Review Agent",
    "security": "Security Agent",
    "bug": "Bug Detection Agent",
    "auto_fix": "Auto Fix Agent",
    "documentation": "Documentation Agent",
    "refactor": "Refactoring Agent",
    "test": "Test Generator Agent",
    "uml": "UML Agent",
    "dependency": "Dependency Agent",
}

# Maximum file size in bytes to analyze (5MB)
MAX_FILE_ANALYZE_BYTES = 5 * 1024 * 1024

# Health score weights
HEALTH_SCORE_WEIGHTS = {
    "security": 0.30,
    "bug": 0.20,
    "code_review": 0.20,
    "documentation": 0.10,
    "test": 0.10,
    "dependency": 0.10,
}
