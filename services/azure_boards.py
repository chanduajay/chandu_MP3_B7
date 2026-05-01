# services/azure_boards.py
import base64
import json
import logging
import config
from utils.decorators import log_call, retry

_PRIORITY_MAP = {"critical": 1, "high": 2, "medium": 3, "low": 4}

def _auth_header() -> str:
    token = base64.b64encode(f":{config.AZURE_PAT}".encode()).decode()
    return f"Basic {token}"

@log_call
@retry(times=3, delay=1)
def create_work_item(incident) -> str:
    payload = [
        {"op": "add", "path": "/fields/System.Title",      "value": incident.title},
        {"op": "add", "path": "/fields/System.Description","value": incident.description},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority",
                              "value": _PRIORITY_MAP.get(incident.severity, 3)},
        {"op": "add", "path": "/fields/System.AssignedTo", "value": incident.assigned_team},
        {"op": "add", "path": "/fields/System.Tags",
                              "value": f"{type(incident).__name__}; {incident.severity}"},
    ]
    use_mock = getattr(config, 'MOCK_AZURE', config.MOCK_API)
    if use_mock:
        print(f"\n[Azure MOCK] {incident.id} -> payload sent (mock)")
        ticket_id = f"AZURE-{incident.id.replace('INC','')}"
        incident.ticket_ids["azure"] = ticket_id
        logging.info(f"[Azure MOCK] {ticket_id}")
        return ticket_id
    import requests
    response = requests.post(
        config.AZURE_BASE_URL,
        headers={"Authorization": _auth_header(),
                 "Content-Type": "application/json-patch+json",
                 "Accept": "application/json"},
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    work_item_id = str(response.json()["id"])
    incident.ticket_ids["azure"] = work_item_id
    logging.info(f"[Azure LIVE] Work item: {work_item_id} for {incident.id}")
    return work_item_id
