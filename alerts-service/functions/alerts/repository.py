from typing import Protocol

import boto3
from boto3.dynamodb.conditions import Attr, Key

from entities import PARTITION_KEY, SEVERITY, from_item, to_item
from models import Alert, Severity


class AlertRepository(Protocol):
    """Contrato de persistencia. El servicio depende de esto, no de DynamoDB."""

    def save(self, alert: Alert) -> None: ...

    def find_by_order(self, order_id: str, severity: Severity | None) -> list[Alert]: ...


class InMemoryAlertRepository:
    """Implementación en memoria para pruebas unitarias."""

    def __init__(self) -> None:
        self._alerts: list[Alert] = []

    def save(self, alert: Alert) -> None:
        self._alerts.append(alert)

    def find_by_order(self, order_id: str, severity: Severity | None) -> list[Alert]:
        found = [alert for alert in self._alerts if alert.order_id == order_id]
        if severity is not None:
            found = [alert for alert in found if alert.severity == severity]
        return sorted(found, key=lambda alert: alert.alert_id)


class DynamoAlertRepository:
    """Implementación real sobre DynamoDB.

    Mejora posible (no implementada): paginar la consulta con LastEvaluatedKey,
    porque DynamoDB devuelve como máximo 1 MB por página.
    """

    def __init__(self, table_name: str) -> None:
        self._table = boto3.resource("dynamodb").Table(table_name)

    def save(self, alert: Alert) -> None:
        # Falla si ya existe una alerta con la misma clave: nunca sobrescribe.
        self._table.put_item(
            Item=to_item(alert),
            ConditionExpression="attribute_not_exists(alertId)",
        )

    def find_by_order(self, order_id: str, severity: Severity | None) -> list[Alert]:
        query_args = {
            "KeyConditionExpression": Key(PARTITION_KEY).eq(order_id),
            "ScanIndexForward": True,
        }
        if severity is not None:
            query_args["FilterExpression"] = Attr(SEVERITY).eq(severity.value)
        response = self._table.query(**query_args)
        return [from_item(item) for item in response.get("Items", [])]
