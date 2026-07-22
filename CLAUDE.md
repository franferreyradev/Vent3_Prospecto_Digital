# CLAUDE.md — Vent3 Prospecto Digital

> Este archivo es leído automáticamente por Claude Code al iniciar cualquier sesión
> en este repositorio. Contiene las reglas, convenciones y contexto permanente del proyecto.
> No modificar sin revisar el impacto en todas las tareas pendientes.

---

## Identidad del proyecto

**Laboratorio Vent3 — Córdoba, Argentina**
Sistema de prospecto digital conforme a ANMAT Disposición N° 2891/2026 + estándar GS1 Digital Link.
El QR impreso en el packaging de cada medicamento apunta a `https://www.vent3.com.ar/01/[GTIN-14-dígitos]`
y muestra el prospecto vigente del producto.

**Deadline regulatorio inamovible: 15 de noviembre de 2026.**

---

## Documentos de referencia

Antes de iniciar cualquier tarea, consultar en este orden:

1. `docs/TASK.md` — estado actual del proyecto (qué tarea va ahora, qué está hecho).
2. `docs/PLAN.md` — arquitectura técnica, esquema SQL, endpoints, orden de tareas.
3. `docs/SPEC.md` — especificación funcional, actores, requerimientos, criterios de aceptación.
4. `docs/BD_Diseño_v2.docx` — diseño de base de datos aprobado (referencia conceptual).

**Si hay contradicción entre documentos:** SPEC.md prevalece sobre PLAN.md en lo funcional.
PLAN.md prevalece sobre CLAUDE.md en lo técnico. CLAUDE.md define reglas de proceso y convenciones.

---

## Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| Backend | FastAPI (Python 3.12) | Entry point: `apps/api/src/main.py` |
| ORM | SQLAlchemy 2.0 async | NO usar API 1.x (`session.query()`) |
| Migraciones | Alembic | Una migración por cambio de schema |
| Validación | Pydantic v2 | Usar `model_config = ConfigDict(...)`, no `class Config` |
| Dependencias Python | uv | `uv sync` para instalar, `uv add` para agregar |
| Frontend | Next.js 14 (App Router) + TypeScript | SSR para páginas públicas |
| Estilos | Tailwind CSS | Design tokens en `apps/web/tailwind.config.ts` |
| Base de datos | PostgreSQL 16 | Railway en producción, Docker en desarrollo local |
| Storage PDFs | Cloudflare R2 (compatible S3) | Egress gratuito, CDN Cloudflare |
| Auth | JWT en cookie httpOnly | 8 horas, bcrypt costo 12 |
| Tipos compartidos | OpenAPI → openapi-typescript | Generados en `packages/contracts/src/api.ts` |
| Hosting API | Railway | |
| Hosting Frontend | Vercel | |

---

## Reglas de desarrollo

### Base de datos

- **UUIDs en todas las PKs.** Nunca SERIAL ni BIGSERIAL.
- **Soft delete siempre.** Nunca `DELETE` en tablas de negocio. Usar campo `estado` o `activo`.
- **`audit_log` es append-only a nivel de DB.** El rol de aplicación (`vent3_app`) tiene solo `INSERT` y `SELECT`. Ningún código de aplicación intenta `UPDATE` o `DELETE` sobre esta tabla.
- **`updated_at` automático.** Toda tabla con `updated_at` tiene trigger `BEFORE UPDATE` que lo actualiza a `NOW()`. No actualizar desde la aplicación.
- **Migraciones versionadas.** Cada cambio de schema tiene su propia migración Alembic. Nunca modificar una migración ya aplicada en producción: crear una nueva.

### Backend (FastAPI / Python)

- **Pydantic v2:** `model_config = ConfigDict(from_attributes=True)`, `@field_validator` en lugar de `@validator`.
- **SQLAlchemy 2.0 async:** usar `AsyncSession`, `select()`, `await session.execute()`. Nunca `session.query()`.
- **Dependency injection:** toda dependencia de DB, auth y config se inyecta vía `Depends()`. No instanciar servicios directamente en los handlers.
- **Separación de capas estricta:** router → service → repository. La lógica de negocio vive en services. El acceso a DB vive en repositories. Los routers solo validan input/output.
- **Variables de entorno:** leer siempre desde `apps/api/src/core/config.py` (Settings). Nunca `os.environ.get()` directo en código de negocio.
- **Errores HTTP:** usar `HTTPException` con `status_code` y `detail` en español claro.

### Frontend (Next.js / TypeScript)

- **SSR obligatorio para páginas públicas** (`/01/[gtin]`). Estas páginas deben ser Server Components que resuelven el prospecto en el servidor antes de enviar HTML al cliente.
- **Tipos desde contratos:** usar siempre tipos de `@vent3/contracts`. Nunca tipar manualmente las respuestas de la API.
- **No usar `any`.** TypeScript strict activado. Si el tipo no existe en contratos, generarlos (`npm run contracts:generate`).
- **Componentes de servidor por default.** Marcar con `'use client'` solo cuando sea estrictamente necesario (interactividad, hooks de estado).

### Seguridad

- **Endpoint interno `/api/internal/*`** solo acepta requests con header `X-Internal-Token` válido. Este header lo agrega Next.js server-side. Nunca exponer este endpoint al navegador.
- **Contraseñas:** siempre bcrypt costo 12. Nunca loguear passwords ni hashes.
- **JWT:** firmado con `SECRET_KEY` del entorno. Expiración 8 horas. Nunca en localStorage.
- **Lockout:** 5 intentos fallidos de login bloquean la cuenta 15 minutos. Ver `usuarios.intentos_fallidos` y `usuarios.bloqueado_hasta`.

---

## Decisiones que NO se revierten

Estas decisiones están cerradas. Si durante el desarrollo surge una razón para cuestionarlas,
documentar el análisis en `docs/adr/` y consultar antes de cambiar cualquier cosa.

1. **URL del QR es `/01/[GTIN-14-dígitos]` directamente en `www.vent3.com.ar`.** No agregar prefijos como `/productos/`. Es el estándar GS1 Digital Link y las URLs impresas en packaging son permanentes.

2. **Una sola URL por producto, landing de selección de perfil** para los que tienen dos versiones de prospecto (público general / profesional de salud). No se generan dos QRs distintos usando AI 240.

3. **Dominio principal `www.vent3.com.ar`**, no subdominio. La permanencia del QR lo requiere.

4. **`audit_log` inmutable a nivel de base de datos**, no solo de aplicación. Trigger SQL + permisos de rol de DB.

5. **Productos de licitación y oncológicos (línea MU-) están fuera del MVP.** Existen en la DB pero no generan flujo activo. No implementar lógica especial para ellos hasta nueva instrucción de ANMAT.

6. ~~Panel de gestión de múltiples usuarios es post-MVP.~~ **Revertida el 22 jul 2026** (ver `docs/adr/003-gestion-usuarios-post-mvp.md`) — el MVP ya fue presentado, gestión de usuarios pasó a ser tarea activa (T-USUARIOS). Alta vía link de invitación de un solo uso, roles `admin`/`editor` habilitados; `lector` queda en el enum sin flujo de alta hasta que haya caso de uso concreto.

---

## Convenciones de Git

```
Ramas:     feat/t[N]-descripcion-corta
           docs/t[N]-descripcion
           fix/t[N]-descripcion

Commits:   feat: T[N] — descripción
           fix: T[N] — descripción
           docs: T[N] — descripción
           test: T[N] — descripción

Merge:     git merge --no-ff feat/t[N]-...
           (siempre --no-ff para preservar separación de tareas en git log)
```

**Flujo por tarea:**
1. `git checkout -b feat/tN-nombre`
2. Implementar hasta que criterio de done esté 100% cumplido
3. Tests en verde
4. Actualizar `docs/TASK.md` (completadas + notas de sesión)
5. Commit + push + merge a main con `--no-ff`
6. Borrar rama local

---

## Convenciones de tests

- **Backend:** pytest + httpx `AsyncClient`. Un archivo de tests por módulo en `apps/api/tests/`.
- **Naming:** `test_[accion]_[contexto]_[resultado_esperado]`. Ejemplo: `test_login_password_incorrecto_retorna_401`.
- **Cada test es independiente:** setup y teardown propios. No depender del orden de ejecución.
- **Los tests no mockean la DB** salvo casos extremos: usan la DB de test real (variable `TEST_DATABASE_URL`).
- **Criterio de merge:** 100% de tests acumulados en verde. Nunca mergear con tests rojos.

---

## Convenciones de nombres

| Elemento | Convención | Ejemplo |
|---|---|---|
| Tablas PostgreSQL | snake_case plural | `productos`, `audit_log` |
| Modelos SQLAlchemy | PascalCase singular | `Producto`, `AuditLog` |
| Schemas Pydantic | PascalCase + sufijo | `ProductoCreate`, `ProductoResponse` |
| Rutas FastAPI | snake_case con guiones | `/api/productos/{id}` |
| Archivos Python | snake_case | `productos.py`, `auth_service.py` |
| Componentes React | PascalCase | `PDFViewer.tsx`, `SelectorAudiencia.tsx` |
| Hooks React | camelCase con `use` | `useProductos.ts` |
| Variables de entorno | UPPER_SNAKE_CASE | `DATABASE_URL`, `SECRET_KEY` |

---

## Qué hacer ante bloqueos

Si durante la implementación de una tarea aparece un bloqueo no previsto:

1. **Documentarlo en `docs/TASK.md` §Notas de sesión** con el prefijo `[BLOQUEANTE]`.
2. **No improvisar soluciones que contradigan el PLAN.md o los ADRs** sin documentar el cambio.
3. **Si el bloqueo afecta la arquitectura**, crear un ADR en `docs/adr/` antes de cambiar rumbo.
4. **El deadline del 15 de noviembre es inamovible.** Ante duda entre la solución correcta y la solución que cumple el deadline: priorizar el deadline y documentar la deuda técnica.
