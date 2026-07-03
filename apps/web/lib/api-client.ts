import type { components } from '@vent3/contracts';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface ApiFetchOptions extends RequestInit {
  /**
   * En /api/auth/login un 401 significa "credenciales inválidas", no
   * "sesión expirada" — ahí no corresponde redirigir, el caller (T19)
   * necesita el detail para mostrarlo en el formulario.
   */
  redirectOn401?: boolean;
}

async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { redirectOn401 = true, ...fetchOptions } = options;
  const isFormData = fetchOptions.body instanceof FormData;

  const response = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    credentials: 'include',
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...fetchOptions.headers,
    },
  });

  if (response.status === 401 && redirectOn401) {
    if (typeof window !== 'undefined') {
      window.location.href = '/admin/login';
    }
    throw new ApiError(401, 'No autenticado');
  }

  if (!response.ok) {
    let detail = 'Error inesperado al comunicarse con el servidor';
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') {
        detail = body.detail;
      }
    } catch {
      // respuesta sin body JSON parseable
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) query.set(key, String(value));
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ── Auth ──────────────────────────────────────────────────────────────

type LoginRequest = components['schemas']['LoginRequest'];
type UsuarioResponse = components['schemas']['UsuarioResponse'];

export async function login(body: LoginRequest): Promise<void> {
  await apiFetch<void>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(body),
    redirectOn401: false,
  });
}

export async function logout(): Promise<void> {
  await apiFetch<void>('/api/auth/logout', { method: 'POST' });
}

export async function getMe(): Promise<UsuarioResponse> {
  return apiFetch<UsuarioResponse>('/api/auth/me');
}

// ── Productos ─────────────────────────────────────────────────────────

type ProductoListResponse = components['schemas']['PaginatedResponse_ProductoListResponse_'];
type ProductoDetalleResponse = components['schemas']['ProductoDetalleResponse'];
type ProductoUpdateRequest = components['schemas']['ProductoUpdateRequest'];
type ProductoCambiarEstadoRequest = components['schemas']['ProductoCambiarEstadoRequest'];

export interface ListarProductosParams {
  estado?: string;
  canal?: string;
  search?: string;
  page?: number;
  limit?: number;
  [key: string]: string | number | undefined;
}

export async function listarProductos(
  params: ListarProductosParams = {},
): Promise<ProductoListResponse> {
  return apiFetch<ProductoListResponse>(`/api/productos${buildQuery(params)}`);
}

export async function obtenerProducto(id: string): Promise<ProductoDetalleResponse> {
  return apiFetch<ProductoDetalleResponse>(`/api/productos/${id}`);
}

export async function actualizarProducto(
  id: string,
  body: ProductoUpdateRequest,
): Promise<ProductoDetalleResponse> {
  return apiFetch<ProductoDetalleResponse>(`/api/productos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export async function cambiarEstadoProducto(
  id: string,
  body: ProductoCambiarEstadoRequest,
): Promise<ProductoDetalleResponse> {
  return apiFetch<ProductoDetalleResponse>(`/api/productos/${id}/estado`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

// ── Prospectos ────────────────────────────────────────────────────────
// Nota: PLAN.md §Sección 3 documenta también `GET /api/prospectos` y
// `GET /api/prospectos/{id}/download-url`, pero esos endpoints no están
// implementados en apps/api/src/routers/prospectos.py (solo existen POST
// "" y PATCH "/{id}/activar"). No se agregan funciones para rutas que no
// existen en el backend — ver docs/TASK.md para el seguimiento de este
// gap.

type ProspectoResponse = components['schemas']['ProspectoResponse'];
type ProspectoActivarResponse = components['schemas']['ProspectoActivarResponse'];

export async function subirProspecto(formData: FormData): Promise<ProspectoResponse> {
  return apiFetch<ProspectoResponse>('/api/prospectos', {
    method: 'POST',
    body: formData,
  });
}

export async function activarProspecto(
  id: string,
  productoId: string,
): Promise<ProspectoActivarResponse> {
  return apiFetch<ProspectoActivarResponse>(`/api/prospectos/${id}/activar`, {
    method: 'PATCH',
    body: JSON.stringify({ producto_id: productoId }),
  });
}

// ── Audit log ─────────────────────────────────────────────────────────

type AuditLogListResponse = components['schemas']['PaginatedResponse_AuditLogResponse_'];

export interface ListarAuditLogParams {
  tabla?: string;
  registro_id?: string;
  usuario_id?: string;
  desde?: string;
  hasta?: string;
  page?: number;
  limit?: number;
  [key: string]: string | number | undefined;
}

export async function listarAuditLog(
  params: ListarAuditLogParams = {},
): Promise<AuditLogListResponse> {
  return apiFetch<AuditLogListResponse>(`/api/audit-log${buildQuery(params)}`);
}
