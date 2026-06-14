#!/usr/bin/env python3
"""
IPTV Link Scraper & Updater
Automatiza la actualización selectiva de enlaces .m3u en GitHub
con tokens frescos desde las páginas de origen.
"""

import re
import os
import sys
import logging
from typing import Optional, Dict, Tuple
import subprocess
from pathlib import Path

try:
    from playwright.async_api import async_playwright
    import asyncio
except ImportError:
    print("❌ Playwright no instalado. Ejecuta: pip install playwright")
    sys.exit(1)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IPTVScraper:
    """Scraper y actualizador selectivo de links IPTV en archivos .m3u"""

    def __init__(self, m3u_path: str):
        """
        Inicializa el scraper con la ruta al archivo .m3u
        
        Args:
            m3u_path: Ruta al archivo .m3u (ej: 'prueba01.m3u')
        """
        self.m3u_path = Path(m3u_path)
        if not self.m3u_path.exists():
            raise FileNotFoundError(f"Archivo {m3u_path} no encontrado")
        
        self.m3u_content = self._read_m3u()
        self.channels = self._parse_channels()

    def _read_m3u(self) -> str:
        """Lee el contenido completo del archivo .m3u"""
        with open(self.m3u_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_channels(self) -> Dict[str, Dict]:
        """
        Parsea el archivo .m3u y extrae información de canales
        
        Retorna dict con estructura:
        {
            'tvg-id': {
                'name': 'Nombre Canal',
                'origin_url': 'https://...',
                'extinf_line': '#EXTINF:...',
                'stream_url': 'https://...',
                'full_entry': 'bloque completo'
            }
        }
        """
        channels = {}
        
        # Pattern para encontrar bloques de canales
        # Busca: comentario ORIGEN -> línea EXTINF -> URL
        pattern = r'#\s*ORIGEN:\s*(https?://[^\s]+)\s*\n#EXTINF:([^\n]+)\n([^\n]+)'
        
        matches = re.finditer(pattern, self.m3u_content, re.MULTILINE)
        
        for match in matches:
            origin_url = match.group(1).strip()
            extinf_line = match.group(2).strip()
            stream_url = match.group(3).strip()
            
            # Extrae tvg-id del EXTINF
            tvg_id_match = re.search(r'tvg-id="([^"]+)"', extinf_line)
            tvg_id = tvg_id_match.group(1) if tvg_id_match else None
            
            # Extrae nombre del canal
            name_match = re.search(r',([^\n]+)$', extinf_line)
            name = name_match.group(1).strip() if name_match else "Desconocido"
            
            if tvg_id:
                channels[tvg_id] = {
                    'name': name,
                    'origin_url': origin_url,
                    'extinf_line': extinf_line,
                    'stream_url': stream_url,
                    'full_pattern': match.group(0)  # Para reemplazo exacto
                }
                logger.info(f"✅ Canal parseado: {name} ({tvg_id})")
        
        return channels

    async def scrape_m3u8_url(self, origin_url: str, tvg_id: str) -> Optional[str]:
        """
        Scraping de la página de origen para obtener el URL .m3u8 con token fresco
        
        Args:
            origin_url: URL de la página origen del canal
            tvg_id: ID del canal (para logging)
            
        Returns:
            URL .m3u8 con token actualizado o None si falla
        """
        logger.info(f"🔍 Scrapiendo {tvg_id} desde: {origin_url}")
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Espera a que cargue la página (máx 15 segundos)
                await page.goto(origin_url, timeout=15000, wait_until='networkidle')
                
                # Intenta encontrar URLs .m3u8 en:
                # 1. Atributos de video/fuentes
                # 2. Scripts con URLs de streaming
                
                m3u8_url = await page.evaluate('''
                    () => {
                        // Busca en etiquetas de video/source
                        const sources = document.querySelectorAll('source, video');
                        for (let src of sources) {
                            const url = src.src || src.getAttribute('data-src');
                            if (url && url.includes('.m3u8')) return url;
                        }
                        
                        // Busca en contenido de scripts
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const match = script.textContent.match(/(https?:[^"'<>]*\.m3u8[^"'<>]*)/);
                            if (match) return match[1];
                        }
                        
                        // Busca en atributos data-
                        for (let elem of document.querySelectorAll('[data-stream]')) {
                            const url = elem.getAttribute('data-stream');
                            if (url && url.includes('.m3u8')) return url;
                        }
                        
                        return null;
                    }
                ''')
                
                await browser.close()
                
                if m3u8_url:
                    logger.info(f"✅ URL .m3u8 encontrada para {tvg_id}")
                    return m3u8_url
                else:
                    logger.warning(f"⚠️  No se encontró .m3u8 en {tvg_id}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Error scrapeando {tvg_id}: {str(e)}")
                return None

    def update_channel(self, tvg_id: str, new_stream_url: str) -> bool:
        """
        Actualiza selectivamente el enlace de un canal en el archivo .m3u
        
        Args:
            tvg_id: ID del canal a actualizar
            new_stream_url: Nueva URL del stream
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        if tvg_id not in self.channels:
            logger.error(f"❌ Canal {tvg_id} no encontrado")
            return False
        
        channel = self.channels[tvg_id]
        old_pattern = channel['full_pattern']
        
        # Crea el nuevo bloque manteniendo la estructura
        new_block = old_pattern.split('\n')
        new_block[-1] = new_stream_url  # Reemplaza solo la última línea (URL)
        new_block = '\n'.join(new_block)
        
        # Reemplaza en el contenido
        if old_pattern in self.m3u_content:
            self.m3u_content = self.m3u_content.replace(old_pattern, new_block)
            logger.info(f"✅ Canal {tvg_id} actualizado en memoria")
            return True
        else:
            logger.error(f"❌ No se pudo encontrar el patrón para {tvg_id}")
            return False

    def save_m3u(self) -> bool:
        """Guarda los cambios en el archivo .m3u"""
        try:
            with open(self.m3u_path, 'w', encoding='utf-8') as f:
                f.write(self.m3u_content)
            logger.info(f"💾 Archivo {self.m3u_path} guardado")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando archivo: {str(e)}")
            return False

    async def update_channel_async(self, tvg_id: str) -> bool:
        """
        Ejecuta el scraping y actualización de un canal (async)
        
        Args:
            tvg_id: ID del canal a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        if tvg_id not in self.channels:
            logger.error(f"❌ Canal {tvg_id} no encontrado en la lista")
            return False
        
        channel = self.channels[tvg_id]
        origin_url = channel['origin_url']
        
        # Scraping
        new_url = await self.scrape_m3u8_url(origin_url, tvg_id)
        
        if not new_url:
            logger.warning(f"⚠️  No se pudo obtener nueva URL para {tvg_id}, saltando...")
            return False
        
        # Actualización selectiva
        if self.update_channel(tvg_id, new_url):
            logger.info(f"✅ {tvg_id}: {channel['stream_url']} → {new_url}")
            return True
        
        return False

    def list_channels(self):
        """Lista todos los canales disponibles"""
        logger.info("\n📺 CANALES DISPONIBLES:")
        for tvg_id, channel in self.channels.items():
            print(f"  • {channel['name']} ({tvg_id})")
            print(f"    Origen: {channel['origin_url']}")
            print(f"    URL actual: {channel['stream_url']}\n")


def git_commit_and_push(message: str, m3u_file: str = "prueba01.m3u") -> bool:
    """
    Realiza commit y push de los cambios a GitHub
    
    Args:
        message: Mensaje del commit
        m3u_file: Archivo a commitear
        
    Returns:
        True si el commit y push fueron exitosos
    """
    try:
        # Configura git si es necesario
        os.system("git config user.email 'bot@iptv-scraper.local'")
        os.system("git config user.name 'IPTV Auto-Scraper'")
        
        # Add
        result = subprocess.run(['git', 'add', m3u_file], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"❌ Error en 'git add': {result.stderr}")
            return False
        
        # Commit
        result = subprocess.run(['git', 'commit', '-m', message], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"⚠️  Commit sin cambios o error: {result.stderr}")
            return False
        
        logger.info(f"✅ Commit realizado: {message}")
        
        # Push
        result = subprocess.run(['git', 'push'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"❌ Error en 'git push': {result.stderr}")
            return False
        
        logger.info("✅ Push a GitHub completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en git operations: {str(e)}")
        return False


async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="IPTV Auto-Scraper: Actualiza selectivamente enlaces .m3u",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Listar canales disponibles
  python iptv_scraper.py prueba01.m3u --list
  
  # Actualizar un canal específico
  python iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD
  
  # Actualizar múltiples canales
  python iptv_scraper.py prueba01.m3u --update Telefuturo.py@SD Trece.py@SD
  
  # Actualizar todos los canales
  python iptv_scraper.py prueba01.m3u --update-all
        """
    )
    
    parser.add_argument('m3u_file', help='Ruta al archivo .m3u')
    parser.add_argument('--list', action='store_true', help='Lista todos los canales')
    parser.add_argument('--update', nargs='+', help='Actualiza canales específicos (por tvg-id)')
    parser.add_argument('--update-all', action='store_true', help='Actualiza todos los canales')
    parser.add_argument('--no-push', action='store_true', help='No hace push a GitHub')
    
    args = parser.parse_args()
    
    try:
        scraper = IPTVScraper(args.m3u_file)
        
        if args.list:
            scraper.list_channels()
            return
        
        updated_channels = []
        
        # Determina qué canales actualizar
        tvg_ids_to_update = []
        if args.update_all:
            tvg_ids_to_update = list(scraper.channels.keys())
        elif args.update:
            tvg_ids_to_update = args.update
        else:
            logger.error("❌ Especifica --list, --update <tvg-id> o --update-all")
            sys.exit(1)
        
        # Ejecuta scraping y actualización para cada canal
        logger.info(f"\n🚀 Iniciando actualización de {len(tvg_ids_to_update)} canal(es)...\n")
        
        for tvg_id in tvg_ids_to_update:
            success = await scraper.update_channel_async(tvg_id)
            if success:
                updated_channels.append(tvg_id)
        
        # Guarda cambios
        if updated_channels:
            scraper.save_m3u()
            logger.info(f"\n✅ {len(updated_channels)} canal(es) actualizados")
            
            # Commit y push si está habilitado
            if not args.no_push:
                channels_str = ', '.join([scraper.channels[cid]['name'] for cid in updated_channels])
                commit_msg = f"🔄 Auto-update IPTV: {channels_str}"
                git_commit_and_push(commit_msg, args.m3u_file)
            else:
                logger.info("⏭️  Push a GitHub omitido (--no-push)")
        else:
            logger.warning("⚠️  No se realizaron actualizaciones")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
