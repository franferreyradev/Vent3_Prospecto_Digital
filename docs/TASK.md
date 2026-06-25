# TASK.md — Prospecto Digital Vent3

> **Instrucciones de uso:**
> Este documento es la handoff note del proyecto. Al iniciar cada sesión de trabajo con Claude, pegá este archivo como primer mensaje para restaurar el contexto completo del estado actual. Al terminar cada sesión, actualizá las secciones ESTADO ACTUAL y LOG antes de cerrar.

---

## ESTADO ACTUAL

**Tarea en progreso:** Ninguna — T1 completada.
**Bloqueantes activos:** Ninguno.
**Última sesión:** 25 de junio de 2026 — T1 Setup del monorepo completado.

---

## PRÓXIMA TAREA

**T2 — Contratación de infraestructura**

Crear cuentas y proyectos en Railway (backend + PostgreSQL), Vercel (frontend) y Cloudflare R2 (storage).
Configurar dominios: apuntar `www.vent3.com.ar` a Vercel y `api.vent3.com.ar` a Railway.

Referencia completa en `docs/PLAN.md § Sección 4 · T2`.

---

## TAREAS PENDIENTES

### FASE 0 — Fundación

- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026
- [ ] **T2** — Contratación de infraestructura (Railway, Vercel, Cloudflare R2, DNS)
- [ ] **T3** — Schema SQL inicial y migraciones Alembic
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

---
> Actualizar este archivo al finalizar cada sesión. Formato sugerido para COMPLETADAS:
> `- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026`
