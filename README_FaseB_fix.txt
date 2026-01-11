EXTRACTOR SECOP v1.2.14.1 — Fix post Fase B (UI)
==================================================

Problema resuelto
-----------------
- Error 500 al abrir / (Internal Server Error) por:
    NameError: HEADLESS_DEFAULT is not defined

Ajustes incluidos (seguros, sin cambio de lógica)
-------------------------------------------------
1) Se define HEADLESS_DEFAULT con base en la variable de entorno:
     SECOP_HEADLESS = 1  -> checkbox marcado (headless por defecto)
     SECOP_HEADLESS = 0  -> checkbox desmarcado (visible por defecto)

2) Se convierte el template HTML a raw string (HTML = r""" ... """)
   para eliminar el warning:
     SyntaxWarning: invalid escape sequence '\d'

Cómo implementar
---------------
1) En tu proyecto, reemplaza el archivo:
     secop_ui.py
   por:
     secop_ui_FaseB_fix.py  (renómbralo a secop_ui.py)

2) Reinicia el servidor (cierra la consola y vuelve a ejecutar el .bat o el comando).

3) (Opcional) Definir el modo por defecto:
     - PowerShell:
         setx SECOP_HEADLESS 1
     - CMD:
         setx SECOP_HEADLESS 1

   Usa 0 para volver a modo visible por defecto.

Verificación rápida
-------------------
- Abre http://127.0.0.1:5000
- Debe cargar la UI sin error 500.
- El checkbox “modo oculto (headless)” debe reflejar SECOP_HEADLESS.
