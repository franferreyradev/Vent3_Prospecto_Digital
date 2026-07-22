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

// ── GTINs ─────────────────────────────────────────────────────────────

type GtinRegistroResponse = components['schemas']['GtinRegistroResponse'];
type GtinUpdateRequest = components['schemas']['GtinUpdateRequest'];

export async function actualizarGtin(
  id: string,
  body: GtinUpdateRequest,
): Promise<GtinRegistroResponse> {
  return apiFetch<GtinRegistroResponse>(`/api/gtins/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

// ── Prospectos ────────────────────────────────────────────────────────

type ProspectoResponse = components['schemas']['ProspectoResponse'];
type ProspectoActivarResponse = components['schemas']['ProspectoActivarResponse'];
type ProspectoListResponse = components['schemas']['PaginatedResponse_ProspectoResponse_'];
type ProspectoDownloadUrlResponse = components['schemas']['ProspectoDownloadUrlResponse'];

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

export interface ListarProspectosParams {
  producto_id?: string;
  estado_vigencia?: string;
  page?: number;
  limit?: number;
  [key: string]: string | number | undefined;
}

export async function listarProspectos(
  params: ListarProspectosParams = {},
): Promise<ProspectoListResponse> {
  return apiFetch<ProspectoListResponse>(`/api/prospectos${buildQuery(params)}`);
}

export async function obtenerUrlDescargaProspecto(id: string): Promise<ProspectoDownloadUrlResponse> {
  return apiFetch<ProspectoDownloadUrlResponse>(`/api/prospectos/${id}/download-url`);
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

// ── Invitaciones ──────────────────────────────────────────────────────

type InvitacionCreateRequest = components['schemas']['InvitacionCreateRequest'];
type InvitacionCreadaResponse = components['schemas']['InvitacionCreadaResponse'];
type InvitacionResponse = components['schemas']['InvitacionResponse'];
type InvitacionListResponse = components['schemas']['PaginatedResponse_InvitacionResponse_'];
type InvitacionValidarResponse = components['schemas']['InvitacionValidarResponse'];
type InvitacionActivarRequest = components['schemas']['InvitacionActivarRequest'];

export async function crearInvitacion(
  body: InvitacionCreateRequest,
): Promise<InvitacionCreadaResponse> {
  return apiFetch<InvitacionCreadaResponse>('/api/invitaciones', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export interface ListarInvitacionesParams {
  estado?: string;
  page?: number;
  limit?: number;
  [key: string]: string | number | undefined;
}

export async function listarInvitaciones(
  params: ListarInvitacionesParams = {},
): Promise<InvitacionListResponse> {
  return apiFetch<InvitacionListResponse>(`/api/invitaciones${buildQuery(params)}`);
}

export async function validarInvitacion(token: string): Promise<InvitacionValidarResponse> {
  return apiFetch<InvitacionValidarResponse>(`/api/invitaciones/validar/${token}`, {
    redirectOn401: false,
  });
}

export async function activarInvitacion(
  token: string,
  body: InvitacionActivarRequest,
): Promise<UsuarioResponse> {
  return apiFetch<UsuarioResponse>(`/api/invitaciones/${token}/activar`, {
    method: 'POST',
    body: JSON.stringify(body),
    redirectOn401: false,
  });
}

// ── Usuarios ──────────────────────────────────────────────────────────

type UsuarioListResponse = components['schemas']['PaginatedResponse_UsuarioResponse_'];
type UsuarioCambiarEstadoRequest = components['schemas']['UsuarioCambiarEstadoRequest'];

export interface ListarUsuariosParams {
  rol?: string;
  activo?: string;
  search?: string;
  page?: number;
  limit?: number;
  [key: string]: string | number | undefined;
}

export async function listarUsuarios(
  params: ListarUsuariosParams = {},
): Promise<UsuarioListResponse> {
  return apiFetch<UsuarioListResponse>(`/api/usuarios${buildQuery(params)}`);
}

export async function cambiarEstadoUsuario(
  id: string,
  body: UsuarioCambiarEstadoRequest,
): Promise<UsuarioResponse> {
  return apiFetch<UsuarioResponse>(`/api/usuarios/${id}/estado`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}
