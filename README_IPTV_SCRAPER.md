# 🎯 IPTV Auto-Scraper: Solución Completa

Tu solicitud ya está **implementada y lista para usar**. Este repositorio ahora tiene un sistema completo de automatización para mantener actualizados los enlaces IPTV con tokens frescos.

---

## 📦 ¿Qué se ha creado?

### 1. **Script Python** (`scripts/iptv_scraper.py`)
- ✅ Scraping inteligente usando **Playwright**
- ✅ Actualización **selectiva y quirúrgica** por canal
- ✅ Parseo automático del archivo .m3u
- ✅ Commit y push automático a GitHub
- ✅ Logging detallado

### 2. **Script Node.js** (`scripts/iptv_scraper_nodejs.js`)
- ✅ Alternativa en JavaScript
- ✅ Misma funcionalidad que Python
- ✅ Ideal si prefieres Node.js

### 3. **GitHub Actions Workflow** (`.github/workflows/iptv-auto-update.yml`)
- ✅ Ejecución automática cada 6 horas
- ✅ Ejecución manual bajo demanda desde Actions
- ✅ Selección flexible de canales
- ✅ Commit y push automático

### 4. **Documentación Completa** (`IPTV_SCRAPER_GUIDE.md`)
- ✅ Guía de instalación
- ✅ Ejemplos de uso
- ✅ Troubleshooting
- ✅ Explicación del flujo

---

## 🚀 Inicio Rápido

### Opción A: Ejecutar desde GitHub Actions (Recomendado)

1. Ve a **GitHub → Actions → "🔄 IPTV Auto-Update"**
2. Haz clic en **"Run workflow"**
3. Ingresa qué canales actualizar:
   - Dejar vacío → actualiza todos
   - Ej: `Telefuturo.py@SD,Trece.py@SD` → solo esos dos
4. Espera a que termine el workflow

**¡Listo!** Los cambios se pushearán automáticamente si hay algo nuevo.

### Opción B: Ejecutar Localmente (Python)

```bash
# 1. Instalar dependencias
pip install -r scripts/requirements.txt
playwright install chromium

# 2. Listar canales disponibles
python scripts/iptv_scraper.py prueba01.m3u --list

# 3. Actualizar canales
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD Trece.py@SD

# 4. O actualizar todos
python scripts/iptv_scraper.py prueba01.m3u --update-all
```

### Opción C: Ejecutar Localmente (Node.js)

```bash
# 1. Instalar dependencias
cd scripts
npm install
npx playwright install chromium

# 2. Listar canales
node iptv_scraper_nodejs.js ../prueba01.m3u --list

# 3. Actualizar
node iptv_scraper_nodejs.js ../prueba01.m3u --update Telefuturo.py@SD
```

---

## 🎯 Características Principales

### ✅ Actualización Selectiva (Tu Requisito Crítico)

El script realiza una actualización **quirúrgica**:

```
❌ MAL:  Sobrescribir todo el archivo (pierdes canales)
✅ BIEN: Buscar canal específico → reemplazar solo su URL

Resultado: ABC-TV y NPY se mantienen, solo se actualiza ABC-TV
```

### ✅ Scraping Inteligente

- Usa **Playwright** (navegador real, no simple HTTP)
- Simula navegador para burlar protecciones
- Busca .m3u8 en múltiples lugares:
  - Etiquetas `<source>` y `<video>`
  - Scripts JavaScript
  - Atributos `data-*`
- Obtiene token **fresco** cada vez

### ✅ Automatización GitHub Actions

- ⏰ Cronograma automático (cada 6 horas)
- 🎯 Ejecución manual desde Actions
- 📝 Commit automático con descripción
- 🚀 Push automático a main

---

## 📋 Formato Requerido en .m3u

Tu archivo **ya tiene el formato correcto**:

```m3u
# ORIGEN: https://www.telefuturo.com.py/envivo
#EXTINF:-1 tvg-id="Telefuturo.py@SD" tvg-logo="..." group-title="NACIONALES.PY",Telefuturo
https://rds3tf.desdeparaguay.net/telefuturo/...
```

**Elementos obligatorios:**
1. `# ORIGEN: <URL>` → dónde scraping obtiene el enlace fresco
2. `tvg-id="<IDENTIFICADOR>"` → para identificar el canal
3. Última línea → URL actual (será reemplazada)

---

## 🔄 Flujo Completo de Automatización

```
1. GitHub Actions se ejecuta (automático cada 6h o manual)
   ↓
2. Script Python/Node descarga y actualiza dependencias
   ↓
3. Playwright abre navegador y scraping las páginas origen
   ↓
4. Obtiene URLs .m3u8 con tokens FRESCOS
   ↓
5. Lee prueba01.m3u y parsea canales
   ↓
6. Reemplaza SOLO el enlace del canal especificado
   ↓
7. Guarda archivo .m3u actualizado
   ↓
8. Git commit con mensaje descriptivo
   ↓
9. Git push a main (cambios quedan en repo)
   ↓
10. ✅ COMPLETO - Enlaces actualizados y pusheados
```

---

## 💡 Ejemplos de Uso

### Actualizar un canal
```bash
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD
```

### Actualizar múltiples canales
```bash
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD Trece.py@SD ESPN.py@SD
```

### Actualizar todos
```bash
python scripts/iptv_scraper.py prueba01.m3u --update-all
```

### Sin push automático (solo actualizar archivo)
```bash
python scripts/iptv_scraper.py prueba01.m3u --update-all --no-push
```

### Listar canales disponibles
```bash
python scripts/iptv_scraper.py prueba01.m3u --list
```

---

## ⚙️ Configuración

### Cambiar frecuencia de actualización automática

Edita `.github/workflows/iptv-auto-update.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Cada 6 horas
  # Cambiar a:
  # - cron: '0 0 * * *'   # Diariamente a las 00:00
  # - cron: '0 */3 * * *' # Cada 3 horas
  # - cron: '*/30 * * * *' # Cada 30 minutos
```

[Referencia de cron en GitHub Actions](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

### Timeout de scraping

En `scripts/iptv_scraper.py` (línea ~150):
```python
await page.goto(origin_url, timeout=15000, wait_until='networkidle')
# Aumentar timeout si las páginas son lentas
```

---

## 📊 Monitoreo

### Ver logs de ejecución en GitHub Actions

1. Ve a **Actions** en tu repo
2. Selecciona **"🔄 IPTV Auto-Update"**
3. Haz clic en el último workflow ejecutado
4. Expande los pasos para ver logs detallados

**Logs muestran:**
- ✅/❌ Canales actualizados
- 🔍 URLs encontradas
- 📝 Commit y push realizados
- ⚠️ Warnings o errores

---

## 🐛 Troubleshooting

### ❌ "Canal XXX no encontrado"
```bash
# Verifica con:
python scripts/iptv_scraper.py prueba01.m3u --list
```

### ❌ "No se encontró .m3u8"
- La página está bloqueada
- El sitio cambió su HTML
- Necesita más tiempo para cargar
- → Aumenta timeout en el script

### ❌ "Error en git push"
- Verifica permisos del repositorio
- Token de GitHub Actions está activo

---

## 📚 Documentación Completa

Para detalles completos, ve a: **`IPTV_SCRAPER_GUIDE.md`**

Contiene:
- Instalación paso a paso
- Ejemplos de cada comando
- Explicación del flujo
- Casos de uso
- FAQ

---

## ✨ Casos de Uso

✅ **Tu situación**: Tokens dinámicos que expiran  
✅ **Actualizar solo algunos canales**: Especifica cuáles  
✅ **Automatización 24/7**: GitHub Actions corre sin intervención  
✅ **Múltiples repos**: Copia el script a otros repos  
✅ **Personalización**: Modifica frecuencia, canales, etc.  

---

## 🎯 Resumen de Solución

| Requisito | Solución |
|-----------|----------|
| Scraping de tokens frescos | ✅ Playwright (navegador real) |
| Actualización selectiva | ✅ Búsqueda por tvg-id, reemplazo quirúrgico |
| No sobrescribir resto | ✅ Patrón exacto, sin tocar otras líneas |
| Automatización GitHub | ✅ GitHub Actions cada 6h o manual |
| Commit y push automático | ✅ Git commands en workflow |
| Fácil de usar | ✅ Comandos simples, interfaz clara |
| Documentado | ✅ Guía completa incluida |

---

## 🚀 Próximos Pasos

1. **Ahora mismo**: Haz tu primer test manualmente
   ```bash
   python scripts/iptv_scraper.py prueba01.m3u --list
   ```

2. **Prueba con un canal**:
   ```bash
   python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD
   ```

3. **O usa GitHub Actions**:
   - Ve a Actions
   - Ejecuta workflow manualmente
   - Observa los logs

4. **Configura automático**:
   - Ya está listo (cada 6 horas)
   - Puedes cambiar la frecuencia si quieres

---

## 📞 Soporte

Si encuentras algún problema:
1. Revisa los logs en GitHub Actions
2. Consulta `IPTV_SCRAPER_GUIDE.md` sección Troubleshooting
3. Verifica que el formato del .m3u sea correcto

---

**¡Tu sistema IPTV automático está listo! 🎉**

El código está en `feature/iptv-auto-scraper` y listo para PR/merge a main.
