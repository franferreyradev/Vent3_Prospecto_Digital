# TASK.md — Prospecto Digital Vent3

> **Instrucciones de uso:**
> Este documento es la handoff note del proyecto. Al iniciar cada sesión de trabajo con Claude, pegá este archivo como primer mensaje para restaurar el contexto completo del estado actual. Al terminar cada sesión, actualizá las secciones ESTADO ACTUAL y LOG antes de cerrar.

---

## ESTADO ACTUAL

**Tarea en progreso:** Ninguna — T7+T8 completadas.
**Bloqueantes activos:** Ninguno.
**Última sesión:** 29 de junio de 2026 — T7+T8 autorización por rol y servicio de auditoría completados.

---

## PRÓXIMA TAREA

**T9 — CRUD de productos**

Endpoints de gestión de productos: crear, listar, obtener, activar/desactivar.
Todos protegidos con `Depends(require_admin)` según el patrón documentado en `tests/test_autorizacion.py`.

Referencia completa en `docs/PLAN.md § Sección 3 · T9`.

---

## TAREAS PENDIENTES

### FASE 0 — Fundación

- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026
- [x] **T2** — Contratación de infraestructura ✅ · 29 jun 2026
- [x] **T3** — Schema SQL inicial y migraciones Alembic ✅ · 29 jun 2026
- [x] **T4** — Modelos SQLAlchemy y repositorios base ✅ · 29 jun 2026
- [x] **T5** — Schemas Pydantic y generación de tipos TypeScript ✅ · 29 jun 2026

### FASE 1 — Backend core

- [x] **T6** — Auth: login del admin + JWT en cookie httpOnly ✅ · 29 jun 2026
- [x] **T7** — Middleware de autorización por rol ✅ · 29 jun 2026
- [x] **T8** — Servicio de auditoría (audit_log) ✅ · 29 jun 2026
- [ ] **T9** — CRUD de productos
- [ ] **T10** — Cliente Cloudflare R2 y upload de PDFs
- [ ] **T11** — CRUD de prospectos con upload y activación
- [ ] **T12** — Resolución pública GTIN → prospectos
- [ ] **T13** — Endpoint de audit_log
- [ ] **T14** — Script de migración desde Excel

### FASE 2 — Frontend público

- [ ] **T15** — Setup Next.js + Tailwind + design tokens
- [ ] **T16** — Componentes UI base
- [ ] **T17** — Cliente HTTP del frontend
- [ ] **T18** — Página pública de prospecto (resolver del QR)

### FASE 3 — Panel admin

- [ ] **T19** — Login del admin
- [ ] **T20** — Dashboard de productos
- [ ] **T21** — Detalle de producto y gestión de prospectos
- [ ] **T22** — Vista de audit log

### FASE 4 — Sitio institucional

- [ ] **T23** — Páginas institucionales (home, nosotros, productos, contacto)
- [ ] **T24** — SEO, metadata y accesibilidad

### FASE 5 — Operativa GS1 y entrega

- [ ] **T25** — Generación de QRs en portal GS1 Argentina
- [ ] **T26** — Validación de lectura con Servicio de Calidad GS1
- [ ] **T27** — Pruebas de aceptación final (checklist SPEC §10)
- [ ] **T28** — Entrega y handoff a Asuntos Regulatorios

---

## COMPLETADAS

- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026
- [x] **T2** — Contratación de infraestructura ✅ · 29 jun 2026
- [x] **T3** — Schema SQL inicial y migraciones Alembic ✅ · 29 jun 2026
- [x] **T4** — Modelos SQLAlchemy 2.0 y repositorios base ✅ · 29 jun 2026
- [x] **T5** — Schemas Pydantic y generación de tipos TypeScript ✅ · 29 jun 2026
- [x] **T6** — Auth: login del admin + JWT en cookie httpOnly ✅ · 29 jun 2026
- [x] **T7** — Middleware de autorización por rol ✅ · 29 jun 2026
- [x] **T8** — Servicio de auditoría (audit_log) ✅ · 29 jun 2026

---

## CONTEXTO RÁPIDO DEL PROYECTO

| Item | Valor |
|---|---|
| **Proyecto** | Prospecto Digital ANMAT — Laboratorio Vent3, Córdoba |
| **Deadline regulatorio** | 15 de noviembre de 2026 |
| **Normativa** | ANMAT Disposición N° 2891/2026 + estándar GS1 Digital Link |
| **Dominio resolver** | `https://www.vent3.com.ar/01/[GTIN-14-dígitos]` |
| **Backend** | FastAPI (Python 3.12) + PostgreSQL · deploy en Railway |
| **Frontend** | Next.js (App Router, SSR) · deploy en Vercel |
| **Storage PDFs** | Cloudflare R2 |
| **Base de datos** | PostgreSQL · 9 tablas · diseño aprobado en BD_Diseño_v2.docx |
| **Auth** | JWT en cookie httpOnly · bcrypt costo 12 · 1 usuario admin MVP |
| **Documentos de referencia** | docs/SPEC.md, docs/PLAN.md, docs/BD_Diseño_v2.docx |

### Decisiones críticas que no deben revertirse

- La URL `/01/[gtin]` es el estándar GS1 Digital Link. No agregar prefijos como `/productos/`.
- Un producto con dos versiones de prospecto usa **una sola URL** con landing de selección de perfil (Opción A). No dos QRs.
- Productos de licitación y oncológicos (línea MU-) están **fuera del scope del MVP**. Existen en la DB pero no generan flujo activo.
- El `audit_log` es **inmutable a nivel de base de datos** (trigger SQL + permisos de rol), no solo a nivel de aplicación.
- El panel de **gestión de múltiples usuarios es post-MVP**. En MVP solo existe un usuario admin.

---

## NOTAS DE SESIÓN

**[T1 · 25 jun 2026]** PLAN.md, SPEC.md y TASK.md estaban en la raíz del repo al iniciar T1 — fueron movidos a `docs/` para alinear con la estructura definida en PLAN.md §1.

**[T1 · 25 jun 2026]** `.env.example` no pudo ser creado automáticamente por restricciones de permisos del agente sobre archivos `.env*`. Crearlo manualmente — contenido en la sección `.env.example` del README.md.

**[T1 · 25 jun 2026]** `tests/conftest.py` setea env vars a nivel de módulo (fuera de fixture) para que `Settings()` de pydantic-settings pueda instanciarse al momento del import de `config.py`. Patrón obligatorio en todos los tests de la API.

**[T1 · 25 jun 2026]** Puerto 5432 ocupado por otro proyecto en la máquina de desarrollo (`alcosto-db-1`). `infra/docker-compose.yml` usa puerto 5433 para vent3-db. `DATABASE_URL` en `apps/api/.env` debe apuntar a `localhost:5433`.

**[T1 · 25 jun 2026]** `Settings` en `config.py` necesita `extra="ignore"` en ConfigDict porque el `.env` contiene variables del frontend (`NEXT_PUBLIC_API_URL`) que pydantic v2 rechaza por defecto si no están declaradas en el modelo.

**[T2 · 29 jun 2026]** Infraestructura de producción operativa: Railway (API + PostgreSQL), Vercel (frontend), Cloudflare R2 (bucket vent3-prospectos). Dominios `api.vent3.com.ar` y `www.vent3.com.ar` activos con SSL. Checks C1-C4 verdes.

**[T2 · 29 jun 2026]** Los atributos de `Settings` en `config.py` son UPPERCASE (`s.R2_ACCOUNT_ID`, no `s.r2_account_id`). Al escribir scripts o checks que usen `settings`, usar el nombre exacto de la variable de entorno.

**[T2 · 29 jun 2026]** `.env.example` no pudo ser modificado automáticamente por restricciones del agente. Las secciones nuevas (comentarios DATABASE_URL local/Railway, R2_PUBLIC_URL, y bloque NEXT.JS) quedaron pendientes de agregar manualmente.

**[T3 · 29 jun 2026]** Railway CLI instalado pero no linkeado al proyecto (no hay proyecto linkeado en la máquina). Las migraciones se aplican en Railway via `alembic upgrade head` en el `startCommand` de `railway.toml`. Esto corre en cada deploy — es aceptable para el MVP ya que las migraciones son idempotentes. Para futura granularidad, linkear con `railway link` y usar `railway run alembic upgrade head` de forma explícita.

**[T3 · 29 jun 2026]** `passlib[bcrypt]` (1.7.x) es incompatible con `bcrypt>=4.x` — la función `detect_wrap_bug` falla al inicializar el backend. La migración 004 usa `bcrypt` directamente (sin passlib) para hashear la contraseña del admin. Para T6 (auth), considerar el mismo patrón o actualizar a `bcrypt-compat` / `argon2-cffi`.

**[T3 · 29 jun 2026]** pytest-asyncio 1.4.0 (auto mode) usa un event loop por test (function scope). Los fixtures de conexión asyncpg deben ser function-scoped para evitar "Future attached to a different loop". Ver `tests/test_schema.py`.

**[T3 · 29 jun 2026]** `password_hash VARCHAR(60)` es exactamente el largo de un hash bcrypt estándar (7 prefijo + 22 salt + 31 hash = 60 chars). Los tests que necesiten insertar usuarios dummy deben generar un hash real con `bcrypt.hashpw(b"test", bcrypt.gensalt(rounds=4))`.

**[T3 · 29 jun 2026]** El rol `vent3_app` no existe en Railway (usa el rol por defecto de PostgreSQL). El bloque REVOKE en la migración 003 es condicional (`IF EXISTS`) — no falla si el rol no existe. La inmutabilidad de audit_log está garantizada por el trigger `trg_audit_inmutable`, independientemente del rol.

**[T4 · 29 jun 2026]** FastAPI >= 0.93: usar `lifespan` (asynccontextmanager) en lugar del deprecated `on_event`. Ver `apps/api/src/main.py`.

**[T4 · 29 jun 2026]** ENUMs de PostgreSQL en SQLAlchemy ORM: deben usar `postgresql.ENUM(..., name='enum_name', create_type=False)`. Sin `create_type=False`, SQLAlchemy intenta `CREATE TYPE` al crear tablas y falla porque los ENUMs ya existen en la DB. Todos los ENUMs están en `apps/api/src/models/enums.py`.

**[T4 · 29 jun 2026]** `ip_origen` en `audit_log` es tipo `INET` en PostgreSQL (no VARCHAR). Requiere `postgresql.INET` en el modelo ORM para que `alembic check` no reporte diferencias de tipo.

**[T4 · 29 jun 2026]** `alembic check` con modelos vs schema: los índices creados por SQL raw en las migraciones (no declarados en los modelos) generan falsos positivos de "Detected removed index". Solución: `include_object` en `alembic/env.py` que ignora índices que existen solo en DB. Ver `apps/api/alembic/env.py`.

**[T4 · 29 jun 2026]** `expire_on_commit=False` es CRÍTICO en `AsyncSessionLocal`. Sin esto, acceder a atributos de un objeto ORM después del commit genera `DetachedInstanceError` (lazy load imposible en async). Ver `apps/api/src/core/db.py`.

**[T4 · 29 jun 2026]** En tests con `AsyncSession` y triggers de DB: después de `session.flush()`, el objeto Python en memoria no refleja los cambios del trigger. Llamar `await session.refresh(objeto)` explícitamente para recargar los campos actualizados por triggers (ej: `nombre_normalizado` en `principios_activos`).

**[T4 · 29 jun 2026]** `selectinload(Relacion).where(...)` NO existe en SQLAlchemy. Para cargar relaciones con filtros usar `with_loader_criteria` o filtrar en Python post-carga. Ver `apps/api/src/repositories/productos.py`.

**[T4 · 29 jun 2026]** Tests acumulados al cierre de T4: **18/18 verdes** (1 T1 + 7 T3 + 10 T4).

**[T5 · 29 jun 2026]** `pydantic[email]` (email-validator) no estaba en el `pyproject.toml`. Se agregó como dependencia al usar `EmailStr` en `LoginRequest`. Ejecutar `uv sync` al hacer checkout fresco.

**[T5 · 29 jun 2026]** Los computed_fields (`tipo_landing`, `tiene_dos_prospectos`) de `ResolverResponse` requieren Pydantic v2 (ya instalado). En Pydantic v1 no existe `@computed_field`. No hay restricción adicional de versión más allá de `pydantic>=2.0` que ya estaba declarada.

**[T5 · 29 jun 2026]** `packages/contracts/src/api.ts` está en `.gitignore` como archivo generado (correcto). No se commitea. Se genera corriendo `npm run generate` desde `packages/contracts/` con la API corriendo en `:8000`.

**[T5 · 29 jun 2026]** El OpenAPI de FastAPI solo incluye schemas que están wired a endpoints con `response_model`. Para exponer todos los schemas antes de T6+, se sobrescribe `app.openapi()` en `main.py` con una función que inyecta los schemas en `components/schemas`. Los `$defs` anidados se extraen al nivel raíz antes de insertar.

**[T5 · 29 jun 2026]** Tests acumulados al cierre de T5: **11/11 verdes** (1 T1 + 10 T5 schemas). Los 17 tests de T3/T4 (DB integration) se skipean sin PostgreSQL local en `:5433` — comportamiento esperado.

**[T6 · 29 jun 2026]** `ENVIRONMENT: str = "production"` agregado a `Settings` con default producción. En tests, `conftest.py` setea `ENVIRONMENT=development` → `secure=False` en la cookie. En Railway setear `ENVIRONMENT=production` para activar `secure=True`. Sin este flag las cookies no se envían sobre HTTP en desarrollo local.

**[T6 · 29 jun 2026]** TC4 (lockout) usa un usuario temporal `lockout_tc4@vent3.test` creado y eliminado dentro del mismo test (try/finally). No usa el admin seed — el admin nunca se bloquea durante los tests. Patrón a replicar en futuros tests de lockout.

**[T6 · 29 jun 2026]** httpx 0.27+ depreca `cookies={}` per-request. Usar `client.cookies.set(key, value)` sobre la instancia del cliente. Ver `tests/test_auth.py` TC6, TC7, TC8.

**[T6 · 29 jun 2026]** python-jose funcionó correctamente con HS256 sin gotchas. `ExpiredSignatureError` es subclase de `JWTError` — atrapar `JWTError` es suficiente para cubrir ambos casos en `decodificar_token()`. Retorna `None` en cualquier error de validación.

**[T6 · 29 jun 2026]** Dependencias de auth disponibles en `src/core/deps.py`: `get_current_user` (verifica cookie + JWT + usuario activo), `require_admin` (verifica rol == 'admin'). Router de auth en `src/routers/auth.py` con prefix `/api/auth`.

**[T6 · 29 jun 2026]** Tests acumulados al cierre de T6: **13/13 verdes** (1 health + 10 schemas + 2 auth sin DB). 6 tests de auth requieren DB y skipean sin PostgreSQL — comportamiento esperado.

**[T7+T8 · 29 jun 2026]** `require_admin` ya existía en `src/core/deps.py` desde T6. T7 agrega 5 TCs dedicados en `test_autorizacion.py`. Patrón `Depends(require_admin)` documentado ahí.

**[T7+T8 · 29 jun 2026]** GOTCHA — event loop / NullPool: los tests que hacen requests ASGI a una app con el engine de módulo (`app` de `src/main.py`) fallan con "Future attached to a different loop" cuando corren secuencialmente con event loops function-scoped (pytest-asyncio 1.4.0). Fix en `test_autorizacion.py`: overridear `get_db` con `_get_db_nullpool` que usa `sqlalchemy.pool.NullPool`. Cada request crea su propia conexión — sin pool, sin conflicto de loops. Los tests de `test_auth.py` tienen este problema latente cuando se corre contra el dev DB; pasan correctamente contra el test DB (donde corren los 13 tests de T6).

**[T7+T8 · 29 jun 2026]** `AuditoriaService` en `src/services/auditoria.py`. Patrón: `AuditoriaService(session)` → `await service.registrar_cambio(...)`. El método NUNCA propaga excepción — loguea con `logger.error()` y retorna None silenciosamente. Esto es intencional: un fallo de auditoría no debe revertir la operación principal.

**[T7+T8 · 29 jun 2026]** TC5 de test_auditoria (inmutabilidad): usa `begin_nested()` (SAVEPOINT) para intentar el UPDATE dentro de un savepoint. Si el trigger lanza excepción, el savepoint se revierte automáticamente y la transacción exterior queda intacta. Sin esto, el `trans.rollback()` del fixture fallaría.

**[T7+T8 · 29 jun 2026]** Tests acumulados al cierre de T7+T8: **24/24 verdes** (13 anteriores + 5 T7 + 6 T8). Verificados contra el dev DB local (`vent3_db` en puerto 5433).

---
> Actualizar este archivo al finalizar cada sesión. Formato sugerido para COMPLETADAS:
> `- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026`
