# IT Incident Auto-Triage & Tracker
### Mini Project 3 — DOTNET FSD WITH PYTHON

A Python CLI tool that automatically classifies IT incidents by type and severity using regex,
creates tickets on ServiceNow, Jira, and Azure Boards (mock or live), and generates a styled
HTML + JSON report — all with one command.

---

## Project Structure

```
incident_tracker/
├── main.py                  # CLI entry point; orchestrates the full pipeline
├── config.py                # API credentials and MOCK_API flag
├── models/
│   ├── __init__.py
│   ├── incident.py          # Incident base class + 3 subclasses + IncidentIterator + batch_incidents
│   └── report.py            # ReportGenerator — produces HTML and JSON output
├── services/
│   ├── __init__.py
│   ├── servicenow.py        # ServiceNow REST API integration
│   ├── jira.py              # Jira REST API integration
│   └── azure_boards.py      # Azure Boards REST API integration
├── utils/
│   ├── __init__.py
│   ├── classifier.py        # Regex-based type and severity detection
│   ├── decorators.py        # @log_call and @retry decorators
│   └── helpers.py           # map / filter / reduce helper functions
├── data/
│   └── incidents.json       # 12 sample incident records
└── output/
    ├── report.html          # Auto-generated report (created on run)
    └── report.json          # Auto-generated JSON summary (created on run)
```

---

## Prerequisites

- Python 3.8 or above
- No external packages required in mock mode
- For live API calls: `pip install requests`

---

## Setup

1. **Clone / unzip** the project folder.

2. **Configure** `config.py`:
   - `MOCK_API = True` (default) — runs without real API credentials.
   - `MOCK_API = False` — fill in real credentials for live ticket creation.

3. *(Optional)* Use environment variables instead of editing `config.py`:
   ```bash
   export SNOW_INSTANCE=dev12345
   export SNOW_USERNAME=admin
   export SNOW_PASSWORD=mypassword
   export JIRA_DOMAIN=mycompany
   export JIRA_EMAIL=user@example.com
   export JIRA_API_TOKEN=mytoken
   export JIRA_PROJECT_KEY=IT
   export AZURE_ORG=myorg
   export AZURE_PROJECT=IncidentTracker
   export AZURE_PAT=mypat
   ```

---

## Running the Tool

### Process all incidents (mock mode)
```bash
cd incident_tracker
python main.py
```

### Filter by severity (stretch goal — `--severity` flag)
```bash
python main.py --severity critical    # push only critical incidents
python main.py --severity high        # push only high incidents
python main.py --severity medium
python main.py --severity low
```

### Help
```bash
python main.py --help
```

---

## Output

After a successful run:

| File | Description |
|---|---|
| `output/report.html` | Styled HTML dashboard — summary cards, breakdowns, and full incident table |
| `output/report.json` | JSON summary of all incidents including ticket IDs |

---

## Python Concepts Demonstrated

| Concept | Where used |
|---|---|
| OOP — inheritance, abstract methods | `models/incident.py` — Incident base class + 3 subclasses |
| `@property` | `Incident.severity` property |
| `__lt__`, `__str__`, `__repr__` | `Incident` dunder methods for sorting and printing |
| Static method | `Incident.validate_schema()` |
| Iterator protocol (`__iter__`, `__next__`) | `IncidentIterator` class |
| Generator function | `batch_incidents()` — yields batches using a generator expression |
| Generator expression | Used in `batch_incidents()` with a comment explaining why |
| `re` — compiled regex patterns | `utils/classifier.py` — `detect_type()` and `detect_severity()` |
| Decorators (`functools.wraps`) | `@log_call`, `@retry(times=3)` in `utils/decorators.py` |
| `map`, `filter`, `reduce` | `utils/helpers.py` — all three functional helpers |
| `lambda` | Throughout `helpers.py` |
| File I/O | `models/report.py` — writes HTML and JSON files |
| `json` module | `main.py` (load), `models/report.py` (export), service modules (payload printing) |
| `argparse` | `main.py` — `--severity` CLI flag |
| `logging` | Every module uses `logging.info` / `logging.warning` / `logging.critical` |
| `requests` library | All three service modules (live mode) |
| Exception handling | `@retry` decorator, `validate_schema()`, `load_incidents()` |
| `datetime.fromisoformat` | `Incident.__init__` — ISO 8601 timestamp parsing |
| `os.makedirs` | `ReportGenerator` — auto-creates `output/` directory |

---

## Stretch Goals Implemented

- ✅ `--severity` flag in `main.py` for filtering which incidents get pushed
- ✅ Generator expression used in `batch_incidents()` with explanatory comment
- ✅ Static method `Incident.validate_schema()` validates JSON schema before loading

---

## Common Pitfalls Addressed

- Credentials read from `config.py` / environment variables — never hardcoded
- `NotImplementedError` in base `classify()` ensures silent-failure is impossible
- `re.IGNORECASE` used on all patterns so casing does not matter
- `@retry(times=3)` wraps every API call — one bad call does not abort the batch
- Report generated **after** all API calls complete — all ticket IDs collected first
- `__lt__` maps `critical=0, high=1, medium=2, low=3` so `sorted()` orders correctly
