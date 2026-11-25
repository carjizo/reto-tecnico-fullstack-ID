from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class Alert:
    """Modelo de negocio. No sabe cómo se guarda ni cómo se envía por HTTP."""

    order_id: str
    alert_id: str
    severity: Severity
    message: str
    source: str
    created_at: str
