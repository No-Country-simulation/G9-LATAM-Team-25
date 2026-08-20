// Cliente centralizado para las funcionalidades reales del backend HoneyGuard.
// El navegador llama a rutas /api/* del propio frontend y TanStack Start
// reenvía las solicitudes al backend FastAPI configurado en BACKEND_API_URL.

export type MetadatosDocumento = {
  id: number;
  titulo?: string | null;
  autor?: string | null;
  formato_archivo: string;
  tipo_contenido?: string | null;
  url_archivo: string;
};

export type ClasificacionDocumento = {
  categoria: string;
  probabilidad: number;
  palabras_clave: string[];
  resumen?: string | null;
  requiere_revision: boolean;
};

export type DocumentoRelacionado = {
  id: number;
  titulo?: string | null;
  similitud: number;
};

export type ContenidoExtraido = {
  texto_extraido: string;
  total_palabras: number;
};

export type RespuestaCargaExitosa = {
  metadatos: MetadatosDocumento;
  clasificacion: ClasificacionDocumento;
  contenido_relacionado: DocumentoRelacionado[];
  contenido: ContenidoExtraido;
};

export type RespuestaDuplicado = {
  mensaje: string;
  documento_original: { id: number; titulo?: string | null };
  similitud: number;
};

export type RespuestaCargaArchivo = RespuestaCargaExitosa | RespuestaDuplicado;

export type RespuestaClasificacionTexto = {
  categoria: string;
  probabilidad: number;
  palabras_clave: string[];
  requiere_revision: boolean;
};

export type DocumentoListado = {
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

export type DocumentoCompleto = DocumentoListado & {
  tema?: string | null;
  texto: string;
  contenido_relacionado?: number[] | null;
};

export type RespuestaListaDocumentos = {
  items: DocumentoListado[];
  total: number;
  offset: number;
  limit: number;
};

export type RespuestaBusqueda = {
  resultados: DocumentoListado[];
  total: number;
  query?: string | null;
  filtros: Record<string, string | null>;
  offset: number;
  limit: number;
};

export function esRespuestaDuplicado(
  respuesta: RespuestaCargaArchivo,
): respuesta is RespuestaDuplicado {
  return "mensaje" in respuesta && "documento_original" in respuesta;
}

export class ErrorApiContenido extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ErrorApiContenido";
  }
}

// Alias conservado para no romper imports existentes en subir.tsx.
export class ErrorSubidaArchivo extends ErrorApiContenido {
  constructor(message: string, status?: number) {
    super(message, status);
    this.name = "ErrorSubidaArchivo";
  }
}

async function leerJson<T>(
  res: Response,
  mensajePorDefecto: string,
): Promise<T> {
  const texto = await res.text();

  let data: any = null;

  try {
    data = texto ? JSON.parse(texto) : null;
  } catch {
    data = null;
  }

  if (!res.ok) {
    let mensaje: string | undefined;

    if (Array.isArray(data?.detail)) {
      mensaje = data.detail
        .map((error: any) => {
          const campo = Array.isArray(error?.loc)
            ? error.loc.join(" → ")
            : "campo desconocido";

          return `${campo}: ${error?.msg ?? "Error de validación"}`;
        })
        .join(", ");
    } else {
      mensaje = data?.detail ?? data?.error ?? data?.message;
    }

    if (!mensaje && texto) {
      mensaje = texto;
    }

    throw new ErrorApiContenido(
      mensaje || `${mensajePorDefecto} (HTTP ${res.status})`,
      res.status,
    );
  }

  if (!data) {
    throw new ErrorApiContenido(
      `El servidor respondió sin JSON válido. HTTP ${res.status}. Respuesta: ${
        texto || "vacía"
      }`,
      res.status,
    );
  }

  return data as T;
}

export async function subirArchivoContenido(params: {
  file: File;
  autor: string;
  tipo: string;
}): Promise<RespuestaCargaArchivo> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("autor", params.autor);
  formData.append("tipo", params.tipo);

  let res: Response;
  try {
    res = await fetch("/api/contenido-archivo", {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ErrorSubidaArchivo(
      "No se pudo conectar con el servidor. Verifica tu conexión e inténtalo de nuevo.",
    );
  }

  return leerJson<RespuestaCargaArchivo>(
    res,
    "El backend rechazó la subida. Verifica el archivo e inténtalo de nuevo.",
  );
}

export async function clasificarTextoContenido(params: {
  texto: string;
  top_n_palabras_clave?: number;
}): Promise<RespuestaClasificacionTexto> {
  let res: Response;
  try {
    res = await fetch("/api/clasificar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        texto: params.texto,
        top_n_palabras_clave: params.top_n_palabras_clave ?? 8,
      }),
    });
  } catch {
    throw new ErrorApiContenido("No se pudo conectar con el servicio de clasificación.");
  }

  return leerJson<RespuestaClasificacionTexto>(
    res,
    "No fue posible clasificar el texto.",
  );
}

export type FiltrosContenido = {
  categoria?: string;
  autor?: string;
  tipo_contenido?: string;
  offset?: number;
  limit?: number;
};

function construirQuery(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function buscarContenido(
  q: string,
  filtros: FiltrosContenido = {},
): Promise<RespuestaBusqueda> {
  const query = construirQuery({ q, ...filtros });
  let res: Response;
  try {
    res = await fetch(`/api/buscar${query}`);
  } catch {
    throw new ErrorApiContenido("No se pudo conectar con el servicio de búsqueda.");
  }

  return leerJson<RespuestaBusqueda>(res, "No fue posible buscar contenidos.");
}

export async function listarContenido(
  filtros: FiltrosContenido = {},
): Promise<RespuestaListaDocumentos> {
  const query = construirQuery(filtros);
  let res: Response;
  try {
    res = await fetch(`/api/contenido${query}`);
  } catch {
    throw new ErrorApiContenido("No se pudo conectar con el repositorio de documentos.");
  }

  return leerJson<RespuestaListaDocumentos>(res, "No fue posible listar los documentos.");
}

export async function obtenerContenidoPorId(id: number): Promise<DocumentoCompleto> {
  let res: Response;
  try {
    res = await fetch(`/api/contenido/${id}`);
  } catch {
    throw new ErrorApiContenido("No se pudo conectar con el repositorio de documentos.");
  }

  return leerJson<DocumentoCompleto>(res, "No fue posible obtener el documento.");
}
