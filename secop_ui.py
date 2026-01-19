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

from flask import Flask, request, send_file, render_template_string, url_for, redirect, after_this_request, session

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


def _render_main(raw: str, result: Optional[dict], mode: str, accumulate: bool):
    _, batch_path, batch_count = _get_workspace_info()
    return render_template_string(
        HTML,
        raw=raw,
        result=result,
        mode=mode,
        version=constancia_config.__version__,
        accumulate=accumulate,
        batch_active=bool(batch_path),
        batch_count=batch_count,
        batch_name=batch_path.name if batch_path else "-",
    )


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
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75' font-weight='bold' fill='%230ea5e9'>SECOP</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  
  <style>
    /* ============== VARIABLES Y TEMAS ============== */
    :root {
      --primary: #0f766e;
      --primary-dark: #115e59;
      --accent-1: #f59e0b;
      --accent-2: #22c55e;
      --accent-3: #ea580c;
      --success: #16a34a;
      --warning: #f59e0b;
      --danger: #dc2626;
      --bg: #f4f7f6;
      --bg-secondary: #ffffff;
      --surface: #ffffff;
      --text: #0f172a;
      --text-muted: #5b6472;
      --border: #e3e8ef;
      --shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
      --shadow-lg: 0 22px 40px rgba(15, 23, 42, 0.12);
      --ring: rgba(15, 118, 110, 0.2);
    }
    
    @media (prefers-color-scheme: dark) {
      :root {
        --primary: #14b8a6;
        --primary-dark: #0f766e;
        --accent-1: #fbbf24;
        --accent-2: #4ade80;
        --accent-3: #fb923c;
        --bg: #0b1214;
        --bg-secondary: #11181b;
        --surface: #0f1720;
        --text: #e2e8f0;
        --text-muted: #9aa4b2;
        --border: #1f2937;
        --shadow: 0 10px 28px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 18px 36px rgba(0, 0, 0, 0.5);
        --ring: rgba(20, 184, 166, 0.25);
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
      font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
      background-color: var(--bg);
      background-image:
        radial-gradient(circle at 10% 10%, rgba(15, 118, 110, 0.12), transparent 50%),
        radial-gradient(circle at 90% 15%, rgba(245, 158, 11, 0.12), transparent 45%),
        linear-gradient(120deg, rgba(15, 23, 42, 0.03) 0%, rgba(15, 23, 42, 0.0) 60%),
        repeating-linear-gradient(90deg, rgba(15, 23, 42, 0.03) 0 1px, transparent 1px 48px);
      color: var(--text);
      line-height: 1.6;
      padding: 24px;
      min-height: 100vh;
      transition: background 0.3s ease, color 0.3s ease;
      position: relative;
      overflow-x: hidden;
    }

    body::before,
    body::after {
      content: "";
      position: absolute;
      z-index: 0;
      width: 520px;
      height: 520px;
      border-radius: 50%;
      filter: blur(90px);
      opacity: 0.25;
      pointer-events: none;
    }

    body::before {
      top: -160px;
      right: -160px;
      background: radial-gradient(circle, rgba(15, 118, 110, 0.45) 0%, transparent 70%);
    }

    body::after {
      bottom: -200px;
      left: -140px;
      background: radial-gradient(circle, rgba(245, 158, 11, 0.4) 0%, transparent 70%);
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
      position: relative;
      z-index: 1;
    }
    
    .logo {
      display: flex;
      align-items: center;
      gap: 16px;
      flex: 1;
      min-width: 250px;
    }
    
    .logo-icon {
      font-size: 12px;
      letter-spacing: 2px;
      padding: 10px 16px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--primary), var(--accent-1));
      color: #ffffff;
      font-weight: 700;
      text-transform: uppercase;
      animation: float 3s ease-in-out infinite;
      box-shadow: 0 10px 18px rgba(15, 118, 110, 0.35);
    }
    
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-8px); }
    }
    
    .logo-text h1 {
      font-size: 26px;
      font-weight: 700;
      margin: 0;
      font-family: 'Space Grotesk', 'IBM Plex Sans', sans-serif;
      background: linear-gradient(120deg, var(--primary) 0%, var(--accent-1) 80%);
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
      background: linear-gradient(135deg, var(--accent-3), var(--primary));
      color: white;
      padding: 8px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      box-shadow: 0 8px 18px rgba(234, 88, 12, 0.35);
    }
    
    /* ============== CONTENEDOR PRINCIPAL ============== */
    .container {
      max-width: 940px;
      margin: 0 auto;
      position: relative;
      z-index: 1;
    }
    
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 20px;
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
      font-family: 'IBM Plex Mono', 'Courier New', monospace;
      font-size: 14px;
      background: var(--bg-secondary);
      color: var(--text);
      resize: vertical;
      transition: all 0.3s ease;
    }
    
    textarea:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--ring);
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
      border: 1px solid transparent;
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
      background: rgba(15, 118, 110, 0.12);
      color: var(--primary-dark);
      border-color: rgba(15, 118, 110, 0.25);
    }
    
    .badge-success {
      background: rgba(22, 163, 74, 0.12);
      color: var(--success);
      border-color: rgba(22, 163, 74, 0.25);
    }
    
    .badge-warning {
      background: rgba(245, 158, 11, 0.14);
      color: #b45309;
      border-color: rgba(245, 158, 11, 0.3);
    }

    .badge-danger {
      background: rgba(220, 38, 38, 0.12);
      color: var(--danger);
      border-color: rgba(220, 38, 38, 0.28);
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
      background: linear-gradient(135deg, var(--primary), var(--accent-1));
      color: white;
      box-shadow: 0 10px 20px rgba(15, 118, 110, 0.35);
      flex: 1;
      min-width: 120px;
    }
    
    #btnExtract:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 14px 28px rgba(15, 118, 110, 0.4);
    }
    
    #btnExtract:active:not(:disabled) {
      transform: translateY(0);
    }
    
    .btn-secondary {
      background: transparent;
      color: var(--text);
      border: 2px solid var(--border);
    }
    
    .btn-secondary:hover:not(:disabled) {
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
    
    /* ============== PANEL DE RESULTADOS ============== */
    .status {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin-top: 24px;
      display: grid;
      gap: 18px;
      animation: fadeUp 0.35s ease;
      background: linear-gradient(120deg, rgba(15, 118, 110, 0.08), rgba(245, 158, 11, 0.05));
    }

    .status.success {
      border-color: rgba(22, 163, 74, 0.45);
    }

    .status.warning {
      border-color: rgba(245, 158, 11, 0.5);
    }

    .status.error {
      border-color: rgba(220, 38, 38, 0.5);
    }

    .results-head {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      justify-content: space-between;
      align-items: center;
    }

    .results-title {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 6px;
    }

    .results-subtitle {
      font-size: 13px;
      color: var(--text-muted);
    }

    .status-pill {
      padding: 8px 14px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 12px;
      letter-spacing: 0.3px;
      text-transform: uppercase;
      background: rgba(15, 118, 110, 0.16);
      color: var(--primary-dark);
    }

    .status.warning .status-pill {
      background: rgba(245, 158, 11, 0.18);
      color: #a16207;
    }

    .status.error .status-pill {
      background: rgba(220, 38, 38, 0.18);
      color: #991b1b;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.02);
    }

    .stat-label {
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }

    .stat-value {
      font-size: 18px;
      font-weight: 700;
      font-family: 'Space Grotesk', sans-serif;
    }

    .download-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: space-between;
      align-items: center;
      padding-top: 6px;
      border-top: 1px dashed rgba(15, 23, 42, 0.12);
    }

    .batch-panel {
      margin-top: 18px;
      padding: 14px;
      border-radius: 12px;
      border: 1px dashed rgba(15, 23, 42, 0.12);
      background: var(--bg-secondary);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .batch-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    /* ============== TEXTO ============== */
    .mono {
      font-family: 'IBM Plex Mono', monospace;
      font-weight: 600;
      background: rgba(15, 23, 42, 0.08);
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
      padding: 18px;
      background: linear-gradient(120deg, rgba(15, 118, 110, 0.08), rgba(255, 255, 255, 0.6));
      border: 1px solid rgba(15, 118, 110, 0.2);
      border-radius: 12px;
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
      background: linear-gradient(90deg, var(--primary), var(--accent-2));
      width: 0%;
      transition: width 0.3s ease;
      box-shadow: 0 0 10px rgba(14, 165, 233, 0.5);
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
      background: rgba(244, 63, 94, 0.06);
      border-left: 4px solid var(--accent-3);
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
        <div class="results-head">
          <div>
            <div class="results-title">Resultados de extraccion</div>
            <div class="results-subtitle">Resumen del lote procesado en SECOP</div>
          </div>
          <div class="status-pill">
            {% if result and result.ok_count > 0 and result.fail_count == 0 %}
              Completado sin errores
            {% elif result and result.ok_count > 0 and result.fail_count > 0 %}
              Completado con advertencias
            {% elif result and result.ok_count == 0 and result.fail_count > 0 %}
              No se pudo completar
            {% else %}
              Sin ejecucion
            {% endif %}
          </div>
        </div>
        {% if result %}
          <div class="stats">
            <div class="stat-card">
              <div class="stat-label">Constancias detectadas</div>
              <div class="stat-value">{{ result.detected_count }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Procesadas con exito</div>
              <div class="stat-value">{{ result.ok_count }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Con errores</div>
              <div class="stat-value">{{ result.fail_count }}</div>
            </div>
          </div>
          <div class="download-row">
            <div>
              <strong>Archivo generado:</strong>
              <span class="mono">{{ result.output_name }}</span>
            </div>
            {% if result.download_url %}
              <a href="{{ result.download_url }}" style="display: inline-flex; align-items: center; gap: 6px;">
                Descargar Excel
              </a>
            {% endif %}
          </div>
          {% if result.fail_count > 0 %}
            <div style="margin-top: 6px;">
              <strong class="small">Errores encontrados ({{ result.errors|length }}{% if result.has_more_errors %} de {{ result.total_errors }}{% endif %}):</strong>
              <div class="error-list small">
                {% for c, e in result.errors %}
                  <div class="error-item">
                    <span class="mono">{{ c }}</span> - {{ e }}
                  </div>
                {% endfor %}
              </div>
              {% if result.has_more_errors %}
                <div class="small warn" style="margin-top: 12px; padding: 8px; background: rgba(245, 158, 11, 0.1); border-radius: 6px;">
                  Se muestran {{ result.errors|length }} de {{ result.total_errors }} errores. Revisa la hoja <span class="mono">Errores</span> en el Excel para la lista completa.
                </div>
              {% endif %}
            </div>
          {% endif %}
        {% endif %}
      </div>

      <!-- FORMULARIO PRINCIPAL -->
      <form id="form" method="post" action="{{ url_for('extract') }}">
        <label for="raw">Constancias a procesar</label>
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

        <div class="row" style="margin-top: 12px;">
          <label for="mode" style="margin: 0;">Modo de extraccion</label>
          <select id="mode" name="mode" style="padding: 8px 10px; border-radius: 8px; border: 2px solid var(--border); background: var(--bg-secondary); color: var(--text); font-weight: 600;">
            <option value="normal" {% if mode == "normal" %}selected{% endif %}>Normal (mas rapido)</option>
            <option value="seguro" {% if mode == "seguro" %}selected{% endif %}>Seguro (anti-bloqueo)</option>
          </select>
        </div>

        <div class="row" style="margin-top: 10px;">
          <label style="margin: 0; display: flex; align-items: center; gap: 10px;">
            <input type="checkbox" id="accumulate" name="accumulate" value="1" {% if accumulate %}checked{% endif %} />
            Acumular en un solo Excel (descarga manual)
          </label>
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
          <strong>Procesando constancias</strong>
          - Se abrira un navegador por cada constancia<br/>
          - Resuelve manualmente reCAPTCHA si aparece<br/>
          - La salida se guarda en un unico Excel: <span class="mono">Resultados_Extraccion</span>
        </div>

        <!-- INSTRUCCIONES PERMANENTES -->
        <div class="hint">
          <strong>Guia rapida</strong>
          <ol>
            <li>Ingresa constancias (una por linea o tabla completa)</li>
            <li>Haz clic en "Extraer" para iniciar el proceso</li>
            <li>Se abrira un navegador por cada constancia</li>
            <li>Si aparece reCAPTCHA, resuelvelo manualmente</li>
            <li>Recibiras un unico Excel con los resultados consolidados</li>
            <li>Si activas acumulacion, descarga el Excel cuando presiones "Descargar lote"</li>
          </ol>
        </div>

        <div class="footer">
          <div>Salida: <span class="mono">Resultados_Extraccion</span> (Excel unico)</div>
          <div>Creado por O.Guerra26</div>
        </div>
      </form>

      {% if batch_active %}
        <div class="batch-panel">
          <div>
            <strong>Lote activo:</strong>
            <span class="mono">{{ batch_name }}</span>
            <span class="small muted" style="margin-left: 8px;">{{ batch_count }} registros acumulados</span>
          </div>
          <div class="batch-actions">
            <form method="post" action="{{ url_for('finalize') }}">
              <button id="btnFinalize" type="submit">Descargar lote</button>
            </form>
            <form method="post" action="{{ url_for('reset_batch') }}">
              <button class="btn-secondary" type="submit">Reiniciar lote</button>
            </form>
          </div>
        </div>
      {% endif %}
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
        preinfo.textContent = `Detectadas: ${c.length} constancia${c.length !== 1 ? 's' : ''}`;
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
        alert("Ingresa al menos una constancia valida (formato: YY-XX-NNNN)");
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
    cleanup_old_downloads()
    cleanup_old_workspaces()
    return _render_main(raw="", result=None, mode="normal", accumulate=False)


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
    accumulate = request.form.get("accumulate", "").strip() == "1"
    cleanup_old_workspaces()
    
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

    if accumulate:
        workspace_id, batch_path, batch_count = _get_workspace_info()
        if not workspace_id or not batch_path:
            workspace_id = secrets.token_urlsafe(10)
            batch_name = f"Resultados_Extraccion_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{workspace_id}.xlsx"
            batch_path = OUTPUT_DIR / batch_name
            _WORKSPACES[workspace_id] = (batch_path, time.time(), 0)
            session["workspace_id"] = workspace_id
            batch_count = 0

        final_path, errors, ok_added = secop_extract.append_batch_to_excel(
            constancias,
            batch_path,
            headless=False,
            delay_seconds=delay_seconds,
            backoff_max_seconds=backoff_max_seconds,
        )
        batch_count = batch_count + ok_added
        _WORKSPACES[workspace_id] = (final_path, time.time(), batch_count)
        download_url = None
    else:
        final_path, errors = secop_extract.extract_batch_to_excel(
            constancias,
            OUTPUT_DIR,
            headless=False,
            delay_seconds=delay_seconds,
            backoff_max_seconds=backoff_max_seconds,
        )
        download_url = None

    if accumulate:
        ok_count = ok_added
    else:
        ok_count = detected_count - len(errors)
    fail_count = len(errors)

    output_name = final_path.name
    if not accumulate:
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
        "download_url": download_url,
        "errors": errors_ui,
        "has_more_errors": has_more_errors,
        "total_errors": len(errors),
    }
    
    return _render_main(raw=raw, result=result, mode=mode, accumulate=accumulate)


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
