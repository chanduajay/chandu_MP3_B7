# utils/classifier.py
"""
Regex-based incident type and severity detection.

All patterns are pre-compiled with re.IGNORECASE so casing in the raw data
does not affect classification.

Public API
----------
detect_type(text: str)     -> 'network' | 'security' | 'app' | 'general'
detect_severity(text: str) -> 'critical' | 'high' | 'medium' | 'low'
"""

import re

# ── Type patterns ──────────────────────────────────────────────────────────────
# network: IP addresses, protocol names, network hardware / topology keywords
network = re.compile(
    r"""
    \b(?:
        (?:\d{1,3}\.){3}\d{1,3}        # IPv4 address  e.g. 192.168.1.45
      | TCP | UDP | ICMP                # protocol names
      | VLAN | switch | firewall        # network hardware / topology
      | router | subnet | gateway       # additional network terms
      | DNS | packet | latency          # network diagnostics
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# security: threat keywords
security = re.compile(
    r"""
    \b(?:
        breach | ransomware | brute[\-\s]?force
      | malware | phishing | unauthorized
      | intrusion | exploit | vulnerability
      | threat | attack | compromise
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# app: error codes, exception names, HTTP status codes, stack-trace markers
app = re.compile(
    r"""
    \b(?:
        HTTP[\-\s]?\d{3}                        # HTTP-503, HTTP 404, HTTP503
      | [A-Z][a-zA-Z]+Exception                 # NullPointerException, etc.
      | [A-Z][a-zA-Z]+Error                     # ValueError, RuntimeError, etc.
      | error[\s_]?code                         # "error code", "error_code"
      | stack[\s_]?trace                        # stack trace
      | timeout | latency | p95 | p99           # performance indicators
      | deploy | build | pipeline | release     # CI/CD terms
      | api | endpoint | microservice           # application-layer terms
      | checkout | payment | gateway | service  # business-layer application terms
      | job[\s_]?fail                           # scheduled job failed
      | response[\s_]?slow | slow[\s_]?response
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ── Severity keyword patterns ──────────────────────────────────────────────────
critical_kw = re.compile(
    r"\b(?:outage|down|breach|ransomware|production|critical|emergency|offline)\b",
    re.IGNORECASE,
)

high_kw = re.compile(
    r"\b(?:timeout|failing|unavailable|unreachable|high|urgent|severe)\b",
    re.IGNORECASE,
)

medium_kw = re.compile(
    r"\b(?:slow|degraded|warning|intermittent|medium|moderate|occasional)\b",
    re.IGNORECASE,
)


# ── Public functions ───────────────────────────────────────────────────────────
def detect_type(text: str) -> str:
    """
    Return 'network', 'security', 'app', or 'general' based on keyword matching.

    Priority order: security > network > app > general
    (Security incidents are highest priority to flag first.)
    """
    if security.search(text):
        return "security"
    if network.search(text):
        return "network"
    if app.search(text):
        return "app"
    return "general"


def detect_severity(text: str) -> str:
    """
    Return 'critical', 'high', 'medium', or 'low' based on keyword matching.

    Priority order: critical > high > medium > low (default).
    """
    if critical_kw.search(text):
        return "critical"
    if high_kw.search(text):
        return "high"
    if medium_kw.search(text):
        return "medium"
    return "low"
