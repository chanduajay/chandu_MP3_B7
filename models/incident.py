# models/incident.py
"""
Incident base class, three subclasses (NetworkIncident, AppIncident, SecurityIncident),
IncidentIterator, and batch_incidents generator — exactly as specified in the project spec.
"""

import logging
from datetime import datetime
from utils.classifier import detect_type, detect_severity


# ── Severity ordering (critical=0 sorts first, low=3 sorts last) ─────────────
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


# ══════════════════════════════════════════════════════════════════════════════
# Base class
# ══════════════════════════════════════════════════════════════════════════════
class Incident:
    """Abstract base class shared by all incident types."""

    # ── Static validator ──────────────────────────────────────────────────────
    REQUIRED_FIELDS = {"id", "title", "description", "reported_by",
                       "timestamp", "assigned_team"}

    @staticmethod
    def validate_schema(record: dict) -> bool:
        """Validate that a JSON record contains all required fields.

        Raises ValueError if any field is missing.
        Returns True if valid.
        """
        missing = Incident.REQUIRED_FIELDS - record.keys()
        if missing:
            raise ValueError(
                f"Incident record missing required fields: {missing}  |  record id={record.get('id', 'UNKNOWN')}"
            )
        return True

    # ── Constructor ───────────────────────────────────────────────────────────
    def __init__(self, id, title, description, reported_by, timestamp, assigned_team):
        self.id            = id
        self.title         = title
        self.description   = description
        self.reported_by   = reported_by
        self.timestamp     = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        self.assigned_team = assigned_team
        self._severity     = None   # private — set by classify()
        self.ticket_ids    = {}     # populated after API calls

    # ── Abstract method ───────────────────────────────────────────────────────
    def classify(self):
        """Must be overridden by every subclass."""
        raise NotImplementedError("Subclasses must implement classify()")

    # ── Severity property ─────────────────────────────────────────────────────
    @property
    def severity(self):
        return self._severity

    # ── Serialisation ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "title":         self.title,
            "description":   self.description,
            "reported_by":   self.reported_by,
            "timestamp":     self.timestamp.isoformat(),
            "assigned_team": self.assigned_team,
            "severity":      self._severity,
            "ticket_ids":    self.ticket_ids,
            "type":          type(self).__name__,
        }

    def __str__(self):
        return (
            f"[{self.id}] {self.title} | "
            f"Type: {type(self).__name__} | "
            f"Severity: {self._severity} | "
            f"Team: {self.assigned_team}"
        )

    def __repr__(self):
        return (
            f"{type(self).__name__}(id={self.id!r}, "
            f"severity={self._severity!r}, "
            f"assigned_team={self.assigned_team!r})"
        )

    def __lt__(self, other):
        """Enable sorting by severity; critical < high < medium < low."""
        return _SEVERITY_ORDER.get(self._severity, 99) < _SEVERITY_ORDER.get(other._severity, 99)


# ══════════════════════════════════════════════════════════════════════════════
# Subclass 1 — NetworkIncident
# ══════════════════════════════════════════════════════════════════════════════
class NetworkIncident(Incident):
    """Incident related to network infrastructure."""

    def __init__(self, id, title, description, reported_by,
                 timestamp, assigned_team, affected_host="", protocol=""):
        super().__init__(id, title, description, reported_by, timestamp, assigned_team)
        self.affected_host = affected_host
        self.protocol      = protocol

    def classify(self):
        """Detect severity using combined title + description text."""
        combined = f"{self.title} {self.description}"
        self._severity = detect_severity(combined)
        logging.info(f"{self.id}: NetworkIncident classified as {self._severity}")

    def escalate(self):
        """Page the on-call network team."""
        msg = (
            f"[ESCALATE] On-call network team paged for incident {self.id}: "
            f"{self.title} (severity={self._severity}, host={self.affected_host})"
        )
        logging.warning(msg)
        print(msg)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"affected_host": self.affected_host, "protocol": self.protocol})
        return d


# ══════════════════════════════════════════════════════════════════════════════
# Subclass 2 — AppIncident
# ══════════════════════════════════════════════════════════════════════════════
class AppIncident(Incident):
    """Incident related to application errors."""

    def __init__(self, id, title, description, reported_by,
                 timestamp, assigned_team, app_name="", error_code=""):
        super().__init__(id, title, description, reported_by, timestamp, assigned_team)
        self.app_name   = app_name
        self.error_code = error_code

    def classify(self):
        """Detect severity using combined title + description text."""
        combined = f"{self.title} {self.description}"
        self._severity = detect_severity(combined)
        logging.info(f"{self.id}: AppIncident classified as {self._severity}")

    def get_stack_trace(self) -> str:
        """Return a log snippet / stack trace extracted from the description."""
        lines = self.description.split("\n")
        # Return lines that look like stack-trace lines or the full description if short
        trace_lines = [l for l in lines if "at " in l.lower() or "exception" in l.lower()
                       or "error" in l.lower() or "traceback" in l.lower()]
        snippet = "\n".join(trace_lines) if trace_lines else self.description[:300]
        return f"[Stack Trace for {self.id}]\n{snippet}"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"app_name": self.app_name, "error_code": self.error_code})
        return d


# ══════════════════════════════════════════════════════════════════════════════
# Subclass 3 — SecurityIncident
# ══════════════════════════════════════════════════════════════════════════════
class SecurityIncident(Incident):
    """Incident related to security threats."""

    def __init__(self, id, title, description, reported_by,
                 timestamp, assigned_team, threat_type="", source_ip=""):
        super().__init__(id, title, description, reported_by, timestamp, assigned_team)
        self.threat_type = threat_type
        self.source_ip   = source_ip

    def classify(self):
        """Detect severity using combined title + description text."""
        combined = f"{self.title} {self.description}"
        self._severity = detect_severity(combined)
        logging.info(f"{self.id}: SecurityIncident classified as {self._severity}")

    def notify_soc(self):
        """Send SOC alert for this security incident."""
        msg = (
            f"[SOC ALERT] Security incident {self.id} requires immediate attention! "
            f"Threat: {self.threat_type} | Source IP: {self.source_ip} | "
            f"Severity: {self._severity} | Title: {self.title}"
        )
        logging.critical(msg)
        print(msg)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"threat_type": self.threat_type, "source_ip": self.source_ip})
        return d


# ══════════════════════════════════════════════════════════════════════════════
# IncidentIterator
# ══════════════════════════════════════════════════════════════════════════════
class IncidentIterator:
    """
    Implements the iterator protocol (__iter__ and __next__) to step through
    a list of incidents one at a time.
    Supports optional severity filtering.
    """

    def __init__(self, incidents: list, severity_filter: str = None):
        """
        :param incidents:       List of Incident objects.
        :param severity_filter: If provided, only incidents with this severity are yielded.
                                E.g. 'critical', 'high', 'medium', 'low'.
        """
        if severity_filter:
            self._incidents = [i for i in incidents if i.severity == severity_filter]
        else:
            self._incidents = list(incidents)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._incidents):
            raise StopIteration
        incident = self._incidents[self._index]
        self._index += 1
        return incident


# ══════════════════════════════════════════════════════════════════════════════
# Batch generator
# ══════════════════════════════════════════════════════════════════════════════
def batch_incidents(incidents: list, batch_size: int = 3):
    """Yield incidents in batches of batch_size.

    Using a generator expression here (via range + slice) avoids materialising
    the full list of batches in memory — useful when incident counts are large.
    """
    # Generator expression: each element is a slice (batch) produced on demand
    return (incidents[i: i + batch_size] for i in range(0, len(incidents), batch_size))
