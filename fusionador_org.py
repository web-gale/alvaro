import requests
import re

# URLs de origen (IPTV-ORG)
URL_PARAGUAY = "https://iptv-org.github.io/iptv/countries/py.m3u"
URL_ESPANOL = "https://iptv-org.github.io/iptv/languages/spa.m3u"

def descargar_y_combinar_listas():
    print("-> Iniciando descarga de fuentes de iptv-org...")
    canales_unicos = {}
    fuentes = [URL_PARAGUAY, URL_ESPANOL]
    
    for url in fuentes:
        print(f"-> Descargando y procesando: {url}")
        try:
            respuesta = requests.get(url, timeout=20)
            respuesta.raise_for_status()
            contenido = respuesta.text
        except Exception as e:
            print(f"[ERROR] No se pudo descargar {url}: {e}")
            continue
            
        lineas = contenido.splitlines()
        i = 0
        total_lineas = len(lineas)
        
        while i < total_lineas:
            linea_actual = lineas[i].strip()
            
            if linea_actual.startswith("#EXTINF"):
                info_canal = linea_actual
                
                nombre_canal = "Desconocido"
                if "," in info_canal:
                    nombre_canal = info_canal.split(",")[-1].strip().lower()
                
                tvg_id_match = re.search(r'tvg-id="([^"]+)"', info_canal)
                id_unico = tvg_id_match.group(1).lower() if tvg_id_match else nombre_canal
                
                url_canal = ""
                j = i + 1
                while j < total_lineas:
                    siguiente_linea = lineas[j].strip()
                    if siguiente_linea.startswith("#") or not siguiente_linea:
                        j += 1
                    else:
                        url_canal = siguiente_linea
                        break
                
                # Evitamos duplicados: si ya se cargó desde PY, se ignora en SPA
                if id_unico not in canales_unicos and url_canal:
                    canales_unicos[id_unico] = {
                        "info": info_canal,
                        "url": url_canal
                    }
                i = j
            i += 1

    # GUARDAR EN TU NUEVO ARCHIVO ESPECÍFICO
    archivo_salida = "Alvaro01.m3u"
    print(f"-> Guardando canales unificados en '{archivo_salida}'...")
    
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for datos in canales_unicos.values():
            f.write(datos["info"] + "\n")
            f.write(datos["url"] + "\n\n")
            
    print(f"[✓] ¡Listo! Se guardaron {len(canales_unicos)} canales únicos en {archivo_salida}.")

if __name__ == "__main__":
    descargar_y_combinar_listas()
