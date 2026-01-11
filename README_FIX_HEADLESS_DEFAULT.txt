FIX – HEADLESS_DEFAULT (Extractor SECOP v1.2.14.1)
=================================================

Síntoma
-------
Al abrir http://127.0.0.1:5000 aparece error 500 y en consola:

  NameError: name 'HEADLESS_DEFAULT' is not defined

Causa
-----
secop_ui.py usa HEADLESS_DEFAULT en index(), pero la variable no está definida
en el archivo.

Corrección
----------
Se agrega el bloque:

  def _env_flag(...)
  HEADLESS_DEFAULT = _env_flag("SECOP_HEADLESS", default=False)

Ubicación: inmediatamente después de:
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

Cómo aplicar
------------
1) Reemplaza tu secop_ui.py por el que viene en este ZIP (mismo nombre).
2) Reinicia el .bat / servidor.

Verificación
------------
- Abre http://127.0.0.1:5000
- Debe cargar la UI sin error 500.
