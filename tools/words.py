#!/usr/bin/env python3
"""Palabras con tiempo → words.json ([[inicio, fin, "palabra"], ...]; "" = silencio).

  python3 words.py textgrid <a.TextGrid> <out.json>            # alineación MFA (precisa, ±20 ms)
  python3 words.py whisper  <whisper.json> <out.json> [offset]  # whisper --word_timestamps (ventanas aisladas)
  python3 words.py show     <words.json>                        # imprime "inicio:palabra", marca ~ si dura > 1 s
"""
import json, re, sys


def from_textgrid(path):
    t = open(path).read()
    tier = t.split('name = "words"')[1].split("item [")[0]
    return [[round(float(a), 2), round(float(b), 2), x]
            for a, b, x in re.findall(r'xmin = ([\d.]+)\s+xmax = ([\d.]+)\s+text = "(.*?)"', tier)]


def from_whisper(path, offset=0.0):
    d = json.load(open(path))
    return [[round(offset + w["start"], 2), round(offset + w["end"], 2), w["word"].strip(" ,.¿?¡!").lower()]
            for s in d["segments"] for w in s.get("words", [])]


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "show":
        w = json.load(open(sys.argv[2]))
        print(" ".join(f"{a:.2f}:{x}" + ("~" if b - a > 1 else "") if x else f"[{b - a:.1f}]" for a, b, x in w if x or b - a > 0.5))
    else:
        w = from_textgrid(sys.argv[2]) if mode == "textgrid" else from_whisper(sys.argv[2], float(sys.argv[4]) if len(sys.argv) > 4 else 0.0)
        json.dump(w, open(sys.argv[3], "w"), ensure_ascii=False)
        print(f"{sum(1 for x in w if x[2])} palabras → {sys.argv[3]}")
