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
from pathlib import Path
from typing import List, Tuple, Dict
from html import escape

from flask import Flask, request, send_file, render_template_string, url_for, redirect, after_this_request

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


# ============================================================================
# PLANTILLA HTML - VERSION MEJORADA CON DISENO MODERNO
# ============================================================================
HTML = r"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
  <title>Extractor SECOP - Automatizacion de Procesos</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75' font-weight='bold' fill='%232563eb'>SECOP</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    /* ============== VARIABLES Y TEMAS ============== */
    :root {
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --bg: #ffffff;
      --bg-secondary: #f9fafb;
      --text: #111827;
      --text-muted: #6b7280;
      --border: #e5e7eb;
      --shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
      --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
    }
    
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #111827;
        --bg-secondary: #1f2937;
        --text: #f3f4f6;
        --text-muted: #d1d5db;
        --border: #374151;
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
      }
    }
    
    /* ============== RESET Y BASE ============== */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    html {
      scroll-behavior: smooth;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, var(--bg) 0%, var(--bg-secondary) 100%);
      color: var(--text);
      line-height: 1.6;
      padding: 20px;
      min-height: 100vh;
      transition: background 0.3s ease, color 0.3s ease;
    }
    
    /* ============== HEADER ============== */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 2px solid var(--border);
      gap: 16px;
      flex-wrap: wrap;
    }
    
    .logo {
      display: flex;
      align-items: center;
      gap: 16px;
      flex: 1;
      min-width: 250px;
    }
    
    .logo-icon {
      font-size: 40px;
      animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-8px); }
    }
    
    .logo-text h1 {
      font-size: 24px;
      font-weight: 700;
      margin: 0;
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .tagline {
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
      font-weight: 500;
    }
    
    .version-badge {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: white;
      padding: 8px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* ============== CONTENEDOR PRINCIPAL ============== */
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    
    .card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 32px;
      box-shadow: var(--shadow);
      transition: all 0.3s ease;
    }
    
    .card:hover {
      box-shadow: var(--shadow-lg);
      transform: translateY(-2px);
    }
    
    /* ============== FORMULARIO ============== */
    label {
      display: block;
      font-weight: 600;
      margin-bottom: 10px;
      color: var(--text);
      font-size: 14px;
    }
    
    textarea {
      width: 100%;
      min-height: 180px;
      padding: 14px;
      border: 2px solid var(--border);
      border-radius: 10px;
      font-family: 'Fira Code', 'Courier New', monospace;
      font-size: 14px;
      background: var(--bg-secondary);
      color: var(--text);
      resize: vertical;
      transition: all 0.3s ease;
    }
    
    textarea:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
      background: var(--bg);
    }
    
    textarea::placeholder {
      color: var(--text-muted);
      opacity: 0.7;
    }
    
    /* ============== INPUTS ============== */
    .input-hint {
      margin-top: 10px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }
    
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-5px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    .badge-info {
      background: rgba(37, 99, 235, 0.1);
      color: var(--primary);
    }
    
    .badge-success {
      background: rgba(16, 185, 129, 0.1);
      color: var(--success);
    }
    
    .badge-warning {
      background: rgba(245, 158, 11, 0.1);
      color: var(--warning);
    }
    
    /* ============== BOTONES ============== */
    .row {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 16px;
      flex-wrap: wrap;
    }
    
    button {
      padding: 11px 20px;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }
    
    #btnExtract {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: white;
      box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
      flex: 1;
      min-width: 120px;
    }
    
    #btnExtract:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(37, 99, 235, 0.5);
    }
    
    #btnExtract:active:not(:disabled) {
      transform: translateY(0);
    }
    
    .btn-secondary {
      background: var(--border);
      color: var(--text);
      border: 2px solid var(--border);
    }
    
    .btn-secondary:hover:not(:disabled) {
      background: transparent;
      border-color: var(--primary);
      color: var(--primary);
    }
    
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    /* ============== PANEL DE ESTADO ============== */
    .status {
      background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
      border: 2px solid var(--success);
      border-radius: 12px;
      padding: 20px;
      margin-top: 24px;
      display: grid;
      gap: 12px;
      animation: slideIn 0.3s ease;
    }
    
    .status.success {
      background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
      border-color: var(--success);
    }

    .status.warning {
      background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
      border-color: var(--warning);
    }
    
    .status.error {
      background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
      border-color: var(--danger);
    }
    
    .status div {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
    }
    
    .status strong {
      font-weight: 600;
      min-width: 100px;
    }
    
    /* ============== TEXTO ============== */
    .mono {
      font-family: 'Fira Code', monospace;
      font-weight: 600;
      background: rgba(0, 0, 0, 0.05);
      padding: 2px 6px;
      border-radius: 3px;
    }
    
    .ok {
      color: var(--success);
      font-weight: 600;
    }
    
    .warn {
      color: var(--warning);
      font-weight: 600;
    }
    
    .err {
      color: var(--danger);
      font-weight: 600;
    }
    
    .small {
      font-size: 12px;
    }
    
    .muted {
      color: var(--text-muted);
      font-size: 13px;
    }
    
    /* ============== HINT Y INSTRUCCIONES ============== */
    .hint {
      margin-top: 16px;
      padding: 16px;
      background: rgba(37, 99, 235, 0.05);
      border-left: 4px solid var(--primary);
      border-radius: 8px;
      color: var(--text);
      font-size: 13px;
      line-height: 1.6;
    }
    
    .hint strong {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
    }
    
    .hint ol {
      margin-left: 20px;
      margin-top: 8px;
    }
    
    .hint li {
      margin: 6px 0;
    }
    
    /* ============== PROGRESS ============== */
    .progress-container {
      margin: 16px 0;
    }
    
    .progress-bar {
      width: 100%;
      height: 6px;
      background: var(--border);
      border-radius: 3px;
      overflow: hidden;
    }
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary), var(--primary-dark));
      width: 0%;
      transition: width 0.3s ease;
      box-shadow: 0 0 10px rgba(37, 99, 235, 0.5);
    }
    
    .progress-text {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 8px;
      text-align: center;
    }
    
    /* ============== LISTA DE ERRORES ============== */
    .error-list {
      margin-top: 12px;
      max-height: 400px;
      overflow-y: auto;
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.02);
      padding: 12px;
    }
    
    .error-item {
      padding: 10px 12px;
      margin: 8px 0;
      background: rgba(239, 68, 68, 0.05);
      border-left: 4px solid var(--danger);
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.5;
      transition: all 0.2s ease;
    }
    
    .error-item:hover {
      background: rgba(239, 68, 68, 0.08);
    }
    
    /* ============== FOOTER ============== */
    .footer {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }
    
    a {
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
      transition: all 0.2s ease;
    }
    
    a:hover {
      color: var(--primary-dark);
      text-decoration: underline;
    }
    
    /* ============== RESPONSIVE ============== */
    @media (max-width: 640px) {
      body {
        padding: 12px;
      }
      
      .card {
        padding: 20px;
      }
      
      .header {
        flex-direction: column;
        align-items: flex-start;
      }
      
      .logo {
        width: 100%;
      }
      
      .version-badge {
        width: 100%;
        text-align: center;
      }
      
      button {
        width: 100%;
        justify-content: center;
      }
      
      .row {
        flex-direction: column;
      }
      
      #btnExtract {
        width: 100%;
      }
      
      .footer {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <div class="logo">
        <div class="logo-icon">SECOP</div>
        <div class="logo-text">
          <h1>Extractor SECOP</h1>
          <p class="tagline">Automatizacion de procesos de contratacion</p>
        </div>
      </div>
      <div class="version-badge">v{{ version }}</div>
    </header>

    <div class="card">
      <!-- PANEL DE RESULTADOS -->
      <div class="status {% if result %}{% if result.ok_count > 0 and result.fail_count == 0 %}success{% elif result.ok_count > 0 and result.fail_count > 0 %}warning{% else %}error{% endif %}{% endif %}" style="display:{% if result %}block{% else %}none{% endif %};">
        <div>
          <strong>Estado:</strong>
          {% if result and result.ok_count > 0 and result.fail_count == 0 %}
            <span class="ok">OK Finalizado con exito</span>
          {% elif result and result.ok_count > 0 and result.fail_count > 0 %}
            <span class="warn">ALERTA Finalizado con advertencias</span>
          {% elif result and result.ok_count == 0 and result.fail_count > 0 %}
            <span class="err">ERROR Fallo</span>
          {% else %}
            <span>-</span>
          {% endif %}
        </div>
        {% if result %}
          <div>
            <strong>Detectadas:</strong>
            <span class="badge badge-info">INFO {{ result.detected_count }}</span>
          </div>
          <div>
            <strong>Correctas:</strong>
            <span class="badge badge-success">OK {{ result.ok_count }}</span>
          </div>
          <div>
            <strong>Con error:</strong>
            <span class="badge badge-warning">ERROR {{ result.fail_count }}</span>
          </div>
          <div>
            <strong>Salida:</strong>
            <span class="mono">{{ result.output_name }}</span>
          </div>
          <hr style="margin: 12px 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);">
          {% if result.download_url %}
            <div>
              <strong>Descargar:</strong>
              <a href="{{ result.download_url }}" style="display: inline-flex; align-items: center; gap: 6px;">
                DESCARGA Descargar archivo
              </a>
            </div>
          {% endif %}
          {% if result.fail_count > 0 %}
            <div style="margin-top: 12px;">
              <strong class="small">Errores ({{ result.errors|length }}{% if result.has_more_errors %} de {{ result.total_errors }}{% endif %}):</strong>
              <div class="error-list small">
                {% for c, e in result.errors %}
                  <div class="error-item">
                    <span class="mono">{{ c }}</span> - {{ e }}
                  </div>
                {% endfor %}
              </div>
              {% if result.has_more_errors %}
                <div class="small warn" style="margin-top: 12px; padding: 8px; background: rgba(245, 158, 11, 0.1); border-radius: 6px;">
                  ALERTA Mostrando {{ result.errors|length }} de {{ result.total_errors }} errores. Revisa la hoja <span class="mono">Errores</span> en el Excel para la lista completa.
                </div>
              {% endif %}
            </div>
          {% endif %}
        {% endif %}
      </div>

      <!-- FORMULARIO PRINCIPAL -->
      <form id="form" method="post" action="{{ url_for('extract') }}">
        <label for="raw">Numeros de constancia (numConstancia)</label>
        <textarea 
          id="raw" 
          name="raw" 
          placeholder="Ingresa constancias (una por linea):
25-11-14555665
25-15-14581710

O pega una tabla completa: el sistema detecta automaticamente"
        >{{ raw or '' }}</textarea>

        <div class="input-hint">
          <span id="preinfo" class="badge badge-info" style="display: none;"></span>
        </div>

        <div class="row">
          <button id="btnExtract" type="submit">
            <span id="btnIcon"></span>
            <span id="btnText">Extraer</span>
          </button>
          <button id="btnClear" class="btn-secondary" type="button">Limpiar</button>
        </div>

        <!-- PROGRESO (Oculto hasta submit) -->
        <div id="progressContainer" class="progress-container" style="display: none;">
          <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
          </div>
          <p class="progress-text" id="progressText">Iniciando extraccion...</p>
        </div>

        <!-- MENSAJES DE PROCESAMIENTO -->
        <div id="runtime" class="hint" style="display:none;">
          <strong>PROCESANDO Procesando Constancias</strong>
          - Se abrira un navegador por cada constancia<br/>
          - Resuelve manualmente reCAPTCHA si aparece<br/>
          - La salida se guarda en un unico Excel: <span class="mono">Resultados_Extraccion</span>
        </div>

        <!-- INSTRUCCIONES PERMANENTES -->
        <div class="hint">
          <strong>INFO Instrucciones de Uso</strong>
          <ol>
            <li>Ingresa constancias (una por linea o tabla completa)</li>
            <li>Haz clic en "Extraer" para iniciar el proceso</li>
            <li>Se abrira un navegador por cada constancia</li>
            <li>Si aparece reCAPTCHA, resuelvelo manualmente</li>
            <li>Recibiras un unico Excel con los resultados consolidados</li>
          </ol>
        </div>

        <div class="footer">
          <div>SALIDA Salida: <span class="mono">Resultados_Extraccion</span> (Excel unico)</div>
          <div>AUTOR Creado por O.Guerra26</div>
        </div>
      </form>
    </div>
  </div>

  <script>
    const CONSTANCIA_RE = /\b(\d{2}-\d{1,2}-\d{4,12})\b/g;
    const DASHES_UNICODE = ["\u2013", "\u2014", "\u2212", "\u2010", "\u2011", "\u2012", "\u2043"];
    function normalizeText(s){
      let result = (s || "");
      result = result.replace(/\u00A0/g, " ");
      for (let dash of DASHES_UNICODE) {
        result = result.replace(new RegExp(dash.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), "-");
      }
      return result;
    }

    function detectConstancias(){
      const t = normalizeText(document.getElementById("raw").value);
      const m = t.match(CONSTANCIA_RE) || [];
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
      if (c.length > 0) {
        preinfo.textContent = `INFO ${c.length} constancia${c.length !== 1 ? 's' : ''} detectada${c.length !== 1 ? 's' : ''}`;
        preinfo.style.display = "inline-flex";
      } else {
        preinfo.style.display = "none";
      }
    }
    
    raw.addEventListener("input", updatePreinfo);
    updatePreinfo();

    document.getElementById("btnClear").addEventListener("click", () => {
      raw.value = "";
      updatePreinfo();
      const status = document.querySelector(".status");
      if (status) { status.style.display = "none"; }
      document.getElementById("runtime").style.display = "none";
      document.getElementById("progressContainer").style.display = "none";
      const btn = document.getElementById("btnExtract");
      btn.disabled = false;
      document.getElementById("btnIcon").textContent = "";
      document.getElementById("btnText").textContent = "Extraer";
      raw.focus();
    });

    document.getElementById("form").addEventListener("submit", (e) => {
      const raw_val = raw.value.trim();
      const constancias = detectConstancias();
      
      if (!raw_val || constancias.length === 0) {
        e.preventDefault();
        alert("ALERTA Ingresa al menos una constancia valida (formato: YY-XX-NNNN)");
        raw.focus();
        return false;
      }
      
      document.getElementById("btnExtract").disabled = true;
      document.getElementById("btnIcon").textContent = "";
      document.getElementById("btnText").textContent = "Procesando...";
      document.getElementById("runtime").style.display = "block";
      document.getElementById("progressContainer").style.display = "block";
      
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress > 90) progress = 90;
        document.getElementById("progressFill").style.width = progress + "%";
      }, 500);
      
      window.addEventListener("beforeunload", () => clearInterval(interval));
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
    """Pagina principal con formulario de entrada."""
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
    - POST form field "raw": texto con constancias (una por linea o tabla)
    
    Retorna:
    - HTML con resultados o lista de errores
    """
    raw = request.form.get("raw", "").strip()
    
    # Validacion: entrada vacia
    if not raw:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "-",
            "download_url": None,
            "errors": [],
            "has_more_errors": False,
            "total_errors": 0,
        }
        logger.warning("POST /extract con entrada vacia")
        return render_template_string(
            HTML, 
            raw=raw, 
            result=result,
            version=constancia_config.__version__
        )
    
    # Extraccion de constancias
    constancias = constancia_config.extract_constancias(raw)
    detected_count = len(constancias)
    
    if detected_count == 0:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "-",
            "download_url": None,
            "errors": [],
            "has_more_errors": False,
            "total_errors": 0,
        }
        logger.warning(f"No se detectaron constancias validas en entrada: {raw[:100]}")
        return render_template_string(
            HTML, 
            raw=raw, 
            result=result,
            version=constancia_config.__version__
        )
    
    logger.info(f"Iniciando extraccion de {detected_count} constancia(s)")

    # Proceso secuencial (permite interaccion manual con reCAPTCHA)
    final_path, errors = secop_extract.extract_batch_to_excel(
        constancias,
        OUTPUT_DIR,
        headless=False,
    )

    ok_count = detected_count - len(errors)
    fail_count = len(errors)

    # Generacion de archivo final (siempre un solo XLSX)
    output_name = final_path.name
    token = secrets.token_urlsafe(16)
    
    # Registrar descarga disponible con timestamp
    _DOWNLOADS[token] = (final_path, time.time())
    
    # Limitar errores mostrados en UI
    errors_safe = [(c, escape(str(e))) for c, e in errors]
    errors_ui = errors_safe[:MAX_ERRORS_DISPLAY]
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
    
    Parametros:
    - token: token aleatorio unico asignado en /extract
    
    Retorna:
    - Archivo (XLSX o ZIP) si existe y es valido
    - Redireccion a indice si no existe
    """
    # Limpiar descargas antiguas
    cleaned = cleanup_old_downloads()
    
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
