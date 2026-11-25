# Reto técnico FullStack: Alertas operativas por orden

Módulo de **registro y consulta de alertas operativas** asociadas a una orden (`orderId`).

- **Backend:** API REST con AWS SAM, Python 3.12, DynamoDB y Secrets Manager.
- **Frontend:** Angular 21 (una sola pantalla).
- **Entorno local:** LocalStack (emulación de AWS en tu máquina). No se hacen despliegues reales a AWS.
- **Calidad:** pruebas unitarias, lint, análisis de seguridad, escaneo de secretos y CI en GitHub Actions.

Documentos clave:
- [`SPEC.md`](SPEC.md): requisitos, contrato de la API, modelo de datos y criterios de aceptación.
- [`CLAUDE.md`](CLAUDE.md): reglas de ingeniería para la IA en este repositorio.
- [`INCIDENT.md`](INCIDENT.md): diagnóstico del incidente de producción.

---

## Índice

1. [Estructura del repositorio](#1-estructura-del-repositorio)
2. [Requisitos previos](#2-requisitos-previos)
3. [Preparar el entorno local (LocalStack)](#3-preparar-el-entorno-local-localstack)
4. [Backend: pruebas, despliegue y API](#4-backend-pruebas-despliegue-y-api)
5. [Frontend: instalación, pruebas y ejecución](#5-frontend-instalación-pruebas-y-ejecución)
6. [Probar la API con Postman](#6-probar-la-api-con-postman)
7. [Ambientes: dev, qa y prod](#7-ambientes-dev-qa-y-prod)
8. [Integración continua (CI)](#8-integración-continua-ci)
9. [Limitaciones conocidas](#9-limitaciones-conocidas)
10. [Solución de problemas](#10-solución-de-problemas)
11. [Uso y supervisión de IA](#11-uso-y-supervisión-de-ia)

---

## 1. Estructura del repositorio

```
reto-tecnico-fullstack-ID/
├── .github/workflows/ci.yml      Pipeline de CI (backend, frontend, secretos)
├── alerts-service/               Backend (SAM + Python 3.12)
│   ├── template.yaml             Plantilla SAM: API, Lambda, DynamoDB, secreto
│   ├── samconfig.toml            Perfiles de despliegue: dev, qa, prod
│   ├── functions/alerts/         Código de la Lambda
│   │   ├── handler.py            Rutas HTTP, API key, códigos de respuesta
│   │   ├── service.py            Reglas de negocio
│   │   ├── repository.py         Acceso a DynamoDB (y versión en memoria)
│   │   ├── entities.py           Conversión entre el modelo y la tabla
│   │   ├── models.py             Modelo de negocio (Alert, Severity)
│   │   ├── validation.py         Validación de entradas
│   │   └── config.py             Lectura de la API key (env o Secrets Manager)
│   ├── tests/unit/               Pruebas unitarias con pytest
│   ├── postman/                  Colección y environment de Postman
│   ├── pytest.ini
│   └── requirements-dev.txt
├── alerts-web/                   Frontend (Angular 21)
│   ├── src/app/                  Pantalla, servicio y modelo
│   ├── src/environments/         URL de la API por ambiente
│   └── proxy.conf.json           Proxy de desarrollo hacia LocalStack
├── SPEC.md · CLAUDE.md · INCIDENT.md
```

---

## 2. Requisitos previos

Instala estas herramientas antes de empezar. Las versiones son las que usamos para validar el proyecto.

| Herramienta | Versión | Para qué |
|---|---|---|
| Windows 10/11 | — | Sistema usado para validar la guía (PowerShell) |
| Docker Desktop | Reciente | Ejecuta LocalStack |
| Python | **3.12** | Backend, pruebas y herramientas de calidad |
| Node.js | **22 LTS** o superior | Frontend (Angular 21) |
| AWS CLI v2 | Reciente | Consultar LocalStack (ver secretos y tablas) |
| LocalStack CLI (`lstk`) | 1.5.0 o superior | Desplegar la plantilla SAM en LocalStack |
| Cuenta de LocalStack | — | Token de autenticación (`LOCALSTACK_AUTH_TOKEN`) |
| VS Code (opcional) | Reciente | Editor y terminal |

> **Importante:** el proyecto usa **Python 3.12**, no la versión por defecto de tu equipo. En Windows, usa siempre el lanzador `py -3.12`.

Verifica las versiones en PowerShell:

```powershell
py -3.12 --version
```

```powershell
node --version
```

```powershell
docker --version
```

```powershell
aws --version
```

---

## 3. Preparar el entorno local (LocalStack)

### 3.1 Obtener el token de LocalStack

1. Crea una cuenta gratuita en https://app.localstack.cloud.
2. Copia tu **auth token** desde el panel de la cuenta.
3. Guárdalo como **variable de entorno de usuario** en Windows. No lo escribas en ningún archivo del proyecto:

```powershell
setx LOCALSTACK_AUTH_TOKEN "PEGA_AQUI_TU_TOKEN"
```

Cierra y vuelve a abrir la terminal (o VS Code) para que la variable se cargue. Verifica que existe, sin mostrar su valor:

```powershell
if ($env:LOCALSTACK_AUTH_TOKEN) { "Token configurado" } else { "Token NO encontrado" }
```

### 3.2 Instalar las herramientas

Herramientas de Python para Python 3.12:

```powershell
py -3.12 -m pip install awscli-local aws-sam-cli-local cfn-lint
```

LocalStack CLI (`lstk`), con Node.js:

```powershell
npm install -g @localstack/lstk
```

AWS CLI v2 (si no la tienes instalada):

```powershell
winget install -e --id Amazon.AWSCLI
```

Verifica las herramientas:

```powershell
lstk --version
```

```powershell
"C:\Users\TU_USUARIO\AppData\Local\Programs\Amazon\AWSCLIV2\aws.exe" --version
```

> Si `aws` no se reconoce después de instalar, cierra y abre la terminal, o usa la ruta completa como en el ejemplo.

### 3.3 Descargar la imagen de LocalStack

La primera vez tarda, porque la imagen pesa bastante:

```powershell
docker pull localstack/localstack
```

### 3.4 Iniciar LocalStack

Con `docker run`, que es la forma que usamos para validar el proyecto:

```powershell
docker run -d --name localstack-main -p 4566:4566 -p 4510-4559:4510-4559 -e LOCALSTACK_AUTH_TOKEN=$env:LOCALSTACK_AUTH_TOKEN -v //var/run/docker.sock:/var/run/docker.sock localstack/localstack
```

Comprueba que responde (espera unos 20 a 30 segundos la primera vez):

```powershell
curl.exe -s http://localhost:4566/_localstack/health
```

Revisa el estado con `lstk`:

```powershell
lstk status
```

Para detenerlo más adelante:

```powershell
docker stop localstack-main
```

### 3.5 Credenciales de prueba para LocalStack

LocalStack no necesita credenciales reales. Para usar la AWS CLI contra LocalStack, configura estas variables en cada terminal donde las uses:

```powershell
$env:AWS_ACCESS_KEY_ID = 'test'
$env:AWS_SECRET_ACCESS_KEY = 'test'
$env:AWS_DEFAULT_REGION = 'us-east-1'
```

> Nunca uses credenciales reales de AWS en este proyecto. Los comandos de la AWS CLI usan `--endpoint-url=http://localhost:4566` para apuntar a LocalStack.

---

## 4. Backend: pruebas, despliegue y API

Todos los comandos de esta sección se ejecutan desde la carpeta `alerts-service`:

```powershell
cd alerts-service
```

### 4.1 Instalar dependencias de desarrollo

```powershell
py -3.12 -m pip install -r requirements-dev.txt
```

Incluye `pytest`, `boto3`, `ruff`, `bandit` y `cfn-lint`.

### 4.2 Ejecutar las pruebas unitarias

```powershell
py -3.12 -m pytest -v
```

Resultado esperado: `11 passed`. Las pruebas no llaman a AWS.

### 4.3 Revisar lint, seguridad y la plantilla

Lint:

```powershell
py -3.12 -m ruff check functions tests
```

Análisis de seguridad:

```powershell
py -3.12 -m bandit -r functions -q
```

Validación de la plantilla SAM:

```powershell
cfn-lint template.yaml
```

Los tres deben terminar sin errores.

### 4.4 Construir la aplicación

```powershell
lstk sam build
```

Resultado esperado: `Build Succeeded`.

### 4.5 Desplegar el ambiente dev en LocalStack

```powershell
lstk sam deploy --config-env dev
```

Al final muestra la salida `AlertsBaseUrl`. Para volver a verla en cualquier momento:

```powershell
& "C:\Users\TU_USUARIO\AppData\Local\Programs\Amazon\AWSCLIV2\aws.exe" --endpoint-url=http://localhost:4566 cloudformation describe-stacks --stack-name alerts-dev --query "Stacks[0].Outputs[?OutputKey=='AlertsBaseUrl'].OutputValue" --output text
```

> Si el stack se recrea, el ID de la API cambia. Tendrás que actualizar la URL en `alerts-web/proxy.conf.json` y en `alerts-web/src/environments/environment.qa.ts` si aplica (ver sección 5 y 7).

### 4.6 Obtener la API key

La API key está en el secreto `alerts/dev/api-key`. Este comando la copia al portapapeles sin mostrarla en pantalla:

```powershell
& "C:\Users\TU_USUARIO\AppData\Local\Programs\Amazon\AWSCLIV2\aws.exe" --endpoint-url=http://localhost:4566 secretsmanager get-secret-value --secret-id alerts/dev/api-key --query SecretString --output text | Set-Clipboard
```

Recuerda definir antes las variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y `AWS_DEFAULT_REGION` (ver 3.5).

### 4.7 Endpoints de la API

Base (dev): `https://ylblzrt42n.execute-api.localhost.localstack.cloud:4566/dev/api/v1/orders`

Todas las rutas requieren el header `X-Api-Key`.

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| `POST` | `/{orderId}/alerts` | Registra una alerta | 201, 400, 401, 500 |
| `GET` | `/{orderId}/alerts` | Lista las alertas de la orden | 200, 400, 401, 500 |
| `GET` | `/{orderId}/alerts?severity=HIGH` | Lista filtrando por severidad (`LOW`, `MEDIUM`, `HIGH`) | 200, 400, 401, 500 |

Ejemplo de creación:

```json
{
  "severity": "HIGH",
  "message": "Latencia alta en el pago",
  "source": "monitoring"
}
```

Respuesta `201` (ejemplo):

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

Reglas:
- `orderId`: de 1 a 64 caracteres: letras, números, `-` o `_`.
- `severity`: exactamente `LOW`, `MEDIUM` o `HIGH`.
- `message`: obligatorio, máximo 500 caracteres.
- `source`: obligatorio, máximo 100 caracteres.

---

## 5. Frontend: instalación, pruebas y ejecución

Todos los comandos de esta sección se ejecutan desde la carpeta `alerts-web`:

```powershell
cd alerts-web
```

### 5.1 Instalar dependencias

```powershell
npm install --legacy-peer-deps
```

> La bandera `--legacy-peer-deps` es necesaria: npm 10 no resuelve bien las dependencias *peer* de `vitest`. Úsala siempre en este proyecto, incluido el CI.

### 5.2 Ejecutar en desarrollo

```powershell
npm start
```

Abre http://localhost:4200 en el navegador. El servidor de desarrollo reenvía `/api` a la API de LocalStack (`dev`) a través de `proxy.conf.json`, así que no hay problemas de CORS en local.

Uso de la pantalla:
1. Escribe un `orderId`, por ejemplo `ORD-1001`.
2. Pega la API key en el campo correspondiente. Se guarda solo en `sessionStorage` de la pestaña.
3. Pulsa **Buscar** para ver las alertas. Usa el filtro de severidad para acotar.
4. En **Registrar una alerta**, completa severidad, mensaje y origen, y pulsa **Registrar**.

### 5.3 Ejecutar las pruebas

```powershell
npm test -- --watch=false
```

Resultado esperado: `10 passed`. Las pruebas cubren el servicio HTTP y la pantalla (carga, lista vacía, errores 401, 400 y de red).

### 5.4 Compilar

Build de desarrollo:

```powershell
npm run build
```

Build para QA (apunta a la API de `alerts-qa`):

```powershell
npm run build:qa
```

Build de producción:

```powershell
npm run build:prod
```

> El build de `prod` usa un marcador (`REEMPLAZAR_CON_AlertsBaseUrl_DE_PROD`) porque el ambiente de producción aún no está desplegado. Reemplázalo con la salida `AlertsBaseUrl` de `alerts-prod` cuando exista.

Los archivos generados quedan en `alerts-web/dist/alerts-web/browser`. Esa carpeta está ignorada por Git.

---

## 6. Probar la API con Postman

1. Abre Postman y pulsa **Import**.
2. Importa `alerts-service/postman/alerts-api.postman_collection.json`.
3. Importa `alerts-service/postman/alerts-dev.postman_environment.json`.
4. Arriba a la derecha, selecciona el environment **alerts-dev**.
5. En la variable `apiKey` del environment, pega la API key (ver 4.6). El archivo del repositorio la deja vacía a propósito.
6. Ejecuta la colección con **Run collection**.

La colección tiene 7 requests con pruebas automáticas: creación (201), validaciones (400), listado, filtro por severidad, filtro inválido y ausencia de API key (401).

Si una request no funciona, revisa que el environment **alerts-dev** esté seleccionado y que `apiKey` tenga valor.

---

## 7. Ambientes: dev, qa y prod

| Ambiente | Backend (stack) | Frontend | Estado |
|---|---|---|---|
| **dev** | `alerts-dev` | `ng start` con proxy hacia `alerts-dev` | Desplegado en LocalStack |
| **qa** | `alerts-qa` | `npm run build:qa` | Desplegado en LocalStack |
| **prod** | `alerts-prod` | `npm run build:prod` | Configurado, **no desplegado** |

Para desplegar `qa` en LocalStack, desde `alerts-service`:

```powershell
lstk sam deploy --config-env qa
```

Cada ambiente usa su propio nombre de tabla (`alerts-<ambiente>`) y su propio secreto (`alerts/<ambiente>/api-key`). El mismo template sirve para los tres; solo cambia el parámetro `StageName`.

Para `prod`, la recomendación para un caso real es una cuenta de AWS separada. Aquí solo está documentado.

---

## 8. Integración continua (CI)

El workflow `.github/workflows/ci.yml` se ejecuta en cada push y pull request a `main`:

| Job | Qué hace |
|---|---|
| **Backend - lint, seguridad y pruebas** | `ruff`, `bandit`, `pytest` y `cfn-lint` |
| **Frontend - pruebas y build** | `npm ci --legacy-peer-deps`, `npm test` y `npm run build`, y guarda el build como artefacto |
| **Buscar secretos en el repositorio** | `gitleaks` sobre el historial |
| **Desplegar a dev (manual)** | Solo con **Run workflow** en la pestaña Actions. Requiere credenciales de AWS por OIDC y no se ejecuta en un push normal. |

El despliegue manual no se usa en esta entrega, porque no hacemos despliegues reales a AWS.

---

## 9. Limitaciones conocidas

- **Paginación:** la consulta a DynamoDB devuelve como máximo 1 MB por página. Si una orden tuviera un volumen muy grande de alertas, el listado no devolvería todo. Está documentado en `repository.py` como mejora pendiente: paginar con `LastEvaluatedKey`.
- **CORS con LocalStack:** la plantilla configura CORS con la propiedad `Cors` de SAM, pero LocalStack no genera el método `OPTIONS`. Por eso en desarrollo el frontend usa el proxy de `ng serve`. En AWS real el preflight sí debería funcionar.
- **Ambiente `prod`:** configurado pero no desplegado. `environment.prod.ts` tiene un marcador.
- **Proxy de desarrollo:** la URL de `proxy.conf.json` depende del ID de la API de `alerts-dev`. Si recreas el stack, cambia y hay que actualizarla.
- **Frontend sin despliegue:** el CI genera el build y lo guarda como artefacto. El despliegue a S3 y CloudFront queda como siguiente paso.
- **Validación del 404:** el reto no define un servicio de órdenes para verificar que `orderId` existe. Por eso solo se valida el formato, y el 404 se reserva para rutas inexistentes.

---

## 10. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Token NO encontrado` | La variable no se cargó | Cierra y vuelve a abrir la terminal después de `setx` |
| `python` ejecuta otra versión | El Python por defecto es 3.13 | Usa siempre `py -3.12` |
| `python -m cfnlint` no funciona | El módulo no se puede ejecutar así | Usa `cfn-lint template.yaml` |
| `npm install` falla con `edgesOut` | Bug de npm 10 con `vitest` | Usa `npm install --legacy-peer-deps` |
| `lstk sam deploy` no encuentra la API | LocalStack no está corriendo | Revisa `docker ps` y `lstk status` |
| El frontend muestra "No se pudo conectar" | LocalStack apagado o el ID de la API cambió | Inicia LocalStack y revisa `proxy.conf.json` |
| El frontend muestra "API key inválida" | La clave del campo no coincide con el secreto | Vuelve a copiarla con el comando de 4.6 |
| Postman devuelve 401 | `apiKey` vacío o environment no seleccionado | Revisa el paso 5 de la sección 6 |
| `docker pull` tarda mucho | La imagen de LocalStack es grande | Espera a que termine; solo pasa la primera vez |

---

## 11. Uso y supervisión de IA

Este proyecto se desarrolló con asistencia de IA (Claude Code), con supervisión humana en cada paso:

- **Especificación primero:** el `SPEC.md` y las reglas de `CLAUDE.md` se escribieron antes de generar código. La IA propuso el contrato y yo lo ajusté, por ejemplo para validar `orderId` por formato y no contra un catálogo de órdenes que el reto no define.
- **Error de la IA corregido a mano (clave de API):** la primera versión generaba la API key con puros ceros, porque usaba `RandomNumberGenerator.Fill`, que no existe en PowerShell 5.1. Lo detecté al revisar el valor y lo corregí con `GetBytes`.
- **Error de la IA corregido a mano (`samlocal`):** la guía inicial usaba `samlocal`, que está obsoleto. Lo cambié por `lstk sam` después de validarlo con un despliegue de prueba.
- **Decisión tomada tras revisar el CI:** la acción oficial de gitleaks falló en el primer push, porque el primer commit no tiene padre. Probé una alternativa con Docker, la descarté por no integrarse con GitHub y no fijar la imagen por digest, y volví a la acción oficial. El fallo solo afecta al primer push.
- **Refactor del modelo:** la primera versión mezclaba el modelo de negocio con el formato de DynamoDB en `models.py`. Lo separé en `entities.py` para que el dominio no dependa de la tabla.

---

Autor: [carjizo](https://github.com/carjizo)
