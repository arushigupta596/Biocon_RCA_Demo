"""Audit trail: tamper-evident record locking and JSON export (21 CFR Part 11 / Annex 11)."""

import hashlib
import json
from datetime import datetime, timezone


def lock_record(
    incident_id: str,
    site: str,
    product: str,
    model: str,
    rca_text: str,
    capa_text: str,
    user: str = "demo",
) -> dict:
    """
    Build a locked audit record with a SHA-256 integrity hash.

    The hash is computed over the canonical JSON of the record (sort_keys=True)
    BEFORE the sha256 and locked fields are added — so it covers all content fields.
    """
    record = {
        "incident_id":   incident_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "site":          site,
        "product":       product,
        "model":         model,
        "user":          user,
        "rca_output":    rca_text,
        "capa_output":   capa_text,
    }
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
    record["sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    record["locked"] = True
    return record


def export_json(record: dict) -> bytes:
    """Return the locked record as indented UTF-8 JSON bytes for download."""
    return json.dumps(record, indent=2, ensure_ascii=False).encode("utf-8")
