from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if SCRIPTS_DIR.exists():
    sys.path.insert(0, str(SCRIPTS_DIR))

import secop_extract

FIXTURES_DIR = Path("fixtures/detalle")
REPORTS_DIR = Path("reports/offline")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Defina aqui los valores esperados por fixture (archivo HTML).
# Ejemplo:
# EXPECTED = {
#   "Detalle_SAMC_009_25.html": {
#       "Registro Presupuestal (RP)": "2511250001",
#       "Certificado de disponibilidad presupuestal": "84009052",
#   }
# }
EXPECTED = {
    # "mi_archivo.html": {
    #     "Registro Presupuestal (RP)": "2511250001",
    #     "Certificado de disponibilidad presupuestal": "84009052",
    # },
}

FIELDS_UNDER_TEST = [
    "Registro Presupuestal (RP)",
    "Certificado de disponibilidad presupuestal",
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
        print("Coloque aqui archivos .html de 'Detalle del proceso' y vuelva a ejecutar.")
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
            "record": {k: record.get(k, "") for k in ["Registro Presupuestal (RP)","Certificado de disponibilidad presupuestal"]},
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
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print("VALIDACION OFFLINE FINALIZADA")
    print(f"OK: {ok} | FAIL: {fail} | SIN_EXPECTED: {report['summary']['sin_expected']}")
    print(f"Reporte: {out_path.resolve()}")


if __name__ == "__main__":
    main()
