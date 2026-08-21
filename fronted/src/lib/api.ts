// Cliente del backend HoneyGuard (FastAPI). Todas las llamadas pasan por el
// proxy de mismo origen /api/backend/* definido en src/routes/api/backend/$.ts.

export type Clasificacion = {
  categoria: string;
  probabilidad: number;
  palabras_clave: string[];
  resumen?: string | null;
  requiere_revision: boolean;
};

export type Metadatos = {
  id: number;
  titulo?: string | null;
  autor?: string | null;
  formato_archivo: string;
  tipo_contenido?: string | null;
  url_archivo: string;
};

export type DocumentoRelacionado = {
  id: number;
  titulo?: string | null;
  similitud: number;
};

export type CargaExitosa = {
  metadatos: Metadatos;
  clasificacion: Clasificacion;
  contenido_relacionado?: DocumentoRelacionado[];
  contenido: { texto_extraido: string; total_palabras: number };
};

export type Duplicado = {
  mensaje: string;
  documento_original: { id: number; titulo?: string | null };
  similitud: number;
};

export type Documento = {
  id: number;
  titulo?: string | null;
  autor?: string | null;
  categoria: string;
  probabilidad: number;
  resumen?: string | null;
  palabras_clave?: string[] | null;
  formato_archivo: string;
  tipo_contenido?: string | null;
  url_archivo: string;
  fecha_creacion: string;
};

export type DocumentoDetalle = Documento & {
  tema?: string | null;
  texto: string;
  contenido_relacionado?: number[] | null;
};

export type ListaDocumentos = {
  items: Documento[];
  total: number;
  offset: number;
  limit: number;
};

export type RespuestaBusqueda = {
  resultados: Documento[];
  total: number;
  query?: string | null;
  filtros: Record<string, unknown>;
  offset: number;
  limit: number;
};

export type ClasificarTextoResponse = {
  categoria: string;
  probabilidad: number;
  palabras_clave: string[];
  requiere_revision: boolean;
};

export function esDuplicado(data: unknown): data is Duplicado {
  return !!data && typeof data === "object" && "documento_original" in (data as object);
}

function mensajeError(data: any, fallback: string) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return data?.error ?? data?.mensaje ?? fallback;
}

async function leer<T>(res: Response, fallback: string): Promise<T> {
  const data = await res.json().catch(() => null);
  if (!res.ok || data === null) throw new Error(mensajeError(data, fallback));
  return data as T;
}

const base = "/api/backend";

export async function clasificarTexto(texto: string): Promise<ClasificarTextoResponse> {
  const res = await fetch(`${base}/contenido/clasificar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto, top_n_palabras_clave: 8 }),
  });
  return leer(res, "No se pudo clasificar el texto.");
}

export async function subirArchivo(input: {
  file: File;
  autor: string;
  tipo: string;
}): Promise<CargaExitosa | Duplicado> {
  const formData = new FormData();
  formData.append("file", input.file);
  formData.append("autor", input.autor);
  formData.append("tipo", input.tipo);

  const res = await fetch(`${base}/contenido/archivo`, { method: "POST", body: formData });
  return leer(res, "El backend rechazó la subida. Verifica el archivo e inténtalo de nuevo.");
}

export type FiltrosBusqueda = {
  q?: string;
  categoria?: string;
  autor?: string;
  tipo_contenido?: string;
  offset?: number;
  limit?: number;
};

function query(filtros: Record<string, unknown>) {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(filtros)) {
    if (v !== undefined && v !== null && `${v}`.trim() !== "") params.set(k, `${v}`);
  }
  const s = params.toString();
  return s ? `?${s}` : "";
}

export async function buscarContenido(filtros: FiltrosBusqueda): Promise<RespuestaBusqueda> {
  const res = await fetch(`${base}/buscar${query(filtros)}`);
  return leer(res, "No se pudo realizar la búsqueda.");
}

export async function listarContenido(filtros: FiltrosBusqueda = {}): Promise<ListaDocumentos> {
  const res = await fetch(`${base}/contenido${query(filtros)}`);
  return leer(res, "No se pudo cargar la biblioteca.");
}

export async function obtenerContenido(id: number | string): Promise<DocumentoDetalle> {
  const res = await fetch(`${base}/contenido/${id}`);
  return leer(res, "No se pudo cargar el documento.");
}

export function porcentaje(valor: number) {
  const n = valor <= 1 ? valor * 100 : valor;
  return Math.round(n);
}

export function colorConfianza(valor: number) {
  const p = porcentaje(valor);
  if (p >= 75) return "var(--confianza-alta)";
  if (p >= 50) return "var(--confianza-media)";
  return "var(--confianza-baja)";
}
