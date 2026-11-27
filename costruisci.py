#!/usr/bin/env python3
"""Costruisce il sito da `contenuti/` e `risorse/` nella cartella `pubblico/`.

Solo libreria standard di Python: gira ovunque, anche nella pubblicazione automatica.
Uso:  python3 costruisci.py              (sito pubblico: i file con «bozza: sì» restano fuori)
      python3 costruisci.py --anteprima  (anteprima privata: entrano anche le bozze, con etichetta)
"""
import datetime, html, json, urllib.parse, pathlib, re, shutil, sys, unicodedata
import yaml

QUI = pathlib.Path(__file__).parent
CONT, RIS, OUT = QUI / 'contenuti', QUI / 'risorse', QUI / 'pubblico'
SITO = json.loads((CONT / 'sito.json').read_text(encoding='utf-8'))
BASE = SITO['indirizzo'].rstrip('/') + '/'
OGGI = datetime.date.today()
ANTEPRIMA = '--anteprima' in sys.argv
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
MESI3 = ['GEN', 'FEB', 'MAR', 'APR', 'MAG', 'GIU', 'LUG', 'AGO', 'SET', 'OTT', 'NOV', 'DIC']
PROVINCE = ['Agrigento', 'Caltanissetta', 'Catania', 'Enna', 'Messina', 'Palermo', 'Ragusa', 'Siracusa', 'Trapani']
SIGLE = [('TP', 'Trapani', ''), ('PA', 'Palermo', ''), ('ME', 'Messina', 'me'), ('AG', 'Agrigento', ''), ('CL', 'Caltanissetta', ''), ('EN', 'Enna', ''), ('CT', 'Catania', ''), ('RG', 'Ragusa', 'rg'), ('SR', 'Siracusa', '')]
e = html.escape


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def data_estesa(d):
    return f'{d.day} {MESI[d.month - 1]} {d.year}'


# ---------- lettura dei contenuti ----------
def leggi(percorso):
    """Un file di contenuto: intestazione `chiave: valore` fra due righe `---`, poi il testo."""
    t = percorso.read_text(encoding='utf-8')
    m = re.match(r'---\n(.*?)\n---\n?(.*)', t, re.S)
    if not m:
        raise SystemExit(f'ERRORE in {percorso.name}: manca l’intestazione fra le righe ---')
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as errore:
        raise SystemExit(f'ERRORE in {percorso.name}: intestazione non leggibile · {errore}')
    if not isinstance(meta, dict):
        raise SystemExit(f'ERRORE in {percorso.name}: l’intestazione deve essere un elenco di «chiave: valore»')
    meta = {k: ('' if v is None else (v.isoformat() if hasattr(v, 'isoformat') else str(v))) for k, v in meta.items()}
    meta['corpo'], meta['file'] = m.group(2).strip(), percorso.stem
    meta['esempio'] = meta.get('esempio', '').lower() in ('sì', 'si', 'vero', 'true')
    meta['bozza'] = meta.get('bozza', '').lower() in ('sì', 'si', 'vero', 'true')
    if 'data' in meta:
        try:
            meta['giorno'] = datetime.date.fromisoformat(meta['data'])
        except ValueError:
            raise SystemExit(f'ERRORE in {percorso.name}: la data deve essere scritta come 2026-12-05')
    return meta


ESCLUSE = []


def cartella(nome):
    tutte = [leggi(p) for p in sorted((CONT / nome).glob('*.md'))]
    ESCLUSE.extend(f'{nome}/{x["file"]}' for x in tutte if x['bozza'] and not ANTEPRIMA)
    return [x for x in tutte if ANTEPRIMA or not x['bozza']]


def sezioni(md):
    """Divide un testo nei suoi capitoli `## Titolo`: restituisce [(titolo, testo), ...]; il primo può avere titolo vuoto."""
    parti = re.split(r'^## (.+)$', md, flags=re.M)
    out = [('', parti[0].strip())] if parti[0].strip() else []
    return out + [(parti[i].strip(), parti[i + 1].strip()) for i in range(1, len(parti), 2)]


def in_linea(s):
    s = e(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|[^)\s]+\.html[^)\s]*)\)', lambda m: f'<a href="{m.group(2)}"' + (' rel="noopener"' if m.group(2).startswith('http') else '') + f'>{m.group(1)}</a>', s)


def cifre(righe):
    """Numeri in evidenza. Una riga per numero: `= numero | che cosa dice | da dove viene`.
    Il numero è già scritto per intero nella pagina: il conteggio che sale è solo un ornamento di chi ha il
    browser acceso, e chi ha chiesto meno animazioni lo vede fermo."""
    voci = []
    for r in righe:
        parti = [x.strip() for x in r.lstrip()[2:].split('|')]
        numero = in_linea(parti[0])
        detto = in_linea(parti[1]) if len(parti) > 1 else ''
        fonte = in_linea(parti[2]) if len(parti) > 2 else ''
        voci.append(f'<li><strong data-conta>{numero}</strong><span>{detto}</span>'
                    + (f'<small>{fonte}</small>' if fonte else '') + '</li>')
    return '<ul class="cifre riv">' + ''.join(voci) + '</ul>'


def testo(md):
    """Testo semplice: righe vuote separano i capoversi, `## ` titolo, `### ` sottotitolo, `- ` elenco,
    `= numero | che cosa dice | fonte` numeri in evidenza, **grassetto**, [testo](indirizzo)."""
    out = []
    for blocco in re.split(r'\n\s*\n', md.strip()):
        righe = [r for r in blocco.strip().splitlines() if r.strip()]
        if not righe:
            continue
        if righe[0].startswith('### '):
            out.append(f'<h3>{in_linea(righe[0][4:])}</h3>')
        elif righe[0].startswith('## '):
            out.append(f'<h2>{sa(in_linea(righe[0][3:]))}</h2>')
        elif all(r.lstrip().startswith('= ') for r in righe):
            out.append(cifre(righe))
        elif all(r.lstrip().startswith('- ') for r in righe):
            out.append('<ul>' + ''.join(f'<li>{in_linea(r.lstrip()[2:])}</li>' for r in righe) + '</ul>')
        else:
            out.append(f'<p>{in_linea(" ".join(r.strip() for r in righe))}</p>')
    return '\n'.join(out)


PILASTRI = cartella('pilastri')
MATERIALI = json.loads((CONT / 'materiali.json').read_text(encoding='utf-8'))
NOTIZIE = sorted(cartella('notizie'), key=lambda n: n['giorno'], reverse=True)
EVENTI = sorted(cartella('agenda'), key=lambda n: n['giorno'])
TERRITORI = {t['titolo']: t for t in cartella('territori')}
PAGINE = {p['file']: p for p in cartella('pagine')}
for p in PILASTRI:
    p['indirizzo'] = f"programma/{slug(p['titolo'])}.html"
for n in NOTIZIE:
    n['indirizzo'] = f"notizie/{n['file']}.html"
    n['quando'] = n.get('data_testo') or data_estesa(n['giorno'])
for v in EVENTI:
    v['indirizzo'] = f"agenda/{v['file']}.html"
    v['passato'] = v['giorno'] < OGGI
for nome, t in TERRITORI.items():
    t['indirizzo'] = f'territori/{slug(nome)}.html'
FUTURI = [v for v in EVENTI if not v['passato']]
def sa(t, variante=''):
    """REGOLA DEL SITO: «la Sicilia (che) SA …» si scrive con il monogramma al posto della parola. `variante`: '' su chiaro, 'nero' su fondo nero, 'rosso' su fondo rosso."""
    file = {'': 'sa-monogramma.svg', 'nero': 'sa-monogramma-negativo-su-nero.svg', 'rosso': 'sa-monogramma-bianco.svg'}[variante]
    return re.sub(r'(?i)(sicilia)(\s+che)?\s+sa\b', lambda m: (f'{m.group(1)} <span class="nsa">che ' if m.group(2) else f'<span class="nsa">{m.group(1)} ') + f'<img class="sa" src="{{r}}risorse/loghi/{file}" alt="SA" width="65" height="42"></span>', t)


CONTATTI = SITO['contatti']
AVVISO_BOZZA = bool(SITO.get('avviso_bozza', SITO.get('bozza')))


def pronto_per_il_definitivo():
    """Quando qualcuno mette «bozza: false» il sito smette di dire che è una bozza, toglie l'etichetta
    e si fa indicizzare. Se in quel momento mancano i dati veri, la costruzione si ferma: è l'unico modo
    perché nessuno pubblichi come definitivo un sito con i contatti vuoti o il committente non indicato."""
    if SITO.get('bozza'):
        return
    g = SITO.get('legale', {})
    manca = []
    if not CONTATTI.get('email'):
        manca.append('contatti.email')
    if not SITO.get('committente') or 'da indicare' in SITO['committente']:
        manca.append('committente')
    for k in ('titolare', 'sede_titolare', 'incaricati', 'servizio_modulo', 'conservazione'):
        if not g.get(k):
            manca.append('legale.' + k)
    if not SITO.get('modulo', {}).get('invia_a'):
        manca.append('modulo.invia_a')
    esempi = [x.get('titolo', '?') for x in list(NOTIZIE) + list(TERRITORI.values()) + list(EVENTI) if x.get('esempio')]
    if esempi:
        manca.append('contenuti ancora segnati «esempio»: ' + ', '.join(esempi))
    if manca:
        raise SystemExit('ERRORE: «bozza» è stata messa a false ma mancano ancora:\n  - '
                         + '\n  - '.join(manca)
                         + '\nRimetti «bozza»: true oppure completa queste voci in contenuti/sito.json.')


def ics_testo(s):
    """Nel formato dei calendari la virgola, il punto e virgola e la barra rovesciata vanno protetti,
    altrimenti l'appuntamento arriva troncato."""
    return str(s).replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')


def google_calendario(v, inizio, fine, con_ora):
    """Collegamento che apre Google Calendar con l'appuntamento già compilato. È solo un collegamento:
    non carica niente di Google nel sito e non lascia cookie finché non lo si clicca."""
    q = {'action': 'TEMPLATE', 'text': v['titolo'], 'dates': inizio + '/' + fine,
         'details': f"{SITO['nome']} · {BASE}{v['indirizzo']}", 'location': v.get('luogo', '')}
    if con_ora:
        q['ctz'] = 'Europe/Rome'
    return 'https://calendar.google.com/calendar/render?' + urllib.parse.urlencode(q)


def voci_contatto(coppie, titolo):
    """Colonna del piede: salta le voci vuote e sparisce del tutto se non ne resta nessuna."""
    righe = ''.join(f'<li>{p}{e(v)}</li>' for p, v in coppie if v)
    return f'<div><h2>{titolo}</h2><ul>{righe}</ul></div>' if righe else ''


def elenco_contatti():
    """Pagina Contatti: mostra solo quello che esiste davvero."""
    etichette = [('Email', 'email'), ('Telefono', 'telefono'), ('Sede', 'sede'),
                 ('Facebook', 'facebook'), ('Instagram', 'instagram')]
    righe = ''.join(f'<dt>{n}</dt><dd>{e(CONTATTI[k])}</dd>' for n, k in etichette if CONTATTI.get(k))
    return f'<dl class="elenco">{righe}</dl>' if righe else ''


ES = ' <em class="es">esempio</em>'
BZ = ' <em class="es bz">bozza non pubblica</em>'


def segni(x):
    return (ES if x['esempio'] else '') + (BZ if x.get('bozza') else '')

# ---------- parti comuni ----------
MENU = [('chi-siamo.html', 'Chi siamo'), ('programma/index.html', 'Programma'), ('notizie/index.html', 'Notizie'), ('agenda/index.html', 'Agenda'), ('territori/index.html', 'Territori'), ('contatti.html', 'Contatti')]
PAGINE_FATTE = []


ST = SITO.get('statistiche', {})
COOKIE_ATTIVI = bool(ST.get('google_analytics') or ST.get('meta_pixel'))


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
<link rel="stylesheet" href="{r}risorse/stile.css?v={SITO['versione']}">
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
{misure(r)}<script src="{r}risorse/sito.js?v={SITO['versione']}" defer></script>
</body>
</html>
'''
    f = OUT / percorso
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(pagina_html, encoding='utf-8')
    PAGINE_FATTE.append(percorso)


def intesta(occhiello, titolo, sotto=''):
    return f'<div class="intesta"><div class="in"><h1>{sa(titolo)}</h1>' + (f'<p class="sott">{sotto}</p>' if sotto else '') + '</div></div>'


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'strumenti'))
import ottimizza_foto
ottimizza_foto.ottimizza(pathlib.Path(__file__).resolve().parent / 'risorse' / 'img')  # regola 8
FOTO = {f['file']: f for f in json.loads((CONT / 'foto.json').read_text(encoding='utf-8'))}
def crediti_da_contenuto(v, file):
    """Se chi scrive ha compilato autore e licenza nel pannello, valgono quelli: foto.json resta per le foto già a posto."""
    if v.get('foto_autore') and v.get('foto_licenza'):
        FOTO[file] = {'file': file, 'commons': v.get('foto_origine', ''), 'soggetto': v.get('foto_soggetto') or v.get('titolo', ''),
                      'autore': v['foto_autore'], 'anno': v.get('foto_anno', ''), 'licenza': v['foto_licenza'],
                      'licenza_url': v.get('foto_licenza_url', '')}


for _n in NOTIZIE:
    crediti_da_contenuto(_n, _n['file'])
for _p in PILASTRI:
    crediti_da_contenuto(_p, 'pilastro-' + _p['numero'])


IMG = pathlib.Path(__file__).resolve().parent / 'risorse' / 'img'


def foto(file, attesa, extra=''):
    """Spazio per una fotografia: mostra `risorse/img/<file>.jpg` se c'è, altrimenti il segnaposto con il nome atteso.
    Quando c'è anche la copia da 700 px, il browser scarica quella se lo schermo è piccolo (regola 8)."""
    c = FOTO.get(file)
    if c:
        primo = ' fetchpriority="high"' if 'grande' in extra else ' loading="lazy"'
        v = SITO['versione']
        misure = ''
        if (IMG / f'{file}-700.jpg').exists():
            larga = '1180px' if 'grande' in extra else '390px'
            misure = (f' srcset="{{r}}risorse/img/{file}-700.jpg?v={v} 700w, {{r}}risorse/img/{file}.jpg?v={v} 1400w"'
                      f' sizes="(min-width: 1000px) {larga}, 100vw"')
        return f'<figure class="foto{extra}{" riv" if "grande" in extra else ""}"><img src="{{r}}risorse/img/{file}.jpg?v={v}"{misure} alt="{e(c["soggetto"])}" width="1400" height="933" decoding="async"{primo} data-se-manca="FOTO DA INSERIRE · risorse/img/{file}.jpg"></figure>'
    return f'<div class="foto vuota{extra}" data-file="{{r}}risorse/img/{file}.jpg?v={SITO["versione"]}" data-et="FOTO DA INSERIRE · {e(attesa)} · risorse/img/{file}.jpg" role="img" aria-label="{e(attesa)}"></div>'


def scheda_notizia(n):
    return f'''<li><a class="scheda riv" href="{{r}}{n['indirizzo']}">{foto(n['file'], n['titolo'])}<span class="tx"><span class="quando">{n['quando']}{segni(n)}</span><strong>{e(n['titolo'])}</strong><p>{e(n.get('sintesi', ''))}</p><span class="vai">Leggi →</span></span></a></li>'''


def riga_evento(v, calendario=True):
    """Riga dell'agenda. Accanto agli incontri futuri c'è il segnaposto per il calendario: il file si
    scarica e l'appuntamento entra nel calendario del telefono o del computer, con l'avviso il giorno prima."""
    d = v['giorno']
    cal = ''
    if calendario and not v['passato']:
        cal = (f'<a class="cal" href="{{r}}agenda/{v["file"]}.ics" download '
               f'aria-label="Salva nel calendario: {e(v["titolo"])}" title="Salva nel calendario">'
               f'{icona("calendario")}</a>')
    return (f'''<li class="ev"><a class="evento{' passato' if v['passato'] else ''}" href="{{r}}{v['indirizzo']}">'''
            f'''<span class="d"><b>{d.day:02d}</b><small>{MESI3[d.month - 1]} {d.year}</small></span>'''
            f'''<span><strong>{e(v['titolo'])}</strong><span>{e(v.get('luogo', ''))}'''
            f'''{' · ore ' + v['ora'] if v.get('ora') else ''}{' · già svolto' if v['passato'] else ''}'''
            f'''{segni(v)}</span></span></a>{cal}</li>''')


def striscia():
    return '<ol class="striscia">' + ''.join(f'''<li><a href="{{r}}{p['indirizzo']}"><i>{p['numero']}</i>{e(p['titolo'])}</a></li>''' for p in PILASTRI) + '</ol>'


def banda_aderisci(titolo='Il programma si scrive ai tavoli', testo_='Comitati, collettivi, sindacati, singole e singoli: lascia i tuoi contatti, ti scriviamo per gli incontri nel tuo territorio.', q=''):
    return f'<section class="sez su-rosso"><div class="in alto"><h2>{sa(titolo, "rosso")}</h2><p class="largo36">{testo_}</p><a class="btn bw" href="{{r}}aderisci.html{q}">Aderisci ora</a></div></section>'


def mappa(corrente=''):
    """Le nove province come blocchi uguali, in ordine alfabetico (stessa forma della fascia dei pilastri)."""
    sigla = {p: sg for sg, p, _ in SIGLE}
    return '<ol class="striscia province">' + ''.join(f'''<li><a href="{{r}}{TERRITORI[p]['indirizzo']}"{' aria-current="page"' if p == corrente else ''}><i>{sigla[p]}</i>{e(p)}</a></li>''' for p in PROVINCE if p in TERRITORI) + '</ol>'


# ---------- costruzione ----------
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(RIS, OUT / 'risorse')
# Il pannello di scrittura viene copiato così com'è: non è una pagina del sito, non entra
# nel menù, non va nella mappa del sito e non è indicizzabile.
if (QUI / 'admin').exists():
    shutil.copytree(QUI / 'admin', OUT / 'admin')
(OUT / '.nojekyll').write_text('')

# ====================================================================================================
# REGOLA DELLE SCHERMATE: ogni pagina è fatta di blocchi grandi quanto lo schermo (su computer).
# Ogni `S(...)` è una schermata intera: quando la pagina si ferma, nessun blocco resta tagliato.
# Unica eccezione dichiarata: `LIBERO(...)`, per il testo lungo di una notizia e per la pagina da stampare.
# ====================================================================================================
def S(dentro, classe=''):
    return f'<section class="schermo {classe}"><div class="in">{dentro}</div></section>'


def LIBERO(dentro):
    return f'<section class="schermo libero"><div class="in">{dentro}</div></section>'


# Pittogrammi nostri, disegnati qui: dicono l'azione, non il marchio. I loghi di WhatsApp, Telegram e
# Facebook sono marchi registrati e non si riproducono, nemmeno ridisegnati.
ICONE = {
    'bolla': '<path d="M2 3h20v13h-9l-7 5v-5H2Z"/>',
    'invio': '<path d="m12 1 7 8h-5v7h-4V9H5Z"/><path d="M3 13h4v5h10v-5h4v9H3Z"/>',
    'megafono': '<path d="M2 9h5l12-6v18L7 15H2Z"/><path d="M7 15h3.4l1.2 7H8.2Z"/>',
    'busta': '<path fill-rule="evenodd" d="M2 4h20v16H2Zm2 3v10h16V7l-8 6Z"/>',
    'catena': '<path fill-rule="evenodd" d="M1 7h22v10H1Zm3 3v4h5v-4Zm11 0v4h5v-4ZM10.5 7h3v3h-3Zm0 7h3v3h-3Z"/>',
    'lente': '<path fill-rule="evenodd" d="M10.5 1a9.5 9.5 0 1 0 5.6 17.2l5.1 5.1 2.1-2.1-5.1-5.1A9.5 9.5 0 0 0 10.5 1Zm0 3a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13Z"/>',
    'calendario': '<path fill-rule="evenodd" d="M6 1h3v2h6V1h3v2h4v20H2V3h4Zm14 7H4v13h16Zm-13 3h4v4H7Z"/>',
}


def icona(nome):
    """Pieno, non filettato: il segno deve avere la stessa massa dei caratteri del sito e gli stessi angoli vivi.
    Il colore lo eredita dal pulsante, così sul fondo nero diventa bianco da sé."""
    return (f'<svg class="ic" viewBox="0 0 24 24" width="20" height="20" fill="currentColor" '
            f'aria-hidden="true" focusable="false">{ICONE[nome]}</svg>')


SERVIZI = pathlib.Path(__file__).resolve().parent / 'risorse' / 'loghi' / 'servizi'


def icone_da_terzi():
    """Se qualcuno ha caricato i loghi dei servizi, la licenza di chi li distribuisce può chiedere un credito
    nel piede su ogni pagina che li usa. La nota compare da sola e sparisce da sola."""
    if not SERVIZI.exists() or not any(SERVIZI.glob('*.svg')):
        return ''
    fonte = SITO.get('icone_fonte') or {}
    if not fonte.get('nome') or not fonte.get('indirizzo'):
        return ''
    return (f' · Icone dei servizi di condivisione: <a href="{e(fonte["indirizzo"])}" target="_blank"'
            f' rel="noopener">{e(fonte["nome"])}</a>')


def segno_ufficiale(marchio):
    """Se in `risorse/loghi/servizi/` c'è `<servizio>.svg`, il sito usa quello al posto del nostro pittogramma.
    Va messa la versione a un colore solo: il sito la usa come sagoma e le dà lui il colore del pulsante,
    così diventa bianca sul fondo nero come tutte le altre icone.
    I file li mette chi ha deciso di usarli, scaricandoli dalle pagine ufficiali dei marchi e rispettandone
    le condizioni d'uso: non si ridisegnano e non si prendono da altre fonti."""
    if not marchio or not (SERVIZI / f'{marchio}.svg').exists():
        return ''
    return f'<span class="ic ic-m ic-{marchio}" aria-hidden="true"></span>'


def condividi(titolo, percorso):
    """Pulsanti per mandare la pagina ad altri. Solo collegamenti: nessuno script di terze parti, nessun cookie.
    I pittogrammi sono nostri e descrivono il gesto; il nome del servizio resta scritto, perché un'icona sola
    si legge male e chi usa il lettore di schermo non la sente."""
    u = urllib.parse.quote(BASE + percorso, safe='')
    t = urllib.parse.quote(titolo + ' — ' + SITO['nome'], safe='')
    vie = [('WhatsApp', 'whatsapp', 'bolla', f'https://wa.me/?text={t}%20{u}'),
           ('Telegram', 'telegram', 'invio', f'https://t.me/share/url?url={u}&text={t}'),
           ('Facebook', 'facebook', 'megafono', f'https://www.facebook.com/sharer/sharer.php?u={u}'),
           ('Email', '', 'busta', f'mailto:?subject={t}&body={u}')]
    link = ''
    for n, marchio, ic, v in vie:
        link += f'<a href="{v}" target="_blank" rel="noopener">{segno_ufficiale(marchio) or icona(ic)}<span>{n}</span></a>'
    copia = f'<button type="button" data-copia="{e(BASE + percorso)}">{icona("catena")}<span>Copia il link</span></button>'
    return f'<div class="condividi"><span class="k">Condividi</span>{link}{copia}</div>'


PAROLE = {1: 'uno', 2: 'due', 3: 'tre', 4: 'quattro', 5: 'cinque', 6: 'sei', 7: 'sette', 8: 'otto', 9: 'nove', 10: 'dieci'}


def testa_numerata(numero, quanti, cosa, titolo, sotto=''):
    """Testa con il numero grande, da manifesto: la cifra è il segno, non un sopratitolo in maiuscolo."""
    quanti_ = PAROLE.get(quanti, str(quanti))
    return (f'<header class="capo-p numerata riv"><p class="ordinale"><b>{e(numero)}</b>'
            f'<i>{e(cosa)}<br>di {quanti_}</i></p><h1>{sa(titolo)}</h1>'
            + (f'<p class="sott">{sotto}</p>' if sotto else '') + '</header>')


def testa(occhiello, titolo, sotto=''):
    """Niente sopratitolo: la briciola in cima e la voce accesa nel menù dicono già la sezione, e la
    micro-etichetta maiuscola sopra ogni titolo è la cosa che fa sembrare uguali tutte le pagine.
    L'`occhiello` resta nella firma perché è il nome della sezione e lo usa chi chiama."""
    return f'<header class="capo-p riv"><h1>{sa(titolo)}</h1>' + (f'<p class="sott">{sotto}</p>' if sotto else '') + '</header>'


def a_gruppi(lista, n):
    return [lista[i:i + n] for i in range(0, len(lista), n)]


ADERISCI = S(f'<h2>{sa("Il programma si scrive ai tavoli", "rosso")}</h2><p class="sott">Comitati, collettivi, sindacati, singole e singoli: lascia i tuoi contatti, ti scriviamo per gli incontri nel tuo territorio.</p><div class="azioni"><a class="btn bw" href="{{r}}aderisci.html">Aderisci ora</a></div>', 'su-rosso centro')


def aderisci_con(titolo, riga, q=''):
    return S(f'<h2>{sa(titolo, "rosso")}</h2><p class="sott">{riga}</p><div class="azioni"><a class="btn bw" href="{{r}}aderisci.html{q}">Aderisci ora</a></div>', 'su-rosso centro')


# I numeri in evidenza: scritti in «Chi siamo», mostrati anche in apertura
CHI = PAGINE['chi-siamo']
SZ_CHI = dict(sezioni(CHI['corpo']))
NUMERI = testo(SZ_CHI.get('I numeri', ''))

# Home
verbi = ''.join(f"<li>{e(p['verbo'])}</li>" for p in PILASTRI)
prossimo = ''
if FUTURI:
    v = FUTURI[0]
    prossimo = f'''<div class="prossimo riquadro-nero"><div><span class="k">Prossimo incontro</span><h2>{e(v['titolo'])}{segni(v)}</h2><p class="quando">{data_estesa(v['giorno'])}{' · ore ' + v['ora'] if v.get('ora') else ''} · {e(v.get('luogo', ''))}</p></div><a class="btn" href="{{r}}{v['indirizzo']}">Tutti i dettagli</a></div>'''
def striscia_pilastri(corrente=None):
    """I sette pilastri in fila: dalla home e da dentro ogni pilastro, per saltare dove si vuole
    senza tornare all'indice. Quello in cui sei è segnato."""
    voci = ''
    for x in PILASTRI:
        qui = ' aria-current="page"' if x['numero'] == corrente else ''
        voci += (f'<li><a href="{{r}}{x["indirizzo"]}"{qui}><i>{x["numero"]}</i>{e(x["titolo"])}'
                 f'<small>{e(x["slogan"])}</small></a></li>')
    return f'<ol class="striscia alta riv">{voci}</ol>'


striscia_p = striscia_pilastri()
pagina('index.html', SITO['nome'], SITO['descrizione'], f'''<section class="apertura schermo-a">
<div class="sx"><h1>La Sicilia che <img src="{{r}}risorse/loghi/sa-monogramma.svg" alt="SA" width="649" height="418"></h1>
<ul class="verbi">{verbi}</ul>
<div class="azioni"><a class="btn" href="{{r}}aderisci.html">Aderisci ora</a><a class="btn b2" href="{{r}}programma/index.html">Il programma</a></div></div>
<div class="dx"><img src="{{r}}risorse/loghi/sa-contrassegno.svg" alt="Contrassegno {e(SITO['nome_logo'])}" width="430" height="430"></div>
</section>''' + S(f'<div class="capo"><div><h2>{sa("La Sicilia che sa")}</h2></div><a href="{{r}}programma/index.html">Tutto il programma →</a></div>{striscia_p}') + S(f'<div class="capo"><div><h2>Che cosa succede</h2></div><a href="{{r}}notizie/index.html">Tutte le notizie →</a></div><ul class="griglia tre">{"".join(scheda_notizia(n) for n in NOTIZIE[:3])}</ul>', 'carta') + S(f'<div class="capo"><div><h2>Perché adesso</h2></div><a href="{{r}}chi-siamo.html">Chi siamo →</a></div>{NUMERI}') + S(f'{prossimo}<div class="capo"><div><h2>Nove province, un tavolo in ognuna</h2></div><a href="{{r}}territori/index.html">Tutti i territori →</a></div>{mappa()}') + ADERISCI,
       dati={'@context': 'https://schema.org', '@type': 'Organization', 'name': SITO['nome'], 'alternateName': 'Sinistra Alternativa Sicilia', 'areaServed': 'Sicilia', 'url': BASE, 'logo': BASE + 'risorse/loghi/sa-contrassegno.png', 'description': SITO['descrizione']})

# Chi siamo
p = CHI; sz = SZ_CHI
forze = re.findall(r'^- (.*)$', sz.get('Le forze del coordinamento', ''), re.M)
oss = re.sub(r'^- .*$', '', sz.get('Le forze del coordinamento', ''), flags=re.M).strip()

SPECIALI = ('', 'I numeri', 'Le forze del coordinamento')
corpo_chi = S(f'<div class="col2">{testa(p["occhiello"], e(p["titolone"]), e(p["sintesi"]))}'
              f'<div class="testo">{testo(sz.get("", ""))}</div></div>')
# Ogni altra sezione scritta in «Chi siamo» diventa una schermata, nell'ordine in cui è scritta.
# Prima venivano buttate via in silenzio: chi scriveva dal pannello non se ne accorgeva.
for _titolo, _corpo in sezioni(p['corpo']):
    if _titolo in SPECIALI:
        continue
    # Una sezione lunga non entra in una schermata intera: va a scorrimento libero, altrimenti si taglia.
    _schermata = LIBERO if len(_corpo) > 700 else S
    corpo_chi += _schermata(f'<header class="capo-p riv"><h2>{sa(_titolo)}</h2></header>'
                            f'<div class="testo lungo">{testo(_corpo)}</div>')
    if _titolo == 'Una sola radice':
        corpo_chi += S(f'<header class="capo-p riv"><h2>I numeri</h2></header>{NUMERI}')
corpo_chi += S(f'<div class="capo"><div><h2>Le forze del coordinamento</h2></div>'
               f'<a href="{{r}}metodo.html">Come lavoriamo →</a></div>'
               f'<ul class="griglia quattro forze">'
               + ''.join(f"<li><span class=scheda><span class=tx><strong>{e(x)}</strong></span></span></li>" for x in forze)
               + '<li><a class="scheda nera" href="{r}aderisci.html"><span class="tx"><strong>Manchi tu</strong>'
                 '<span class="vai">Aderisci →</span></span></a></li></ul>'
               + f'<p class="nota">{e(oss)}</p>', 'carta')
pagina('chi-siamo.html', p['titolo'], p['sintesi'], corpo_chi + ADERISCI, 'chi-siamo', [('', 'Chi siamo')])

# Controllo: nessuna sezione scritta deve sparire dalla pagina
_mancanti = [x for x, _ in sezioni(p['corpo']) if x and x not in SPECIALI and sa(x) not in corpo_chi]
if _mancanti:
    raise SystemExit('ERRORE: sezioni di «Chi siamo» non mostrate in pagina: ' + ', '.join(_mancanti))

# Programma
schede = ''.join(f'''<li><a class="scheda pil riv" href="{{r}}{p['indirizzo']}"><span class="tx"><span class="n">{p['numero']}</span><strong>{e(p['titolo'])}</strong><p>{e(p['sintesi'])}</p><span class="vai">Le proposte →</span></span></a></li>''' for p in PILASTRI)
schede += '<li><span class="scheda pil nera"><span class="tx"><strong>Come si legge</strong><p>Ogni pilastro dice che cosa può fare la Regione subito e che cosa va strappato allo Stato.</p><a class="vai" href="{r}metodo.html">I due binari →</a><a class="vai" href="{r}programma/tutto.html">Tutto in una pagina →</a></span></span></li>'
pagina('programma/index.html', 'Il programma', 'Sette pilastri per un’alternativa popolare in Sicilia: pace, lavoro, salute, acqua, diritti, accoglienza, territorio.', S(testa('Il programma', 'La Sicilia che SA', 'Sette pilastri. Bozza in attesa di approvazione del coordinamento.') + f'<ul class="griglia quattro">{schede}</ul>', 'carta fitta') + ADERISCI, 'programma', [('', 'Programma')])
for i, p in enumerate(PILASTRI):
    prima, dopo = PILASTRI[i - 1], PILASTRI[(i + 1) % len(PILASTRI)]
    incontri = [v for v in FUTURI if v.get('pilastro') == p['numero']][:2]
    collegate = [n for n in NOTIZIE if n.get('pilastro') == p['numero']][:3]
    sz = sezioni(p['corpo'])
    # I due binari si riconoscono dal titolo, non dalla posizione: così davanti si può mettere il «Perché»
    # senza che il problema finisca al posto della proposta.
    def _quale(titolo):
        b = titolo.lower()
        if b.startswith('cosa può fare') or b.startswith('che cosa può fare'):
            return 1
        if b.startswith('cosa va strappato') or b.startswith('che cosa va strappato'):
            return 2
        return 0
    coppia = [(t, c) for t, c in sz if _quale(t)]
    coppia.sort(key=lambda x: _quale(x[0]))
    if len(coppia) != 2:
        raise SystemExit(f'ERRORE in {p["titolo"]}: servono le due sezioni dei binari '
                         f'(«Cosa può fare la Regione…» e «Cosa va strappato allo Stato»), trovate {len(coppia)}')
    primo = [x for x in sz if not _quale(x[0])][:max(0, [i for i, x in enumerate(sz) if _quale(x[0])][0])]
    dopo_binari = [x for x in sz if not _quale(x[0])][len(primo):]
    binari = ''.join(f'<div class="binario b{k}"><span class="k">{"Primo" if k == 1 else "Secondo"} binario</span><h2>{e(t)}</h2><div class="testo">{testo(c)}</div></div>' for k, (t, c) in enumerate(coppia, 1))
    resto = ''.join(f'<h2>{e(t)}</h2>{testo(c)}' for t, c in dopo_binari)
    lato = f'''<aside class="lato"><h3>Il tavolo di questo pilastro</h3><p>Aperto a comitati, collettivi, sindacati e singole persone.</p>{'<ul class="eventi">' + ''.join(riga_evento(v) for v in incontri) + '</ul>' if incontri else '<p><strong>Nessun incontro in calendario per ora.</strong></p>'}<a class="btn" href="{{r}}aderisci.html">Partecipa al tavolo</a><a class="vai-a" href="{{r}}metodo.html">Che cosa sono i due binari →</a></aside>'''
    corpo = S(f'''<div class="col2"><div class="colonna">{testa_numerata(p['numero'], len(PILASTRI), 'pilastro', e(p['titolo']), e(p['slogan']))}<p class="sintesi">{e(p['sintesi'])}</p><div class="azioni"><a class="btn" href="{{r}}aderisci.html">Partecipa al tavolo</a></div></div>{foto('pilastro-' + p['numero'], p['foto_attesa'], ' grande')}</div>''')
    for _t, _c in primo:
        corpo += (LIBERO if len(_c) > 700 else S)(
            f'<header class="capo-p riv"><h2>{sa(_t)}</h2></header><div class="testo lungo">{testo(_c)}</div>')
    # Con elenchi lunghi i due binari non entrano in una schermata: allora scorre.
    _lungo = sum(len(c) for _, c in coppia) > 1100
    corpo += (LIBERO(f'<div class="capo"><div><h2>Due binari</h2></div><a href="{{r}}metodo.html">Che cosa sono →</a></div><div class="binari">{binari}</div>')
              if _lungo else
              S(f'<div class="capo"><div><h2>Due binari</h2></div><a href="{{r}}metodo.html">Che cosa sono →</a></div><div class="binari">{binari}</div>', 'carta'))
    # Con «L'obiezione» e «Come ci arriviamo» il blocco non entra in una schermata: allora scorre.
    corpo += (LIBERO if sum(len(c) for _, c in dopo_binari) > 900 else S)(f'''<div class="due"><div class="testo">{resto}</div>{lato}</div>{condividi(p['titolo'], p['indirizzo'])}<nav class="vicini" aria-label="Altri pilastri"><a href="{{r}}{prima['indirizzo']}">← {prima['numero']} {e(prima['titolo'])}</a><a href="{{r}}{dopo['indirizzo']}">{dopo['numero']} {e(dopo['titolo'])} →</a></nav>''')
    corpo += S(f'<div class="capo"><div><h2>Gli altri pilastri</h2></div>'
               f'<a href="{{r}}programma/index.html">Tutto il programma →</a></div>'
               + striscia_pilastri(p['numero']))
    _persi = [x for x, _ in sz if sa(x) not in corpo and e(x) not in corpo]
    if _persi:
        raise SystemExit(f'ERRORE in {p["titolo"]}: sezioni non mostrate in pagina: ' + ', '.join(_persi))
    if collegate:
        corpo += S(f'<div class="capo"><div><h2>Su questo pilastro</h2></div><a href="{{r}}notizie/index.html">Tutte le notizie →</a></div><ul class="griglia tre">{"".join(scheda_notizia(n) for n in collegate)}</ul>', 'carta')
    pagina(p['indirizzo'], p['titolo'], p['sintesi'], corpo + aderisci_con(f"La Sicilia che sa {e(p['verbo'])}", 'Dai forza a questa proposta: aderisci e partecipa al tavolo.'), 'programma', [('programma/index.html', 'Programma'), ('', p['titolo'])], og='pilastro-' + p['numero'], ricerca=(p.get('titolo_ricerca'), p.get('descrizione_ricerca')) if p.get('titolo_ricerca') else None, immagine=FOTO.get('pilastro-' + p['numero']))

# Tutto il programma in una pagina sola, da stampare o salvare in PDF (eccezione dichiarata alla regola delle schermate)
tutto = ''.join(f'''<article class="blocco-p"><span class="k">Pilastro {p['numero']}</span><h2>{e(p['titolo'])}</h2><p class="sintesi">{e(p['sintesi'])}</p>{''.join(f'<h3>{e(t)}</h3><div class="testo">{testo(c)}</div>' for t, c in sezioni(p['corpo']))}</article>''' for p in PILASTRI)
# Carta intestata e riga in fondo: si vedono solo sul foglio stampato, non a schermo.
carta_intestata = ('<div class="intestata">'
                   '<img src="{r}risorse/loghi/sa-contrassegno.svg" alt="" width="150" height="150">'
                   f'<div class="chi"><strong>{e(SITO["nome"])}</strong>'
                   f'<span>Coordinamento regionale siciliano · Elezioni regionali 2027</span></div>'
                   f'<div class="dt">Programma<br><small>Bozza in discussione nei tavoli<br>{data_estesa(OGGI)}</small></div>'
                   '</div>')
pie_stampa = (f'<div class="pie-stampa"><span>{e(SITO["nome"])} · Coordinamento regionale siciliano</span>'
              f'<span>{BASE.replace("https://", "").rstrip("/")}</span></div>')
pagina('programma/tutto.html', 'Il programma completo', 'I sette pilastri in una pagina sola, da leggere di seguito o da stampare.', LIBERO(carta_intestata + testa('Il programma', 'Il programma completo', 'I sette pilastri di seguito. Bozza in attesa di approvazione del coordinamento.') + f'<div class="azioni"><button class="btn bn" type="button" data-stampa>Stampa o salva in PDF</button><a class="btn b2" href="{{r}}programma/index.html">Torna ai pilastri</a></div>{tutto}' + pie_stampa), 'programma', [('programma/index.html', 'Programma'), ('', 'Il programma completo')])

# Il metodo
p = PAGINE['metodo']; sz = sezioni(p['corpo']); d = {t: c for t, c in sz}; nomi = [t for t, _ in sz if t]
binari_m = ''.join(f'<div class="binario b{k}"><span class="k">{"Primo" if k == 1 else "Secondo"} binario</span><h2>{e(t.split(": ", 1)[-1][0].upper() + t.split(": ", 1)[-1][1:])}</h2><div class="testo">{testo(d[t])}</div></div>' for k, t in enumerate(nomi[:2], 1))
pagina('metodo.html', p['titolo'], p['sintesi'], S(f'<div class="col2"><div class="colonna">{testa(p["occhiello"], e(p["titolone"]), e(p["sintesi"]))}<div class="testo">{testo(d.get("", ""))}</div></div><aside class="lato"><h3>{e(nomi[2]) if len(nomi) > 2 else ""}</h3><div class="testo">{testo(d[nomi[2]]) if len(nomi) > 2 else ""}</div><a class="btn" href="{{r}}programma/index.html">Vai al programma</a></aside></div>') + S(f'<div class="capo"><div><span class="k">Ogni proposta dice su quale sta</span><h2>I due binari</h2></div></div><div class="binari">{binari_m}</div>', 'carta') + ADERISCI, 'programma', [('programma/index.html', 'Programma'), ('', 'Come lavoriamo')])

# Notizie: un flusso solo, dalla più recente alla meno recente.
# Niente «meno recenti» e niente gruppi: spezzare l'elenco faceva sembrare le notizie vecchie
# una sezione a parte, mentre è lo stesso elenco che continua.
corpo = LIBERO(testa('Notizie', 'Che cosa succede')
               + f'<ul class="griglia tre">{"".join(scheda_notizia(n) for n in NOTIZIE)}</ul>'
               + '<a class="vai-a" href="{r}cerca.html">Cerca nel sito →</a>')
pagina('notizie/index.html', 'Notizie', 'Le notizie del coordinamento: incontri, presìdi, tavoli.', corpo + ADERISCI, 'notizie', [('', 'Notizie')])
for n in NOTIZIE:
    pil = next((p for p in PILASTRI if p['numero'] == n.get('pilastro')), None); terr = TERRITORI.get(n.get('provincia', ''))
    legami = ''.join([f'<li><a href="{{r}}{pil["indirizzo"]}">Pilastro {pil["numero"]} · {e(pil["titolo"])}</a></li>' if pil else '', f'<li><a href="{{r}}{terr["indirizzo"]}">Provincia di {e(n["provincia"])}</a></li>' if terr else ''])
    legami = f'<ul class="etichette legami">{legami}</ul>' if legami else ''
    fonte = f'''<p class="avviso">Fonte esterna: <a href="{n['fonte']}" rel="noopener">{e(n.get('fonte_nome', 'leggi l’articolo'))} →</a></p>''' if n.get('fonte') else ''
    pagina(n['indirizzo'], n['titolo'], n.get('sintesi', ''), S(f'''<div class="col2"><div class="colonna">{testa(f"{n['quando']}{' · ' + e(n['luogo']) if n.get('luogo') else ''}{segni(n)}", e(n['titolo']), e(n.get('sintesi', '')))}{legami}<a class="vai-a" href="#testo">Leggi ↓</a></div>{foto(n['file'], n['titolo'], ' grande')}</div>''') + LIBERO(f'''<div class="testo" id="testo">{testo(n['corpo'])}{fonte}</div>{condividi(n['titolo'], n['indirizzo'])}<nav class="vicini"><a href="{{r}}notizie/index.html">← Tutte le notizie</a></nav>''') + ADERISCI, 'notizie', [('notizie/index.html', 'Notizie'), ('', n['titolo'])], tipo='article',
           dati={'@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': n['titolo'], 'datePublished': n['data'], 'publisher': {'@type': 'Organization', 'name': SITO['nome']}})
voci_rss = ''.join(f"<item><title>{e(n['titolo'])}</title><link>{BASE}{n['indirizzo']}</link><guid>{BASE}{n['indirizzo']}</guid><pubDate>{n['giorno'].strftime('%a, %d %b %Y')} 09:00:00 +0100</pubDate><description>{e(n.get('sintesi', ''))}</description></item>" for n in NOTIZIE if not n['esempio'] and not n['bozza'])
(OUT / 'notizie').mkdir(exist_ok=True)
(OUT / 'notizie' / 'feed.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{e(SITO["nome"])} — Notizie</title><link>{BASE}</link><description>{e(SITO["descrizione"])}</description><language>it</language>{voci_rss}</channel></rss>\n', encoding='utf-8')

# Agenda: quattro incontri per schermata
passati_l = list(reversed([v for v in EVENTI if v['passato']]))
corpo = ''
for k, g in enumerate(a_gruppi(FUTURI, 4) or [[]]):
    corpo += S((testa('Agenda', 'Dove ci vediamo') if k == 0 else f'<div class="capo"><div><h2>Prossimi incontri · {k + 1}</h2></div></div>') + ('<ul class="eventi">' + ''.join(riga_evento(v) for v in g) + '</ul>' if g else '<p class="sott">Nessun incontro in calendario per ora.</p>'))
for k, g in enumerate(a_gruppi(passati_l, 4)):
    corpo += S(f'<div class="capo"><div><h2>Già svolti{" · " + str(k + 1) if k else ""}</h2></div></div><ul class="eventi">{"".join(riga_evento(v) for v in g)}</ul>', 'carta')
# Calendario: i mesi con incontri, costruito dal browser a partire dall'elenco qui sotto.
# Senza JavaScript non compare e resta l'elenco, che basta da solo.
if EVENTI:
    dati = [{'g': f"{v['giorno']:%Y-%m-%d}", 'o': v.get('ora', ''), 't': v['titolo'],
             'l': v.get('luogo', ''), 'u': '{r}' + v['indirizzo'], 'p': bool(v['passato'])} for v in EVENTI]
    # Un mese intero non entra in una schermata su un portatile: il calendario scorre.
    corpo = LIBERO('<div class="capo"><div><h2>Il calendario</h2></div>'
              '<a class="vai-a" href="#elenco">Vai all’elenco ↓</a></div>'
              '<div id="calendario" class="calendario" data-vuoto="Nessun incontro in questo mese."></div>'
              '<script type="application/json" id="sa-eventi">' + json.dumps(dati, ensure_ascii=False) + '</script>'
              ) + corpo.replace('<div class="capo">', '<div class="capo" id="elenco">', 1)

pagina('agenda/index.html', 'Agenda', 'Assemblee, tavoli e presìdi del coordinamento in Sicilia.', corpo + aderisci_con('Vuoi sapere quando siamo vicino a te?', 'Lascia i tuoi contatti e la provincia: ti scriviamo noi.'), 'agenda', [('', 'Agenda')])
(OUT / 'agenda').mkdir(exist_ok=True)
for v in EVENTI:
    d = v['giorno']
    ics = ''
    if not v['passato']:
        ora = v.get('ora', '').replace(':', '')
        inizio = f"{d:%Y%m%d}T{ora}00" if ora else f'{d:%Y%m%d}'
        fine = f"{d:%Y%m%d}T{int(ora[:2]) + 2:02d}{ora[2:]}00" if ora else f'{d + datetime.timedelta(days=1):%Y%m%d}'
        tz = ';TZID=Europe/Rome' if ora else ';VALUE=DATE'
        nome_ics = v['file'] + '.ics'
        # Promemoria il giorno prima: un segnaposto senza avviso si perde fra gli altri impegni.
        (OUT / 'agenda' / nome_ics).write_text('\r\n'.join([
            'BEGIN:VCALENDAR', 'VERSION:2.0', "PRODID:-//Sinistra per l'Alternativa//Agenda//IT",
            'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
            'BEGIN:VEVENT', f"UID:{v['file']}@sinistra-alternativa-sicilia",
            f'DTSTAMP:{OGGI:%Y%m%d}T000000Z', f'DTSTART{tz}:{inizio}', f'DTEND{tz}:{fine}',
            'SUMMARY:' + ics_testo(v['titolo']),
            'LOCATION:' + ics_testo(v.get('luogo', '')),
            'DESCRIPTION:' + ics_testo(f"{SITO['nome']} · {BASE}{v['indirizzo']}"),
            f"URL:{BASE}{v['indirizzo']}",
            'BEGIN:VALARM', 'ACTION:DISPLAY',
            'DESCRIPTION:' + ics_testo('Domani: ' + v['titolo']), 'TRIGGER:-P1D', 'END:VALARM',
            'END:VEVENT', 'END:VCALENDAR', '']), encoding='utf-8')
        ics = (f'<a class="btn bn" href="{nome_ics}" download>Salva nel calendario</a>'
               f'<a class="vai-a" href="{google_calendario(v, inizio, fine, bool(ora))}" target="_blank"'
               f' rel="noopener">Aggiungi a Google Calendar →</a>')
    pil = next((p for p in PILASTRI if p['numero'] == v.get('pilastro')), None)
    terr = TERRITORI.get(v.get('provincia', ''))
    scheda = f'''<aside class="lato"><dl><dt>Quando</dt><dd>{data_estesa(d)}{' · ore ' + v['ora'] if v.get('ora') else ''}</dd><dt>Dove</dt><dd>{e(v.get('luogo', 'da indicare'))}</dd>{f'<dt>Provincia</dt><dd><a href="{{r}}{terr["indirizzo"]}">{e(v["provincia"])}</a></dd>' if terr else ''}{f'<dt>Pilastro</dt><dd><a href="{{r}}{pil["indirizzo"]}">{pil["numero"]} · {e(pil["titolo"])}</a></dd>' if pil else ''}</dl>{ics}<a class="btn" href="{{r}}aderisci.html{'?provincia=' + v['provincia'] if v.get('provincia') else ''}">{'Aderisci' if v['passato'] else 'Ci sarò: aderisci'}</a></aside>'''
    pagina(v['indirizzo'], v['titolo'], f"{data_estesa(d)} · {v.get('luogo', '')}", S(f'''<div class="due"><div class="colonna">{testa(f"{'Incontro già svolto' if v['passato'] else 'Incontro'}{segni(v)}", e(v['titolo']))}<div class="testo">{testo(v['corpo']) if v['corpo'] else '<p>Dettagli in arrivo.</p>'}</div><a class="vai-a" href="{{r}}agenda/index.html">← Tutta l’agenda</a></div>{scheda}</div>'''), 'agenda', [('agenda/index.html', 'Agenda'), ('', v['titolo'])],
           dati=None if v['esempio'] else {'@context': 'https://schema.org', '@type': 'Event', 'name': v['titolo'], 'startDate': v['data'] + (f"T{v['ora']}" if v.get('ora') else ''), 'location': {'@type': 'Place', 'name': v.get('luogo', '')}, 'organizer': {'@type': 'Organization', 'name': SITO['nome']}})

# Territori
pagina('territori/index.html', 'Territori', 'Nove province, un tavolo in ognuna: le lotte, gli incontri, come partecipare.', S(testa('Territori', 'Dov’è la tua Sicilia?', 'Scegli la provincia: trovi le lotte aperte, il prossimo incontro e come partecipare.') + f'''<ul class="griglia tre">{''.join(f'<li><a class="scheda riv" href="{{r}}{t["indirizzo"]}"><span class="tx"><strong>{e(nome)}</strong><p>{e(t.get("lotte", ""))}</p><span class="vai">Vai →</span></span></a></li>' for nome, t in sorted(TERRITORI.items()))}</ul>''', 'carta fitta') + ADERISCI, 'territori', [('', 'Territori')])
for nome, t in TERRITORI.items():
    inc = [v for v in EVENTI if v.get('provincia') == nome][:3]
    not_p = [n for n in NOTIZIE if n.get('provincia') == nome][:3]
    lotte = ''.join(f'<li>{e(x.strip())}</li>' for x in t.get('lotte', '').split(','))
    corpo = S(f'''<div class="due"><div class="colonna">{testa(f"Territori{segni(t)}", e(nome))}<h2>Le lotte</h2><ul class="etichette">{lotte}</ul><div class="testo">{testo(t['corpo'])}</div></div><aside class="lato">{foto('provincia-' + t['indirizzo'].split('/')[-1][:-5], nome)}<dl><dt>Referente</dt><dd>{e(t.get('referente', 'da indicare'))}</dd><dt>Contatto</dt><dd>{e(t.get('contatto', 'da indicare'))}</dd></dl><a class="btn" href="{{r}}aderisci.html?provincia={nome}">Aderisci da {e(nome)}</a></aside></div>''')
    corpo += S(f'''<div class="capo"><div><span class="k">In provincia di {e(nome)}</span><h2>Gli incontri</h2></div><a href="{{r}}agenda/index.html">Tutta l’agenda →</a></div>{'<ul class="eventi">' + ''.join(riga_evento(v) for v in inc) + '</ul>' if inc else '<p class="sott">Nessun incontro in calendario per ora in questa provincia.</p>'}<div class="capo"><div><h2>Le altre province</h2></div></div>{mappa(nome)}''', 'carta')
    if not_p:
        corpo += S(f'<div class="capo"><div><h2>Da questa provincia</h2></div></div><ul class="griglia tre">{"".join(scheda_notizia(n) for n in not_p)}</ul>')
    pagina(t['indirizzo'], f'Provincia di {nome}', f"Le lotte e gli incontri del coordinamento in provincia di {nome}: {t.get('lotte', '')}.", corpo + aderisci_con('Il programma si scrive ai tavoli', f'Aderisci dalla provincia di {e(nome)}: ti scriviamo per il prossimo incontro.', f'?provincia={nome}'), 'territori', [('territori/index.html', 'Territori'), ('', nome)])

# Aderisci
opz = ''.join(f'<option>{p}</option>' for p in PROVINCE)
opz_tavoli = ''.join(f'<option value="{p["numero"]}">{p["numero"]} · {e(p["titolo"])}</option>' for p in PILASTRI)
MANO = ['Volantinaggio e banchetti', 'Social e comunicazione', 'Competenze professionali', 'Ospitare un incontro', 'Contributo in denaro']
opz_mano = ''.join(f'<label><input type="checkbox" name="mano" value="{e(m)}"><span>{e(m)}</span></label>' for m in MANO)
pagina('aderisci.html', 'Aderisci', 'Aderisci al coordinamento: lascia i tuoi contatti, ti scriviamo per gli incontri nel tuo territorio.', S(f'''<div class="col2"><div class="colonna">{testa('Partecipa', 'Aderisci al coordinamento', 'Comitati, collettivi, sindacati, singole e singoli: lascia i tuoi contatti, ti scriviamo per i tavoli e gli incontri nel tuo territorio.')}<ul class="testo passi"><li>Scegli se aderisci tu o la tua organizzazione.</li><li>Ti scriviamo quando c’è un incontro nella tua provincia.</li><li>Puoi partecipare a uno dei sette tavoli del programma.</li></ul>{'<p class="avviso">Il modulo non è ancora collegato: in questa bozza non invia e non conserva nulla.</p>' if not SITO['modulo']['invia_a'] else ''}</div>
<form id="adesione" novalidate data-invia-a="{e(SITO['modulo']['invia_a'])}">
<p class="passo-n" aria-live="polite">Passo <b>1</b> di 2</p>
<div class="passo" data-passo="1">
<div class="chi" role="radiogroup" aria-label="Chi aderisce"><label class="scelta"><input type="radio" name="chi" value="persona" checked><span>Aderisco io</span></label><label class="scelta"><input type="radio" name="chi" value="organizzazione"><span>Aderisce la mia organizzazione</span></label></div>
<div class="riga2 solo-org" hidden><label>Nome dell’organizzazione<input type="text" name="organizzazione" autocomplete="organization"></label><label>Che cos’è<select name="tipo_organizzazione"><option value="">Scegli…</option><option>Comitato</option><option>Collettivo</option><option>Sindacato</option><option>Associazione</option><option>Circolo o sezione</option><option>Altro</option></select></label></div>
<label><span class="et-nome">Nome e cognome</span><input type="text" name="nome" autocomplete="name"></label>
<div class="riga2"><label>Email<input type="email" name="email" autocomplete="email" inputmode="email"></label><label>Telefono (facoltativo)<input type="tel" name="telefono" autocomplete="tel" inputmode="tel"></label></div>
<div class="riga2"><label>Comune<input type="text" name="comune" autocomplete="address-level2"></label><label>Provincia<select name="provincia"><option value="">Scegli…</option>{opz}</select></label></div>
<button class="btn" type="button" data-avanti>Avanti</button>
</div>
<div class="passo" data-passo="2">
<label>Tavolo che ti interessa<select name="tavolo"><option value="">Non so ancora</option>{opz_tavoli}</select></label>
<fieldset class="mano"><legend>Come vuoi dare una mano (facoltativo)</legend>{opz_mano}</fieldset>
<label class="consenso"><input type="checkbox" name="consenso"><span>Ho letto l’<a href="{{r}}privacy.html">informativa privacy</a> e acconsento all’uso dei miei dati, che rivelano un’adesione politica, per essere ricontattato dal coordinamento.</span></label>
<label class="consenso"><input type="checkbox" name="notizie"><span>Voglio ricevere gli aggiornamenti per email: notizie, incontri e appelli. Facoltativo, e puoi cancellarti con un clic da ogni messaggio.</span></label>
<div class="riga2 fine"><button class="btn b2" type="button" data-indietro>Indietro</button><button class="btn" type="submit">Invia adesione</button></div>
</div>
<input class="trappola" type="text" name="sito_web" tabindex="-1" autocomplete="off" aria-hidden="true">
<p class="esito" role="status" aria-live="polite"></p>
</form></div>''', 'carta'), 'aderisci', [('', 'Aderisci')])

# Contatti
c = SITO['contatti']
pagina('contatti.html', 'Contatti e stampa', 'Come contattare il coordinamento. Materiali per la stampa.', S(f'''<div class="col2"><div class="colonna">{testa('Contatti', 'Scrivici, chiamaci, vieni')}{'<p class="avviso">I contatti del coordinamento non sono ancora pubblicati. Per ora si scrive dal modulo di adesione.</p>' if not any(c.get(k) for k in ('email', 'telefono', 'sede', 'facebook', 'instagram')) else ''}
{elenco_contatti()}</div>
<aside class="lato"><h3>Per la stampa</h3><p>Simbolo, identità visiva, programma e propaganda sono raccolti in una pagina sola, pronti da scaricare.</p><a class="btn b2" href="{{r}}materiali.html">Tutti i materiali</a><a class="btn b2" href="{{r}}territori/index.html">Trova la tua provincia</a><a class="btn" href="{{r}}aderisci.html">Aderisci</a></aside></div>'''), 'contatti', [('', 'Contatti')])

# Ricerca nel sito: un indice leggero letto dal browser, nessun servizio esterno
INDICE = [{'t': p['titolo'], 'd': p['sintesi'], 'u': p['indirizzo'], 'k': 'Programma', 'x': re.sub(r'[#*\[\]()-]', ' ', p['corpo'])} for p in PILASTRI]
INDICE += [{'t': n['titolo'], 'd': n.get('sintesi', ''), 'u': n['indirizzo'], 'k': 'Notizie · ' + n['quando'], 'x': re.sub(r'[#*\[\]()-]', ' ', n['corpo'])} for n in NOTIZIE]
INDICE += [{'t': v['titolo'], 'd': data_estesa(v['giorno']) + ' · ' + v.get('luogo', ''), 'u': v['indirizzo'], 'k': 'Agenda', 'x': v['corpo']} for v in EVENTI]
INDICE += [{'t': 'Provincia di ' + nome, 'd': t.get('lotte', ''), 'u': t['indirizzo'], 'k': 'Territori', 'x': ''} for nome, t in TERRITORI.items()]
INDICE += [{'t': 'Materiali', 'd': 'Logo, identità visiva, programma da stampare, volantini e manifesti.', 'u': 'materiali.html', 'k': 'Materiali', 'x': ' '.join(m['titolo'] + ' ' + m['descrizione'] for m in MATERIALI)}]
INDICE += [{'t': 'Chi siamo', 'd': PAGINE['chi-siamo']['sintesi'], 'u': 'chi-siamo.html', 'k': 'Il coordinamento', 'x': PAGINE['chi-siamo']['corpo']}, {'t': 'Come lavoriamo', 'd': PAGINE['metodo']['sintesi'], 'u': 'metodo.html', 'k': 'Il metodo', 'x': PAGINE['metodo']['corpo']}, {'t': 'Aderisci', 'd': 'Lascia i tuoi contatti', 'u': 'aderisci.html', 'k': 'Partecipa', 'x': 'adesione modulo iscriversi partecipare'}]
(OUT / 'risorse' / 'indice.json').write_text(json.dumps(INDICE, ensure_ascii=False), encoding='utf-8')
pagina('cerca.html', 'Cerca nel sito', 'Cerca fra programma, notizie, incontri e territori.', S(testa('Cerca', 'Che cosa cerchi?') + '''<form class="cerca" role="search" onsubmit="return false"><label>Parole da cercare<input type="text" id="q" name="q" autocomplete="off" autofocus></label></form><p id="conta" role="status" aria-live="polite"></p><ul class="eventi scorre" id="esiti"></ul><noscript><p class="avviso">La ricerca ha bisogno di JavaScript. In alternativa usa il menu.</p></noscript>''', 'alto'), '', [('', 'Cerca')])

# Pagine di servizio
LG = SITO.get('legale', {})
MANCA = '**[da indicare]**'
VOCI_LEGALI = {
    'titolare': LG.get('titolare') or MANCA.strip('*'), 'sede_titolare': LG.get('sede_titolare') or 'sede ' + MANCA,
    'email': SITO['contatti']['email'] if SITO['contatti'].get('reali') else 'indirizzo ' + MANCA,
    'committente': SITO['committente'] if SITO['committente'] != 'nome da indicare' else MANCA.strip('*'),
    'incaricati': LG.get('incaricati') or MANCA, 'servizio_modulo': LG.get('servizio_modulo') or (MANCA if SITO['modulo'].get('invia_a') else 'nessuno, per ora: il modulo non è ancora collegato'),
    'conservazione': LG.get('conservazione') or 'Durata ' + MANCA + ' dal coordinamento. In ogni caso i dati si cancellano appena lo chiedi.',
    'ospite': 'oggi GitHub Pages, della società statunitense GitHub' if 'github.io' in BASE else 'il fornitore dello spazio web',
    'stato_modulo': 'Oggi il modulo di adesione **non invia e non conserva nulla**: questa informativa descrive come funzionerà quando verrà collegato. Le voci «da indicare» vanno decise dal coordinamento prima di quel momento.' if not SITO['modulo'].get('invia_a') else 'Il modulo di adesione è attivo.',
    'stato_sito': 'Questa è una bozza. I contatti del coordinamento non sono ancora pubblicati, il programma è in discussione nei tavoli e attende il voto dell’assemblea, e il modulo di adesione non è ancora collegato a nessun servizio: non invia e non conserva nulla.' if SITO['bozza'] else f"Versione {SITO['versione']}.",
    'oggi': data_estesa(OGGI),
}
for chiave in ('privacy', 'note-legali'):
    p = PAGINE[chiave]
    corpo_l = p['corpo']
    for k_, v_ in VOCI_LEGALI.items():
        corpo_l = corpo_l.replace('{' + k_ + '}', v_)
    # Un'informativa con voci ancora da decidere non deve passare per quella definitiva: l'avviso
    # compare da sé finché restano «da indicare», e sparisce da sé quando il coordinamento le riempie.
    quante = corpo_l.count('da indicare')
    avviso = (f'<p class="avviso">Questo testo non è ancora approvato dal coordinamento: '
              f'{quante} voci sono indicate come «da indicare» e vanno decise prima che il sito '
              f'raccolga dati. Per qualunque questione sui tuoi dati scrivici dal modulo di adesione.</p>'
              if quante else '')
    pagina(f'{chiave}.html', p['titolo'], p['sintesi'],
           S(testa(p['occhiello'], e(p['titolo']), e(p['sintesi'])) + avviso + '<a class="vai-a" href="#testo">Leggi ↓</a>')
           + LIBERO(f'<div class="testo" id="testo">{testo(corpo_l)}</div>'), '', [('', p['titolo'])])
# Materiali scaricabili
def _peso(b):
    return f'{b / 1048576:.1f} MB'.replace('.', ',') if b >= 1048576 else f'{max(1, round(b / 1024))} KB'


gruppi_mat, mancanti_mat = {}, 0
for m in MATERIALI:
    f_ = RIS / 'materiali' / m['file']
    pronto = f_.exists()
    if not pronto:
        mancanti_mat += 1
    tipo = m['file'].rsplit('.', 1)[-1].upper()
    extra = f'<a class="vai" href="{{r}}{m["anche"]}">Leggilo sul sito →</a>' if m.get('anche') else ''
    if m.get('varianti'):
        extra = '<p class="varianti"><span>Scarica la versione:</span>' + ''.join(f'<a href="{{r}}risorse/materiali/{v}" download>{e(n)}</a>' for n, v in m['varianti'] if (RIS / 'materiali' / v).exists()) + '</p>' + extra
    bottone = f'<a class="btn" href="{{r}}risorse/materiali/{m["file"]}" download>Scarica</a>'
    testa_s = f'<strong>{e(m["titolo"])}</strong><p>{e(m["descrizione"])}</p>'
    if pronto:
        corpo_s = extra if m.get('varianti') else (bottone + extra)
        voce = f'<li><span class="scheda mat"><span class="tx"><span class="k">{tipo} · {_peso(f_.stat().st_size)}</span>{testa_s}{corpo_s}</span></span></li>'
    else:
        voce = f'<li><span class="scheda mat attesa"><span class="tx"><span class="k">{tipo} · in preparazione</span>{testa_s}{extra}</span></span></li>'
    gruppi_mat.setdefault(m['gruppo'], []).append(voce)
nota_mat = '<p class="avviso">Qualche materiale è ancora in preparazione: lo trovi qui appena pronto.</p>' if mancanti_mat else ''
gruppi_lista = list(gruppi_mat.items())
testa_mat = testa('Materiali', 'Materiali da scaricare', 'Logo, identità visiva, programma e propaganda: tutto pronto da usare per banchetti, assemblee e social.') + (nota_mat if mancanti_mat else '')
blocchi_mat = S(testa_mat + f'<div class="capo"><div><h2>{e(gruppi_lista[0][0])}</h2></div></div><ul class="griglia tre">{"".join(gruppi_lista[0][1])}</ul>', 'fitta')
blocchi_mat += ''.join(S(f'<div class="capo"><div><h2>{e(g)}</h2></div></div><ul class="griglia tre">{"".join(v)}</ul>', 'carta' if i % 2 == 0 else '') for i, (g, v) in enumerate(gruppi_lista[1:]))
pagina('materiali.html', 'Materiali', 'Logo, identità visiva, programma da stampare, volantini e manifesti da scaricare e usare.',
       blocchi_mat + ADERISCI, '', [('', 'Materiali')])

# Crediti delle fotografie (le licenze Creative Commons chiedono autore, licenza e fonte)
def dove_usata(file):
    """In quale pagina compare la fotografia. Serve perché, tolta la banda dall'immagine, il credito deve
    essere ritrovabile: chi legge la pagina dei crediti deve poter risalire alla foto, e viceversa."""
    if file.startswith('pilastro-'):
        v = next((x for x in PILASTRI if x['numero'] == file[9:]), None)
        return (v['indirizzo'], f'Pilastro {v["numero"]} · {v["titolo"]}') if v else None
    if file.startswith('provincia-'):
        v = next((x for n, x in TERRITORI.items() if slug(n) == file[10:]), None)
        nome = next((n for n in TERRITORI if slug(n) == file[10:]), '')
        return (v['indirizzo'], f'Provincia di {nome}') if v else None
    v = next((x for x in NOTIZIE if x['file'] == file), None)
    return (f'notizie/{file}.html', v['titolo']) if v else None


voci_crediti = []
for c in FOTO.values():
    dove = dove_usata(c['file'])
    usata = (f'<span class="dove">Nella pagina <a href="{{r}}{dove[0]}">{e(dove[1])}</a></span>'
             if dove else '<span class="dove">Non usata in nessuna pagina</span>')
    anno = f' ({c["anno"]})' if c.get('anno') else ''
    originale = (f'. Originale: <a href="https://commons.wikimedia.org/wiki/File:'
                 f'{urllib.parse.quote(c["commons"].replace(" ", "_"))}" rel="noopener">Wikimedia Commons</a>'
                 if c.get('commons') else '')
    voci_crediti.append(
        f'<li><strong><a href="{{r}}risorse/img/{c["file"]}.jpg?v={SITO["versione"]}">{e(c["soggetto"])}</a></strong>'
        f'<span>Foto di {e(c["autore"])}{anno}, licenza '
        f'<a href="{c["licenza_url"]}" rel="license noopener">{e(c["licenza"])}</a>{originale}. '
        f'Ridimensionata e ritagliata.</span>{usata}</li>')
righe_crediti = ''.join(voci_crediti)
senza_pagina = [c['file'] for c in FOTO.values() if not dove_usata(c['file'])]
if senza_pagina:
    print('Fotografie registrate ma non usate in nessuna pagina: ' + ', '.join(senza_pagina))

pagina('crediti.html', 'Crediti fotografici', 'Autori, licenze e fonti delle fotografie usate nel sito.', S(testa('Fotografie', 'Crediti fotografici', 'Le fotografie vengono da Wikimedia Commons e restano dei loro autori. Qui, per ognuna, l’autore, la licenza, l’originale e la pagina in cui compare: è questa la nostra attribuzione, come le licenze consentono.') + '<a class="vai-a" href="#elenco">Vedi l’elenco ↓</a>') + LIBERO(f'<ul class="crediti" id="elenco">{righe_crediti}</ul>'), '', [('', 'Crediti fotografici')])
# Cookie e statistiche: la pagina dice sempre e solo ciò che il sito fa davvero (si aggiorna da contenuti/sito.json)
righe_ck = []
if COOKIE_ATTIVI: righe_ck.append(('sa-consenso', 'Questo sito', 'Tecnico', '6 mesi', 'Ricorda la scelta fatta sui cookie (memoria del dispositivo, non è un cookie)'))
if ST.get('goatcounter'): righe_ck.append(('nessuno', 'GoatCounter', 'Statistiche senza cookie', '—', 'Conta le pagine viste senza salvare nulla sul dispositivo e senza riconoscere le persone'))
if ST.get('google_analytics'): righe_ck.append(('_ga, _ga_*', 'Google Analytics', 'Statistiche', 'Fino a 2 anni', 'Statistiche di visita. Solo dopo il consenso'))
if ST.get('meta_pixel'): righe_ck.append(('_fbp, _fbc', 'Meta (Facebook, Instagram)', 'Campagne social', 'Fino a 3 mesi', 'Misura delle campagne sui social. Solo dopo il consenso'))
tab_ck = ('<table class="tab-cookie"><thead><tr><th>Nome</th><th>Servizio</th><th>Categoria</th><th>Durata</th><th>A che cosa serve</th></tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{e(x)}</td>' for x in rg) + '</tr>' for rg in righe_ck) + '</tbody></table>') if righe_ck else '<p><strong>Oggi il sito non usa cookie e non misura le visite.</strong> Non c’è nulla da accettare o rifiutare. Caratteri e immagini sono ospitati sul sito: nessuna chiamata a servizi esterni.</p>'
gest_ck = ('<p>Alla prima visita un avviso chiede la scelta: «Accetta tutto», «Rifiuta» o «Personalizza». Rifiutare, o chiudere con la ×, non cambia nulla: il sito funziona allo stesso modo e nessuno strumento con cookie viene caricato. La scelta vale sei mesi e si può cambiare quando si vuole.</p><div class="azioni"><button class="btn" type="button" data-cookie-scelta>Cambia la tua scelta</button></div>') if COOKIE_ATTIVI else '<p>Non essendoci cookie, non c’è nessun consenso da dare.</p>'
corpo_ck = f'''<div class="testo"><h2>1. Che cosa sono i cookie</h2><p>Piccoli file che un sito salva sul dispositivo di chi lo visita. Quelli tecnici servono a far funzionare il sito; quelli di terze parti servono a statistiche o pubblicità e richiedono il consenso.</p>
<h2>2. Che cosa usa questo sito</h2>{tab_ck}
<h2>3. Consenso e come cambiarlo</h2>{gest_ck}
<h2>4. Bloccarli dal browser</h2><p>Ogni browser permette di bloccare o cancellare i cookie dalle proprie impostazioni: <a href="https://support.google.com/chrome/answer/95647" rel="noopener">Chrome</a>, <a href="https://support.mozilla.org/it/kb/protezione-antitracciamento-avanzata-firefox-desktop" rel="noopener">Firefox</a>, <a href="https://support.apple.com/it-it/guide/safari/sfri11471/mac" rel="noopener">Safari</a>, <a href="https://support.microsoft.com/it-it/microsoft-edge" rel="noopener">Edge</a>.</p>
<h2>5. I tuoi diritti</h2><p>Per sapere quali dati ti riguardano, correggerli o farli cancellare scrivi a {e(SITO["contatti"]["email"])}. Il resto è nell’<a href="{{r}}privacy.html">informativa privacy</a>.</p></div>'''
pagina('cookie.html', 'Cookie e statistiche', 'Che cosa usa il sito per misurare le visite e come cambiare la propria scelta.', S(testa('Cookie', 'Cookie e statistiche', 'Che cosa usa questo sito, detto in chiaro.') + '<a class="vai-a" href="#cookie">Leggi ↓</a>') + LIBERO(f'<div id="cookie">{corpo_ck}</div>'), '', [('', 'Cookie e statistiche')])
pagina('404.html', 'Pagina non trovata', 'La pagina cercata non esiste o è stata spostata.', S(testa('Errore 404', 'Questa pagina non c’è', 'Errore 404: l’indirizzo non esiste o è stato spostato. Riparti da qui:') + f'<div class="azioni"><a class="btn" href="{BASE}index.html">Pagina iniziale</a><a class="btn b2" href="{BASE}programma/index.html">Il programma</a></div>'))
# la pagina 404 è servita da qualunque indirizzo: i suoi collegamenti devono essere assoluti
f404 = OUT / '404.html'
f404.write_text(re.sub(r'(href|src)="(?!https?:|#|mailto:)([^"]+)"', lambda m: f'{m.group(1)}="{BASE}{m.group(2)}"', f404.read_text(encoding='utf-8')), encoding='utf-8')

(OUT / '.well-known').mkdir(exist_ok=True)
(OUT / '.well-known' / 'security.txt').write_text(
    '# Come segnalare un problema di sicurezza di questo sito.\n'
    f"Contact: mailto:{SITO['contatti']['email'] if SITO['contatti'].get('reali') else 'indirizzo da indicare'}\n"
    'Preferred-Languages: it, en\n'
    f'Expires: {datetime.date.today().year + 1}-12-31T23:59:59.000Z\n', encoding='utf-8')

(OUT / 'sito.webmanifest').write_text(json.dumps({
    'name': SITO['nome'] + ' — Sicilia', 'short_name': 'SA Sicilia', 'description': SITO['descrizione'], 'lang': 'it',
    'start_url': BASE, 'scope': BASE, 'display': 'browser', 'background_color': '#ffffff', 'theme_color': '#000000',
    'icons': [{'src': BASE + 'risorse/loghi/sa-icona-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': BASE + 'risorse/loghi/sa-icona-512.png', 'sizes': '512x512', 'type': 'image/png'},
              {'src': BASE + 'risorse/loghi/sa-icona.svg', 'sizes': 'any', 'type': 'image/svg+xml'}],
}, ensure_ascii=False, indent=1), encoding='utf-8')

# Mappa del sito e istruzioni per i motori di ricerca
indicizzabili = [p for p in PAGINE_FATTE if p != '404.html']
OGGI = datetime.date.today().isoformat()
def _voce(pg):
    foto_pg = ''
    m = re.match(r'programma/(.+)\.html$', pg)
    if m:
        for pl in PILASTRI:
            if pl['indirizzo'] == pg and FOTO.get('pilastro-' + pl['numero']):
                foto_pg = f"<image:image><image:loc>{BASE}risorse/img/pilastro-{pl['numero']}.jpg</image:loc></image:image>"
    return f"<url><loc>{BASE}{'' if pg == 'index.html' else pg}</loc><lastmod>{OGGI}</lastmod>{foto_pg}</url>\n"
(OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + ''.join(_voce(pg) for pg in indicizzabili if pg not in ('cerca.html',)) + '</urlset>\n', encoding='utf-8')
(OUT / 'robots.txt').write_text((f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n' if SITO['indicizzabile'] else 'User-agent: *\nDisallow: /\n'), encoding='utf-8')
print(f'Sito costruito: {len(PAGINE_FATTE)} pagine in {OUT.name}/ · versione {SITO["versione"]}' + (' · ANTEPRIMA con bozze' if ANTEPRIMA else '') + (f' · bozze lasciate fuori: {len(ESCLUSE)} ({", ".join(ESCLUSE)})' if ESCLUSE else ''))

pronto_per_il_definitivo()
