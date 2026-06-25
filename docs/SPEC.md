# SPEC.md — Sistema de Prospecto Digital Vent3
**Versión:** 1.0  
**Estado:** Borrador para aprobación  
**Fecha:** Junio 2026  
**Autor:** Área de Sistemas — Laboratorio Vent3  
**Deadline regulatorio:** 15 de noviembre de 2026 (ANMAT Disposición N° 2891/2026)

---

## 1. Propósito

Diseñar y construir un sistema web que permita a Laboratorio Vent3 cumplir con la Disposición N° 2891/ANMAT/2026, la cual exige que todos los medicamentos en circulación lleven en su packaging un código QR o Datamatrix conforme al estándar GS1 Digital Link, que al ser escaneado desde cualquier dispositivo muestre el prospecto digital vigente del producto.

El sistema debe ser robusto, auditable y extensible: diseñado para ser la base de la transformación digital del laboratorio, no solo una solución puntual al requerimiento regulatorio.

---

## 2. Contexto regulatorio

- **Norma aplicable:** Disposición N° 2891/ANMAT/2026.
- **Estándar técnico:** GS1 Digital Link. El QR codifica una URL con estructura `/01/[GTIN-14-dígitos]`.
- **Organismo de validación de estándar:** GS1 Argentina (no valida contenido, solo estructura y legibilidad).
- **Dominio del resolver:** `www.vent3.com.ar` — dominio principal, confirmado como opción correcta por permanencia del QR impreso.
- **Formato de URL en QR:** `https://www.vent3.com.ar/01/[GTIN-14-dígitos]`
- **Vent3 ya tiene GTINs registrados en GS1 Argentina** para todos sus productos activos.

---

## 3. Actores del sistema

| Actor | Descripción | Autenticación |
|---|---|---|
| **Usuario final (paciente)** | Escanea el QR del packaging desde su celular. No tiene cuenta. | Ninguna |
| **Profesional de salud** | Escanea el QR y selecciona perfil profesional para acceder a versión técnica del prospecto. | Ninguna |
| **Administrador del sistema** | Usuario interno de Vent3. Gestiona productos, sube PDFs, administra el sistema. | JWT (email + contraseña) |

---

## 4. Objetivos del sistema (lo que SÍ hace)

### 4.1 Resolver el QR y servir el prospecto
Cuando un usuario escanea el QR de un producto, el sistema debe:
1. Recibir la petición en la ruta `GET /01/[gtin]`.
2. Resolver el GTIN en la base de datos.
3. Determinar si el producto tiene prospecto vigente.
4. Si tiene un único prospecto: redirigir o mostrar el PDF directamente.
5. Si tiene dos versiones (público general y profesional de salud): mostrar una landing page de selección de perfil y enrutar al PDF correspondiente según la elección.
6. Manejar todos los casos de error con páginas informativas (producto inactivo, sin prospecto vigente, GTIN no encontrado).

### 4.2 Panel de administración
Un panel web con autenticación que permita al usuario admin:
- Ver el listado completo de productos con su estado y estado del prospecto.
- Subir un nuevo PDF de prospecto y asociarlo a un producto.
- Activar un prospecto (lo que automáticamente marca el anterior como reemplazado).
- Activar o desactivar un producto.
- Ver el historial de cambios (audit log) de cualquier producto o prospecto.

### 4.3 Autenticación del admin
- Login con email y contraseña.
- Sesión gestionada con JWT.
- Un único usuario admin para el MVP. El sistema de gestión de múltiples usuarios queda fuera del MVP pero la arquitectura lo contempla.

### 4.4 Migración desde Excel
- Script de migración único que lee el Excel `BD_productos_v2.xlsx` y carga todos los productos activos de canal farmacia a la base de datos PostgreSQL.
- Los productos inactivos, de licitación y oncológicos se migran al estado correspondiente pero no generan flujo activo.

### 4.5 Sitio institucional
- Rediseño completo de `www.vent3.com.ar` con identidad visual moderna.
- El sitio institucional y el portal de prospectos conviven en el mismo proyecto Next.js bajo el mismo dominio.

---

## 5. No-objetivos del MVP (lo que explícitamente NO hace)

Estos ítems están documentados para evitar expansión de scope durante el desarrollo.

| Ítem | Justificación |
|---|---|
| QR para productos de licitación | Sin bajada de línea de ANMAT. Fuera de scope hasta nueva instrucción. |
| QR para productos oncológicos (línea MU-) | Sin bajada de línea de ANMAT. Fuera de scope hasta nueva instrucción. |
| Panel de gestión de usuarios (alta/baja/edición) | Se implementa post-MVP. La DB y la arquitectura lo contemplan. |
| Trazabilidad de lotes (AI dinámicos GS1) | Fuera de scope regulatorio actual. El modelo de datos lo permite a futuro. |
| Gestión de stock o inventario | No es objetivo de este sistema. |
| Notificaciones automáticas (vencimiento de prospectos, etc.) | Post-MVP. |
| API pública para terceros | No requerido. |
| Aplicación móvil nativa | El sistema es web-first y mobile-responsive. |
| Integración con sistemas ERP o facturación | Fuera de scope. |

---

## 6. Requerimientos funcionales

### RF-01 — Resolución de QR por GTIN
- **Actor:** Usuario final / Profesional de salud
- **Trigger:** Escaneo del QR desde cualquier dispositivo
- **Flujo principal:**
  1. El dispositivo abre `https://www.vent3.com.ar/01/[gtin]`.
  2. El sistema valida que el GTIN tenga 14 dígitos.
  3. El sistema busca el producto en la DB.
  4. Si el producto está activo y tiene un único prospecto vigente → renderiza página de prospecto con PDF embebido y opción de descarga.
  5. Si el producto tiene dos prospectos (público + profesional) → renderiza landing de selección de perfil.
- **Flujos alternativos:**
  - GTIN no encontrado → página 404 informativa con datos de contacto de Vent3.
  - Producto inactivo → página informativa "Este producto no se encuentra en circulación".
  - Producto sin prospecto vigente → página informativa "Prospecto no disponible temporalmente".
- **Restricciones:** Tiempo de respuesta < 2 segundos en conexión 4G. No requiere autenticación.

### RF-02 — Landing de selección de perfil (dos prospectos)
- **Actor:** Usuario final / Profesional de salud
- **Trigger:** RF-01 detecta que el producto tiene dos versiones de prospecto
- **Flujo:**
  1. Se muestra pantalla con dos opciones: "Soy paciente o cuidador" / "Soy profesional de la salud".
  2. El usuario selecciona su perfil.
  3. El sistema sirve el PDF correspondiente.
- **Restricciones:** La URL no cambia. La selección de perfil no requiere registro ni autenticación.

### RF-03 — Login del administrador
- **Actor:** Administrador
- **Flujo:**
  1. El admin accede a `/admin/login`.
  2. Ingresa email y contraseña.
  3. El sistema valida contra la DB.
  4. Si es correcto: genera JWT y redirige al dashboard.
  5. Si es incorrecto: mensaje de error sin detallar cuál campo falló.
- **Restricciones:** Máximo 5 intentos fallidos antes de bloqueo temporal de 15 minutos. Contraseña almacenada con bcrypt.

### RF-04 — Dashboard de productos
- **Actor:** Administrador
- **Descripción:** Vista principal del panel. Lista todos los productos con columnas: código interno, nombre, forma farmacéutica, presentación, estado (activo/inactivo), estado del prospecto (vigente/sin prospecto/reemplazado), y acciones disponibles.
- **Filtros disponibles:** por estado del producto, por estado del prospecto, por nombre o código.

### RF-05 — Carga de prospecto
- **Actor:** Administrador
- **Flujo:**
  1. El admin selecciona un producto desde el dashboard.
  2. Accede a la sección "Prospectos" del producto.
  3. Sube un archivo PDF (máx. 20 MB).
  4. Completa: código de prospecto interno, versión, tipo (público / profesional / único).
  5. Guarda en estado `en_revision`.
  6. Activa el prospecto: el sistema lo marca como `vigente` y el anterior pasa a `reemplazado`.
- **Restricciones:** Solo se aceptan archivos PDF. El sistema almacena el PDF en el servicio de objetos (Cloudflare R2 o Supabase Storage) y guarda la URL en la DB.

### RF-06 — Activar / desactivar producto
- **Actor:** Administrador
- **Flujo:** El admin puede cambiar el estado de un producto entre `activo` e `inactivo` desde el dashboard o desde la ficha del producto.
- **Restricciones:** Toda activación/desactivación queda registrada en el audit_log.

### RF-07 — Audit log
- **Actor:** Administrador
- **Descripción:** Vista de solo lectura que muestra el historial de cambios del sistema. Filtrable por producto, por tipo de acción y por rango de fechas.
- **Restricciones:** Ningún usuario puede editar ni eliminar registros del audit log. Es append-only a nivel de base de datos.

### RF-08 — Sitio institucional
- **Actor:** Visitante web
- **Descripción:** Páginas institucionales del laboratorio: home, quiénes somos, línea de productos (informativa, no el portal de prospectos), contacto.
- **Restricciones:** El sitio institucional comparte dominio y proyecto con el portal de prospectos pero son secciones independientes. No requiere autenticación.

---

## 7. Requerimientos no funcionales

| ID | Categoría | Requerimiento |
|---|---|---|
| RNF-01 | Rendimiento | La página de prospecto debe cargar en menos de 2 segundos en conexión 4G móvil. |
| RNF-02 | Disponibilidad | El sistema debe estar disponible 99.5% del tiempo. El downtime planificado debe comunicarse previamente. |
| RNF-03 | Compatibilidad | La página de prospecto debe funcionar correctamente en los navegadores móviles de los últimos 3 años (Chrome Android, Safari iOS). Sin requerir instalación de apps. |
| RNF-04 | Seguridad | Contraseñas hasheadas con bcrypt. JWT con expiración de 8 horas. HTTPS obligatorio. Headers de seguridad estándar (HSTS, CSP, X-Frame-Options). |
| RNF-05 | Escalabilidad | El sistema debe poder incorporar nuevos productos, prospectos y eventualmente usuarios sin cambios estructurales en la DB ni en la API. |
| RNF-06 | Accesibilidad | La página pública de prospecto debe cumplir con criterios básicos de accesibilidad WCAG 2.1 nivel AA: contraste adecuado, texto alternativo en imágenes, navegación por teclado. |
| RNF-07 | Auditoría | Todo cambio sobre datos críticos (productos, prospectos, GTINs) debe quedar registrado en audit_log con usuario, timestamp y valores anterior/nuevo. |
| RNF-08 | Permanencia de URLs | Las URLs de los QR impresos en packaging no pueden cambiar bajo ninguna circunstancia. Cualquier cambio en el destino se gestiona a nivel de la DB, no de la URL. |
| RNF-09 | Mobile-first | La interfaz pública está diseñada primero para móvil. El panel de administración puede ser desktop-first. |

---

## 8. Modelo de datos — resumen de tablas

El diseño completo está documentado en `Vent3_Diseño_BD_Prospecto_Digital_v2.docx`. Resumen:

| Tabla | Propósito |
|---|---|
| `productos` | SKU de cada presentación comercial. |
| `principios_activos` | Catálogo maestro de drogas. |
| `producto_principios` | Composición (relación N:M con potencia). |
| `prospectos` | Documentos PDF con su estado de vigencia. |
| `producto_prospectos` | Vínculo producto ↔ prospecto (con variante GS1 opcional). |
| `gtin_registro` | GTINs de GS1 y estado del QR. |
| `usuarios` | Cuentas de acceso al panel. |
| `audit_log` | Historial inmutable de cambios. |
| `producto_materiales_packaging` | Materiales de envasado (extensión futura). |

---

## 9. Decisiones de arquitectura confirmadas

| Decisión | Resolución |
|---|---|
| Dominio del resolver GS1 Digital Link | `www.vent3.com.ar` (dominio principal, no subdominio) |
| Estructura de URL | `https://www.vent3.com.ar/01/[GTIN-14-dígitos]` — estándar GS1, no modificable |
| Destino del QR | Landing page Next.js (SSR), no PDF directo |
| Producto con dos prospectos | Una URL única, landing de selección de perfil (Opción A) |
| Opción GS1 elegida | Dominio propio ("Llevar a mi página web") |
| Stack backend | FastAPI (Python) + PostgreSQL |
| Stack frontend | Next.js (SSR/SSG) |
| Almacenamiento de PDFs | Cloudflare R2 o Supabase Storage (a confirmar en PLAN.md) |
| Hosting | A contratar (Railway/Render para API, Vercel para frontend) |

---

## 10. Criterios de aceptación del MVP

El MVP se considera completo y listo para entrega cuando:

- [ ] Escanear el QR de cualquier producto activo con prospecto vigente muestra el prospecto en menos de 2 segundos desde un celular.
- [ ] Un producto sin prospecto vigente muestra una página informativa (no un error genérico).
- [ ] Un GTIN desconocido devuelve una página 404 informativa.
- [ ] Un producto con dos versiones de prospecto muestra la landing de selección de perfil correctamente.
- [ ] El admin puede hacer login y acceder al dashboard.
- [ ] El admin puede subir un PDF y activarlo como prospecto vigente de un producto.
- [ ] El admin puede activar y desactivar productos.
- [ ] Cada acción del admin queda registrada en el audit log.
- [ ] El sitio institucional está publicado bajo `www.vent3.com.ar`.
- [ ] El sistema funciona correctamente en Chrome Android y Safari iOS.
- [ ] Todos los GTINs activos tienen su QR generado en el portal de GS1 y validado por el Servicio de Calidad de Lectura.

---

## 11. Fuera de scope — aclaración sobre productos especiales

Los siguientes grupos de productos están presentes en la base de datos pero **no generan QR ni flujo activo** en el MVP:

- **Productos de licitación** (`canal = 'licitacion'`): sin instrucción de ANMAT al respecto.
- **Productos oncológicos línea MU-** (`tiene_prospecto = false`): sin prospecto existente ni instrucción de ANMAT.
- **Productos inactivos** (`estado = 'inactivo'`): excluidos del flujo operativo. Conservados en DB por trazabilidad histórica.

Cuando ANMAT emita instrucción para alguno de estos grupos, el sistema puede incorporarlos sin cambios estructurales.

---

## 12. Glosario

| Término | Definición |
|---|---|
| **ANMAT** | Administración Nacional de Medicamentos, Alimentos y Tecnología Médica. Ente regulador argentino. |
| **GS1 Digital Link** | Estándar internacional que permite expresar identificadores de producto (GTIN) como URLs web. |
| **GTIN** | Global Trade Item Number. Número de 14 dígitos que identifica una presentación comercial en el sistema GS1. |
| **Prospecto digital** | Versión electrónica del prospecto de un medicamento, accesible mediante QR en el packaging. |
| **Resolver** | Servidor que recibe la URL del QR y devuelve el recurso correcto (en este caso, el prospecto). |
| **Landing de perfil** | Página intermedia que aparece cuando un producto tiene dos versiones de prospecto. Pregunta al usuario si es paciente o profesional. |
| **MVP** | Minimum Viable Product. Versión mínima funcional del sistema que cumple con el requerimiento regulatorio. |
| **Audit log** | Registro inmutable y cronológico de todos los cambios realizados en los datos del sistema. |
