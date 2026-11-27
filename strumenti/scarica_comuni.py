#!/usr/bin/env python3
"""Scrive `contenuti/comuni.json`: ogni comune siciliano con la sua provincia.

Serve a «Cosa succede vicino a me»: chi scrive il nome del proprio paese deve arrivare
al tavolo giusto senza sapere a quale provincia appartiene. I dati vengono da una
raccolta pubblica dei codici ISTAT dei comuni italiani (matteocontrini/comuni-json),
filtrata sulla Sicilia. Si rilancia quando cambia l'assetto dei comuni.
"""
import json, pathlib, urllib.request

FONTE = 'https://raw.githubusercontent.com/matteocontrini/comuni-json/master/comuni.json'
ARRIVO = pathlib.Path(__file__).resolve().parent.parent / 'contenuti' / 'comuni.json'
# Le province indicate nel sito: i tavoli sono nove, le città metropolitane comprese.
NOSTRE = {'Agrigento', 'Caltanissetta', 'Catania', 'Enna', 'Messina', 'Palermo', 'Ragusa', 'Siracusa', 'Trapani'}

with urllib.request.urlopen(FONTE, timeout=120) as r:
    tutti = json.load(r)

comuni = {}
for c in tutti:
    if c['regione']['nome'] != 'Sicilia':
        continue
    prov = c['provincia']['nome']
    if prov not in NOSTRE:
        raise SystemExit(f'Provincia inattesa: {prov} ({c["nome"]}). Controlla l\'elenco dei tavoli.')
    comuni[c['nome']] = prov

# La raccolta a monte si ferma prima del 2021 e non ha Misiliscemi, istituito il 20 febbraio
# 2021 per distacco dal comune di Trapani (legge regionale 10 febbraio 2021, n. 3): è il 391°
# comune siciliano e il 25° della provincia di Trapani. Lo aggiungiamo qui finché non arriva.
comuni.setdefault('Misiliscemi', 'Trapani')

if len(comuni) != 391:
    print(f'Attenzione: {len(comuni)} comuni, ne erano attesi 391. Controlla la fonte.')

ARRIVO.write_text(json.dumps(dict(sorted(comuni.items())), ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
print(f'{len(comuni)} comuni → {ARRIVO.name}')
