import argparse
import csv
import datetime
import html as html_lib
import os
import re
import sys
import urllib.robotparser
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://learn.microsoft.com"
CATALOG_URL = f"{BASE}/api/catalog/"
LOCALE = "es-es"

HEADERS = {
    "User-Agent": (
        "TechCourseMetadataBot/1.0 "
        "(Educational Research; "
        "Non-commercial; "
        "+mailto:YOUR_EMAIL@example.com)" # Reemplazar por un correo de contacto antes de ejecutar
    ),
    "Accept": "application/json",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

FIELDNAMES = [
    "id", "titulo", "descripcion", "categoria", "subcategoria", "temario",
    "tecnologias_mencionadas", "tipo_contenido", "nivel_dificultad", "idioma",
    "fuente", "autor", "url", "fecha_publicacion", "licencia",
    "fecha_recoleccion",
]

TIPO_CONTENIDO = {"module": "módulo", "learningPath": "ruta de aprendizaje"}
FUENTE = "microsoft learn"
AUTOR = "Microsoft"
LICENCIA = "Información protegida (derechos de autor)"
IDIOMA = "es"

# Algunos identificadores de temas vienen sin traducir de la taxonomía es-es
# (name == id); se les asignan nombres adecuados en español.
SUBJECT_ES = {
    "app-development": "Desarrollo de aplicaciones",
    "data-integration": "Integración de datos",
    "data-storage": "Almacenamiento de datos",
    "databases": "Bases de datos",
    "cloud-computing": "Computación en la nube",
    "devops": "DevOps",
    "it-management-monitoring": "Gestión y monitoreo de TI",
    "networking": "Redes",
    "security": "Seguridad",
    "artificial-intelligence": "Inteligencia artificial",
    "machine-learning": "Aprendizaje automático",
}

# Términos tecnológicos para tecnologias_mencionadas (la misma lista que en los
# otros scrapers, más nombres del ecosistema de Microsoft).
TECH_TOKENS = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node", "nodejs", "django", "flask", "spring", "sql", "mysql", "mongodb",
    "postgresql", "web", "html", "css", "php", "laravel", "wordpress",
    "android", "ios", "flutter", "kotlin", "swift", "unity", "unreal",
    "docker", "kubernetes", "aws", "azure", "cloud", "linux", "devops",
    "git", "github", "api", "rest", "programacion", "desarrollo", "software",
    "datos", "data", "machine", "learning", "deep", "ia", "chatgpt",
    "ciberseguridad", "hacking", "redes", "cisco", "servidores", "scratch",
    "algoritmos", "backend", "frontend", "fullstack", "csharp", "dotnet",
    "arduino", "robotica", "blockchain", "excel",
    "microsoft", "windows", "powershell", "copilot", "fabric", "dynamics",
    "sharepoint", "teams", "openai", "iot", "blazor",
}

TECH_SYMBOL_PATTERNS = {
    "c#": re.compile(r"(?<![\w#])c#", re.IGNORECASE),
    "c++": re.compile(r"(?<![\w+])c\+\+", re.IGNORECASE),
    ".net": re.compile(r"\.net\b", re.IGNORECASE),
}


def build_session() -> requests.Session:
    """Una sesión para todo: reutilización de conexiones y reintentos con espera progresiva."""
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=5,
        backoff_factor=1.5,          # 0 s, 3 s, 6 s, 12 s y 24 s entre reintentos
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def check_robots(session: requests.Session):
    """Genera un error claro si robots.txt comienza a bloquear la API del catálogo."""
    rp = urllib.robotparser.RobotFileParser()
    resp = session.get(urljoin(BASE, "/robots.txt"), timeout=20)
    resp.raise_for_status()
    rp.parse(resp.text.splitlines())
    # urllib.robotparser no admite el comodín *; también se comprueban los prefijos manualmente.
    disallowed_prefixes = [
        line.split(":", 1)[1].strip().replace("*", "")
        for line in resp.text.splitlines()
        if line.lower().startswith("disallow:")
    ]
    path = urlparse(CATALOG_URL).path
    if any(path.startswith(p) for p in disallowed_prefixes if p) or \
            not rp.can_fetch(HEADERS["User-Agent"], CATALOG_URL):
        raise SystemExit(f"robots.txt now disallows {CATALOG_URL}; aborting.")


def fetch_catalog(session: requests.Session) -> dict:
    resp = session.get(
        CATALOG_URL,
        params={"locale": LOCALE,
                "type": "modules,learningPaths,units,levels,products,subjects"},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


def flatten_products(products: list) -> dict[str, str]:
    names = {}
    for p in products:
        names[p["id"]] = p.get("name") or p["id"]
        for c in p.get("children") or []:
            names[c["id"]] = c.get("name") or c["id"]
    return names


def subject_maps(subjects: list) -> tuple[dict[str, str], dict[str, str]]:
    """id -> nombre visible (con reemplazos en español) e id secundario -> id principal."""
    names, parent = {}, {}
    for s in subjects:
        names[s["id"]] = SUBJECT_ES.get(s["id"], s.get("name") or s["id"])
        for c in s.get("children") or []:
            names[c["id"]] = SUBJECT_ES.get(c["id"], c.get("name") or c["id"])
            parent[c["id"]] = s["id"]
    return names, parent


def clean_url(url: str) -> str:
    """Elimina el parámetro de seguimiento ?WT.mc_id=... que agrega la API."""
    return urlunparse(urlparse(url)._replace(query=""))


def extract_tecnologias(product_names: list[str], *texts: str) -> str:
    blob = " ".join(t for t in texts if t).lower()
    words = set(re.findall(r"[a-z0-9áéíóúñ]+", blob))
    found = set(words & TECH_TOKENS)
    found |= {name for name, pat in TECH_SYMBOL_PATTERNS.items() if pat.search(blob)}
    found |= {n.lower() for n in product_names}
    return ", ".join(sorted(found))


def build_row(item: dict, maps: dict) -> dict:
    unescape = lambda s: html_lib.unescape(s) if isinstance(s, str) else s
    titulo = unescape(item.get("title"))
    descripcion = unescape(item.get("summary"))

    subjects = item.get("subjects") or []
    categoria = subcategoria = ""
    if subjects:
        sid = subjects[0]
        parent = maps["subject_parent"].get(sid)
        if parent:
            categoria = maps["subject_name"].get(parent, parent)
            subcategoria = maps["subject_name"].get(sid, sid)
        else:
            categoria = maps["subject_name"].get(sid, sid)

    if item.get("type") == "module":
        child_titles = [maps["unit_title"].get(u) for u in item.get("units") or []]
    else:
        child_titles = [maps["module_title"].get(m) for m in item.get("modules") or []]
    temario = unescape(" | ".join(t for t in child_titles if t))

    productos = [maps["product_name"].get(p, p) for p in item.get("products") or []]
    levels = item.get("levels") or []
    nivel = maps["level_name"].get(levels[0], levels[0]) if levels else ""

    last_modified = item.get("last_modified") or ""
    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "temario": temario,
        "tecnologias_mencionadas": extract_tecnologias(
            productos, titulo or "", descripcion or "", temario),
        "tipo_contenido": TIPO_CONTENIDO.get(item.get("type"), item.get("type")),
        "nivel_dificultad": nivel,
        "idioma": IDIOMA,
        "fuente": FUENTE,
        "autor": AUTOR,
        "url": clean_url(item.get("url") or ""),
        "fecha_publicacion": last_modified[:10],
        "licencia": LICENCIA,
    }


def load_done_rows(out_path: str) -> tuple[set[str], int]:
    """Devuelve las URL ya recopiladas y el siguiente id secuencial que se asignará."""
    if not os.path.exists(out_path):
        return set(), 1
    with open(out_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    done = {row["url"] for row in rows if row.get("url")}
    max_id = max((int(row["id"]) for row in rows
                  if (row.get("id") or "").isdigit()), default=0)
    return done, max_id + 1


def scrape(limit: int, out_path: str):
    session = build_session()
    check_robots(session)

    done, next_id = load_done_rows(out_path)
    print(f"resuming: {len(done)} rows already in {out_path} (next id: {next_id})",
          file=sys.stderr)

    catalog = fetch_catalog(session)
    maps = {
        "unit_title": {u["uid"]: u.get("title") for u in catalog.get("units", [])},
        "module_title": {m["uid"]: m.get("title") for m in catalog.get("modules", [])},
        "product_name": flatten_products(catalog.get("products", [])),
        "level_name": {l["id"]: l.get("name") for l in catalog.get("levels", [])},
    }
    maps["subject_name"], maps["subject_parent"] = subject_maps(
        catalog.get("subjects", []))

    items = catalog.get("modules", []) + catalog.get("learningPaths", [])
    print(f"catalog: {len(catalog.get('modules', []))} modules + "
          f"{len(catalog.get('learningPaths', []))} learning paths",
          file=sys.stderr)

    new_file = not done
    mode = "w" if new_file else "a"
    kept = skipped = 0
    with open(out_path, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if new_file:
            writer.writeheader()

        for item in items:
            if kept >= limit:
                break
            row = build_row(item, maps)
            if not row["url"] or row["url"] in done:
                skipped += 1
                continue
            writer.writerow({
                "id": next_id,
                "fecha_recoleccion": datetime.date.today().isoformat(),
                **row,
            })
            f.flush()
            next_id += 1
            kept += 1
            if kept % 100 == 0 or kept <= 5:
                print(f"[{kept}/{limit}] {row['categoria']} | {row['titulo']}")

    print(f"Done. kept={kept} skipped={skipped} -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect Spanish training metadata from the Microsoft Learn Catalog API")
    parser.add_argument("--limit", type=int, default=300, help="Target number of NEW rows")
    parser.add_argument("--out", type=str, default="courses_mslearn.csv",
                        help="Output CSV path")
    args = parser.parse_args()
    scrape(args.limit, args.out)
