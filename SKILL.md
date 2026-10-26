---
name: editor-video
description: Editor de video profesional para clientes (reels, talking heads, montajes de eventos, videos de aplicación) en español. Organiza el material por cliente y proyecto, analiza referencias para escribir la guía de estilo de cada cliente, selecciona las mejores tomas con alineación MFA, y arma el video en HyperFrames con un motor propio (subtítulos por palabra, zooms, b-roll, tarjetas, sonidos) cuyo look define cada cliente. Úsala cuando el usuario pida editar videos de un cliente, "nuevo cliente", "nuevo proyecto", "analiza estas referencias", pase crudos o guiones para editar, o pida reels/shorts/recaps.
---

# Editor de video por cliente

Motor y flujo para editar como un editor humano: entender el material, cortar con precisión, aplicar el look del cliente,
verificar y entregar. **El motor no tiene estilo propio**: todo lo visual viene de `clientes/<CLIENTE>/look.py`.

`SKILL_DIR` = carpeta de esta skill. Herramientas: `engine/reel.py`, `tools/{takes.py, words.py, media.sh}`,
plantillas en `templates/`, looks de partida en `looks/`.

## Requisitos (verificar la primera vez; instalar lo que falte)
- `ffmpeg`, `python3`, `node`/`npx` · macOS: `avconvert` y `sips` (vienen con el sistema) para HDR→SDR y fotos HEIC.
- **HyperFrames** (render y librería de SFX): `npx hyperframes skills update general-video` (instala también `media-use`).
- **watch** (ver/transcribir videos y bajar links de Instagram/TikTok/YouTube con yt-dlp): skill `watch` de
  github.com/bradautomates/claude-video, motor local WhisperX (gratis): `setup.py --engine local` y `--backend whisperx`.
- **whisper** CLI (ventanas de verificación): `uv tool install --python 3.12 openai-whisper --with setuptools`.
- **MFA** (alineación de palabras ±20 ms): `brew install --cask miniforge`, `conda create -n mfa -c conda-forge montreal-forced-aligner -y`,
  `conda run -n mfa mfa model download acoustic spanish_mfa` y `… dictionary spanish_mfa` (otro idioma: su modelo).

## Estructura de carpetas (base de trabajo, p. ej. `~/Documents/VIDEOS/`)
```
clientes/<CLIENTE>/
├── estilo.md      guía del cliente (templates/estilo.md) — se lee SIEMPRE antes de editar
├── look.py        el estilo traducido a opciones del motor (de looks/nativo.py o looks/datos.py)
├── refs/          videos de referencia + hojas de frames + análisis
├── marca/         logo, colores, fuentes, música propia
└── proyectos/<AAAA-MM-DD_nombre>/
    ├── crudo/     material del usuario — NUNCA se modifica ni se borra
    ├── broll/     tomas de apoyo (opcional)
    ├── guion.md   script o notas (opcional; manda sobre estilo.md para este proyecto)
    ├── trabajo/   media/ (convertida), mfa/, gt/, y una carpeta por video con config.py + takes.json
    └── final/     solo entregables: <cliente>_<tema>_v1.mp4 · correcciones = v2, v3 sin borrar la anterior
```
El usuario no crea carpetas: dice "nuevo proyecto de <CLIENTE>, el material está en <ruta>" y aquí se crea
`proyectos/<fecha_nombre>/` y se **mueve** el crudo (preguntar antes si está fuera de la base y no quiere moverlo).

## Flujo

### 0 · Cliente nuevo → analizar referencias y escribir `estilo.md`
1. Bajar/leer las referencias (links con `watch`, que usa yt-dlp) a `refs/`. Ideal ~5.
2. Por cada una medir: gancho (primeros 3 s), cortes/min (`ffmpeg -vf "select='gt(scene,0.3)',showinfo"` → contar),
   subtítulos (fuente o la gratuita más parecida, tamaño, posición, color, resaltados, animación), color/look, tarjetas y
   animaciones, sonido (música, SFX, voz), encuadre, estructura, CTA. Hoja de frames: `fps=16/dur,scale=270:480,tile=8x2`.
3. Escribir `estilo.md` (plantilla) **solo con patrones vistos en ≥ 2 referencias**; separar medido de inferido; no copiar
   frases ni marcas ajenas. Si las referencias se contradicen, preguntar cuál priorizar.
4. Crear `look.py` desde el look de partida más cercano y ajustarlo a la guía. **Mostrar guía + stills de prueba y esperar
   aprobación** antes de editar.

### 1 · Entender el crudo
- Leer `estilo.md` y `guion.md`. Probar cada archivo (`ffprobe`: duración, rotación, `color_transfer`).
- `watch` sobre cada crudo con `WATCH_WHISPERX_LANGUAGE=es` y `--out-dir trabajo/watch`: qué se dice, qué tomas
  sirven, retomas, qué NO cortar. **Esa transcripción es la única completa**: se reutiliza para MFA.
- Cruzar con el guion: qué partes del guion no se grabaron o se improvisaron → avisar al usuario.
- Varios clips cortos sin voz (eventos): hoja de frames por clip, **clasificar por tema** y proponer agrupaciones
  (un video por tema + sueltos + un recap general) antes de editar.

### 2 · Preparar media
- `media.sh video <crudo> trabajo/media/<nombre>.mp4 [vertical|horizontal]` — convierte HDR (iPhone/DJI) a SDR en
  una sola pasada, keyframes cada 1 s, 30 fps. **No recomprimir más veces**: cada pasada pierde detalle.
- Fotos: `media.sh foto <foto> trabajo/media/<nombre>.mp4 2.5`. Audio para alinear: `media.sh audio`.

### 3 · Alinear palabras (videos con voz)
- `corpus/a.wav` + `corpus/a.txt` (texto plano de watch) → `conda run -n mfa mfa align --clean <corpus ABSOLUTO> spanish_mfa spanish_mfa <salida ABSOLUTA>`
  (rutas absolutas o falla; sin `--beam`). `words.py textgrid … words.json` y `words.py show words.json`.
- Palabras con `~` (duran > 1 s) esconden pausas o retomas; huecos largos sin texto pueden ser retomas que watch
  no transcribió. **Verificar con ventana aislada**: cortar 3–15 s del audio, `whisper --model small --language es
  --word_timestamps True`, `words.py whisper … <offset>`. MFA puede desviarse segundos donde hubo ruidos o retomas.

### 4 · Seleccionar tomas → `takes.json` → `takes.py`
- Por cada frase elegir la **mejor toma (normalmente la última)**; quitar retomas, arranques en falso, muletillas,
  instrucciones al editor ("este quiero que sea otro video") y lo que no sirve al objetivo. Cumplir la duración máxima.
- Spans por **inicio** de palabra: `(inicio de la 1ª, inicio de la última + 0.2)`. Si el fin cae antes del inicio de la
  última palabra, se la come. `word_fix` corrige palabras que MFA ubicó mal (con tiempos de la ventana aislada).
- Texto: `phrases` / `words` corrigen lo que el ASR oyó mal (nombres, marcas: "Claude" no "Klaus", "IA" no "ella").
- `python3 $SKILL_DIR/tools/takes.py trabajo/<video>/takes.json trabajo/<video>` → imprime duración y texto final.
  **Leer el texto completo**: que no falte la última palabra de ningún tramo ni sobren palabras cortadas.

### 5 · Armar el video
- `trabajo/<video>/`: `config.py` (de `templates/config.py`), `media → ../media` (symlink),
  `media.sh sfx trabajo/<video>`, `hyperframes.json` mínimo (`{"paths": {"assets": "assets"}}`).
- En `edit(e)`: tarjetas/POV/CTA, b-roll y sonidos **anclados a palabras** (`e.word_t(None, "palabra")`). Tarjetas a las
  orillas: con zoom la cara se ensancha. Un evento visible cada ≤ 3 s (el motor mete auto-punches si falta).
- `python3 $SKILL_DIR/engine/reel.py trabajo/<video>` → `npx hyperframes check trabajo/<video>` (0 errores; los avisos
  de "archivo grande / track denso / nested" son normales en este motor).

### 6 · Revisar antes de renderizar
- `npx hyperframes snapshot trabajo/<video> --at <t1,t2,…> --no-end -o <ruta ABSOLUTA>` en cada tarjeta, gancho y CTA.
  Revisar: nada tapa la cara, textos no se parten feo, colores correctos, subtítulos legibles.
- **Mostrar stills al usuario y esperar aprobación** (salvo que el estilo ya esté aprobado y diga "renderiza").

### 7 · Render y entrega
- `npx hyperframes render --quality delivery -o …/raw.mp4` dentro de `trabajo/<video>` → `media.sh final raw.mp4
  final/<cliente>_<tema>_v1.mp4` (−14 LUFS). Borrar solo el `raw.mp4` intermedio que se acaba de crear.
- Verificar con `watch --detail transcript`: texto completo y sin repeticiones. Si el inicio "falta", revisar los
  primeros 3 s con whisper antes de concluir (la transcripción completa a veces omite el arranque).

## Lecciones (no repetir)
- HDR sin convertir se ve deslavado; convertir con `avconvert` una sola vez.
- Grabar en **4K** si habrá zooms: 1080p ampliado 13–22 % se ve suave. Avisar al cliente.
- Una frase corregida con más palabras no puede repartir el mismo tiempo: subtítulo de duración 0 se queda pegado.
- Emojis en texto de pantalla no siempre renderizan: evitarlos.
- `snapshot -o` con ruta relativa escribe junto al proyecto: usar rutas absolutas.
- Mismo archivo usado en dos partes del video → claves distintas en `takes.json` (ids únicos).
- No subir la librería de SFX a ningún repo (licencia Pixabay de media-use): se copia por proyecto con `media.sh sfx`.
- Correcciones del cliente sobre un solo video (p. ej. "sin sonidos en el 07") van en su `config.py`
  (`SFX = {"card": None, "broll": None, "cut": None}` y `sfx: None` en tarjetas), no editando el `index.html`
  (se pierde al reconstruir).
