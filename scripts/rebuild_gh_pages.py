import base64
import json
import os
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent

def read_local(rel_path):
    return (root / rel_path).read_text(encoding='utf-8')

def read_local_bytes(rel_path):
    return (root / rel_path).read_bytes()

def rebuild():
    print("Iniciando reconstrucción de la web Miku Desktop (gh-pages)...")

    # 1. Archivos locales de UI
    island_css = read_local('miku_ui/src/island.css')
    island_js = read_local('miku_ui/src/island.js')
    settings_css = read_local('miku_ui/src/settings.css')
    settings_js = read_local('miku_ui/src/settings.js')
    bridge_js = read_local('miku_ui/src/bridge.js')
    sound_fx_js = read_local('miku_ui/src/sound_fx.js')
    index_island_html = read_local('miku_ui/src/index.html')
    settings_html = read_local('miku_ui/src/miku_settings.html')

    # 1b. Assets en base64 para los simuladores embebidos
    b64_icon_settings = ""
    icon_settings_path = root / 'miku_ui/src/assets/icon_settings.png'
    if icon_settings_path.exists():
        b64_icon_settings = base64.b64encode(icon_settings_path.read_bytes()).decode('ascii')

    b64_icon_main = ""
    icon_main_path = root / 'miku_ui/src/assets/icon_main.png'
    if icon_main_path.exists():
        b64_icon_main = base64.b64encode(icon_main_path.read_bytes()).decode('ascii')

    # 2. Simulador d1 (Isla Dinámica)
    d1_inlined = index_island_html
    d1_inlined = d1_inlined.replace('<head>', '<head><script>window.IS_WEB_SHOWCASE = true;</script>')
    if b64_icon_main:
        d1_inlined = d1_inlined.replace('assets/icon_main.png', f'data:image/png;base64,{b64_icon_main}')
    d1_inlined = d1_inlined.replace('<link rel="stylesheet" href="island.css">', f'<style>\n{island_css}\n</style>')
    d1_inlined = d1_inlined.replace('<script src="sound_fx.js"></script>', f'<script>\n{sound_fx_js}\n</script>')
    d1_inlined = d1_inlined.replace('<script src="bridge.js"></script>', f'<script>\n{bridge_js}\n</script>')
    d1_inlined = d1_inlined.replace('<script src="island.js"></script>', f'<script>\n{island_js}\n</script>')
    b64_d1 = base64.b64encode(d1_inlined.encode('utf-8')).decode('ascii')

    # 3. Simulador d2 (Ajustes & Miku-Link)
    d2_inlined = settings_html
    d2_inlined = d2_inlined.replace('<head>', '<head><script>window.IS_WEB_SHOWCASE = true;</script>')
    if b64_icon_settings:
        d2_inlined = d2_inlined.replace('assets/icon_settings.png', f'data:image/png;base64,{b64_icon_settings}')
    d2_inlined = d2_inlined.replace('<link rel="stylesheet" href="settings.css">', f'<style>\n{settings_css}\n</style>')
    d2_inlined = d2_inlined.replace('<script src="bridge.js"></script>', f'<script>\n{bridge_js}\n</script>')
    d2_inlined = d2_inlined.replace('<script src="sound_fx.js"></script>', f'<script>\n{sound_fx_js}\n</script>')
    d2_inlined = d2_inlined.replace('<script src="settings.js"></script>', f'<script>\n{settings_js}\n</script>')
    b64_d2 = base64.b64encode(d2_inlined.encode('utf-8')).decode('ascii')

    # 4. Obtener plantilla base
    template_path = root / 'website' / 'landing_template.html'
    if template_path.exists():
        base_html = template_path.read_text(encoding='utf-8')
    else:
        # Fallback a git
        try:
            base_html = subprocess.check_output(['git', 'show', 'origin/gh-pages:index.html'], cwd=str(root)).decode('utf-8', errors='ignore')
        except Exception:
            base_html = subprocess.check_output(['git', 'show', 'gh-pages:index.html'], cwd=str(root)).decode('utf-8', errors='ignore')

    # Reemplazar payloads embebidos
    html = re.sub(r'<script id="d1" type="text/plain">.*?</script>', f'<script id="d1" type="text/plain">{b64_d1}</script>', base_html, flags=re.DOTALL)
    html = re.sub(r'<script id="d2" type="text/plain">.*?</script>', f'<script id="d2" type="text/plain">{b64_d2}</script>', html, flags=re.DOTALL)

    # 5. Obtener versión del proyecto desde tauri.conf.json
    tauri_conf_path = root / 'miku_ui/src-tauri/tauri.conf.json'
    cur_ver = '0.2.0'
    if tauri_conf_path.exists():
        try:
            tauri_conf = json.loads(tauri_conf_path.read_text(encoding='utf-8'))
            cur_ver = tauri_conf.get('version', cur_ver)
        except Exception:
            pass
    print(f"Sincronizando página web a la versión: v{cur_ver}")

    html = re.sub(r'v0\.[0-9]+\.[0-9]+', f'v{cur_ver}', html)
    html = re.sub(r'0\.[0-9]+\.[0-9]+', cur_ver, html)

    # Cache-Control meta
    cache_meta = '''<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">'''
    if 'http-equiv="Cache-Control"' not in html:
        html = html.replace('<head>', f'<head>\n{cache_meta}')

    # Limpiar botón viejo de kofi en nav
    html = re.sub(r'<a href="https://ko-fi\.com/cxmlo"[^>]*class="kofi-nav-btn"[^>]*>.*?</a>\s*', '', html, flags=re.DOTALL)

    # Tarjeta Ko-fi oficial en Hero
    kofi_card_html = '''    <!-- Tarjeta de Apoyo de la Comunidad Ko-fi (Estilo Miku Cyber Glass) -->
    <div class="kofi-showcase-card">
      <div class="kofi-showcase-avatar-box">
        <img src="assets/kofi_badge.png" class="kofi-avatar-img" alt="Miku Ko-fi">
      </div>
      <div class="kofi-showcase-text">
        <span class="kofi-tag">Comunidad & Apoyo Libre</span>
        <h3 class="kofi-title">¿Te gusta Miku? Invítame un café en Ko-fi</h3>
        <p class="kofi-desc">Tu aporte ayuda a costear APIs y mantener el software 100% libre, gratuito y sin publicidad.</p>
      </div>
      <a href="https://ko-fi.com/cxmlo" target="_blank" rel="noopener noreferrer" class="kofi-action-btn" title="Apoyar en Ko-fi">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M23.881 8.948c-.773-4.085-4.859-4.593-4.859-4.593H.723c-.604 0-.679.798-.679.798s-.082 7.324-.022 11.822c.164 2.424 2.586 2.672 2.586 2.672s8.267-.023 11.966-.049c2.438-.426 2.683-2.566 2.658-3.734 4.352.24 7.422-2.831 6.649-6.916zm-11.062 3.511c-1.246 1.453-4.011 3.976-4.011 3.976s-.121.119-.31.023c-.076-.057-.028-.155-.028-.155s-2.766-2.523-4.012-3.976c-1.572-1.833-.699-4.225 1.543-4.225 1.516 0 2.453 1.258 2.695 1.701.241-.443 1.178-1.701 2.695-1.701 2.242 0 3.115 2.392 1.543 4.225zm8.472-1.571c-.139 1.633-1.633 2.193-3.666 2.158.077-1.748.077-4.032.077-4.032s1.777-.077 3.589.654c.78.315.823 1.053.823 1.053z"/></svg>
        <span>Invitar un café</span>
      </a>
    </div>'''

    sub_tag = '<p class="sub" data-t="sub"></p>'
    if sub_tag in html and 'kofi-showcase-card' not in html:
        html = html.replace(sub_tag, f'{sub_tag}\n\n{kofi_card_html}')

    clean_custom_css = '''
/* ── Reglas Estrictas para Navbar, Botones e Icono ── */
nav {
  position: fixed !important;
  top: env(safe-area-inset-top, 0px) !important;
  left: 0 !important;
  right: 0 !important;
  z-index: 100 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  height: 52px !important;
  max-height: 52px !important;
  padding: 0 18px !important;
  gap: clamp(10px, 2vw, 24px) !important;
  background: rgba(8, 9, 13, 0.88) !important;
  -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
  backdrop-filter: blur(24px) saturate(180%) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-sizing: border-box !important;
}
nav a.brand {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  font-weight: 700 !important;
  font-size: 14.5px !important;
  color: #fff !important;
  text-decoration: none !important;
  flex: none !important;
}
nav a.brand img {
  width: 22px !important;
  height: 22px !important;
  border-radius: 6px !important;
  object-fit: cover !important;
  flex: none !important;
  display: inline-block !important;
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.3) !important;
}
nav .gh-btn {
  height: 30px !important;
  max-height: 30px !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 0 10px !important;
  border-radius: 99px !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.18) !important;
  color: var(--mut) !important;
  text-decoration: none !important;
  font-size: 11.5px !important;
  font-family: var(--mono) !important;
  transition: all .2s !important;
  flex: none !important;
  background: none !important;
}
nav .gh-btn:hover {
  color: #fff !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35) !important;
}
nav .gh-btn svg {
  width: 14px !important;
  height: 14px !important;
  fill: currentColor !important;
  flex: none !important;
}
nav .lang {
  height: 30px !important;
  max-height: 30px !important;
  display: inline-flex !important;
  align-items: center !important;
  border-radius: 99px !important;
  background: rgba(255, 255, 255, 0.06) !important;
  padding: 2px !important;
  flex: none !important;
  box-sizing: border-box !important;
}
nav .lang button {
  height: 26px !important;
  line-height: 26px !important;
  padding: 0 8px !important;
  border-radius: 99px !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  color: var(--mut) !important;
  background: none !important;
  border: none !important;
  cursor: pointer !important;
  transition: all .16s !important;
}
nav .lang button.on {
  background: rgba(255, 255, 255, 0.18) !important;
  color: #fff !important;
}
.kofi-showcase-card {
  margin: 22px auto 28px !important;
  max-width: 680px !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 18px !important;
  padding: 16px 22px !important;
  background: radial-gradient(120% 80% at 50% 0%, rgba(255, 94, 91, 0.14) 0%, rgba(13, 16, 24, 0.9) 100%) !important;
  border: 1px solid rgba(255, 94, 91, 0.28) !important;
  border-radius: 20px !important;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 24px rgba(255, 94, 91, 0.1) !important;
  box-sizing: border-box !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
}
.kofi-showcase-avatar-box {
  width: 56px !important;
  height: 56px !important;
  flex: none !important;
  display: grid !important;
  place-items: center !important;
}
.kofi-avatar-img {
  width: 56px !important;
  height: 56px !important;
  border-radius: 14px !important;
  object-fit: contain !important;
  filter: drop-shadow(0 6px 14px rgba(255, 94, 91, 0.45)) !important;
  animation: kofiFloat 3.2s ease-in-out infinite !important;
}
@keyframes kofiFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px) scale(1.02); }
}
.kofi-showcase-text {
  flex: 1 !important;
  min-width: 0 !important;
  text-align: left !important;
}
.kofi-tag {
  display: inline-block !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
  color: #ff827f !important;
  margin-bottom: 3px !important;
}
.kofi-title {
  margin: 0 0 3px !important;
  font-size: 14.5px !important;
  font-weight: 700 !important;
  color: #fff !important;
  letter-spacing: -.01em !important;
}
.kofi-desc {
  margin: 0 !important;
  font-size: 11.5px !important;
  line-height: 1.4 !important;
  color: var(--mut) !important;
}
.kofi-action-btn {
  height: 36px !important;
  padding: 0 16px !important;
  border-radius: 99px !important;
  background: #ff5e5b !important;
  color: #fff !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  text-decoration: none !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  white-space: nowrap !important;
  transition: all .2s ease !important;
  box-shadow: 0 4px 16px rgba(255, 94, 91, 0.4) !important;
  flex: none !important;
}
.kofi-action-btn:hover {
  background: #ff4743 !important;
  box-shadow: 0 6px 22px rgba(255, 94, 91, 0.6) !important;
  transform: translateY(-2px) !important;
}
@media (max-width: 768px) {
  nav {
    justify-content: space-between !important;
    padding: 0 12px !important;
    height: 48px !important;
  }
  nav .nav-link-sub { display: none !important; }
  nav .gh-btn span { display: none !important; }
  nav .gh-btn { padding: 0 7px !important; height: 28px !important; }
  nav .lang { height: 28px !important; }
  nav .lang button { height: 24px !important; padding: 0 6px !important; font-size: 10px !important; }
  .kofi-showcase-card {
    flex-direction: column !important;
    text-align: center !important;
    padding: 18px 14px !important;
    gap: 12px !important;
    margin: 18px auto 22px !important;
  }
  .kofi-showcase-text {
    text-align: center !important;
  }
  .kofi-action-btn {
    width: 100% !important;
    justify-content: center !important;
  }
}
'''
    if 'kofi-showcase-card' not in html or 'kofiFloat' not in html:
        style_end = html.find('</style>')
        if style_end != -1:
            html = html[:style_end] + '\n' + clean_custom_css + '\n' + html[style_end:]

    release_sync_js = r'''
/* Sincronización automática de versiones en tiempo real desde GitHub Releases */
(async () => {
  try {
    const res = await fetch('https://api.github.com/repos/cxmlo/miku/releases/latest');
    if (!res.ok) return;
    const rel = await res.json();
    const tag = rel.tag_name || '';
    if (!tag) return;
    const ver = tag.replace(/^v/, '');

    document.querySelectorAll('.dl-badge, #dt-win, #dt-apk, [data-t="tag"], [data-t="w_set"], [data-t="dl_win_tag"], [data-t="dl_apk_tag"]').forEach(el => {
      if (el && el.textContent) el.textContent = el.textContent.replace(/v?0\.[0-9]+\.[0-9]+/g, 'v' + ver);
    });

    if (typeof I !== 'undefined') {
      for (const lang in I) {
        for (const key in I[lang]) {
          if (typeof I[lang][key] === 'string') {
            I[lang][key] = I[lang][key].replace(/v?0\.[0-9]+\.[0-9]+/g, 'v' + ver);
          }
        }
      }
    }

    if (Array.isArray(rel.assets)) {
      const winAsset = rel.assets.find(a => a.name.endsWith('.exe') && !a.name.includes('core'));
      if (winAsset) {
        const mb = (winAsset.size / (1024 * 1024)).toFixed(0);
        document.querySelectorAll('[data-t="dl_win_p"]').forEach(p => {
          p.textContent = p.textContent.replace(/\([0-9]+\s*MB\)/i, `(${mb} MB)`);
        });
      }
      const apkAsset = rel.assets.find(a => a.name.endsWith('.apk'));
      if (apkAsset) {
        const mb = (apkAsset.size / (1024 * 1024)).toFixed(1);
        document.querySelectorAll('[data-t="dl_apk_p"]').forEach(p => {
          p.textContent = p.textContent.replace(/\([0-9.]+\s*MB\)/i, `(${mb} MB)`);
        });
      }
    }
  } catch (_) {}
})();
'''
    if 'releases/latest' not in html:
        html = html.replace('</script></body>', f'\n{release_sync_js}\n</script></body>')

    # Guardar en website/index.html (para despliegue directo de páginas)
    website_dir = root / 'website'
    website_dir.mkdir(exist_ok=True)
    out_file = website_dir / 'index.html'
    out_file.write_text(html, encoding='utf-8')
    print(f"Página construida con éxito en: {out_file} ({len(html)} bytes)")

    # Guardar también en scratch si existe
    scratch_dir = root / 'scratch'
    if scratch_dir.exists():
        (scratch_dir / 'gh_pages_index_built.html').write_text(html, encoding='utf-8')

    return out_file

if __name__ == '__main__':
    rebuild()
