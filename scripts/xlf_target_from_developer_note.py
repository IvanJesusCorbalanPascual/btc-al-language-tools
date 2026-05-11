#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Este script procesa archivos XLF y rellena etiquetas <target> tomando como base
# notas de desarrollador que contienen códigos de idioma como ESP=, DEU=, FRA=.
"""
Rellena <target> en un fichero XLF a partir del texto entre comillas en las notas
de desarrollador (p. ej. ESP="...", DEU="...", FRA="...").

El script detecta automáticamente qué códigos de idioma están presentes en las
notas Developer del .g.xlf base y genera un fichero de salida por cada idioma
encontrado (p. ej. MiExtension.es-ES.g.xlf, MiExtension.de-DE.g.xlf, ...).

Por defecto se busca la carpeta Translations en el directorio actual y, si no
existe, en la raíz del repositorio (carpeta padre de scripts/). Si hay varios
.g.xlf base, se elige en un menú. La ruta -i relativa se busca primero en el cwd
y luego en la raíz del repo.

Uso:
  python scripts/xlf_target_from_developer_note.py
  python scripts/xlf_target_from_developer_note.py --lang de
  python scripts/xlf_target_from_developer_note.py -i "Translations/MiApp.g.xlf"
"""

from __future__ import annotations
# Importación del futuro para facilitar las anotaciones de tipo en Python.

import argparse 
import json 
import re 
import sys 
import xml.etree.ElementTree as ET 
from pathlib import Path 

# Carpeta del script (p. ej. .../proyecto/scripts); la raíz del repo es el padre.
# Carpeta del script actual (identifica su ubicación en el sistema).
_SCRIPT_DIR = Path(__file__).resolve().parent
# Carpeta raíz del repositorio, se asume como el padre del directorio del script.
_REPO_ROOT = _SCRIPT_DIR.parent

# Código en la nota del desarrollador → (código BCP 47 para <file target-language>, sufijo sugerido del fichero)
# Mapeo entre códigos internos de las notas de desarrollador y códigos BCP 47.
LANGUAGE_MAP = {
    "es": ("ESP", "es-ES"),
    "fr": ("FRA", "fr-FR"),
    "de": ("DEU", "de-DE"),
}

# Etiquetas más descriptivas para los idiomas soportados.
LANGUAGE_LABELS = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

# Dinámica de Idiomas
# Carga una configuración externa de idiomas desde un archivo JSON, construyendo
# estructuras útiles para los mapas de traducciones y etiquetas de idioma.
def load_language_config() -> tuple[dict, dict, dict]:
    """Lee el JSON externo y construye los diccionarios de configuración."""
    cwd = Path.cwd()
    
    # Posibles rutas donde buscar languages.json (de mayor a menor prioridad)
    candidates = [
        cwd / ".vscode" / "languages.json",
        cwd / "languages.json",
        cwd / "Translations" / "languages.json",
        cwd / "translations" / "languages.json",
    ]
    
    config_path = None
    for candidate in candidates:
        if candidate.is_file():
            config_path = candidate
            break

    # Si no existe el archivo, creamos uno por defecto con idiomas básicos.
    if not config_path:
        default_config = {
            "es": {"note_code": "ESP", "bcp47": "es-ES", "label": "Spanish"},
            "fr": {"note_code": "FRA", "bcp47": "fr-FR", "label": "French"},
            "de": {"note_code": "DEU", "bcp47": "de-DE", "label": "German"}
        }
        config_path = cwd / ".vscode" / "languages.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"INFO: Default configuration file created: {config_path}")
        except Exception as e:
            print(f"Error creating 'languages.json' configuration file: {e}", file=sys.stderr)
            sys.exit(1)
        
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lang_map = {}
    lang_labels = {}
    note_code_to_lang = {}

    for lang_key, info in data.items():
        note_code = info["note_code"]
        bcp47 = info["bcp47"]
        label = info["label"]

        # Reconstruimos las estructuras que el resto del script necesita
        lang_map[lang_key] = (note_code, bcp47)
        lang_labels[lang_key] = label
        note_code_to_lang[note_code] = (lang_key, bcp47, label)

    return lang_map, lang_labels, note_code_to_lang

# Inicializamos las variables globales cargando el JSON
LANGUAGE_MAP, LANGUAGE_LABELS, _NOTE_CODE_TO_LANG = load_language_config()

# Ficheros ya traducidos suelen ser Nombre.es-ES.g.xlf (sufijo BCP 47 antes de .g.xlf)
# Expresión regular para identificar sufijos de archivos locales, como 'es-ES' en nombres de archivo.
_LOCALE_STEM_SUFFIX = re.compile(r"^(.+)\.[a-z]{2}-[A-Z]{2}$")


# Extrae el nombre base lógico de un archivo .g.xlf, eliminando información 
# de sufijos de idioma, como '.es-ES', para evitar duplicaciones.
def _logical_base_name_from_g_xlf(path: Path) -> str:
    """
    MiApp.g.xlf -> MiApp
    MiApp.de-DE.g.xlf -> MiApp (para no duplicar .de-DE.de-DE)
    """
    name = path.name
    if not name.endswith(".g.xlf"):
        return path.stem
    stem = name[: -len(".g.xlf")]
    m = _LOCALE_STEM_SUFFIX.match(stem)
    if m:
        return m.group(1)
    return stem


# Verifica si un archivo tiene un sufijo local correspondiente a un idioma
# (por ejemplo, 'nombre.es-ES.g.xlf').
def _is_locale_g_xlf_filename(name: str) -> bool:
    """True si parece Nombre.xx-XX.g.xlf (fichero de idioma), no el .g.xlf base."""
    if not name.endswith(".g.xlf"):
        return False
    stem = name[: -len(".g.xlf")]
    return _LOCALE_STEM_SUFFIX.match(stem) is not None


# Busca en un directorio específico todos los archivos .g.xlf que no contienen
# sufijos de idioma (archivos base para traducciones).
def _discover_base_g_xlf_files(translations_dir: Path) -> list[Path]:
    """*.g.xlf en la carpeta que son bases (excluye *.xx-XX.g.xlf)."""
    if not translations_dir.is_dir():
        return []
    found: list[Path] = []
    for p in sorted(translations_dir.iterdir()):
        if not p.is_file():
            continue
        if _is_locale_g_xlf_filename(p.name):
            continue
        if p.name.endswith(".g.xlf"):
            found.append(p)
    return found


def _prompt_input_file(candidates: list[Path]) -> Path:
    print("Base .g.xlf files found:")
    for i, p in enumerate(candidates, start=1):
        print(f"  {i}) {p.name}")
    choice = input(f"Select 1-{len(candidates)} [1]: ").strip() or "1"
    try:
        idx = int(choice)
    except ValueError:
        print("Invalid option.", file=sys.stderr)
        sys.exit(1)
    if idx < 1 or idx > len(candidates):
        print("Option out of range.", file=sys.stderr)
        sys.exit(1)
    return candidates[idx - 1]


# Resuelve la ruta de un archivo proporcionado por el usuario, buscando en distintas
# ubicaciones predefinidas (directorio actual, raíz del repo, etc.).
def _resolve_user_input_file(path: Path) -> Path:
    """
    Resuelve --input: primero desde el directorio de trabajo, luego desde la raíz
    del repo (donde está Translations/ si ejecutas el script desde scripts/ u otra carpeta).
    """
    path = path.expanduser()
    if path.is_absolute():
        return path
    trials = (
        Path.cwd() / path,
        _REPO_ROOT / path,
        _SCRIPT_DIR / path,
    )
    for t in trials:
        resolved = t.resolve()
        if resolved.is_file():
            return resolved
    return (Path.cwd() / path).resolve()


# Determina la ruta del archivo de entrada según el argumento explícito o
# busca automáticamente archivos base en el directorio de traducciones.
def _resolve_input_path(
    explicit: Path | None,
    translations_dir: Path,
) -> Path:
    if explicit is not None:
        return _resolve_user_input_file(explicit)
    candidates = _discover_base_g_xlf_files(translations_dir)
    if not candidates:
        print(
            f"No base .g.xlf file found in {translations_dir}. "
            "Use --input or create a MyProject.g.xlf file (not MyProject.de-DE.g.xlf).",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(candidates) == 1:
        return candidates[0]
    return _prompt_input_file(candidates)


def _default_output_path(input_path: Path, bcp47: str) -> Path:
    base = _logical_base_name_from_g_xlf(input_path)
    return input_path.parent / f"{base}.{bcp47}.g.xlf"


# Encuentra el directorio de traducciones predeterminado. Busca directorios
# llamados 'Translations' en el directorio actual o en la raíz del repositorio.
def _default_translations_dir() -> Path:
    """
    Busca la carpeta de traducciones en este orden (sin duplicar la misma ruta):
    ./Translations desde el cwd, luego la raíz del repo (padre de scripts/).
    Así funciona aunque ejecutes el script desde scripts/ o desde Cursor con cwd distinto.
    """
    cwd = Path.cwd()
    candidates = [
        cwd / "Translations",
        cwd / "translations",
        _REPO_ROOT / "Translations",
        _REPO_ROOT / "translations",
    ]
    seen: set[Path] = set()
    for p in candidates:
        r = p.resolve()
        if r in seen:
            continue
        seen.add(r)
        if r.is_dir():
            return r
    print(
        "No Translations folder found. Tested paths:",
        file=sys.stderr,
    )
    for r in seen:
        print(f"  - {r}", file=sys.stderr)
    print(
        "Specify the folder with -t / --translations-dir or run the script "
        "from the project root (where the Translations folder is located).",
        file=sys.stderr,
    )
    sys.exit(1)


def _ns_uri(root: ET.Element) -> str:
    if root.tag.startswith("{"):
        return root.tag.split("}")[0][1:]
    return ""


def _q(ns_uri: str, local: str) -> str:
    return f"{{{ns_uri}}}{local}" if ns_uri else local


# Extrae un valor asociado a un código específico dentro del texto de una nota
# de desarrollador, con el formato CODE="...".
def _extract_from_note(note_text: str, code: str) -> str | None:
    """Devuelve el valor de CODE = \"...\" o None si no existe."""
    if not note_text:
        return None
    # CODE = "..." con espacios opcionales; el valor no puede contener comillas sin escapar (convención AL)
    m = re.search(rf"\b{re.escape(code)}\s*=\s*\"([^\"]*)\"", note_text)
    if not m:
        return None
    return m.group(1)


def _discover_note_codes(input_path: Path) -> list[str]:
    """
    Escanea el .g.xlf base y devuelve los códigos de idioma (p. ej. ["DEU", "ESP", "FRA"])
    que aparecen en al menos una nota Developer con el patrón CODE = "...".
    Solo se devuelven códigos registrados en LANGUAGE_MAP.
    """
    tree = ET.parse(input_path)
    root = tree.getroot()
    ns_uri = _ns_uri(root)
    q_tu = _q(ns_uri, "trans-unit")
    q_note = _q(ns_uri, "note")
    pattern = re.compile(r'\b([A-Z]{2,4})\s*=\s*"[^"]*"')
    found: set[str] = set()
    known_codes = {note_code for note_code, *_ in LANGUAGE_MAP.values()}

    for trans_unit in root.iter(q_tu):
        for el in trans_unit:
            if el.tag != q_note:
                continue
            if el.get("from") != "Developer":
                continue
            text = "".join(el.itertext())
            for m in pattern.finditer(text):
                code = m.group(1)
                if code in known_codes:
                    found.add(code)

    return sorted(found)


def _set_or_replace_target(trans_unit: ET.Element, ns_uri: str, text: str) -> None:
    q_target = _q(ns_uri, "target")
    existing = None
    for child in trans_unit:
        if child.tag == q_target:
            existing = child
            break
    if existing is not None:
        existing.text = text
        return
    target_el = ET.Element(q_target)
    target_el.text = text
    # Insertar <target> justo después de <source>
    children = list(trans_unit)
    insert_at = 0
    for i, ch in enumerate(children):
        if ch.tag == _q(ns_uri, "source"):
            insert_at = i + 1
            break
    trans_unit.insert(insert_at, target_el)


def _update_file_target_language(file_el: ET.Element, lang: str) -> None:
    file_el.set("target-language", lang)


# Procesa un archivo XLF, rellenando etiquetas <target> basadas en las notas
# de desarrollador y el código de idioma proporcionado. Devuelve estadísticas
# sobre las actualizaciones realizadas y omisiones (claves no encontradas).
def process_xlf(
    input_path: Path,
    output_path: Path,
    note_code: str,
    target_lang: str,
) -> tuple[int, int]:
    """
    Devuelve (n_actualizados, n_omitidos_sin_clave).
    """
    tree = ET.parse(input_path)
    root = tree.getroot()
    ns_uri = _ns_uri(root)
    q_tu = _q(ns_uri, "trans-unit")
    updated = 0
    skipped = 0

    for trans_unit in root.iter(q_tu):
        dev_text = None
        for el in trans_unit:
            if el.tag != _q(ns_uri, "note"):
                continue
            if el.get("from") != "Developer":
                continue
            dev_text = "".join(el.itertext())
            break
        if dev_text is None:
            continue
        value = _extract_from_note(dev_text, note_code)
        if value is None:
            skipped += 1
            continue
        _set_or_replace_target(trans_unit, ns_uri, value)
        updated += 1

    file_el = root.find(_q(ns_uri, "file"))
    if file_el is not None:
        _update_file_target_language(file_el, target_lang)

    if ns_uri:
        ET.register_namespace("", ns_uri)
    ET.indent(tree.getroot(), space="  ")

    tree.write(
        str(output_path),
        encoding="utf-8",
        xml_declaration=True,
    )
    return updated, skipped


def _configure_stdout_utf8() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError, AttributeError):
        pass


def _process_single_lang(
    input_path: Path,
    note_code: str,
    bcp47: str,
    label: str,
    output_override: Path | None,
) -> None:
    out = output_override or _default_output_path(input_path, bcp47)
    print(f"\nLanguage: {label} ({note_code}= -> target-language {bcp47})")
    print(f"  Output: {out}")
    updated, skipped = process_xlf(input_path, out, note_code, bcp47)
    print(
        f"  Done:   {updated} <target> updated; "
        f"{skipped} notes missing {note_code}= key (skipped)."
    )


# Punto de entrada principal del script. Procesa argumentos de usuario, detecta
# idiomas en las notas de desarrollador, y genera archivos XLF para cada idioma.
def main() -> None:
    _configure_stdout_utf8()
    parser = argparse.ArgumentParser(
        description=(
            "Rellena <target> desde ESP=/DEU=/FRA= en notas Developer del XLF base. "
            "Por defecto detecta automáticamente los idiomas presentes en el fichero "
            "y genera un .g.xlf de salida por cada uno."
        )
    )
    
    # 1. Argumento: Directorio de traducciones
    parser.add_argument(
        "--translations-dir",
        "-t",
        type=Path,
        help="Carpeta con los XLF (por defecto: Translations junto al cwd o en la raíz del repo)",
    )

    # 2. Argumento: Archivo de entrada
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Fichero .g.xlf base. Si se omite, se listan los *.g.xlf base en --translations-dir y se elige uno.",
    )

    # 3. Argumento: Archivo de salida
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Fichero de salida (solo cuando se usa --lang). Por defecto: <nombre lógico>.<locale>.g.xlf junto al fichero de entrada.",
    )

    # 4. Argumento: Idioma (¡La versión limpia y dinámica, UNA SOLA VEZ!)
    texto_ayuda = f"Genera solo este idioma: {', '.join([f'{k}={v[0]}' for k, v in LANGUAGE_MAP.items()])}. Si se omite, se generan todos los idiomas."
    parser.add_argument(
        "--lang",
        choices=list(LANGUAGE_MAP.keys()),
        help=texto_ayuda
    )
    
    args = parser.parse_args()

    translations_dir = (args.translations_dir or _default_translations_dir()).resolve()
    if args.translations_dir is None:
        print(f"XLF Folder: {translations_dir}")
        
    input_path = _resolve_input_path(args.input, translations_dir)
    if not input_path.is_file():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Input:    {input_path}")
    
    # Resto de la lógica del main...
    if args.lang:
        note_code, bcp47 = LANGUAGE_MAP[args.lang]
        label = LANGUAGE_LABELS[args.lang]
        _process_single_lang(input_path, note_code, bcp47, label, args.output)
    else:
        if args.output:
            print("WARNING: --output is ignored in automatic mode. Use --lang to select a language.", file=sys.stderr)
        detected_codes = _discover_note_codes(input_path)
        if not detected_codes:
            print("No known language code found.", file=sys.stderr)
            sys.exit(1)

        print(f"Languages detected in notes: {', '.join(detected_codes)}")
        for note_code in detected_codes:
            lang_key, bcp47, label = _NOTE_CODE_TO_LANG[note_code]
            _process_single_lang(input_path, note_code, bcp47, label, None)

# Verifica si el archivo se está ejecutando como script principal.
if __name__ == "__main__":
    main()