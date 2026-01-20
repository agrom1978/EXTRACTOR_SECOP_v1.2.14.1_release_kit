# 🔍 ANÁLISIS: Lógica de Detección de Bloqueo Anti-DDoS/WAF

## Pregunta del Usuario
> "Si la aplicación abre y despliega el detalle del proceso, la extracción de datos es local... ¿Dónde está la lógica a este error de bloqueo?"

---

## 📋 RESPUESTA: La Detección de Bloqueo es **Local/HTML**

La detección **NO** depende de códigos HTTP o conexiones rechazadas. En lugar de eso:

1. **Playwright sí abre la página** (no hay rechazo a nivel HTTP)
2. **Descarga el HTML renderizado** (el navegador completó la carga)
3. **Analiza el contenido del HTML** en búsqueda de patrones típicos de bloqueo anti-bot
4. **Si encuentra indicadores**, dispara el error de bloqueo

---

## 🔴 BLOCK_MARKERS: Los 6 Marcadores de Bloqueo

La aplicación busca estas 6 frases exactas en el **contenido HTML descargado**:

```python
BLOCK_MARKERS = [
    "access blocked",
    "acceso bloqueado",
    "possible ddos",
    "denegacion",
    "hic",
    "incident id",
]
```

### Significado de Cada Marcador

| Marcador | Origen | Significado |
|----------|--------|------------|
| `"access blocked"` | CloudFlare / WAF genérico | Acceso rechazado explícitamente |
| `"acceso bloqueado"` | SECOP (es-CO) | Versión en español del mensaje anterior |
| `"possible ddos"` | CloudFlare / Detectores anti-bot | Sospecha de patrón DDoS |
| `"denegacion"` | SECOP / Sistemas legacy | Denegación de acceso genérica |
| `"hic"` | CloudFlare Incident Code | Código de incidente de CloudFlare |
| `"incident id"` | CloudFlare / WAF genérico | ID de incidente (señal de bloqueo) |

---

## 🔎 CÓMO FUNCIONA LA DETECCIÓN

### Función: `_is_blocked_html(html: str) -> bool`

```python
def _is_blocked_html(html: str) -> bool:
    text = (html or "").lower()  # ← Convertir a minúsculas
    return any(marker in text for marker in BLOCK_MARKERS)  # ← Buscar ANY marcador
```

**Lógica:**
1. Toma el HTML descargado
2. Lo convierte a minúsculas (case-insensitive)
3. Busca si **CUALQUIERA** de los 6 marcadores está presente en el texto
4. **Si encuentra 1 o más → Retorna TRUE (bloqueado)**
5. **Si no encuentra ninguno → Retorna FALSE (OK)**

---

## 🚨 DÓNDE SE DISPARA LA DETECCIÓN

### En `_fetch_detail_html_with_page()` (línea 474-476)

```python
def _fetch_detail_html_with_page(page, constancia: str, timeout_ms: int = 120_000) -> str:
    url = build_url(constancia)
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(1500)
    try:
        page.wait_for_selector("td.tttablas", timeout=20_000)
    except PWTimeoutError:
        pass
    page.wait_for_timeout(1200)
    html = page.content()
    
    # ← AQUÍ ACONTECE LA DETECCIÓN
    if _is_blocked_html(html):
        raise SecopExtractionError(
            "Acceso bloqueado por el sitio (posible DDoS/WAF). Deteniendo el lote; esperar y/o contactar soporte."
        )
    return html
```

**Secuencia:**
1. ✅ Playwright abre la URL
2. ✅ Espera a que se cargue el DOM (`wait_until="domcontentloaded"`)
3. ✅ Espera elementos típicos (`td.tttablas`)
4. ✅ Descarga el HTML renderizado con `page.content()`
5. 🔴 **Analiza el HTML buscando marcadores**
6. 🔴 **Si encuentra → Lanza SecopExtractionError**

---

## 📍 ESCENARIOS DE DETECCIÓN

### Escenario 1: CloudFlare "Access Denied"
```html
<!-- HTML DevueltoDescargado por Playwright -->
<html>
    <head><title>403 Forbidden</title></head>
    <body>
        <h1>Access Blocked</h1>
        <p>Possible DDoS attack detected...</p>
        <p>Incident ID: a1b2c3d4e5f6</p>
    </body>
</html>
```

**Detección:**
- ✅ Contiene: `"access blocked"` (match)
- ✅ Contiene: `"possible ddos"` (match)
- ✅ Contiene: `"incident id"` (match)
- 🔴 **RESULTADO: Bloqueado → Error disparado**

---

### Escenario 2: SECOP con Página de Error
```html
<!-- HTML Descargado -->
<html>
    <body>
        <div class="error-panel">
            <h2>Acceso bloqueado</h2>
            <p>El sistema ha detectado múltiples intentos...</p>
        </div>
    </body>
</html>
```

**Detección:**
- ✅ Contiene: `"acceso bloqueado"` (match)
- 🔴 **RESULTADO: Bloqueado → Error disparado**

---

### Escenario 3: SECOP Normal (SIN Bloqueo)
```html
<!-- HTML Normal Descargado -->
<html>
    <body>
        <table>
            <tr><td class="tttablas">Modalidad de Selección</td><td>Licitación Pública</td></tr>
            <!-- ... Datos normales ... -->
        </table>
    </body>
</html>
```

**Detección:**
- ❌ NO contiene ninguno de los 6 marcadores
- ✅ **RESULTADO: NO bloqueado → Continúa extracción normal**

---

## ⚠️ FALSOS POSITIVOS POSIBLES

Aunque la lógica es razonablemente específica, pueden ocurrir falsos positivos si:

1. **La palabra "bloqueado" aparece en metadatos u objeto del proceso**
   - Ejemplo: Un proceso llamado "Sistema de Bloqueo de Puertas"
   - HTML incluye: `"...procuramiento del sistema de bloqueo..."`
   - Detección: Falso positivo

2. **La palabra "hic" aparece como sigla legítima**
   - Ejemplo: Un proveedor con código "HIC-2025"
   - HTML incluye: `"...código contratista: HIC-2025..."`
   - Detección: Falso positivo

3. **Documentos adjuntos con nombres que contienen estos términos**

---

## 🔗 FLUJO COMPLETO EN LOTES

```
usuario_paste_constancias()
  ↓
extract_batch_to_excel(constancias)
  ↓
for cada constancia:
  ├─ _fetch_detail_html_with_page(page, constancia)
  │   ├─ page.goto(url)
  │   ├─ page.wait_for_selector("td.tttablas")
  │   ├─ html = page.content()  ← DESCARGA COMPLETA
  │   ├─ _is_blocked_html(html)  ← ⚠️ ANÁLISIS LOCAL
  │   │   └─ if any(marker in html.lower()): BLOQUEADO
  │   └─ if bloqueado: raise SecopExtractionError
  │
  ├─ [ÉXITO] Procesa HTML normalmente
  │
  └─ [ERROR] Captura error y establece blocked=True
      └─ break  ← Salir del lote
```

---

## 🛑 IMPACTO EN EL LOTE

Cuando se detecta bloqueo:

```python
# En extract_batch_to_excel() línea 987-990
except SecopExtractionError as e:
    msg = str(e)
    errors.append((c, msg))
    if "bloqueado" in msg.lower() or "blocked" in msg.lower():
        blocked = True
        break  # ← SALIR DEL CICLO INMEDIATAMENTE
    backoff = min(backoff * 2, backoff_max_seconds)
```

**Acciones:**
1. ✅ Registra el error para la constancia actual
2. 🔴 Detecta que contiene "bloqueado"
3. 🛑 Detiene el procesamiento de constancias posteriores
4. ⏸️ **No intenta procesar más constancias del lote**

**Resultado en UI:**
```
Errores encontrados (2):
  ✗ 25-12-14585765 - Acceso bloqueado por el sitio (posible DDoS/WAF)...
  ✗ _BLOQUEO_ - Lote detenido por bloqueo anti-DDoS. Reintenta más tarde.
```

---

## 💡 VENTAJA DE ESTA ARQUITECTURA

### ¿Por qué NOT basarse solo en códigos HTTP?

**SECOP usa CloudFlare que:**
- ✅ Devuelve HTTP 200 (conexión exitosa)
- ✅ Entrega HTML (no rechaza a nivel TCP)
- ❌ Pero el HTML contiene página de bloqueo (no el contenido real)

**Nuestra solución:**
- ✅ Abre exitosamente (HTTP 200)
- ✅ Descarga el HTML (Playwright lo renderiza)
- ✅ Analiza el contenido (busca marcadores específicos)
- ✅ Detecta bloqueo aunque HTTP sea 200

---

## 📊 ESTADÍSTICAS

| Métrica | Valor |
|---------|-------|
| **Marcadores definidos** | 6 |
| **Búsqueda** | Case-insensitive (convertido a minúsculas) |
| **Lógica** | ANY (cualquiera de los 6 activa bloqueo) |
| **Localización detección** | En el HTML descargado (ANÁLISIS LOCAL) |
| **No requiere** | Códigos HTTP, headers, o conexión secundaria |

---

## 🎯 CONCLUSIÓN

**Tu pregunta:** *"Si abre y despliega el detalle, ¿dónde está la lógica?"*

**Respuesta:** La lógica está **dentro del HTML descargado**, no en la conexión:

```
Búsqueda en HTML (ANÁLISIS LOCAL):
  if "access blocked" in html ✓
  if "acceso bloqueado" in html ✓
  if "possible ddos" in html ✓
  if "denegacion" in html ✓
  if "hic" in html ✓
  if "incident id" in html ✓
  
Si CUALQUIER condición = TRUE → BLOQUEADO
```

No depende de rechazos HTTP sino de **análisis de contenido HTML** que Playwright ya descargó.

---

**Archivo relevante:** [secop_extract.py](secop_extract.py#L30-L40) y [secop_extract.py](secop_extract.py#L456-L480)
