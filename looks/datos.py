# Look "datos y personalidad": subtítulos en mayúsculas con palabras clave en color de acento, tarjetas con cifras,
# lower-third con nombre, zooms marcados. Bueno para marca personal, educativo, aplicaciones, B2B.
# Copiar a clientes/<CLIENTE>/look.py y cambiar ACCENT / CARD_BG / BORDER por los colores del cliente.
W, H = 1080, 1920            # 16:9 → W, H = 1920, 1080
ACCENT = "#FFC83D"           # números y palabras clave
CARD_BG = "#1F4BFF"          # fondo de tarjetas
BORDER = "#FFFFFF"           # borde de tarjetas / texto secundario
CAPTIONS = {"max_words": 3, "max_chars": 18}
ZOOM = {"levels": [1.0, 1.08], "punch": 1.16, "auto_gap": 3.0}
SFX = {"card": "pop", "card_vol": 0.5, "broll": "whoosh", "cut": "whoosh-short", "zoom": "whoosh-short"}
CARD_ROTATION = 0
GRADE_BASE = {"contrast": 0.08, "vibrance": 0.12, "highlights": -0.12, "shadows": 0.06}
CARD_W = 520 if W > H else 760
SIDE_X = (40, W - 40 - CARD_W)

EXTRA_CSS = f"""
      .cap .w {{ font-weight: 900; font-size: {66 if W > H else 82}px; text-transform: uppercase;
        -webkit-text-stroke: {11 if W > H else 13}px #121212; paint-order: stroke fill; }}
      .cap .w.hl {{ color: {ACCENT}; }}
      {".cap { left: 380px; right: 380px; top: 830px; height: 190px; }" if W > H else ""}
      .stat {{ width: 100%; height: 100%; background: {CARD_BG}; border: 4px solid {BORDER}; border-radius: 30px;
        box-shadow: 0 18px 40px rgba(0,0,0,0.5); display: flex; flex-direction: column; align-items: center;
        justify-content: center; font-family: "Montserrat", sans-serif; text-align: center; padding: 0 26px; }}
      .stat .n {{ font-weight: 900; font-size: 84px; line-height: 1; letter-spacing: -0.03em; white-space: nowrap; color: {ACCENT}; }}
      .stat .t {{ font-weight: 900; font-size: 44px; line-height: 1.1; color: #fff; text-transform: uppercase; }}
      .stat .l {{ font-weight: 800; font-size: 28px; line-height: 1.15; color: #fff; text-transform: uppercase; margin-top: 12px; }}
      .lt {{ width: 100%; height: 100%; background: {CARD_BG}; border-left: 10px solid {ACCENT}; border-radius: 18px;
        box-shadow: 0 18px 40px rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: center;
        padding: 0 34px; font-family: "Montserrat", sans-serif; }}
      .lt .nm {{ font-weight: 900; font-size: 52px; color: #fff; }}
      .lt .rl {{ font-weight: 700; font-size: 26px; white-space: nowrap; color: {ACCENT}; margin-top: 6px; }}
"""


def stat(n, label=""):
    """Cifra grande + etiqueta (5 M+ / vistas)."""
    return f'<div class="stat"><span class="n">{n}</span>{f"<span class=l>{label}</span>" if label else ""}</div>'


def text(t, label=""):
    """Frase corta en tarjeta (Director de Finanzas / Tec)."""
    return f'<div class="stat"><span class="t">{t}</span>{f"<span class=l>{label}</span>" if label else ""}</div>'


def lower_third(name, role):
    return f'<div class="lt"><span class="nm">{name}</span><span class="rl">{role}</span></div>'


def card(e, cid, html_key, word, dur, side="right", h=260, nth=1):
    """Tarjeta lateral anclada a una palabra. Las tarjetas van a las orillas: con zoom la cara se ensancha."""
    t0 = e.word_t(None, word, nth) - 0.05
    return {"id": cid, "card": html_key, "t0": t0, "t1": t0 + dur, "pos": side,
            "x": SIDE_X[side == "right"], "y": int(H * 0.28), "w": CARD_W, "h": h}
