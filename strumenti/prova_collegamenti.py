#!/usr/bin/env python3
"""Controlla che le fonti citate negli articoli esistano ancora.

Le pagine delle testate locali e dei comunicati sindacali spariscono o cambiano indirizzo.
Il giorno in cui qualcuno contesta un nostro dato e il collegamento alla fonte dà 404, il
problema non è tecnico. Questo esame apre ogni indirizzo esterno del sito e dice quali non
rispondono più, e in quale pagina stanno.

Serve il sito già costruito e una rete che arrivi fuori. Si lancia con:
  python3 strumenti/prova_collegamenti.py
"""
import concurrent.futures, pathlib, re, sys, urllib.error, urllib.request

RADICE = pathlib.Path(__file__).resolve().parent.parent
OUT = RADICE / 'pubblico'
# alcuni siti rifiutano le richieste senza un browser dichiarato: non è un collegamento rotto
TESTA = {'User-Agent': 'Mozilla/5.0 (compatible; SinistraAlternativaSicilia/1.0; controllo collegamenti)'}
ATTESA = 25
# i servizi di condivisione non sono fonti: sono pulsanti, e rispondono solo al browser
SALTA = ('wa.me', 't.me/share', 'facebook.com/sharer', 'creativecommons.org/licenses')

if not OUT.exists():
    raise SystemExit('Prima costruisci il sito: python3 costruisci.py')

dove = {}
for f in sorted(OUT.rglob('*.html')):
    for u in re.findall(r'href="(https?://[^"]+)"', f.read_text(encoding='utf-8')):
        u = u.split('#')[0]
        if 'github.io' in u or any(s in u for s in SALTA):
            continue
        dove.setdefault(u, set()).add(f.relative_to(OUT).as_posix())


def prova(u):
    for metodo in ('HEAD', 'GET'):
        try:
            r = urllib.request.Request(u, headers=TESTA, method=metodo)
            with urllib.request.urlopen(r, timeout=ATTESA) as risposta:
                if risposta.status < 400:
                    return None
        except urllib.error.HTTPError as err:
            # 403 e 405 su HEAD capitano con siti che non gradiscono: si riprova con GET
            if err.code in (403, 405) and metodo == 'HEAD':
                continue
            return f'{err.code}'
        except Exception as err:
            if metodo == 'GET':
                return type(err).__name__
    return None


rotti = []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for u, esito in zip(dove, pool.map(prova, dove)):
        if esito:
            rotti.append((u, esito, sorted(dove[u])))

# Se cade tutto, non sono i siti a essere spariti: è questa macchina che non arriva fuori.
# Dirlo apertamente, invece di presentare trentatré falsi allarmi come collegamenti rotti.
if dove and len(rotti) == len(dove):
    print(f'Nessuno dei {len(dove)} indirizzi risponde: questa macchina non raggiunge la rete esterna.')
    print('L’esame va lanciato dove la rete c’è: lo fa da solo il controllo settimanale su GitHub.')
    raise SystemExit(0)

for u, esito, pagine in sorted(rotti, key=lambda x: x[0]):
    print(f'{esito} · {u}\n        nelle pagine: {", ".join(pagine)}')
print(f'\ncollegamenti esterni controllati: {len(dove)} · non raggiungibili: {len(rotti)}')
sys.exit(1 if rotti else 0)
