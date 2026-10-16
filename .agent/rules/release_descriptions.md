# Regla Obligatoria: Descripciones Detalladas en Releases (Changelog Obligatorio)

Siempre que se prepare, configure o publique una nueva versión (Release) o etiqueta Git (`vX.Y.Z`) en el proyecto Miku Desktop, es **ESTRICTAMENTE OBLIGATORIO** redactar una descripción completa y estructurada del lanzamiento (Release Notes / Changelog).

---

### Motivo Crítico
El sistema de **Actualizador Automático en 1 Clic** integrado en la aplicación (Tauri Updater) consulta las GitHub Releases y extrae directamente el campo `body` (descripción del release) para mostrárselo al usuario en la ventana de Ajustes antes de presionar "Instalar".
Si una release no tiene descripción o usa frases vacías como *"Descarga la última versión"*, el usuario no sabrá qué cambios, mejoras o correcciones contiene.

---

### Estructura Obligatoria de la Descripción de Release

Toda release DEBE estructurarse con las siguientes secciones:

```markdown
## 🚀 Novedades Principales
- Descripción clara y orientada al usuario de las nuevas funcionalidades añadidas.

## 🛠️ Mejoras y Optimización
- Mejoras de rendimiento, reducción de consumo de recursos, interfaz gráfica, UX y sincronización.

## 🐛 Correcciones de Errores (Fixes)
- Errores solucionados, estabilidad de sockets, variables de entorno, cierres inesperados o bugs visuales.

---
**Instalación:** Descarga y ejecuta `Miku_Setup.exe` o utiliza el actualizador integrado desde Ajustes → General.
```

---

### Procedimiento de Release
1. **Actualizar versiones en el código**:
   - `miku_ui/src-tauri/Cargo.toml` (`version = "X.Y.Z"`)
   - `miku_ui/src-tauri/tauri.conf.json` (`"version": "X.Y.Z"`)
   - `miku_ui/package.json` (`"version": "X.Y.Z"`)
   - `miku_ui/src/miku_settings.html` y `bridge.js` (textos e indicadores de versión `vX.Y.Z`)
   - `README.md` y `README.es.md` (badges e información de versión)
2. **Generar la descripción del release** siguiendo la plantilla obligatoria.
3. **Flujo de GitHub Actions**:
   - Si se usa `workflow_dispatch`, pasar la descripción en el parámetro `releaseNotes`.
   - Si se dispara por Tag Git, el workflow debe incluir un changelog generado o tomar el archivo de notas de release.
4. **Validación**:
   - Verificar que no queden textos con versiones anteriores desfasadas en la interfaz gráfica.
