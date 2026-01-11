FIX DEFINITIVO – FASE B (Extractor SECOP v1.2.14.1)
=================================================

Problema corregido
------------------
Error 500 al abrir la UI:
  NameError: HEADLESS_DEFAULT is not defined

Causa
-----
La variable HEADLESS_DEFAULT era utilizada en la plantilla,
pero no estaba definida en secop_ui.py.

Corrección aplicada
-------------------
Se define explícitamente:

- Función _env_flag()
- Variable HEADLESS_DEFAULT basada en la variable de entorno SECOP_HEADLESS

Cómo aplicar
------------
1. Reemplaza tu archivo actual:
     secop_ui.py
   por:
     secop_ui_FaseB_CORREGIDO.py
   (renómbralo a secop_ui.py)

2. Reinicia el extractor (cierra la consola y vuelve a ejecutar el .bat).

Opcional
--------
Define el modo por defecto del navegador:

  setx SECOP_HEADLESS 1   -> headless
  setx SECOP_HEADLESS 0   -> visible

Resultado esperado
------------------
- La UI abre sin error 500.
- El checkbox “modo oculto (headless)” funciona correctamente.
- Fase B queda estable y operativa.
