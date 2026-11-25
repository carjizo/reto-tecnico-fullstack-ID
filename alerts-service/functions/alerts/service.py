import uuid
from datetime import datetime, timezone
from typing import Any

from models import Alert, Severity
from repository import AlertRepository
from validation import validate_create_payload, validate_order_id


class AlertService:
    """Reglas de negocio de alertas. No sabe nada de HTTP ni de DynamoDB."""

    def __init__(self, repository: AlertRepository) -> None:
        self._repository = repository

    def create_alert(self, order_id: str, payload: dict[str, Any]) -> Alert:
        order_id = validate_order_id(order_id)
        severity, message, source = validate_create_payload(payload)

        created_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        alert = Alert(
            order_id=order_id,
            alert_id=f"{created_at}#{uuid.uuid4()}",
            severity=severity,
            message=message,
            source=source,
            created_at=created_at,
        )
        self._repository.save(alert)
        return alert

    def list_alerts(self, order_id: str, severity: Severity | None) -> list[Alert]:
        order_id = validate_order_id(order_id)
        return self._repository.find_by_order(order_id, severity)
