#!/usr/bin/env python3
"""Rigenera «Il programma in una pagina» in PDF dalla pagina del sito già costruita.
Va rilanciato ogni volta che cambia un pilastro: il PDF scaricabile non si aggiorna da solo.
Si lancia con: python3 strumenti/programma_pdf.py
"""
import pathlib, subprocess, sys, threading, http.server, functools

QUI = pathlib.Path(__file__).resolve().parent.parent
OUT = QUI / 'pubblico'
ARRIVO = QUI / 'risorse' / 'materiali' / 'SA-programma-in-una-pagina.pdf'

if not (OUT / 'programma' / 'tutto.html').exists():
    raise SystemExit('Prima costruisci il sito: python3 costruisci.py')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit('Serve Playwright: pip install playwright --break-system-packages && playwright install chromium')

gestore = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 8931), gestore)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto('http://127.0.0.1:8931/programma/tutto.html')
        pg.wait_for_timeout(1500)
        pg.pdf(path=str(ARRIVO), format='A4', print_background=True,
               margin={'top': '14mm', 'bottom': '18mm', 'left': '15mm', 'right': '15mm'})
        b.close()
finally:
    server.shutdown()
print(f'{ARRIVO.name}: {ARRIVO.stat().st_size // 1024} KB')
