from typing import Any

from models import Alert, Severity

# Nombres de atributos tal como están en la tabla DynamoDB.
# La API usa el mismo formato, así que to_item también sirve para la respuesta HTTP.
PARTITION_KEY = "orderId"
SORT_KEY = "alertId"
SEVERITY = "severity"


def to_item(alert: Alert) -> dict[str, Any]:
    return {
        PARTITION_KEY: alert.order_id,
        SORT_KEY: alert.alert_id,
        SEVERITY: alert.severity.value,
        "message": alert.message,
        "source": alert.source,
        "createdAt": alert.created_at,
    }


def from_item(item: dict[str, Any]) -> Alert:
    return Alert(
        order_id=item[PARTITION_KEY],
        alert_id=item[SORT_KEY],
        severity=Severity(item[SEVERITY]),
        message=item["message"],
        source=item["source"],
        created_at=item["createdAt"],
    )
