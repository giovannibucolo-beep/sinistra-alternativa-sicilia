"""I pezzi di pagina sempre uguali: la schermata, la testa, i pittogrammi.

Tengono insieme l'aspetto del sito: quando una di queste funzioni cambia, cambia ovunque.
È il motivo per cui stanno qui e non sparse nel generatore.
"""
from .testi import e, sa


def S(dentro, classe=''):
    return f'<section class="schermo {classe}"><div class="in">{dentro}</div></section>'


def LIBERO(dentro):
    return f'<section class="schermo libero"><div class="in">{dentro}</div></section>'


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


def intesta(occhiello, titolo, sotto=''):
    return f'<div class="intesta"><div class="in"><h1>{sa(titolo)}</h1>' + (f'<p class="sott">{sotto}</p>' if sotto else '') + '</div></div>'
