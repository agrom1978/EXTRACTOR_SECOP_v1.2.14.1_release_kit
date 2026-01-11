# Copilot Instructions for SECOP Extractor

## Project Overview

SECOP Extractor is a Python tool that scrapes procurement contract details from **SECOP I** (Colombian government contracts portal) and exports them to standardized Excel spreadsheets.

**Main Components:**
- **`secop_extract.py`** (800 lines): Core scraping logic—HTML parsing, field extraction, data cleaning, Excel generation
- **`secop_ui.py`** (296 lines): Flask web UI for batch processing with error handling and ZIP packaging
- **`validators/validate_offline.py`**: Regression testing framework for extraction accuracy using local HTML fixtures

## Architecture & Data Flow

### 1. Input Normalization → Validation
- **Entry point**: User pastes constancia numbers (format: `YY-XX-NNNN`, e.g., `25-11-14555665`)
- **Normalization**: Convert Unicode dashes to ASCII `-`, trim whitespace, deduplicate
- **Validation**: `validate_constancia()` enforces format via `CONSTANCIA_RE` regex
- **Error class**: `SecopExtractionError` for all extraction failures

### 2. Web Scraping (Playwright)
- **`fetch_detail_html(constancia, headless=False)`**: Uses Playwright to navigate to SECOP detail page
- **Timeout**: 120 seconds with manual reCAPTCHA resolution support (non-headless mode)
- **Returns**: Raw HTML → parsed via BeautifulSoup for field extraction

### 3. HTML Field Extraction (Tolerant Parsing)
SECOP's HTML structure is inconsistent. Extraction uses layered fallbacks:

- **Layer 1 - Targeted extraction**: For critical fields like representative ID and CRP (RP) code
  - `_find_row_value_by_label()`: Case-insensitive label matching in table cells
  - `_extract_crp_code()`: Uses table structure (columns: Código, Fecha, Valor) + regex fallback
  
- **Layer 2 - Section-based KV pairs**: For General info (modalidad, estado) and Contract info (objeto, valor)
  - `_parse_section_kv(header_text)`: Finds section header, locates next table, extracts key-value pairs
  - `_parse_all_kv()`: Fallback that scans entire page for 2-column tables
  - `_kv_to_map()`: Normalizes keys (lowercase, remove diacritics, collapse spaces)
  
- **Layer 3 - Specialized parsers**: 
  - `_parse_fuente_financiacion()`: Table-first, then KV fallback
  - `_find_rp_code()`: Direct table columns OR regex in full text

**Key normalization utility**: `_norm_key(s)` removes accents, lowercases, collapses spaces for robust matching

### 4. Data Cleaning & Type Conversion
Applied post-extraction to normalize inconsistent portal values:

- **`_clean_id(raw)`**: Extracts digits from ID fields (removes hyphens, letters)
- **`_clean_money(s)`**: Converts currency (handles es-CO `608.603.520,00` + en-US `608,603,520.00`) → numeric string
- **`_clean_bpim(raw)`**: Normalizes BPIM/BPIN codes (extracts YYYY + consecutive sequence)
- **`_clean_fuente_financiacion(raw)`**: Maps raw descriptions to 4 standardized categories (SGR, SGP, Recursos propios, Otros)

### 5. Record Assembly & Validation
- **`extract_to_excel(constancia, out_dir, headless, template_path)`**: Orchestrates extraction
  - Builds record dict with 20+ fields (see `record = { ... }` at line ~700)
  - Calls `_estado_validacion()` to set validation status and collect missing field warnings
  - Writes to Excel template's `Resultados_Extraccion` sheet (one row per constancia)
  - Returns output path for UI packaging

- **Validation rules**: Checks presence of critical contract fields; marks status as "Validado", "Advertencia", or "Error"

### 6. Excel Output
- **Template**: `templates/Plantilla_Salida_EXTRACTOR_SECOP_v1.2.10.xlsx`
  - Single sheet: `Resultados_Extraccion`
  - Header row defined in template; script appends data rows
  - Special column `Abrir detalle`: Hyperlink to SECOP detail page (uses base URL from `Config.B1` if present)
- **File naming**: `Resultados_Extraccion_{constancia}_{timestamp}.xlsx`
- **`_find_next_row(ws)`**: Finds first empty row after headers

### 7. Web UI (Flask)
- **`secop_ui.py`**: Single-page Flask app (runs on `http://127.0.0.1:5000`)
- **Routes**:
  - `GET /`: Renders HTML form (detects constancias via browser-side regex)
  - `POST /extract`: Processes batch, calls `secop_extract.extract_to_excel()` per constancia
  - `GET /download/<token>`: Serves final Excel/ZIP with automatic cleanup
- **Batch packaging**:
  - 1 success, 0 errors → serve XLSX directly
  - Multiple/mixed → create ZIP with all successful XLSXs + `reporte_errores.csv`
- **Download security**: Uses random tokens (`secrets.token_urlsafe()`) mapped to file paths

### 8. Offline Validation
- **`validators/validate_offline.py`**: Regression framework (no web calls)
- **Usage**: Place HTML fixtures in `fixtures/detalle/`, define expected field values in `EXPECTED` dict
- **Output**: JSON report with per-fixture status (OK, FAIL, SIN_EXPECTED) saved to `reports/offline/`

## Developer Workflows

### Running the UI
```batch
python secop_ui.py
# Opens browser at http://127.0.0.1:5000
```

### Direct CLI extraction
```python
python secop_extract.py 25-11-14555665
# Or import: secop_extract.extract_to_excel(constancia, Path.home() / "secop_exports")
```

### Adding a new extraction field
1. Add field to template header row (if new column)
2. Extract in `extract_to_excel()` using pattern matching helper (e.g., `_get_first(map, [key_variants])`)
3. Apply cleaning function if needed (`_clean_*()`)
4. Add to `record` dict before validation
5. If critical, add to `FIELDS_UNDER_TEST` in `validate_offline.py`

### Testing extraction accuracy
```bash
# Place test HTML in fixtures/detalle/detalle_PROCESS_NAME.html
# Update EXPECTED dict in validate_offline.py with known values
python validators/validate_offline.py
# Review reports/offline/reporte_validacion_offline_*.json
```

## Project-Specific Patterns

### Constancia Format Standardization
- Stored/transmitted as normalized strings: `YY-XX-NNNN` (always with dashes)
- Regex `CONSTANCIA_RE` in both `secop_extract.py` and `secop_ui.py` (keep in sync!)
- Unicode dash support: `DASHES_RE` converts em-dashes/en-dashes to ASCII `-`

### Environment Configuration
- **Output directory**: `SECOP_OUTPUT_DIR` env var (default: `~/secop_exports`)
- **UI secret key**: `SECOP_UI_SECRET` env var (for session security)
- **Playwright headless mode**: Controlled by function parameters (defaults to `False` for reCAPTCHA manual intervention)

### Error Handling
- **Custom exception**: `SecopExtractionError` with localized Spanish messages
- **UI strategy**: Collects errors per constancia, caps display at 25, includes in CSV inside ZIP
- **Partial success**: If 3/5 extractions fail, still creates ZIP with 2 XLSXs + error report

### Field Mapping Resilience
- **No hardcoded column indices**: All extraction uses label-based matching (`_norm_key()` comparisons)
- **Merge strategy**: `_merge_maps_keep_first()` respects extraction priority (targeted > section KV > baseline KV)
- **Empty value detection**: `_is_nonempty()` filters out "NaN", "None", "null", "-" strings

## Critical External Dependencies
- **openpyxl**: Excel template loading/writing
- **BeautifulSoup4**: HTML parsing (tolerant of malformed markup)
- **Playwright**: Headless browser automation (Chromium-based)
- **Flask**: Web UI framework
- **unicodedata**: Unicode normalization (accents removal)

## Known Limitations & Future Considerations
- **SECOP II support**: Portal refactored in recent years; current scraper targets SECOP I format
- **CRP extraction**: Depends on specific table structure; some legacy processes may use non-standard layouts
- **Rate limiting**: No built-in throttling; SECOP may block rapid sequential requests (implement delay if needed)
- **File cleanup**: Downloaded files remain in `OUTPUT_DIR`; consider scheduled purge for production
