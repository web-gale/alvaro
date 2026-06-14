# 📺 Guía: IPTV Auto-Scraper & Updater

## ¿Qué es?

Un sistema completo de **automatización inteligente** para mantener actualizados los enlaces IPTV (.m3u) en tu repositorio GitHub. El script:

✅ **Scraping selectivo**: Entra a las páginas origen, obtiene el enlace .m3u8 con token fresco  
✅ **Actualización quirúrgica**: Reemplaza SOLO el canal especificado, sin tocar el resto  
✅ **Automatización GitHub Actions**: Ejecuta en cronograma automático o manualmente  
✅ **Versionado git**: Realiza commits y pushes automáticos con cambios  

---

## 🚀 Uso

### 1️⃣ Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/galeano200718-hub/alvaro.git
cd alvaro

# Instalar dependencias
pip install -r scripts/requirements.txt

# Descargar navegador Chromium para Playwright
playwright install chromium
```

### 2️⃣ Listar Canales Disponibles

```bash
python scripts/iptv_scraper.py prueba01.m3u --list
```

**Salida:**
```
📺 CANALES DISPONIBLES:
  • Telefuturo (Telefuturo.py@SD)
    Origen: https://www.telefuturo.com.py/envivo
    URL actual: https://rds3tf.desdeparaguay.net/...
  
  • Trece (Trece.py@SD)
    Origen: https://trece.com.py/en-vivo/
    URL actual: https://dmxleo.dailymotion.com/...
```

### 3️⃣ Actualizar Canales Específicos

```bash
# Actualizar un canal
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD

# Actualizar múltiples canales
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD Trece.py@SD ESPN.py@SD

# Actualizar todos los canales
python scripts/iptv_scraper.py prueba01.m3u --update-all

# Sin hacer push automático (solo actualizar archivo localmente)
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD --no-push
```

---

## ⚙️ Automatización con GitHub Actions

El workflow `.github/workflows/iptv-auto-update.yml` ya está configurado para:

### Opción A: Actualización Automática (Cronograma)

Se ejecuta **automáticamente cada 6 horas**:
- Hora: 00:00, 06:00, 12:00, 18:00 (UTC)
- Actualiza todos los canales
- Si hay cambios, hace commit y push automático

### Opción B: Ejecución Manual

1. Ve a **GitHub → Actions → "🔄 IPTV Auto-Update"**
2. Haz clic en **"Run workflow"**
3. Ingresa qué canales actualizar (opcional):
   - Dejar vacío o escribir `all` → actualiza todos
   - Ejemplo: `Telefuturo.py@SD,Trece.py@SD` → actualiza esos 2

---

## 📋 Formato del Archivo .m3u

El script espera este formato (es lo que ya tienes):

```m3u
# ORIGEN: https://www.telefuturo.com.py/envivo
#EXTINF:-1 tvg-id="Telefuturo.py@SD" tvg-logo="..." group-title="NACIONALES.PY",Telefuturo
https://rds3tf.desdeparaguay.net/telefuturo/...?token=abc123...

# ORIGEN: https://trece.com.py/en-vivo/
#EXTINF:-1 tvg-id="Trece.py@SD" tvg-logo="..." group-title="NACIONALES.PY",Trece
https://dmxleo.dailymotion.com/cdn/manifest/...
```

**Elementos críticos:**
- `# ORIGEN: <URL>` → la página web donde el script hace scraping
- `tvg-id="<ID>"` → identificador único del canal (usado en comandos)
- Última línea → URL del stream (será reemplazada por la nueva)

---

## 🔍 Cómo Funciona

### Flujo completo:

```
┌─────────────────────────────────────────────┐
│ 1. Script inicia (manual o cronograma)       │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ 2. Lee prueba01.m3u, parsea canales         │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ 3. Para cada canal especificado:            │
│   - Abre navegador (Playwright)             │
│   - Carga URL origen                        │
│   - Busca .m3u8 en la página                │
│   - Obtiene URL con token fresco            │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ 4. Actualización selectiva:                 │
│   - Busca exactamente el bloque del canal   │
│   - Reemplaza SOLO la URL                   │
│   - El resto del archivo no se toca         │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ 5. Guarda archivo .m3u modificado           │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ 6. Git commit + push a main                 │
│   Mensaje: "🔄 Auto-update IPTV: [canales]"│
└─────────────────────────────────────────────┘
```

---

## ⚡ Ejemplos de Uso

### Ejemplo 1: Actualizar Telefuturo manualmente

```bash
python scripts/iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD
```

**Resultado:**
```
✅ Canal parseado: Telefuturo (Telefuturo.py@SD)
🔍 Scrapiendo Telefuturo.py@SD desde: https://www.telefuturo.com.py/envivo
✅ URL .m3u8 encontrada para Telefuturo.py@SD
✅ Telefuturo.py@SD: https://rds3tf.desdeparaguay.net/...?token=abc → https://rds3tf.desdeparaguay.net/...?token=xyz123
💾 Archivo prueba01.m3u guardado
✅ Commit realizado: 🔄 Auto-update IPTV: Telefuturo
✅ Push a GitHub completado
```

### Ejemplo 2: Actualizar todos los canales

```bash
python scripts/iptv_scraper.py prueba01.m3u --update-all
```

---

## 🛠️ Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'playwright'"

```bash
pip install -r scripts/requirements.txt
playwright install chromium
```

### ❌ "Canal XXX no encontrado"

Verifica que el `tvg-id` existe:
```bash
python scripts/iptv_scraper.py prueba01.m3u --list
```

### ❌ "No se encontró .m3u8 en XXX"

El scraping no pudo encontrar la URL en la página. Posibles causas:
- La página está protegida/bloqueada
- El sitio cambió su estructura HTML
- Necesita más tiempo de carga (aumentar timeout en script)

### ❌ "Error en 'git push'"

En GitHub Actions, verifica:
- Token de autenticación configurado
- Permisos del repositorio

---

## 🎯 Casos de Uso

✅ **Uso personal**: Mantén tu lista IPTV siempre actualizada sin intervención  
✅ **Múltiples repos**: Copia el script a otros repositorios con listas IPTV  
✅ **Selectivo**: Actualiza solo los canales que fallan, no todos  
✅ **Scheduled**: Ejecuta cada X horas automáticamente  
✅ **Manual**: Ejecuta bajo demanda desde Actions  

---

## 📝 Notas Importantes

⚠️ **Tokens dinámicos**: El script obtiene tokens **frescos cada vez**, así que los enlaces siempre estarán actualizados  
⚠️ **Selectividad**: La actualización es quirúrgica — solo se toca el canal especificado  
⚠️ **Seguridad**: Los credentials de GitHub se manejan automáticamente en Actions (GITHUB_TOKEN)  
⚠️ **Logs**: Revisa los logs en GitHub Actions para ver exactamente qué pasó  

---

## 🚀 Próximos Pasos

1. **Personaliza el cronograma**: Edita `.github/workflows/iptv-auto-update.yml` si quieres otra frecuencia
2. **Agrega más canales**: Sigue el formato `# ORIGEN:` + `#EXTINF:` + URL
3. **Monitorea**: Ve a Actions y revisa los logs de ejecución

¡Listo! Tu IPTV ahora se actualiza automáticamente. 🎉

