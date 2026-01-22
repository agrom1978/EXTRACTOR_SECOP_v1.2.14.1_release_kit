ROADMAP MEJORAS - EXTRACTOR SECOP

Objetivo
- Planificar mejoras para futuras versiones del extractor con enfoque en instalacion, rendimiento, UX, validacion y mantenimiento.

Instalacion
- Crear install.bat o setup.ps1 para:
  - Verificar version de Python.
  - Crear/activar venv.
  - Instalar dependencias desde requirements.txt.
  - Lanzar tools/arrancar_secop_ui.bat al finalizar.
- Generar requirements.txt con versiones fijas.
- Agregar README_INSTALACION.txt con pasos claros y offline-safe.

Rendimiento y tiempo de extraccion
- Medir tiempos por constancia y total (logging con time.monotonic).
- Reutilizar browser/context de Playwright en lote para reducir overhead.
- Habilitar timeout configurable via variable de entorno.
- Reintentos controlados para fallos transitorios (goto/selector).

UX y operacion
- Progreso real (n/total) en UI con endpoint de estado o polling simple.
- Mensajes en UI alineados con un solo Excel consolidado.
- Hoja "Resumen" en el Excel con totales OK/ERROR.

Validacion y calidad
- Mejorar tools/run_validate_offline.bat con mensajes mas claros y check de fixtures.
- Agregar fixtures de ejemplo y README en fixtures/.
- Validacion automatica de campos criticos con reporte mas detallado.

Mantenimiento y estructura
- Migrar HTML embebido a templates/index.html.
- Centralizar configuracion en .env o config.toml.
- Logging a archivo con rotacion en logs/.
- Normalizar encoding en todo el repo (UTF-8 o ASCII consistente).

Notas
- Las mejoras se implementaran en futuras versiones segun prioridad y disponibilidad.
