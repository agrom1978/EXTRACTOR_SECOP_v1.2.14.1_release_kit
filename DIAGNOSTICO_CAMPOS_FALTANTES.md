# 🔴 Diagnóstico: Campos Faltantes en Salida Excel

## Problema Reportado
Los siguientes campos NO aparecen en el archivo Excel de resultados:
1. **Registro del documento del contratista** (CC/NIT)
2. **Documento del representante legal**

---

## Análisis del Flujo

### 1. PLANTILLA EXCEL (Esperado)
Archivo: `templates/Plantilla_Salida_EXTRACTOR_SECOP_v1.2.10.xlsx`

**Encabezados en hoja "Resultados_Extraccion":**

| Col | Encabezado | Estado |
|-----|-----------|--------|
| 17  | **Identificación del proponente (CC/NIT)** | ❌ FALTA |
| 18  | **Identificación del proponente/contratista (limpio)** | ❌ FALTA |
| 19  | Representante legal | ✓ Sí |
| 20  | **Identificación representante legal** | ❌ FALTA |
| 21  | **Identificación del representante legal (limpio)** | ❌ FALTA |

### 2. CÓDIGO EXTRACTOR (secop_extract.py - Líneas 680-700)

**Lo que se INTENTA escribir:**
```python
record = {
    ...
    "Identificación del proponente/contratista (CC/NIT)": ident_clean,  # ← MISMATCH!
    "Representante legal": rep_legal,
    "Identificación del representante legal (CC/NIT)": rep_ident_clean_final,  # ← MISMATCH!
    ...
}
```

**Lo que REALMENTE DEBERÍA ser:**
```python
record = {
    ...
    "Identificación del proponente (CC/NIT)": ident,           # ← NUEVO (raw)
    "Identificación del proponente/contratista (limpio)": ident_clean,  # ← RENOMBRADO
    "Representante legal": rep_legal,
    "Identificación representante legal": rep_ident,           # ← NUEVO (raw)
    "Identificación del representante legal (limpio)": rep_ident_clean_final,  # ← RENOMBRADO
    ...
}
```

---

## Raíz del Problema

### Desajuste de Nombres de Columnas

El diccionario `record` en `secop_extract.py` usa claves que **NO coinciden exactamente** con los encabezados de la plantilla:

| Campo | Clave en record | Clave en plantilla | Coincide |
|-------|-----------------|-------------------|----------|
| Identif. Contratista (raw) | ❌ No existe | "Identificación del proponente (CC/NIT)" | ❌ No |
| Identif. Contratista (limpio) | "Identificación del proponente/contratista (CC/NIT)" | "Identificación del proponente/contratista (limpio)" | ❌ No |
| Identif. Representante (raw) | ❌ No existe | "Identificación representante legal" | ❌ No |
| Identif. Representante (limpio) | "Identificación del representante legal (CC/NIT)" | "Identificación del representante legal (limpio)" | ❌ No |

### Cómo Falla el Flujo

```
1. HTML de SECOP se parsea correctamente
   ├─ ident_raw = "1234567890"  ✓
   └─ rep_ident_raw = "9876543210"  ✓

2. Se limpian los IDs
   ├─ ident_clean = _clean_id("1234567890") → "1234567890"  ✓
   └─ rep_ident_clean_final = _clean_id("9876543210") → "9876543210"  ✓

3. Se ARMA el diccionario record (AQUÍ ESTÁ EL ERROR)
   ├─ record["Identificación del proponente/contratista (CC/NIT)"] = "1234567890"  ← CLAVE INCORRECTA
   └─ record["Identificación del representante legal (CC/NIT)"] = "9876543210"  ← CLAVE INCORRECTA

4. Se ESCRIBE en Excel (Línea 726)
   for col_idx, h in enumerate(headers, start=1):
       if h in record:  ← BUSCA CLAVE "Identificación del proponente (CC/NIT)"
           ws.cell(row=row_idx, column=col_idx, value=record[h])
   
   Resultado: headers NO ENCUENTRA las claves en record → CELDA VACÍA ❌
```

---

## Solución

### Cambio en secop_extract.py (Líneas 680-700)

**ANTES (Incorrecto):**
```python
record = {
    ...
    "Identificación del proponente/contratista (CC/NIT)": ident_clean,
    "Representante legal": rep_legal,
    "Identificación del representante legal (CC/NIT)": rep_ident_clean_final,
    ...
}
```

**DESPUÉS (Correcto):**
```python
record = {
    ...
    "Identificación del proponente (CC/NIT)": ident,                              # RAW
    "Identificación del proponente/contratista (limpio)": ident_clean,           # LIMPIO
    "Representante legal": rep_legal,
    "Identificación representante legal": rep_ident_final,                        # RAW
    "Identificación del representante legal (limpio)": rep_ident_clean_final,    # LIMPIO
    ...
}
```

---

## Variables Disponibles en secop_extract.py (Línea 640-680)

```python
# Línea 641: Extracción dirigida por rótulo (la más estable)
rep_id_raw = _find_row_value_by_label(soup, "Identificación del Representante Legal")

# Línea 658: Extracción del contrato_map y general_map
ident = _get_first(contrato_map, [
    "Identificación del Contratista",
    "Identificacion del Contratista",
    "NIT del Contratista",
    "NIT", "Cédula", "Cedula", "Identificación", "Identificacion"
])

# Línea 659: Fallback en general_map
if not ident:
    ident = _get_first(general_map, ["Identificación", "Identificacion", "NIT", "Cédula", "Cedula"])

# Línea 661-668: Limpieza y priorización
ident_clean = _clean_id(ident)
rep_ident = _get_first(contrato_map, [...])
rep_ident_final = rep_id_raw or rep_ident  # Prioridad: rótulo > KV
rep_ident_clean_final = _clean_id(rep_ident_final)
```

✅ **Todas las variables están disponibles y correctamente extraídas.**

---

## Checklist de Implementación

- [ ] Abrir `secop_extract.py`
- [ ] Localizar línea ~690 (diccionario `record`)
- [ ] Cambiar clave "Identificación del proponente/contratista (CC/NIT)" → agregar versión raw
- [ ] Cambiar clave "Identificación del representante legal (CC/NIT)" → agregar versiones raw y limpia
- [ ] Validar que se usan variables: `ident`, `ident_clean`, `rep_ident_final`, `rep_ident_clean_final`
- [ ] Ejecutar prueba: `python secop_extract.py 25-11-14555665`
- [ ] Verificar en Excel que aparezcan los 5 campos de identificación

---

## Impacto de la Fix

**Antes:**
- Columna 17 (Identif. Contratista raw): **VACÍA** ❌
- Columna 18 (Identif. Contratista limpio): **VACÍA** ❌
- Columna 20 (Identif. Representante): **VACÍA** ❌
- Columna 21 (Identif. Representante limpio): **VACÍA** ❌

**Después:**
- Columna 17: Valor del CC/NIT sin limpiar (ej: "1.234.567-8") ✓
- Columna 18: Valor limpio del CC/NIT (ej: "12345678") ✓
- Columna 20: Documento del representante sin limpiar ✓
- Columna 21: Documento del representante limpio ✓

---

## Referencias de Código

| Línea | Función | Propósito |
|-------|---------|----------|
| 641 | `_find_row_value_by_label()` | Extrae ID representante legal por etiqueta HTML |
| 658-668 | Búsqueda en `contrato_map`/`general_map` | Extrae identificaciones por clave mapa |
| 670-672 | Priorización | Usa etiqueta si existe, sino KV map |
| 673-674 | Limpieza | `_clean_id()` elimina caracteres especiales |
| 680-700 | Construcción record | **AQUÍ ESTÁ EL BUG** |
| 726 | Escritura en Excel | Usa claves de record para llenar celdas |

