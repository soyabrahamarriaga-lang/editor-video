#!/usr/bin/env python3
"""Selección de tomas → clips.json + words_raw.json para el motor.

Uso:  python3 takes.py <takes.json> <carpeta_proyecto>

takes.json (lo escribe Claude a mano por video, ver SKILL.md · Selección de tomas):
{
  "pad_in": 0.03, "pad_out": 0.06, "gap_max": 0.25,          # opcionales (modo agresivo)
  "parts": [
    {"key": "a1", "file": "img_9002", "words": "trabajo/mfa/9002/words.json",
     "spans": [[1.1, 3.9], [21.6, 25.4]],                      # (inicio 1ª palabra, inicio última palabra + margen)
     "word_fix": {"19.27": [21.62, 22.0]}},                    # inicio MFA → [inicio, fin] verificados con ventana aislada
    {"key": "b1", "file": "img_8946", "range": [20.8, 23.5]}  # sin palabras: rango literal (montajes, b-roll con audio)
  ],
  "phrases": [["rafa rega", "Abraham Arriaga"]],               # correcciones de texto multi-palabra (minúsculas MFA)
  "words": {"sat": "SAT"}                                      # correcciones de una palabra
}
words.json = [[inicio, fin, "palabra"], ...] (salida de words.py; "" = silencio). Rutas relativas al proyecto.
Las palabras se miden por su INICIO: un span termina después del inicio de su última palabra (si no, se come esa palabra).
"""
import json, os, sys


def tighten(words, spans, pad_in, pad_out, gap_max):
    """Palabras cuyo inicio cae en algún span; huecos > gap_max (o saltos entre spans) se vuelven corte."""
    inside = lambda w: any(a - 0.15 <= w[0] <= b for a, b in spans)
    segs, prev = [], None
    for w in words:
        if not inside(w):
            prev = None
            continue
        if prev is not None and w[0] - prev[1] <= gap_max:
            segs[-1][1] = w[1]
        else:
            segs.append([w[0], w[1]])
        prev = w
    return [[round(a - pad_in, 3), round(b + pad_out, 3)] for a, b in segs]


def fix_text(ws, phrases, single):
    """Aplica correcciones; si la frase corregida tiene más palabras, las extra van +0.12 s (nunca mismo tiempo)."""
    out, i = [], 0
    while i < len(ws):
        for src, dst in phrases:
            n = len(src.split())
            if " ".join(w["text"] for w in ws[i:i + n]) == src:
                for k, t in enumerate(dst.split()):
                    out.append({"text": t, "start": round(ws[i + min(k, n - 1)]["start"] + 0.12 * max(0, k - (n - 1)), 3)})
                i += n
                break
        else:
            out.append({"text": single.get(ws[i]["text"], ws[i]["text"]), "start": ws[i]["start"]})
            i += 1
    return out


def main(spec_path, root):
    spec = json.load(open(spec_path))
    pad_in, pad_out, gap_max = spec.get("pad_in", 0.03), spec.get("pad_out", 0.06), spec.get("gap_max", 0.25)
    clips, raw, total = [], {}, 0.0
    for p in spec["parts"]:
        if "range" in p:
            rng, ws = [p["range"]], []
        else:
            fx = {round(float(k), 2): v for k, v in p.get("word_fix", {}).items()}
            w = [x for x in json.load(open(os.path.join(root, p["words"]))) if x[2]]
            w = sorted(([*fx[round(x[0], 2)], x[2]] if round(x[0], 2) in fx else x for x in w), key=lambda x: x[0])
            rng = tighten(w, p["spans"], pad_in, pad_out, gap_max)
            # +0.1: una palabra que empieza dentro del pad final no se oye
            ws = [{"text": x[2], "start": x[0]} for x in w if any(a <= x[0] and x[0] + 0.1 < b for a, b in rng)]
        assert rng, f"{p['key']}: ninguna palabra cae en los spans"
        clips.append([p["key"], p["file"], rng])
        raw[p["key"]] = fix_text(ws, spec.get("phrases", []), spec.get("words", {}))
        assert all(raw[p["key"]][i]["start"] < raw[p["key"]][i + 1]["start"] for i in range(len(raw[p["key"]]) - 1)), p["key"]
        total += sum(b - a for a, b in rng)
    keys = [c[0] for c in clips]
    assert len(keys) == len(set(keys)), "claves repetidas en parts"
    json.dump(clips, open(os.path.join(root, "clips.json"), "w"))
    json.dump(raw, open(os.path.join(root, "words_raw.json"), "w"), ensure_ascii=False)
    print(f"{total:.1f}s · {sum(len(c[2]) for c in clips)} segmentos")
    print(" ".join(w["text"] for k in keys for w in raw[k]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
