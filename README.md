# IPTV scraper con Playwright

Este repositorio actualiza enlaces `.m3u8` frescos para 5 canales IPTV y reemplaza solo la URL del canal scrapeado dentro de `prueba.m3u`.

## Archivos

- `scraper.py`: orquestador principal del scraping
- `m3u_parser.py`: reemplazo selectivo de URLs en `prueba.m3u`
- `channels_config.py`: configuración de canales objetivo
- `.github/workflows/update-iptv.yml`: ejecución automática cada 2 horas

## Uso local

```bash
pip install -r requirements.txt
python -m playwright install chromium
python scraper.py --m3u-file prueba.m3u
```

## Requisito del M3U

Cada canal debe tener una línea `# ORIGEN:` asociada a su bloque y un `tvg-id` que coincida con la configuración del scraper.

## Automatización

El workflow de GitHub Actions ejecuta el scraper cada 2 horas y hace commit/push automático solo si `prueba.m3u` cambió.