// Вспомогательные функции оформления по ГОСТ 7.32-2017
const fs = require("fs");
const D = require("docx");
const {
  Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  HeadingLevel, BorderStyle, VerticalAlign, TabStopType, LevelFormat, LevelSuffix,
  MathRun, MathFraction, MathSubScript,
} = D;
const OMath = D.Math;

const PORTRAIT_W = 9355;      // ширина текста, twips: 210 − 30 − 15 мм
const LANDSCAPE_W = 14288;    // 297 − 30 − 15 мм
const INDENT = 709;           // абзацный отступ 1,25 см
const FONT = "Times New Roman";
const MONO = "Courier New";

// ------------------------------------------------------------ нумерация
const counters = { fig: [], tab: [], f: [], cite: [], app: [] };
const APP_LETTERS = ["А", "Б", "В", "Г", "Д", "Ж", "И", "К"];
// Рисунки и таблицы приложений нумеруются в пределах приложения: «А.1», «Б.2» (ГОСТ 7.32).
// Их объявляют заранее, чтобы ссылки из основного текста получили верный номер.
const appItems = { fig: {}, tab: {} };
function declareApp(kind, key, letter) {
  const same = Object.values(appItems[kind]).filter((v) => v.letter === letter).length;
  appItems[kind][key] = { letter, label: `${letter}.${same + 1}` };
}
function num(kind, key) {
  if ((kind === "fig" || kind === "tab") && appItems[kind][key]) return appItems[kind][key].label;
  const arr = counters[kind];
  let i = arr.indexOf(key);
  if (i < 0) { arr.push(key); i = arr.length - 1; }
  return kind === "app" ? APP_LETTERS[i] : String(i + 1);
}
const created = { fig: [], tab: [] };
function markCreated(kind, key) {
  if (appItems[kind] && appItems[kind][key]) return appItems[kind][key].label;
  const n = Number(num(kind, key));
  const prev = created[kind].length ? created[kind][created[kind].length - 1] : 0;
  if (n !== prev + 1) throw new Error(`${kind} ${key}: номер ${n} создан не по порядку (предыдущий ${prev})`);
  created[kind].push(n);
  return n;
}

// ------------------------------------------------------------ текст
// Разметка: `код` — моноширинный; {fig:key} {tab:key} {f:key} {app:key} — номера; {cite:key} — [n]
function resolve(text) {
  return text.replace(/\{(fig|tab|f|app|cite):([\w-]+)\}/g, (_, kind, key) => {
    const n = num(kind, key);
    return kind === "cite" ? `[${n}]` : n;
  });
}

function runs(text, opts = {}) {
  const t = resolve(text);
  const parts = t.split("`");
  const out = [];
  parts.forEach((s, i) => {
    if (!s) return;
    if (i % 2 === 1) { out.push(new TextRun({ text: s, font: MONO, size: opts.monoSize || (opts.size ? opts.size - 2 : 26), bold: opts.bold, italics: opts.italics })); return; }
    s.split(/(_\{[^}]*\})/).forEach((seg) => {
      if (!seg) return;
      const m = seg.match(/^_\{([^}]*)\}$/);
      if (m) out.push(new TextRun({ text: m[1], font: FONT, size: opts.size, subScript: true, bold: opts.bold }));
      else out.push(new TextRun({ text: seg, font: FONT, size: opts.size, bold: opts.bold, italics: opts.italics }));
    });
  });
  return out;
}

const P = (text, o = {}) => new Paragraph({
  children: runs(text, o),
  alignment: o.align || AlignmentType.JUSTIFIED,
  indent: o.noIndent ? { firstLine: 0 } : { firstLine: INDENT },
  spacing: { before: o.before || 0, after: o.after || 0, line: 360 },
  keepNext: o.keepNext,
});

const H1 = (text, o = {}) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  alignment: o.center ? AlignmentType.CENTER : AlignmentType.LEFT,
  indent: o.center ? { firstLine: 0 } : { firstLine: INDENT },
  children: o.children || [new TextRun({ text, bold: true, font: FONT, size: 28 })],
  pageBreakBefore: o.noBreak ? false : true,
});
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, bold: true, font: FONT, size: 28 })] });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, bold: true, font: FONT, size: 28 })] });

// заголовок структурного элемента, не попадающий в содержание (РЕФЕРАТ, СОДЕРЖАНИЕ)
const StructTitle = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, pageBreakBefore: true, keepNext: true,
  spacing: { before: 0, after: 360, line: 360 },
  children: [new TextRun({ text, bold: true, font: FONT, size: 28 })],
});

// списки
let listInstance = 0;
function list(items, kind = "dash") {
  listInstance += 1;
  const inst = listInstance;
  return items.map((it, i) => new Paragraph({
    numbering: { reference: kind, level: 0, instance: inst },
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 0, line: 360 },
    children: runs(it),
    keepNext: false,
  }));
}
const numberingConfig = [
  { reference: "dash", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT,
      suffix: LevelSuffix.SPACE, style: { paragraph: { indent: { left: 0, firstLine: INDENT } } } }] },
  { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1)", alignment: AlignmentType.LEFT,
      suffix: LevelSuffix.SPACE, style: { paragraph: { indent: { left: 0, firstLine: INDENT } } } }] },
  { reference: "lit", levels: [{ level: 0, format: LevelFormat.RUSSIAN_LOWER || LevelFormat.LOWER_LETTER, text: "%1)",
      alignment: AlignmentType.LEFT, suffix: LevelSuffix.SPACE, style: { paragraph: { indent: { left: 0, firstLine: INDENT } } } }] },
];

// ------------------------------------------------------------ рисунки
function figure(key, file, caption, widthIn, o = {}) {
  const n = markCreated("fig", key);
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  let wpx = widthIn * 96, hpx = wpx * h / w;
  if (o.maxHeightIn && hpx > o.maxHeightIn * 96) { hpx = o.maxHeightIn * 96; wpx = hpx * w / h; }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: o.before ?? 120, after: 120, line: 240 },
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: Math.round(wpx), height: Math.round(hpx) } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240, line: 240 },
      children: [new TextRun({ text: `Рисунок ${n} — ${caption}`, font: FONT, size: 28 })],
    }),
  ];
}

// ------------------------------------------------------------ таблицы
const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border };

function cellParas(content, o) {
  const items = Array.isArray(content) ? content : [content];
  return items.map((t) => new Paragraph({
    alignment: o.align || AlignmentType.LEFT,
    spacing: { before: 0, after: 0, line: 240 },
    children: runs(String(t), { size: o.size || 24, bold: o.bold, monoSize: (o.size || 24) - 2 }),
  }));
}

// headers: массив строк; rows: массив массивов; widths: twips; o.align: массив выравниваний по столбцам
function table(key, caption, headers, rows, widths, o = {}) {
  const n = markCreated("tab", key);
  const total = widths.reduce((a, b) => a + b, 0);
  const size = o.size || 24;
  const mk = (cells, isHead) => new TableRow({
    tableHeader: isHead, cantSplit: true,
    children: cells.map((c, i) => {
      if (c === null) return null;     // ячейка занята объединением по вертикали
      const spec = (c && typeof c === "object" && !Array.isArray(c)) ? c : { t: c };
      const w = spec.span ? widths.slice(i, i + spec.span).reduce((a, b) => a + b, 0) : widths[i];
      return new TableCell({
        width: { size: w, type: WidthType.DXA },
        columnSpan: spec.span,
        rowSpan: spec.rowSpan,
        verticalAlign: isHead ? VerticalAlign.CENTER : VerticalAlign.TOP,
        margins: { top: 40, bottom: 40, left: 90, right: 90 },
        children: cellParas(spec.t, {
          size, bold: isHead,
          align: isHead ? AlignmentType.CENTER : (o.align ? o.align[i] : AlignmentType.LEFT),
        }),
      });
    }).filter(Boolean),
  });
  const caption_p = new Paragraph({
    alignment: AlignmentType.LEFT, keepNext: true, spacing: { before: 240, after: 0, line: 240 },
    children: [new TextRun({ text: `Таблица ${n} — ${caption}`, font: FONT, size: 28 })],
  });
  const tbl = new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, borders,
    rows: [mk(headers, true), ...rows.map((r) => mk(r, false))],
  });
  const after = new Paragraph({ spacing: { before: 0, after: 120, line: 240 }, children: [] });
  return [caption_p, tbl, after];
}

// ------------------------------------------------------------ формулы
function formula(key, mathChildren, o = {}) {
  const n = num("f", key);
  const w = o.width || PORTRAIT_W;
  return new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(w / 2) }, { type: TabStopType.RIGHT, position: w }],
    spacing: { before: 240, after: 240, line: 276 },
    keepNext: true,
    children: [new TextRun({ text: "\t", font: FONT, size: 28 }), new OMath({ children: mathChildren }),
      new TextRun({ text: `\t(${n})`, font: FONT, size: 28 })],
  });
}
const mr = (t) => new MathRun(t);
const sub = (base, s) => new MathSubScript({ children: [mr(base)], subScript: [mr(s)] });
const frac = (numr, den) => new MathFraction({ numerator: numr, denominator: den });

// «где ...» — первая строка с абзаца со слова «где», далее каждое обозначение с новой строки
function where(lines) {
  return lines.map((l, i) => new Paragraph({
    alignment: AlignmentType.LEFT,
    indent: i === 0 ? { firstLine: INDENT } : { left: INDENT + 560 },
    spacing: { before: 0, after: 0, line: 360 },
    children: runs((i === 0 ? "где " : "") + l),
  }));
}

// листинг
function listing(file, o = {}) {
  const lines = fs.readFileSync(file, "utf8").replace(/\t/g, "    ").replace(/\s+$/, "").split("\n");
  return lines.map((l) => new Paragraph({
    spacing: { before: 0, after: 0, line: 240 },
    indent: { firstLine: 0 },
    alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: l.length ? l : " ", font: MONO, size: o.size || 18 })],
  }));
}

module.exports = {
  D, P, H1, H2, H3, StructTitle, list, numberingConfig, figure, table, formula, mr, sub, frac, where,
  listing, runs, resolve, num, counters, created, PORTRAIT_W, LANDSCAPE_W, INDENT, FONT, MONO, declareApp, appItems,
};
