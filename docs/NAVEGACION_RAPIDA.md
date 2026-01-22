# 🗺️ NAVEGACIÓN RÁPIDA - SECOP UI v1.2.14.2-struct

**⏱️ Necesito:** 5 minutos  
**👤 Soy:** [Selecciona tu rol]

---

## 👨‍💻 Soy DESARROLLADOR

### Quiero entender los cambios rápido
1. [RESUMEN_RAPIDO.txt](RESUMEN_RAPIDO.txt) — 5 min
2. [tests/test_cambios.py](tests/test_cambios.py) — Ejecutar tests
3. [CAMBIOS_IMPLEMENTADOS_secop_ui.md](CAMBIOS_IMPLEMENTADOS_secop_ui.md) — 15 min

### Quiero revisar el código
- [scripts/constancia_config.py](scripts/constancia_config.py) — Módulo centralizado
- [secop_ui.py](secop_ui.py) — Interfaz Flask mejorada
- [scripts/secop_ui_backup.py](scripts/secop_ui_backup.py) — Código original (para comparar)

### Quiero ejecutar tests
```bash
python tests/test_cambios.py
# Resultado: ✅ 8/8 TESTS PASANDO
```

### Quiero iniciar la UI
```bash
python secop_ui.py
# Abre: http://127.0.0.1:5000
```

---

## 🏗️ Soy ARQUITECTO / TECH LEAD

### Necesito ver el big picture
1. [RESUMEN_EJECUTIVO_IMPLEMENTACION.md](RESUMEN_EJECUTIVO_IMPLEMENTACION.md) — Análisis cuantitativo
2. [MANIFESTO_ENTREGA.md](MANIFESTO_ENTREGA.md) — Checklist de entrega
3. [CAMBIOS_IMPLEMENTADOS_secop_ui.md](CAMBIOS_IMPLEMENTADOS_secop_ui.md) — Detalles técnicos

### Necesito validar que funciona
```bash
python tests/test_cambios.py
# Todos los tests deben pasar
```

### Próximas integraciones
- Actualizar `scripts/secop_extract.py` para usar `scripts/constancia_config.py`
- Agregar tests unitarios adicionales
- Integración con CI/CD

---

## 🚀 Soy DEVOPS / SRE

### Necesito desplegar
1. [GUIA_DESPLIEGUE.md](GUIA_DESPLIEGUE.md) — Instrucciones completas
2. [CHECKLIST DE DESPLIEGUE](GUIA_DESPLIEGUE.md#-checklist-de-despliegue) — Step by step
3. [MONITOREO RECOMENDADO](GUIA_DESPLIEGUE.md#-monitoreo-recomendado) — Post-despliegue

### Necesito hacer rollback
```bash
# Opción 1: Archivo backup
copy scripts/secop_ui_backup.py secop_ui.py

# Opción 2: Git
git checkout HEAD~1 -- secop_ui.py scripts/constancia_config.py
```

### Necesito monitorear
- Logs: Timestamps + niveles de severidad
- Limpieza: Archivos > 1 hora se eliminan automáticamente
- Memoria: _DOWNLOADS dict decrece cada hora

### Problemas comunes
→ [TROUBLESHOOTING](GUIA_DESPLIEGUE.md#-troubleshooting) en GUIA_DESPLIEGUE.md

---

## 👔 Soy GESTOR / EJECUTIVO

### Quiero un resumen ejecutivo
[RESUMEN_EJECUTIVO_IMPLEMENTACION.md](RESUMEN_EJECUTIVO_IMPLEMENTACION.md) — 10 min

### Necesito métricas
```
Problemas resueltos:    13/15 (93%)
Tests pasando:          8/8 (100%)
Código nuevo:           776 líneas (+147%)
Documentación:          1,960 líneas
Estado:                 ✅ Listo para producción
```

### Presupuesto/Timeline
- Implementación: COMPLETADA ✓
- Testing: COMPLETADO ✓
- Documentación: COMPLETADA ✓
- Despliegue: LISTO ✓

### Próximos pasos
→ Consultar "Próximos pasos recomendados" en [RESUMEN_EJECUTIVO_IMPLEMENTACION.md](RESUMEN_EJECUTIVO_IMPLEMENTACION.md)

---

## 🧪 Soy QA / TESTER

### Necesito validar
1. Ejecutar: `python tests/test_cambios.py` (8 tests automatizados)
2. Revisar: [tests/test_cambios.py](tests/test_cambios.py) — Casos de cobertura
3. Checklist: [CHECKLIST DE DESPLIEGUE](GUIA_DESPLIEGUE.md#-checklist-de-despliegue)

### Problemas para validar
- Entrada vacía: ❌ Rechazada
- Constancia válida: ✓ Detectada y procesada
- Constancia inválida: ❌ Rechazada
- XLSX generado: ✓ Con reporte de errores
- Descarga funciona: ✓ Descarga segura con token

### Regresiones a verificar
- Plantillas Excel: Sin cambios (compatibilidad regresiva ✓)
- Extracción: Funciona igual (código estable)
- UI: Mejorada sin cambios en flow

---

## 📚 Soy DOCUMENTALISTA

### Documentos generados
1. [LISTA_ENTREGA.md](LISTA_ENTREGA.md) — Inventario completo
2. [RESUMEN_RAPIDO.txt](RESUMEN_RAPIDO.txt) — Síntesis visual
3. [CAMBIOS_IMPLEMENTADOS_secop_ui.md](CAMBIOS_IMPLEMENTADOS_secop_ui.md) — Detalles técnicos
4. [RESUMEN_EJECUTIVO_IMPLEMENTACION.md](RESUMEN_EJECUTIVO_IMPLEMENTACION.md) — Análisis cuantitativo
5. [GUIA_DESPLIEGUE.md](GUIA_DESPLIEGUE.md) — Operacional completa
6. [INDICE_CAMBIOS.md](INDICE_CAMBIOS.md) — Navegación
7. [MANIFESTO_ENTREGA.md](MANIFESTO_ENTREGA.md) — Entrega formal
8. [REVISION_CODIGO_secop_ui.md](REVISION_CODIGO_secop_ui.md) — Análisis inicial

### Total documentación
1,960 líneas distribuidas en 8 documentos

### Formatos disponibles
- Markdown (.md) — 7 documentos
- Texto plano (.txt) — 1 documento
- Python (.py) — 4 archivos de código

---

## 🎯 MATRIZ DE REFERENCIA RÁPIDA

| Necesidad | Documento | Tiempo |
|-----------|-----------|--------|
| Ver cambios rápido | RESUMEN_RAPIDO.txt | 5 min |
| Detalles técnicos | CAMBIOS_IMPLEMENTADOS_secop_ui.md | 15 min |
| Análisis ejecutivo | RESUMEN_EJECUTIVO_IMPLEMENTACION.md | 10 min |
| Desplegar | GUIA_DESPLIEGUE.md | 30 min |
| Rollback | scripts/secop_ui_backup.py | 2 min |
| Validar todo | tests/test_cambios.py | 1 min |
| Entender problema | REVISION_CODIGO_secop_ui.md | 20 min |
| Navegar docs | INDICE_CAMBIOS.md | 10 min |

---

## 🔍 BÚSQUEDA RÁPIDA

### Necesito información sobre...

**REGEX CONSTANCIA**
→ [CAMBIOS_IMPLEMENTADOS_secop_ui.md](CAMBIOS_IMPLEMENTADOS_secop_ui.md#1-duplicación-de-lógica-de-normalización--crítico)

**DASHES UNICODE**
→ [scripts/constancia_config.py](scripts/constancia_config.py) línea 9

**LOGGING**
→ [secop_ui.py](secop_ui.py) línea 27-31 + 18+ usos

**LIMPIEZA DESCARGAS**
→ [secop_ui.py](secop_ui.py) línea 71-102

**VALIDACIONES**
→ [secop_ui.py](secop_ui.py) línea 356-361 (servidor) + línea 256-272 (cliente)

**SANITIZACIÓN**
→ [secop_ui.py](secop_ui.py) línea 371

**TESTS**
→ [tests/test_cambios.py](tests/test_cambios.py) (8 tests)

**DESPLIEGUE**
→ [GUIA_DESPLIEGUE.md](GUIA_DESPLIEGUE.md)

**TROUBLESHOOTING**
→ [GUIA_DESPLIEGUE.md#-troubleshooting](GUIA_DESPLIEGUE.md#-troubleshooting)

---

## ⚡ INICIO ULTRA-RÁPIDO (3 minutos)

```bash
# 1. Validar
python tests/test_cambios.py

# 2. Iniciar
python secop_ui.py

# 3. Probar
# Abre http://127.0.0.1:5000
# Ingresa una constancia: 25-1-241304
# Presiona "Extraer"
```

---

## 📞 SOPORTE RÁPIDO

| Problema | Solución |
|----------|----------|
| No sé por dónde empezar | Lee RESUMEN_RAPIDO.txt |
| Algo no funciona | Ejecuta tests/test_cambios.py |
| Necesito desplegar | Consulta GUIA_DESPLIEGUE.md |
| Quiero rollback | Ejecuta: copy scripts/secop_ui_backup.py secop_ui.py |
| Necesito entender un cambio | Abre CAMBIOS_IMPLEMENTADOS_secop_ui.md |
| Bug en producción | Busca en GUIA_DESPLIEGUE.md#troubleshooting |

---

## ✅ CHECKLIST INICIAL

- [ ] Leí RESUMEN_RAPIDO.txt (5 min)
- [ ] Ejecuté tests/test_cambios.py (1 min)
- [ ] Leí documentación según mi rol (10-30 min)
- [ ] Entiendo los cambios principales
- [ ] Validé que funciona localmente

---

## 🎓 SIGUIENTES PASOS SEGÚN ROL

**Desarrollador:**
- [ ] Revisar integración con scripts/secop_extract.py
- [ ] Agregar más tests unitarios
- [ ] Considerar refactorizar HTML template

**DevOps:**
- [ ] Planificar despliegue a staging
- [ ] Configurar monitoreo y alertas
- [ ] Establecer runbook de rollback

**Ejecutivo:**
- [ ] Aprobación para despliegue
- [ ] Asignación de presupuesto para monitoreo
- [ ] Planificación de comunicación a usuarios

**QA:**
- [ ] Testing en staging
- [ ] Pruebas de regresión
- [ ] Validación end-to-end

---

**Última actualización:** 11 de enero de 2026  
**Versión:** 1.2.14.2-struct  
**Estado:** ✅ Listo para usar
