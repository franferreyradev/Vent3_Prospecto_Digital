# Prospecto Digital — Laboratorio Vent3

Sistema de prospecto digital conforme a ANMAT Disposición N° 2891/2026 + estándar GS1 Digital Link.

El QR impreso en el packaging de cada medicamento apunta a `https://www.vent3.com.ar/01/[GTIN-14-dígitos]`
y muestra el prospecto vigente del producto.

**Deadline regulatorio:** 15 de noviembre de 2026.

---

## Prerrequisitos

- Node.js >= 20.0.0
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) — gestor de dependencias Python
- Docker y Docker Compose

## Setup de desarrollo local

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd vent3-prospecto-digital

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env con los valores reales de desarrollo

# 3. Instalar dependencias JavaScript (workspaces)
npm install

# 4. Instalar dependencias Python
cd apps/api
uv sync
cd ../..

# 5. Levantar PostgreSQL local con Docker
docker-compose -f infra/docker-compose.yml up -d

# 6. Aplicar migraciones de base de datos
cd apps/api
alembic upgrade head
cd ../..

# 7. Iniciar el frontend (puerto 3000)
cd apps/web
npm run dev

# 8. Iniciar la API (puerto 8000) — en otra terminal
cd apps/api
uvicorn src.main:app --reload
```

## Scripts npm disponibles desde la raíz

| Comando | Descripción |
|---|---|
| `npm run dev` | Levanta el frontend Next.js en modo desarrollo |
| `npm run build` | Build de producción del frontend |
| `npm run contracts:generate` | Genera tipos TypeScript desde el schema OpenAPI de la API |

## Estructura de carpetas

```
vent3/
├── apps/
│   ├── web/          → Next.js frontend
│   └── api/          → FastAPI backend (Python 3.12)
├── packages/
│   └── contracts/    → Tipos TypeScript generados desde OpenAPI
├── docs/             → SPEC.md, PLAN.md, TASK.md, ADRs
├── infra/            → docker-compose.yml
├── package.json      → Raíz del monorepo (workspaces JS)
└── .env.example      → Plantilla de variables de entorno
```

Ver `docs/PLAN.md §Sección 1` para la estructura de carpetas completa.

## Documentación

- `docs/SPEC.md` — Especificación funcional
- `docs/PLAN.md` — Arquitectura técnica y orden de implementación
- `docs/TASK.md` — Estado actual del proyecto
- `docs/adr/` — Architecture Decision Records
