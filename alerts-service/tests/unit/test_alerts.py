import json
import re
from typing import Any

from handler import ALERTS_RESOURCE, handle_request
from models import Alert, Severity
from repository import InMemoryAlertRepository
from service import AlertService

API_KEY = "clave-de-prueba-1234567890"
ORDER_ID = "ORD-1001"
ALERT_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z#[0-9a-f-]{36}$")


class FailingRepository:
    """Simula una falla de la capa de datos (por ejemplo, DynamoDB caído)."""

    def save(self, alert: Alert) -> None:
        raise RuntimeError("DynamoDB no disponible")

    def find_by_order(self, order_id: str, severity: Severity | None) -> list[Alert]:
        raise RuntimeError("DynamoDB no disponible")


def make_event(
    method: str,
    body: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
    api_key: str | None = API_KEY,
    order_id: str = ORDER_ID,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["X-Api-Key"] = api_key
    return {
        "httpMethod": method,
        "resource": ALERTS_RESOURCE,
        "pathParameters": {"orderId": order_id},
        "queryStringParameters": query,
        "headers": headers,
        "body": json.dumps(body) if body is not None else None,
        "requestContext": {"requestId": "test-request-1"},
    }


def valid_body(severity: str = "HIGH") -> dict[str, str]:
    return {"severity": severity, "message": "Latencia alta en el pago", "source": "monitoring"}


def test_crear_alerta_devuelve_201_con_id_ordenable():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("POST", valid_body()), service, API_KEY)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["orderId"] == ORDER_ID
    assert body["severity"] == "HIGH"
    assert ALERT_ID_PATTERN.match(body["alertId"])


def test_datos_invalidos_devuelven_400_y_no_guardan_nada():
    repository = InMemoryAlertRepository()
    service = AlertService(repository)

    response = handle_request(make_event("POST", valid_body(severity="CRITICAL")), service, API_KEY)

    assert response["statusCode"] == 400
    assert "severity debe ser LOW, MEDIUM o HIGH" in json.loads(response["body"])["error"]
    assert repository.find_by_order(ORDER_ID, None) == []


def test_fallo_de_datos_devuelve_500_sin_detalles_internos():
    service = AlertService(FailingRepository())

    response = handle_request(make_event("POST", valid_body()), service, API_KEY)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body == {"error": "Error interno del servidor"}
    assert "DynamoDB" not in response["body"]


def test_listar_con_filtro_severity_devuelve_solo_esa_severidad():
    service = AlertService(InMemoryAlertRepository())
    handle_request(make_event("POST", valid_body("HIGH")), service, API_KEY)
    handle_request(make_event("POST", valid_body("LOW")), service, API_KEY)

    response = handle_request(make_event("GET", query={"severity": "HIGH"}), service, API_KEY)

    assert response["statusCode"] == 200
    alerts = json.loads(response["body"])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"


def test_listar_sin_alertas_devuelve_200_con_lista_vacia():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("GET"), service, API_KEY)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == []


def test_filtro_severity_invalido_devuelve_400():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("GET", query={"severity": "URGENT"}), service, API_KEY)

    assert response["statusCode"] == 400


def test_sin_api_key_devuelve_401():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("GET", api_key=None), service, API_KEY)

    assert response["statusCode"] == 401


def test_api_key_incorrecta_devuelve_401():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("GET", api_key="otra-clave"), service, API_KEY)

    assert response["statusCode"] == 401


def test_preflight_options_responde_204_sin_api_key():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("OPTIONS", api_key=None), service, API_KEY)

    assert response["statusCode"] == 204
    assert response["body"] == ""
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "X-Api-Key" in response["headers"]["Access-Control-Allow-Headers"]


def test_respuestas_incluyen_cabeceras_cors():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("POST", valid_body()), service, API_KEY)

    assert response["headers"]["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"


def test_severity_en_minusculas_devuelve_400():
    service = AlertService(InMemoryAlertRepository())

    response = handle_request(make_event("POST", valid_body("high")), service, API_KEY)

    assert response["statusCode"] == 400
