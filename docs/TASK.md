# TASK.md — Prospecto Digital Vent3

> **Instrucciones de uso:**
> Este documento es la handoff note del proyecto. Al iniciar cada sesión de trabajo con Claude, pegá este archivo como primer mensaje para restaurar el contexto completo del estado actual. Al terminar cada sesión, actualizá las secciones ESTADO ACTUAL y LOG antes de cerrar.

---

## ESTADO ACTUAL

**Tarea en progreso:** Ninguna — T3 completada.
**Bloqueantes activos:** Ninguno.
**Última sesión:** 29 de junio de 2026 — T3 Schema SQL inicial y migraciones Alembic completada.

---

## PRÓXIMA TAREA

**T4 — Modelos SQLAlchemy y repositorios base**

Modelos ORM de las 9 tablas, sesión de DB con dependency injection, repositorios con métodos CRUD básicos.

Referencia completa en `docs/PLAN.md § Sección 4 · T4`.

---

## TAREAS PENDIENTES

### FASE 0 — Fundación

- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026
- [x] **T2** — Contratación de infraestructura ✅ · 29 jun 2026
- [x] **T3** — Schema SQL inicial y migraciones Alembic ✅ · 29 jun 2026
- [ ] **T4** — Modelos SQLAlchemy y repositorios base
- [ ] **T5** — Schemas Pydantic y generación de tipos TypeScript

### FASE 1 — Backend core

- [ ] **T6** — Auth: login del admin + JWT en cookie httpOnly
- [ ] **T7** — Middleware de autorización por rol
- [ ] **T8** — Servicio de auditoría (audit_log)
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

---
> Actualizar este archivo al finalizar cada sesión. Formato sugerido para COMPLETADAS:
> `- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026`
