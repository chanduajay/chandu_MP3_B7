# utils/helpers.py
"""
Functional helper utilities using map, filter, and reduce.
"""

from functools import reduce


def get_critical_incidents(incidents: list) -> list:
    """Return only critical-severity incidents (uses filter + lambda)."""
    return list(filter(lambda i: i.severity == "critical", incidents))


def get_incidents_by_severity(incidents: list, severity: str) -> list:
    """Return incidents matching the given severity level (uses filter + lambda)."""
    return list(filter(lambda i: i.severity == severity, incidents))


def build_jira_payloads(incidents: list) -> list:
    """Return a list of to_dict() representations for all incidents (uses map + lambda)."""
    return list(map(lambda i: i.to_dict(), incidents))


def count_by_team(incidents: list) -> dict:
    """Return a dict mapping assigned_team -> incident count (uses reduce + lambda)."""
    return reduce(
        lambda acc, i: {**acc, i.assigned_team: acc.get(i.assigned_team, 0) + 1},
        incidents,
        {},
    )


def count_by_severity(incidents: list) -> dict:
    """Return a dict mapping severity -> count (uses reduce + lambda)."""
    return reduce(
        lambda acc, i: {**acc, i.severity: acc.get(i.severity, 0) + 1},
        incidents,
        {},
    )


def count_by_type(incidents: list) -> dict:
    """Return a dict mapping incident type name -> count (uses reduce + lambda)."""
    return reduce(
        lambda acc, i: {**acc, type(i).__name__: acc.get(type(i).__name__, 0) + 1},
        incidents,
        {},
    )
