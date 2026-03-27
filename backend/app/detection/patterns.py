"""Heuristic patterns for detecting CI/CD pipeline source platform, format, and config type."""

import re

# ============================================
# Platform + Format Detection Patterns
# Each tuple: (compiled_regex, weight)
# ============================================

TEAMCITY_KOTLIN_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"import\s+jetbrains\.buildServer\.configs\.kotlin"), 0.4),
    (re.compile(r"project\s*\{"), 0.15),
    (re.compile(r"buildType\s*\{"), 0.2),
    (re.compile(r"object\s+\w+\s*:\s*BuildType"), 0.3),
    (re.compile(r"vcsRoot\s*\("), 0.15),
    (re.compile(r"triggers\s*\{"), 0.1),
    (re.compile(r"steps\s*\{"), 0.05),
    (re.compile(r"\.kts\b"), 0.1),
]

TEAMCITY_XML_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"<build-type"), 0.3),
    (re.compile(r"<build-runners>"), 0.3),
    (re.compile(r"<vcs-root"), 0.2),
    (re.compile(r"<project\b.*jetbrains", re.IGNORECASE), 0.3),
    (re.compile(r"<step\s+.*type="), 0.15),
    (re.compile(r"<param\s+name=.*value="), 0.1),
]

TEAMCITY_JSON_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r'"buildType"\s*:'), 0.25),
    (re.compile(r'"buildTypes"\s*:'), 0.25),
    (re.compile(r'"vcsRootEntries"\s*:'), 0.2),
    (re.compile(r'"steps"\s*:.*"type"\s*:\s*"(simpleRunner|gradle|maven|dotnet)'), 0.3),
    (re.compile(r'"build-configuration"', re.IGNORECASE), 0.2),
    (re.compile(r'"snapshot-dependencies"'), 0.15),
]

JENKINS_GROOVY_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"pipeline\s*\{"), 0.35),
    (re.compile(r"node\s*\{"), 0.2),
    (re.compile(r"stage\s*\(\s*['\"]"), 0.2),
    (re.compile(r"agent\s+(any|none|\{)"), 0.25),
    (re.compile(r"@Library\s*\("), 0.3),
    (re.compile(r"\bsh\s+['\"]"), 0.1),
    (re.compile(r"steps\s*\{"), 0.05),
    (re.compile(r"post\s*\{"), 0.1),
    (re.compile(r"environment\s*\{"), 0.05),
]

# ============================================
# Config Type Detection Patterns
# ============================================

# Shared Library indicators
SHARED_LIBRARY_PATTERNS: list[tuple[re.Pattern, float]] = [
    # Jenkins
    (re.compile(r"@Library\s*\("), 0.35),
    (re.compile(r"def\s+call\s*\("), 0.3),
    (re.compile(r"vars/"), 0.2),
    (re.compile(r"src/org/"), 0.15),
    # TeamCity
    (re.compile(r"class\s+\w+\s*:\s*(?:BuildType|Template)"), 0.3),
    (re.compile(r"abstract\s+class"), 0.15),
]

# Complete Pipeline indicators
COMPLETE_PIPELINE_PATTERNS: list[tuple[re.Pattern, float]] = [
    # Jenkins
    (re.compile(r"pipeline\s*\{[\s\S]*agent\s+"), 0.3),
    (re.compile(r"stages\s*\{[\s\S]*stage\s*\("), 0.25),
    # TeamCity Kotlin
    (re.compile(r"project\s*\{[\s\S]*buildType"), 0.3),
    # TeamCity XML
    (re.compile(r"<project\b"), 0.25),
]

# Fragment indicators (detected by presence of inner constructs WITHOUT top-level wrappers)
# These are scored dynamically in detect_config_type() instead of using broken negative lookaheads
FRAGMENT_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"stage\s*\("), 0.2),
    (re.compile(r"<build-runner"), 0.2),
    (re.compile(r"buildType\s*\{"), 0.2),
]

# Top-level wrappers that indicate this is NOT a fragment
FRAGMENT_NEGATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"pipeline\s*\{"),
    re.compile(r"<project\b"),
    re.compile(r"project\s*\{"),
]


def _score_patterns(content: str, patterns: list[tuple[re.Pattern, float]]) -> tuple[float, list[str]]:
    """Score content against a list of patterns. Returns (score, matched_patterns)."""
    total = 0.0
    matched = []
    for pattern, weight in patterns:
        if pattern.search(content):
            total += weight
            matched.append(pattern.pattern)
    return min(total, 1.0), matched


def detect_platform_and_format(
    content: str, filename: str | None = None
) -> dict:
    """
    Detect source platform and format using heuristic pattern matching.

    Returns dict with: source_platform, source_format, confidence, matched_patterns
    """
    scores = {}

    # Score each platform/format
    tc_kotlin_score, tc_kotlin_matched = _score_patterns(content, TEAMCITY_KOTLIN_PATTERNS)
    tc_xml_score, tc_xml_matched = _score_patterns(content, TEAMCITY_XML_PATTERNS)
    tc_json_score, tc_json_matched = _score_patterns(content, TEAMCITY_JSON_PATTERNS)
    jenkins_score, jenkins_matched = _score_patterns(content, JENKINS_GROOVY_PATTERNS)

    # Filename hints
    if filename:
        lower_name = filename.lower()
        if lower_name.endswith(".kts"):
            tc_kotlin_score += 0.3
        elif lower_name.endswith(".xml"):
            tc_xml_score += 0.2
        elif lower_name.endswith(".json"):
            tc_json_score += 0.15
        elif lower_name in ("jenkinsfile",) or lower_name.endswith(".groovy"):
            jenkins_score += 0.3

    scores = {
        ("teamcity", "kotlin_dsl"): (min(tc_kotlin_score, 1.0), tc_kotlin_matched),
        ("teamcity", "xml"): (min(tc_xml_score, 1.0), tc_xml_matched),
        ("teamcity", "json_api"): (min(tc_json_score, 1.0), tc_json_matched),
        ("jenkins", "groovy"): (min(jenkins_score, 1.0), jenkins_matched),
    }

    # Pick the highest scoring
    best_key = max(scores, key=lambda k: scores[k][0])
    best_score, best_matched = scores[best_key]

    return {
        "source_platform": best_key[0],
        "source_format": best_key[1],
        "confidence": round(best_score, 3),
        "matched_patterns": best_matched,
    }


def detect_config_type(content: str) -> dict:
    """
    Detect whether the config is a shared library, complete pipeline, or fragment.

    Returns dict with: config_type, confidence
    """
    shared_score, _ = _score_patterns(content, SHARED_LIBRARY_PATTERNS)
    complete_score, _ = _score_patterns(content, COMPLETE_PIPELINE_PATTERNS)
    fragment_score, _ = _score_patterns(content, FRAGMENT_PATTERNS)

    # If any top-level wrapper is present, suppress fragment score
    for negation in FRAGMENT_NEGATION_PATTERNS:
        if negation.search(content):
            fragment_score = 0.0
            break

    scores = {
        "shared_library": shared_score,
        "complete_pipeline": complete_score,
        "fragment": fragment_score,
    }

    best_type = max(scores, key=scores.get)
    return {
        "config_type": best_type,
        "confidence": round(scores[best_type], 3),
    }
