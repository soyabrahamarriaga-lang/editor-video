# Look "nativo de celular": se siente real, no producido. Subtítulos blancos simples, sin tarjetas de datos,
# zoom sutil, texto grande arriba para gancho/POV/CTA. Bueno para bodas, eventos, behind the scenes, UGC.
# Copiar a clientes/<CLIENTE>/look.py y ajustar.
W, H = 1080, 1920
CAPTIONS = {"max_words": 3, "max_chars": 20}
ZOOM = {"levels": [1.0, 1.03], "punch": 1.06, "auto_gap": 3.0}
SFX = {"card": None, "broll": "whoosh", "broll_vol": 0.35, "cut": "whoosh-short", "cut_vol": 0.25, "zoom": None}
GRADE_BASE = {"contrast": 0.04, "vibrance": 0.06}
TEXT = "#FFFFFF"

EXTRA_CSS = f"""
      .cap {{ top: {int(H * 0.615)}px; height: 220px; left: 70px; right: 70px; gap: 0 16px; }}
      .cap .w {{ color: {TEXT}; font-weight: 800; font-size: 70px; }}
      .big {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; text-align: center;
        font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 78px; line-height: 1.06; color: {TEXT};
        text-shadow: 0 4px 14px rgba(0,0,0,0.8); }}
"""


def big(text):
    """Texto grande sin caja (gancho, POV, CTA). Sin emojis: no siempre renderizan."""
    return f'<div class="big">{text}</div>'


def overlay(cid, html_key, t0, t1, sfx=None, vol=0.4):
    """Texto grande arriba entre t0 y t1 (p. ej. gancho 0–2.6 s, POV todo el video, CTA hasta el final)."""
    return {"id": cid, "card": html_key, "t0": t0, "t1": t1, "pos": "top", "w": W - 100, "h": 300, "y": int(H * 0.15),
            "sfx": sfx, "vol": vol}
