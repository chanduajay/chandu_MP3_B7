# services/jira.py
import base64
import json
import logging
import config
from utils.decorators import log_call, retry

_PRIORITY_MAP = {"critical": "Highest", "high": "High", "medium": "Medium", "low": "Low"}

def _auth_header() -> str:
    token = base64.b64encode(
        f"{config.JIRA_EMAIL}:{config.JIRA_API_TOKEN}".encode()
    ).decode()
    return f"Basic {token}"

@log_call
@retry(times=3, delay=1)
def create_issue(incident) -> str:
    payload = {
        "fields": {
            "summary": incident.title,
            "description": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph",
                             "content": [{"type": "text", "text": incident.description}]}],
            },
            "issuetype": {"name": "Bug"},
            "priority":  {"name": _PRIORITY_MAP.get(incident.severity, "Medium")},
            "project":   {"key": config.JIRA_PROJECT_KEY},
            "labels":    [type(incident).__name__.lower(), incident.severity],
        }
    }
    use_mock = getattr(config, 'MOCK_JIRA', config.MOCK_API)
    if use_mock:
        print(f"\n[Jira MOCK] {incident.id} -> payload sent (mock)")
        ticket_id = f"PROJ-{incident.id.replace('INC','')}"
        incident.ticket_ids["jira"] = ticket_id
        logging.info(f"[Jira MOCK] {ticket_id}")
        return ticket_id
    import requests
    response = requests.post(
        config.JIRA_BASE_URL,
        headers={"Authorization": _auth_header(),
                 "Content-Type": "application/json",
                 "Accept": "application/json"},
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    key = response.json()["key"]
    incident.ticket_ids["jira"] = key
    logging.info(f"[Jira LIVE] Issue: {key} for {incident.id}")
    return key

@log_call
@retry(times=3, delay=1)
def update_issue(key: str, priority: str = "Medium") -> bool:
    use_mock = getattr(config, 'MOCK_JIRA', config.MOCK_API)
    if use_mock:
        print(f"[Jira MOCK] PUT {key} -> priority={priority}")
        return True
    import requests
    url = f"{config.JIRA_BASE_URL}/{key}"
    response = requests.put(
        url,
        headers={"Authorization": _auth_header(), "Content-Type": "application/json"},
        json={"fields": {"priority": {"name": priority}}},
        timeout=15,
    )
    response.raise_for_status()
    return True
