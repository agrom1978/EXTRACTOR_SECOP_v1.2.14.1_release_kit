#!/usr/bin/env python3
"""
Validacion offline de extraccion completa usando HTML guardado.
Requiere el HTML de FireShot usado en la prueba de CDP.
"""

import re
import sys
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

import secop_extract

HTML_PATH = r"C:\Users\USUARIO\Downloads\FireShot\Detalle del proceso_ LIC 002-25.html"


def _norm_text(s: str) -> str:
    s = (s or "").strip()
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def _get_value_by_norm_key(record: dict, norm_key: str) -> str:
    for k, v in record.items():
        if _norm_text(k) == norm_key:
            return v or ""
    return ""


def main() -> int:
    html_file = Path(HTML_PATH)
    if not html_file.exists():
        print(f"[SKIP] No existe HTML de prueba: {HTML_PATH}")
        return 0

    html = html_file.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    record = secop_extract._build_record_from_soup(soup, "25-15-14581710")

    print("[INFO] Datos extraidos:")
    for k in sorted(record.keys()):
        print(f"  {k}: {record[k]}")

    assert record.get("Certificado de disponibilidad presupuestal") == "2502060001"
    assert record.get("Registro Presupuestal (RP)") == "2503100004"
    assert record.get("Valor del contrato (COP)") == "496510063"
    assert _norm_text(record.get("Modalidad de contratacion")) == "licitacion publica"
    assert _norm_text(record.get("Estado del proceso")) == "liquidado"
    assert _norm_text(record.get("Numero de proceso (informativo)")) == "lic 002 25"
    assert _norm_text(record.get("Numero de contrato")) == "069 25 ver adiciones"
    assert record.get("Identificacion del proponente/contratista") == "900228413"
    assert _get_value_by_norm_key(record, "identificacion del representante legal") == "84009052"

    print("[OK] Extraccion completa valida (HTML offline).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
