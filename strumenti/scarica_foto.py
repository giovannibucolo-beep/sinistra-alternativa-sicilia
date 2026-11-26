"""Scarica da Wikimedia Commons le fotografie elencate in contenuti/foto.json dentro risorse/img/.
Gira nella pubblicazione automatica, prima di costruisci.py. Se una foto non si scarica il sito
resta con il segnaposto: la pubblicazione non si ferma."""
import json, pathlib, sys, urllib.parse, urllib.request

RADICE = pathlib.Path(__file__).resolve().parent.parent
IMG = RADICE / 'risorse' / 'img'
IMG.mkdir(parents=True, exist_ok=True)
AGENTE = {'User-Agent': 'SinistraAlternativaSicilia-sito/1.0 (https://github.com/giovannibucolo-beep/sinistra-alternativa-sicilia)'}


def apri(indirizzo):
    return urllib.request.urlopen(urllib.request.Request(indirizzo, headers=AGENTE), timeout=60).read()


foto = json.loads((RADICE / 'contenuti' / 'foto.json').read_text(encoding='utf-8'))
mancanti = 0
for f in foto:
    arrivo = IMG / (f['file'] + '.jpg')
    if arrivo.exists():
        continue
    try:
        q = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'prop': 'imageinfo', 'iiprop': 'url', 'iiurlwidth': 1920, 'titles': 'File:' + f['commons']})
        dati = json.loads(apri('https://commons.wikimedia.org/w/api.php?' + q))
        info = next(iter(dati['query']['pages'].values()))['imageinfo'][0]
        corpo = apri(info.get('thumburl') or info['url'])
        if corpo[:2] != b'\xff\xd8':
            raise ValueError('non è un JPEG')
        arrivo.write_bytes(corpo)
        print(f"scaricata {arrivo.name} ({len(corpo) // 1024} KB)")
    except Exception as errore:
        mancanti += 1
        print(f"NON scaricata {arrivo.name}: {errore}", file=sys.stderr)
print(f"{len(foto) - mancanti} fotografie su {len(foto)} presenti")
