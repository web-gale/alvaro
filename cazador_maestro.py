import re
import os
import sys
from playwright.sync_api import sync_playwright

# Configuración del archivo local
ARCHIVO_M3U = "playlist.m3u"

# Diccionario que mapea el nombre exacto de la lista M3U con su URL iframe correspondiente
CANALES_CONFIG = {
    # SPORTS
    "ESPN Premium": "https://embed.ksdjugfsddeports.com/embed2/espnpremium.html",
    "ESPN": "https://embed.ksdjugfsddeports.com/embed2/espn.html",
    "ESPN 2": "https://embed.ksdjugfsddeports.com/embed2/espn2.html",
    "ESPN 3": "https://embed.ksdjugfsddeports.com/embed2/espn3.html",
    "ESPN 4": "https://embed.ksdjugfsddeports.com/embed2/espn4.html",
    "ESPN 5": "https://embed.ksdjugfsddeports.com/embed2/espn5.html",
    "ESPN 6": "https://embed.ksdjugfsddeports.com/embed2/espn6.html",
    "ESPN 7": "https://embed.ksdjugfsddeports.com/embed2/espn7.html",
    "Fox Sports": "https://embed.ksdjugfsddeports.com/embed2/foxsports.html",
    "Fox Sports 2": "https://embed.ksdjugfsddeports.com/embed2/foxsports2.html",
    "Fox Sports 3": "https://embed.ksdjugfsddeports.com/embed2/foxsports3.html",
    "TUDN": "https://embed.ksdjugfsddeports.com/embed/tudn.html",
    "TyC Sports": "https://embed.ksdjugfsddeports.com/embed2/tycsports.html",
    "DirecTV Sports": "https://embed.ksdjugfsddeports.com/embed2/directvsports.html",
    "DirecTV Sports 2": "https://embed.ksdjugfsddeports.com/embed2/directvsports2.html",
    "Liga 1": "https://embed.ksdjugfsddeports.com/embed2/liga1.html",
    "DAZN LaLiga": "https://embed.ksdjugfsddeports.com/embed2/daznlaliga.html",
    "Movistar Liga de Campeones": "https://embed.ksdjugfsddeports.com/embed2/movistarligadecampeones.html",
    "Win Sports": "https://embed.ksdjugfsddeports.com/embed2/winsports.html",
    "Win Sports Plus": "https://embed.ksdjugfsddeports.com/embed2/winsportsplus.html",
    "beIN Sports XTRA": "https://embed.ksdjugfsddeports.com/embed2/beinsportsxtra.html",
    
    # ENTERTAINMENT
    "Space": "https://embed.ksdjugfsddeports.com/embed2/space.html",
    "Warner Channel": "https://embed.ksdjugfsddeports.com/embed2/warnerchannel.html",
    "TNT": "https://embed.ksdjugfsddeports.com/embed2/tnt.html",
    "Star Channel": "https://embed.ksdjugfsddeports.com/embed2/starchannel.html",
    "Cinemax": "https://embed.ksdjugfsddeports.com/embed2/cinemax.html",
    "Cinecanal": "https://embed.ksdjugfsddeports.com/embed2/cinecanal.html",
    "Distrito Comedia": "https://embed.ksdjugfsddeports.com/embed2/distritocomedia.html",
    "History": "https://embed.ksdjugfsddeports.com/embed2/history.html",
    "History 2": "https://embed.ksdjugfsddeports.com/embed2/history2.html",
    "Pasiones": "https://embed.ksdjugfsddeports.com/embed2/pasiones.html",
    "Tlnovelas": "https://embed.ksdjugfsddeports.com/embed2/tlnovelas.html",
    "Las Estrellas": "https://embed.ksdjugfsddeports.com/embed2/lasestrellas.html",
    "FX": "https://embed.ksdjugfsddeports.com/embed2/fx.html",
    "Golden Plus": "https://embed.ksdjugfsddeports.com/embed2/goldenplus.html",
    "Golden Edge": "https://embed.ksdjugfsddeports.com/embed2/goldenedge.html",
    "TNT Series": "https://embed.ksdjugfsddeports.com/embed2/tntseries.html",
    "Sony Channel": "https://embed.ksdjugfsddeports.com/embed2/sony.html",
    "AXN": "https://embed.ksdjugfsddeports.com/embed2/axn.html",
    "AMC": "https://embed.ksdjugfsddeports.com/embed2/amc.html",
    "Nat Geo": "https://embed.ksdjugfsddeports.com/embed2/natgeo.html",
    "Animal Planet": "https://embed.ksdjugfsddeports.com/embed2/animalplanet.html",
    "Discovery Channel": "https://embed.ksdjugfsddeports.com/embed2/discoverychannel.html",
    "TNT Novelas": "https://embed.ksdjugfsddeports.com/embed2/tntnovelas.html",
    "Discovery A&E": "https://embed.ksdjugfsddeports.com/embed2/discoveryaye.html",
    "Investigation Discovery": "https://embed.ksdjugfsddeports.com/embed2/idinvestigation.html",
    
    # KIDS
    "Cartoon Network": "https://embed.ksdjugfsddeports.com/embed2/cartoonnetwork.html",
    "Tooncast": "https://embed.ksdjugfsddeports.com/embed2/tooncast.html",
    "Disney Channel": "https://embed.ksdjugfsddeports.com/embed2/disneychannel.html"
}

def cazar_m3u8(url_iframe):
    url_capturada = None
    
    with sync_playwright() as p:
        # Iniciamos navegador de forma oculta
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )
        page = context.new_page()
        
        # Analizador de tráfico en tiempo real
        def evaluar_peticion(request):
            nonlocal url_capturada
            # Buscamos coincidencias con transmisiones .m3u8 que no sean vacías
            if ".m3u8" in request.url and ("live" in request.url or "embed" in request.url):
                url_capturada = request.url

        page.on("request", evaluar_peticion)
        
        try:
            # Forzamos la carga esperando a que se detenga el tráfico pesado
            page.goto(url_iframe, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(3000) # Colchón de espera dinámico
        except Exception:
            pass # Si da timeout pero capturó el link, nos sirve igual
        finally:
            browser.close()
            
    return url_capturada

def parchar_archivo_m3u(diccionario_enlaces):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"[-] Error crítico: No se encontró el archivo {ARCHIVO_M3U}")
        return False

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    i = 0
    conteo_actualizaciones = 0

    while i < len(lineas):
        linea = lineas[i]
        nuevas_lineas.append(linea)
        
        # Buscamos el patrón del nombre del canal al final del renglón #EXTINF
        if linea.startswith("#EXTINF"):
            canal_detectado = None
            for nombre_canal in diccionario_enlaces.keys():
                if linea.strip().endswith("," + nombre_canal):
                    canal_detectado = nombre_canal
                    break
            
            if canal_detectado and diccionario_enlaces[canal_detectado]:
                # Avanzamos para pasar los bloques #EXTVLCOPT intermediarios
                j = i + 1
                while j < len(lineas):
                    if lineas[j].strip().startswith("http"):
                        # Parcheamos la URL vieja con el flujo capturado fresco
                        nuevas_lineas.append(diccionario_enlaces[canal_detectado] + "\n")
                        conteo_actualizaciones += 1
                        i = j
                        break
                    else:
                        nuevas_lineas.append(lineas[j])
                        j += 1
        i += 1

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(nuevas_lineas)
        
    print(f"[+] Proceso completado: Se actualizaron {conteo_actualizaciones} canales en la lista.")

if __name__ == "__main__":
    print("[*] Iniciando cacería de tokens dinámicos...")
    enlaces_frescos = {}
    
    for canal, url in CANALES_CONFIG.items():
        print(f"[->] Extrayendo flujo para: {canal}")
        link = cazar_m3u8(url)
        if link:
            print(f"    [OK] Detectado: {link[:60]}...")
            enlaces_frescos[canal] = link
        else:
            print(f"    [X] No se pudo capturar flujo para este canal.")
            enlaces_frescos[canal] = None

    parchar_archivo_m3u(enlaces_frescos)
