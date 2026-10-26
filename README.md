# editor-video

Skill de Claude Code para editar videos de clientes como un editor profesional: organiza el material por cliente,
analiza referencias para escribir la guía de estilo de cada uno, corta con precisión de palabra (MFA) y arma el video
en [HyperFrames](https://github.com/heygen-com/hyperframes) con un motor cuyo look define cada cliente.

## Instalar
```bash
git clone <este-repo> ~/.claude/skill-repos/editor-video
ln -s ~/.claude/skill-repos/editor-video ~/.claude/skills/editor-video
```
Reinicia Claude Code. La primera vez, Claude revisa los requisitos de `SKILL.md` (ffmpeg, HyperFrames, watch, whisper,
MFA) e instala lo que falte.

## Usar
Abre Claude Code en tu carpeta de trabajo (p. ej. `~/Documents/VIDEOS`) y di:
- *"Nuevo cliente: <nombre>. Estas son sus referencias: <links>"* → analiza y propone `estilo.md` + `look.py`.
- *"Nuevo proyecto de <cliente>, el material está en <ruta>, aquí va el guion…"* → selecciona tomas, edita, te muestra
  stills y renderiza al aprobar.

## Qué hay
| Ruta | Qué es |
|---|---|
| `SKILL.md` | Flujo completo + lecciones aprendidas |
| `engine/reel.py` | Motor: cortes, subtítulos por palabra, zooms, b-roll, tarjetas, SFX → HyperFrames |
| `tools/takes.py` | Selección de tomas (spans por palabra MFA) → `clips.json` + `words_raw.json` |
| `tools/words.py` | MFA TextGrid / whisper → `words.json` |
| `tools/media.sh` | HDR→SDR, fotos→clip, audio, SFX, loudness final |
| `looks/` | Looks de partida: `nativo` (UGC/eventos) y `datos` (marca personal, tarjetas) |
| `templates/` | `estilo.md` del cliente y `config.py` de cada video |
| `tests/` | Autotest del motor (sin media): `python3 tests/test_engine.py` |

Los efectos de sonido no vienen en el repo (licencia de su fuente): se copian de la skill `media-use` de HyperFrames.
