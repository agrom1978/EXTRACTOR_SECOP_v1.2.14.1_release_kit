# CAMBIOS IMPLEMENTADOS - AutoSECOP1

Este documento resume mejoras principales del release actual.

## UI (secop_ui.py)
- Logo y header actualizados.
- Mejor jerarquia visual en formulario.
- Contadores en tiempo real: validas, duplicadas, invalidas.
- CTA con estado de carga y spinner.
- Guia rapida colapsable.
- Panel de resultados centrado y consistente.

## Extraccion (secop_extract.py)
- Validacion y normalizacion de constancias.
- Extraccion robusta de RP y CDP.
- Deteccion local de bloqueo (WAF) por marcadores en HTML.
- Exportacion a plantilla Excel.

## Configuracion (constancia_config.py)
- Regex centralizadas para deteccion y validacion.
- Normalizacion de dashes Unicode.

## Validacion
- tests automatizados en test_cambios.py, test_campos_faltantes.py y test_extraccion_html_completa.py
- validacion offline con validators/validate_offline.py

## Metricas
- Tests ejecutados: 8
- Pasados: 8
- Fallidos: 0
- Exito: 100%
