# Reglas de ingeniería para asistentes de IA

Alcance: este repositorio. Aplican a cualquier asistente de IA que genere, modifique o revise código o documentación. El código debe ser legible y mantenible; la IA propone, el ingeniero decide y responde por el resultado.

## 1. Fuente de verdad y diseño
- `SPEC.md` es la fuente de verdad del contrato (rutas, payloads, códigos HTTP, modelo de datos). Si el código y el SPEC no coinciden, se corrige el código o se actualiza el SPEC con una justificación en el commit.
- Antes de generar código, la IA debe proponer el cambio y sus alternativas cuando haya un trade-off relevante.
- Principios: SOLID aplicado a Python. Separación por capas: `handler` (transporte HTTP) → `service` (reglas de negocio) → `repository` (persistencia).
- Dependencias por abstracción: el `service` depende de un `Protocol` de repositorio, nunca de la implementación concreta de DynamoDB.
- Ninguna lógica de negocio en el `handler` ni en el `repository`.

## 2. Stack y versiones fijadas
- Python **3.12** en local y en Lambda. No se cambia sin un ADR (registro de decisión) que lo justifique.
- Angular **21** en el frontend. AWS SAM para la infraestructura. DynamoDB como almacenamiento.
- Configuración según 12-factor: todo lo que cambia entre entornos sale de variables de entorno o de Secrets Manager.

## 3. Calidad de código
- Type hints obligatorios en funciones públicas.
- `ruff` (lint y formato) y `mypy` sin errores. Un warning nuevo bloquea el merge.
- Funciones con una sola responsabilidad y nombres que describan el dominio (`create_alert`, no `process`).
- Sin código muerto, sin `print` para depurar, sin comentarios que repitan lo que hace el código.

## 4. Errores y contratos
- Errores de dominio tipados: `ValidationError` (400) y `NotFoundError` (404). El resto es 500.
- El mapeo de excepción a código HTTP ocurre en un solo lugar (el `handler`).
- El 500 responde un mensaje genérico. Nunca se expone un stack trace, una consulta ni un detalle de infraestructura.

## 5. Observabilidad y operación
- Logs estructurados en JSON, con `correlation_id` por petición y nivel de log adecuado.
- Nunca registrar datos sensibles: API keys, tokens, datos personales ni cuerpos completos de petición.
- Timeouts de Lambda menores a 29 s (límite de API Gateway). Reintentos con límite y backoff.
- Toda ruta de producción tiene al menos una alarma de latencia y otra de errores 5xx.

## 6. Seguridad (OWASP)
- Validar toda entrada en el borde (handler) antes de llegar al servicio.
- Mínimo privilegio en IAM: prohibido `Resource: "*"` y acciones `*`. Cada política se limita al recurso exacto.
- Prohibido hardcodear credenciales, API keys, tokens o ARNs sensibles. Los secretos se leen de Secrets Manager o de variables de entorno locales.
- `.gitignore` y `gitleaks` en CI como barrera contra la fuga de secretos. Nunca se sube un `.env` ni un token.

## 7. Pruebas
- Mínimo 3 pruebas unitarias obligatorias: creación exitosa, rechazo por datos inválidos y fallo de la capa de datos.
- Las pruebas unitarias no llaman a AWS. Se usa `InMemoryAlertRepository` o un doble de prueba.
- Toda regla de negocio nueva llega con su prueba, en el mismo commit.

## 8. Proceso y entregas
- Conventional Commits: `docs:`, `feat:`, `fix:`, `test:`, `ci:`, `refactor:`.
- Un commit por fase del plan. El historial debe contar la historia del proyecto.
- Definition of Done: el SPEC se cumple, las pruebas pasan, el CI está en verde y no hay secretos en el diff.

## 9. Supervisión humana de la IA
- Toda salida de la IA se revisa antes de aceptarse.
- Cada corrección manual importante se documenta en la sección "Uso y supervisión de IA" del README.
