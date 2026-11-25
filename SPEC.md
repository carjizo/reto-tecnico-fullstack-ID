# SPEC – Registro y Consulta de Alertas Operativas

## 1. Objetivo
Permitir registrar y consultar alertas operativas asociadas a una orden (`orderId`).

## 2. Requisitos funcionales
- RF-1: Registrar una alerta para una orden con severidad, mensaje y origen.
- RF-2: Listar las alertas de una orden, con filtro opcional por severidad.
- RF-3: Validar las entradas y devolver errores claros (400, 404, 500).
- RF-4: Frontend que permita ingresar un `orderId`, listar alertas, filtrar, y registrar nuevas alertas, con estados de carga, lista vacía y errores.

## 3. Contrato de la API

Base path: `/api/v1`

### 3.1 Registrar alerta
`POST /api/v1/orders/{orderId}/alerts`

Body (JSON):
```json
{
  "severity": "HIGH",
  "message": "Latencia alta en el pago",
  "source": "monitoring"
}
```

| Campo | Tipo | Reglas |
|---|---|---|
| `severity` | string | Obligatorio. Valores: `LOW`, `MEDIUM`, `HIGH`. |
| `message` | string | Obligatorio. Entre 1 y 500 caracteres. |
| `source` | string | Obligatorio. Entre 1 y 100 caracteres. |

Respuestas:
| Código | Cuándo | Body |
|---|---|---|
| 201 | Alerta creada | Alerta creada (ver modelo) |
| 400 | Body inválido o campos faltantes | `{"error": "...mensaje claro..."}` |
| 404 | La ruta no existe (ver decisión 8.1) | `{"error": "Not found"}` |
| 500 | Error inesperado o de base de datos | `{"error": "Internal server error"}` |

### 3.2 Listar alertas de una orden
`GET /api/v1/orders/{orderId}/alerts?severity=LOW|MEDIUM|HIGH`

| Código | Cuándo | Body |
|---|---|---|
| 200 | Lista (puede estar vacía) | Array de alertas |
| 400 | `severity` con valor no permitido | `{"error": "..."}` |
| 500 | Error inesperado o de base de datos | `{"error": "Internal server error"}` |

### 3.3 Modelo de alerta
```json
{
  "orderId": "ORD-1001",
  "alertId": "2026-11-25T10:15:00.123Z#0b9c4f2e-7a1d-4c3b-9e8f-2d5a6b7c8d9e",
  "severity": "HIGH",
  "message": "Latencia alta en el pago",
  "source": "monitoring",
  "createdAt": "2026-11-25T10:15:00.123Z"
}
```

Los campos `alertId` y `createdAt` los genera el servicio en el POST, en UTC. El cliente no los envía.

### 3.4 Autenticación
Todas las rutas requieren el header `X-Api-Key`. El valor se compara con el secreto `ALERTS_API_KEY`. Si falta o no coincide, responde 401.

## 4. Modelo de datos
Tabla DynamoDB `alerts`:
- Clave de partición: `orderId` (String). Es el valor de la URL, validado por formato. El servicio no lo genera; pertenece al sistema de órdenes.
- Clave de ordenación: `alertId` (String), formato `createdAt#uuid` (fecha ISO UTC con milisegundos, `#`, uuid4). El prefijo de fecha ordena las alertas cronológicamente; el uuid evita colisiones si dos alertas se crean en el mismo milisegundo.
- Facturación: `PAY_PER_REQUEST`.

## 5. Criterios de aceptación
- CA-1: Un POST válido devuelve 201 y la alerta guardada en la tabla.
- CA-2: Un POST con severidad inválida o sin `message` devuelve 400 con mensaje claro, y no escribe en la tabla.
- CA-3: Si la capa de datos falla, la respuesta es 500 controlado, sin stack trace.
- CA-4: Un GET sin alertas devuelve 200 con lista vacía.
- CA-5: Un GET con `severity=HIGH` devuelve solo alertas HIGH.
- CA-6: Sin `X-Api-Key` válido, la respuesta es 401.
- CA-7: Ningún secreto está escrito en el código ni en el repositorio.

## 6. Decisiones
- 8.1 Existencia de la orden: el reto no define un servicio de órdenes para validar si `orderId` existe. Se valida solo el formato. El 404 se usa cuando la ruta no existe. **Pendiente de confirmar con el usuario.**
- Base de datos: DynamoDB (pendiente de confirmar).
- Runtime: Python 3.12 en local y en Lambda.
