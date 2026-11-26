#!/usr/bin/env python3
"""Controlla il sito costruito in `pubblico/`. Se trova un errore esce con codice 1 e la pubblicazione si ferma.
Solo libreria standard.  Uso:  python3 controlla.py
"""
import pathlib, re, sys
from html.parser import HTMLParser
OUT = pathlib.Path(__file__).parent / 'pubblico'
errori, avvisi = [], []


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
        if not dest.exists(): (avvisi if '/risorse/img/' in str(dest) else errori).append(f'{nome}: ' + ('fotografia non ancora scaricata' if '/risorse/img/' in str(dest) else 'collegamento rotto') + f' → {h}')
for t, dove in titoli.items():
    if len(dove) > 1: errori.append(f'titolo ripetuto «{t}» in: {", ".join(dove)}')
for f in OUT.rglob('*'):
    # i materiali da scaricare sono pesanti per natura: si scaricano apposta, non si caricano con la pagina
    if f.is_file() and f.stat().st_size > 600_000 and 'risorse/materiali/' not in f.as_posix(): avvisi.append(f'{f.relative_to(OUT)}: file pesante ({f.stat().st_size // 1024} KB)')
for a in avvisi: print('AVVISO  ', a)
for x in errori: print('ERRORE  ', x)
# Regola 8: fotografie sempre ottimizzate per il web
for f in sorted((OUT / 'risorse' / 'img').glob('*')):
    if f.suffix.lower() in ('.png', '.jpeg', '.webp', '.tif', '.tiff', '.gif', '.bmp', '.heic', '.heif', '.avif'): errori.append(f'risorse/img/{f.name}: fotografia non convertita in JPEG ottimizzato')
    elif f.suffix == '.jpg' and f.stat().st_size > 350 * 1024: errori.append(f'risorse/img/{f.name}: fotografia non ottimizzata ({f.stat().st_size // 1024} KB, massimo 350)')
print(f'Controllate {len(pagine)} pagine: {len(errori)} errori, {len(avvisi)} avvisi')
sys.exit(1 if errori else 0)
