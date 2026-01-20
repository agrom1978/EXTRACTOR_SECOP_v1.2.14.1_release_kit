# MANIFESTO DE ENTREGA - AutoSECOP1

## Objetivo
Entregar una aplicacion estable para extraccion y consolidacion de datos SECOP I.

## Entregables
- UI web: secop_ui.py
- Motor de extraccion: secop_extract.py
- Configuracion central: constancia_config.py
- Plantilla Excel: templates/Plantilla_Salida_EXTRACTOR_SECOP_v1.2.10.xlsx
- Validacion offline: validators/validate_offline.py

## Criterios de aceptacion
- La UI inicia en http://127.0.0.1:5000
- La extraccion genera un Excel unico por lote
- Se registran errores por constancia
- La validacion de formato de constancia funciona

## Metricas de calidad
- Tests ejecutados: 8
- Pasados: 8
- Fallidos: 0
- Exito: 100%

## Soporte
- Revisar GUIA_DESPLIEGUE.md y GUIA_PRUEBAS_UI.md
