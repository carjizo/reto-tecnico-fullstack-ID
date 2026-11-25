# SPEC – Registro y consulta de alertas operativas

## 1. Objetivo
Registrar y consultar alertas operativas asociadas a una orden (`orderId`).

## 2. Requisitos
- **RF-1** Registrar una alerta con severidad, mensaje y origen.
- **RF-2** Listar las alertas de una orden, con filtro opcional por severidad.
- **RF-3** Validar las entradas y devolver errores claros.
- **RF-4** Frontend para ingresar un `orderId`, listar, filtrar y registrar alertas, con estados de carga, lista vacía y errores de red y validación.

## 3. Contrato de la API
Base: `/api/v1/orders/{orderId}/alerts`. Todas las rutas requieren el header `X-Api-Key`.

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| `POST` | `/{orderId}/alerts` | Registra una alerta | 201, 400, 401, 500 |
| `GET` | `/{orderId}/alerts?severity=LOW\|MEDIUM\|HIGH` | Lista alertas (filtro opcional) | 200, 400, 401, 500 |

**Body del POST**

| Campo | Reglas |
|---|---|
| `severity` | Obligatorio: `LOW`, `MEDIUM` o `HIGH`. |
| `message` | Obligatorio. Máximo 500 caracteres. |
| `source` | Obligatorio. Máximo 100 caracteres. |

**Alerta (respuesta 201 y elementos del listado)**

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

`alertId` y `createdAt` los genera el servicio en UTC. El cliente no los envía.

**Errores**

| Código | Cuándo | Body |
|---|---|---|
| 400 | Dato inválido (severidad, campos vacíos, `orderId` con formato incorrecto, JSON mal formado) | `{"error": "<mensaje claro>"}` |
| 401 | Falta `X-Api-Key` o no coincide | `{"error": "API key inválida o ausente"}` |
| 404 | La ruta no existe | `{"error": "Ruta no encontrada"}` |
| 500 | Error inesperado o de la capa de datos | `{"error": "Error interno del servidor"}` |

## 4. Modelo de datos
Tabla DynamoDB `alerts-<ambiente>`, modo `PAY_PER_REQUEST`.

- **Clave de partición:** `orderId`. Viene de la URL y pertenece al sistema de órdenes; el servicio solo valida su formato.
- **Clave de ordenación:** `alertId` con formato `createdAt#uuid`. La fecha ISO en UTC con milisegundos ordena cronológicamente; el uuid evita colisiones.

## 5. Criterios de aceptación
- **CA-1** Un POST válido devuelve 201 y la alerta queda guardada.
- **CA-2** Un POST con severidad inválida o campos vacíos devuelve 400 con mensaje claro y no escribe en la tabla.
- **CA-3** Si la capa de datos falla, responde 500 sin detalles internos.
- **CA-4** Un GET sin alertas devuelve 200 con una lista vacía.
- **CA-5** Un GET con `severity=HIGH` devuelve solo alertas `HIGH`.
- **CA-6** Sin `X-Api-Key` válido, responde 401.
- **CA-7** Ningún secreto está escrito en el código ni en el repositorio.

## 6. Decisiones
- **Existencia de la orden:** el reto no define un servicio de órdenes, así que solo se valida el formato de `orderId`. El 404 se reserva para rutas inexistentes.
- **Base de datos:** DynamoDB, porque se ejecuta en local con LocalStack y encaja con Lambda.
- **Runtime:** Python 3.12 en local y en Lambda.
