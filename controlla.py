#!/usr/bin/env python3
"""Controlla il sito costruito in `pubblico/`. Se trova un errore esce con codice 1 e la pubblicazione si ferma.
Solo libreria standard.  Uso:  python3 controlla.py
"""
import pathlib, re, sys
from html.parser import HTMLParser
OUT = pathlib.Path(__file__).parent / 'pubblico'
errori, avvisi = [], []
foto_mancanti = set()


class Lettore(HTMLParser):
    def __init__(self):
        super().__init__(); self.link, self.h1, self.img_senza_alt, self.meta, self.titolo, self._in_t, self.ids = [], 0, 0, {}, '', False, set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        if tag in ('a', 'link') and a.get('href'): self.link.append(a['href'])
        if tag in ('img', 'script') and a.get('src'): self.link.append(a['src'])
        if tag == 'h1': self.h1 += 1
        if tag == 'img' and 'alt' not in a: self.img_senza_alt += 1
        if tag == 'meta': self.meta[a.get('name') or a.get('property') or ''] = a.get('content', '')
        if tag == 'title': self._in_t = True

    def handle_endtag(self, tag):
        if tag == 'title': self._in_t = False

    def handle_data(self, d):
        if self._in_t: self.titolo += d


# Il pannello di scrittura non è una pagina del sito: niente titoli, anteprime social o briciole da controllare.
pagine = sorted(f for f in OUT.rglob('*.html') if not f.relative_to(OUT).as_posix().startswith('admin/'))
if not pagine: sys.exit('ERRORE: nessuna pagina in pubblico/. Lancia prima costruisci.py')
titoli = {}
for f in pagine:
    nome = str(f.relative_to(OUT)); L = Lettore(); L.feed(f.read_text(encoding='utf-8'))
    if L.h1 != 1: errori.append(f'{nome}: deve avere un solo titolo principale, ne ha {L.h1}')
    if L.img_senza_alt: errori.append(f'{nome}: {L.img_senza_alt} immagini senza descrizione alternativa')
    if not L.titolo.strip(): errori.append(f'{nome}: manca il titolo della pagina')
    for chiave in ('description', 'og:title', 'og:description', 'og:image'):
        if not L.meta.get(chiave): errori.append(f'{nome}: manca {chiave} (anteprima nei social e nei motori)')
    if len(L.meta.get('description', '')) > 200: avvisi.append(f'{nome}: descrizione lunga ({len(L.meta["description"])} caratteri)')
    titoli.setdefault(L.titolo.strip(), []).append(nome)
    og = L.meta.get('og:image', '')
    if og and not (OUT / 'risorse' / 'og' / og.rsplit('/', 1)[-1]).exists(): errori.append(f'{nome}: immagine di anteprima mancante ({og.rsplit("/", 1)[-1]})')
    # REGOLA: nei titoli «la Sicilia (che) SA» si scrive con il simbolo, non a lettere
    for m in re.finditer(r'<h[12][^>]*>(.*?)</h[12]>', f.read_text(encoding='utf-8'), re.S):
        if re.search(r'(?i)sicilia(\s+che)?\s+sa\b', re.sub(r'<[^>]+>', '', m.group(1))): errori.append(f'{nome}: «SA» scritto a lettere in un titolo, deve essere il simbolo')
    if nome == '404.html': continue
    for h in L.link:
        if re.match(r'(https?:|mailto:|tel:|data:)', h): continue
        percorso, _, ancora = h.partition('#'); percorso = percorso.split('?')[0]
        if not percorso:
            if ancora and ancora not in L.ids: errori.append(f'{nome}: àncora inesistente #{ancora}')
            continue
        dest = (f.parent / percorso).resolve()
        if not dest.exists():
            if '/risorse/img/' in str(dest):
                # In pubblicazione le foto si scaricano prima del controllo: se mancano qui, manca
                # solo la copia locale. Una riga sola invece di una per pagina, o il rumore nasconde il resto.
                foto_mancanti.add(dest.name)
            else:
                errori.append(f'{nome}: collegamento rotto → {h}')
for t, dove in titoli.items():
    if len(dove) > 1: errori.append(f'titolo ripetuto «{t}» in: {", ".join(dove)}')
for f in OUT.rglob('*'):
    # i materiali da scaricare sono pesanti per natura: si scaricano apposta, non si caricano con la pagina
    if f.is_file() and f.stat().st_size > 600_000 and 'risorse/materiali/' not in f.as_posix(): avvisi.append(f'{f.relative_to(OUT)}: file pesante ({f.stat().st_size // 1024} KB)')
if foto_mancanti:
    avvisi.append(f'{len(foto_mancanti)} fotografie non sono sul disco locale: si scaricano in pubblicazione '
                  f'(strumenti/scarica_foto.py per averle anche qui)')
for a in avvisi: print('AVVISO  ', a)
for x in errori: print('ERRORE  ', x)
# Le intestazioni dei contenuti devono essere YAML valido: è ciò che legge anche il pannello di scrittura
import yaml
for f in sorted((OUT.parent / 'contenuti').glob('*/*.md')):
    testa_f = re.match(r'---\n(.*?)\n---', f.read_text(encoding='utf-8'), re.S)
    if not testa_f:
        errori.append(f'contenuti/{f.parent.name}/{f.name}: manca l’intestazione fra le righe ---'); continue
    try:
        if not isinstance(yaml.safe_load(testa_f.group(1)), dict): raise ValueError('non è un elenco di «chiave: valore»')
    except Exception as errore_f:
        errori.append(f'contenuti/{f.parent.name}/{f.name}: intestazione non leggibile dal pannello · {errore_f}')

# Regola 8: fotografie sempre ottimizzate per il web
for f in sorted((OUT / 'risorse' / 'img').glob('*')):
    if f.suffix.lower() in ('.png', '.jpeg', '.webp', '.tif', '.tiff', '.gif', '.bmp', '.heic', '.heif', '.avif'): errori.append(f'risorse/img/{f.name}: fotografia non convertita in JPEG ottimizzato')
    elif f.suffix == '.jpg' and f.stat().st_size > 350 * 1024: errori.append(f'risorse/img/{f.name}: fotografia non ottimizzata ({f.stat().st_size // 1024} KB, massimo 350)')
# L'HTML deve essere valido: un browser perdona quasi tutto, un lettore di schermo e un
# motore di ricerca no. Qui si ferma la pubblicazione, non si segnala soltanto.
try:
    import html5lib
    from html5lib.html5parser import ParseError
    for f in sorted(OUT.rglob('*.html')):
        try:
            html5lib.HTMLParser(strict=True).parse(f.read_text(encoding='utf-8'))
        except ParseError as errore_h:
            errori.append(f'{f.relative_to(OUT)}: HTML non valido · {str(errore_h).splitlines()[0]}')
except ImportError:
    avvisi.append('html5lib non installato: la validità dell’HTML non è stata controllata '
                  '(pip install -r requirements.txt)')

print(f'Controllate {len(pagine)} pagine: {len(errori)} errori, {len(avvisi)} avvisi')
sys.exit(1 if errori else 0)
