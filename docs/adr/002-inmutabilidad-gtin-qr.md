# ADR 002 — Inmutabilidad de GTIN/QR y excepción exclusiva de rol admin

**Fecha:** 2026-07-15
**Estado:** Aceptado
**Autor:** Laboratorio Vent3

## Contexto

Una vez que un GTIN tiene `qr_generado = true`, ese código puede estar ya impreso en
packaging físico en circulación (ver RNF-08 en SPEC.md). Modificar el GTIN o la URL de
destino después de ese punto rompería el QR impreso — el paquete físico apuntaría a un
producto o URL distinta a la real. Por eso `PATCH /api/gtins/{id}` bloquea cambios al
campo `gtin` cuando `qr_generado` ya es `true` en la fila (`apps/api/src/services/gtins.py`).

Durante una revisión se detectó que esa protección tiene un bypass de dos pasos:
1. `PATCH { qr_generado: false }` — no hay ninguna regla que lo impida.
2. `PATCH { gtin: "nuevo" }` — como `qr_generado` ya quedó en `false` en la DB, el
   chequeo de bloqueo no se dispara.

Es decir, desmarcar la casilla "QR generado" anula la protección por completo.

## Decisión (revisada — ver "Actualización" más abajo)

1. **La posibilidad de desmarcar `qr_generado` y volver a editar el GTIN se mantiene
   como excepción intencional**, no como bug a eliminar de raíz. Motivo: un error humano
   de tipeo al cargar el GTIN (dígito equivocado) debe poder corregirse sin pasar por una
   migración manual de base de datos.
2. **Esa excepción es exclusiva del rol `admin`.**
3. **La falta de fricción del lado del admin es el problema real, no el control de
   acceso.** Se agrega en el frontend (`GtinTable.tsx`) un modal de confirmación
   explícita en ambas transiciones sensibles:
   - **Bloqueo:** GTIN modificado + casilla "QR generado" marcada → modal de advertencia
     mostrando el GTIN ingresado, para verificación antes de una acción irreversible.
   - **Desbloqueo:** casilla "QR generado" pasa de `true` a `false` → mismo tipo de modal,
     porque es el paso que reabre la edición del GTIN.

   Esta fricción es deliberadamente solo de UI (no bloquea a nivel de API): el admin es
   un rol de confianza y el objetivo es evitar un clic accidental, no impedir la
   corrección legítima de un error humano.

## Actualización (2026-07-15, misma fecha) — `editor` comparte pantalla y endpoint

La versión original de este ADR (punto 3, ya reemplazado) decía que los futuros
endpoints de `editor` no debían exponer `gtin`/`qr_generado`/`url_digital_link` en
absoluto. Se revisó esa decisión: el negocio necesita que `editor` **sí** pueda cargar
estos campos — es quien hace la carga inicial de productos —, pero sin la capacidad de
revertir una vez generado el QR.

Decisión final:

- `PATCH /api/gtins/{id}` pasa a estar protegido por `require_editor_or_admin`
  (`apps/api/src/core/deps.py`) en lugar de `require_admin` — mismo endpoint, mismo
  schema `GtinUpdateRequest`, sin duplicar rutas.
- Dentro de `GtinsService.actualizar` (`apps/api/src/services/gtins.py`) las reglas de
  bloqueo quedan así:
  - **`gtin`**: bloqueado para cualquier rol (incluido admin) mientras
    `gtin_registro.qr_generado` sea `true` en la fila persistida — HTTP 409. La única
    vía de corrección es primero desmarcar `qr_generado` (paso siguiente) y recién ahí,
    en un segundo PATCH, editar el GTIN.
  - **`qr_generado` y `url_digital_link`**: una vez que `gtin_registro.qr_generado` es
    `true`, modificarlos requiere `rol == "admin"` — HTTP 403 para cualquier otro rol
    (`editor` o `lector`). Esto es lo que impide que `editor` revierta el candado.
  - `es_vigente` y `validado_gs1` quedan sin restricción de rol — no forman parte de lo
    que queda impreso en el QR físico.
- El rol `lector` sigue sin acceso al endpoint en absoluto (es de solo lectura, no debe
  poder escribir nada).
- En el frontend (`GtinTable.tsx`), el checkbox "QR generado" y el input de URL
  Digital Link quedan **deshabilitados** para cualquier usuario no-admin una vez que
  `gtin.qr_generado` es `true` en el registro (prop `rolUsuario`, obtenida via
  `GET /api/auth/me` en `apps/web/app/admin/productos/[id]/page.tsx` y pasada a
  `GtinTable`). El modal de "desbloqueo" nunca se dispara para un no-admin porque la
  casilla ya es imposible de destildar desde la UI; el 403 del backend es la garantía
  real, la UI es solo la comodidad de no ofrecer un botón que va a fallar.

## Alternativas consideradas

| Opción | Descartada porque |
|---|---|
| Bloquear a nivel de backend la transición `qr_generado: true → false` sin excepción | Elimina la vía de corrección de error humano que el propio negocio pidió mantener |
| Excluir a `editor` del endpoint por completo (decisión original de este ADR) | El negocio necesita que `editor` cargue estos campos la primera vez; excluirlo forzaría un endpoint/flujo separado solo para la carga inicial |
| Endpoint separado para `editor` en vez de reglas por rol en el mismo servicio | Duplica el schema y la lógica de reemplazo de `es_vigente`; el enfoque por rol dentro del mismo servicio es más simple y ya sigue el patrón de `require_admin`/`require_editor_or_admin` existente |
| Requerir un flag adicional en el body del PATCH (ej. `confirmar_accion_irreversible: true`) para hacer cumplir la confirmación también a nivel de API | Redundante mientras la única vía de acceso es el panel propio; se documenta como posible endurecimiento futuro si se agregan integraciones externas al endpoint |

## Consecuencias

- Nueva dependency `require_editor_or_admin` en `apps/api/src/core/deps.py`.
- `GtinsService.actualizar` ahora recibe el objeto `Usuario` completo (antes recibía
  solo `usuario_id: UUID`) para poder evaluar `usuario.rol` en las reglas de bloqueo.
- El frontend necesitó, por primera vez, conocer el rol del usuario autenticado en una
  pantalla del panel admin — se resolvió con `getMe()` en el padre de `GtinTable`
  (`apps/web/app/admin/productos/[id]/page.tsx`) en lugar de crear un contexto de auth
  global, porque es el único consumidor hasta ahora. Si aparece un segundo componente
  que necesite el rol, ahí sí vale la pena evaluar un contexto compartido.
- Cualquier tarea futura que agregue una UI de carga para `editor` debe revisar este ADR
  antes de decidir qué reglas de bloqueo aplican a qué campos.
