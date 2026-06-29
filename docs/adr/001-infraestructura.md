# ADR 001 — Infraestructura de producción

**Fecha:** 2026-06-29
**Estado:** Aceptado
**Autor:** Área de Sistemas — Laboratorio Vent3

## Contexto

El sistema necesita hosting para: API FastAPI (Python), frontend Next.js (SSR), base de datos PostgreSQL y almacenamiento de archivos PDF. La infraestructura debe ser contratada nueva (el laboratorio no tiene servidor propio). El deadline regulatorio del 15 de noviembre de 2026 limita la ventana de operación: se priorizan plataformas con deploys automáticos desde Git y SSL gestionado, para reducir al mínimo el overhead operativo.

## Decisión

| Componente | Plataforma | Detalles |
|---|---|---|
| **API FastAPI** | Railway | Servicio "vent3-api", deploy desde GitHub, carpeta `apps/api` |
| **Base de datos** | Railway PostgreSQL 16 | Mismo proyecto que la API — conexión interna sin latencia de red externa |
| **Frontend Next.js** | Vercel | Deploy desde GitHub, root directory `apps/web` |
| **Storage PDFs** | Cloudflare R2 | Bucket `vent3-prospectos`, acceso público habilitado |
| **Dominio API** | `api.vent3.com.ar` | CNAME → Railway |
| **Dominio frontend** | `www.vent3.com.ar` | CNAME → Vercel |

## Alternativas consideradas

| Opción | Descartada porque |
|---|---|
| AWS (EC2 + RDS + S3) | Overhead operativo excesivo para un proyecto unipersonal con deadline ajustado |
| Supabase full-stack | Acopla al BaaS de Supabase; este proyecto usa FastAPI + SQLAlchemy, lo que elimina las ventajas del ecosistema de Supabase |
| VPS propio (DigitalOcean, Linode) | Requiere gestión de OS, SSL, backups — sin beneficio a esta escala |
| Heroku | Costos más altos que Railway para el mismo tier |
| Neon (PostgreSQL serverless) | Introduce latencia de cold start inaceptable para el endpoint público del resolver |

## Consecuencias

- Deploys automáticos al mergear a `main` en GitHub (Railway y Vercel escuchan el repo).
- SSL gestionado automáticamente por Railway (Let's Encrypt) y Vercel.
- Backups automáticos de PostgreSQL incluidos en Railway.
- Egress de PDFs gratuito con Cloudflare R2 — relevante porque los prospectos se descargan muchas veces por día.
- Costo operativo mensual estimado: tier gratuito/hobby mientras el tráfico sea bajo; escala automáticamente según uso.
- La URL interna de Railway (`postgres.railway.internal`) permite que la API acceda a la DB sin pasar por la red pública — menor latencia y sin costo de egress.

## Variables de entorno requeridas por plataforma

### Railway (apps/api)

```
DATABASE_URL              # Provista automáticamente por Railway al conectar el servicio PostgreSQL
SECRET_KEY                # JWT signing key — generar con: python -c "import secrets; print(secrets.token_hex(32))"
ADMIN_EMAIL               # admin@vent3.com.ar
ADMIN_INITIAL_PASSWORD    # Password seguro para el usuario admin inicial
FRONTEND_URL              # https://www.vent3.com.ar
INTERNAL_API_TOKEN        # Token compartido con Vercel — generar con: python -c "import secrets; print(secrets.token_hex(32))"
R2_ACCOUNT_ID             # Account ID de Cloudflare
R2_ACCESS_KEY_ID          # API token R2 (Object Read & Write)
R2_SECRET_ACCESS_KEY      # API token R2 secret
R2_BUCKET_NAME            # vent3-prospectos
R2_PUBLIC_URL             # https://[hash].r2.dev (o dominio custom si se configura)
```

### Vercel (apps/web)

```
NEXT_PUBLIC_API_URL       # https://api.vent3.com.ar
INTERNAL_API_TOKEN        # Mismo valor que el configurado en Railway — DEBEN SER IDÉNTICOS
```

## Notas operativas

- **`DATABASE_URL` en Railway:** Railway puede inyectar la URL en formato `postgres://`. SQLAlchemy async requiere el prefijo `postgresql+asyncpg://`. Verificar y ajustar si es necesario.
- **`INTERNAL_API_TOKEN`** es el secreto compartido entre Next.js SSR (Vercel) y FastAPI (Railway). Si difieren, el resolver del QR retornará 403 en producción.
- **Puerto de la API:** Railway inyecta `$PORT` dinámicamente. El `railway.toml` usa `--port $PORT` en el start command — no hardcodear 8000.
