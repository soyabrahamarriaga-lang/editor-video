#!/usr/bin/env python3
"""Autotest del motor sin media: arma un proyecto falso con cada look y revisa el HTML/EDL.  python3 tests/test_engine.py"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import reel, takes  # noqa: E402

TMP = os.path.join(HERE, "_tmp")
WORDS = [[0.5, 0.8, "hola"], [0.8, 1.0, "soy"], [1.0, 1.5, "abraham"], [1.5, 2.2, ""], [2.2, 2.6, "vendemos"],
         [2.6, 3.1, "millones"], [3.1, 3.4, "de"], [3.4, 3.9, "vistas"], [3.9, 6.0, ""], [6.0, 6.5, "comenta"], [6.5, 7.0, "boda"]]


def project(look):
    root = os.path.join(TMP, look, "proyectos", "p", "trabajo", "v1")
    shutil.rmtree(os.path.join(TMP, look), ignore_errors=True)
    os.makedirs(root)
    open(os.path.join(TMP, look, "estilo.md"), "w").write("# test")
    shutil.copy(os.path.join(HERE, "..", "looks", f"{look}.py"), os.path.join(TMP, look, "look.py"))
    json.dump(WORDS, open(os.path.join(root, "w.json"), "w"))
    json.dump({"parts": [{"key": "a", "file": "x", "words": "w.json", "spans": [[0.5, 1.2], [2.2, 3.6]]},
                         {"key": "b", "file": "x", "words": "w.json", "spans": [[6.0, 6.7]]},
                         {"key": "c", "file": "y", "range": [1.0, 3.0]}],
               "phrases": [["hola soy", "Hola, yo soy"]], "words": {"abraham": "Abraham"}},
              open(os.path.join(root, "takes.json"), "w"))
    takes.main(os.path.join(root, "takes.json"), root)
    cfg = open(os.path.join(HERE, "..", "templates", "config.py")).read()
    extra = {"nativo": 'CARDS["cta"] = big("COMENTA BODA")\n',
             "datos": 'CARDS["vistas"] = stat("5 M+", "vistas")\nHIGHLIGHT |= {"millones"}\n'}[look]
    body = {"nativo": '    images = [overlay("t-cta", "cta", w("comenta") - 0.05, e.TOTAL, sfx="chime")]\n',
            "datos": '    images = [card(e, "c-v", "vistas", "millones", 2.0)]\n'}[look]
    cfg = cfg.replace("\n\ndef edit(e):", "\n" + extra + "\n\ndef edit(e):").replace("    images = [\n", body + "    images += [\n")
    open(os.path.join(root, "config.py"), "w").write(cfg)
    return root


for look in ("nativo", "datos"):
    sys.modules.pop("look", None)  # cada proyecto carga el look de SU cliente
    root = project(look)
    edl = reel.build(root)
    html = open(os.path.join(root, "index.html")).read()
    raw = json.load(open(os.path.join(root, "words_raw.json")))
    ids = re.findall(r' id="([^"]+)"', html)
    assert len(ids) == len(set(ids)), "ids duplicados"
    assert [w["text"] for w in raw["a"]][:4] == ["Hola,", "yo", "soy", "Abraham"], raw["a"]
    assert all(c["end"] > c["start"] for c in edl["captions"]), "subtítulo de duración 0"
    assert "vistas" in " ".join(c["text"] for c in edl["captions"]), "se perdió la última palabra del tramo"
    assert edl["total"] > 0 and len(edl["segments"]) == 4
    if look == "nativo":
        assert not any("pop" in s["src"] for s in edl["sfx"]), "nativo no lleva pop"
        assert any("chime" in s["src"] for s in edl["sfx"])
    else:
        assert 'class="w hl"' in html and "rotation: 0" in html
        assert any("pop" in s["src"] for s in edl["sfx"])
    print(f"ok {look}")
shutil.rmtree(TMP)
print("todo ok")
