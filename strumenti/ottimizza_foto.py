"""Regola 8: ogni fotografia in risorse/img/ viene ottimizzata per il web, qualunque formato abbia.
Esce sempre un JPEG progressivo, largo al massimo 1400 px, senza dati incorporati, sotto i 350 KB.
Gira da solo dentro costruisci.py e nella pubblicazione automatica."""
import pathlib, sys

LATO, PESO = 1400, 350 * 1024
FORMATI = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff', '.gif', '.bmp', '.heic', '.heif', '.avif'}


def ottimizza(cartella):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print('ATTENZIONE: Pillow non installato, fotografie non ottimizzate', file=sys.stderr)
        return 0
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    fatte = 0
    for f in sorted(pathlib.Path(cartella).iterdir()):
        if f.suffix.lower() not in FORMATI:
            continue
        arrivo = f.with_suffix('.jpg')
        try:
            with Image.open(f) as im:
                a_posto = f.suffix == '.jpg' and im.format == 'JPEG' and im.width <= LATO and f.stat().st_size <= PESO and not im.info.get('exif')
                if a_posto:
                    continue
                im = ImageOps.exif_transpose(im)
                if im.mode in ('RGBA', 'LA', 'P'):
                    im = im.convert('RGBA')
                    fondo = Image.new('RGB', im.size, (255, 255, 255))
                    fondo.paste(im, mask=im.split()[-1])
                    im = fondo
                else:
                    im = im.convert('RGB')
                if im.width > LATO:
                    im = im.resize((LATO, round(im.height * LATO / im.width)), Image.LANCZOS)
                prima = f.stat().st_size
                for q in (78, 70, 62, 54):
                    im.save(arrivo, 'JPEG', quality=q, optimize=True, progressive=True)
                    if arrivo.stat().st_size <= PESO:
                        break
            if f != arrivo:
                f.unlink()
            fatte += 1
            print(f'ottimizzata {arrivo.name}: {prima // 1024} KB → {arrivo.stat().st_size // 1024} KB')
        except Exception as errore:
            print(f'NON ottimizzata {f.name}: {errore}', file=sys.stderr)
    return fatte


if __name__ == '__main__':
    ottimizza(pathlib.Path(__file__).resolve().parent.parent / 'risorse' / 'img')
