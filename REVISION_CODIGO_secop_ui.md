# REVISIÓN DE CÓDIGO: secop_ui.py

**Fecha:** 11 de enero de 2026  
**Versión:** 1.2.14.1  
**Revisor:** Análisis Automático

---

## 🔴 INCONSISTENCIAS CRÍTICAS

### 1. **Duplicación de Lógica de Normalización** ⚠️ CRÍTICO
**Ubicación:** Líneas 155 (JavaScript) vs 170 (Python)

**Problema:**
- JavaScript tiene `normalizeText()` que convierte dashes Unicode
- Python tiene `_normalize_text()` que hace lo mismo
- **Pero están implementadas DIFERENTE:**
  - JS: `replace(/[‐‑‒–—―]/g, "-")` (6 caracteres Unicode)
  - Python: `.translate(str.maketrans({c: "-" for c in "‐‑‒–—―"}))` (6 caracteres)
  - ✅ Son iguales, PERO si se actualizan deben sincronizarse

**Riesgo:** Si alguien agrega/quita un carácter en uno de los lados, la normalización se rompe.

**Recomendación:**
- Extraer los caracteres Unicode a una CONSTANTE compartida
- O usar expresión regular idéntica en ambos lados

---

### 2. **Duplicación de Regex CONSTANCIA_RE** 🟡 IMPORTANTE
**Ubicación:** 
- Línea 28 en `secop_ui.py`: `CONSTANCIA_RE = re.compile(r"\b(\d{2}-\d{1,2}-\d{3,10})\b")`
- `secop_extract.py` línea 23: `CONSTANCIA_RE = re.compile(r"^(?P<yy>\d{2})-(?P<xx>\d{1,2})-(?P<num>\d{4,12})$")`

**Problema:**
- Son DIFERENTES:
  - `secop_ui.py`: Permite 3-10 dígitos en tercera posición
  - `secop_extract.py`: Permite 4-12 dígitos
  - `secop_ui.py` usa `\b` (word boundaries), `secop_extract.py` usa `^...$` (anchors exactos)

- **Consecuencia:** Una constancia válida en UI podría ser rechazada en backend (o viceversa)
  - Ejemplo: `25-1-123` pasa en UI (3 dígitos) pero fallaría en extract.py (mínimo 4)

**Riesgo:** Validación inconsistente = bugs en producción

**Recomendación:**
```python
# Crear archivo: constancia_regex.py (compartido)
CONSTANCIA_RE = re.compile(r"^(?P<yy>\d{2})-(?P<xx>\d{1,2})-(?P<num>\d{4,12})$")
DASHES_UNICODE = "‐‑‒–—―"
```
- Importar en ambos archivos
- Así están SIEMPRE en sync

---

### 3. **Inconsistencia en Detección de Constancias (JS vs Python)**
**Ubicación:** Línea 155 (JS) vs línea 177 (Python `extract_constancias()`)

**Problema:**
- JS usa `/\b(\d{2}-\d{1,2}-\d{3,10})\b/g` (permite 3-10 dígitos)
- Python usa la misma regex de `secop_extract.py` (4-12 dígitos via `CONSTANCIA_RE`)
- **Resultado:** El navegador detecta constancias que Python rechaza después

**Ejemplo:**
```
Usuario pega: 25-1-123
JavaScript detecta: Constancias detectadas: 1 ✓
Python extrae:     Error: Constancia inválida (menos de 4 dígitos) ✗
```

---

### 4. **Desincronización de Versión HTML vs Código**
**Ubicación:** Línea 113 (HTML) vs realidad

```html
<div><span class="mono">v1.2.10</span> · O.Guerra26</div>
```

**Problema:**
- El footer dice `v1.2.10` pero debería ser `v1.2.14.1`
- Crea confusión en usuarios sobre qué versión está corriendo

---

## 🟡 PROBLEMAS DE CALIDAD

### 5. **Falta de Validación de Entrada en `/extract`**
**Ubicación:** Línea 211 (`@APP.post("/extract")`)

**Problema:**
```python
raw = request.form.get("raw", "")
constancias = extract_constancias(raw)
```

- No valida si `raw` está vacío ANTES de procesar
- Si usuario hace POST con campo vacío, devuelve estado 200 pero sin hacer nada
- No hay feedback claro de "sin constancias detectadas"

**Recomendación:**
```python
if not raw or not raw.strip():
    return render_template_string(HTML, raw="", result={
        "detected_count": 0,
        "ok_count": 0,
        "fail_count": 0,
        "output_name": "—",
        "download_url": None,
        "errors": [],
        "message": "⚠️ Ingresa al menos una constancia"
    })
```

---

### 6. **Gestión de Memoria: _DOWNLOADS no se limpia**
**Ubicación:** Línea 24 (`_DOWNLOADS: Dict[str, Path] = {}`)

**Problema:**
- Diccionario crece indefinidamente en memoria
- Después de cada descarga, la entrada no se elimina
- En producción con múltiples usuarios → memory leak

**Riesgo:** Servidor consume más RAM con cada extracción

**Recomendación:**
```python
import time

_DOWNLOADS: Dict[str, Tuple[Path, float]] = {}  # (path, timestamp)

def cleanup_old_downloads(max_age_seconds=3600):
    """Elimina descargas más antiguas que max_age_seconds"""
    now = time.time()
    expired = [k for k, (_, t) in _DOWNLOADS.items() if now - t > max_age_seconds]
    for k in expired:
        try:
            _DOWNLOADS[k][0].unlink()  # elimina archivo
        except:
            pass
        del _DOWNLOADS[k]

# En /download/<token>:
cleanup_old_downloads()
path, _ = _DOWNLOADS.get(token, (None, 0))
```

---

### 7. **Falta Manejo de Excepciones en Descarga**
**Ubicación:** Línea 267 (`@APP.get("/download/<token>")`)

**Problema:**
```python
return send_file(path, as_attachment=True, download_name=path.name)
```

- Si el archivo fue eliminado entre que se generó y se descargó → crash
- No hay try/except para `send_file()`
- Usuario ve página de error genérica en lugar de mensaje claro

**Recomendación:**
```python
@APP.get("/download/<token>")
def download(token: str):
    path = _DOWNLOADS.get(token)
    if not path or not path.exists():
        return render_template_string(HTML, raw="", result={
            "errors": [("sistema", "Archivo expirado o no encontrado. Intenta nuevamente.")],
        }), 404
    try:
        return send_file(path, as_attachment=True, download_name=path.name)
    except Exception as e:
        return render_template_string(HTML, raw="", result={
            "errors": [("sistema", f"Error al descargar: {str(e)}")],
        }), 500
```

---

### 8. **Limite de Errores Mostrados (25) No Está Documentado**
**Ubicación:** Línea 253

```python
errors_ui = errors[:25]
```

**Problema:**
- Trunca el listado de errores silenciosamente
- Usuario no sabe que hay más errores si envía 50 constancias y 40 fallan
- No hay mensaje "Mostrando 25 de 40 errores"

**Recomendación:**
```python
MAX_ERRORS_DISPLAY = 25
errors_ui = errors[:MAX_ERRORS_DISPLAY]
has_more_errors = len(errors) > MAX_ERRORS_DISPLAY

result = {
    ...
    "errors": errors_ui,
    "has_more_errors": has_more_errors,
    "total_errors": len(errors),
}

# En HTML:
{% if result.has_more_errors %}
  <div class="small warn">⚠️ Mostrando {{ result.errors|length }} de {{ result.total_errors }} errores</div>
{% endif %}
```

---

### 9. **Endpoint `/extract` No Valida Método HTTP Explícitamente**
**Ubicación:** Línea 211

```python
@APP.post("/extract")
def extract():
```

- Usa decorador `@APP.post()` correctamente ✓
- Pero `request.form.get()` podría fallar si no hay form data
- No hay validación de Content-Type

**Recomendación:**
```python
@APP.post("/extract")
def extract():
    if request.content_type and "application/x-www-form-urlencoded" not in request.content_type:
        return {"error": "Content-Type debe ser application/x-www-form-urlencoded"}, 400
    
    raw = request.form.get("raw", "").strip()
    # ...resto del código
```

---

## 🟢 PROBLEMAS MENORES

### 10. **Imports No Utilizados en Algunas Rutas**
**Ubicación:** Líneas 10-13

```python
from flask import Flask, request, send_file, render_template_string, url_for, redirect
```

- Se importan pero `redirect` solo se usa una vez (línea 271)
- Considerar si es realmente necesario (es estándar, OK dejar)

---

### 11. **Falta de Logging**
**Problema:**
- No hay registro de errores o eventos
- Si falla una extracción, no queda log en el servidor
- Dificulta debugging en producción

**Recomendación:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# En extract():
logger.info(f"Iniciando extracción de {detected_count} constancias")
logger.error(f"Error extrayendo {c}: {e}")
```

---

### 12. **Session Security: Secret Key Débil por Defecto**
**Ubicación:** Línea 16

```python
APP.secret_key = os.environ.get("SECOP_UI_SECRET", "secop-ui-local")
```

**Problema:**
- Secret key por defecto es predecible (`"secop-ui-local"`)
- Si no se configura variable de entorno, seguridad baja

**Recomendación:**
```python
import warnings

secret = os.environ.get("SECOP_UI_SECRET")
if not secret:
    secret = "secop-ui-local"
    warnings.warn(
        "⚠️ SECOP_UI_SECRET no configurado. Usa una clave segura en producción.",
        RuntimeWarning
    )

APP.secret_key = secret
```

---

### 13. **Falta Sanitización en Mensajes de Error**
**Ubicación:** Línea 246

```python
errors.append((c, str(e)))
```

**Problema:**
- `str(e)` podría contener caracteres especiales o paths del sistema
- No se sanitiza antes de mostrar en HTML (aunque Jinja2 por defecto escapa, es buena práctica explícita)

**Recomendación:**
```python
from html import escape

errors.append((c, escape(str(e))))
```

---

### 14. **Redundancia en Instrucciones de UI**
**Ubicación:** Líneas 85-104

Hay DOS secciones con instrucciones prácticamente idénticas:
- Línea 85: `<div id="runtime">` (oculta hasta submit)
- Línea 97: `<div class="hint">` (siempre visible)

Ambas explican lo mismo:
```
1. Se abrirá navegador por constancia
2. Resolver reCAPTCHA manualmente
3. Salida en hoja Resultados_Extraccion
4. ZIP si hay múltiples/errores
```

**Recomendación:** Fusionar en una sola sección o hacer que una sea resumen y otra detalle

---

### 15. **Timestamp no Sincronizado entre Python y JavaScript**
**Ubicación:** Línea 237 (Python) y no existe en JS

**Problema:**
- Timestamp se genera EN SERVIDOR cuando se procesa
- JavaScript no sabe del timestamp, así que ZIP se descarga con timestamp del SERVIDOR
- Si usuario abre UI en zona horaria diferente, puede confundirse

**Recomendación:**
- Pasar timestamp al template y mostrar en resultado

---

## 📋 RESUMEN DE PRIORIDADES

| Criticidad | Problema | Línea | Acción |
|-----------|----------|-------|--------|
| 🔴 CRÍTICA | Duplicación regex constancia (3-10 vs 4-12 dígitos) | 28, extract.py:23 | **Unificar en constante compartida** |
| 🔴 CRÍTICA | Normalización dashes sin sincronización | 155 (JS), 170 (Py) | **Crear CONSTANTES_UNICODE compartidas** |
| 🟡 ALTA | _DOWNLOADS sin limpieza (memory leak) | 24 | **Implementar cleanup con timestamp** |
| 🟡 ALTA | Sin validación entrada vacía | 211 | **Agregar validación previa** |
| 🟡 MEDIA | Sin manejo excepciones en /download | 267 | **Agregar try/except y mensaje claro** |
| 🟡 MEDIA | Versión HTML desactualizada | 113 | **Actualizar a v1.2.14.1** |
| 🟢 BAJA | Falta logging | — | **Agregar logger** |
| 🟢 BAJA | Secret key débil por defecto | 16 | **Agregar warning** |

---

## ✅ LO QUE ESTÁ BIEN

- ✓ Estructura clara de rutas (GET `/`, POST `/extract`, GET `/download`)
- ✓ Detección de constancias en JavaScript con deduplicación
- ✓ Manejo de ZIP automático cuando hay múltiples extracciones
- ✓ UI responsiva con feedback visual (loading, resultados)
- ✓ Uso de tokens aleatorios para seguridad de descarga
- ✓ Integración limpia con `secop_extract.py`
- ✓ HTML bien formado y accesible (lang="es", charset UTF-8)
- ✓ Reporte de errores en CSV incluido en ZIP

---

## 🔧 PRÓXIMOS PASOS RECOMENDADOS

1. **INMEDIATO:** Unificar regex CONSTANCIA_RE en archivo compartido
2. **INMEDIATO:** Sincronizar normalización de dashes (crear constante Unicode)
3. **PRONTO:** Implementar cleanup automático de _DOWNLOADS
4. **PRONTO:** Agregar validación de entrada vacía
5. **PRONTO:** Actualizar versión en HTML a v1.2.14.1
6. **DESPUÉS:** Agregar logging estructurado
7. **DESPUÉS:** Mejorar manejo de excepciones globales
