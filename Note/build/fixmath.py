"""Прямое (неналоновое) начертание в формулах для имён функций и текстовых индексов."""
import re, sys, zipfile, shutil
src = sys.argv[1]; tmp = src + ".tmp"
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/document.xml":
            xml = data.decode("utf-8")
            def fix(m):
                text = m.group(2)
                if text in ("max", "log") or re.search("[А-Яа-яЁё]", text):
                    return f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr>{m.group(1)}'
                return m.group(0)
            xml, n = re.subn(r'<m:r>(<m:t(?: [^>]*)?>([^<]*)</m:t>)', fix, xml)
            data = xml.encode("utf-8")
        zout.writestr(item, data)
shutil.move(tmp, src)
print("math runs patched")
