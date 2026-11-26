#!/usr/bin/env python3
"""REGOLA DELLE SCHERMATE: su computer ogni blocco occupa esattamente una schermata e il suo contenuto ci sta tutto.
Apre ogni pagina a quattro misure di schermo e segnala i blocchi tagliati. Serve Playwright."""
import pathlib, sys, http.server, threading, functools
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(__file__).parent.parent / 'pubblico'
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8811), functools.partial(H, directory=str(OUT))); threading.Thread(target=srv.serve_forever, daemon=True).start()
guai = 0; contate = 0
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--no-sandbox'])
    for w, h in [(1440, 900), (1280, 720), (1920, 1080), (1366, 768)]:
        pg = b.new_page(viewport={'width': w, 'height': h})
        for f in sorted(OUT.rglob('*.html')):
            nome = str(f.relative_to(OUT))
            if nome == '404.html': continue
            pg.goto('http://127.0.0.1:8811/' + nome); pg.wait_for_timeout(120)
            r = pg.evaluate('''()=>{const hh=document.querySelector('.testata').getBoundingClientRect().height, disp=innerHeight-hh, out=[];let n=0;
              document.querySelectorAll('.schermo, .schermo-a').forEach((s,i)=>{n++;const libero=s.classList.contains('libero');const r=s.getBoundingClientRect();
                if(!libero&&Math.abs(r.height-disp)>1)out.push('schermata '+(i+1)+': alta '+Math.round(r.height)+' invece di '+Math.round(disp));
                if(!libero){const c=s.querySelector('.in')||s;const fuori=[...c.querySelectorAll('*')].filter(e=>{if(e.closest('.scorre'))return false;const q=e.getBoundingClientRect();return q.height>0&&(q.bottom>r.bottom+1||q.top<r.top-1)});
                  if(fuori.length)out.push('schermata '+(i+1)+' ('+s.className.replace('schermo','').trim()+'): contenuto tagliato → '+fuori[0].tagName+'.'+fuori[0].className+' «'+(fuori[0].textContent||'').trim().slice(0,30)+'» di '+Math.round(Math.max(...fuori.map(e=>e.getBoundingClientRect().bottom))-r.bottom)+'px')}});
              const altri=[...document.querySelectorAll('main > *')].filter(e=>!e.matches('.schermo, .schermo-a')).map(e=>e.tagName+'.'+e.className);if(altri.length)out.push('blocchi fuori dalle schermate: '+altri.join(', '));
              return {n,out}}''')
            contate += r['n']
            for x in r['out']: guai += 1; print(f'{w}x{h}', nome, '·', x)
        pg.close()
    b.close()
print(f'schermate controllate: {contate} · problemi: {guai}'); sys.exit(1 if guai else 0)
