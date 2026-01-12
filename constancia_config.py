# constancia_config.py
"""
Configuración centralizada de formato y validación de constancias.
Este módulo es compartido entre secop_extract.py y secop_ui.py para garantizar
consistencia en la detección, validación y normalización de constancias.

Formato de constancia: YY-XX-NNNN
Ejemplos válidos:
  - 25-1-241304 (4 dígitos en tercera posición)
  - 25-15-14542595 (8 dígitos en tercera posición)
  - 25-11-14555665 (8 dígitos en tercera posición)
"""

import re
from typing import List, Set

# ============================================================================
# CONSTANTES UNICODE PARA NORMALIZACIÓN
# ============================================================================
# Caracteres dash Unicode que pueden aparecer en texto pegado/copiado
DASHES_UNICODE = "‐‑‒–—―"  # U+2010 a U+2015 (6 caracteres)

# ============================================================================
# EXPRESIÓN REGULAR CONSTANCIA
# ============================================================================
# Formato: YY-XX-NNNN
# - YY: exactamente 2 dígitos (año de dos cifras)
# - XX: 1-2 dígitos (mes o subsección)
# - NNNN: 4-12 dígitos (número secuencial)
# 
# Utilizamos ^ y $ para validación exacta (no solo detection con \b)
CONSTANCIA_RE = re.compile(r"^(?P<yy>\d{2})-(?P<xx>\d{1,2})-(?P<num>\d{4,12})$")

# Patrón alternativo para DETECTION con word boundaries (usado en UI para extraer del texto)
# Permite detectar constancias dentro de bloques de texto sin anclas
CONSTANCIA_DETECTION_RE = re.compile(r"\b(\d{2}-\d{1,2}-\d{4,12})\b")

# ============================================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normaliza texto de entrada:
    - Convierte espacios no-breaking en espacios regulares
    - Convierte todos los dashes Unicode en ASCII hyphen (-)
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
        
    Ejemplos:
        >>> normalize_text("25–1–241304")  # en-dash
        "25-1-241304"
        >>> normalize_text("25—1—241304")  # em-dash
        "25-1-241304"
    """
    if not text:
        return ""
    
    # Reemplazar nbsp (U+00A0) con espacio regular
    text = text.replace("\u00A0", " ")
    
    # Reemplazar todos los dashes Unicode con ASCII hyphen
    for dash in DASHES_UNICODE:
        text = text.replace(dash, "-")
    
    return text


def normalize_constancia(constancia: str) -> str:
    """
    Normaliza una constancia individual:
    - Trim
    - Normaliza dashes
    - Elimina espacios
    
    Args:
        constancia: Constancia bruta (ej: "25–1–241304  ")
        
    Returns:
        Constancia normalizada (ej: "25-1-241304")
    """
    text = (constancia or "").strip()
    text = normalize_text(text)
    text = re.sub(r"\s+", "", text)
    return text


def validate_constancia(constancia: str) -> str:
    """
    Valida formato de constancia.
    
    Args:
        constancia: Constancia a validar (puede estar sin normalizar)
        
    Returns:
        Constancia normalizada si es válida
        
    Raises:
        ValueError: Si el formato no es válido
        
    Ejemplos:
        >>> validate_constancia("25-1-241304")
        "25-1-241304"
        >>> validate_constancia("25–1–241304")  # convierte dashes
        "25-1-241304"
        >>> validate_constancia("invalid")
        ValueError: Constancia inválida...
    """
    normalized = normalize_constancia(constancia)
    
    if not CONSTANCIA_RE.match(normalized):
        raise ValueError(
            f"Constancia inválida: '{constancia}'. "
            f"Formato esperado: YY-XX-NNNN (ej.: 25-1-241304, 25-15-14542595)"
        )
    
    return normalized


def extract_constancias(raw_text: str) -> List[str]:
    """
    Extrae todas las constancias de un texto, eliminando duplicados.
    
    Args:
        raw_text: Texto que puede contener una o más constancias
        
    Returns:
        Lista de constancias únicas, en orden de aparición, normalizadas
        
    Ejemplos:
        >>> extract_constancias("25-1-241304\\n25-15-14542595\\n25-1-241304")
        ["25-1-241304", "25-15-14542595"]
        
        >>> extract_constancias("Tabla: 25–1–241304 y también 25–15–14542595")
        ["25-1-241304", "25-15-14542595"]
    """
    normalized_text = normalize_text(raw_text)
    found_raw = CONSTANCIA_DETECTION_RE.findall(normalized_text)
    
    # Deduplicación manteniendo orden de aparición
    seen: Set[str] = set()
    result: List[str] = []
    
    for constancia_raw in found_raw:
        constancia = normalize_constancia(constancia_raw)
        if constancia not in seen:
            seen.add(constancia)
            result.append(constancia)
    
    return result


# ============================================================================
# VERSIONADO
# ============================================================================
__version__ = "1.2.14.1"
