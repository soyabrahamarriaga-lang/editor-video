#!/bin/zsh
# Prepara material para el motor. Nunca toca el original.
#   media.sh video <entrada> <salida.mp4> [vertical|horizontal]   → H.264 SDR 709, keyframes cada 1 s, 30 fps
#   media.sh foto  <entrada.jpg|heic> <salida.mp4> [seg] [vertical|horizontal] → clip con zoom lento + silencio
#   media.sh audio <video.mp4> <salida.wav>                       → mono 16 kHz para watch / MFA / whisper
#   media.sh sfx   <carpeta_proyecto>                             → copia la librería de SFX de media-use a assets/sfx
#   media.sh final <render.mp4> <salida.mp4>                      → audio a −14 LUFS (pico −1.5 dB), video sin recomprimir
set -e
mode=$1; shift
size() { [[ ${1:-vertical} == horizontal ]] && echo 1920:1080 || echo 1080:1920; }
case $mode in
  video)
    in=$1; out=$2; wh=$(size $3); tmp=""
    # iPhone/DJI HDR (HLG/PQ): convertir a SDR con avconvert (macOS) en UNA pasada; si no, se ve deslavado
    trc=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$in")
    if [[ $trc == arib-std-b67 || $trc == smpte2084 ]] && command -v avconvert >/dev/null; then
      tmp="${out%.*}.sdr.mov"; avconvert -s "$in" -p PresetHighestQuality -o "$tmp" --replace >/dev/null; in=$tmp
    fi
    ffmpeg -y -hide_banner -loglevel error -i "$in" -vf "scale=$wh:force_original_aspect_ratio=increase,crop=$wh" -r 30 \
      -c:v libx264 -preset slow -crf 15 -g 30 -keyint_min 30 -pix_fmt yuv420p \
      -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -ar 48000 -ac 2 "$out"
    [[ -n $tmp ]] && rm -f "$tmp"; true ;;
  foto)
    in=$1; out=$2; dur=${3:-2.5}; wh=$(size $4); jpg="${out%.*}.tmp.jpg"
    sips -s format jpeg "$in" --out "$jpg" >/dev/null
    ffmpeg -y -hide_banner -loglevel error -loop 1 -t $dur -i "$jpg" -f lavfi -t $dur -i anullsrc=r=48000:cl=stereo \
      -vf "scale=$wh:force_original_aspect_ratio=increase,crop=$wh,zoompan=z='1+0.0016*on':d=$(( ${dur%.*} * 30 + 15 )):s=${wh/:/x}:fps=30" \
      -c:v libx264 -preset slow -crf 15 -g 30 -pix_fmt yuv420p -c:a aac -shortest "$out"
    rm -f "$jpg" ;;
  audio)
    ffmpeg -y -hide_banner -loglevel error -i "$1" -vn -ac 1 -ar 16000 "$2" ;;
  sfx)
    src=$(ls -d ~/.claude/skills/media-use/audio/assets/sfx 2>/dev/null || true)
    [[ -z $src ]] && { echo "Falta la librería de SFX: instala HyperFrames (npx hyperframes skills update media-use)"; exit 1; }
    mkdir -p "$1/assets/sfx" && cp "$src"/*.mp3 "$1/assets/sfx/" && cp "$src"/CREDITS.md "$1/assets/sfx/" 2>/dev/null; ls "$1/assets/sfx" | wc -l ;;
  final)
    ffmpeg -y -hide_banner -loglevel error -i "$1" -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 192k "$2"
    ffmpeg -hide_banner -i "$2" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2 ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
