# config.py — API credentials and MOCK_API flag

# Never hardcode real credentials in source files; use environment variables in production.

import os

# ── Mock mode ──────────────────────────────────────────────────────────────────
MOCK_API = True   # Set to False and fill real credentials below for live calls

# ── ServiceNow ────────────────────────────────────────────────────────────────
SNOW_INSTANCE   = os.environ.get("SNOW_INSTANCE",  "dev12345")
SNOW_USERNAME   = os.environ.get("SNOW_USERNAME",  "admin")
SNOW_PASSWORD   = os.environ.get("SNOW_PASSWORD",  "password")
SNOW_BASE_URL   = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"

# ── Jira ──────────────────────────────────────────────────────────────────────
JIRA_DOMAIN      = os.environ.get("JIRA_DOMAIN",     "mycompany")
JIRA_EMAIL       = os.environ.get("JIRA_EMAIL",      "user@example.com")
JIRA_API_TOKEN   = os.environ.get("JIRA_API_TOKEN",  "jira_api_token_here")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY","IT")
JIRA_BASE_URL    = f"https://{JIRA_DOMAIN}.atlassian.net/rest/api/3/issue"

# ── Azure Boards ──────────────────────────────────────────────────────────────
AZURE_ORG       = os.environ.get("AZURE_ORG",     "myorg")
AZURE_PROJECT   = os.environ.get("AZURE_PROJECT", "IncidentTracker")
AZURE_PAT       = os.environ.get("AZURE_PAT",     "azure_pat_here")
AZURE_BASE_URL  = (
    f"https://dev.azure.com/{AZURE_ORG}/{AZURE_PROJECT}"
    "/_apis/wit/workitems/$Bug?api-version=7.1"
)