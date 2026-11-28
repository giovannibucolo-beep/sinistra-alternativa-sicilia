#!/usr/bin/env python3
"""Apre ogni pagina a misura telefono e computer: sbordi orizzontali, tasti troppo piccoli, errori di script.

  python3 strumenti/prova_resa.py            con Chrome
  python3 strumenti/prova_resa.py --webkit   con WebKit, il motore di Safari e di tutti i
                                             browser su iPhone: è il motore che rompe cose
                                             diverse dagli altri, e metà della Sicilia ha un iPhone.

Serve Playwright.
"""
import pathlib, json, sys, http.server, threading, functools
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(__file__).parent.parent / 'pubblico'
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8791), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))); srv.RequestHandlerClass.log_message = lambda *a: None
threading.Thread(target=srv.serve_forever, daemon=True).start()
guai = 0
with sync_playwright() as p:
    motore = '--webkit' in sys.argv
    b = p.webkit.launch() if motore else p.chromium.launch(channel='chrome', args=['--no-sandbox'])
    print('motore:', 'WebKit (Safari, iPhone)' if motore else 'Chrome')
    for f in sorted(OUT.rglob('*.html')):
        if f.relative_to(OUT).as_posix().startswith('admin/'): continue  # pannello di scrittura, non è una pagina del sito
        nome = str(f.relative_to(OUT))
        if nome == '404.html': continue   # usa indirizzi assoluti: si prova solo in linea
        for et, w, h in [('tel stretto', 320, 640), ('tel', 390, 844), ('tablet', 760, 1000), ('pc piccolo', 1180, 800), ('pc', 1440, 900)]:
            pg = b.new_page(viewport={'width': w, 'height': h}); err = []; pg.on('pageerror', lambda e: err.append(str(e))); pg.on('requestfailed', lambda r: err.append('non caricato: ' + r.url) if '/risorse/img/' not in r.url else None)
            pg.goto('http://127.0.0.1:8791/' + nome); pg.wait_for_timeout(250)
            r = pg.evaluate('''()=>{const W=innerWidth;const fuori=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>W+1||r.left<-1)&&!e.closest('.salta')&&!e.closest('.menu:not(.aperto)')}).slice(0,3).map(e=>e.tagName+'.'+e.className);
              const picc=[...document.querySelectorAll('main a.btn, main button, .menu-b, main input, main select, a.evento, a.scheda, .striscia a')].filter(e=>{const r=e.getBoundingClientRect();return r.height>0&&r.height<44}).map(e=>(e.textContent||e.name||'').trim().slice(0,18)+':'+Math.round(e.getBoundingClientRect().height));
              // REGOLA: i blocchi sulla stessa fila hanno la stessa altezza e lo stesso bordo inferiore
              const storti=[];document.querySelectorAll('.griglia,.striscia,.binari,.mappa').forEach(g=>{const righe={};[...g.children].forEach(c=>{const b=(c.matches('li')?c.firstElementChild:c).getBoundingClientRect();if(!b.height)return;const k=Math.round(b.top);(righe[k]=righe[k]||[]).push([Math.round(b.height),Math.round(b.bottom)])});
                const tutte=Object.values(righe).flat();if(new Set(tutte.map(x=>x[0])).size>1)storti.push(g.className+': altezze '+[...new Set(tutte.map(x=>x[0]))].join('/'));
                Object.values(righe).forEach(rg=>{if(new Set(rg.map(x=>x[1])).size>1)storti.push(g.className+': bordi inferiori non allineati')})});
              document.querySelectorAll('.striscia a, .scheda strong').forEach(x=>{if(x.scrollWidth>x.clientWidth+1)storti.push('testo tagliato: '+x.textContent.trim().slice(0,24))});
              return {sw:document.documentElement.scrollWidth,W,fuori,picc,storti}}''')
            if r['sw'] > r['W'] or r['fuori'] or r['picc'] or r['storti'] or err: guai += 1; print(nome, et, json.dumps(r, ensure_ascii=False), err)
            pg.close()
    b.close()
print('pagine con problemi:', guai); sys.exit(1 if guai else 0)
