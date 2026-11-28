#!/usr/bin/env python3
"""Rete di sicurezza per chi tocca il generatore: il sito che esce adesso è identico
a quello che usciva prima delle modifiche?

Costruisce il sito due volte — una dall'ultima versione registrata in git, una dai
file come sono adesso — e confronta file per file. Serve quando si cambia il codice
e l'uscita NON deve cambiare: se cambia qualcosa che non doveva, qui si vede quale.

  python3 strumenti/prova_uscita.py            confronta con l'ultima versione in git
  python3 strumenti/prova_uscita.py HEAD~3     confronta con una versione più indietro

Non c'è nessun file di impronte da tenere aggiornato: il paragone è sempre con git.
Le immagini scaricate restano fuori dal confronto: non le produce il generatore.
"""
import hashlib, pathlib, shutil, subprocess, sys, tempfile

RADICE = pathlib.Path(__file__).resolve().parent.parent
RIFERIMENTO = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
SALTA = ('risorse/img/',)


def costruisci(dove):
    subprocess.run([sys.executable, 'costruisci.py'], cwd=dove, check=True, stdout=subprocess.DEVNULL)
    out = pathlib.Path(dove) / 'pubblico'
    d = {}
    for f in sorted(out.rglob('*')):
        if f.is_file():
            r = f.relative_to(out).as_posix()
            if not any(r.startswith(s) for s in SALTA):
                d[r] = hashlib.sha256(f.read_bytes()).hexdigest()
    return d


with tempfile.TemporaryDirectory() as tmp:
    albero = pathlib.Path(tmp) / 'prima'
    albero.mkdir()
    archivio = subprocess.run(['git', 'archive', RIFERIMENTO], cwd=RADICE, check=True, capture_output=True).stdout
    subprocess.run(['tar', '-x', '-C', str(albero)], input=archivio, check=True)
    # le foto scaricate non sono in git: senza di loro le due costruzioni non sarebbero confrontabili
    if (RADICE / 'risorse' / 'img').exists():
        shutil.copytree(RADICE / 'risorse' / 'img', albero / 'risorse' / 'img', dirs_exist_ok=True)
    prima = costruisci(albero)

dopo = costruisci(RADICE)

spariti = sorted(set(prima) - set(dopo))
nuovi = sorted(set(dopo) - set(prima))
cambiati = sorted(k for k in set(prima) & set(dopo) if prima[k] != dopo[k])

for titolo, elenco in (('sparito', spariti), ('nuovo', nuovi), ('diverso', cambiati)):
    for k in elenco[:25]:
        print(f'{titolo}: {k}')
    if len(elenco) > 25:
        print(f'{titolo}: e altri {len(elenco) - 25}')

if spariti or nuovi or cambiati:
    print(f'\nRispetto a {RIFERIMENTO} l’uscita è cambiata: '
          f'{len(spariti)} spariti, {len(nuovi)} nuovi, {len(cambiati)} diversi.')
    raise SystemExit(1)

print(f'{len(dopo)} file: uscita identica a {RIFERIMENTO}.')
