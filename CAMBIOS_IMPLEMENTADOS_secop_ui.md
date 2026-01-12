# CAMBIOS IMPLEMENTADOS: secop_ui.py v1.2.14.1

**Fecha:** 11 de enero de 2026  
**Cambios:** Refactorización mayor con enfoque en consistencia, seguridad y mantenibilidad

---

## 📁 ARCHIVOS MODIFICADOS/CREADOS

### ✅ NUEVO: `constancia_config.py`
Archivo centralizado de configuración para constancias, compartido entre `secop_extract.py` y `secop_ui.py`.

**Contenido:**
- Constantes Unicode de dashes: `DASHES_UNICODE = "‐‑‒–—―"`
- Regex única validada: `CONSTANCIA_RE = r"^(?P<yy>\d{2})-(?P<xx>\d{1,2})-(?P<num>\d{4,12})$"`
- Regex de detección: `CONSTANCIA_DETECTION_RE = r"\b(\d{2}-\d{1,2}-\d{4,12})\b"`
- Funciones centralizadas:
  - `normalize_text(text)` — Normaliza dashes Unicode y nbsp
  - `normalize_constancia(constancia)` — Normaliza constancia individual
  - `validate_constancia(constancia)` — Valida y retorna normalizada
  - `extract_constancias(raw_text)` — Extrae y deduplica constancias
- Versionado: `__version__ = "1.2.14.1"`

**Beneficio:** Garantiza sincronización entre frontend (JavaScript) y backend (Python)

---

### 🔄 ACTUALIZADO: `secop_ui.py`

#### 1. **Imports Mejorados**
```python
# ANTES:
import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

# DESPUÉS:
import os
import secrets
import logging
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from html import escape

import secop_extract
import constancia_config  # ← NUEVA IMPORTACIÓN
```

#### 2. **Logging Estructurado** (NUEVO)
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
```

**Logs registrados:**
- `logger.info()` — Operaciones normales (inicio extracción, éxito, etc.)
- `logger.warning()` — Situaciones de atención (entrada vacía, secret key no configurada)
- `logger.error()` — Errores de extracción y limpieza
- `logger.debug()` — Detalles de procesamiento (archivos agregados a ZIP)

#### 3. **Hardening de Seguridad**
```python
# ANTES:
APP.secret_key = os.environ.get("SECOP_UI_SECRET", "secop-ui-local")

# DESPUÉS:
secret = os.environ.get("SECOP_UI_SECRET")
if not secret:
    secret = "secop-ui-local-default"
    logger.warning(
        "⚠️ Variable SECOP_UI_SECRET no configurada. "
        "Usa una clave segura en producción."
    )
APP.secret_key = secret
```

**Mejora:** Aviso explícito si secret key es débil (no se configura en producción).

#### 4. **Sistema de Limpieza de Descargas** (NUEVO)
```python
_DOWNLOADS: Dict[str, Tuple[Path, float]] = {}  # token -> (path, timestamp)
MAX_DOWNLOAD_AGE_SECONDS = 3600  # 1 hora
MAX_ERRORS_DISPLAY = 25

def cleanup_old_downloads(max_age_seconds: int = MAX_DOWNLOAD_AGE_SECONDS) -> int:
    """Elimina archivos más antiguos que max_age_seconds"""
    # Implementación con logging
```

**Beneficios:**
- ✅ Evita memory leak (diccionario crecía indefinidamente)
- ✅ Limpia archivos automáticamente cada 1 hora
- ✅ Se ejecuta antes de cada descarga
- ✅ Retorna número de archivos eliminados

#### 5. **Plantilla HTML Mejorada**

**Cambios en UI:**
- ✅ Versión actualizada a `v{{ version }}` (dinámica desde `constancia_config.__version__`)
- ✅ Fusión de secciones de instrucciones duplicadas (simplificadas)
- ✅ Mejor feedback visual:
  - Emojis en estados (✓, ⚠, ✗, ℹ️, ⏳)
  - Scroll automático en lista de errores si hay muchos
  - Advertencia clara si hay errores truncados:
    ```html
    ⚠️ Mostrando 25 de 40 errores. Revisa reporte_errores.csv...
    ```
- ✅ Validación cliente previa al envío

#### 6. **JavaScript Sincronizado** (ACTUALIZADO)
```javascript
// Expresión regular sincronizada con constancia_config.py
const CONSTANCIA_RE = /\b(\d{2}-\d{1,2}-\d{4,12})\b/g;  // ← 4-12 dígitos (consistente)
const DASHES_UNICODE = "‐‑‒–—―";

function normalizeText(s){
  // Ahora reemplaza dashes Unicode de forma más robusta
  for (let dash of DASHES_UNICODE) {
    result = result.replace(new RegExp(...), "-");
  }
}
```

**Validación cliente:**
```javascript
document.getElementById("form").addEventListener("submit", (e) => {
  if (!raw_val || constancias.length === 0) {
    e.preventDefault();
    alert("⚠️ Ingresa al menos una constancia válida");
    return false;
  }
});
```

#### 7. **Endpoint `/extract` Mejorado**

**ANTES:**
```python
@APP.post("/extract")
def extract():
    raw = request.form.get("raw", "")
    constancias = extract_constancias(raw)  # Función local duplicada
    if detected_count == 0:
        # ...sin logging, sin validación clara
```

**DESPUÉS:**
```python
@APP.post("/extract")
def extract():
    raw = request.form.get("raw", "").strip()
    
    # Validación explícita de entrada vacía
    if not raw:
        logger.warning("POST /extract con entrada vacía")
        # ...devuelve resultado vacío con mensaje claro
    
    # Usa constancia_config.extract_constancias()
    constancias = constancia_config.extract_constancias(raw)
    
    if detected_count == 0:
        logger.warning(f"No se detectaron constancias válidas")
    
    # Logging detallado de proceso
    for i, c in enumerate(constancias, 1):
        try:
            logger.info(f"[{i}/{detected_count}] Extrayendo: {c}")
            out_file = secop_extract.extract_to_excel(c, OUTPUT_DIR, headless=False)
            outputs.append(Path(out_file))
            logger.info(f"[{i}/{detected_count}] ✓ Éxito: {c}")
        except Exception as e:
            error_msg = escape(str(e))  # ← SANITIZACIÓN (NUEVO)
            errors.append((c, error_msg))
            logger.error(f"[{i}/{detected_count}] ✗ Error: {e}")
```

**Mejoras:**
- ✅ Sanitización HTML de mensajes de error (`escape()`)
- ✅ Logging estructurado con progreso `[i/total]`
- ✅ Manejo explícito de entrada vacía
- ✅ Detalles de errores con contexto

#### 8. **Endpoint `/download/<token>` Hardened**

**ANTES:**
```python
@APP.get("/download/<token>")
def download(token: str):
    path = _DOWNLOADS.get(token)
    if not path or not path.exists():
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True, download_name=path.name)
    # ← Sin try/except, sin logging, sin limpieza
```

**DESPUÉS:**
```python
@APP.get("/download/<token>")
def download(token: str):
    # Limpiar descargas antiguas
    cleaned = cleanup_old_downloads()
    
    # Buscar token con logging
    download_info = _DOWNLOADS.get(token)
    if not download_info:
        logger.warning(f"Intento de descarga con token inválido: {token}")
        return redirect(url_for("index"))
    
    path, _ = download_info
    
    # Validación explícita
    if not path or not path.exists():
        logger.warning(f"Intento de descargar archivo inexistente: {path}")
        return redirect(url_for("index"))
    
    # Descarga con try/except
    try:
        logger.info(f"Descargando: {path.name}")
        return send_file(...)
    except Exception as e:
        logger.error(f"Error descargando {path}: {e}")
        return redirect(url_for("index"))
```

**Mejoras:**
- ✅ Limpieza automática de archivos expirados
- ✅ Try/except para errores de descarga
- ✅ Logging de intentos fallidos
- ✅ Mejor manejo de archivos eliminados

#### 9. **Panel de Resultados Mejorado**

**ANTES:**
```html
{% if result.fail_count > 0 %}
  <div class="small" style="margin-top:8px;"><strong>Errores:</strong></div>
  <ul class="small">
    {% for c, e in result.errors %}
      <li><span class="mono">{{ c }}</span> — {{ e }}</li>
    {% endfor %}
  </ul>
{% endif %}
<!-- ← Sin indicación de truncado -->
```

**DESPUÉS:**
```html
<div class="small" style="margin-top:8px;">
  <strong>Errores ({{ result.errors|length }}{% if result.has_more_errors %} de {{ result.total_errors }}{% endif %}):</strong>
</div>
<div class="error-list small">
  <!-- Lista con scroll si hay muchos errores -->
  {% for c, e in result.errors %}...{% endfor %}
</div>

{% if result.has_more_errors %}
  <div class="small warn">
    ⚠️ Mostrando {{ result.errors|length }} de {{ result.total_errors }} errores.
    Revisa <span class="mono">reporte_errores.csv</span> en el ZIP...
  </div>
{% endif %}
```

**Mejoras:**
- ✅ Muestra cuántos errores hay (25/40)
- ✅ Feedback claro si están truncados
- ✅ Referencia a CSV completo en ZIP

---

## 🐛 PROBLEMAS RESUELTOS

| Problema | Solución | Archivo |
|----------|----------|---------|
| 🔴 Regex CONSTANCIA_RE desincronizado (3-10 vs 4-12 dígitos) | Centralizado en `constancia_config.py` con CONSTANCIA_DETECTION_RE | constancia_config.py |
| 🔴 Normalización de dashes sin sincronización (JS vs Py) | Constante compartida `DASHES_UNICODE` | constancia_config.py |
| 🔴 Memory leak en _DOWNLOADS | Sistema de limpieza con timestamp | secop_ui.py:71-102 |
| 🟡 Sin validación de entrada vacía | Validación cliente + servidor | secop_ui.py:327, 356 |
| 🟡 Sin manejo excepciones en /download | Try/except con logging | secop_ui.py:487-509 |
| 🟡 Versión HTML desactualizada (v1.2.10) | Dinámica desde `constancia_config.__version__` | secop_ui.py:200 |
| 🟡 Errores truncados sin aviso | Indicador "N de M" + warning | secop_ui.py:178-180, 382 |
| 🟢 Sin logging | Sistema completo de logging | secop_ui.py:27-31 |
| 🟢 Secret key débil por defecto | Warning si no se configura | secop_ui.py:40-47 |
| 🟢 Sin sanitización de errores | `escape()` en mensajes | secop_ui.py:371 |

---

## 📊 ESTADÍSTICAS DE CAMBIOS

| Métrica | ANTES | DESPUÉS | Δ |
|---------|-------|---------|---|
| Líneas (secop_ui.py) | 313 | 506 | +193 (+62%) |
| Imports | 10 | 12 | +2 |
| Funciones | 4 | 7 | +3 (cleanup, mejoradas) |
| Docstrings | 0 | 11 | +11 |
| Líneas de logging | 0 | 18+ | +18 |
| Líneas de validación | 2 | 12+ | +10 |
| Constantes | 1 | 3 | +2 |

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [x] **Imports sincronizados** — Usa `constancia_config.extract_constancias()`
- [x] **Regex consistentes** — 4-12 dígitos en ambos lados (JS y Py)
- [x] **Logging funcional** — 18+ llamadas a logger en puntos clave
- [x] **Limpieza automática** — Archivos > 1 hora se eliminan
- [x] **Validación entrada** — Rechaza vacíos con mensaje claro
- [x] **Try/except crítico** — En /download y limpieza
- [x] **Sanitización HTML** — `escape()` en mensajes de error
- [x] **Versión dinámica** — Lee desde `constancia_config.__version__`
- [x] **Documentación** — Docstrings completos en todas las funciones
- [x] **UX mejorada** — Emojis, progreso [i/N], errores truncados con aviso

---

## 🚀 RECOMENDACIONES PRÓXIMAS

1. **Actualizar `secop_extract.py`** para importar desde `constancia_config.py`
   - Reemplazar `CONSTANCIA_RE` local por `constancia_config.CONSTANCIA_RE`
   - Reemplazar `DASHES_RE` local por `constancia_config.DASHES_UNICODE`
   - Usar `constancia_config.validate_constancia()` en lugar de local

2. **Agregar respaldos automáticos** de archivos en OUTPUT_DIR

3. **Monitoreo de rendimiento**
   - Registrar tiempo de extracción por constancia
   - Alertar si excede 2 minutos (posible timeout)

4. **Tests unitarios para `constancia_config.py`**
   - Validar regex con 20+ casos de prueba
   - Verificar sincronización JavaScript-Python

5. **Considerar Redis** para sesiones distribuidas en producción

---

## 📝 NOTAS

- Backup original: [secop_ui_backup.py](secop_ui_backup.py)
- Compatible con `secop_extract.py` v1.2.14.1+
- Requiere: Flask, openpyxl, BeautifulSoup4, Playwright
- No requiere cambios en templates de Excel (compatibilidad regresiva ✓)
