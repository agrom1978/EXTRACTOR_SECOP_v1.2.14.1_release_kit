# Instrucciones para Ajustar la Plantilla Excel

## 📋 Cambios Aplicados en el Código Python

✅ **Ya aplicados en `scripts/secop_extract.py`:**
1. Eliminado campo: `"Registro Presupuestal (RP/CRP) (limpio)"`
2. Eliminado campo: `"Identificación del proponente (CC/NIT)"`
3. Eliminado campo: `"Identificación representante legal"`
4. Renombrado: `"Identificación del proponente/contratista (limpio)"` → `"Identificación del proponente/contratista (CC/NIT)"`
5. Renombrado: `"Identificación del representante legal (limpio)"` → `"Identificación del representante legal (CC/NIT)"`

---

## 🔧 Cambios Necesarios en la Plantilla Excel

### Archivo: `templates/Plantilla_Salida_EXTRACTOR_SECOP_v1.2.10.xlsx`

### Paso 1: Abrir la Plantilla
1. Abre el archivo `templates/Plantilla_Salida_EXTRACTOR_SECOP_v1.2.10.xlsx`
2. Ve a la hoja **"Resultados_Extraccion"**

### Paso 2: Eliminar Columnas Redundantes

#### 2.1 Eliminar Columna 9: "Registro Presupuestal (RP/CRP) (limpio)"
- **Ubicación:** Columna I (después de "Código Registro Presupuestal (CRP)")
- **Acción:** 
  1. Click derecho en el encabezado de la columna I
  2. Seleccionar "Eliminar"
  3. O seleccionar toda la columna (click en la letra I) y presionar Ctrl + -

#### 2.2 Eliminar Columna 17: "Identificación del proponente (CC/NIT)"
- **Ubicación:** Columna Q (actualmente después de "Razón social del proponente/contratista")
- **Nota:** Después de eliminar la columna 9, esta será la columna Q
- **Acción:** Mismo procedimiento que arriba

#### 2.3 Eliminar Columna 20: "Identificación representante legal"
- **Ubicación:** Columna T (después de "Representante legal")
- **Nota:** Después de eliminar las columnas anteriores, esta será la columna T
- **Acción:** Mismo procedimiento que arriba

### Paso 3: Renombrar Columnas

#### 3.1 Renombrar: "Identificación del proponente/contratista (limpio)"
- **Ubicación:** Columna Q (después de eliminar las anteriores)
- **Nuevo nombre:** `Identificación del proponente/contratista (CC/NIT)`
- **Acción:**
  1. Click en la celda del encabezado
  2. Cambiar el texto a: `Identificación del proponente/contratista (CC/NIT)`

#### 3.2 Renombrar: "Identificación del representante legal (limpio)"
- **Ubicación:** Columna S (después de eliminar las anteriores)
- **Nuevo nombre:** `Identificación del representante legal (CC/NIT)`
- **Acción:**
  1. Click en la celda del encabezado
  2. Cambiar el texto a: `Identificación del representante legal (CC/NIT)`

---

## ✅ Verificación Final

Después de hacer los cambios, verifica que:

1. **Total de columnas:** Deben quedar **22 columnas** (antes eran 25)
2. **Columnas eliminadas:**
   - ✅ Ya no existe "Registro Presupuestal (RP/CRP) (limpio)"
   - ✅ Ya no existe "Identificación del proponente (CC/NIT)"
   - ✅ Ya no existe "Identificación representante legal"

3. **Columnas renombradas:**
   - ✅ "Identificación del proponente/contratista (limpio)" → "Identificación del proponente/contratista (CC/NIT)"
   - ✅ "Identificación del representante legal (limpio)" → "Identificación del representante legal (CC/NIT)"

4. **Orden final de columnas debe ser:**
   1. Número de proceso (informativo)
   2. Número de constancia
   3. Abrir detalle
   4. Tipo de Gasto
   5. Estado del proceso
   6. Modalidad de contratación
   7. Fuente de financiación
   8. Código Registro Presupuestal (CRP)
   9. Número de contrato
   10. Objeto del contrato
   11. Valor del contrato (COP)
   12. Plazo de ejecución
   13. Fecha de inicio
   14. Fecha de terminación
   15. Razón social del proponente/contratista
   16. Identificación del proponente/contratista (CC/NIT) ← **RENOMBRADA**
   17. Representante legal
   18. Identificación del representante legal (CC/NIT) ← **RENOMBRADA**
   19. Código BPIM
   20. Fuente del documento
   21. Estado de validación
   22. Observaciones

---

## 📝 Notas Importantes

- **Hacer backup:** Antes de modificar, guarda una copia de seguridad de la plantilla original
- **Formulas:** Si hay fórmulas en otras hojas que referencian estas columnas, ajustarlas también
- **Formato:** Mantén el formato (negrita, color, etc.) de los encabezados
- **Pruebas:** Después de los cambios, ejecuta una extracción de prueba para verificar que todo funciona

---

## 🔄 Alternativa: Crear Nueva Plantilla

Si prefieres crear una nueva plantilla desde cero:

1. Copia la plantilla actual como `Plantilla_Salida_EXTRACTOR_SECOP_v1.2.11.xlsx`
2. Aplica los cambios en la nueva versión
3. Actualiza la ruta en `scripts/secop_extract.py` línea 613 si es necesario

---

*Instrucciones para sincronizar la plantilla Excel con los cambios aplicados en el código Python*
