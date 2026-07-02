# TASK.md — Prospecto Digital Vent3

> **Instrucciones de uso:**
> Este documento es la handoff note del proyecto. Al iniciar cada sesión de trabajo con Claude, pegá este archivo como primer mensaje para restaurar el contexto completo del estado actual. Al terminar cada sesión, actualizá las secciones ESTADO ACTUAL y LOG antes de cerrar.

---

## ESTADO ACTUAL

**Tarea en progreso:** Ninguna — T12 completada.
**Bloqueantes activos:** Ninguno (ver nota sobre `test_auth.py` en Notas de sesión — preexistente, no bloquea T12).
**Última sesión:** 2 de julio de 2026 — T12 resolución pública GTIN → prospectos completado.

---

## PRÓXIMA TAREA

**T13 — Endpoint de audit_log**

Referencia completa en `docs/PLAN.md § Sección 3 · T13`.

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
- [x] **T9** — CRUD de productos ✅ · 2 jul 2026
- [x] **T10** — Cliente Cloudflare R2 y upload de PDFs ✅ · 2 jul 2026
- [x] **T11** — CRUD de prospectos con upload y activación ✅ · 2 jul 2026
- [x] **T12** — Resolución pública GTIN → prospectos ✅ · 2 jul 2026
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
- [x] **T9** — CRUD de productos ✅ · 2 jul 2026
- [x] **T10** — Cliente Cloudflare R2 y upload de PDFs ✅ · 2 jul 2026
- [x] **T11** — CRUD de prospectos con upload y activación ✅ · 2 jul 2026
- [x] **T12** — Resolución pública GTIN → prospectos ✅ · 2 jul 2026

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

**[T9 · 2 jul 2026]** Patrón NullPool de T7+T8 se reusó exactamente igual en `test_productos.py`, aplicado sobre la app real (`from src.main import app`) vía `app.dependency_overrides[get_db] = _get_db_nullpool` — así el fixture `auth_client` puede loguear contra `/api/auth/login` y reusar la cookie contra los endpoints de productos con la misma app. Funcionó sin ajustes: 10/10 TCs verdes.

**[T9 · 2 jul 2026]** `model_dump(exclude_none=True)` en Pydantic v2 se comportó como se esperaba: solo incluye las claves con valor no-`None` enviadas en el request, permitiendo el PATCH semántico sin pisar campos no enviados. Sin sorpresas.

**[T9 · 2 jul 2026]** GOTCHA nuevo — `session.refresh(producto)` sin `attribute_names` expira TODOS los atributos del objeto, incluidas relaciones ya eager-cargadas (`principios`). En AsyncSession eso dispara `MissingGreenlet` al serializar la respuesta porque el lazy-load implícito no puede correr fuera de un `await`. Fix: `await session.refresh(producto, attribute_names=["updated_at"])` — refresca solo la columna que necesitamos (la que toca el trigger `trg_updated_at_productos`) y no toca las relaciones ya cargadas.

**[T9 · 2 jul 2026]** GOTCHA — `ProductoDetalleResponse.principios` no puede poblarse con `model_validate(producto)` directo: `ProductoPrincipio` no tiene columna `nombre`, vive en `PrincipioActivo.nombre` vía la relación `principio`. Se agregó `selectinload(Producto.principios).selectinload(ProductoPrincipio.principio)` en `get_detalle_completo()` (repo) y se arma `PrincipioActivoEnProducto` a mano en el router (`_to_detalle_response`) mapeando `pp.principio.nombre`.

**[T9 · 2 jul 2026]** `audit_log` es append-only también contra `DELETE`, no solo `UPDATE` (el trigger bloquea ambos). El teardown de `productos_seed` en los tests intentaba borrar filas de `audit_log` generadas por los TCs de auditoría y explotaba con "audit_log es inmutable". Fix: el teardown solo borra `productos`; las filas de auditoría quedan (esperado, coherente con la regla de negocio).

**[T9 · 2 jul 2026]** [BLOQUEANTE] preexistente, no introducido por T9: `test_auth.py` tiene 2 TCs (`test_login_email_inexistente...`, `test_lockout_tras_cinco_intentos_fallidos`) que fallan con 422 en lugar de 401 al correr el suite completo contra la DB de test local (puerto 5433, container `vent3-db`). Confirmado con `git stash` que la falla existe también en `main` sin los cambios de T9 — es el mismo gotcha de event loop / DB que ya se documentó en T7+T8 (línea de arriba), simplemente se manifiesta distinto según el entorno de ejecución. No se tocó `test_auth.py` porque está fuera del alcance de T9. Suite completo al cierre: **55 passed, 2 failed (preexistentes)** — de los cuales 10/10 son los nuevos de T9.

**[T10 · 2 jul 2026]** DESVÍO de estructura documentado: el `session_prompt` de T10 pedía un paquete nuevo `src/storage/` (`r2_client.py` + `storage_service.py`). Se descartó esa opción a favor de PLAN.md §T10, que especifica `apps/api/src/services/storage.py` — consistente con el patrón `router → service → repository` ya establecido (`services/auditoria.py`, `services/productos.py`). El cliente boto3 quedó en `src/core/r2_client.py` (junto a `config.py`, `security.py`), no en un paquete `storage/` separado. Confirmado con el usuario antes de escribir código.

**[T10 · 2 jul 2026]** GOTCHA evitado, no nuevo: el snippet del `session_prompt` usaba `settings.r2_account_id` en minúsculas. Los atributos de `Settings` son UPPERCASE (gotcha ya documentado en T2, línea arriba: `s.R2_ACCOUNT_ID`, no `s.r2_account_id`). Se usó la convención correcta desde el inicio en `r2_client.py` y `services/storage.py`.

**[T10 · 2 jul 2026]** `asyncio.to_thread()` con boto3 (`put_object`, `generate_presigned_url`, `delete_object`) funcionó sin comportamiento inesperado. boto3 instalado desde T1, sin necesidad de ajustar versión.

**[T10 · 2 jul 2026]** Verificación manual con R2 real (bucket `vent3-prospectos`) exitosa sin ajustes de credenciales ni `endpoint_url`: subida, URL pública (`pub-*.r2.dev`, HTTP 200, `Content-Type: application/pdf`), URL firmada (`ExpiresIn=300`) y eliminación funcionaron en el primer intento contra `apps/api/.env` real.

**[T10 · 2 jul 2026]** Tests: `tests/test_storage.py` mockea `src.services.storage.r2` con `unittest.mock.patch` (no se llama a R2 real en CI). 6 criterios de done cubiertos con 10 TCs (parametrizados en `sanitizar_nombre_archivo`). Suite completo al cierre: **65 passed, 2 failed (preexistentes de T9/`test_auth.py`, sin cambios)** — de los cuales 10/10 son los nuevos de T10.

**[T11 · 2 jul 2026]** No se recrearon `models/prospecto.py`, `models/producto_prospecto.py`, `schemas/prospecto.py` ni `repositories/prospectos.py` — ya existían desde T4/T5 y `activar_prospecto()` del repo ya traía el swap atómico completo implementado. Se agregaron solo `services/prospectos.py` (`ProspectosService.subir()` / `.activar()`) y `routers/prospectos.py`, reusando `StorageService.subir_pdf()` (T10) y `AuditoriaService.registrar_activacion_prospecto()` (T8) tal cual. `ProductosRepository.get_by_id()` (heredado de `BaseRepository`) alcanzó para validar `producto_id` en el POST — no hizo falta agregar nada a `ProductosService`/`ProductosRepository`.

**[T11 · 2 jul 2026]** Decisión sobre mockeo en tests: se mockeó `src.services.storage.r2` (el cliente boto3), no `StorageService` completo — mismo patrón que `test_storage.py` de T10. Fixture `mock_r2` autouse en `test_prospectos.py`. Así TC1 (upload válido) ejercita la lógica real de `StorageService.subir_pdf()` (validación de magic bytes `%PDF`, tamaño, armado de key) sin pegarle a R2 real en CI.

**[T11 · 2 jul 2026]** Técnica para TC7 (atomicidad): `AuditoriaService.registrar_cambio()` nunca propaga excepciones (diseño de T8) así que no sirve como punto de fallo para forzar un rollback observable. En su lugar se parcheó la clase `ProspectosRepository.activar_prospecto` completa (`unittest.mock.patch("src.repositories.prospectos.ProspectosRepository.activar_prospecto", ...)`) por una función que reproduce el `session.add()` de la nueva asociación y el cambio de estado del prospecto nuevo, y después lanza `RuntimeError` **antes** del `flush()`. Como `AsyncClient(transport=ASGITransport(...))` tiene `raise_app_exceptions=True` por default, la excepción no vuelve como response 500 sino que se re-lanza en el test — hubo que envolver el `await auth_client.patch(...)` en `with pytest.raises(RuntimeError):`. Después se verifica con una conexión nueva (no la del fixture) que `prospecto.estado_vigencia` sigue `en_revision`, no hay fila en `producto_prospectos`, y `productos.tiene_prospecto` no cambió. Referencia útil para futuros tests de atomicidad de transacciones ASGI.

**[T11 · 2 jul 2026]** El sandbox del agente no tiene `DATABASE_URL`/`ADMIN_EMAIL`/`ADMIN_INITIAL_PASSWORD` exportadas ni acceso a los `.env*` (restricción de permisos). Los 8 TCs de `test_prospectos.py` colectaron bien ahí pero corrieron en skip. El usuario corrió la suite en su máquina (Docker `vent3-db`, puerto 5433) con las credenciales reales: **8/8 verdes en `test_prospectos.py`**. Suite completa al cierre: **73 passed, 2 failed (los mismos 2 preexistentes de `test_auth.py` desde T9, sin cambios)** — 65 + 8 nuevos = 73, sin regresiones.

**[T11 · 2 jul 2026]** GOTCHA nuevo, importante para futuras sesiones que reseteen la DB de test: la migración `004_seed_admin_inicial.py` lee `ADMIN_EMAIL`/`ADMIN_INITIAL_PASSWORD` del **entorno vigente en el momento de correr `alembic upgrade head`**, no del `.env` actual, y usa `ON CONFLICT (email) DO NOTHING` — si después se cambia la password en `.env` sin volver a seedear desde cero, el hash en la DB queda desactualizado y el login falla con 401 aunque la password en `.env` sea "correcta". En esta sesión el hash de `admin@vent3.com.ar` en la DB de test local no coincidía con el valor actual de `ADMIN_INITIAL_PASSWORD` (`.env`); se corrigió con un `UPDATE usuarios SET password_hash = ...` directo contra la DB de test local (puerto 5433), regenerando el hash bcrypt a partir de la password real de `.env`. No se tocó ningún archivo de migración ni producción. Si esto vuelve a pasar: verificar `password_hash` vs `bcrypt.checkpw()` antes de asumir que el código de login está roto.

**[T12 · 2 jul 2026]** No se recrearon `models/gtin_registro.py`, `schemas/resolver.py`, `schemas/gtin.py` ni `repositories/resolver.py` — ya existían desde T4/T5 y `ResolverRepository.resolver_gtin()` ya traía toda la lógica de negocio de los 4 casos (no_encontrado/inactivo/sin_prospecto/con_prospecto) testeada a nivel unitario desde T4 (`test_repositorios.py` TC4). Se agregaron solo `services/resolver.py` (`ResolverService.resolver()`, arma el `ResolverResponse` a partir del dict del repo), `routers/internal.py` y `require_internal_token()` en `deps.py`.

**[T12 · 2 jul 2026]** El endpoint SIEMPRE responde HTTP 200 con el error semántico en el body (`{"error": "no_encontrado"}` etc.) — nunca 404. Los únicos códigos de error HTTP reales son 403 (token ausente/inválido, vía `secrets.compare_digest()` constant-time) y 422 (formato de GTIN inválido, vía `Annotated[str, Path(pattern=r"^\d{14}$")]`, sin lógica manual). Este contrato es el que va a consumir el SSR de Next.js en T18.

**[T12 · 2 jul 2026]** Para el escenario de "dos prospectos vigentes" (TC8) se reusó el flujo real de T11 (`auth_client` con `POST /api/prospectos` + `PATCH /activar`, dos veces con `tipo_audiencia` distinto) en lugar de insertar filas por SQL directo — así el test también ejerce la integración real entre T11 y T12, no solo el estado final de la tabla `producto_prospectos`.

**[T12 · 2 jul 2026]** `secrets.compare_digest(token_recibido, settings.INTERNAL_API_TOKEN)` funcionó sin problemas de tipos (ambos son `str`, no hace falta encodear a bytes).

**[T12 · 2 jul 2026]** [BLOQUEANTE resuelto, NO es el gotcha de T11] Al correr los tests el usuario obtuvo "password authentication failed for user vent3" en los 8 TCs nuevos. Investigado con `docker exec` + `psql` directo: **no era el hash de password desactualizado de T11** (ese gotcha era sobre el admin seed). La causa real: `apps/api/.env` tenía `DATABASE_URL` apuntando a `localhost:5432`, pero `infra/docker-compose.yml` mapea `vent3-db` al puerto **5433** (`"5433:5432"`). El puerto 5432 de la máquina del usuario está ocupado por `alcosto-db`, un contenedor Postgres de otro proyecto sin relación con Vent3 — los tests se conectaban silenciosamente a la DB equivocada y fallaban con un error de auth que parecía de credenciales pero era de proyecto equivocado. Se corrigió el puerto en el `.env` del usuario (5432 → 5433) y los 8 TCs pasaron. Confirmar siempre host:puerto de `DATABASE_URL` contra `docker-compose.yml` antes de asumir que un "password authentication failed" es un problema de hash o de credenciales — puede ser simplemente el puerto equivocado en una máquina con múltiples proyectos Postgres locales.

**[T12 · 2 jul 2026]** Suite completa al cierre: **81 passed, 2 failed** (los mismos 2 preexistentes de `test_auth.py` desde T9, sin cambios) — 73 + 8 nuevos = 81, sin regresiones.

---
> Actualizar este archivo al finalizar cada sesión. Formato sugerido para COMPLETADAS:
> `- [x] **T1** — Setup del monorepo ✅ · 25 jun 2026`
