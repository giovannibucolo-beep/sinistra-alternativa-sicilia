"""Dal testo scritto dai compagni all'HTML: titoli, capoversi, elenchi, numeri in evidenza.

Nessuna di queste funzioni sa niente del sito: prendono testo e restituiscono testo.
Per questo si leggono, si correggono e si provano da sole.
"""
import html, re, unicodedata

e = html.escape

MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
MESI3 = ['GEN', 'FEB', 'MAR', 'APR', 'MAG', 'GIU', 'LUG', 'AGO', 'SET', 'OTT', 'NOV', 'DIC']


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def data_estesa(d):
    return f'{d.day} {MESI[d.month - 1]} {d.year}'


def sa(t, variante=''):
    """REGOLA DEL SITO: «la Sicilia (che) SA …» si scrive con il monogramma al posto della parola. `variante`: '' su chiaro, 'nero' su fondo nero, 'rosso' su fondo rosso."""
    file = {'': 'sa-monogramma.svg', 'nero': 'sa-monogramma-negativo-su-nero.svg', 'rosso': 'sa-monogramma-bianco.svg'}[variante]
    return re.sub(r'(?i)(sicilia)(\s+che)?\s+sa\b', lambda m: (f'{m.group(1)} <span class="nsa">che ' if m.group(2) else f'<span class="nsa">{m.group(1)} ') + f'<img class="sa" src="{{r}}risorse/loghi/{file}" alt="SA" width="65" height="42"></span>', t)


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


def ics_testo(s):
    """Nel formato dei calendari la virgola, il punto e virgola e la barra rovesciata vanno protetti,
    altrimenti l'appuntamento arriva troncato."""
    return str(s).replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')


def a_gruppi(lista, n):
    return [lista[i:i + n] for i in range(0, len(lista), n)]
