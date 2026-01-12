# secop_ui.py
"""
Interfaz web Flask para procesamiento por lotes de constancias SECOP.

Proporciona:
- Interfaz HTML simple para ingresar constancias
- Detección automática de constancias en texto pegado
- Procesamiento secuencial con manejo de reCAPTCHA
- Empaquetado automático de resultados en ZIP
- Descargas seguras con tokens aleatorios
"""

from __future__ import annotations

import os
import secrets
import logging
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from html import escape

from flask import Flask, request, send_file, render_template_string, url_for, redirect

import secop_extract
import constancia_config

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

APP = Flask(__name__)

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================================================
secret = os.environ.get("SECOP_UI_SECRET")
if not secret:
    secret = "secop-ui-local-default"
    logger.warning(
        "⚠️ Variable SECOP_UI_SECRET no configurada. "
        "Usa una clave segura en producción."
    )

APP.secret_key = secret

# ============================================================================
# CONFIGURACIÓN DE DIRECTORIOS Y DESCARGAS
# ============================================================================
DEFAULT_OUTPUT_DIR = Path.home() / "secop_exports"
OUTPUT_DIR = Path(os.environ.get("SECOP_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapeo en memoria: token -> (ruta de archivo, timestamp de creación)
# Se limpia automáticamente de archivos más antiguos que MAX_DOWNLOAD_AGE_SECONDS
_DOWNLOADS: Dict[str, Tuple[Path, float]] = {}
MAX_DOWNLOAD_AGE_SECONDS = 3600  # 1 hora
MAX_ERRORS_DISPLAY = 25  # Límite de errores mostrados en UI


def cleanup_old_downloads(max_age_seconds: int = MAX_DOWNLOAD_AGE_SECONDS) -> int:
    """
    Elimina archivos de descarga más antiguos que max_age_seconds.
    Se ejecuta antes de cada descarga para mantener almacenamiento limpio.
    
    Args:
        max_age_seconds: Edad máxima en segundos antes de eliminar
        
    Returns:
        Número de archivos eliminados
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


# ============================================================================
# PLANTILLA HTML
# ============================================================================
HTML = r"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Extractor SECOP (Detalle del Proceso)</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #fff; color:#111; }
    h1 { margin: 0 0 14px; font-size: 22px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 18px; max-width: 980px; }
    label { font-weight: 700; display: block; margin-bottom: 8px; }
    textarea { width: 100%; min-height: 210px; font-family: Consolas, monospace; font-size: 13px; padding: 10px; border: 1px solid #bbb; border-radius: 6px; box-sizing: border-box; }
    .row { display:flex; gap: 10px; align-items:center; margin-top: 12px; }
    button { padding: 10px 16px; border: 1px solid #888; border-radius: 6px; background: #f3f3f3; cursor:pointer; font-size: 14px; }
    button:hover:not(:disabled) { background: #e0e0e0; }
    button:disabled { opacity: .6; cursor:not-allowed; }
    .muted { color:#444; font-size: 13px; }
    .hint { margin-top: 10px; font-size: 13px; color:#333; line-height: 1.45; }
    .mono { font-family: Consolas, monospace; }
    .hr { height:1px; background:#eee; margin: 14px 0; }
    .status { margin-top: 10px; padding: 10px 12px; border-radius: 8px; background:#fafafa; border:1px solid #eee; }
    .status strong { display:inline-block; min-width: 140px; }
    .ok { color:#0b6b0b; }
    .warn { color:#8a5a00; }
    .err { color:#9b1c1c; }
    .footer { margin-top: 12px; font-size: 12px; color:#666; display:flex; justify-content:space-between; }
    .small { font-size: 12px; }
    .btn-secondary { background:#fff; }
    .error-list { margin-top: 8px; max-height: 200px; overflow-y: auto; }
    .error-item { margin: 4px 0; }
  </style>
</head>
<body>
  <h1>Extractor SECOP (Detalle del Proceso)</h1>

  <div class="card">
    <!-- PANEL DE RESULTADOS (Mostrado después de extraer) -->
    <div class="status" style="display:{% if result %}block{% else %}none{% endif %};">
      <div><strong>Estado:</strong>
        {% if result and result.ok_count > 0 and result.fail_count == 0 %}<span class="ok">✓ Finalizado</span>
        {% elif result and result.ok_count > 0 and result.fail_count > 0 %}<span class="warn">⚠ Finalizado con advertencias</span>
        {% elif result and result.ok_count == 0 and result.fail_count > 0 %}<span class="err">✗ Falló</span>
        {% else %}<span>—</span>{% endif %}
      </div>
      {% if result %}
        <div><strong>Detectadas:</strong> {{ result.detected_count }}</div>
        <div><strong>Correctas:</strong> {{ result.ok_count }}</div>
        <div><strong>Con error:</strong> {{ result.fail_count }}</div>
        <div><strong>Salida:</strong> <span class="mono">{{ result.output_name }}</span></div>
        <div class="hr"></div>
        {% if result.download_url %}
          <div><strong>Descarga:</strong> <a href="{{ result.download_url }}">Descargar archivo</a></div>
        {% endif %}
        {% if result.fail_count > 0 %}
          <div class="small" style="margin-top:8px;"><strong>Errores ({{ result.errors|length }}{% if result.has_more_errors %} de {{ result.total_errors }}{% endif %}):</strong></div>
          <div class="error-list small">
            <ul style="margin: 6px 0; padding-left: 20px;">
              {% for c, e in result.errors %}
                <li class="error-item"><span class="mono">{{ c }}</span> — {{ e }}</li>
              {% endfor %}
            </ul>
          </div>
          {% if result.has_more_errors %}
            <div class="small warn" style="margin-top: 8px;">⚠️ Mostrando {{ result.errors|length }} de {{ result.total_errors }} errores. Revisa <span class="mono">reporte_errores.csv</span> en el ZIP para la lista completa.</div>
          {% endif %}
        {% endif %}
      {% endif %}
    </div>

    <!-- FORMULARIO PRINCIPAL -->
    <form id="form" method="post" action="{{ url_for('extract') }}">
      <label for="raw">Números de constancia (numConstancia) — una por línea o tabla completa</label>
      <textarea 
        id="raw" 
        name="raw" 
        placeholder="Ejemplos:
25-11-14555665
25-15-14581710

También puedes pegar una tabla completa: el sistema detecta las constancias automáticamente."
      >{{ raw or '' }}</textarea>

      <div class="row">
        <button id="btnExtract" type="submit">Extraer</button>
        <button id="btnClear" class="btn-secondary" type="button">Limpiar</button>
        <span id="preinfo" class="muted"></span>
      </div>

      <!-- MENSAJES DE PROCESAMIENTO (Oculto hasta submit) -->
      <div id="runtime" class="hint" style="display:none;">
        <strong>⏳ Procesando…</strong> Se abrirá un navegador por cada constancia.
        <div style="margin-top: 8px; font-size: 12px; color: #666;">
          • Si aparece reCAPTCHA, resuélvelo manualmente.<br/>
          • La salida se consolida en una sola hoja <span class="mono">Resultados_Extraccion</span>.<br/>
          • Si hay errores o múltiples constancias, recibirás un <span class="mono">.zip</span> con Excel(es) y reporte de errores.
        </div>
      </div>

      <!-- INSTRUCCIONES PERMANENTES -->
      <div class="hint">
        <strong>ℹ️ Notas operativas</strong>
        <ol style="margin-top: 6px;">
          <li>Se abrirá un navegador (Playwright) por cada constancia.</li>
          <li>Si aparece reCAPTCHA, lo resuelves manualmente.</li>
          <li>La salida se consolida en una sola hoja <span class="mono">Resultados_Extraccion</span> (plantilla estándar).</li>
          <li>Si envías varias constancias o hay fallas, se generará un <span class="mono">.zip</span> con Excel(es) y reporte de errores.</li>
        </ol>
      </div>

      <div class="footer">
        <div>Formato de salida: <span class="mono">Resultados_Extraccion</span> (hoja única)</div>
        <div><span class="mono">v{{ version }}</span> · O.Guerra26</div>
      </div>
    </form>
  </div>

  <script>
    // Expresión regular para detectar constancias (sincronizada con constancia_config.py)
    const CONSTANCIA_RE = /\b(\d{2}-\d{1,2}-\d{4,12})\b/g;
    const DASHES_UNICODE = "‐‑‒–—―";

    function normalizeText(s){
      let result = (s || "");
      // Reemplazar nbsp
      result = result.replace(/\u00A0/g, " ");
      // Reemplazar todos los dashes Unicode
      for (let dash of DASHES_UNICODE) {
        result = result.replace(new RegExp(dash.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), "-");
      }
      return result;
    }

    function detectConstancias(){
      const t = normalizeText(document.getElementById("raw").value);
      const m = t.match(CONSTANCIA_RE) || [];
      // Deduplicación preservando orden
      const seen = new Set();
      const out = [];
      for (const x of m){
        const v = x.replace(/\s+/g, "");
        if (!seen.has(v)){
          seen.add(v);
          out.push(v);
        }
      }
      return out;
    }

    const preinfo = document.getElementById("preinfo");
    const raw = document.getElementById("raw");
    
    function updatePreinfo(){
      const c = detectConstancias();
      preinfo.textContent = c.length ? `📋 Detectadas: ${c.length} constancia${c.length !== 1 ? 's' : ''}` : "";
    }
    
    raw.addEventListener("input", updatePreinfo);
    updatePreinfo();

    document.getElementById("btnClear").addEventListener("click", () => {
      raw.value = "";
      updatePreinfo();
      const status = document.querySelector(".status");
      if (status) { status.style.display = "none"; }
      document.getElementById("runtime").style.display = "none";
      const btn = document.getElementById("btnExtract");
      btn.disabled = false;
      btn.textContent = "Extraer";
      preinfo.textContent = "";
      raw.focus();
    });

    document.getElementById("form").addEventListener("submit", (e) => {
      // Validación cliente: no enviar si está vacío
      const raw_val = raw.value.trim();
      const constancias = detectConstancias();
      
      if (!raw_val || constancias.length === 0) {
        e.preventDefault();
        alert("⚠️ Ingresa al menos una constancia válida");
        raw.focus();
        return false;
      }
      
      // Feedback visual durante procesamiento
      document.getElementById("btnExtract").disabled = true;
      document.getElementById("btnExtract").textContent = "Procesando…";
      document.getElementById("runtime").style.display = "block";
    });
  </script>
</body>
</html>
"""


# ============================================================================
# RUTAS
# ============================================================================

@APP.get("/")
def index():
    """Página principal con formulario de entrada."""
    return render_template_string(
        HTML, 
        raw="", 
        result=None,
        version=constancia_config.__version__
    )


@APP.post("/extract")
def extract():
    """
    Endpoint de procesamiento de constancias.
    
    Recibe:
    - POST form field "raw": texto con constancias (una por línea o tabla)
    
    Retorna:
    - HTML con resultados o lista de errores
    """
    raw = request.form.get("raw", "").strip()
    
    # Validación: entrada vacía
    if not raw:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "—",
            "download_url": None,
            "errors": [],
            "has_more_errors": False,
            "total_errors": 0,
        }
        logger.warning("POST /extract con entrada vacía")
        return render_template_string(
            HTML, 
            raw=raw, 
            result=result,
            version=constancia_config.__version__
        )
    
    # Extracción de constancias
    constancias = constancia_config.extract_constancias(raw)
    detected_count = len(constancias)
    
    if detected_count == 0:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "—",
            "download_url": None,
            "errors": [],
            "has_more_errors": False,
            "total_errors": 0,
        }
        logger.warning(f"No se detectaron constancias válidas en entrada: {raw[:100]}")
        return render_template_string(
            HTML, 
            raw=raw, 
            result=result,
            version=constancia_config.__version__
        )
    
    logger.info(f"Iniciando extracción de {detected_count} constancia(s)")
    
    outputs: List[Path] = []
    errors: List[Tuple[str, str]] = []
    
    # Proceso secuencial (permite interacción manual con reCAPTCHA)
    for i, c in enumerate(constancias, 1):
        try:
            logger.info(f"[{i}/{detected_count}] Extrayendo constancia: {c}")
            out_file = secop_extract.extract_to_excel(c, OUTPUT_DIR, headless=False)
            outputs.append(Path(out_file))
            logger.info(f"[{i}/{detected_count}] ✓ Éxito: {c}")
        except Exception as e:
            error_msg = escape(str(e))
            errors.append((c, error_msg))
            logger.error(f"[{i}/{detected_count}] ✗ Error extrayendo {c}: {e}")
    
    ok_count = len(outputs)
    fail_count = len(errors)
    
    # Generación de archivo final
    token = secrets.token_urlsafe(16)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if ok_count == 1 and fail_count == 0:
        # Caso simple: un único XLSX exitoso
        final_path = outputs[0]
        output_name = final_path.name
        logger.info(f"Resultado único: {output_name}")
    else:
        # Caso múltiple o con errores: empaquetar en ZIP
        zip_name = f"Resultados_Extraccion_{timestamp}.zip"
        final_path = OUTPUT_DIR / zip_name
        
        try:
            with zipfile.ZipFile(final_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                # Agregar XLSX exitosos
                for f in outputs:
                    z.write(f, arcname=f.name)
                    logger.debug(f"Agregado a ZIP: {f.name}")
                
                # Agregar reporte de errores si hay
                if errors:
                    lines = ["numConstancia,error"]
                    for c, err in errors:
                        err_clean = err.replace("\n", " ").replace("\r", " ")
                        lines.append(f'"{c}","{err_clean}"')
                    csv_content = "\n".join(lines) + "\n"
                    z.writestr("reporte_errores.csv", csv_content)
                    logger.info(f"Agregado reporte de errores: {len(errors)} error(es)")
            
            output_name = zip_name
            logger.info(f"ZIP creado: {output_name}")
        except Exception as e:
            logger.error(f"Error creando ZIP: {e}")
            raise
    
    # Registrar descarga disponible con timestamp
    _DOWNLOADS[token] = (final_path, time.time())
    
    # Limitar errores mostrados en UI
    errors_ui = errors[:MAX_ERRORS_DISPLAY]
    has_more_errors = len(errors) > MAX_ERRORS_DISPLAY
    
    result = {
        "detected_count": detected_count,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "output_name": output_name,
        "download_url": url_for("download", token=token),
        "errors": errors_ui,
        "has_more_errors": has_more_errors,
        "total_errors": len(errors),
    }
    
    return render_template_string(
        HTML, 
        raw=raw, 
        result=result,
        version=constancia_config.__version__
    )


@APP.get("/download/<token>")
def download(token: str):
    """
    Descarga segura de archivo generado.
    
    Parámetros:
    - token: token aleatorio único asignado en /extract
    
    Retorna:
    - Archivo (XLSX o ZIP) si existe y es válido
    - Redirección a índice si no existe
    """
    # Limpiar descargas antiguas
    cleaned = cleanup_old_downloads()
    
    # Buscar token
    download_info = _DOWNLOADS.get(token)
    if not download_info:
        logger.warning(f"Intento de descarga con token inválido: {token}")
        return redirect(url_for("index"))
    
    path, _ = download_info
    
    # Validación de existencia
    if not path or not path.exists():
        logger.warning(f"Intento de descargar archivo inexistente: {path}")
        return redirect(url_for("index"))
    
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
