import re
from typing import Any

from errors import ValidationError
from models import Severity

ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_MESSAGE_LENGTH = 500
MAX_SOURCE_LENGTH = 100


def validate_order_id(order_id: str) -> str:
    if not ORDER_ID_PATTERN.match(order_id or ""):
        raise ValidationError("orderId inválido: use de 1 a 64 letras, números, '-' o '_'")
    return order_id


def validate_create_payload(payload: dict[str, Any]) -> tuple[Severity, str, str]:
    severity = parse_severity(payload.get("severity"))
    message = _required_text(payload, "message", MAX_MESSAGE_LENGTH)
    source = _required_text(payload, "source", MAX_SOURCE_LENGTH)
    return severity, message, source


def parse_severity_filter(value: str | None) -> Severity | None:
    """El filtro es opcional: si no viene, se devuelven todas las severidades."""
    if value is None or value == "":
        return None
    return parse_severity(value)


def parse_severity(value: Any) -> Severity:
    try:
        return Severity(value)
    except ValueError:
        raise ValidationError("severity debe ser LOW, MEDIUM o HIGH") from None


def _required_text(payload: dict[str, Any], field: str, max_length: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} es obligatorio")
    text = value.strip()
    if len(text) > max_length:
        raise ValidationError(f"{field} no puede superar {max_length} caracteres")
    return text
