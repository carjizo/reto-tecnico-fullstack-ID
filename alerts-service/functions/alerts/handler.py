import hmac
import json
import logging
import os
from typing import Any

from config import get_api_key
from entities import to_item
from errors import ValidationError
from repository import DynamoAlertRepository
from service import AlertService
from validation import parse_severity_filter

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALERTS_RESOURCE = "/api/v1/orders/{orderId}/alerts"


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Punto de entrada de AWS Lambda. Solo arma las dependencias y delega."""
    try:
        api_key = get_api_key()
    except Exception:
        logger.exception(json.dumps({"event": "api_key_unavailable"}))
        return _response(500, {"error": "Error interno del servidor"})

    service = AlertService(DynamoAlertRepository(os.environ["TABLE_NAME"]))
    return handle_request(event, service, api_key)


def handle_request(event: dict[str, Any], service: AlertService, expected_api_key: str) -> dict[str, Any]:
    """Traduce el evento HTTP a llamadas del servicio y convierte errores en respuestas."""
    request_id = (event.get("requestContext") or {}).get("requestId", "local")
    try:
        response = _route(event, service, expected_api_key)
    except ValidationError as error:
        response = _response(400, {"error": str(error)})
    except Exception:
        logger.exception(json.dumps({"correlationId": request_id, "event": "unhandled_error"}))
        response = _response(500, {"error": "Error interno del servidor"})

    logger.info(json.dumps({
        "correlationId": request_id,
        "method": event.get("httpMethod"),
        "status": response["statusCode"],
    }))
    return response


def _route(event: dict[str, Any], service: AlertService, expected_api_key: str) -> dict[str, Any]:
    if not _is_authorized(event, expected_api_key):
        return _response(401, {"error": "API key inválida o ausente"})

    if event.get("resource") != ALERTS_RESOURCE:
        return _response(404, {"error": "Ruta no encontrada"})

    order_id = (event.get("pathParameters") or {}).get("orderId", "")
    method = event.get("httpMethod")
    if method == "POST":
        return _create_alert(order_id, event, service)
    if method == "GET":
        return _list_alerts(order_id, event, service)
    return _response(405, {"error": "Método no permitido"})


def _create_alert(order_id: str, event: dict[str, Any], service: AlertService) -> dict[str, Any]:
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValidationError("El body debe ser JSON válido") from None
    if not isinstance(payload, dict):
        raise ValidationError("El body debe ser un objeto JSON")

    alert = service.create_alert(order_id, payload)
    return _response(201, to_item(alert))


def _list_alerts(order_id: str, event: dict[str, Any], service: AlertService) -> dict[str, Any]:
    query = event.get("queryStringParameters") or {}
    severity = parse_severity_filter(query.get("severity"))
    alerts = service.list_alerts(order_id, severity)
    return _response(200, [to_item(alert) for alert in alerts])


def _is_authorized(event: dict[str, Any], expected_api_key: str) -> bool:
    headers = {name.lower(): value for name, value in (event.get("headers") or {}).items()}
    received = headers.get("x-api-key", "")
    return hmac.compare_digest(received.encode(), expected_api_key.encode())


def _response(status_code: int, body: Any) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
