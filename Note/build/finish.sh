#!/bin/bash
# Сборка записки: docx (node) → прямое начертание в формулах → Word (оглавление, PDF, число страниц).
# Результат: note.docx и note.pdf в этой папке. Копирование в Note/ — вручную после проверки.
set -e
B="$(cd "$(dirname "$0")" && pwd)"
SCRIPT=${1:-build_note.js}      # сценарий сборки
NAME=${2:-note}                 # имя результата: note.docx/note.pdf или note_short.*
WT=/mnt/c/Users/Sasha/AppData/Local/Temp/note_build
W='C:\Users\Sasha\AppData\Local\Temp\note_build'
mkdir -p "$WT"
cd "$B"
node "$SCRIPT" "$B/$NAME.docx" >/dev/null
python3 fixmath.py "$NAME.docx"
cp "$B/$NAME.docx" "$WT/note.docx"; cp "$B/finish.ps1" "$WT/finish.ps1"
(cd "$WT" && timeout 300 powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$W\\finish.ps1" -in "$W\\note.docx" -pdf "$W\\note.pdf" 2>&1 | tr -d '\r' | grep PAGES)
cp "$WT/note.docx" "$B/$NAME.docx"; cp "$WT/note.pdf" "$B/$NAME.pdf"
