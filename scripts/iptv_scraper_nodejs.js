#!/usr/bin/env node

/**
 * IPTV Link Scraper & Updater (Node.js Alternative)
 * Automatiza la actualización selectiva de enlaces .m3u en GitHub
 * con tokens frescos desde las páginas de origen.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const playwright = require('playwright');

// Color output
const colors = {
  reset: '\x1b[0m',
  info: '\x1b[36m',    // cyan
  success: '\x1b[32m',  // green
  warning: '\x1b[33m',  // yellow
  error: '\x1b[31m',    // red
};

function log(level, message) {
  const timestamp = new Date().toISOString();
  const prefix = level.toUpperCase().padEnd(5);
  console.log(`${timestamp} - ${prefix} - ${message}`);
}

function info(msg) { console.log(`${colors.info}ℹ️  ${msg}${colors.reset}`); }
function success(msg) { console.log(`${colors.success}✅ ${msg}${colors.reset}`); }
function warning(msg) { console.log(`${colors.warning}⚠️  ${msg}${colors.reset}`); }
function error(msg) { console.log(`${colors.error}❌ ${msg}${colors.reset}`); }

/**
 * IPTVScraper - Scraper y actualizador de enlaces IPTV
 */
class IPTVScraper {
  constructor(m3uPath) {
    this.m3uPath = m3uPath;
    
    if (!fs.existsSync(m3uPath)) {
      throw new Error(`Archivo ${m3uPath} no encontrado`);
    }
    
    this.m3uContent = fs.readFileSync(m3uPath, 'utf8');
    this.channels = this.parseChannels();
  }

  /**
   * Parsea el archivo .m3u y extrae información de canales
   */
  parseChannels() {
    const channels = {};
    
    // Patrón: comentario ORIGEN -> línea EXTINF -> URL
    const pattern = /#\s*ORIGEN:\s*(https?:\/\/[^\s]+)\s*\n#EXTINF:([^\n]+)\n([^\n]+)/gm;
    
    let match;
    while ((match = pattern.exec(this.m3uContent)) !== null) {
      const originUrl = match[1].trim();
      const extinfLine = match[2].trim();
      const streamUrl = match[3].trim();
      
      // Extrae tvg-id
      const tvgIdMatch = extinfLine.match(/tvg-id="([^"]+)"/);
      const tvgId = tvgIdMatch ? tvgIdMatch[1] : null;
      
      // Extrae nombre del canal
      const nameMatch = extinfLine.match(/,([^\n]+)$/);
      const name = nameMatch ? nameMatch[1].trim() : 'Desconocido';
      
      if (tvgId) {
        channels[tvgId] = {
          name,
          originUrl,
          extinfLine,
          streamUrl,
          fullPattern: match[0]
        };
        success(`Canal parseado: ${name} (${tvgId})`);
      }
    }
    
    return channels;
  }

  /**
   * Scraping de la página de origen para obtener el URL .m3u8 con token fresco
   */
  async scrapeM3u8Url(originUrl, tvgId) {
    info(`Scrapiendo ${tvgId} desde: ${originUrl}`);
    
    let browser;
    try {
      browser = await playwright.chromium.launch({ headless: true });
      const page = await browser.newPage();
      
      // Carga la página
      await page.goto(originUrl, { timeout: 15000, waitUntil: 'networkidle' });
      
      // Busca URL .m3u8
      const m3u8Url = await page.evaluate(() => {
        // Busca en etiquetas source/video
        const sources = document.querySelectorAll('source, video');
        for (let src of sources) {
          const url = src.src || src.getAttribute('data-src');
          if (url && url.includes('.m3u8')) return url;
        }
        
        // Busca en scripts
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
      });
      
      await browser.close();
      
      if (m3u8Url) {
        success(`URL .m3u8 encontrada para ${tvgId}`);
        return m3u8Url;
      } else {
        warning(`No se encontró .m3u8 en ${tvgId}`);
        return null;
      }
      
    } catch (err) {
      error(`Error scrapiendo ${tvgId}: ${err.message}`);
      if (browser) await browser.close();
      return null;
    }
  }

  /**
   * Actualiza selectivamente el enlace de un canal
   */
  updateChannel(tvgId, newStreamUrl) {
    if (!this.channels[tvgId]) {
      error(`Canal ${tvgId} no encontrado`);
      return false;
    }
    
    const channel = this.channels[tvgId];
    const oldPattern = channel.fullPattern;
    
    // Crea el nuevo bloque
    const lines = oldPattern.split('\n');
    lines[lines.length - 1] = newStreamUrl;
    const newBlock = lines.join('\n');
    
    // Reemplaza en contenido
    if (this.m3uContent.includes(oldPattern)) {
      this.m3uContent = this.m3uContent.replace(oldPattern, newBlock);
      success(`Canal ${tvgId} actualizado en memoria`);
      return true;
    } else {
      error(`No se pudo encontrar el patrón para ${tvgId}`);
      return false;
    }
  }

  /**
   * Guarda los cambios en el archivo .m3u
   */
  saveM3u() {
    try {
      fs.writeFileSync(this.m3uPath, this.m3uContent, 'utf8');
      success(`Archivo ${this.m3uPath} guardado`);
      return true;
    } catch (err) {
      error(`Error guardando archivo: ${err.message}`);
      return false;
    }
  }

  /**
   * Ejecuta scraping y actualización de un canal
   */
  async updateChannelAsync(tvgId) {
    if (!this.channels[tvgId]) {
      error(`Canal ${tvgId} no encontrado`);
      return false;
    }
    
    const channel = this.channels[tvgId];
    const newUrl = await this.scrapeM3u8Url(channel.originUrl, tvgId);
    
    if (!newUrl) {
      warning(`No se pudo obtener nueva URL para ${tvgId}, saltando...`);
      return false;
    }
    
    if (this.updateChannel(tvgId, newUrl)) {
      info(`${tvgId}: ${channel.streamUrl.substring(0, 50)}... → ${newUrl.substring(0, 50)}...`);
      return true;
    }
    
    return false;
  }

  /**
   * Lista todos los canales disponibles
   */
  listChannels() {
    console.log('\n📺 CANALES DISPONIBLES:');
    for (const [tvgId, channel] of Object.entries(this.channels)) {
      console.log(`  • ${channel.name} (${tvgId})`);
      console.log(`    Origen: ${channel.originUrl}`);
      console.log(`    URL: ${channel.streamUrl}\n`);
    }
  }
}

/**
 * Git operations
 */
function gitCommitAndPush(message, m3uFile = 'prueba01.m3u') {
  try {
    execSync('git config user.email "bot@iptv-scraper.local"', { stdio: 'pipe' });
    execSync('git config user.name "IPTV Auto-Scraper"', { stdio: 'pipe' });
    
    execSync(`git add ${m3uFile}`, { stdio: 'pipe' });
    execSync(`git commit -m "${message}"`, { stdio: 'pipe' });
    execSync('git push', { stdio: 'pipe' });
    
    success('Commit y push completados');
    return true;
  } catch (err) {
    warning(`Git error: ${err.message}`);
    return false;
  }
}

/**
 * Main
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
Uso: node iptv_scraper_nodejs.js <m3u-file> [opciones]

Opciones:
  --list              Lista todos los canales
  --update <ids>      Actualiza canales específicos
  --update-all        Actualiza todos los canales
  --no-push           No hace push a GitHub

Ejemplos:
  node iptv_scraper_nodejs.js prueba01.m3u --list
  node iptv_scraper_nodejs.js prueba01.m3u --update Telefuturo.py@SD
  node iptv_scraper_nodejs.js prueba01.m3u --update-all
    `);
    process.exit(0);
  }
  
  const m3uFile = args[0];
  const command = args[1];
  
  try {
    const scraper = new IPTVScraper(m3uFile);
    
    if (command === '--list') {
      scraper.listChannels();
      return;
    }
    
    let tvgIdsToUpdate = [];
    let shouldPush = !args.includes('--no-push');
    
    if (command === '--update-all') {
      tvgIdsToUpdate = Object.keys(scraper.channels);
    } else if (command === '--update') {
      tvgIdsToUpdate = args.slice(2).filter(a => !a.startsWith('--'));
    } else {
      error('Comando no reconocido. Usa --list, --update <ids> o --update-all');
      process.exit(1);
    }
    
    info(`\n🚀 Iniciando actualización de ${tvgIdsToUpdate.length} canal(es)...\n`);
    
    const updated = [];
    for (const tvgId of tvgIdsToUpdate) {
      const result = await scraper.updateChannelAsync(tvgId);
      if (result) updated.push(tvgId);
    }
    
    if (updated.length > 0) {
      scraper.saveM3u();
      success(`${updated.length} canal(es) actualizados`);
      
      if (shouldPush) {
        const channels = updated.map(id => scraper.channels[id].name).join(', ');
        gitCommitAndPush(`🔄 Auto-update IPTV: ${channels}`, m3uFile);
      }
    } else {
      warning('No se realizaron actualizaciones');
      process.exit(1);
    }
    
  } catch (err) {
    error(`Error fatal: ${err.message}`);
    process.exit(1);
  }
}

main();
