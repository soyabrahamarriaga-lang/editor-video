#!/usr/bin/env python3
"""Motor de edición para HyperFrames: talking heads, reels y montajes con subtítulos por palabra, zooms, b-roll,
tarjetas y efectos de sonido. Todo lo visual lo define el look del cliente; aquí solo hay valores neutros.

Uso:   python3 reel.py <carpeta_proyecto>        → lee <proyecto>/config.py, escribe index.html + edl.json

config.py (ver templates/config.py) define:
  CLIPS       [(clave, archivo_sin_ext, [(inicio, fin), ...]), ...]   en segundos del archivo media/<archivo>.mp4
  WORDS_FILE  json {clave: [{"text", "start"}, ...]}                  tiempos en segundos del archivo
  edit(e)     -> {"broll": [...], "images": [...], "punches": [...], "sfx": [(t, nombre, vol), ...]}  (todas opcionales)
y cualquier opción de OPTIONS para sobreescribir el valor neutro (normalmente vienen del look del cliente).
"""
import importlib.util, json, os, sys

# ------------------------------------------------------------------ opciones (valores neutros)
OPTIONS = {
    "W": 1080, "H": 1920, "FPS": 30,
    "WORDS_FILE": "words_raw.json",
    "FIXES": {},            # palabra → corrección (texto exacto)
    "MERGE": [],            # [(primera, segunda)] une dos palabras en un solo bloque ("Y", "Combinator")
    "HIGHLIGHT": set(),     # palabras (minúsculas, sin puntuación) con clase .hl
    "CAPTIONS": {"max_words": 3, "max_chars": 18, "max_gap": 0.35, "lead": 0.10, "break_on_caps": True},
    "ZOOM": {"levels": [1.0, 1.05], "punch": 1.12, "auto_gap": 3.0, "origin": "50% 34%"},  # auto_gap None = sin auto-punch
    "CARD_ROTATION": 0,     # grados de inclinación de tarjetas laterales (izq = -, der = +)
    "SFX": {                # nombre de assets/sfx/<nombre>.mp3 o None para silenciar ese evento
        "card": "pop", "card_vol": 0.5,
        "broll": "whoosh", "broll_vol": 0.4,
        "cut": "whoosh-short", "cut_vol": 0.3,      # cambio de clip (clave distinta)
        "zoom": None, "zoom_vol": 0.22,             # punch-in
        "min_gap": 0.45,                            # nunca dos sonidos más juntos: gana el de mayor prioridad
    },
    "GRADE_BASE": {}, "GRADE_FILE": {},             # data-color-grading de HyperFrames (base + ajuste por archivo)
    "CARDS": {}, "EXTRA_CSS": "",
}
MERGEABLE = ("CAPTIONS", "ZOOM", "SFX")  # el look puede cambiar solo algunas claves de estas
BASE_CSS = """
      .cap {{ position: absolute; left: 60px; right: 60px; top: {cap_top}px; height: 240px; z-index: 30;
        display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 18px; text-align: center; }}
      .cap .w {{ display: inline-block; font-family: "Montserrat", sans-serif; font-weight: 800; font-size: {cap_size}px;
        line-height: 1.08; color: #fff; text-shadow: 0 3px 10px rgba(0,0,0,0.75), 0 0 2px rgba(0,0,0,0.9); }}
"""


def load_config(root):
    sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location("config", os.path.join(root, "config.py"))
    cfg = importlib.util.module_from_spec(spec)
    cwd = os.getcwd()
    os.chdir(root)  # el config puede leer clips.json, etc. con rutas relativas
    try:
        spec.loader.exec_module(cfg)
    finally:
        os.chdir(cwd)
    o = {k: (dict(v) if isinstance(v, dict) else v) for k, v in OPTIONS.items()}
    for k in o:
        if hasattr(cfg, k):
            o[k] = {**o[k], **getattr(cfg, k)} if k in MERGEABLE else getattr(cfg, k)
    return cfg, o


def build(root):
    cfg, o = load_config(root)
    W, H, FPS = o["W"], o["H"], o["FPS"]
    q = lambda t: round(round(t * FPS) / FPS, 4)

    # -------------------------------------------------------------- cortes → línea de tiempo
    segments, T = [], 0.0
    for key, f, rng in cfg.CLIPS:
        for i, (a, b) in enumerate(rng):
            assert b > a, (key, a, b)
            segments.append({"id": f"{key}-{i}", "key": key, "file": f, "a": a, "b": b, "T": q(T)})
            T += b - a
    TOTAL = q(T)
    seg_end = lambda g: q(g["T"] + g["b"] - g["a"])

    def to_timeline(key, s):
        for g in (g for g in segments if g["key"] == key):
            if s < g["a"]:
                return g["T"]
            if g["a"] <= s < g["b"]:
                return g["T"] + (s - g["a"])
        return None

    # -------------------------------------------------------------- palabras
    wf = os.path.join(root, o["WORDS_FILE"])
    raw = json.load(open(wf)) if os.path.exists(wf) else {}
    lead = o["CAPTIONS"]["lead"]
    words = []
    for key, _, _ in cfg.CLIPS:
        for w in raw.get(key, []):
            t = to_timeline(key, w["start"] - lead)
            if t is not None:
                words.append({"key": key, "text": o["FIXES"].get(w["text"], w["text"]), "t": q(t)})
    for first, second in o["MERGE"]:
        merged = []
        for w in words:
            if merged and merged[-1]["text"] == first and w["text"].startswith(second):
                merged[-1]["text"] = first + " " + w["text"]
                continue
            merged.append(w)
        words = merged
    for i, w in enumerate(words):
        nxt = words[i + 1]["t"] if i + 1 < len(words) else TOTAL
        w["end"] = q(min(nxt, w["t"] + 1.0))

    clean = lambda s: s.lower().strip(",.¿?!¡\"“”")

    class E:
        """API para edit(e): tiempos en la línea de tiempo final."""

        @staticmethod
        def word_t(key, text, nth=1):
            """Tiempo de la n-ésima `text` dentro de la clave `key` (key=None: en todo el video)."""
            n = 0
            for w in words:
                if (key is None or w["key"] == key) and clean(w["text"]) == clean(text):
                    n += 1
                    if n == nth:
                        return w["t"]
            raise KeyError(f"{key}:{text}")

        @staticmethod
        def seg_start(seg_id):
            return next(g for g in segments if g["id"] == seg_id)["T"]

        @staticmethod
        def seg_end(seg_id):
            return seg_end(next(g for g in segments if g["id"] == seg_id))

    e = E()
    e.TOTAL, e.q, e.segments, e.words, e.W, e.H = TOTAL, q, segments, words, W, H
    plan = cfg.edit(e) if hasattr(cfg, "edit") else {}
    BROLL, IMAGES = plan.get("broll", []), plan.get("images", [])
    punch_times = sorted(q(t) for t in plan.get("punches", []))
    ids = [s["id"] for s in segments] + [b["id"] for b in BROLL] + [i["id"] for i in IMAGES]
    assert len(ids) == len(set(ids)), "ids repetidos en clips/b-roll/tarjetas"

    # -------------------------------------------------------------- ritmo: auto-punch si hay huecos sin evento
    def events():
        ev = [g["T"] for g in segments] + [b["t0"] for b in BROLL] + [b["t1"] for b in BROLL]
        ev += [i["t0"] for i in IMAGES] + punch_times
        return sorted(set(q(x) for x in ev if x < TOTAL))

    auto, gap_max = [], o["ZOOM"]["auto_gap"]
    while gap_max:
        ev = sorted(set(events() + auto)) + [TOTAL]
        gaps = [(ev[i], ev[i + 1]) for i in range(len(ev) - 1) if ev[i + 1] - ev[i] > gap_max]
        if not gaps:
            break
        a, b = gaps[0]
        target = a + min(gap_max - 0.4, (b - a) / 2)
        cand = min((w for w in words if a + 1.0 < w["t"] < b - 0.8), key=lambda w: abs(w["t"] - target), default=None)
        t = q(cand["t"] - 0.03) if cand else q(target)
        auto.append(t)
        punch_times.append(t)
    punch_times = sorted(set(punch_times))

    # -------------------------------------------------------------- subtítulos
    C = o["CAPTIONS"]
    groups, cur = [], []
    for w in words:
        if cur:
            p = cur[-1]
            if (len(cur) >= C["max_words"] or len(" ".join(x["text"] for x in cur + [w])) > C["max_chars"]
                    or p["text"][-1] in ",.?!" or w["key"] != p["key"] or w["t"] - p["end"] > C["max_gap"]
                    or (C["break_on_caps"] and w["text"][0].isupper() and not w["text"].isupper())):
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    caps = []
    for gi, g in enumerate(groups):
        end = groups[gi + 1][0]["t"] if gi + 1 < len(groups) else TOTAL
        end = min(end, g[-1]["end"] + 0.6, TOTAL)
        if end - g[0]["t"] >= 1 / FPS:  # un subtítulo de duración 0 se queda pegado en pantalla
            caps.append({"start": g[0]["t"], "end": q(end), "words": g})

    # -------------------------------------------------------------- zooms: base alternado por toma + punch-ins
    Z = o["ZOOM"]
    levels, punch = Z["levels"], Z["punch"]
    zoom_plan = []  # (seg_id, t, nivel, es_acercamiento)
    for i, g in enumerate(segments):
        level = levels[i % len(levels)]
        for t in punch_times:
            if g["T"] + 0.2 < t < seg_end(g) - 0.2:
                new = punch if level < punch - 0.01 else levels[0]
                zoom_plan.append((g["id"], t, new, new > level))
                level = new

    hidden = lambda t: any(b["t0"] - 0.05 <= t <= b["t1"] + 0.05 for b in BROLL)

    # -------------------------------------------------------------- SFX: solo cuando pasa algo visible
    S = o["SFX"]
    cand = []  # (t, prioridad, nombre, vol, dur)
    for im in IMAGES:
        name = im.get("sfx", S["card"])
        if name:
            cand.append((im["t0"] - 0.02, 3, name, im.get("vol", S["card_vol"]), 1.2))
    for t, name, vol in plan.get("sfx", []):
        cand.append((t, 4, name, vol, 1.5))
    if S["broll"]:
        cand += [(b["t0"] - 0.10, 3, S["broll"], S["broll_vol"], 0.6) for b in BROLL]
    if S["cut"]:
        cand += [(g["T"] - 0.10, 2, S["cut"], S["cut_vol"], 0.6) for i, g in enumerate(segments[1:], 1)
                 if g["key"] != segments[i - 1]["key"] and not hidden(g["T"])]
    if S["zoom"]:
        cand += [(t - 0.04, 1, S["zoom"], S["zoom_vol"], 0.6) for _, t, _, is_in in zoom_plan if is_in and not hidden(t)]
    kept = []
    for c in sorted(cand, key=lambda c: (c[0], -c[1])):
        clash = [k for k in kept if abs(k[0] - c[0]) < S["min_gap"]]
        if clash and not all(c[1] > k[1] for k in clash):
            continue
        for k in clash:
            kept.remove(k)
        kept.append(c)
    sfx, lanes = [], []
    for t, _, name, vol, dur in sorted(kept):
        if t < TOTAL - 0.05:
            t = q(max(0, t))
            s = {"id": f"sfx-{len(sfx):02d}", "src": f"assets/sfx/{name}.mp3", "t": t, "vol": vol, "dur": q(min(dur, TOTAL - t))}
            li = next((i for i, busy in enumerate(lanes) if busy <= t - 0.01), None)
            if li is None:
                lanes.append(0)
                li = len(lanes) - 1
            lanes[li] = t + s["dur"]
            s["track"] = 10 + li
            sfx.append(s)

    def grade_attr(f):
        adj = dict(o["GRADE_BASE"])
        for k, v in o["GRADE_FILE"].get(f, {}).items():
            adj[k] = round(adj.get(k, 0) + v, 3)
        return f" data-color-grading='{json.dumps({'intensity': 1, 'adjust': adj}, separators=(',', ':'))}'" if adj else ""

    # -------------------------------------------------------------- posiciones de tarjetas
    def place(im):
        h, w = im.get("h", 300), im.get("w", min(760, W - 160))
        if "x" in im:
            return f"left:{im['x']}px;top:{im['y']}px;width:{w}px;height:{h}px;"
        y = im.get("y", int(H * 0.16))
        x = {"top": (W - w) // 2, "left": 40, "right": W - 40 - w}[im["pos"]]
        return f"left:{x}px;top:{y}px;width:{w}px;height:{h}px;"

    # -------------------------------------------------------------- HTML
    out = [f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #000; font-family: "Montserrat", sans-serif; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }}
      .shot {{ position: absolute; inset: 0; overflow: hidden; }}
      .cam {{ position: absolute; inset: 0; transform-origin: {Z['origin']}; }}
      .cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
      .broll {{ z-index: 5; }}
      .card-host {{ position: absolute; z-index: 10; pointer-events: none; }}
      .card {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }}
      .card img {{ max-width: 100%; max-height: 100%; }}
{BASE_CSS.format(cap_top=int(H * 0.63), cap_size=round(W * 0.066))}
{o['EXTRA_CSS']}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">"""]
    A = out.append
    for i, g in enumerate(segments):
        nxt = segments[i + 1]["T"] if i + 1 < len(segments) else TOTAL
        A(f"""      <div class="shot"><div class="cam" data-layout-allow-overflow id="cam-{g['id']}">
        <video id="v-{g['id']}" class="clip" src="media/{g['file']}.mp4" data-start="{g['T']}" data-duration="{q(nxt - g['T'])}" data-media-start="{g['a']}" data-track-index="{i % 2}" playsinline data-has-audio="true"{grade_attr(g['file'])}></video>
      </div></div>""")
    for b in BROLL:
        t0, t1 = q(b["t0"]), q(b["t1"])
        A(f"""      <div class="shot broll"><div class="cam" data-layout-allow-overflow id="cam-{b['id']}">
        <video id="v-{b['id']}" class="clip" src="media/{b['file']}.mp4" data-start="{t0}" data-duration="{q(t1 - t0)}" data-media-start="{b.get('ms', 0)}" data-track-index="5" muted playsinline{grade_attr(b['file'])}></video>
      </div></div>""")
    for im in IMAGES:
        t0, t1 = q(im["t0"]), q(min(im["t1"], TOTAL))
        body = o["CARDS"][im["card"]] if im.get("card") else f'<img src="{im["src"]}" alt="" />'
        A(f"""      <div id="{im['id']}" class="clip card-host" data-start="{t0}" data-duration="{q(t1 - t0)}" data-track-index="2" style="{place(im)}"><div class="card" id="in-{im['id']}" style="opacity:0">{body}</div></div>""")
    for ci, c in enumerate(caps):
        spans = "".join(f'<span class="w{" hl" if clean(w["text"]) in o["HIGHLIGHT"] else ""}" id="w{ci}-{wi}" style="opacity:0">{w["text"]}</span>'
                        for wi, w in enumerate(c["words"]))
        A(f"""      <div id="cap-{ci:03d}" class="clip cap" data-start="{c['start']}" data-duration="{q(c['end'] - c['start'])}" data-track-index="3">{spans}</div>""")
    for s in sfx:
        A(f"""      <audio id="{s['id']}" class="clip" src="{s['src']}" data-start="{s['t']}" data-duration="{s['dur']}" data-track-index="{s['track']}" data-volume="{s['vol']}"></audio>""")

    # -------------------------------------------------------------- animación (GSAP, seekable)
    js = ['const tl = gsap.timeline({ paused: true });']
    J = js.append
    for i, g in enumerate(segments):
        base, cam = levels[i % len(levels)], f'"#cam-{g["id"]}"'
        J(f'tl.fromTo({cam}, {{ scale: {base + 0.04 if i == 0 else base} }}, {{ scale: {base}, duration: {0.5 if i == 0 else 0.01}, ease: "power2.out" }}, {g["T"]});')
        for seg_id, t, level, _ in zoom_plan:
            if seg_id == g["id"]:
                J(f'tl.to({cam}, {{ scale: {level}, duration: 0.14, ease: "power3.out" }}, {t});')
    for b in BROLL:
        t0, t1 = q(b["t0"]), q(b["t1"])
        J(f'tl.fromTo("#cam-{b["id"]}", {{ scale: {b.get("scale0", 1.08)} }}, {{ scale: {b.get("scale1", 1.0)}, duration: {q(t1 - t0)}, ease: "power1.out" }}, {t0});')
    for im in IMAGES:
        t0, t1, sel = q(im["t0"]), q(im["t1"]), f'"#in-{im["id"]}"'
        if im["pos"] == "top":
            J(f'tl.fromTo({sel}, {{ scale: 0.4, opacity: 0, y: -30 }}, {{ scale: 1, opacity: 1, y: 0, duration: 0.32, ease: "back.out(2.2)" }}, {t0});')
        else:
            rot = im.get("rot", o["CARD_ROTATION"] * (-1 if im["pos"] == "left" else 1))
            x0 = -260 if im["pos"] == "left" else 260
            J(f'tl.fromTo({sel}, {{ scale: 0.3, opacity: 0, rotation: {rot * 2}, x: {x0} }}, {{ scale: 1, opacity: 1, rotation: {rot}, x: 0, duration: 0.38, ease: "back.out(1.8)" }}, {t0});')
        if t1 < TOTAL - 0.05:
            J(f'tl.to({sel}, {{ scale: 0.6, opacity: 0, duration: 0.18, ease: "power2.in" }}, {q(t1 - 0.18)});')
        for sel2, dt in im.get("reveal", []):
            J(f'tl.fromTo("#in-{im["id"]} {sel2}", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2.4)" }}, {q(t0 + dt)});')
    for ci, c in enumerate(caps):
        for wi, w in enumerate(c["words"]):
            J(f'tl.fromTo("#w{ci}-{wi}", {{ opacity: 0, scale: 0.6, y: 18 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.6)" }}, {q(max(c["start"], w["t"]))});')
    J('window.__timelines["main"] = tl;')
    out += ["    </div>", "    <script>\n      " + "\n      ".join(js) + "\n    </script>", "  </body>\n</html>\n"]
    open(os.path.join(root, "index.html"), "w").write("\n".join(out))
    edl = {"total": TOTAL, "segments": segments, "broll": BROLL, "images": IMAGES, "punches": punch_times, "auto_punches": auto,
           "captions": [{"start": c["start"], "end": c["end"], "text": " ".join(w["text"] for w in c["words"])} for c in caps], "sfx": sfx}
    json.dump(edl, open(os.path.join(root, "edl.json"), "w"), indent=1, ensure_ascii=False)
    ev = sorted(set(events() + punch_times)) + [TOTAL]
    print(f"duración {TOTAL}s · {len(segments)} cortes · {len(BROLL)} b-roll · {len(IMAGES)} tarjetas · "
          f"{len(punch_times)} zooms ({len(auto)} auto) · {len(caps)} subtítulos · {len(sfx)} sfx · "
          f"hueco máx {round(max(ev[i + 1] - ev[i] for i in range(len(ev) - 1)), 2)} s")
    return edl


if __name__ == "__main__":
    build(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "."))
