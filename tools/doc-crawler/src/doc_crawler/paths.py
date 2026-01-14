"""
Semantic path generation for documentation files.

Provides utilities for generating human-readable, topic-organized file paths
from article metadata. This enables effective discovery via Glob patterns
when used by agentic frameworks like Claude Code.
"""

import re

__all__ = [
    "TOPIC_DESCRIPTIONS",
    "TOPIC_KEYWORDS",
    "classify_topic",
    "extract_keywords",
    "generate_semantic_path",
    "slugify",
]

# Topic classification based on keywords in title/content
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "vlans": ["vlan", "network", "subnet", "dhcp", "ip range"],
    "firewall": [
        "firewall",
        "traffic",
        "rule",
        "block",
        "allow",
        "port forwarding",
        "threat management",
    ],
    "switching": ["switch", "port", "poe", "lacp", "trunk", "stp", "aggregation"],
    "wireless": ["wifi", "wireless", "ssid", "ap", "access point", "wlan", "radio"],
    "vpn": ["vpn", "wireguard", "ipsec", "openvpn", "teleport", "site-to-site"],
    "gateway": ["gateway", "wan", "internet", "routing", "nat", "isp"],
    "clients": ["client", "device", "fingerprint", "block client", "alias"],
    "system": [
        "backup",
        "restore",
        "update",
        "firmware",
        "controller",
        "adopt",
        "migrate",
        "console",
    ],
    "troubleshooting": [
        "troubleshoot",
        "debug",
        "log",
        "issue",
        "problem",
        "fix",
        "error",
    ],
}

TOPIC_DESCRIPTIONS: dict[str, str] = {
    "vlans": "VLAN and network configuration",
    "firewall": "Firewall rules and traffic management",
    "switching": "Switch configuration and port management",
    "wireless": "WiFi and access point configuration",
    "vpn": "VPN setup and remote access",
    "gateway": "Gateway, WAN, and routing configuration",
    "clients": "Client device management",
    "system": "System administration and maintenance",
    "troubleshooting": "Debugging and problem resolution",
    "general": "General documentation",
}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: Text to convert to a slug.

    Returns:
        Lowercase, hyphenated slug with special characters removed.
        Maximum length is 60 characters, truncated at word boundary.
    """
    # Lowercase
    slug = text.lower()
    # Remove special characters
    slug = re.sub(r"[^\w\s-]", "", slug)
    # Replace whitespace with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    # Trim hyphens from ends
    slug = slug.strip("-")
    # Limit length, truncate at word boundary
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0]
    return slug


def _word_match(keyword: str, text: str) -> bool:
    """Check if keyword matches as a whole word in text.

    Uses regex word boundaries to avoid partial matches like
    'port' matching in 'teleport'.

    Args:
        keyword: Keyword to search for.
        text: Text to search in.

    Returns:
        True if keyword is found as a whole word.
    """
    # For multi-word keywords, search for exact phrase
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return bool(re.search(pattern, text))


def classify_topic(title: str, content: str = "") -> str:
    """Classify article into a topic based on keywords.

    Scans the title and content for topic-specific keywords and returns
    the topic with the highest match score. Uses word boundary matching
    to avoid partial matches.

    Args:
        title: Article title.
        content: Optional article content for better classification.

    Returns:
        Topic name (e.g., "vlans", "firewall", "general").
    """
    text = f"{title} {content}".lower()

    scores: dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if _word_match(kw, text))
        if score > 0:
            scores[topic] = score

    if scores:
        return max(scores, key=lambda k: scores[k])
    return "general"


def generate_semantic_path(
    title: str,
    content: str = "",
    base_dir: str = "help-center",
) -> str:
    """Generate semantic file path for an article.

    Creates a path organized by topic with a human-readable filename
    derived from the article title.

    Args:
        title: Article title.
        content: Article content (for better classification).
        base_dir: Base directory for output.

    Returns:
        Semantic path like "help-center/vlans/creating-vlans.md".

    Note:
        The original article_id should be preserved in frontmatter
        for traceability, but is not used in path generation.
    """
    topic = classify_topic(title, content)
    slug = slugify(title)
    return f"{base_dir}/{topic}/{slug}.md"


def extract_keywords(title: str, content: str = "") -> list[str]:
    """Extract relevant keywords from title and content.

    Searches for common UniFi-related keywords in the provided text
    using word boundary matching to avoid partial matches.

    Args:
        title: Article title.
        content: Article content.

    Returns:
        List of found keywords (maximum 10).
    """
    text = f"{title} {content}".lower()

    # Common UniFi keywords to look for
    keyword_candidates = [
        "vlan",
        "network",
        "firewall",
        "switch",
        "port",
        "wifi",
        "wireless",
        "ssid",
        "vpn",
        "gateway",
        "wan",
        "dhcp",
        "dns",
        "nat",
        "routing",
        "qos",
        "traffic",
        "rule",
        "client",
        "device",
        "ap",
        "controller",
        "backup",
        "restore",
        "update",
        "firmware",
        "adopt",
        "provision",
        "poe",
        "lacp",
        "trunk",
        "stp",
        "radius",
        "certificate",
        "ssl",
        "wireguard",
        "ipsec",
        "teleport",
        "threat",
        "dpi",
        "ids",
        "ips",
    ]

    found = [kw for kw in keyword_candidates if _word_match(kw, text)]
    return found[:10]
