# models/report.py
"""
ReportGenerator — produces a styled HTML report and a JSON summary.
Style matches the reference image: light background, white cards, colored severity badges,
dark header, ticket chips per row.
"""

import json
import os
from datetime import datetime, timezone

from utils.helpers import count_by_severity, count_by_team, count_by_type


_SEVERITY_COLOR = {
    "critical": "#e53e3e",
    "high":     "#ed8936",
    "medium":   "#ecc94b",
    "low":      "#48bb78",
}

_TYPE_ICON = {
    "NetworkIncident":  "network",
    "AppIncident":      "app",
    "SecurityIncident": "security",
}


class ReportGenerator:
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

    def __init__(self, incidents: list):
        self.incidents    = incidents
        self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def generate_html(self) -> str:
        path = os.path.join(self.OUTPUT_DIR, "report.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._build_html())
        print(f"\n[Report] HTML report written to: {path}")
        return path

    def export_json(self) -> str:
        path = os.path.join(self.OUTPUT_DIR, "report.json")
        summary = {
            "generated_at":    self.generated_at,
            "total_incidents": len(self.incidents),
            "by_severity":     count_by_severity(self.incidents),
            "by_type":         count_by_type(self.incidents),
            "by_team":         count_by_team(self.incidents),
            "incidents":       [i.to_dict() for i in self.incidents],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, default=str)
        print(f"[Report] JSON report written to: {path}")
        return path

    def _build_html(self) -> str:
        by_sev  = count_by_severity(self.incidents)
        by_type = count_by_type(self.incidents)
        by_team = count_by_team(self.incidents)

        total          = len(self.incidents)
        critical_count = by_sev.get("critical", 0)
        high_count     = by_sev.get("high", 0)
        security_count = by_type.get("SecurityIncident", 0)

        # ── Summary cards ──────────────────────────────────────────────────────
        cards_html = f"""
        <div class="card"><div class="num">{total}</div><div class="lbl">Total incidents</div></div>
        <div class="card"><div class="num" style="color:#e53e3e">{critical_count}</div><div class="lbl">Critical</div></div>
        <div class="card"><div class="num" style="color:#ed8936">{high_count}</div><div class="lbl">High</div></div>
        <div class="card"><div class="num" style="color:#4299e1">{security_count}</div><div class="lbl">Security threats</div></div>
        """

        # ── Breakdown badges ───────────────────────────────────────────────────
        type_badge_colors = {
            "AppIncident":      "#e9d8fd",
            "SecurityIncident": "#fed7d7",
            "NetworkIncident":  "#bee3f8",
        }
        type_text_colors = {
            "AppIncident":      "#6b46c1",
            "SecurityIncident": "#c53030",
            "NetworkIncident":  "#2b6cb0",
        }
        type_tags = "".join(
            f'<span class="breakdown-badge" style="background:{type_badge_colors.get(t,"#e2e8f0")};color:{type_text_colors.get(t,"#2d3748")}">'
            f'{_TYPE_ICON.get(t, t.replace("Incident","").lower())}: {c}</span>'
            for t, c in by_type.items()
        )

        sev_badge_colors = {
            "critical": "#fed7d7", "high": "#feebc8",
            "medium":   "#fefcbf", "low":  "#c6f6d5",
        }
        sev_text_colors = {
            "critical": "#c53030", "high": "#c05621",
            "medium":   "#b7791f", "low":  "#276749",
        }
        sev_order = ["critical", "high", "medium", "low"]
        sev_tags = "".join(
            f'<span class="breakdown-badge" style="background:{sev_badge_colors.get(s,"#e2e8f0")};color:{sev_text_colors.get(s,"#2d3748")}">'
            f'{s}: {by_sev.get(s,0)}</span>'
            for s in sev_order if by_sev.get(s, 0) > 0
        )

        team_badge_colors = ["#bee3f8","#c6f6d5","#e9d8fd","#feebc8","#fed7d7"]
        team_text_colors  = ["#2b6cb0","#276749","#6b46c1","#c05621","#c53030"]
        team_tags = "".join(
            f'<span class="breakdown-badge" style="background:{team_badge_colors[i%5]};color:{team_text_colors[i%5]}">'
            f'{tm}: {c}</span>'
            for i,(tm,c) in enumerate(by_team.items())
        )

        # ── Table rows ─────────────────────────────────────────────────────────
        rows_html = ""
        for inc in sorted(self.incidents):
            sev_color    = _SEVERITY_COLOR.get(inc.severity, "#718096")
            type_name    = _TYPE_ICON.get(type(inc).__name__, type(inc).__name__.replace("Incident","").lower())
            ts           = inc.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            snow_id      = inc.ticket_ids.get("snow",  "—")
            jira_id      = inc.ticket_ids.get("jira",  "—")
            azure_id     = inc.ticket_ids.get("azure", "—")
            team_display = inc.assigned_team.lower().replace(" team","").replace(" ","")

            rows_html += f"""
            <tr>
              <td class="col-id">{inc.id}</td>
              <td class="col-title">{inc.title}</td>
              <td class="col-sev">
                <span class="sev-pill" style="background:{sev_color}">
                  {inc.severity.upper()}
                </span>
              </td>
              <td class="col-type">{type_name}</td>
              <td class="col-team">{team_display}</td>
              <td class="col-ts">{ts}</td>
              <td class="col-tickets">
                <span class="chip chip-snow">SNOW: {snow_id}</span>
                <span class="chip chip-jira">JIRA: {jira_id}</span>
                <span class="chip chip-azure">AZURE: {azure_id}</span>
              </td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>IT Incident Auto-Triage Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin:0; padding:0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f7fafc;
    color: #2d3748;
    font-size: 14px;
  }}

  /* ── Header ── */
  header {{
    background: #1a202c;
    color: #fff;
    padding: 16px 32px;
    display: flex;
    align-items: baseline;
    gap: 12px;
  }}
  header h1 {{ font-size: 1.1rem; font-weight: 700; }}
  header .sub {{ font-size: .78rem; color: #a0aec0; margin-top: 2px; }}

  /* ── Page body ── */
  .page {{ max-width: 1400px; margin: 0 auto; padding: 28px 32px; }}

  /* ── Section label ── */
  .section-lbl {{
    font-size: .72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #718096;
    margin-bottom: 10px;
    margin-top: 24px;
  }}

  /* ── Summary cards ── */
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }}
  .card {{
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 18px 28px;
    min-width: 120px;
    text-align: center;
  }}
  .card .num  {{ font-size: 2rem; font-weight: 800; color: #4299e1; line-height:1; }}
  .card .lbl  {{ font-size: .72rem; color: #718096; margin-top: 6px; }}

  /* ── Breakdown badges ── */
  .breakdown-badge {{
    display: inline-block;
    padding: 3px 11px;
    border-radius: 20px;
    font-size: .73rem;
    font-weight: 600;
    margin: 3px 4px 3px 0;
  }}

  /* ── Incident table ── */
  .table-wrap {{
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
    margin-top: 12px;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead tr {{
    background: #2d3748;
    color: #e2e8f0;
  }}
  th {{
    padding: 11px 14px;
    text-align: left;
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .8px;
    white-space: nowrap;
  }}
  td {{
    padding: 10px 14px;
    border-bottom: 1px solid #edf2f7;
    vertical-align: middle;
  }}
  tbody tr:last-child td {{ border-bottom: none; }}
  tbody tr:hover {{ background: #f7fafc; }}

  .col-id    {{ font-weight: 700; color: #4a5568; font-size:.78rem; white-space:nowrap; }}
  .col-title {{ min-width: 240px; }}
  .col-type,
  .col-team  {{ color: #718096; white-space:nowrap; }}
  .col-ts    {{ color: #a0aec0; font-size:.75rem; white-space:nowrap; }}

  /* ── Severity pill ── */
  .sev-pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    color: #fff;
    font-size: .68rem;
    font-weight: 800;
    letter-spacing: .6px;
    white-space: nowrap;
  }}

  /* ── Ticket chips ── */
  .col-tickets {{ white-space: nowrap; }}
  .chip {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: .65rem;
    font-weight: 600;
    margin-right: 5px;
  }}
  .chip-snow  {{ background:#ebf8ff; color:#2b6cb0; }}
  .chip-jira  {{ background:#e9d8fd; color:#6b46c1; }}
  .chip-azure {{ background:#e6fffa; color:#234e52; }}

  /* ── Footer ── */
  footer {{
    text-align: center;
    font-size: .72rem;
    color: #a0aec0;
    padding: 28px 0 16px;
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>IT Incident Auto-Triage Report</h1>
    <div class="sub">Generated: {self.generated_at} &nbsp;|&nbsp; Total incidents: {total}</div>
  </div>
</header>

<div class="page">

  <div class="section-lbl">Summary</div>
  <div class="cards">{cards_html}</div>

  <div class="section-lbl">Breakdown by Type</div>
  <div>{type_tags}</div>

  <div class="section-lbl">Breakdown by Severity</div>
  <div>{sev_tags}</div>

  <div class="section-lbl">Breakdown by Team</div>
  <div>{team_tags}</div>

  <div class="section-lbl">Incident Detail</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Severity</th>
          <th>Type</th>
          <th>Team</th>
          <th>Timestamp</th>
          <th>Tickets</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>

</div>

<footer>IT Incident Auto-Triage &amp; Tracker — Mini Project 3</footer>
</body>
</html>"""
