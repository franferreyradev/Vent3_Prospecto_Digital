# PLAN.md — Sistema de Prospecto Digital Vent3

**Versión:** 1.0
**Estado:** Borrador para aprobación
**Fecha:** Junio 2026
**Autor:** Área de Sistemas — Laboratorio Vent3
**Documento padre:** SPEC.md v1.0
**Deadline regulatorio:** 15 de noviembre de 2026

---

## SECCIÓN 1 — ARQUITECTURA DE CARPETAS

```
vent3/
├── apps/
│   ├── web/                    → Next.js frontend (sitio institucional + portal de prospectos + panel admin)
│   │   ├── app/                → Rutas App Router
│   │   │   ├── (public)/       → Sitio institucional (home, productos, contacto)
│   │   │   ├── 01/[gtin]/      → Resolver GS1 Digital Link
│   │   │   └── admin/          → Panel administrativo (login, dashboard, productos, prospectos, auditoría)
│   │   ├── components/         → Componentes atómicos y compuestos UI
│   │   ├── lib/                → Cliente HTTP de la API, hooks, utilidades
│   │   ├── public/             → Assets estáticos (logos, fuentes, favicons)
│   │   ├── styles/             → CSS global, configuración base de Tailwind
│   │   ├── next.config.js      → Configuración Next.js
│   │   ├── tailwind.config.ts  → Design tokens extendidos
│   │   └── package.json        → Workspace del frontend
│   │
│   └── api/                    → FastAPI backend (Python 3.12)
│       ├── src/
│       │   ├── routers/        → Definición de endpoints por módulo (FastAPI APIRouter)
│       │   ├── schemas/        → Pydantic v2 (request/response DTOs)
│       │   ├── models/         → SQLAlchemy 2.0 (modelos ORM)
│       │   ├── services/       → Lógica de negocio pura, testeable en aislamiento
│       │   ├── repositories/   → Acceso a PostgreSQL (queries, transacciones)
│       │   ├── core/           → Config, seguridad (JWT, bcrypt), dependencias
│       │   ├── storage/        → Cliente Cloudflare R2 (upload/download de PDFs)
│       │   ├── auditing/       → Decoradores y middleware de audit_log
│       │   └── main.py         → Entry point FastAPI
│       ├── alembic/            → Migraciones SQL versionadas
│       │   ├── versions/       → Una migración por cambio de schema
│       │   └── env.py          → Configuración Alembic
│       ├── tests/              → Tests con pytest (unit + integration)
│       ├── scripts/            → Scripts operativos
│       │   └── migrar_excel.py → Migración one-shot desde BD_productos_v2.xlsx
│       ├── pyproject.toml      → Dependencias Python (Poetry o uv)
│       └── alembic.ini         → Config Alembic
│
├── packages/
│   └── contracts/              → Tipos TypeScript generados desde OpenAPI
│       ├── src/
│       │   └── api.ts          → Tipos auto-generados (openapi-typescript)
│       ├── scripts/
│       │   └── generate.sh     → Descarga openapi.json desde /api/openapi.json y genera tipos
│       └── package.json
│
├── docs/
│   ├── SPEC.md                 → Especificación funcional aprobada
│   ├── PLAN.md                 → Este documento
│   ├── TASK.md                 → Estado vivo del trabajo (handoff note)
│   ├── BD_Diseño_v2.docx       → Diseño de base de datos aprobado
│   └── adr/                    → Architecture Decision Records (uno por decisión)
│
├── .github/
│   └── workflows/              → CI/CD (lint, test, deploy a Railway/Vercel)
│
├── infra/
│   └── docker-compose.yml      → PostgreSQL + servicio de objetos local para desarrollo
│
├── package.json                → Raíz monorepo (orquesta workspaces JS y comandos generales)
├── tsconfig.base.json          → Configuración TypeScript compartida
├── .env.example                → Plantilla de variables de entorno
└── README.md                   → Setup, scripts, convenciones
```

**Nota sobre monorepo poliglota:** dado que el backend es Python (FastAPI) y el frontend TypeScript (Next.js), no se usan workspaces npm de manera homogénea como en un stack puro JS. La raíz contiene workspaces npm para `apps/web` y `packages/contracts`. El backend Python tiene su propio sistema de dependencias (`pyproject.toml`). La sincronización de tipos entre backend y frontend se resuelve mediante generación automática de tipos TypeScript desde el schema OpenAPI que FastAPI expone en `/api/openapi.json`.

---

## SECCIÓN 2 — ESQUEMA DE BASE DE DATOS

El diseño completo y aprobado está documentado en `docs/BD_Diseño_v2.docx`. Esta sección traduce ese diseño a SQL ejecutable.

### Tipos personalizados (ENUMs PostgreSQL)

```sql
CREATE TYPE canal_enum AS ENUM ('farmacia', 'licitacion');
CREATE TYPE estado_producto_enum AS ENUM ('activo', 'inactivo');
CREATE TYPE estado_vigencia_enum AS ENUM ('vigente', 'reemplazado', 'en_revision');
CREATE TYPE tipo_audiencia_enum AS ENUM ('publico_general', 'profesional_salud', 'unico');
CREATE TYPE estado_gtin_enum AS ENUM ('activo', 'en_desarrollo', 'inactivo');
CREATE TYPE rol_usuario_enum AS ENUM ('admin', 'editor', 'lector');
CREATE TYPE accion_audit_enum AS ENUM ('INSERT', 'UPDATE', 'DELETE');
CREATE TYPE tipo_envase_enum AS ENUM ('blister', 'frasco', 'otro');
```

### Extensiones requeridas

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- Para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS unaccent;  -- Para normalización de búsquedas
```

### Tabla: productos

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| codigo_interno | VARCHAR(20) | NULL, UNIQUE |
| nombre_comercial | VARCHAR(200) | NOT NULL |
| forma_farmaceutica | VARCHAR(100) | NOT NULL |
| presentacion_cantidad | VARCHAR(50) | NOT NULL |
| canal | canal_enum | NOT NULL DEFAULT 'farmacia' |
| estado | estado_producto_enum | NOT NULL DEFAULT 'activo' |
| tiene_prospecto | BOOLEAN | NOT NULL DEFAULT FALSE |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**Trigger:** `BEFORE UPDATE` que actualiza `updated_at = NOW()` automáticamente.

**Índices:**
- `CREATE INDEX idx_producto_estado ON productos(estado) WHERE estado = 'activo';`
- `CREATE INDEX idx_producto_canal ON productos(canal);`
- `CREATE INDEX idx_producto_codigo_interno ON productos(codigo_interno);`

### Tabla: principios_activos

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| nombre | VARCHAR(150) | NOT NULL UNIQUE |
| nombre_normalizado | VARCHAR(150) | NOT NULL UNIQUE |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**Trigger:** `BEFORE INSERT OR UPDATE` que genera `nombre_normalizado = lower(unaccent(nombre))` automáticamente.

**Índices:**
- `CREATE INDEX idx_principio_normalizado ON principios_activos(nombre_normalizado);`

### Tabla: producto_principios

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| producto_id | UUID | NOT NULL, FK → productos(id) ON DELETE CASCADE |
| principio_id | UUID | NOT NULL, FK → principios_activos(id) ON DELETE RESTRICT |
| potencia | VARCHAR(30) | NOT NULL |
| unidad | VARCHAR(20) | NULL |
| orden | SMALLINT | NOT NULL CHECK (orden > 0) |

**UNIQUE constraint:** `UNIQUE (producto_id, principio_id)` — evita duplicar la misma droga en un producto.

**ON DELETE CASCADE en producto_id:** si se elimina un producto (no debería ocurrir, se usa soft delete vía estado), sus principios asociados también.
**ON DELETE RESTRICT en principio_id:** protege el catálogo histórico de drogas.

**Índices:**
- `CREATE INDEX idx_pp_producto ON producto_principios(producto_id);`
- `CREATE INDEX idx_pp_principio ON producto_principios(principio_id);`

### Tabla: prospectos

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| numero_expediente | VARCHAR(30) | NOT NULL |
| version | SMALLINT | NOT NULL CHECK (version > 0) |
| tipo_audiencia | tipo_audiencia_enum | NOT NULL DEFAULT 'unico' |
| url_archivo | TEXT | NOT NULL |
| nombre_archivo | VARCHAR(200) | NOT NULL |
| estado_vigencia | estado_vigencia_enum | NOT NULL DEFAULT 'en_revision' |
| subido_por | UUID | NOT NULL, FK → usuarios(id) ON DELETE RESTRICT |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**UNIQUE constraint:** `UNIQUE (numero_expediente, version, tipo_audiencia)` — un código de prospecto no puede tener dos versiones idénticas para la misma audiencia.

**Nota sobre `numero_expediente`:** es una codificación interna del laboratorio (ej. IB-22/2, A-21/1, CL-21/01). No es un código administrado por ANMAT.

**Nota sobre `tipo_audiencia`:** un producto con un único prospecto usa `'unico'`. Cuando hay versiones diferenciadas se cargan dos registros, uno `'publico_general'` y otro `'profesional_salud'`, ambos vigentes simultáneamente para el mismo producto.

**Índices:**
- `CREATE INDEX idx_prospecto_vigente ON prospectos(estado_vigencia) WHERE estado_vigencia = 'vigente';`
- `CREATE INDEX idx_prospecto_numero ON prospectos(numero_expediente);`

### Tabla: producto_prospectos

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| producto_id | UUID | NOT NULL, FK → productos(id) ON DELETE RESTRICT |
| prospecto_id | UUID | NOT NULL, FK → prospectos(id) ON DELETE RESTRICT |
| variante_gs1 | VARCHAR(30) | NULL |
| activo | BOOLEAN | NOT NULL DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**UNIQUE constraint (parcial):** `CREATE UNIQUE INDEX idx_pp_unico_vigente ON producto_prospectos(producto_id, prospecto_id) WHERE activo = TRUE;` — la misma asociación no puede estar activa dos veces.

**Regla de negocio implementada vía service layer:** un producto puede tener simultáneamente activas como máximo dos asociaciones, una con prospecto de `tipo_audiencia='publico_general'` y otra de `'profesional_salud'`, o una sola con `'unico'`. Se valida en el service de activación de prospectos.

**Índices:**
- `CREATE INDEX idx_prodprosp_producto ON producto_prospectos(producto_id);`
- `CREATE INDEX idx_prodprosp_activo ON producto_prospectos(producto_id) WHERE activo = TRUE;`

### Tabla: gtin_registro

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| producto_id | UUID | NOT NULL, FK → productos(id) ON DELETE RESTRICT |
| gtin | CHAR(14) | NOT NULL CHECK (gtin ~ '^\d{14}$') |
| estado_gtin | estado_gtin_enum | NOT NULL DEFAULT 'en_desarrollo' |
| es_vigente | BOOLEAN | NOT NULL DEFAULT FALSE |
| url_digital_link | TEXT | NULL |
| qr_generado | BOOLEAN | NOT NULL DEFAULT FALSE |
| validado_gs1 | BOOLEAN | NOT NULL DEFAULT FALSE |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**UNIQUE constraint:** `UNIQUE (gtin)` — un GTIN identifica un único producto a nivel global GS1.

**UNIQUE parcial:** `CREATE UNIQUE INDEX idx_gtin_vigente_unico ON gtin_registro(producto_id) WHERE es_vigente = TRUE;` — solo un GTIN vigente por producto.

**CHECK regex `^\d{14}$`:** garantiza exactamente 14 dígitos numéricos según estándar GS1.

**Índices:**
- `CREATE UNIQUE INDEX idx_gtin_lookup ON gtin_registro(gtin);` — esta es la query crítica del endpoint público.
- `CREATE INDEX idx_gtin_producto ON gtin_registro(producto_id);`

### Tabla: usuarios

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| email | VARCHAR(150) | NOT NULL UNIQUE |
| nombre | VARCHAR(100) | NOT NULL |
| password_hash | VARCHAR(60) | NOT NULL |
| rol | rol_usuario_enum | NOT NULL DEFAULT 'lector' |
| activo | BOOLEAN | NOT NULL DEFAULT TRUE |
| ultimo_acceso | TIMESTAMPTZ | NULL |
| intentos_fallidos | SMALLINT | NOT NULL DEFAULT 0 |
| bloqueado_hasta | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**Nota sobre `password_hash`:** longitud 60 corresponde a bcrypt. Costo 12 (configurable vía env).

**Nota sobre lockout:** `intentos_fallidos` y `bloqueado_hasta` implementan el bloqueo temporal de 15 minutos tras 5 intentos fallidos (RF-03 de SPEC).

**Seed inicial:** un único usuario admin se carga en la migración inicial con email y password leídos desde variables de entorno (`ADMIN_EMAIL`, `ADMIN_INITIAL_PASSWORD`).

**Índices:**
- `CREATE UNIQUE INDEX idx_usuario_email ON usuarios(email);`

### Tabla: audit_log

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tabla_afectada | VARCHAR(50) | NOT NULL |
| registro_id | UUID | NOT NULL |
| accion | accion_audit_enum | NOT NULL |
| campo_modificado | VARCHAR(80) | NULL |
| valor_anterior | TEXT | NULL |
| valor_nuevo | TEXT | NULL |
| usuario_id | UUID | NOT NULL, FK → usuarios(id) ON DELETE RESTRICT |
| ip_origen | INET | NULL |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**Inmutabilidad total:** trigger `BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION raise_audit_inmutable()` que rechaza cualquier operación destructiva.

**Permisos de DB:** el rol de aplicación (`vent3_app`) tiene solo `INSERT` y `SELECT` sobre esta tabla, nunca `UPDATE` ni `DELETE`. La inmutabilidad se refuerza a nivel de base de datos, no solo de aplicación.

**Índices:**
- `CREATE INDEX idx_audit_tabla_registro ON audit_log(tabla_afectada, registro_id);`
- `CREATE INDEX idx_audit_usuario ON audit_log(usuario_id);`
- `CREATE INDEX idx_audit_created ON audit_log(created_at DESC);`

### Tabla: producto_materiales_packaging

| Columna | Tipo | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| producto_id | UUID | NOT NULL UNIQUE, FK → productos(id) ON DELETE CASCADE |
| tipo_envase | tipo_envase_enum | NOT NULL |
| codigo_estuche | VARCHAR(30) | NULL |
| codigo_aluminio | VARCHAR(30) | NULL |
| codigo_pvc | VARCHAR(30) | NULL |
| codigo_frasco | VARCHAR(30) | NULL |
| codigo_etiqueta | VARCHAR(30) | NULL |
| codigo_vaso_inserto | VARCHAR(30) | NULL |
| codigo_tapa | VARCHAR(30) | NULL |
| notas | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

**UNIQUE en producto_id:** una sola configuración de packaging por producto.

**Nota:** tabla incorporada como extensión futura. No participa del flujo del MVP pero se crea desde el inicio para que la migración del Excel pueda volcar los datos relevados.

**Índices:** ninguno adicional, el UNIQUE cubre las lecturas.

---

## SECCIÓN 3 — ENDPOINTS REST DE LA API

| Método | Ruta | Rol requerido | Descripción | Body / Response |
|---|---|---|---|---|
| GET | `/01/{gtin}` | Público | Resolver GS1 Digital Link. **Este endpoint NO es JSON sino HTML SSR servido por Next.js.** Listado aquí por completitud; la implementación vive en `apps/web/app/01/[gtin]/page.tsx` y consulta internamente `/api/internal/prospectos/by-gtin/{gtin}` | — → HTML del prospecto |
| GET | `/api/internal/prospectos/by-gtin/{gtin}` | Público (uso interno SSR) | Resolución de GTIN a prospectos vigentes. Solo accesible desde el servidor Next.js (validado por header secreto). | — → `{ producto: {...}, prospectos: [{ tipo_audiencia, url_archivo }], error?: 'no_encontrado' \| 'inactivo' \| 'sin_prospecto' }` |
| POST | `/api/auth/login` | Público | Login del admin. Emite JWT en cookie httpOnly de 8 horas. | `{ email, password }` → 204 + Set-Cookie, o 401 genérico |
| POST | `/api/auth/logout` | Cualquier rol | Invalida la cookie actual. | — → 204 |
| GET | `/api/auth/me` | Cualquier rol | Devuelve el usuario actual. | — → `{ id, email, nombre, rol }` |
| GET | `/api/productos` | admin, editor, lector | Lista productos con filtros y paginación. | `?estado=&canal=&search=&page=&limit=` → `{ data: [...], total, page, limit }` |
| GET | `/api/productos/{id}` | admin, editor, lector | Detalle completo de un producto (incluye principios, GTIN vigente, prospectos vigentes, packaging). | — → `Producto detallado` |
| PATCH | `/api/productos/{id}` | admin, editor | Modifica un producto. Cambios registrados en audit_log. | `{ ...campos }` → Producto |
| PATCH | `/api/productos/{id}/estado` | admin, editor | Activa o desactiva un producto. | `{ estado: 'activo' \| 'inactivo' }` → Producto |
| GET | `/api/prospectos` | admin, editor, lector | Lista todos los prospectos con filtros. | `?estado_vigencia=&producto_id=` → `[...]` |
| POST | `/api/prospectos` | admin, editor | Sube un PDF y crea el registro. **Endpoint multipart/form-data.** | `multipart: file + { numero_expediente, version, tipo_audiencia, producto_id }` → Prospecto creado en estado 'en_revision' |
| PATCH | `/api/prospectos/{id}/activar` | admin, editor | Activa el prospecto: lo marca como vigente y desactiva el anterior del mismo producto + tipo_audiencia (transacción atómica). | — → `{ activado: Prospecto, reemplazado?: Prospecto }` |
| GET | `/api/prospectos/{id}/download-url` | admin, editor, lector | Genera URL firmada temporal del PDF para descarga desde panel. | — → `{ url, expires_in_seconds }` |
| GET | `/api/audit-log` | admin | Listado paginado de eventos de auditoría. | `?tabla=&registro_id=&usuario_id=&desde=&hasta=&page=&limit=` → `{ data: [...], total, page, limit }` |
| GET | `/api/openapi.json` | Público (solo en dev/staging) | Schema OpenAPI usado para generar tipos del frontend. | — → OpenAPI 3.1 JSON |

**Nota sobre autorización:** los roles `editor` y `lector` no se usan en el MVP (solo existe `admin`) pero los endpoints ya validan correctamente para no requerir refactorización cuando se habilite gestión multi-usuario.

**Nota sobre el header secreto del SSR:** la ruta `/api/internal/*` solo acepta peticiones que incluyan el header `X-Internal-Token` con un valor compartido entre Next.js (server-side) y FastAPI vía variable de entorno `INTERNAL_API_TOKEN`. Esto evita que un atacante consulte directamente la API interna desde el navegador.

---

## SECCIÓN 4 — ORDEN DE IMPLEMENTACIÓN

### FASE 0 — Fundación (Semanas 1-2)

#### T1 — Setup del monorepo

- **Descripción:** estructura de carpetas, workspaces npm para `apps/web` y `packages/contracts`, configuración Python para `apps/api`, archivos base de configuración.
- **Archivos afectados:** `package.json` raíz, `apps/web/package.json`, `apps/api/pyproject.toml`, `packages/contracts/package.json`, `tsconfig.base.json`, `.env.example`, `README.md`, `.gitignore`.
- **Criterio de done:** `npm install` desde la raíz instala los workspaces JS, `cd apps/api && uv sync` instala dependencias Python sin error, y `docker-compose up` levanta PostgreSQL local.
- **Depende de:** Ninguna.

#### T2 — Contratación de infraestructura

- **Descripción:** crear cuentas y proyectos en Railway (backend + PostgreSQL), Vercel (frontend) y Cloudflare R2 (storage). Configurar dominios: apuntar `www.vent3.com.ar` a Vercel y `api.vent3.com.ar` a Railway. Generar y guardar todas las credenciales en gestor de secretos.
- **Archivos afectados:** `.env.example` (documentar todas las variables necesarias), `docs/adr/001-infraestructura.md`.
- **Criterio de done:** un deploy de prueba "hola mundo" en Vercel responde en `https://www.vent3.com.ar` y FastAPI con un endpoint dummy responde en `https://api.vent3.com.ar/health`. PostgreSQL accesible desde Railway.
- **Depende de:** T1.

#### T3 — Schema SQL inicial y migraciones Alembic

- **Descripción:** crear todas las tablas, ENUMs, triggers de inmutabilidad de `audit_log` y `updated_at`, índices y constraints de la Sección 2.
- **Archivos afectados:** `apps/api/alembic/versions/001_initial_schema.py`, `apps/api/alembic/versions/002_triggers_y_funciones.py`, `apps/api/alembic/versions/003_seed_admin_inicial.py`.
- **Criterio de done:** `alembic upgrade head` sobre DB vacía deja las 9 tablas creadas, los triggers activos (verificado con un INSERT + intento de UPDATE en `audit_log` que debe fallar), y el usuario admin inicial creado con credenciales desde env.
- **Depende de:** T2.

#### T4 — Modelos SQLAlchemy y repositorios base

- **Descripción:** modelos ORM de las 9 tablas, sesión de DB con dependency injection, repositorios con métodos CRUD básicos.
- **Archivos afectados:** `apps/api/src/models/*.py`, `apps/api/src/core/db.py`, `apps/api/src/repositories/*.py`.
- **Criterio de done:** test de integración que inserta un Producto + Principio + ProductoPrincipio y los lee de vuelta pasa verde.
- **Depende de:** T3.

#### T5 — Schemas Pydantic y generación de tipos TypeScript

- **Descripción:** schemas de request/response para todos los endpoints. Script que descarga `/openapi.json` y genera `packages/contracts/src/api.ts` con `openapi-typescript`.
- **Archivos afectados:** `apps/api/src/schemas/*.py`, `packages/contracts/scripts/generate.sh`, `packages/contracts/src/api.ts`.
- **Criterio de done:** desde `apps/web` se puede hacer `import type { Producto } from '@vent3/contracts'` y los tipos coinciden con los Pydantic del backend.
- **Depende de:** T4.

### FASE 1 — Backend core (Semanas 3-4)

#### T6 — Auth: login del admin + JWT en cookie httpOnly

- **Descripción:** endpoints `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`. Bcrypt costo 12. JWT firmado con secret server-side. Cookie httpOnly + Secure + SameSite=Lax expira a 8 horas. Bloqueo temporal tras 5 intentos fallidos.
- **Archivos afectados:** `apps/api/src/routers/auth.py`, `apps/api/src/services/auth.py`, `apps/api/src/core/security.py`, `apps/api/src/core/deps.py`.
- **Criterio de done:** (a) login con credenciales válidas retorna 204 + Set-Cookie; (b) login con password incorrecto retorna 401 genérico que no revela si el email existe; (c) 5 intentos fallidos bloquean al usuario por 15 minutos; (d) cookie expira correctamente a las 8 horas.
- **Depende de:** T5.

#### T7 — Middleware de autorización por rol

- **Descripción:** dependencia FastAPI `require_role(roles: list)` que extrae el JWT de la cookie, valida la sesión, carga el usuario y verifica que el rol esté permitido.
- **Archivos afectados:** `apps/api/src/core/deps.py`.
- **Criterio de done:** request sin cookie retorna 401, request con cookie pero rol insuficiente retorna 403, request con rol correcto pasa y `current_user` está disponible en el handler.
- **Depende de:** T6.

#### T8 — Servicio de auditoría (audit_log)

- **Descripción:** servicio que registra un evento en `audit_log` con la información de la operación y el usuario actual. Se invoca explícitamente desde los services que modifican datos (no es un trigger SQL porque necesita acceso al usuario de aplicación).
- **Archivos afectados:** `apps/api/src/auditing/logger.py`, `apps/api/src/repositories/audit.py`.
- **Criterio de done:** un cambio de estado de producto deja un registro en audit_log con `tabla_afectada='productos'`, `accion='UPDATE'`, `valor_anterior` y `valor_nuevo` correctos, y el `usuario_id` del admin que ejecutó.
- **Depende de:** T7.

#### T9 — CRUD de productos

- **Descripción:** endpoints `GET /api/productos`, `GET /api/productos/{id}`, `PATCH /api/productos/{id}`, `PATCH /api/productos/{id}/estado`. Listado con filtros y paginación. Cada modificación dispara entrada en audit_log.
- **Archivos afectados:** `apps/api/src/routers/productos.py`, `apps/api/src/services/productos.py`.
- **Criterio de done:** todos los flujos probados con tests de integración. Activar/desactivar producto queda registrado en audit_log.
- **Depende de:** T8.

#### T10 — Cliente Cloudflare R2 y upload de PDFs

- **Descripción:** servicio que sube archivos PDF al bucket R2 con nombre único (UUID), retorna la URL pública o firmada según corresponda, y genera URLs firmadas temporales para descarga desde panel.
- **Archivos afectados:** `apps/api/src/storage/r2_client.py`, `apps/api/src/services/storage.py`.
- **Criterio de done:** un PDF subido vía servicio es accesible mediante URL firmada por exactamente 5 minutos y luego retorna 403.
- **Depende de:** T7.

#### T11 — CRUD de prospectos con upload

- **Descripción:** endpoint multipart `POST /api/prospectos` que recibe PDF + metadata, sube a R2 y crea registro en `prospectos` en estado `en_revision`. Endpoint `PATCH /api/prospectos/{id}/activar` que ejecuta transacción atómica: marca el prospecto como `vigente`, marca el anterior del mismo producto + `tipo_audiencia` como `reemplazado` (si existía), actualiza `producto_prospectos` y `productos.tiene_prospecto=TRUE`.
- **Archivos afectados:** `apps/api/src/routers/prospectos.py`, `apps/api/src/services/prospectos.py`.
- **Criterio de done:** (a) upload de PDF válido crea registro y archivo en R2; (b) upload de archivo no-PDF retorna 400; (c) activación de prospecto pasa el anterior a `reemplazado` en una sola transacción atómica (verificado con test que aborta a mitad y verifica que ningún cambio se persistió); (d) la regla de "máximo dos vigentes por producto, uno por audiencia" se enforza correctamente.
- **Depende de:** T9, T10.

#### T12 — Resolución pública GTIN → prospectos

- **Descripción:** endpoint interno `GET /api/internal/prospectos/by-gtin/{gtin}` protegido por header secreto. Valida formato GTIN (14 dígitos), busca el producto, evalúa estado, devuelve estructura completa para que el SSR de Next.js renderice la página.
- **Archivos afectados:** `apps/api/src/routers/internal.py`, `apps/api/src/services/resolver.py`.
- **Criterio de done:** (a) GTIN válido de producto activo con prospecto único retorna `{ producto, prospectos: [{ tipo_audiencia: 'unico', url_archivo }] }`; (b) producto con dos prospectos retorna ambos; (c) producto inactivo retorna `{ error: 'inactivo' }`; (d) GTIN inexistente retorna `{ error: 'no_encontrado' }`; (e) producto activo sin prospecto vigente retorna `{ error: 'sin_prospecto' }`; (f) sin header `X-Internal-Token` retorna 403.
- **Depende de:** T11.

#### T13 — Endpoint de audit_log

- **Descripción:** `GET /api/audit-log` con filtros por tabla, registro, usuario, rango de fechas. Solo rol admin.
- **Archivos afectados:** `apps/api/src/routers/audit.py`, `apps/api/src/services/audit.py`.
- **Criterio de done:** filtros funcionan, paginación funciona, intento de POST/PUT/DELETE a este endpoint retorna 405.
- **Depende de:** T8.

#### T14 — Script de migración desde Excel

- **Descripción:** script Python que lee `BD_productos_v2.xlsx`, normaliza productos multi-droga (resolviendo el patrón de filas huérfanas), crea registros en `principios_activos`, `productos`, `producto_principios`, `producto_materiales_packaging` y `gtin_registro` (con GTINs placeholders si no se tienen los reales aún). Idempotente: ejecutarlo dos veces no duplica datos.
- **Archivos afectados:** `apps/api/scripts/migrar_excel.py`.
- **Criterio de done:** (a) ejecución sobre DB limpia carga los 168 registros del Excel, normalizando los multi-droga correctamente (verificado contando filas en `producto_principios`); (b) segunda ejecución sobre la misma DB no genera duplicados ni errores; (c) productos en estado "en proceso" del Excel son ignorados; (d) productos de licitación y oncológicos quedan registrados con su `canal` y `tiene_prospecto=FALSE` correspondiente.
- **Depende de:** T4.

### FASE 2 — Frontend público (Semanas 5-6)

#### T15 — Setup Next.js + Tailwind + design tokens

- **Descripción:** app Next.js inicial con App Router, TypeScript, Tailwind configurado con los tokens de la Sección 5.
- **Archivos afectados:** `apps/web/tailwind.config.ts`, `apps/web/app/layout.tsx`, `apps/web/styles/globals.css`, `apps/web/next.config.js`.
- **Criterio de done:** página de prueba renderiza con los colores corporativos de Vent3 aplicados correctamente.
- **Depende de:** T2.

#### T16 — Componentes UI base

- **Descripción:** los 8 componentes listados en la Sección 5B.
- **Archivos afectados:** `apps/web/components/ui/*.tsx`.
- **Criterio de done:** una página `/dev/components` (solo en desarrollo) renderiza los 8 componentes con sus variantes.
- **Depende de:** T15.

#### T17 — Cliente HTTP del frontend

- **Descripción:** wrapper sobre `fetch` con manejo de cookies, errores, redirección a login en 401, y tipos generados desde el contrato OpenAPI.
- **Archivos afectados:** `apps/web/lib/api-client.ts`.
- **Criterio de done:** una llamada autenticada que recibe 401 redirige a `/admin/login` automáticamente.
- **Depende de:** T16.

#### T18 — Página pública de prospecto (resolver del QR)

- **Descripción:** ruta `app/01/[gtin]/page.tsx` con Server-Side Rendering. En el servidor consulta `/api/internal/prospectos/by-gtin/{gtin}` con el header secreto, evalúa el resultado y renderiza el HTML apropiado: PDF embebido para prospecto único, landing de selección para dos prospectos, o página de error con el mensaje correcto según el caso.
- **Archivos afectados:** `apps/web/app/01/[gtin]/page.tsx`, `apps/web/components/prospecto/PDFViewer.tsx`, `apps/web/components/prospecto/SelectorAudiencia.tsx`, `apps/web/components/prospecto/ErrorPage.tsx`.
- **Criterio de done:** (a) test E2E que escanea (simula HTTP GET) un GTIN válido carga el PDF en menos de 2 segundos; (b) GTIN inexistente muestra página 404 informativa; (c) producto con dos prospectos muestra correctamente el selector y al elegir un perfil sirve el PDF correcto; (d) la página funciona en Chrome Android y Safari iOS (probado en BrowserStack o dispositivos reales).
- **Depende de:** T12, T17.

### FASE 3 — Panel admin (Semanas 7-8)

#### T19 — Login del admin

- **Descripción:** ruta `app/admin/login/page.tsx` con formulario email + password. POST a `/api/auth/login`. Manejo de errores y bloqueo temporal.
- **Archivos afectados:** `apps/web/app/admin/login/page.tsx`.
- **Criterio de done:** login exitoso redirige al dashboard; login fallido muestra mensaje genérico; tras 5 intentos fallidos muestra mensaje de cuenta bloqueada con tiempo restante.
- **Depende de:** T17.

#### T20 — Dashboard de productos

- **Descripción:** ruta `app/admin/page.tsx` con listado paginado y filtrable de productos (por estado, canal, búsqueda por nombre). Cada fila muestra: código interno, nombre, presentación, estado del producto, estado del prospecto, acciones.
- **Archivos afectados:** `apps/web/app/admin/page.tsx`, `apps/web/components/admin/ProductTable.tsx`.
- **Criterio de done:** admin puede ver, filtrar y navegar productos. Click en una fila abre el detalle.
- **Depende de:** T19.

#### T21 — Detalle de producto y gestión de prospectos

- **Descripción:** ruta `app/admin/productos/[id]/page.tsx`. Muestra ficha completa del producto, listado de prospectos asociados (vigentes y reemplazados), botón para subir nuevo PDF, botón para activar/desactivar producto.
- **Archivos afectados:** `apps/web/app/admin/productos/[id]/page.tsx`, `apps/web/components/admin/UploadProspecto.tsx`.
- **Criterio de done:** admin puede subir un PDF nuevo desde la UI, completar metadata (código, versión, tipo de audiencia), activarlo, y ver el reemplazo automático del anterior.
- **Depende de:** T20.

#### T22 — Vista de audit log

- **Descripción:** ruta `app/admin/auditoria/page.tsx`. Listado paginado de eventos con filtros por tabla, usuario, rango de fechas.
- **Archivos afectados:** `apps/web/app/admin/auditoria/page.tsx`.
- **Criterio de done:** admin puede filtrar y revisar el historial de cambios del sistema.
- **Depende de:** T20.

### FASE 4 — Sitio institucional (Semana 9)

#### T23 — Páginas institucionales

- **Descripción:** home con propuesta de valor del laboratorio, sección "nosotros", listado informativo de líneas de productos (no el resolver de prospecto), página de contacto con formulario.
- **Archivos afectados:** `apps/web/app/(public)/page.tsx`, `apps/web/app/(public)/nosotros/page.tsx`, `apps/web/app/(public)/productos/page.tsx`, `apps/web/app/(public)/contacto/page.tsx`.
- **Criterio de done:** sitio responde correctamente en mobile y desktop, todas las páginas tienen meta tags SEO completos, performance Lighthouse mobile ≥ 90.
- **Depende de:** T16.

#### T24 — SEO, metadata y accesibilidad

- **Descripción:** Open Graph tags, sitemap.xml, robots.txt, validación de accesibilidad WCAG 2.1 AA en las páginas públicas, especialmente en la del prospecto.
- **Archivos afectados:** `apps/web/app/sitemap.ts`, `apps/web/app/robots.ts`, `apps/web/app/layout.tsx`.
- **Criterio de done:** auditoría de accesibilidad con axe-core pasa sin issues críticos, sitemap incluido en Google Search Console.
- **Depende de:** T23.

### FASE 5 — Operativa GS1 y entrega (Semana 10)

#### T25 — Generación de QRs en portal GS1

- **Descripción:** ingresar al portal de GS1 Argentina, responder el pop-up de clasificación ANMAT, para cada GTIN activo de Vent3 generar el QR Datamatrix usando opción "Dominio propio" con dominio `www.vent3.com.ar`, descargar imágenes, guardar en bucket de assets de packaging del laboratorio. Actualizar `gtin_registro.url_digital_link` y `qr_generado=TRUE` en la DB.
- **Archivos afectados:** ninguno de código. Tarea operativa.
- **Criterio de done:** todos los GTINs de productos activos de canal farmacia tienen su QR generado y descargado.
- **Depende de:** T18.

#### T26 — Validación de lectura con GS1

- **Descripción:** envío de imágenes de estuches al Servicio de Calidad de Lectura de GS1 (opción 1 del FAQ). Tras aprobación, marcar `validado_gs1=TRUE` en la DB.
- **Archivos afectados:** ninguno de código. Tarea operativa coordinada con Asuntos Regulatorios.
- **Criterio de done:** GS1 emite respuesta favorable para todos los productos en alcance.
- **Depende de:** T25.

#### T27 — Pruebas de aceptación final

- **Descripción:** ejecutar el checklist completo de criterios de aceptación de SPEC §10 con producción real: cada producto activo del MVP escaneado desde un celular real muestra el prospecto correctamente en menos de 2 segundos.
- **Archivos afectados:** ninguno. Documentar resultados en `docs/aceptacion/` con capturas.
- **Criterio de done:** los 11 ítems del checklist de SPEC §10 marcados como completos.
- **Depende de:** T26, T22.

#### T28 — Entrega y handoff

- **Descripción:** documentación de operación (cómo subir un prospecto, cómo desactivar un producto, qué hacer si un QR no escanea), capacitación al área de Asuntos Regulatorios, entrega formal al laboratorio.
- **Archivos afectados:** `docs/operacion/manual_admin.md`, `docs/operacion/troubleshooting.md`.
- **Criterio de done:** Asuntos Regulatorios firma conformidad de entrega; los QRs están aprobados para impresión en packaging.
- **Depende de:** T27.

---

## SECCIÓN 5 — DESIGN TOKENS Y COMPONENTES UI BASE

### A) Configuración de Tailwind

```ts
// apps/web/tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'vent3-primary': '#0B5394',      // Azul corporativo (a confirmar con identidad de marca)
        'vent3-secondary': '#3D85C6',
        'vent3-accent': '#E69138',
        'vent3-bg': '#FFFFFF',
        'vent3-surface': '#F5F7FA',
        'vent3-text-primary': '#1A1A1A',
        'vent3-text-secondary': '#5F6368',
        'vent3-border': '#D0D7DE',
        'vent3-success': '#1A8754',
        'vent3-warning': '#F0A020',
        'vent3-danger': '#C72424',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Source Serif Pro', 'Georgia', 'serif'],
      },
      maxWidth: {
        'prospecto': '900px',  // Ancho óptimo para lectura del PDF en desktop
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};

export default config;
```

**Nota sobre colores:** los valores actuales son placeholder. Una vez definida la nueva identidad visual del laboratorio (parte del rediseño del sitio institucional), se reemplazan estos tokens y todas las páginas heredan el cambio automáticamente.

### B) Componentes atómicos

| # | Nombre | Props principales | Pantalla donde se usa primero |
|---|---|---|---|
| 1 | `<Button />` | `variant: 'primary' \| 'secondary' \| 'ghost' \| 'danger'`, `size?: 'sm' \| 'md' \| 'lg'`, `loading?: boolean` | `/admin/login` |
| 2 | `<Input />` | `label: string`, `type: 'text' \| 'email' \| 'password' \| 'file'`, `error?: string`, `helperText?: string` | `/admin/login` |
| 3 | `<Select />` | `label: string`, `options: { value, label }[]`, `value`, `onChange`, `error?: string` | `/admin/productos/[id]` |
| 4 | `<Table />` | `columns: ColumnDef[]`, `data: T[]`, `loading?: boolean`, `onRowClick?: (row) => void` | `/admin` |
| 5 | `<Badge />` | `variant: 'success' \| 'warning' \| 'danger' \| 'neutral'`, `label: string` | `/admin` (estados de producto/prospecto) |
| 6 | `<PDFViewer />` | `url: string`, `fileName?: string`, `allowDownload?: boolean` | `/01/[gtin]` |
| 7 | `<SelectorAudiencia />` | `onSelect: (audiencia: 'publico' \| 'profesional') => void` | `/01/[gtin]` (caso dos prospectos) |
| 8 | `<Toast />` | `type: 'success' \| 'error' \| 'info'`, `message: string`, `duration?: number` | transversal |

---

## SECCIÓN 6 — DECISIONES ARQUITECTÓNICAS

**DECISIÓN:** Backend en FastAPI (Python) en lugar de Node.js/Express.
**Alternativa descartada:** Node.js + Express en stack JavaScript unificado.
**Justificación:** FastAPI ofrece documentación OpenAPI automática (que se aprovecha para generar tipos del frontend), tipado fuerte con Pydantic v2, rendimiento async nativo, y alinea con el ecosistema Python que el laboratorio puede aprovechar en el futuro para análisis de datos sobre la misma base. El costo de tener dos lenguajes en el monorepo se mitiga con la generación automática de tipos vía OpenAPI.

**DECISIÓN:** Una única URL en el QR con landing page inteligente para productos con dos versiones de prospecto, en lugar de dos QRs separados.
**Alternativa descartada:** generar dos QRs distintos usando el AI 240 (variante) del estándar GS1, uno con `?240=PUBLICO` y otro con `?240=PROFESIONAL`.
**Justificación:** los QRs impresos en packaging son permanentes y costosos de modificar. Mantener una sola URL por producto preserva esta permanencia y simplifica la operación. La selección de audiencia se resuelve en el servidor con una pantalla intermedia que no requiere ninguna identificación del usuario. Esta decisión está alineada con la opción A consultada al equipo en fase de diseño y confirmada por GS1 como válida dentro del estándar.

**DECISIÓN:** Dominio principal `www.vent3.com.ar` para el resolver, no un subdominio dedicado como `prospectos.vent3.com.ar`.
**Alternativa descartada:** subdominio dedicado para aislar el portal de prospectos del sitio institucional.
**Justificación:** la URL del QR es permanente una vez impresa. Cualquier migración futura entre dominios obligaría a reimprimir packaging. El uso del dominio principal también refuerza la confianza del usuario que escanea (reconoce la marca en la barra del navegador), y Next.js permite cohabitar perfectamente sitio institucional y resolver de QR en el mismo proyecto.

**DECISIÓN:** Autenticación del admin mediante JWT en cookie httpOnly de 8 horas.
**Alternativa descartada:** JWT en localStorage o sesiones server-side con tabla `sessions`.
**Justificación:** la cookie httpOnly elimina el vector XSS sobre el token, no requiere persistencia adicional en DB (a diferencia de sesiones server-side), y permite logout simple (basta expirar del lado del cliente). El refresh token se incorporará si en el futuro hay clientes externos que justifiquen sesiones largas.

**DECISIÓN:** PostgreSQL como única base de datos, sin caché separado tipo Redis en el MVP.
**Alternativa descartada:** capa de caché Redis para acelerar resoluciones de GTIN.
**Justificación:** el volumen de tráfico esperado del MVP (decenas a cientos de escaneos por día por producto activo) es perfectamente absorbible por PostgreSQL con índices correctos (especialmente `idx_gtin_lookup`). Sumar Redis introduce complejidad operativa, otro componente que monitorear y otro punto de falla, sin beneficio mensurable en este volumen. Se reevaluará si el tráfico crece significativamente.

**DECISIÓN:** Cloudflare R2 como storage de PDFs, no Supabase Storage ni AWS S3.
**Alternativa descartada:** Supabase Storage (integrado con el ecosistema Postgres de Supabase) o AWS S3.
**Justificación:** R2 ofrece compatibilidad S3, costos de egress cero (los PDFs se descargan muchas veces, esto es relevante), CDN global integrado de Cloudflare, y tier gratuito generoso. Supabase Storage habría sido válido si usáramos Supabase como BaaS completo, pero el proyecto usa Railway para Postgres y FastAPI por separado.

**DECISIÓN:** Audit log inmutable a nivel de base de datos, no solo a nivel de aplicación.
**Alternativa descartada:** depender únicamente de la lógica de la aplicación para no permitir modificaciones.
**Justificación:** ANMAT es un ente regulador y el audit log es la respuesta del sistema ante una eventual inspección. Una protección solo a nivel de aplicación puede ser bypaseada (bug, acceso directo a DB, error de configuración). El trigger SQL + permisos de DB que niegan UPDATE/DELETE al rol de aplicación garantizan que ni siquiera un administrador del sistema pueda alterar el histórico sin acceso directo de superusuario a la base.

**DECISIÓN:** UUIDs como clave primaria en todas las tablas (no enteros autoincrementales).
**Alternativa descartada:** SERIAL/BIGSERIAL como PKs.
**Justificación:** facilita la integración con sistemas externos, evita colisiones si en el futuro se consolidan datos de múltiples ambientes, y oculta el volumen de datos del sistema (un atacante no puede inferir cuántos productos hay viendo IDs secuenciales). El costo de almacenamiento extra (UUID = 16 bytes vs SERIAL = 4 bytes) es irrelevante para el volumen de este sistema.

**DECISIÓN:** Migración desde Excel como script one-shot, no como sincronización continua.
**Alternativa descartada:** mantener el Excel como fuente de verdad y sincronizar periódicamente.
**Justificación:** el Excel es el problema que el sistema viene a resolver. Mantener sincronización implicaría perpetuar la situación actual donde Excel sigue siendo el sistema operativo de facto. La migración one-shot fuerza la transición: tras la migración, todos los cambios se hacen en el sistema y el Excel queda como archivo histórico.

**DECISIÓN:** Header secreto `X-Internal-Token` para proteger el endpoint de resolución interno, en lugar de IP whitelist.
**Alternativa descartada:** restringir `/api/internal/*` por IP del servidor de Next.js.
**Justificación:** la IP del servidor de Vercel (donde corre el SSR de Next.js) no es estable. El header secreto compartido vía variable de entorno entre Vercel y Railway es estable, fácil de rotar y suficiente para impedir consultas directas al endpoint interno desde el navegador o herramientas externas.
