# ADR 003 — Reversión de "gestión de usuarios es post-MVP"

**Fecha:** 2026-07-22
**Estado:** Aceptado
**Autor:** Laboratorio Vent3

## Contexto

La decisión #6 del CLAUDE.md establece que el panel de gestión de múltiples usuarios
es post-MVP: el MVP contempla un único usuario admin, sembrado por migración de
Alembic (`004_seed_admin_inicial.py`) vía variables de entorno
(`ADMIN_EMAIL`, `ADMIN_INITIAL_PASSWORD`). No existe endpoint ni UI para crear,
editar o desactivar usuarios — la única vía de alta es correr esa migración a mano
contra la base de producción.

El MVP fue presentado en una reunión el 2026-07-15 y se dio por cerrado. El usuario
(dueño del proyecto) determina que ahora es el momento de avanzar con la gestión de
usuarios, priorizándola incluso por delante de T25 (carga de GTINs reales de GS1),
que era la siguiente tarea en el roadmap de TASK.md.

Un dato relevante que reduce el alcance real de este trabajo: el schema de base de
datos y el middleware de autorización **ya estaban preparados para multi-rol desde
T3/T7**, aunque nunca se expuso una UI para administrarlo:

- `rol_usuario_enum` ya define `'admin'`, `'editor'`, `'lector'`
  (`apps/api/alembic/versions/001_extensiones_y_enums.py`).
- `apps/api/src/core/deps.py` ya implementa `require_admin` y
  `require_editor_or_admin`, y ya se usan en producción (ej. `PATCH /api/gtins/{id}`,
  ver ADR 002).
- La tabla `usuarios` ya tiene `activo`, `intentos_fallidos`, `bloqueado_hasta`
  (lockout de RF-03) listos.

Es decir: esta tarea no diseña el modelo de roles desde cero, expone lo que ya existe.

## Decisión

1. Se revierte la decisión #6 del CLAUDE.md. La gestión de usuarios pasa a ser una
   tarea activa, insertada en el roadmap por delante de T25.
2. Roles cubiertos en esta primera versión: `admin` y `editor` (el operativo
   limitado que ya consume el middleware existente). `lector` queda en el enum sin
   flujo de alta propio hasta que haya un caso de uso concreto — no se descarta, no
   se implementa todavía.
3. Alta de usuario vía **link de invitación de un solo uso**, no vía password
   definida por el admin ni invitación por email:
   - El admin genera la invitación desde el panel (elige email, nombre, rol).
   - Se crea un registro de invitación con un token opaco de un solo uso y
     expiración (a definir en el diseño técnico: propuesta 24-48h).
   - El admin comparte el link por el canal que prefiera (no requiere infraestructura
     de email transaccional, que el proyecto no tiene hoy).
   - El invitado abre el link, fija su propia contraseña, y ahí recién se crea (o
     activa) la fila en `usuarios`. El admin nunca conoce ni maneja la contraseña
     del invitado.
   - El token se invalida al usarse o al expirar; un link vencido o ya usado no debe
     permitir fijar contraseña.
4. Se mantiene todo lo ya cerrado en ADR 002 (reglas de rol sobre `gtin`/`qr_generado`)
   sin cambios — esta tarea agrega quién puede tener rol `editor`/`admin`, no cambia
   qué puede hacer cada rol.

## Alternativas consideradas

| Opción | Descartada porque |
|---|---|
| Admin define la password del nuevo usuario | El admin terminaría conociendo la contraseña del usuario, mal hábito de seguridad, y requiere pasarla por un canal que el admin tendría que asegurar por su cuenta. |
| Invitación por email con link | Requeriría contratar/integrar un proveedor de email transaccional que el proyecto no tiene — costo y tiempo no justificados para este alcance, sobre todo con el deadline del 15 de noviembre. |
| Implementar `lector` también en esta vuelta | No hay caso de uso concreto todavía (nadie pidió un rol de solo lectura); se prefiere no construir sobre una hipótesis. Enum ya lo soporta si aparece la necesidad. |

## Consecuencias

- Nueva tabla o extensión de schema para las invitaciones (token, expiración, estado,
  rol propuesto, email propuesto) — a definir en el diseño técnico.
- Nuevos endpoints públicos (sin auth) para consumir el token de invitación, con las
  mismas precauciones de seguridad que `/api/auth/login` (rate limiting, no filtrar
  si un token existe o no en las respuestas de error).
- Nueva UI en el panel admin: listado de usuarios, generación de invitaciones, y una
  pantalla pública `/activar-invitacion/[token]` para fijar contraseña.
- T25 (carga de GTINs reales) queda pausada hasta cerrar esta tarea.
