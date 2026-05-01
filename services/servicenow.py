# services/servicenow.py
import json
import logging
import config
from utils.decorators import log_call, retry

_URGENCY_MAP = {"critical": 1, "high": 1, "medium": 2, "low": 3}

@log_call
@retry(times=3, delay=1)
def create_ticket(incident) -> str:
    payload = {
        "short_description": incident.title,
        "description":       incident.description,
        "urgency":           str(_URGENCY_MAP.get(incident.severity, 3)),
        "category":          _resolve_category(incident),
        "assignment_group":  incident.assigned_team,
        "caller_id":         incident.reported_by,
    }
    use_mock = getattr(config, 'MOCK_SNOW', config.MOCK_API)
    if use_mock:
        print(f"\n[ServiceNow MOCK] {incident.id} -> payload sent (mock)")
        ticket_id = f"MOCK-SNOW-{incident.id}"
        incident.ticket_ids["snow"] = ticket_id
        logging.info(f"[ServiceNow MOCK] {ticket_id}")
        return ticket_id
    import requests
    response = requests.post(
        config.SNOW_BASE_URL,
        auth=(config.SNOW_USERNAME, config.SNOW_PASSWORD),
        json=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    sys_id = response.json()["result"]["sys_id"]
    incident.ticket_ids["snow"] = sys_id
    logging.info(f"[ServiceNow LIVE] Ticket: {sys_id} for {incident.id}")
    return sys_id

@log_call
@retry(times=3, delay=1)
def update_ticket_status(sys_id: str, state: str = "2") -> bool:
    use_mock = getattr(config, 'MOCK_SNOW', config.MOCK_API)
    if use_mock:
        print(f"[ServiceNow MOCK] PATCH {sys_id} -> state={state}")
        return True
    import requests
    url = f"{config.SNOW_BASE_URL}/{sys_id}"
    response = requests.patch(
        url,
        auth=(config.SNOW_USERNAME, config.SNOW_PASSWORD),
        json={"state": state},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return True

def _resolve_category(incident) -> str:
    return {"NetworkIncident": "Network", "AppIncident": "Software",
            "SecurityIncident": "Security"}.get(type(incident).__name__, "General")
