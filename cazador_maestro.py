import sys
import os
import re
import json
import requests
from bs4 import BeautifulSoup

# Configuración básica de cabeceras para simular un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
M3U8_REGEX = re.compile(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*')

# Diccionario de emparejamiento automático: tvg-id -> URL de origen web
MAPA_FUENTES = {
    "telefuturo": "https://www.telefuturo.com.py/envivo",
    "trece": "https://trece.com.py/en-vivo/",
    "unicanal": "https://unicanal.com.py/en-vivo/"
}

# ===========================================================================
# BLOQUE DE SCRAPING (LÓGICA DE CLAUDE)
# ===========================================================================
def extract_m3u8_generic(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        matches = M3U8_REGEX.findall(resp.text)
        if matches:
            return matches[0]
    except Exception as e:
        print(f"[ERROR Generic] {e}")
    return None

def extract_dailymotion_id(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            match = re.search(r"dailymotion\.com/embed/video/([a-zA-Z0-9]+)", src)
            if match: return match.group(1)
        match = re.search(r"dailymotion\.com/(?:embed/)?video/([a-zA-Z0-9]+)", resp.text)
        if match: return match.group(1)
    except Exception as e:
        print(f"[ERROR Dailymotion ID] {e}")
    return None

def get_m3u8_from_dailymotion(video_id):
    metadata_url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"
    try:
        resp = requests.get(metadata_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        qualities = data.get("qualities", {})
        for key in ("auto", "0"):
            if key in qualities and qualities[key]:
                return qualities[key][0]["url"]
        for streams in qualities.values():
            if streams: return streams[0]["url"]
    except Exception as e:
        print(f"[ERROR Dailymotion Metadata] {e}")
    return None

def extract_m3u8_with_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] Playwright no instalado en el entorno.")
        return None

    found_url = {"value": None}
    def handle_request(request):
        if ".m3u8" in request.url and found_url["value"] is None:
            found_url["value"] = request.url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.on("request", handle_request)
        try:
            page.goto(url, timeout=10000)
            page.wait_for_timeout(5000)  # Espera 5 segundos a que cargue el reproductor
        except Exception as e:
            print(f"[ERROR Playwright Navegación] {e}")
        finally:
            browser.close()
    return found_url["value"]

def obtener_enlace_fresco(canal_id):
    url_origen = MAPA_FUENTES.get(canal_id.lower())
    if not url_origen:
        print(f"[X] No hay URL de origen configurada para el id: '{canal_id}'")
        return None

    print(f"-> Analizando origen para [{canal_id}]: {url_origen}")
    
    # Intento 1: Buscar directo en el HTML estático
    link = extract_m3u8_generic(url_origen)
    if link: return link

    # Intento 2: Buscar si usa Dailymotion (Trece, Unicanal)
    dm_id = extract_dailymotion_id(url_origen)
    if dm_id:
        link = get_m3u8_from_dailymotion(dm_id)
        if link: return link

    # Intento 3: Forzar navegador virtual interactivo (Telefuturo)
    print(f"   [INFO] Intentando extracción avanzada por ráfaga de red...")
    link = extract_m3u8_with_playwright(url_origen)
    return link

# ===========================================================================
# BLOQUE INYECTOR QUIRÚRGICO (LÓGICA DE GEMINI)
# ===========================================================================
def inyectar_url_quirurgica(file_path, tvg_id_target, nueva_url):
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe.")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    modificado = False
    nuevas_lineas = []
    i = 0
    total_lineas = len(lineas)

    while i < total_lineas:
        linea = lineas[i]
        nuevas_lineas.append(linea)
        
        # Identifica quirúrgicamente la etiqueta del canal exacto de manera insensible a mayúsculas
        if "#EXTINF" in linea and f'tvg-id="{tvg_id_target.lower()}"' in linea.lower():
            j = i + 1
            while j < total_lineas:
                siguiente_linea = lineas[j]
                if siguiente_linea.strip().startswith('#') or not siguiente_linea.strip():
                    nuevas_lineas.append(siguiente_linea)
                    j += 1
                    i += 1
                else:
                    # Encontró el stream viejo, inyectamos la URL fresca manteniendo el formato del archivo
                    nuevas_lineas.append(nueva_url.strip() + '\n')
                    print(f" [✓] Reemplazo quirúrgico exitoso para el canal: '{tvg_id_target}'")
                    modificado = True
                    i = j
                    break
        i += 1

    if modificado:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(nuevas_lineas)
        return True
    return False

# ===========================================================================
# EJECUCIÓN PRINCIPAL
# ===========================================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cazador_maestro.py <tvg-id>")
        sys.exit(1)
        
    target_canal = sys.argv[1]
    archivo_lista = "lista_personal.m3u"
    
    url_fresca = obtener_enlace_fresco(target_canal)
    
    if url_fresca:
        print(f" [OK] Enlace obtenido: {url_fresca[:60]}...")
        inyectar_url_quirurgica(archivo_lista, target_canal, url_fresca)
    else:
        print(f" [FAIL] No se pudo rescatar un token activo para '{target_canal}'")
