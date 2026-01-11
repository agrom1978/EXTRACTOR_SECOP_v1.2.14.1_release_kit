from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json

import secop_extract

FIXTURES_DIR = Path("fixtures/detalle")
REPORTS_DIR = Path("reports/offline")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Defina aquí los valores esperados por fixture (archivo HTML).
# Ejemplo:
# EXPECTED = {
#   "Detalle_SAMC_009_25.html": {
#       "Código Registro Presupuestal (CRP)": "2511250001",
#       "Identificación del representante legal (limpio)": "84009052",
#   }
# }
EXPECTED = {
    # "mi_archivo.html": {
    #     "Código Registro Presupuestal (CRP)": "2511250001",
    #     "Identificación del representante legal (limpio)": "84009052",
    # },
}

FIELDS_UNDER_TEST = [
    "Código Registro Presupuestal (CRP)",
    "Identificación del representante legal (limpio)",
]


def _read_html(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> None:
    results = []
    ok = 0
    fail = 0

    fixtures = sorted(FIXTURES_DIR.glob("*.html"))
    if not fixtures:
        print(f"No se encontraron fixtures HTML en: {FIXTURES_DIR.resolve()}")
        print("Coloque aquí archivos .html de 'Detalle del proceso' y vuelva a ejecutar.")
        return

    for html_path in fixtures:
        record = secop_extract.extract_record_from_html(_read_html(html_path), constancia_ok="")

        expected = EXPECTED.get(html_path.name, {})
        mismatches = []

        # Si no hay EXPECTED para el fixture, lo marcamos como 'SIN_EXPECTED'
        status = "SIN_EXPECTED" if not expected else "OK"

        for field in FIELDS_UNDER_TEST:
            obtained = str(record.get(field, "") or "").strip()
            exp_val = str(expected.get(field, "") or "").strip() if expected else ""

            if expected and obtained != exp_val:
                status = "FAIL"
                mismatches.append({
                    "field": field,
                    "expected": exp_val,
                    "obtained": obtained,
                })

        if status == "OK":
            ok += 1
        elif status == "FAIL":
            fail += 1

        results.append({
            "fixture": html_path.name,
            "status": status,
            "record": {k: record.get(k, "") for k in ["Código Registro Presupuestal (CRP)",
                                                     "Identificación del representante legal",
                                                     "Identificación del representante legal (limpio)"]},
            "mismatches": mismatches,
        })

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total_fixtures": len(results),
            "ok": ok,
            "fail": fail,
            "sin_expected": sum(1 for r in results if r["status"] == "SIN_EXPECTED"),
        },
        "results": results,
    }

    out_path = REPORTS_DIR / f"reporte_validacion_offline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("VALIDACIÓN OFFLINE FINALIZADA")
    print(f"OK: {ok} | FAIL: {fail} | SIN_EXPECTED: {report['summary']['sin_expected']}")
    print(f"Reporte: {out_path.resolve()}")


if __name__ == "__main__":
    main()
