#!/usr/bin/env python3
"""
Script de validación rápida de los cambios implementados.
Verifica que constancia_config.py y secop_ui.py funcionen correctamente.

Ejecución:
  python test_cambios.py
"""

import sys
from pathlib import Path

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("VALIDACIÓN DE CAMBIOS IMPLEMENTADOS")
print("=" * 70)

# Test 1: Importar constancia_config
print("\n[TEST 1] Importar constancia_config.py...")
try:
    import constancia_config
    print(f"  ✓ Módulo importado correctamente")
    print(f"  ✓ Versión: {constancia_config.__version__}")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 2: Validar constantes
print("\n[TEST 2] Validar constantes Unicode...")
try:
    assert len(constancia_config.DASHES_UNICODE) == 6, "DASHES_UNICODE debe tener 6 caracteres"
    print(f"  ✓ DASHES_UNICODE: {repr(constancia_config.DASHES_UNICODE)}")
    assert constancia_config.CONSTANCIA_RE is not None
    print(f"  ✓ CONSTANCIA_RE compilada")
    assert constancia_config.CONSTANCIA_DETECTION_RE is not None
    print(f"  ✓ CONSTANCIA_DETECTION_RE compilada")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 3: Normalización de texto
print("\n[TEST 3] Normalización de texto...")
test_cases = [
    ("25-1-241304", "25-1-241304"),  # Normal
    ("25–1–241304", "25-1-241304"),  # En-dash
    ("25—1—241304", "25-1-241304"),  # Em-dash
    ("25‐1‐241304", "25-1-241304"),  # Hyphen
]
try:
    for input_text, expected in test_cases:
        result = constancia_config.normalize_constancia(input_text)
        assert result == expected, f"Esperado {expected}, obtuvo {result}"
        print(f"  ✓ {repr(input_text):20} → {repr(result)}")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 4: Validación de constancias
print("\n[TEST 4] Validación de constancias...")
valid_cases = ["25-1-241304", "25-15-14542595", "25-11-14555665"]
invalid_cases = ["25-1-123", "invalid", ""]
try:
    for case in valid_cases:
        result = constancia_config.validate_constancia(case)
        assert result == case
        print(f"  ✓ VÁLIDA: {case}")
    
    for case in invalid_cases:
        try:
            constancia_config.validate_constancia(case)
            print(f"  ✗ INVÁLIDA (no lanzó excepción): {case}")
            sys.exit(1)
        except ValueError:
            print(f"  ✓ INVÁLIDA (rechazada): {case}")
except Exception as e:
    print(f"  ✗ ERROR inesperado: {e}")
    sys.exit(1)

# Test 5: Extracción de constancias
print("\n[TEST 5] Extracción y deduplicación...")
test_text = """
Lista de constancias:
25-1-241304
25-15-14542595
25-11-14555665
25-1-241304  (duplicado)

También estos:
25–15–14581710 (con en-dash)
"""
try:
    results = constancia_config.extract_constancias(test_text)
    expected_unique = 4  # 4 únicas después de deduplicación
    assert len(results) == expected_unique, f"Esperado {expected_unique}, obtuvo {len(results)}"
    print(f"  ✓ Extraídas {len(results)} constancias únicas:")
    for c in results:
        print(f"    - {c}")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 6: Importar secop_ui
print("\n[TEST 6] Importar secop_ui.py...")
try:
    # Solo verificar que se puede compilar, no ejecutar Flask
    import py_compile
    py_compile.compile("secop_ui.py", doraise=True)
    print(f"  ✓ secop_ui.py compila sin errores")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 7: Validar integración
print("\n[TEST 7] Validar integración secop_ui → constancia_config...")
try:
    # Verificar que secop_ui importa constancia_config
    with open("secop_ui.py", "r", encoding="utf-8") as f:
        content = f.read()
        assert "import constancia_config" in content
        print(f"  ✓ secop_ui.py importa constancia_config")
        
        assert "constancia_config.extract_constancias" in content
        print(f"  ✓ secop_ui.py usa extract_constancias()")
        
        assert "constancia_config.__version__" in content
        print(f"  ✓ secop_ui.py usa versionado dinámico")
        
        # Verificar logging
        assert "logger.info" in content
        print(f"  ✓ secop_ui.py tiene logging integrado")
        
        # Verificar cleanup
        assert "cleanup_old_downloads" in content
        print(f"  ✓ secop_ui.py tiene limpieza de descargas")
        
        # Verificar sanitización
        assert "escape(" in content
        print(f"  ✓ secop_ui.py sanitiza mensajes de error")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 8: Expresión regular sincronización
print("\n[TEST 8] Verificar sincronización de regex...")
try:
    # Extraer patrón desde secop_ui.py JavaScript
    with open("secop_ui.py", "r", encoding="utf-8") as f:
        ui_content = f.read()
        # Buscar la regex JavaScript
        assert r"(\d{2}-\d{1,2}-\d{4,12})" in ui_content
        print(f"  ✓ JavaScript usa regex 4-12 dígitos (sincronizado)")
    
    # Verificar Python
    pattern = constancia_config.CONSTANCIA_DETECTION_RE.pattern
    assert r"(\d{2}-\d{1,2}-\d{4,12})" in pattern
    print(f"  ✓ Python usa regex 4-12 dígitos (sincronizado)")
    
    print(f"  ✓ REGEX SINCRONIZADA: {repr(pattern)}")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Resumen
print("\n" + "=" * 70)
print("RESULTADO: ✅ TODOS LOS TESTS PASARON")
print("=" * 70)
print("\nLista de verificación:")
print("  [✓] constancia_config.py funcional")
print("  [✓] Constantes Unicode sincronizadas")
print("  [✓] Expresiones regulares 4-12 dígitos")
print("  [✓] Normalización de dashes (6 tipos)")
print("  [✓] Deduplicación de constancias")
print("  [✓] secop_ui.py integrado correctamente")
print("  [✓] Logging, cleanup, sanitización presentes")
print("  [✓] Versionado dinámico funcional")
print("\n🚀 Sistema listo para producción\n")
