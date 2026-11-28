"""Il guscio di ogni pagina: testata, menù, briciole, piede, dati per i motori di ricerca.

Chi lavora al sito quasi mai deve aprire questo file: qui c'è ciò che tutte le pagine
hanno in comune. `costruisci.py` lo accende una volta con `configura(...)` e poi chiama
`pagina(...)` per ciascuna pagina.
"""
import datetime, hashlib, json, pathlib

from .testi import e, sa
from .impagina import icona

def impronta(file):
    """Le prime otto cifre dell'impronta del file.

    Il foglio di stile e il copione si chiamano sempre allo stesso modo: senza un pezzo
    che cambia, il browser di chi è già stato sul sito continua a usare la copia vecchia.
    Legarlo al contenuto, e non al numero di versione scritto a mano, toglie di mezzo
    l'errore umano: se il file cambia, l'indirizzo cambia; se non cambia, resta in cache.
    """
    return hashlib.sha256(file.read_bytes()).hexdigest()[:8] if file.exists() else '0'


def configura(**valori):
    """Accende il guscio con i dati e le funzioni del sito.

    Va chiamata una volta sola, da `costruisci.py`, prima della prima pagina. I valori
    diventano nomi di questo modulo: è il modo più diretto per tenere il corpo delle
    funzioni qui sotto identico a quando stavano dentro il generatore, senza passare
    dieci parametri a ogni chiamata.
    """
    globals().update(valori)
    globals()['ST'] = valori['SITO'].get('statistiche', {})
    globals()['COOKIE_ATTIVI'] = bool(ST.get('google_analytics') or ST.get('meta_pixel'))
    ris = valori['RIS']
    globals()['V_CSS'] = impronta(ris / 'stile.css')
    globals()['V_JS'] = impronta(ris / 'sito.js')


def misure(r):
    """Strumenti di misura: nulla se non sono configurati. Quelli con cookie partono solo dopo il consenso (sito.js)."""
    if not (ST.get('goatcounter') or COOKIE_ATTIVI):
        return ''
    return '<script type="application/json" id="sa-misure">' + json.dumps({'gc': ST.get('goatcounter', ''), 'ga': ST.get('google_analytics', ''), 'fb': ST.get('meta_pixel', ''), 'r': r}) + '</script>\n'


def pagina(percorso, titolo, descrizione, corpo, sezione='', briciole=None, og='generale', tipo='website', dati=None, ricerca=None, immagine=None):
    """Scrive una pagina completa: testata, briciole, contenuto, piede. `percorso` è relativo alla radice del sito."""
    r = '../' * percorso.count('/')
    voci = ''.join(f'<a href="{r}{h}"' + (' aria-current="page"' if h.split('/')[0].replace('.html', '') == sezione else '') + f'>{t}</a>' for h, t in MENU)
    bric = ''
    if briciole:
        bric = '<nav class="briciole" aria-label="Percorso"><ol>' + f'<li><a href="{r}index.html">Home</a></li>' + ''.join(f'<li><a href="{r}{h}">{e(t)}</a></li>' if h else f'<li aria-current="page">{e(t)}</li>' for h, t in briciole) + '</ol></nav>'
    c = SITO['contatti']
    titolo_pieno = f"{(ricerca or (titolo, ''))[0]} | {SITO['nome']}" if percorso != 'index.html' else f"{SITO['nome']} — Sicilia, Regionali 2027"
    if ricerca and ricerca[1]: descrizione_r = ricerca[1]
    else: descrizione_r = descrizione
    grafo = [dati] if dati else []
    if briciole:
        grafo.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': BASE}] + [{'@type': 'ListItem', 'position': i + 2, 'name': t, 'item': BASE + (h or percorso)} for i, (h, t) in enumerate(briciole)]})
    if immagine:
        grafo.append({'@context': 'https://schema.org', '@type': 'ImageObject', 'contentUrl': BASE + 'risorse/img/' + immagine['file'] + '.jpg', 'name': immagine['soggetto'], 'creditText': immagine['autore'], 'creator': {'@type': 'Person' if immagine['autore'] != 'Commissione europea' else 'Organization', 'name': immagine['autore']}, 'license': immagine['licenza_url'], 'acquireLicensePage': BASE + 'crediti.html'})
    invia = SITO['modulo'].get('invia_a', '') or ''
    invia = invia.split('/')[0] + '//' + invia.split('/')[2] if invia.startswith('http') else ''
    verifica = f'<meta name="google-site-verification" content="{e(SITO["google_verifica"])}">\n' if SITO.get('google_verifica') else ''
    robot = '' if SITO['indicizzabile'] else '<meta name="robots" content="noindex, nofollow">\n'
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(g, ensure_ascii=False)}</script>\n' for g in grafo)
    pagina_html = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<script>document.documentElement.className = "js";</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; form-action 'self' {invia}; base-uri 'none'; connect-src 'self' {invia}">
<meta name="referrer" content="strict-origin-when-cross-origin">
{robot}{verifica}<title>{e(titolo_pieno)}</title>
<meta name="description" content="{e(descrizione_r)}">
<link rel="canonical" href="{BASE}{'' if percorso == 'index.html' else percorso}">
<meta property="og:type" content="{tipo}">
<meta property="og:site_name" content="{e(SITO['nome'])}">
<meta property="og:title" content="{e(titolo)}">
<meta property="og:description" content="{e(descrizione)}">
<meta property="og:url" content="{BASE}{'' if percorso == 'index.html' else percorso}">
<meta property="og:image" content="{BASE}risorse/og/{og}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="it_IT">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">
<link rel="icon" href="{r}risorse/loghi/sa-icona.svg" type="image/svg+xml">
<link rel="icon" href="{r}risorse/loghi/sa-icona-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{r}risorse/loghi/sa-icona-180.png">
<link rel="manifest" href="{r}sito.webmanifest">
<link rel="alternate" type="application/rss+xml" title="Notizie" href="{r}notizie/feed.xml">
<link rel="preload" href="{r}risorse/font/montserrat-latin-900-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}risorse/stile.css?v={V_CSS}">
{ld}</head>
<body>
<a class="salta" href="#contenuto">Salta al contenuto</a>
<header class="testata">
<a class="logo" href="{r}index.html"><img src="{r}risorse/loghi/sa-logo-orizzontale.svg" alt="{e(SITO['nome_logo'])} — pagina iniziale" width="174" height="42"></a>
<button class="menu-b" type="button" aria-expanded="false" aria-controls="menu">Menù</button>
<nav class="menu" id="menu" aria-label="Principale">{voci}<a class="lente" href="{r}cerca.html" title="Cerca nel sito">{icona('lente')}<span>Cerca nel sito</span></a><a class="btn" href="{r}aderisci.html">Aderisci</a></nav>
</header>
{bric}
<main id="contenuto">
{corpo.replace('{r}', r)}
</main>
<footer class="piede schermo">
<div class="in">
<div><img class="logo-f" src="{r}risorse/loghi/sa-logo-orizzontale-negativo-su-nero.svg" alt="{e(SITO['nome_logo'])}" width="330" height="80"><p class="piede-desc">{e(SITO['descrizione'])}</p></div>
<div><h2>Altre pagine</h2><ul><li><a href="{r}metodo.html">Come lavoriamo</a></li><li><a href="{r}materiali.html">Materiali da scaricare</a></li><li><a href="{r}notizie/feed.xml">Notizie in RSS</a></li></ul></div>
{voci_contatto([('', c.get('email')), ('', c.get('telefono')), ('', c.get('sede'))], 'Contatti')}
{voci_contatto([('Facebook — ', c.get('facebook')), ('Instagram — ', c.get('instagram'))], 'Seguici')}
<div class="fondo"><span>Committente responsabile: {e(SITO['committente'])} · <a href="{r}privacy.html">Informativa privacy</a> · <a href="{r}note-legali.html">Note legali</a> · <a href="{r}cookie.html">Cookie</a> · <a href="{r}crediti.html">Crediti fotografici</a>{icone_da_terzi()}</span>
{'<span>Bozza: i contatti del coordinamento non sono ancora pubblicati e il programma attende il voto dell’assemblea.</span>' if AVVISO_BOZZA else ''}
<span class="ver">Versione {SITO['versione']} · aggiornato il {data_estesa(OGGI)}</span></div>
</div>
</footer>
{'<div class="bozza" aria-hidden="true">' + ('ANTEPRIMA PRIVATA · CON BOZZE' if ANTEPRIMA else 'BOZZA DIMOSTRATIVA') + '</div>' if AVVISO_BOZZA or ANTEPRIMA else ''}
{misure(r)}<script src="{r}risorse/sito.js?v={V_JS}" defer></script>
</body>
</html>
'''
    f = OUT / percorso
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(pagina_html, encoding='utf-8')
    PAGINE_FATTE.append(percorso)
