# Líneas Redundantes Encontradas

## 🔍 Resumen de Redundancias

1. **Código duplicado**: Bloque de cálculo CRP duplicado (líneas 628-632 y 774-777)
2. **Asignación redundante**: `crp = crp_final` (línea 683)
3. **Asignación redundante**: `rp_clean = crp` (línea 684)
4. **Funciones similares**: `_digits_only` y `_extract_digits` hacen lo mismo

---

## 1. CÓDIGO DUPLICADO - Cálculo de CRP

### 📍 Ubicación 1: `extract_to_excel()` - Líneas 628-632

```python
# 3) Presupuestal (RP table + fallback KV)
rp = _parse_rp_table(soup)
# Prioridad RP: tabla presupuestal de la sección; fallback conservador a búsqueda tolerante
crp_from_table = _extract_rp_code(rp.get("codigo_rp", ""))
crp_fallback = _find_rp_code(soup) if not crp_from_table else ""
crp_final = crp_from_table or crp_fallback
```

### 📍 Ubicación 2: `extract_record_from_html()` - Líneas 774-777

```python
# RP/CRP (prioridad por tabla de sección; fallback tolerante)
rp = _parse_rp_table(soup)
crp_from_table = _extract_rp_code(rp.get("codigo_rp", ""))
crp_fallback = _find_rp_code(soup) if not crp_from_table else ""
crp = crp_from_table or crp_fallback
```

**Problema:** El mismo bloque de código está duplicado en dos funciones diferentes. Esto viola el principio DRY (Don't Repeat Yourself).

**Recomendación:** Extraer este bloque a una función helper como:
```python
def _extract_crp_code(soup: BeautifulSoup) -> str:
    """Extrae el código CRP usando tabla + fallback."""
    rp = _parse_rp_table(soup)
    crp_from_table = _extract_rp_code(rp.get("codigo_rp", ""))
    if not crp_from_table:
        crp_fallback = _find_rp_code(soup)
        return crp_fallback
    return crp_from_table
```

---

## 2. ASIGNACIÓN REDUNDANTE - Línea 683

```python
# RP/CRP final (prioriza tabla de sección; fallback tolerante)
crp = crp_final
rp_clean = crp
```

**Línea 683:** `crp = crp_final`
- **Problema:** `crp_final` ya contiene el valor correcto calculado en la línea 632. Esta asignación es innecesaria.
- **Uso:** `crp` se usa en la línea 686: `_determine_tipo_proceso(bpim, fuente_fin, crp)`
- **Recomendación:** Usar directamente `crp_final` o renombrar `crp_final` a `crp` desde el inicio.

**Código actual:**
```python
crp_final = crp_from_table or crp_fallback
# ... más código ...
crp = crp_final  # ← REDUNDANTE
```

**Código mejorado:**
```python
crp = crp_from_table or crp_fallback  # Renombrar directamente a crp
# ... más código ...
# Usar crp directamente sin reasignación
```

---

## 3. ASIGNACIÓN REDUNDANTE - Línea 684

```python
crp = crp_final
rp_clean = crp  # ← REDUNDANTE
```

**Línea 684:** `rp_clean = crp`
- **Problema:** `rp_clean` se asigna desde `crp`, pero `rp_clean` se usa solo una vez en el diccionario `record` (línea 695).
- **Uso:** Se usa en `record["Registro Presupuestal (RP/CRP) (limpio)"] = rp_clean`
- **Recomendación:** Usar directamente `crp` en el diccionario o eliminar la asignación intermedia.

**Código actual:**
```python
rp_clean = crp
# ... más código ...
record = {
    ...
    "Registro Presupuestal (RP/CRP) (limpio)": rp_clean,
    ...
}
```

**Código mejorado:**
```python
# Eliminar línea 684
record = {
    ...
    "Registro Presupuestal (RP/CRP) (limpio)": crp,  # Usar crp directamente
    ...
}
```

---

## 4. FUNCIONES SIMILARES - `_digits_only` vs `_extract_digits`

### `_digits_only()` - Líneas 146-149
```python
def _digits_only(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\D+", "", str(s))
```

### `_extract_digits()` - Líneas 395-400
```python
def _extract_digits(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    d = re.sub(r"[^0-9]", "", s)
    return d
```

**Problema:** Ambas funciones hacen prácticamente lo mismo:
- `_digits_only`: usa `\D+` (cualquier no-dígito) y convierte a string
- `_extract_digits`: usa `[^0-9]` (cualquier no-dígito), hace strip primero

**Uso actual:**
- `_digits_only`: Usada 1 vez (línea 200 en `_find_rp_code`)
- `_extract_digits`: Usada 1 vez (línea 404 en `_clean_id`)

**Recomendación:** Unificar en una sola función. `_extract_digits` es más robusta (hace strip), así que usar esa y eliminar `_digits_only`:

```python
# Eliminar _digits_only y reemplazar su uso:
# Línea 200: raw_digits = _digits_only(raw)
# Cambiar a: raw_digits = _extract_digits(raw)
```

---

## 📊 Resumen de Líneas Redundantes

| # | Tipo | Líneas | Archivo | Prioridad |
|---|------|--------|---------|-----------|
| 1 | Código duplicado | 628-632, 774-777 | secop_extract.py | Alta |
| 2 | Asignación redundante | 683 | secop_extract.py | Media |
| 3 | Asignación redundante | 684 | secop_extract.py | Media |
| 4 | Funciones similares | 146-149, 395-400 | secop_extract.py | Baja |

---

## ✅ Beneficios de Corregir

1. **Menos duplicación** → Más fácil de mantener
2. **Código más claro** → Menos variables intermedias innecesarias
3. **Mejor rendimiento** → Menos operaciones redundantes
4. **Principio DRY** → Una sola fuente de verdad

---

*Documento generado analizando el código fuente actual*
