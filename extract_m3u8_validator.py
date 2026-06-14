#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para extraer, validar y procesar URLs m3u8 desde archivos .m3u
Autor: Automatización de canales
Uso: python extract_m3u8_validator.py prueba01.m3u
"""

import re
import requests
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import sys
import os

class M3U8Extractor:
    """Extrae y valida URLs m3u8 de archivos .m3u"""
    
    def __init__(self, input_file: str, output_dir: str = "m3u8_output"):
        """
        Inicializa el extractor
        
        Args:
            input_file: Ruta del archivo .m3u a procesar
            output_dir: Directorio donde guardar los resultados
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.channels = []
        self.valid_urls = []
        self.invalid_urls = []
        self.timeout = 5
        
    def extract_channels(self) -> List[Dict]:
        """
        Extrae información de canales del archivo .m3u
        
        Returns:
            Lista de diccionarios con información de cada canal
        """
        print(f"📂 Leyendo archivo: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividir por líneas EXTINF
        pattern = r'#EXTINF:-1\s+([^\n]*)\n(https?://[^\s\n]+)'
        matches = re.findall(pattern, content)
        
        for metadata, url in matches:
            channel = self._parse_extinf(metadata, url)
            self.channels.append(channel)
        
        print(f"✓ {len(self.channels)} canales encontrados\n")
        return self.channels
    
    def _parse_extinf(self, metadata: str, url: str) -> Dict:
        """Parse de metadatos EXTINF"""
        channel = {
            'tvg_id': self._extract_attr(metadata, 'tvg-id'),
            'tvg_logo': self._extract_attr(metadata, 'tvg-logo'),
            'group_title': self._extract_attr(metadata, 'group-title'),
            'name': metadata.split(',')[-1].strip() if ',' in metadata else 'Unknown',
            'url': url.strip(),
            'status': None,
            'status_code': None,
            'error': None,
            'validated_at': None
        }
        return channel
    
    @staticmethod
    def _extract_attr(text: str, attr: str) -> str:
        """Extrae atributo de metadata EXTINF"""
        match = re.search(rf'{attr}="([^"]*)"', text)
        return match.group(1) if match else ""
    
    def validate_url(self, channel: Dict, max_redirects: int = 3) -> Dict:
        """
        Valida una URL m3u8
        
        Args:
            channel: Diccionario con info del canal
            max_redirects: Máximo de redirecciones a seguir
            
        Returns:
            Canal con resultado de validación
        """
        url = channel['url']
        
        try:
            # Usar HEAD request primero (más rápido)
            response = requests.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False
            )
            
            channel['status'] = 'valid' if response.status_code in [200, 206] else 'invalid'
            channel['status_code'] = response.status_code
            
            # Si HEAD falla, intentar GET
            if response.status_code >= 400:
                try:
                    response = requests.get(
                        url,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=False,
                        stream=True
                    )
                    channel['status_code'] = response.status_code
                    channel['status'] = 'valid' if response.status_code in [200, 206] else 'invalid'
                except Exception as e:
                    channel['status'] = 'invalid'
                    channel['error'] = str(e)
        
        except requests.exceptions.Timeout:
            channel['status'] = 'timeout'
            channel['error'] = 'Timeout'
        except requests.exceptions.ConnectionError:
            channel['status'] = 'connection_error'
            channel['error'] = 'Connection Error'
        except Exception as e:
            channel['status'] = 'error'
            channel['error'] = str(e)
        
        channel['validated_at'] = datetime.now().isoformat()
        return channel
    
    def validate_all(self, max_workers: int = 5) -> Tuple[List, List]:
        """
        Valida todas las URLs en paralelo
        
        Args:
            max_workers: Número de workers concurrentes
            
        Returns:
            Tupla (urls_válidas, urls_inválidas)
        """
        print(f"🔍 Validando {len(self.channels)} URLs (concurrencia: {max_workers})...\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.validate_url, channel): i 
                for i, channel in enumerate(self.channels)
            }
            
            for i, future in enumerate(as_completed(futures), 1):
                channel = future.result()
                status_symbol = "✓" if channel['status'] == 'valid' else "✗"
                
                print(f"[{i}/{len(self.channels)}] {status_symbol} {channel['name']:<20} | "
                      f"Status: {channel['status']:<15} | Code: {channel['status_code']}")
                
                if channel['status'] == 'valid':
                    self.valid_urls.append(channel)
                else:
                    self.invalid_urls.append(channel)
        
        print(f"\n📊 Resultados: {len(self.valid_urls)} válidas, {len(self.invalid_urls)} inválidas\n")
        return self.valid_urls, self.invalid_urls
    
    def save_results(self) -> None:
        """Guarda los resultados en diferentes formatos"""
        
        # 1. M3U con URLs válidas
        self._save_m3u_valid()
        
        # 2. JSON con detalles completos
        self._save_json_detailed()
        
        # 3. Texto plano con URLs válidas
        self._save_txt_urls()
        
        # 4. CSV con todas las URLs
        self._save_csv_all()
        
        # 5. Reporte HTML
        self._save_html_report()
    
    def _save_m3u_valid(self) -> None:
        """Guarda un archivo .m3u solo con URLs válidas"""
        output_file = self.output_dir / "canales_validos.m3u"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write("#PLAYLIST-DURATION:-1\n")
            f.write("#PLAYLIST-VERSION:3\n")
            f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Canales válidos: {len(self.valid_urls)}\n\n")
            
            for channel in self.valid_urls:
                f.write(f"#EXTINF:-1 tvg-id=\"{channel['tvg_id']}\" ")
                f.write(f"tvg-logo=\"{channel['tvg_logo']}\" ")
                f.write(f"group-title=\"{channel['group_title']}\",{channel['name']}\n")
                f.write(f"{channel['url']}\n\n")
        
        print(f"✓ M3U guardado: {output_file}")
    
    def _save_json_detailed(self) -> None:
        """Guarda detalles en JSON"""
        output_file = self.output_dir / "canales_detallado.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'archivo_origen': str(self.input_file),
            'total_canales': len(self.channels),
            'canales_validos': len(self.valid_urls),
            'canales_invalidos': len(self.invalid_urls),
            'porcentaje_validez': round((len(self.valid_urls) / len(self.channels) * 100), 2) if self.channels else 0,
            'canales': self.channels
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON guardado: {output_file}")
    
    def _save_txt_urls(self) -> None:
        """Guarda solo URLs válidas en texto plano"""
        output_file = self.output_dir / "urls_validas.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"URLs M3U8 VÁLIDAS\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {len(self.valid_urls)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, channel in enumerate(self.valid_urls, 1):
                f.write(f"{i}. {channel['name']}\n")
                f.write(f"   Grupo: {channel['group_title']}\n")
                f.write(f"   URL: {channel['url']}\n")
                f.write(f"   Status: {channel['status_code']}\n\n")
        
        print(f"✓ TXT guardado: {output_file}")
    
    def _save_csv_all(self) -> None:
        """Guarda CSV con todas las URLs"""
        import csv
        output_file = self.output_dir / "todos_canales.csv"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['nombre', 'grupo', 'tvg_id', 'url', 'estado', 'status_code', 'validado']
            )
            writer.writeheader()
            
            for channel in self.channels:
                writer.writerow({
                    'nombre': channel['name'],
                    'grupo': channel['group_title'],
                    'tvg_id': channel['tvg_id'],
                    'url': channel['url'],
                    'estado': channel['status'],
                    'status_code': channel['status_code'],
                    'validado': channel['validated_at']
                })
        
        print(f"✓ CSV guardado: {output_file}")
    
    def _save_html_report(self) -> None:
        """Guarda un reporte HTML interactivo"""
        output_file = self.output_dir / "reporte.html"
        
        valid_count = len(self.valid_urls)
        invalid_count = len(self.invalid_urls)
        total = len(self.channels)
        percentage = round((valid_count / total * 100), 2) if total > 0 else 0
        
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte M3U8</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1e1e2e; color: #cdd6f4; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #89b4fa; margin-bottom: 20px; text-align: center; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: #313244; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #89b4fa; }}
        .stat-card.valid {{ border-left-color: #a6e3a1; }}
        .stat-card.invalid {{ border-left-color: #f38ba8; }}
        .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
        .stat-label {{ font-size: 14px; color: #a6adc7; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #313244; padding: 12px; text-align: left; border-bottom: 2px solid #45475a; }}
        td {{ padding: 12px; border-bottom: 1px solid #45475a; }}
        tr:hover {{ background: #313244; }}
        .status-valid {{ color: #a6e3a1; font-weight: bold; }}
        .status-invalid {{ color: #f38ba8; font-weight: bold; }}
        .url-text {{ font-family: monospace; font-size: 12px; color: #a6adc7; overflow-x: auto; }}
        .footer {{ text-align: center; margin-top: 30px; color: #a6adc7; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Reporte de Validación M3U8</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total de Canales</div>
                <div class="stat-number">{total}</div>
            </div>
            <div class="stat-card valid">
                <div class="stat-label">Canales Válidos</div>
                <div class="stat-number">{valid_count}</div>
            </div>
            <div class="stat-card invalid">
                <div class="stat-label">Canales Inválidos</div>
                <div class="stat-number">{invalid_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Tasa de Validez</div>
                <div class="stat-number">{percentage}%</div>
            </div>
        </div>
        
        <h2>Canales Válidos</h2>
        <table>
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Grupo</th>
                    <th>TVG ID</th>
                    <th>Status</th>
                    <th>URL</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for channel in self.valid_urls:
            html_content += f"""                <tr>
                    <td>{channel['name']}</td>
                    <td>{channel['group_title']}</td>
                    <td>{channel['tvg_id']}</td>
                    <td><span class="status-valid">✓ {channel['status_code']}</span></td>
                    <td><div class="url-text">{channel['url'][:70]}...</div></td>
                </tr>
"""
        
        html_content += """            </tbody>
        </table>
        
        <h2 style="margin-top: 30px;">Canales Inválidos</h2>
        <table>
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Grupo</th>
                    <th>Estado</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for channel in self.invalid_urls:
            html_content += f"""                <tr>
                    <td>{channel['name']}</td>
                    <td>{channel['group_title']}</td>
                    <td><span class="status-invalid">✗ {channel['status']}</span></td>
                    <td>{channel['error'] or channel['status_code']}</td>
                </tr>
"""
        
        html_content += f"""            </tbody>
        </table>
        
        <div class="footer">
            <p>Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML guardado: {output_file}")
    
    def print_summary(self) -> None:
        """Imprime resumen de resultados"""
        print("\n" + "="*80)
        print("📈 RESUMEN DE VALIDACIÓN")
        print("="*80)
        print(f"Archivo procesado: {self.input_file}")
        print(f"Total de canales: {len(self.channels)}")
        print(f"✓ Canales válidos: {len(self.valid_urls)}")
        print(f"✗ Canales inválidos: {len(self.invalid_urls)}")
        
        if self.channels:
            percentage = round((len(self.valid_urls) / len(self.channels) * 100), 2)
            print(f"📊 Tasa de validez: {percentage}%")
        
        print(f"\n📁 Resultados guardados en: {self.output_dir.absolute()}")
        print("="*80 + "\n")


def main():
    """Función principal"""
    
    # Validar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: Debes especificar el archivo .m3u")
        print("\n💡 Uso:")
        print("   python extract_m3u8_validator.py prueba01.m3u")
        print("\nEjemplos:")
        print("   python extract_m3u8_validator.py prueba01.m3u")
        print("   python extract_m3u8_validator.py prueba02.m3u")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Validar que el archivo existe
    if not Path(input_file).exists():
        print(f"❌ Error: No se encontró el archivo '{input_file}'")
        print(f"\n📁 Archivos .m3u disponibles en el directorio actual:")
        m3u_files = list(Path('.').glob('*.m3u'))
        if m3u_files:
            for f in m3u_files:
                print(f"   - {f.name}")
        else:
            print("   (Ninguno encontrado)")
        sys.exit(1)
    
    print(f"✅ Usando archivo: {input_file}\n")
    
    # Configuración
    output_dir = "m3u8_output"
    
    # Crear extractor
    extractor = M3U8Extractor(input_file, output_dir)
    
    try:
        # Extraer canales
        extractor.extract_channels()
        
        # Validar URLs
        extractor.validate_all(max_workers=5)
        
        # Guardar resultados
        extractor.save_results()
        
        # Mostrar resumen
        extractor.print_summary()
        
        print("✨ ¡Proceso completado exitosamente!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
