# Config de UN video. Va en clientes/<CLIENTE>/proyectos/<proyecto>/trabajo/<video>/config.py
# El look (colores, subtítulos, zoom, sonidos) viene de clientes/<CLIENTE>/look.py; aquí solo el contenido del video.
import json, os, sys

_here = os.path.dirname(os.path.abspath(__file__))
_client = next(p for p in (os.path.join(_here, *[".."] * n) for n in range(1, 7)) if os.path.exists(os.path.join(p, "estilo.md")))
sys.path.insert(0, os.path.abspath(_client))
from look import *  # noqa: F401,F403  — W, H, CAPTIONS, ZOOM, SFX, EXTRA_CSS, CARDS, helpers del cliente

CLIPS = [(k, f, [tuple(r) for r in rng]) for k, f, rng in json.load(open(os.path.join(_here, "clips.json")))]  # de tools/takes.py
WORDS_FILE = "words_raw.json"
FIXES = {}                       # correcciones de una palabra solo para este video
HIGHLIGHT = set(globals().get("HIGHLIGHT", set())) | set()   # + palabras clave de este video
CARDS = dict(globals().get("CARDS", {}), **{
    # "dato": stat("5 M+", "vistas"),            ← helpers definidos en el look
})


def edit(e):
    """Devuelve lo que pasa en pantalla, anclado a palabras: e.word_t(clave_o_None, "palabra", n)."""
    w = lambda word, n=1: e.word_t(None, word, n)
    images = [
        # {"id": "c-dato", "card": "dato", "t0": w("millones") - 0.05, "t1": w("millones") + 3.0, "pos": "right", "h": 260},
    ]
    broll = [
        # {"id": "br-1", "file": "broll_fiesta", "ms": 2.0, "t0": w("fiesta") - 0.05, "t1": w("fiesta") + 2.5},
    ]
    punches = [
        # w("importante") - 0.03,
    ]
    sfx = [
        # (w("instagram") - 0.05, "sparkle", 0.35),
    ]
    return {"images": images, "broll": broll, "punches": punches, "sfx": sfx}
