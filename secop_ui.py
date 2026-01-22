# secop_ui.py
"""
Interfaz web Flask para procesamiento por lotes de constancias SECOP.

Proporciona:
- Interfaz HTML simple para ingresar constancias
- Deteccion automatica de constancias en texto pegado
- Procesamiento secuencial con manejo de reCAPTCHA
- Empaquetado automatico de resultados en ZIP
- Descargas seguras con tokens aleatorios
"""

from __future__ import annotations

import os
import secrets
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Optional
from html import escape

from flask import Flask, request, send_file, render_template, url_for, redirect, after_this_request, session, jsonify

import secop_extract
import constancia_config

# ============================================================================
# CONFIGURACION DE LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

APP = Flask(__name__)

# ============================================================================
# CONFIGURACION DE SEGURIDAD
# ============================================================================
secret = os.environ.get("SECOP_UI_SECRET")
if not secret:
    secret = "secop-ui-local-default"
    logger.warning(
        "ALERTA Variable SECOP_UI_SECRET no configurada. "
        "Usa una clave segura en produccion."
    )

APP.secret_key = secret

# ============================================================================
# CONFIGURACION DE DIRECTORIOS Y DESCARGAS
# ============================================================================
DEFAULT_OUTPUT_DIR = Path.home() / "secop_exports"
OUTPUT_DIR = Path(os.environ.get("SECOP_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapeo en memoria: token -> (ruta de archivo, timestamp de creacion)
# Se limpia automaticamente de archivos mas antiguos que MAX_DOWNLOAD_AGE_SECONDS
_DOWNLOADS: Dict[str, Tuple[Path, float]] = {}
MAX_DOWNLOAD_AGE_SECONDS = 3600  # 1 hora
MAX_ERRORS_DISPLAY = 25  # Limite de errores mostrados en UI

# Mapeo en memoria: workspace_id -> (ruta de archivo, timestamp, ok_count)
_WORKSPACES: Dict[str, Tuple[Path, float, int]] = {}
MAX_WORKSPACE_AGE_SECONDS = 6 * 3600  # 6 horas


def cleanup_old_downloads(max_age_seconds: int = MAX_DOWNLOAD_AGE_SECONDS) -> int:
    """
    Elimina archivos de descarga mas antiguos que max_age_seconds.
    Se ejecuta antes de cada descarga para mantener almacenamiento limpio.
    
    Args:
        max_age_seconds: Edad maxima en segundos antes de eliminar
        
    Returns:
        Numero de archivos eliminados
    """
    now = time.time()
    expired_tokens = [
        token 
        for token, (path, timestamp) in _DOWNLOADS.items() 
        if now - timestamp > max_age_seconds
    ]
    
    deleted_count = 0
    for token in expired_tokens:
        path, _ = _DOWNLOADS[token]
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Archivo expirado eliminado: {path.name}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error eliminando archivo {path}: {e}")
        finally:
            del _DOWNLOADS[token]
    
    if deleted_count > 0:
        logger.debug(f"Limpieza: {deleted_count} archivo(s) expirado(s) eliminado(s)")
    
    return deleted_count


def cleanup_old_workspaces(max_age_seconds: int = MAX_WORKSPACE_AGE_SECONDS) -> int:
    """
    Elimina workspaces acumulativos antiguos y sus archivos asociados.
    """
    now = time.time()
    expired = [
        workspace_id
        for workspace_id, (path, timestamp, _) in _WORKSPACES.items()
        if now - timestamp > max_age_seconds
    ]

    deleted_count = 0
    for workspace_id in expired:
        path, _, _ = _WORKSPACES[workspace_id]
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Workspace expirado eliminado: {path.name}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error eliminando workspace {path}: {e}")
        finally:
            del _WORKSPACES[workspace_id]
    return deleted_count


def _get_workspace_info() -> Tuple[str, Optional[Path], int]:
    workspace_id = session.get("workspace_id")
    if not workspace_id:
        return "", None, 0
    info = _WORKSPACES.get(workspace_id)
    if not info:
        session.pop("workspace_id", None)
        return "", None, 0
    path, _, count = info
    return workspace_id, path, count


def _render_main(raw: str, result: Optional[dict], mode: str, accumulate: bool, auto_download: bool = False):
    _, batch_path, batch_count = _get_workspace_info()
    return render_template(
        "index.html",
        raw=raw,
        result=result,
        mode=mode,
        version=constancia_config.__version__,
        accumulate=accumulate,
        batch_active=bool(batch_path),
        batch_count=batch_count,
        batch_name=batch_path.name if batch_path else "-",
        auto_download=auto_download,
    )


def _resolve_output_path(path_value: str) -> Tuple[Optional[Path], Optional[str]]:
    if not path_value:
        return None, "Ruta vacia."
    try:
        resolved = Path(path_value).expanduser().resolve()
    except Exception:
        return None, "Ruta invalida."
    output_root = OUTPUT_DIR.resolve()
    if resolved != output_root and output_root not in resolved.parents:
        return None, "Ruta fuera del directorio permitido."
    return resolved, None




# ============================================================================
# RUTAS
# ============================================================================

@APP.get("/")
def index():
    """Pagina principal con formulario de entrada."""
    cleanup_old_downloads()
    cleanup_old_workspaces()
    return _render_main(raw="", result=None, mode="normal", accumulate=False)


@APP.post("/open-folder")
def open_folder():
    data = request.get_json(silent=True) or {}
    resolved, error = _resolve_output_path(data.get("path", ""))
    if error:
        return jsonify(ok=False, error=error), 400
    if not resolved.exists():
        return jsonify(ok=False, error="Ruta no encontrada."), 404
    target = resolved if resolved.is_dir() else resolved.parent
    try:
        os.startfile(str(target))
    except Exception:
        return jsonify(ok=False, error="No se pudo abrir la carpeta."), 500
    return jsonify(ok=True)


@APP.post("/open-file")
def open_file():
    data = request.get_json(silent=True) or {}
    resolved, error = _resolve_output_path(data.get("path", ""))
    if error:
        return jsonify(ok=False, error=error), 400
    if not resolved.exists() or not resolved.is_file():
        return jsonify(ok=False, error="Archivo no encontrado."), 404
    try:
        os.startfile(str(resolved))
    except Exception:
        return jsonify(ok=False, error="No se pudo abrir el archivo."), 500
    return jsonify(ok=True)


@APP.post("/extract")
def extract():
    """
    Endpoint de procesamiento de constancias.
    
    Recibe:
    - POST form field "raw": texto con constancias (una por linea o tabla)
    
    Retorna:
    - HTML con resultados o lista de errores
    """
    raw = request.form.get("raw", "").strip()
    mode = request.form.get("mode", "normal").strip().lower()
    accumulate = False
    cleanup_old_workspaces()
    
    # Validacion: entrada vacia
    if not raw:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "-",
            "output_path": "-",
            "download_url": None,
            "errors": [],
            "has_more_errors": False,
            "total_errors": 0,
        }
        logger.warning("POST /extract con entrada vacia")
        return _render_main(raw=raw, result=result, mode=mode, accumulate=accumulate)
    
    # Extraccion de constancias
    constancias = constancia_config.extract_constancias(raw)
    detected_count = len(constancias)
    
    if detected_count == 0:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "-",
            "output_path": "-",
            "download_url": None,
            "errors": [],
            "has_more_errors": False,
            "total_errors": 0,
        }
        logger.warning(f"No se detectaron constancias validas en entrada: {raw[:100]}")
        return _render_main(raw=raw, result=result, mode=mode, accumulate=accumulate)
    
    logger.info(f"Iniciando extraccion de {detected_count} constancia(s)")

    # Proceso secuencial (permite interaccion manual con reCAPTCHA)
    if mode == "seguro":
        delay_seconds = 30.0
        backoff_max_seconds = 600.0
    else:
        delay_seconds = 10.0
        backoff_max_seconds = 120.0

    final_path, errors = secop_extract.extract_batch_to_excel(
        constancias,
        OUTPUT_DIR,
        headless=False,
        delay_seconds=delay_seconds,
        backoff_max_seconds=backoff_max_seconds,
    )
    download_url = None

    ok_count = detected_count - len(errors)
    fail_count = len(errors)

    output_name = final_path.name
    output_path = str(final_path)
    token = secrets.token_urlsafe(16)
    _DOWNLOADS[token] = (final_path, time.time())
    download_url = url_for("download", token=token)
    
    # Limitar errores mostrados en UI
    errors_safe = [(c, escape(str(e))) for c, e in errors]
    errors_ui = errors_safe[:MAX_ERRORS_DISPLAY]
    has_more_errors = len(errors) > MAX_ERRORS_DISPLAY
    
    result = {
        "detected_count": detected_count,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "output_name": output_name,
        "output_path": output_path,
        "download_url": download_url,
        "errors": errors_ui,
        "has_more_errors": has_more_errors,
        "total_errors": len(errors),
    }
    
    return _render_main(raw=raw, result=result, mode=mode, accumulate=accumulate, auto_download=False)


@APP.post("/finalize")
def finalize():
    """
    Cierra el lote acumulativo actual y habilita descarga.
    """
    cleanup_old_downloads()
    cleanup_old_workspaces()

    workspace_id, batch_path, batch_count = _get_workspace_info()
    if not workspace_id or not batch_path or not batch_path.exists():
        return redirect(url_for("index"))

    token = secrets.token_urlsafe(16)
    _DOWNLOADS[token] = (batch_path, time.time())
    _WORKSPACES.pop(workspace_id, None)
    session.pop("workspace_id", None)

    result = {
        "detected_count": batch_count,
        "ok_count": batch_count,
        "fail_count": 0,
        "output_name": batch_path.name,
        "output_path": str(batch_path),
        "download_url": url_for("download", token=token),
        "errors": [],
        "has_more_errors": False,
        "total_errors": 0,
    }

    return _render_main(raw="", result=result, mode="normal", accumulate=False)


@APP.post("/reset_batch")
def reset_batch():
    """
    Reinicia el lote acumulativo actual y elimina su archivo.
    """
    workspace_id, batch_path, _ = _get_workspace_info()
    if batch_path and batch_path.exists():
        try:
            batch_path.unlink()
            logger.info(f"Lote reiniciado eliminado: {batch_path.name}")
        except Exception as e:
            logger.error(f"Error eliminando lote {batch_path}: {e}")
    if workspace_id:
        _WORKSPACES.pop(workspace_id, None)
    session.pop("workspace_id", None)
    return redirect(url_for("index"))


@APP.get("/download/<token>")
def download(token: str):
    """
    Descarga segura de archivo generado.
    
    Parametros:
    - token: token aleatorio unico asignado en /extract
    
    Retorna:
    - Archivo (XLSX o ZIP) si existe y es valido
    - Redireccion a indice si no existe
    """
    # Limpiar descargas antiguas
    cleanup_old_downloads()
    
    # Buscar token
    download_info = _DOWNLOADS.get(token)
    if not download_info:
        logger.warning(f"Intento de descarga con token invalido: {token}")
        return redirect(url_for("index"))
    
    path, _ = download_info
    
    # Validacion de existencia
    if not path or not path.exists():
        logger.warning(f"Intento de descargar archivo inexistente: {path}")
        return redirect(url_for("index"))
    
    @after_this_request
    def _cleanup_download(response):
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Archivo descargado eliminado: {path.name}")
        except Exception as e:
            logger.error(f"Error eliminando archivo descargado {path}: {e}")
        finally:
            _DOWNLOADS.pop(token, None)
        return response

    # Descarga segura
    try:
        logger.info(f"Descargando: {path.name}")
        return send_file(
            path, 
            as_attachment=True, 
            download_name=path.name
        )
    except Exception as e:
        logger.error(f"Error descargando {path}: {e}")
        return redirect(url_for("index"))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("Iniciando SECOP UI en http://127.0.0.1:5000")
    APP.run(host="127.0.0.1", port=5000, debug=False)
