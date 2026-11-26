#!/usr/bin/env python3
"""Costruisce il sito da `contenuti/` e `risorse/` nella cartella `pubblico/`.

Solo libreria standard di Python: gira ovunque, anche nella pubblicazione automatica.
Uso:  python3 costruisci.py              (sito pubblico: i file con «bozza: sì» restano fuori)
      python3 costruisci.py --anteprima  (anteprima privata: entrano anche le bozze, con etichetta)
"""
import datetime, html, json, pathlib, re, shutil, sys, unicodedata

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
    meta = {}
    for riga in m.group(1).splitlines():
        if ':' in riga:
            k, v = riga.split(':', 1)
            meta[k.strip()] = v.strip()
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


def testo(md):
    """Testo semplice: righe vuote separano i capoversi, `## ` titolo, `### ` sottotitolo, `- ` elenco, **grassetto**, [testo](indirizzo)."""
    out = []
    for blocco in re.split(r'\n\s*\n', md.strip()):
        righe = [r for r in blocco.strip().splitlines() if r.strip()]
        if not righe:
            continue
        if righe[0].startswith('### '):
            out.append(f'<h3>{in_linea(righe[0][4:])}</h3>')
        elif righe[0].startswith('## '):
            out.append(f'<h2>{in_linea(righe[0][3:])}</h2>')
        elif all(r.lstrip().startswith('- ') for r in righe):
            out.append('<ul>' + ''.join(f'<li>{in_linea(r.lstrip()[2:])}</li>' for r in righe) + '</ul>')
        else:
            out.append(f'<p>{in_linea(" ".join(r.strip() for r in righe))}</p>')
    return '\n'.join(out)


PILASTRI = cartella('pilastri')
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
ES = ' <em class="es">esempio</em>'
BZ = ' <em class="es bz">bozza non pubblica</em>'


def segni(x):
    return (ES if x['esempio'] else '') + (BZ if x.get('bozza') else '')

# ---------- parti comuni ----------
MENU = [('chi-siamo.html', 'Chi siamo'), ('programma/index.html', 'Programma'), ('notizie/index.html', 'Notizie'), ('agenda/index.html', 'Agenda'), ('territori/index.html', 'Territori'), ('contatti.html', 'Contatti')]
PAGINE_FATTE = []


def pagina(percorso, titolo, descrizione, corpo, sezione='', briciole=None, og='generale', tipo='website', dati=None):
    """Scrive una pagina completa: testata, briciole, contenuto, piede. `percorso` è relativo alla radice del sito."""
    r = '../' * percorso.count('/')
    voci = ''.join(f'<a href="{r}{h}"' + (' aria-current="page"' if h.split('/')[0].replace('.html', '') == sezione else '') + f'>{t}</a>' for h, t in MENU)
    bric = ''
    if briciole:
        bric = '<nav class="briciole" aria-label="Percorso"><ol>' + f'<li><a href="{r}index.html">Home</a></li>' + ''.join(f'<li><a href="{r}{h}">{e(t)}</a></li>' if h else f'<li aria-current="page">{e(t)}</li>' for h, t in briciole) + '</ol></nav>'
    c = SITO['contatti']
    titolo_pieno = f"{titolo} — {SITO['nome']}" if percorso != 'index.html' else f"{SITO['nome']} — Sicilia"
    robot = '' if SITO['indicizzabile'] else '<meta name="robots" content="noindex, nofollow">\n'
    ld = f'<script type="application/ld+json">{json.dumps(dati, ensure_ascii=False)}</script>\n' if dati else ''
    pagina_html = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<script>document.documentElement.className = "js";</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
{robot}<title>{e(titolo_pieno)}</title>
<meta name="description" content="{e(descrizione)}">
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
<link rel="alternate" type="application/rss+xml" title="Notizie" href="{r}notizie/feed.xml">
<link rel="preload" href="{r}risorse/font/montserrat-latin-900-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}risorse/stile.css">
{ld}</head>
<body>
<a class="salta" href="#contenuto">Salta al contenuto</a>
<header class="testata">
<a class="logo" href="{r}index.html"><img src="{r}risorse/loghi/sa-logo-orizzontale.svg" alt="{e(SITO['nome_logo'])} — pagina iniziale" width="174" height="42"></a>
<button class="menu-b" type="button" aria-expanded="false" aria-controls="menu">Menù</button>
<nav class="menu" id="menu" aria-label="Principale">{voci}<a class="btn" href="{r}aderisci.html">Aderisci</a></nav>
</header>
{bric}
<main id="contenuto">
{corpo.replace('{r}', r)}
</main>
<footer class="piede">
<div class="in">
<div><img class="logo-f" src="{r}risorse/loghi/sa-logo-orizzontale-negativo-su-nero.svg" alt="{e(SITO['nome_logo'])}" width="330" height="80"><p style="margin-top:14px;font-size:15px">{e(SITO['descrizione'])}</p></div>
<div><h2>Il sito</h2><ul>{''.join(f'<li><a href="{r}{h}">{t}</a></li>' for h, t in MENU)}<li><a href="{r}metodo.html">Come lavoriamo</a></li><li><a href="{r}aderisci.html">Aderisci</a></li><li><a href="{r}cerca.html">Cerca nel sito</a></li></ul></div>
<div><h2>Contatti</h2><ul><li>{e(c['email'])}</li><li>{e(c['telefono'])}</li><li>{e(c['sede'])}</li></ul></div>
<div><h2>Seguici</h2><ul><li>Facebook — {e(c['facebook'])}</li><li>Instagram — {e(c['instagram'])}</li><li><a href="{r}notizie/feed.xml">Notizie in RSS</a></li></ul></div>
<div class="fondo"><span>Committente responsabile: {e(SITO['committente'])} · <a href="{r}privacy.html">Informativa privacy</a> · <a href="{r}note-legali.html">Note legali</a></span>
{'<span>Bozza dimostrativa: contatti, account e voci segnate «esempio» non sono reali.</span>' if SITO['bozza'] else ''}
<span class="ver">Versione {SITO['versione']} · aggiornato il {data_estesa(OGGI)}</span></div>
</div>
</footer>
{'<div class="bozza" aria-hidden="true">' + ('ANTEPRIMA PRIVATA · CON BOZZE' if ANTEPRIMA else 'BOZZA DIMOSTRATIVA') + '</div>' if SITO['bozza'] or ANTEPRIMA else ''}
<script src="{r}risorse/sito.js" defer></script>
</body>
</html>
'''
    f = OUT / percorso
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(pagina_html, encoding='utf-8')
    PAGINE_FATTE.append(percorso)


def intesta(occhiello, titolo, sotto=''):
    return f'<div class="intesta"><div class="in"><span class="k">{occhiello}</span><h1>{titolo}</h1>' + (f'<p class="sott">{sotto}</p>' if sotto else '') + '</div></div>'


def foto(file, attesa, extra=''):
    """Spazio per una fotografia: mostra `risorse/img/<file>.jpg` se c'è, altrimenti il segnaposto con il nome atteso."""
    return f'<div class="foto vuota{extra}" data-file="{{r}}risorse/img/{file}.jpg" data-et="FOTO DA INSERIRE · {e(attesa)} · risorse/img/{file}.jpg" role="img" aria-label="{e(attesa)}"></div>'


def scheda_notizia(n):
    return f'''<li><a class="scheda riv" href="{{r}}{n['indirizzo']}">{foto(n['file'], n['titolo'])}<span class="tx"><span class="quando">{n['quando']}{segni(n)}</span><strong>{e(n['titolo'])}</strong><p>{e(n.get('sintesi', ''))}</p><span class="vai">Leggi →</span></span></a></li>'''


def riga_evento(v):
    d = v['giorno']
    return f'''<li><a class="evento{' passato' if v['passato'] else ''}" href="{{r}}{v['indirizzo']}"><span class="d"><b>{d.day:02d}</b><small>{MESI3[d.month - 1]} {d.year}</small></span><span><strong>{e(v['titolo'])}</strong><span>{e(v.get('luogo', ''))}{' · ore ' + v['ora'] if v.get('ora') else ''}{' · già svolto' if v['passato'] else ''}{segni(v)}</span></span></a></li>'''


def striscia():
    return '<ol class="striscia">' + ''.join(f'''<li><a href="{{r}}{p['indirizzo']}"><i>{p['numero']}</i>{e(p['titolo'])}</a></li>''' for p in PILASTRI) + '</ol>'


def banda_aderisci(titolo='Il programma si scrive ai tavoli', testo_='Comitati, collettivi, sindacati, singole e singoli: lascia i tuoi contatti, ti scriviamo per gli incontri nel tuo territorio.', q=''):
    return f'<section class="sez su-rosso"><div class="in" style="align-items:flex-start"><h2>{titolo}</h2><p style="max-width:36em;font-size:19px;font-weight:700">{testo_}</p><a class="btn bw" href="{{r}}aderisci.html{q}">Aderisci ora</a></div></section>'


def mappa(corrente=''):
    return '<nav class="mappa" aria-label="Province">' + ''.join(f'''<a class="{c}" href="{{r}}{TERRITORI[p]['indirizzo']}"{' aria-current="page"' if p == corrente else ''}>{s}<small>{p}</small></a>''' for s, p, c in SIGLE if p in TERRITORI) + '</nav>'


# ---------- costruzione ----------
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(RIS, OUT / 'risorse')
(OUT / '.nojekyll').write_text('')

# Home
verbi = ''.join(f"<li>{e(p['verbo'])}</li>" for p in PILASTRI)
prossimo = ''
if FUTURI:
    v = FUTURI[0]
    prossimo = f'''<section class="sez su-nero"><div class="in prossimo"><div><span class="k">Prossimo incontro</span><h2 style="margin:8px 0">{e(v['titolo'])}{ES if v['esempio'] else ''}</h2><p class="quando">{data_estesa(v['giorno'])}{' · ore ' + v['ora'] if v.get('ora') else ''} · {e(v.get('luogo', ''))}</p></div><a class="btn" href="{{r}}{v['indirizzo']}">Tutti i dettagli</a></div></section>'''
pagina('index.html', SITO['nome'], SITO['descrizione'], f'''<section class="apertura">
<div class="sx"><h1>La Sicilia che <img src="{{r}}risorse/loghi/sa-monogramma.svg" alt="SA" width="649" height="418"></h1>
<ul class="verbi">{verbi}</ul>
<div class="azioni"><a class="btn" href="{{r}}aderisci.html">Aderisci ora</a><a class="btn b2" href="{{r}}programma/index.html">Il programma</a></div></div>
<div class="dx"><img src="{{r}}risorse/loghi/sa-contrassegno.svg" alt="Contrassegno {e(SITO['nome_logo'])}" width="430" height="430"></div>
</section>
{prossimo}
<section class="sez"><div class="in"><div class="capo"><div><span class="k">Il programma</span><h2>Sette cose che la Sicilia sa fare</h2></div><a href="{{r}}programma/index.html">Tutto il programma →</a></div>{striscia()}</div></section>
<section class="sez carta"><div class="in"><div class="capo"><div><span class="k">Notizie</span><h2>Che cosa succede</h2></div><a href="{{r}}notizie/index.html">Tutte le notizie →</a></div><ul class="griglia tre">{''.join(scheda_notizia(n) for n in NOTIZIE[:3])}</ul></div></section>
<section class="sez"><div class="in due"><div><span class="k">Territori</span><h2 style="margin:8px 0 14px">Nove province, un tavolo in ognuna</h2><p style="max-width:32em;font-size:18px">Scegli la tua provincia: trovi le lotte aperte, il prossimo incontro e come partecipare.</p></div>{mappa()}</div></section>
{banda_aderisci()}''', dati={'@context': 'https://schema.org', '@type': 'Organization', 'name': SITO['nome'], 'url': BASE, 'logo': BASE + 'risorse/loghi/sa-contrassegno.png', 'description': SITO['descrizione']})

# Chi siamo
p = PAGINE['chi-siamo']
pagina('chi-siamo.html', p['titolo'], p['sintesi'], intesta(p['occhiello'], e(p['titolone']), e(p['sintesi'])) + f'<section class="sez" style="padding-top:0"><div class="in"><div class="testo">{testo(p["corpo"])}</div></div></section>' + banda_aderisci(), 'chi-siamo', [('', 'Chi siamo')])

# Programma
schede = ''.join(f'''<li><a class="scheda pil riv" href="{{r}}{p['indirizzo']}"><span class="tx"><span class="n">{p['numero']}</span><strong>{e(p['titolo'])}</strong><p>{e(p['sintesi'])}</p><span class="vai">Le proposte →</span></span></a></li>''' for p in PILASTRI)
pagina('programma/index.html', 'Il programma', 'Sette pilastri per un’alternativa popolare in Sicilia: pace, lavoro, salute, acqua, diritti, accoglienza, territorio.', intesta('Il programma', 'La Sicilia che SA', 'Sette pilastri. È una bozza: i testi vengono dall’appello per l’assemblea verso le Regionali 2027 e aspettano l’approvazione del coordinamento.') + f'<section class="sez carta"><div class="in"><ul class="griglia tre">{schede}</ul><div class="azioni" style="justify-content:flex-start"><a class="btn b2" href="{{r}}metodo.html">Come lavoriamo: i due binari</a><a class="btn b2" href="{{r}}programma/tutto.html">Tutto in una pagina</a></div></div></section>' + banda_aderisci(), 'programma', [('', 'Programma')])
for i, p in enumerate(PILASTRI):
    prima, dopo = PILASTRI[i - 1], PILASTRI[(i + 1) % len(PILASTRI)]
    incontri = [v for v in FUTURI if v.get('pilastro') == p['numero']]
    collegate = [n for n in NOTIZIE if n.get('pilastro') == p['numero']]
    sz = sezioni(p['corpo'])
    binari = ''.join(f'<div class="binario b{k}"><span class="k">{"Primo" if k == 1 else "Secondo"} binario</span><h2>{e(t)}</h2><div class="testo">{testo(c)}</div></div>' for k, (t, c) in enumerate(sz[:2], 1))
    resto = ''.join(f'<h2>{e(t)}</h2>{testo(c)}' for t, c in sz[2:])
    lato = f'''<aside class="lato"><h3>Il tavolo di questo pilastro</h3><p style="font-size:15px">Aperto a comitati, collettivi, sindacati e singole persone.</p>{'<ul class="eventi">' + ''.join(riga_evento(v) for v in incontri) + '</ul>' if incontri else '<p style="font-size:15px;font-weight:700">Nessun incontro in calendario per ora.</p>'}<a class="btn" href="{{r}}aderisci.html">Partecipa al tavolo</a><a class="vai-a" href="{{r}}metodo.html">Che cosa sono i due binari →</a></aside>'''
    notizie_p = f'<h2>Notizie su questo pilastro</h2><ul class="griglia tre">{"".join(scheda_notizia(n) for n in collegate[:3])}</ul>' if collegate else ''
    pagina(p['indirizzo'], p['titolo'], p['sintesi'], intesta(f"Pilastro {p['numero']} di {len(PILASTRI):02d}", e(p['titolo']), e(p['slogan'])) + f'''<section class="sez" style="padding-top:0"><div class="in">{foto('pilastro-' + p['numero'], p['foto_attesa'])}<p class="sintesi">{e(p['sintesi'])}</p><div class="binari">{binari}</div><div class="due"><div class="testo">{resto}</div>{lato}</div>{notizie_p}<nav class="vicini" aria-label="Altri pilastri"><a href="{{r}}{prima['indirizzo']}">← {prima['numero']} {e(prima['titolo'])}</a><a href="{{r}}{dopo['indirizzo']}">{dopo['numero']} {e(dopo['titolo'])} →</a></nav></div></section>''' + banda_aderisci(f"La Sicilia che sa {e(p['verbo'])}", 'Dai forza a questa proposta: aderisci e partecipa al tavolo.'), 'programma', [('programma/index.html', 'Programma'), ('', p['titolo'])], og='pilastro-' + p['numero'])

# Tutto il programma in una pagina sola, da stampare o salvare in PDF
tutto = ''.join(f'''<article class="blocco-p"><span class="k">Pilastro {p['numero']}</span><h2>{e(p['titolo'])}</h2><p class="sintesi">{e(p['sintesi'])}</p>{''.join(f'<h3>{e(t)}</h3><div class="testo">{testo(c)}</div>' for t, c in sezioni(p['corpo'])[:2])}</article>''' for p in PILASTRI)
pagina('programma/tutto.html', 'Il programma completo', 'I sette pilastri in una pagina sola, da leggere di seguito o da stampare.', intesta('Il programma', 'Tutto in una pagina', 'I sette pilastri di seguito. Bozza in attesa di approvazione del coordinamento.') + f'<section class="sez" style="padding-top:0"><div class="in"><div class="azioni" style="justify-content:flex-start"><button class="btn bn" type="button" onclick="window.print()">Stampa o salva in PDF</button><a class="btn b2" href="{{r}}programma/index.html">Torna ai pilastri</a></div>{tutto}</div></section>', 'programma', [('programma/index.html', 'Programma'), ('', 'Tutto in una pagina')])

# Il metodo
p = PAGINE['metodo']
pagina('metodo.html', p['titolo'], p['sintesi'], intesta(p['occhiello'], e(p['titolone']), e(p['sintesi'])) + f'<section class="sez" style="padding-top:0"><div class="in"><div class="testo">{testo(p["corpo"])}</div><div class="azioni" style="justify-content:flex-start"><a class="btn" href="{{r}}programma/index.html">Vai al programma</a></div></div></section>' + banda_aderisci(), 'programma', [('programma/index.html', 'Programma'), ('', 'Come lavoriamo')])

# Notizie
pagina('notizie/index.html', 'Notizie', 'Le notizie del coordinamento: incontri, presìdi, tavoli.', intesta('Notizie', 'Che cosa succede') + f'<section class="sez" style="padding:0 var(--lato) 24px"><div class="in"><a class="vai-a" href="{{r}}cerca.html">Cerca nel sito →</a></div></section><section class="sez carta"><div class="in"><ul class="griglia tre">{"".join(scheda_notizia(n) for n in NOTIZIE)}</ul></div></section>', 'notizie', [('', 'Notizie')])
for n in NOTIZIE:
    pil = next((p for p in PILASTRI if p['numero'] == n.get('pilastro')), None); terr = TERRITORI.get(n.get('provincia', ''))
    legami = ''.join([f'<li><a href="{{r}}{pil["indirizzo"]}">Pilastro {pil["numero"]} · {e(pil["titolo"])}</a></li>' if pil else '', f'<li><a href="{{r}}{terr["indirizzo"]}">Provincia di {e(n["provincia"])}</a></li>' if terr else ''])
    legami = f'<ul class="etichette legami">{legami}</ul>' if legami else ''
    fonte = f'''<p class="avviso">Fonte esterna: <a href="{n['fonte']}" rel="noopener">{e(n.get('fonte_nome', 'leggi l’articolo'))} →</a></p>''' if n.get('fonte') else ''
    pagina(n['indirizzo'], n['titolo'], n.get('sintesi', ''), intesta(f"{n['quando']}{' · ' + e(n['luogo']) if n.get('luogo') else ''}{segni(n)}", e(n['titolo']), e(n.get('sintesi', ''))) + f'''<section class="sez" style="padding-top:0"><div class="in">{foto(n['file'], n['titolo'])}<div class="testo">{testo(n['corpo'])}{fonte}</div>{legami}<nav class="vicini"><a href="{{r}}notizie/index.html">← Tutte le notizie</a></nav></div></section>''' + banda_aderisci(), 'notizie', [('notizie/index.html', 'Notizie'), ('', n['titolo'])], tipo='article',
           dati={'@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': n['titolo'], 'datePublished': n['data'], 'publisher': {'@type': 'Organization', 'name': SITO['nome']}})
# Notizie in RSS
voci_rss = ''.join(f"<item><title>{e(n['titolo'])}</title><link>{BASE}{n['indirizzo']}</link><guid>{BASE}{n['indirizzo']}</guid><pubDate>{n['giorno'].strftime('%a, %d %b %Y')} 09:00:00 +0100</pubDate><description>{e(n.get('sintesi', ''))}</description></item>" for n in NOTIZIE if not n['esempio'] and not n['bozza'])
(OUT / 'notizie' / 'feed.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{e(SITO["nome"])} — Notizie</title><link>{BASE}</link><description>{e(SITO["descrizione"])}</description><language>it</language>{voci_rss}</channel></rss>\n', encoding='utf-8')

# Agenda
futuri = ''.join(riga_evento(v) for v in FUTURI) or '<li><p style="padding:16px 0;font-weight:700">Nessun incontro in calendario per ora.</p></li>'
passati = ''.join(riga_evento(v) for v in reversed([v for v in EVENTI if v['passato']]))
pagina('agenda/index.html', 'Agenda', 'Assemblee, tavoli e presìdi del coordinamento in Sicilia.', intesta('Agenda', 'Dove ci vediamo') + f'''<section class="sez" style="padding-top:0"><div class="in"><h2>Prossimi incontri</h2><ul class="eventi">{futuri}</ul>{'<h2 style="margin-top:20px">Già svolti</h2><ul class="eventi">' + passati + '</ul>' if passati else ''}</div></section>''' + banda_aderisci('Vuoi sapere quando siamo vicino a te?', 'Lascia i tuoi contatti e la provincia: ti scriviamo noi.'), 'agenda', [('', 'Agenda')])
for v in EVENTI:
    d = v['giorno']
    ics = ''
    if not v['passato']:
        ora = v.get('ora', '').replace(':', '')
        inizio = f"{d:%Y%m%d}T{ora}00" if ora else f'{d:%Y%m%d}'
        fine = f"{d:%Y%m%d}T{int(ora[:2]) + 2:02d}{ora[2:]}00" if ora else f'{d + datetime.timedelta(days=1):%Y%m%d}'
        tz = ';TZID=Europe/Rome' if ora else ';VALUE=DATE'
        nome_ics = v['file'] + '.ics'
        (OUT / 'agenda' / nome_ics).write_text('\r\n'.join(['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Sinistra per l\'Alternativa//Agenda//IT', 'BEGIN:VEVENT', f"UID:{v['file']}@sinistra-alternativa-sicilia", f'DTSTAMP:{OGGI:%Y%m%d}T000000Z', f'DTSTART{tz}:{inizio}', f'DTEND{tz}:{fine}', 'SUMMARY:' + v['titolo'].replace(',', '\\,'), 'LOCATION:' + v.get('luogo', '').replace(',', '\\,'), f"URL:{BASE}{v['indirizzo']}", 'END:VEVENT', 'END:VCALENDAR', '']), encoding='utf-8')
        ics = f'<a class="btn bn" href="{nome_ics}" download>Salva nel calendario</a>'
    pil = next((p for p in PILASTRI if p['numero'] == v.get('pilastro')), None)
    terr = TERRITORI.get(v.get('provincia', ''))
    scheda = f'''<aside class="lato"><dl><dt>Quando</dt><dd>{data_estesa(d)}{' · ore ' + v['ora'] if v.get('ora') else ''}</dd><dt>Dove</dt><dd>{e(v.get('luogo', 'da indicare'))}</dd>{f'<dt>Provincia</dt><dd><a href="{{r}}{terr["indirizzo"]}">{e(v["provincia"])}</a></dd>' if terr else ''}{f'<dt>Pilastro</dt><dd><a href="{{r}}{pil["indirizzo"]}">{pil["numero"]} · {e(pil["titolo"])}</a></dd>' if pil else ''}</dl>{ics}<a class="btn" href="{{r}}aderisci.html{'?provincia=' + v['provincia'] if v.get('provincia') else ''}">{'Aderisci' if v['passato'] else 'Ci sarò: aderisci'}</a></aside>'''
    pagina(v['indirizzo'], v['titolo'], f"{data_estesa(d)} · {v.get('luogo', '')}", intesta(f"{'Incontro già svolto' if v['passato'] else 'Incontro'}{ES if v['esempio'] else ''}", e(v['titolo'])) + f'''<section class="sez" style="padding-top:0"><div class="in"><div class="due"><div class="testo">{testo(v['corpo']) if v['corpo'] else '<p>Dettagli in arrivo.</p>'}</div>{scheda}</div><nav class="vicini"><a href="{{r}}agenda/index.html">← Tutta l’agenda</a></nav></div></section>''', 'agenda', [('agenda/index.html', 'Agenda'), ('', v['titolo'])],
           dati=None if v['esempio'] else {'@context': 'https://schema.org', '@type': 'Event', 'name': v['titolo'], 'startDate': v['data'] + (f"T{v['ora']}" if v.get('ora') else ''), 'location': {'@type': 'Place', 'name': v.get('luogo', '')}, 'organizer': {'@type': 'Organization', 'name': SITO['nome']}})

# Territori
pagina('territori/index.html', 'Territori', 'Nove province, un tavolo in ognuna: le lotte, gli incontri, come partecipare.', intesta('Territori', 'Dov’è la tua Sicilia?', 'Scegli la provincia: trovi le lotte aperte, il prossimo incontro e come partecipare.') + f'''<section class="sez" style="padding-top:0"><div class="in">{mappa()}<p style="font-size:13px;color:var(--grigio)">Mappa schematica: le caselle seguono la posizione delle province, non i confini.</p><ul class="griglia tre">{''.join(f'<li><a class="scheda riv" href="{{r}}{t["indirizzo"]}"><span class="tx"><strong>{e(nome)}</strong><p>{e(t.get("lotte", ""))}</p><span class="vai">Vai →</span></span></a></li>' for nome, t in sorted(TERRITORI.items()))}</ul></div></section>''', 'territori', [('', 'Territori')])
for nome, t in TERRITORI.items():
    inc = [v for v in EVENTI if v.get('provincia') == nome]
    not_p = [n for n in NOTIZIE if n.get('provincia') == nome]
    lotte = ''.join(f'<li>{e(x.strip())}</li>' for x in t.get('lotte', '').split(','))
    pagina(t['indirizzo'], f'Provincia di {nome}', f"Le lotte e gli incontri del coordinamento in provincia di {nome}: {t.get('lotte', '')}.", intesta(f"Territori{ES if t['esempio'] else ''}", e(nome)) + f'''<section class="sez" style="padding-top:0"><div class="in"><div class="due"><div class="testo"><h2 style="margin-top:0">Le lotte</h2><ul class="etichette" style="flex-direction:row;flex-wrap:wrap">{lotte}</ul>{testo(t['corpo'])}<h2>Gli incontri</h2>{'<ul class="eventi" style="gap:0">' + ''.join(riga_evento(v) for v in inc) + '</ul>' if inc else '<p>Nessun incontro in calendario per ora in questa provincia.</p>'}</div>
<aside class="lato"><dl><dt>Referente</dt><dd>{e(t.get('referente', 'da indicare'))}</dd><dt>Contatto</dt><dd>{e(t.get('contatto', 'da indicare'))}</dd></dl><a class="btn" href="{{r}}aderisci.html?provincia={nome}">Aderisci da {e(nome)}</a></aside></div>
{'<h2>Notizie da questa provincia</h2><ul class="griglia tre">' + ''.join(scheda_notizia(n) for n in not_p[:3]) + '</ul>' if not_p else ''}<h2>Le altre province</h2>{mappa(nome)}</div></section>''', 'territori', [('territori/index.html', 'Territori'), ('', nome)])

# Aderisci
opz = ''.join(f'<option>{p}</option>' for p in PROVINCE)
pagina('aderisci.html', 'Aderisci', 'Aderisci al coordinamento: lascia i tuoi contatti, ti scriviamo per gli incontri nel tuo territorio.', intesta('Partecipa', 'Aderisci al coordinamento', 'Comitati, collettivi, sindacati, singole e singoli: lascia i tuoi contatti, ti scriviamo per i tavoli e gli incontri nel tuo territorio.') + f'''<section class="sez carta" style="padding-top:36px"><div class="in due">
<form id="adesione" novalidate data-invia-a="{e(SITO['modulo']['invia_a'])}">
<label>Nome e cognome<input type="text" name="nome" autocomplete="name"></label>
<label>Email<input type="email" name="email" autocomplete="email" inputmode="email"></label>
<div class="riga2"><label>Comune<input type="text" name="comune" autocomplete="address-level2"></label><label>Provincia<select name="provincia"><option value="">Scegli…</option>{opz}</select></label></div>
<label class="consenso"><input type="checkbox" name="consenso"><span>Ho letto l’<a href="{{r}}privacy.html">informativa privacy</a> e acconsento a essere ricontattato dal coordinamento.</span></label>
<button class="btn" type="submit">Invia adesione</button>
<p class="esito" role="status" aria-live="polite"></p>
</form>
<aside class="lato"><h3>Che cosa succede dopo</h3><ul class="testo" style="font-size:16px"><li>Ricevi una conferma.</li><li>Ti scriviamo quando c’è un incontro nella tua provincia.</li><li>Puoi partecipare a uno dei sette tavoli del programma.</li></ul>{'<p class="avviso">Il modulo non è ancora collegato: in questa bozza non invia e non conserva nulla.</p>' if not SITO['modulo']['invia_a'] else ''}</aside>
</div></section>''', 'aderisci', [('', 'Aderisci')])

# Contatti
c = SITO['contatti']
pagina('contatti.html', 'Contatti e stampa', 'Come contattare il coordinamento. Materiali per la stampa.', intesta('Contatti', 'Scrivici, chiamaci, vieni') + f'''<section class="sez" style="padding-top:0"><div class="in due"><div class="testo">{'<p class="avviso">Contatti e account qui sotto sono segnaposto: vanno sostituiti con quelli veri del coordinamento.</p>' if not c['reali'] else ''}
<h2 style="margin-top:0">Coordinamento regionale</h2><ul><li>Email: {e(c['email'])}</li><li>Telefono: {e(c['telefono'])}</li><li>Sede: {e(c['sede'])}</li></ul>
<h2>Social</h2><ul><li>Facebook — {e(c['facebook'])}</li><li>Instagram — {e(c['instagram'])}</li></ul>
<h2>Per la stampa</h2><p>Simbolo e logo in formato vettoriale:</p><ul><li><a href="{{r}}risorse/loghi/sa-contrassegno.svg" download>Contrassegno (SVG)</a></li><li><a href="{{r}}risorse/loghi/sa-contrassegno.png" download>Contrassegno (PNG)</a></li><li><a href="{{r}}risorse/loghi/sa-logo-orizzontale.svg" download>Logo orizzontale (SVG)</a></li></ul></div>
<aside class="lato"><h3>Nei territori</h3><p style="font-size:15px">Ogni provincia ha la sua pagina con referente e incontri.</p><a class="btn b2" href="{{r}}territori/index.html">Trova la tua provincia</a><a class="btn" href="{{r}}aderisci.html">Aderisci</a></aside></div></section>''', 'contatti', [('', 'Contatti')])

# Ricerca nel sito: un indice leggero letto dal browser, nessun servizio esterno
INDICE = [{'t': p['titolo'], 'd': p['sintesi'], 'u': p['indirizzo'], 'k': 'Programma', 'x': re.sub(r'[#*\[\]()-]', ' ', p['corpo'])} for p in PILASTRI]
INDICE += [{'t': n['titolo'], 'd': n.get('sintesi', ''), 'u': n['indirizzo'], 'k': 'Notizie · ' + n['quando'], 'x': re.sub(r'[#*\[\]()-]', ' ', n['corpo'])} for n in NOTIZIE]
INDICE += [{'t': v['titolo'], 'd': data_estesa(v['giorno']) + ' · ' + v.get('luogo', ''), 'u': v['indirizzo'], 'k': 'Agenda', 'x': v['corpo']} for v in EVENTI]
INDICE += [{'t': 'Provincia di ' + nome, 'd': t.get('lotte', ''), 'u': t['indirizzo'], 'k': 'Territori', 'x': ''} for nome, t in TERRITORI.items()]
INDICE += [{'t': 'Chi siamo', 'd': PAGINE['chi-siamo']['sintesi'], 'u': 'chi-siamo.html', 'k': 'Il coordinamento', 'x': PAGINE['chi-siamo']['corpo']}, {'t': 'Come lavoriamo', 'd': PAGINE['metodo']['sintesi'], 'u': 'metodo.html', 'k': 'Il metodo', 'x': PAGINE['metodo']['corpo']}, {'t': 'Aderisci', 'd': 'Lascia i tuoi contatti', 'u': 'aderisci.html', 'k': 'Partecipa', 'x': 'adesione modulo iscriversi partecipare'}]
(OUT / 'risorse' / 'indice.json').write_text(json.dumps(INDICE, ensure_ascii=False), encoding='utf-8')
pagina('cerca.html', 'Cerca nel sito', 'Cerca fra programma, notizie, incontri e territori.', intesta('Cerca', 'Che cosa cerchi?') + '''<section class="sez" style="padding-top:0"><div class="in"><form class="cerca" role="search" onsubmit="return false"><label>Parole da cercare<input type="text" id="q" name="q" autocomplete="off" autofocus></label></form><p id="conta" role="status" aria-live="polite" style="font-weight:700"></p><ul class="eventi" id="esiti"></ul><noscript><p class="avviso">La ricerca ha bisogno di JavaScript. In alternativa usa il menu.</p></noscript></div></section>''', '', [('', 'Cerca')])

# Pagine di servizio
for chiave in ('privacy', 'note-legali'):
    p = PAGINE[chiave]
    pagina(f'{chiave}.html', p['titolo'], p['sintesi'], intesta(p['occhiello'], e(p['titolo'])) + f'<section class="sez" style="padding-top:0"><div class="in"><div class="testo">{testo(p["corpo"])}</div></div></section>', '', [('', p['titolo'])])
pagina('404.html', 'Pagina non trovata', 'La pagina cercata non esiste o è stata spostata.', intesta('Errore 404', 'Questa pagina non c’è', 'Forse è stata spostata. Riparti da qui:') + f'<section class="sez" style="padding-top:0"><div class="in"><div class="azioni" style="justify-content:flex-start"><a class="btn" href="{BASE}index.html">Pagina iniziale</a><a class="btn b2" href="{BASE}programma/index.html">Il programma</a></div></div></section>')
# la pagina 404 è servita da qualunque indirizzo: i suoi collegamenti devono essere assoluti
f404 = OUT / '404.html'
f404.write_text(re.sub(r'(href|src)="(?!https?:|#|mailto:)([^"]+)"', lambda m: f'{m.group(1)}="{BASE}{m.group(2)}"', f404.read_text(encoding='utf-8')), encoding='utf-8')

# Mappa del sito e istruzioni per i motori di ricerca
indicizzabili = [p for p in PAGINE_FATTE if p != '404.html']
(OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f"<url><loc>{BASE}{'' if p == 'index.html' else p}</loc></url>\n" for p in indicizzabili) + '</urlset>\n', encoding='utf-8')
(OUT / 'robots.txt').write_text((f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n' if SITO['indicizzabile'] else 'User-agent: *\nDisallow: /\n'), encoding='utf-8')
print(f'Sito costruito: {len(PAGINE_FATTE)} pagine in {OUT.name}/ · versione {SITO["versione"]}' + (' · ANTEPRIMA con bozze' if ANTEPRIMA else '') + (f' · bozze lasciate fuori: {len(ESCLUSE)} ({", ".join(ESCLUSE)})' if ESCLUSE else ''))
