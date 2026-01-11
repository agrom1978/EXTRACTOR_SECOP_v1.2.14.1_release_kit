# secop_ui.py
from __future__ import annotations

import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from flask import Flask, request, send_file, render_template_string, url_for, redirect, flash

import secop_extract

APP = Flask(__name__)
APP.secret_key = os.environ.get("SECOP_UI_SECRET", "secop-ui-local")

# Directorio de salida (mantiene el comportamiento por defecto, pero permite override)
DEFAULT_OUTPUT_DIR = Path.home() / "secop_exports"
OUTPUT_DIR = Path(os.environ.get("SECOP_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapeo en memoria: token -> ruta de archivo generado
_DOWNLOADS: Dict[str, Path] = {}

# Regex tolerante para numConstancia (ej. 25-1-241304)
CONSTANCIA_RE = re.compile(r"\b(\d{2}-\d{1,2}-\d{3,10})\b")

HTML = """
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
    textarea { width: 100%; min-height: 210px; font-family: Consolas, monospace; font-size: 13px; padding: 10px; border: 1px solid #bbb; border-radius: 6px; }
    .row { display:flex; gap: 10px; align-items:center; margin-top: 12px; }
    button { padding: 10px 16px; border: 1px solid #888; border-radius: 6px; background: #f3f3f3; cursor:pointer; }
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
  </style>
</head>
<body>
  <h1>Extractor SECOP (Detalle del Proceso)</h1>

  <div class="card">
    <div class="status" style="display:{% if result %}block{% else %}none{% endif %};">
      <div><strong>Estado:</strong>
        {% if result and result.ok_count > 0 and result.fail_count == 0 %}<span class="ok">Finalizado</span>
        {% elif result and result.ok_count > 0 and result.fail_count > 0 %}<span class="warn">Finalizado con advertencias</span>
        {% elif result and result.ok_count == 0 and result.fail_count > 0 %}<span class="err">Falló</span>
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
          <div class="small" style="margin-top:8px;"><strong>Errores:</strong></div>
          <ul class="small">
            {% for c, e in result.errors %}
              <li><span class="mono">{{ c }}</span> — {{ e }}</li>
            {% endfor %}
          </ul>
        {% endif %}
      {% endif %}
    </div>

    <form id="form" method="post" action="{{ url_for('extract') }}">
      <label for="raw">Números de constancia (numConstancia) (una por línea o pega una tabla completa)</label>
      <textarea id="raw" name="raw" placeholder="Ejemplos:
25-11-14555665
25-15-14581710

También puedes pegar una lista/tabla completa: el sistema detecta las constancias automáticamente.">{{ raw or '' }}</textarea>

      <div class="row">
        <button id="btnExtract" type="submit">Extraer</button>
        <button id="btnClear" class="btn-secondary" type="button">Limpiar</button>
        <span id="preinfo" class="muted"></span>
      </div>

      <div id="runtime" class="hint" style="display:none;">
        <div>Procesando… Se abrirá un navegador (Playwright) <strong>por cada constancia</strong>.</div>
        <div>Si aparece reCAPTCHA, resuélvelo manualmente.</div>
        <div>Salida: una sola hoja <span class="mono">Resultados_Extraccion</span> (plantilla estándar).</div>
        <div>Si envías varias constancias o hay fallas, la salida será un <span class="mono">.zip</span> con Excel(es) y reporte de errores.</div>
      </div>

      <div class="hint">
        <div><strong>Notas operativas</strong></div>
        <ol style="margin-top:6px;">
          <li>Se abrirá un navegador (Playwright) por cada constancia.</li>
          <li>Si aparece reCAPTCHA, lo resuelves manualmente.</li>
          <li>La salida se consolida en una sola hoja <span class="mono">Resultados_Extraccion</span> (plantilla estándar).</li>
          <li>Si envías varias constancias o hay fallas, se generará un <span class="mono">.zip</span> con Excel(es) y reporte de errores.</li>
        </ol>
      </div>

      <div class="footer">
        <div>Formato de salida: <span class="mono">Resultados_Extraccion</span> (hoja única)</div>
        <div><span class="mono">v1.2.10</span> · O.Guerra26</div>
      </div>
    </form>
  </div>

  <script>
    const RE = /\b(\d{2}-\d{1,2}-\d{3,10})\b/g;

    function normalizeText(s){
      return (s || "")
        .replace(/[‐‑‒–—―]/g, "-")
        .replace(/\u00A0/g, " "); // nbsp
    }

    function detectConstancias(){
      const t = normalizeText(document.getElementById("raw").value);
      const m = t.match(RE) || [];
      // dedupe preserving order
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
      preinfo.textContent = c.length ? `Constancias detectadas: ${c.length}` : "";
    }
    raw.addEventListener("input", updatePreinfo);
    updatePreinfo();

    document.getElementById("btnClear").addEventListener("click", () => {
      raw.value = "";
      updatePreinfo();
      // reset visual status panel
      const status = document.querySelector(".status");
      if (status) { status.style.display = "none"; }
      // reset runtime/progress hints
      document.getElementById("runtime").style.display = "none";
      const btn = document.getElementById("btnExtract");
      btn.disabled = false;
      btn.textContent = "Extraer";
      preinfo.textContent = "";
      raw.focus();
    });

    document.getElementById("form").addEventListener("submit", () => {
      // feedback visual sin bloquear funcionalidad
      document.getElementById("btnExtract").disabled = true;
      document.getElementById("btnExtract").textContent = "Procesando…";
      document.getElementById("runtime").style.display = "block";
    });
  </script>
</body>
</html>
"""


def _normalize_text(raw: str) -> str:
    return raw.replace("\u00A0", " ").translate(str.maketrans({c: "-" for c in "‐‑‒–—―"}))


def extract_constancias(raw: str) -> List[str]:
    raw_n = _normalize_text(raw)
    found = CONSTANCIA_RE.findall(raw_n)
    out: List[str] = []
    seen = set()
    for c in found:
        c2 = c.replace(" ", "")
        if c2 not in seen:
            seen.add(c2)
            out.append(c2)
    return out


@APP.get("/")
def index():
    return render_template_string(HTML, raw="", result=None)


@APP.post("/extract")
def extract():
    raw = request.form.get("raw", "")
    constancias = extract_constancias(raw)
    detected_count = len(constancias)

    if detected_count == 0:
        result = {
            "detected_count": 0,
            "ok_count": 0,
            "fail_count": 0,
            "output_name": "—",
            "download_url": None,
            "errors": [],
        }
        return render_template_string(HTML, raw=raw, result=result)

    outputs: List[Path] = []
    errors: List[Tuple[str, str]] = []

    # Proceso secuencial visible (mantiene comportamiento y manejo de CAPTCHA)
    for i, c in enumerate(constancias, start=1):
        try:
            out_file = secop_extract.extract_to_excel(c, OUTPUT_DIR, headless=False)
            outputs.append(Path(out_file))
        except Exception as e:
            errors.append((c, str(e)))

    ok_count = len(outputs)
    fail_count = len(errors)

    # Determinar archivo final a entregar:
    # - Si 1 OK y sin errores: entregar ese XLSX
    # - En otros casos: empaquetar ZIP con los XLSX OK + reporte_errores.csv (si aplica)
    token = secrets.token_urlsafe(16)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if ok_count == 1 and fail_count == 0:
        final_path = outputs[0]
        output_name = final_path.name
    else:
        zip_name = f"Resultados_Extraccion_{timestamp}.zip"
        final_path = OUTPUT_DIR / zip_name
        import zipfile
        with zipfile.ZipFile(final_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for f in outputs:
                z.write(f, arcname=Path(f).name)
            if errors:
                # CSV simple de errores
                lines = ["numConstancia,error"]
                for c, err in errors:
                    err2 = err.replace("\n", " ").replace("\r", " ")
                    lines.append(f"\"{c}\",\"{err2}\"")
                z.writestr("reporte_errores.csv", "\n".join(lines) + "\n")
        output_name = zip_name

    _DOWNLOADS[token] = Path(final_path)

    # Limitar el listado de errores mostrado en UI (para no saturar)
    errors_ui = errors[:25]

    result = {
        "detected_count": detected_count,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "output_name": output_name,
        "download_url": url_for("download", token=token),
        "errors": errors_ui,
    }
    return render_template_string(HTML, raw=raw, result=result)


@APP.get("/download/<token>")
def download(token: str):
    path = _DOWNLOADS.get(token)
    if not path or not path.exists():
        # volver al inicio sin romper
        return redirect(url_for("index"))
    # Descarga directa
    return send_file(path, as_attachment=True, download_name=path.name)


if __name__ == "__main__":
    # http://127.0.0.1:5000
    APP.run(host="127.0.0.1", port=5000, debug=False)
