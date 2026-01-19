# 🎯 Guía de Pruebas - Mejoras UI v1.2.15

**Fecha de implementación:** 11 de enero de 2025  
**Estado:** ✅ Completado y sincronizado con GitHub

---

## 🚀 Inicio Rápido

### 1. **Ejecutar la aplicación**
```bash
python secop_ui.py
```

Salida esperada:
```
 * Serving Flask app 'secop_ui'
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### 2. **Abrir en navegador**
```
http://127.0.0.1:5000
```

---

## ✨ Características a Probar

### 🎨 **1. Tema Visual Moderno**

**Verificación:**
- ✅ Font moderna "Inter" (sin Arial genérico)
- ✅ Colores profesionales (azules, verdes, naranjas)
- ✅ Sombras suaves en tarjetas
- ✅ Espaciado consistente (padding/margin)

**Evidencia:**
- Logo flotante 📊 (se mueve sutilmente arriba/abajo)
- Gradiente azul en botón "Extraer"
- Header con tagline "Automatización de procesos"
- Version badge con fondo gradiente

---

### 🌙 **2. Dark Mode Automático**

**Activar dark mode en Windows:**
```
Configuración → Personalización → Colores → Modo oscuro
```

**Activar dark mode en macOS:**
```
System Preferences → General → Appearance → Dark
```

**Activar dark mode en Linux:**
```
Asistente de configuración GTK o KDE → Tema oscuro
```

**Verificación:**
- ✅ Fondo cambia de blanco (#fff) a gris oscuro (#111827)
- ✅ Texto cambia de negro (#111) a blanco (#f3f4f6)
- ✅ Bordes se ajustan automáticamente
- ✅ Las sombras se oscurecen para visibilidad
- ✅ SIN necesidad de recarga (cambia en tiempo real)

---

### 🎬 **3. Animaciones**

**Logo flotante:**
- Mira el emoji 📊 en el header superior izquierdo
- Se mueve arriba/abajo continuamente (3 segundos por ciclo)

**Entrada de badges:**
- Ingresa texto con constancia válida (ej: `25-11-14555665`)
- El badge azul "📋 X constancias detectadas" aparece con animación suave

**Botón "Extraer":**
- Pasa el mouse sobre el botón azul
- Se eleva 2px (transform: translateY(-2px))
- Sombra se hace más profunda
- Click: se hunde de nuevo (transform: translateY(0))

**Spinner de carga:**
- Click en "Extraer"
- El ícono del botón ⚡ cambia a un spinner (círculo que rota)
- Gira continuamente hasta que termina el procesamiento

---

### 📱 **4. Diseño Responsive**

**Pruebas en Desktop (navegadores):**

**Chrome:**
```
Ctrl+Shift+I → Toggle device toolbar (Ctrl+Shift+M)
```

**Firefox:**
```
Ctrl+Shift+M
```

**Safari:**
```
Cmd+Option+U → Responsive Design Mode
```

**Tamaños a probar:**
| Ancho | Tipo | Esperado |
|-------|------|----------|
| 1920px | Desktop | Layout de 800px centralizado |
| 1024px | Tablet | Todo visible, 2 columnas |
| 768px | Tablet Small | Ajustes automáticos |
| 640px | Mobile | Breakpoint: botones 100% ancho |
| 375px | Mobile Small | Stack vertical completo |

**Cambios automáticos en mobile:**
- Botones ocupan ancho completo (100%)
- Header se apila verticalmente
- Badge de versión 100% ancho
- Formulario ocupa pantalla completa
- Instrucciones se redimensionan

---

### 🔘 **5. Botones Mejorados**

**Botón "Extraer":**
- ✅ Gradiente azul (no color sólido)
- ✅ Sombra de 4px (0 4px 15px)
- ✅ Hover: eleva 2px
- ✅ Hover: sombra más profunda (8px)
- ✅ Click: vuelve a su posición

**Botón "Limpiar":**
- ✅ Fondo gris claro
- ✅ Hover: cambia a borde azul (primario) con fondo transparente
- ✅ Transición suave (0.2s)

**Disabled:**
- ✅ Opacidad 50% cuando está deshabilitado
- ✅ Cursor cambia a "not-allowed"

---

### 📊 **6. Barra de Progreso**

**Activación:**
- Click en "Extraer"
- Aparece barra gris con relleno azul

**Comportamiento:**
- ✅ Relleno tiene gradiente azul
- ✅ Glow effect (box-shadow: 0 0 10px)
- ✅ Progresa hasta 90% (naturalmente)
- ✅ Texto debajo: "Iniciando extracción..."
- ✅ Se anima suavemente (transition: width 0.3s)

---

### ⚡ **7. Spinner de Carga**

**Activación:**
- Click en "Extraer" → ícono ⚡ cambia a spinner

**Características:**
- ✅ Círculo blanco que rota continuamente
- ✅ Borde 2px semitransparente
- ✅ Top border (opacity 1) para indicar rotación
- ✅ Animación 0.8s (rápida y fluida)

---

### 🎯 **8. Sistema de Badges**

**Info Badge (Azul):**
```
📋 5 constancias detectadas
```
- Fondo azul translúcido
- Icono y número
- Animación slideIn

**Success Badge (Verde):**
```
✓ 5 extracciones correctas
```
- Aparece en panel de resultados
- Fondo verde translúcido

**Warning Badge (Naranja):**
```
✗ 2 errores encontrados
```
- Fondo naranja translúcido
- Para alertas de validación

---

### 📋 **9. Tabla de Errores**

**Activación:**
- Extraer constancias con errores
- Se muestra panel de resultados con sección "Errores"

**Características:**
- ✅ Altura máxima 400px (scroll si hay muchos)
- ✅ Cada error tiene:
  - Borde izquierdo rojo
  - Fondo rojo translúcido
  - Monospace font para código
  - 10px padding interno
- ✅ Hover: color de fondo se oscurece
- ✅ Animación slideIn al aparecer
- ✅ Mensaje contextual si hay más errores

**Ejemplo:**
```
25-11-14555665 — Conexión expirada
25-15-14581710 — HTML no contiene tabla CRP
```

---

### 🏠 **10. Header con Logo**

**Elementos:**
- 📊 Logo animado (flotante)
- **Extractor SECOP** (título gradiente azul)
- *Automatización de procesos de contratación* (tagline)
- **v1.2.15** (version badge con gradiente)

**Responsividad:**
- Desktop: Horizontal (logo + titulo + version en fila)
- Mobile: Vertical (cada elemento en su línea)

---

## 🧪 Prueba Completa (End-to-End)

### Escenario 1: Extracción Exitosa
```
1. Abre http://127.0.0.1:5000
2. Ingresa: 25-11-14555665
3. Click en "Extraer"
4. Observa:
   ✓ Badge azul "📋 1 constancia detectada"
   ✓ Spinner en botón
   ✓ Barra de progreso animada
   ✓ Panel de estado verde "Finalizado con éxito"
   ✓ Link de descarga operacional
5. Descarga y abre Excel
```

### Escenario 2: Dark Mode
```
1. Abre la app en navegador
2. Abre DevTools (F12)
3. Menú ☰ → More tools → Rendering
4. Scroll → Emulate CSS media feature prefers-color-scheme
5. Selecciona "dark"
6. Observa:
   ✓ Fondo se vuelve gris oscuro
   ✓ Texto se vuelve blanco
   ✓ Todos los colores se invierten
   ✓ Sombras se ajustan
```

### Escenario 3: Mobile
```
1. Abre DevTools → Toggle device toolbar
2. Selecciona dispositivo (iPhone 12, etc.)
3. Observa:
   ✓ Header se apila verticalmente
   ✓ Botones ocupan 100% ancho
   ✓ Textarea se redimensiona
   ✓ Todo es scrolleable y legible
   ✓ Interacciones funcionan (tap en botones)
```

---

## 📸 Puntos de Captura (Screenshots)

Recomendadas para documentación:

1. **Desktop Light Mode - Completo**
2. **Desktop Dark Mode - Completo**
3. **Mobile Landscape**
4. **Mobile Portrait**
5. **Panel de Resultados - Éxito**
6. **Panel de Resultados - Errores**
7. **Detección Constancias - Badge activo**
8. **Procesamiento - Spinner y progreso**

---

## ⚙️ Verificación Técnica

### Consola del Navegador (F12)
- ✅ Sin errores JavaScript
- ✅ Sin advertencias CSS
- ✅ Red: Google Fonts carga correctamente
- ✅ Network: Sin 404s o timeouts

### Validación HTML/CSS
```bash
# CSS Valid
# - Variables CSS soportadas (browserslist: última 2 versiones)
# - Grid y Flexbox compatible
```

### Performance
```bash
# Lighthouse (Chrome DevTools → Lighthouse)
- Performance: >90
- Accessibility: >90
- Best Practices: >90
- SEO: >90
```

---

## 🐛 Troubleshooting

### **Problema:** Dark mode no activa
**Solución:**
- Verifica que tu SO tenga dark mode habilitado
- Prueba: DevTools → Rendering → prefers-color-scheme: dark

### **Problema:** Animaciones lentas
**Solución:**
- Verifica: DevTools → Rendering → Paint timing
- Prueba en otro navegador (Chrome, Firefox, Safari)

### **Problema:** Responsive no funciona
**Solución:**
- Recarga la página (Ctrl+Shift+R para limpiar caché)
- Verifica viewport meta tag en HTML
- Prueba con zoom al 100% (Ctrl+0)

### **Problema:** Fonts no carga
**Solución:**
- Verifica conexión a internet
- Abre DevTools → Network → busca "googleapis.com"
- Si fallida: fallback a sistema (Arial)

---

## 📊 Checklist de Validación

```
✓ Tema moderno visible
✓ Dark mode responde a preferencias SO
✓ Animaciones suaves (sin lag)
✓ Responsive en 375px, 640px, 768px, 1024px, 1920px
✓ Botones interactivos con feedback visual
✓ Barra progreso funcional
✓ Spinner rotando correctamente
✓ Badges animan al aparecer
✓ Tabla errores scrolleable
✓ Header con logo y versión
✓ Sin errores JavaScript
✓ Sin advertencias CSS
✓ Fonts Google cargan correctamente
✓ Colores accesibles (WCAG AA)
```

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa la consola del navegador (F12)
2. Verifica que Python y Flask están en PATH
3. Prueba en otro navegador
4. Intenta en modo incógnito (Ctrl+Shift+N)
5. Limpia caché: Ctrl+Shift+Delete

---

**Versión:** 1.2.15  
**Fecha:** 11 de enero de 2025  
**Estado:** ✅ Listo para producción
