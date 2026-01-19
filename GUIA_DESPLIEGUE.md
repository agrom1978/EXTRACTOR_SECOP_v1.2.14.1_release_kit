# GUÍA DE DESPLIEGUE: secop_ui.py v1.2.15

**Fecha:** 11 de enero de 2026  
**Versión:** 1.2.15  
**Estado:** ✅ Listo para Producción

---

## ✅ PRE-DESPLIEGUE (VERIFICADO)

### Validación Automática
```bash
# Todos los tests pasaron ✓
python test_cambios.py

# Resultado: ✅ TODOS LOS TESTS PASARON
```

### Archivos Listos
- ✅ `constancia_config.py` — Nuevo, compilado, integrado
- ✅ `secop_ui.py` — Refactorizado, compilado, validado
- ✅ `secop_ui_backup.py` — Respaldo disponible
- ✅ `test_cambios.py` — Suite de validación (8 tests)

### Compatibilidad
- ✅ Python 3.7+
- ✅ Flask 1.x / 2.x
- ✅ openpyxl, BeautifulSoup4, Playwright
- ✅ Regresión-compatible (sin cambios a templates Excel)

---

## 🚀 DESPLIEGUE

### Opción 1: Desarrollo Local (RECOMENDADO PARA TESTING)

```bash
# 1. Ubicarse en directorio del proyecto
cd "C:\Users\USUARIO\OneDrive\Escritorio\EXTRACTOR_SECOP_v1.2.15_release_kit"

# 2. Configurar variable de entorno (seguridad)
set SECOP_UI_SECRET=tu-clave-super-segura-aqui

# 3. Iniciar servidor
python secop_ui.py

# 4. Abrir en navegador
# http://127.0.0.1:5000

# 5. Verificar logs en consola
# [timestamp] - secop_ui - INFO - Iniciando SECOP UI...
# [timestamp] - secop_ui - INFO - Iniciando extracción de X constancia(s)
```

### Opción 2: Producción (Gunicorn + Nginx)

```bash
# 1. Instalar servidor WSGI
pip install gunicorn

# 2. Crear archivo .env en proyecto
cat > .env << EOF
SECOP_UI_SECRET=clave-segura-generada-aleatoriamente
SECOP_OUTPUT_DIR=/var/secop/exports
EOF

# 3. Cargar variables
source .env

# 4. Iniciar con Gunicorn (4 workers)
gunicorn --workers 4 --bind 127.0.0.1:5000 secop_ui:APP

# 5. Configurar Nginx (proxy reverso)
# Ver seccion Nginx más abajo
```

### Opción 3: Docker (Containerizado)

```bash
# 1. Crear Dockerfile en proyecto
cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY secop_extract.py secop_ui.py constancia_config.py ./
COPY templates ./templates

ENV SECOP_UI_SECRET=${SECOP_UI_SECRET}
ENV SECOP_OUTPUT_DIR=/app/exports

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "secop_ui:APP"]
EOF

# 2. Crear requirements.txt
cat > requirements.txt << EOF
Flask==2.3.0
openpyxl==3.10.0
beautifulsoup4==4.12.0
playwright==1.40.0
gunicorn==21.0.0
EOF

# 3. Construir imagen
docker build -t secop-ui:1.2.15 .

# 4. Ejecutar contenedor
docker run -d \
  --name secop-ui \
  -p 5000:5000 \
  -e SECOP_UI_SECRET="clave-segura" \
  -v /var/secop/exports:/app/exports \
  secop-ui:1.2.15
```

---

## 📋 CHECKLIST DE DESPLIEGUE

### Antes de Iniciar
- [ ] Revisar `RESUMEN_EJECUTIVO_IMPLEMENTACION.md`
- [ ] Ejecutar `python test_cambios.py` (debe pasar todos)
- [ ] Verificar `secop_ui_backup.py` existe (rollback)
- [ ] Instalar dependencias: `pip install -r requirements.txt`

### Configuración
- [ ] Configurar `SECOP_UI_SECRET` (variable de entorno)
- [ ] Crear directorio `SECOP_OUTPUT_DIR` si no existe
- [ ] Permisos de escritura en directorio de salida
- [ ] Puerto 5000 disponible (o cambiar en APP.run())

### Testing Local
- [ ] Iniciar servidor: `python secop_ui.py`
- [ ] Abrir `http://127.0.0.1:5000` en navegador
- [ ] Probar con constancia válida: `25-1-241304`
- [ ] Verificar:
  - [ ] Detección funciona ("Detectadas: 1")
  - [ ] Extracción funciona (se abre navegador)
  - [ ] ZIP/XLSX generado correctamente
  - [ ] Descarga funciona
  - [ ] Logs aparecen en consola

### Monitoreo
- [ ] Revisar logs en consola (timestamps + niveles)
- [ ] Verificar limpieza de archivos (1 hora)
- [ ] Supervisar uso de memoria (_DOWNLOADS crecimiento controlado)
- [ ] Alert si extracción > 2 minutos

---

## 🔧 CONFIGURACIÓN NGINX (Producción)

```nginx
# /etc/nginx/sites-available/secop-ui
upstream secop_ui {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name tu-dominio.com;
    
    # Límite de upload (archivos grandes)
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://secop_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout para procesamiento de constancias
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Ruta para archivos descargados (opcional)
    location /exports/ {
        alias /var/secop/exports/;
        expires 1h;
    }
}
```

Activar:
```bash
sudo ln -s /etc/nginx/sites-available/secop-ui /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔄 ROLLBACK (Si es Necesario)

### Opción 1: Archivo Backup
```bash
cd "c:\Users\USUARIO\OneDrive\Escritorio\EXTRACTOR_SECOP_v1.2.15_release_kit"

# Revertir a versión anterior
copy secop_ui_backup.py secop_ui.py
```

### Opción 2: Git
```bash
git checkout HEAD~1 -- secop_ui.py
git checkout HEAD~1 -- constancia_config.py

# O eliminar completamente los cambios
git reset --hard HEAD~1
```

### Opción 3: Manual
1. Eliminar `secop_ui.py` y `constancia_config.py`
2. Restaurar desde `secop_ui_backup.py`
3. Reiniciar servicio

---

## 📊 MONITOREO RECOMENDADO

### Logs a Verificar
```bash
# Inicialización
"Iniciando SECOP UI en http://127.0.0.1:5000"

# Procesamiento normal
"[i/total] Extrayendo constancia: XX-XX-XXXXXX"
"[i/total] ✓ Éxito: XX-XX-XXXXXX"

# Advertencias
"⚠️ Variable SECOP_UI_SECRET no configurada"
"No se detectaron constancias válidas"

# Errores
"[i/total] ✗ Error extrayendo XX-XX-XXXXXX: ..."
"Error descargando C:\...\archivo.xlsx: ..."
```

### Métricas a Monitorear
- Tiempo de extracción por constancia (ideal: < 30s)
- Tamaño de `_DOWNLOADS` dict (debe decrecer cada hora)
- Uso de memoria (especialmente si procesa muchas)
- Errores de reCAPTCHA (manual intervention needed)

### Alertas Recomendadas
```
IF tiempo_extraccion > 120s THEN enviar_notificacion("Timeout probable")
IF _DOWNLOADS.size() > 100 THEN revisar_limpieza()
IF errores_secuenciales > 5 THEN revisar_acceso_SECOP()
```

---

## 🆘 TROUBLESHOOTING

### Problema: "ModuleNotFoundError: No module named 'constancia_config'"
**Solución:**
```bash
# Verificar que constancia_config.py está en el directorio correcto
ls constancia_config.py

# O importar manualmente
python -c "import constancia_config; print('OK')"
```

### Problema: "Variable SECOP_UI_SECRET no configurada"
**Solución:**
```bash
# Windows CMD
set SECOP_UI_SECRET=mi-clave-segura

# Windows PowerShell
$env:SECOP_UI_SECRET="mi-clave-segura"

# Linux/Mac
export SECOP_UI_SECRET="mi-clave-segura"
```

### Problema: "Address already in use: port 5000"
**Solución:**
```bash
# Cambiar puerto en secop_ui.py línea 500:
# APP.run(host="127.0.0.1", port=5001, debug=False)

# O matar proceso en puerto 5000
# Windows: taskkill /f /im python.exe
# Linux: sudo lsof -ti:5000 | xargs kill -9
```

### Problema: Archivos no se limpian después de 1 hora
**Revisión:**
```python
# Verificar en secop_ui.py:
MAX_DOWNLOAD_AGE_SECONDS = 3600  # ← Debe ser 3600 (1 hora)

# La limpieza se ejecuta en GET /download/<token>
# Si no hay descargas, no se ejecuta limpiezapor. Es normal.
```

### Problema: JavaScript no detecta constancias correctamente
**Verificación:**
```javascript
// En consola del navegador
const CONSTANCIA_RE = /\b(\d{2}-\d{1,2}-\d{4,12})\b/g;
"25-1-241304".match(CONSTANCIA_RE);  // Debe retornar ["25-1-241304"]

// Verificar normalización
function normalizeText(s){/*...*/}
normalizeText("25–1–241304");  // Debe convertir en-dash a hyphen
```

---

## 📚 DOCUMENTACIÓN RELACIONADA

- [README.md](README.md) — Instrucciones generales
- [CAMBIOS_IMPLEMENTADOS_secop_ui.md](CAMBIOS_IMPLEMENTADOS_secop_ui.md) — Detalles técnicos
- [RESUMEN_EJECUTIVO_IMPLEMENTACION.md](RESUMEN_EJECUTIVO_IMPLEMENTACION.md) — Resumen ejecutivo
- [REVISION_CODIGO_secop_ui.md](REVISION_CODIGO_secop_ui.md) — Análisis de problemas

---

## 🎓 PRÓXIMOS PASOS DESPUÉS DEL DESPLIEGUE

1. **Integración continua**
   - Ejecutar `test_cambios.py` en cada commit
   - Validar sintaxis con `pylint`

2. **Actualización de `secop_extract.py`**
   - Importar de `constancia_config.py`
   - Usar funciones compartidas

3. **Testing más amplio**
   - Pruebas con 50+ constancias
   - Manejo de reCAPTCHA extenso
   - Prueba de fallos de red

4. **Documentación de usuario**
   - Guía de uso de UI
   - Ejemplos de formatos de entrada
   - FAQ de problemas comunes

---

## ✅ ESTADO FINAL

```
✓ Código validado (8/8 tests)
✓ Sintaxis verificada (sin warnings)
✓ Integración completa (constancia_config ↔ secop_ui)
✓ Seguridad mejorada (logging, sanitización, cleanup)
✓ Documentación completa
✓ Rollback disponible

LISTO PARA DESPLIEGUE EN PRODUCCIÓN
```

---

**Soporte:** Revisar archivos de documentación o ejecutar `test_cambios.py` para validar instalación.
