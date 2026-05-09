#!/usr/bin/env python3
# main.py
"""
IT Incident Auto-Triage & Tracker — CLI entry point.

Usage
-----
    python main.py                        # process all incidents (mock mode)
    python main.py --severity critical    # process only critical incidents
    python main.py --help                 # show usage

Pipeline
--------
1. Load incidents.json and validate schema
2. Detect type + build typed Incident objects
3. classify() each incident (sets _severity)
4. (optional) filter by --severity flag
5. Push to ServiceNow, Jira, Azure Boards in batches of 3
6. Generate report.html and report.json
"""

import argparse
import json
import logging
import os
import sys

# ── Allow imports from project root ───────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

import config
from models.incident      import (Incident, NetworkIncident, AppIncident,
                                  SecurityIncident, IncidentIterator,
                                  batch_incidents)
from models.report        import ReportGenerator
from services             import servicenow, jira, azure_boards
from utils.classifier     import detect_type
from utils.helpers        import (get_critical_incidents, count_by_severity,
                                  count_by_type, count_by_team)


# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 — Load incidents.json
# ══════════════════════════════════════════════════════════════════════════════
def load_incidents(path: str) -> list:
    """Load JSON records, validate schema, detect type, and return typed Incident objects."""
    with open(path, "r", encoding="utf-8") as fh:
        records = json.load(fh)

    incidents = []
    for rec in records:
        # Validate schema (raises ValueError on missing fields)
        Incident.validate_schema(rec)

        # Detect incident type from title + description
        combined = f"{rec['title']} {rec['description']}"
        inc_type = detect_type(combined)

        # Build the correct subclass
        if inc_type == "network":
            obj = NetworkIncident(**rec)
        elif inc_type == "security":
            obj = SecurityIncident(**rec)
        elif inc_type == "app":
            obj = AppIncident(**rec)
        else:
            # Fallback: use base class fields with AppIncident as default typed obj
            obj = AppIncident(**rec)

        incidents.append(obj)

    logger.info(f"Loaded {len(incidents)} incidents from {path}")
    return incidents


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 — Classify all incidents
# ══════════════════════════════════════════════════════════════════════════════
def classify_all(incidents: list) -> None:
    """Call classify() on every incident to set its _severity."""
    for inc in incidents:
        inc.classify()
    logger.info("All incidents classified.")


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 — Push tickets in batches
# ══════════════════════════════════════════════════════════════════════════════
def push_tickets(incidents: list) -> None:
    """
    Iterate incidents in batches of 3 and create tickets on all three platforms.
    Uses IncidentIterator internally to traverse each batch.
    """
    total = len(incidents)
    logger.info(f"Pushing {total} incidents to ServiceNow / Jira / Azure Boards …")

    for batch_num, batch in enumerate(batch_incidents(incidents, batch_size=3), start=1):
        logger.info(f"  Processing batch {batch_num} ({len(batch)} incidents) …")

        # Use IncidentIterator to walk through this batch
        for inc in IncidentIterator(batch):
            logger.info(f"    → {inc.id}: {inc.title[:60]}")

            # ServiceNow
            servicenow.create_ticket(inc)

            # Jira
            jira.create_issue(inc)

            # Azure Boards
            azure_boards.create_work_item(inc)

    logger.info("All ticket pushes complete.")


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 — Print console summary
# ══════════════════════════════════════════════════════════════════════════════
def print_summary(incidents: list) -> None:
    """Print a concise summary table to stdout."""
    print("\n" + "═" * 80)
    print("  IT INCIDENT AUTO-TRIAGE SUMMARY")
    print("═" * 80)
    print(f"  Total incidents processed : {len(incidents)}")

    sev = count_by_severity(incidents)
    typ = count_by_type(incidents)
    team = count_by_team(incidents)

    print(f"\n  By Severity:")
    for s in ["critical", "high", "medium", "low"]:
        bar = "█" * sev.get(s, 0)
        print(f"    {s.capitalize():<10} {sev.get(s, 0):>3}  {bar}")

    print(f"\n  By Type:")
    for t, c in typ.items():
        print(f"    {t:<25} {c}")

    print(f"\n  By Team:")
    for team_name, c in team.items():
        print(f"    {team_name:<25} {c}")

    print("\n  Critical incidents:")
    for inc in get_critical_incidents(incidents):
        print(f"    ⚠  [{inc.id}] {inc.title}")

    print("═" * 80 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # ── CLI argument parsing ──────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="IT Incident Auto-Triage & Tracker",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        default=None,
        help=(
            "Filter which incidents get pushed to ticketing platforms.\n"
            "E.g. --severity critical  pushes only critical incidents."
        ),
    )
    args = parser.parse_args()

    # ── Paths ──────────────────────────────────────────────────────────────────
    base_dir   = os.path.dirname(__file__)
    data_path  = os.path.join(base_dir, "data", "incidents.json")

    print("\n" + "─" * 60)
    print("  IT Incident Auto-Triage & Tracker")
    print(f"  Mode : {'MOCK' if config.MOCK_API else 'LIVE'}")
    if args.severity:
        print(f"  Filter: severity = {args.severity}")
    print("─" * 60 + "\n")

    # ── Pipeline ───────────────────────────────────────────────────────────────
    # 1. Load + schema-validate + build typed objects
    all_incidents = load_incidents(data_path)

    # 2. Classify (sets _severity on each incident)
    classify_all(all_incidents)

    # 3. Optionally filter by --severity flag (stretch goal)
    if args.severity:
        filtered = [i for i in all_incidents if i.severity == args.severity]
        logger.info(
            f"Severity filter '{args.severity}': "
            f"{len(filtered)}/{len(all_incidents)} incidents selected."
        )
    else:
        filtered = all_incidents

    if not filtered:
        print(f"No incidents match severity filter '{args.severity}'. Nothing to push.")
        return

    # 4. Push tickets in batches of 3
    push_tickets(filtered)

    # 5. Generate report AFTER all API calls complete (collect ticket IDs first)
    reporter = ReportGenerator(filtered)   # report always covers all incidents
    html_path = reporter.generate_html()
    json_path = reporter.export_json()

    # 6. Console summary
    print_summary(all_incidents)

    print(f"  ✅  Report saved: {html_path}")
    print(f"  ✅  JSON saved  : {json_path}\n")


if __name__ == "__main__":
    main()
