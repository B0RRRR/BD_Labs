"""
Рисунки для пояснительной записки «Система управления проектами».

Отличия от диаграмм ЛР №1 (Lab1/diagrams):
  * нет заголовков внутри рисунков — по ГОСТ 7.32 наименование даётся
    подписью «Рисунок N — ...» под рисунком;
  * шрифты относительно крупнее (параметр K — во сколько раз уменьшается
    физический размер холста при неизменных кеглях), чтобы рисунок читался
    при печати на странице A4;
  * модель данных — итоговая: ЛР №1 + миграция меток (marks, marks_tasks,
    projects.code) + миграция ЛР №2 (tasks.estimate_hours, tasks.completed_at).

Стиль (по эскизу пользователя, 15.11.2026): палитра «bright» — внешние сущности и сущности
голубые с тенью, процессы и компоненты — оранжевая шапка и жёлтое тело, накопители зелёные;
шрифт Arimo (метрики Arial) обычного начертания; потоки чёрные, ортогональные, изломы
скруглены. Схема алгоритма (ГОСТ 19.701) — чёрно-белая, изломы без скругления.
Прежний вид: DIAG_PALETTE=sea (только цвета; шрифт и линии общие).

Рисунки:
  context.png   — контекстная диаграмма (DFD уровня 0), нотация Гейна–Сарсона
  dfd.png       — DFD уровня 1
  dfd2.png      — DFD уровня 2 для процесса 4
  dfd2_p1/p2/p3/p5/p6.png — DFD уровня 2 остальных процессов
  fdd.png       — диаграмма декомпозиции функций (только краткая записка)
  chen.png      — ER-диаграмма в нотации Чена
  quality_chen.png — ER-диаграмма системы оценивания качества (схема quality)
  bpmn_all.png  — обзорная BPMN «Ведение проекта»
  bpmn.png      — процессная модель BPMN «Выполнение задачи проекта» (процесс 4)
  bpmn_p1/p2/p3/p5/p6.png — BPMN остальных процессов
  logical.png   — логическая модель данных (таблицы, ключи, связи)
  arch.png      — архитектура программного обеспечения
  report.png    — схема вычислений аналитического отчёта (report.sql)
  algo.png      — схема алгоритма самого медленного модуля (ГОСТ 19.701)

Запуск:  python3 diagrams.py
"""
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, PathPatch, Polygon,
                                Rectangle)
from matplotlib.path import Path

OUT = os.path.dirname(os.path.abspath(__file__))
# Стиль «упрощённый» (по эскизу пользователя): шрифт с метриками Arial, обычное начертание,
# тёмно-серый текст, тонкие чёрные линии, скруглённые изломы потоков.
plt.rcParams["font.family"] = "Arimo"
TEXT = "#333333"
plt.rcParams["text.color"] = TEXT
BOLD = "normal"   # названия элементов — обычным начертанием

# Палитры. Нотации задают формы и линии, а не цвета, поэтому цвета вынесены сюда.
# Выбор: переменная окружения DIAG_PALETTE (по умолчанию — PALETTE ниже).
PALETTES = {
    "classic": dict(  # исходная: голубой, песочный, зелёный
        ext="#e8eef7", proc="#fdf3e1", store="#eaf5ea", ent="#d9e4f2", shadow="#9aa5b5",
        sys_border="#1d3a8a", sys_fill="#f7f9fd", svc="#e7f3ef", lane="#f3f6fb", client="#eef4fb",
        bpmn_user="#fffbe6", bpmn_service="#e6eefb", db_top="#d6ecd6", op="#f4f4f4",
        card="#b03030", pk="#8a1c1c", fk="#1c3f8a",
        sub={1: "#6a3d9a", 2: "#1b7f5c", 4: "#1f5fbf", 5: "#c25e00", 6: "#b0306a"}),
    "sea": dict(  # морская: бирюза, песок, терракота
        ext="#e1efef", proc="#fbefdc", store="#e7f1e1", ent="#d2e7e6", shadow="#8ea7a6",
        sys_border="#1d5f66", sys_fill="#f5fafa", svc="#e0efeb", lane="#eef6f6", client="#e4f1f1",
        bpmn_user="#fdf5e2", bpmn_service="#dcedee", db_top="#cde5d4", op="#f2f5f5",
        card="#b2452a", pk="#9c3a1d", fk="#1d5f66",
        sub={1: "#5b3e8e", 2: "#1f7a6b", 4: "#1d5f99", 5: "#b5651d", 6: "#9b2c55"}),
    "graphite": dict(  # графит: сдержанные серо-синие заливки, контрастные потоки
        ext="#eceff3", proc="#f5f2ea", store="#ebf0ea", ent="#dfe5ee", shadow="#a3aab5",
        sys_border="#2b3a55", sys_fill="#f8f9fb", svc="#ecf0ee", lane="#f3f4f7", client="#eef0f4",
        bpmn_user="#f7f4ea", bpmn_service="#e6eaf1", db_top="#dbe3d9", op="#f4f4f4",
        card="#a23b2a", pk="#7d2a1f", fk="#2b3a55",
        sub={1: "#5c3c92", 2: "#00796b", 4: "#1e6fd0", 5: "#e07b00", 6: "#c62848"}),
    "pastel": dict(  # пастель: мягкие лавандовые и персиковые заливки
        ext="#ece6f6", proc="#fff2e2", store="#e6f4e8", ent="#e2e8f8", shadow="#ada6c2",
        sys_border="#4527a0", sys_fill="#faf8fd", svc="#e6f4ef", lane="#f5f2fb", client="#f0ecf8",
        bpmn_user="#fff7df", bpmn_service="#ebe5f6", db_top="#d5edd9", op="#f5f3f7",
        card="#c2185b", pk="#ad1457", fk="#4527a0",
        sub={1: "#7b1fa2", 2: "#00897b", 4: "#3949ab", 5: "#ef6c00", 6: "#d81b60"}),
    "bright": dict(  # яркая (эскиз пользователя): голубые сущности, процесс — оранжевая шапка и жёлтое тело
        ext="#a0c8f0", proc="#fff1aa", head="#fa9646", store="#cfe8c0", ent="#a0c8f0", shadow="#a6a6a6",
        sys_border="#808080", sys_fill="#fafafa", svc="#a0c8f0", lane="#f3f3f3", client="#e3effb",
        bpmn_user="#fff1aa", bpmn_service="#a0c8f0", db_top="#b3dc9e", op="white",
        card=TEXT, pk=TEXT, fk=TEXT,
        sub={1: TEXT, 2: TEXT, 4: TEXT, 5: TEXT, 6: TEXT}),
}
PALETTE = "bright"
PAL = PALETTES[os.environ.get("DIAG_PALETTE", PALETTE)]
HEAD = PAL.get("head", PAL["proc"])   # шапка процесса и компонента

LINE = "#222222"
FILL_EXT = PAL["ext"]
FILL_PROC = PAL["proc"]
FILL_STORE = PAL["store"]
FILL_ENT = PAL["ent"]
GREY = "#555555"


# --------------------------------------------------------------------------
# общее
# --------------------------------------------------------------------------
def canvas(w, h, k=1.0, rnd=0.1, shadow=0.045):
    """Холст w × h условных единиц; физический размер — (w·k) × (h·k) дюймов.
    При k < 1 текст и линии становятся относительно крупнее.
    rnd — радиус скругления изломов потоков, shadow — смещение тени (дюймы холста)."""
    fig = plt.figure(figsize=(w * k, h * k))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.rnd, ax.shadow = rnd / k, shadow / k
    return fig, ax


def rounded_path(pts, r):
    """Ломаная pts со скруглёнными (квадратичная кривая) изломами радиуса не больше r."""
    verts, codes = [pts[0]], [Path.MOVETO]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x1, y2 - y1)
        rr = min(r, d1 / 2, d2 / 2)
        if rr <= 1e-9 or abs((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) < 1e-9:
            verts.append((x1, y1))
            codes.append(Path.LINETO)
            continue
        a = (x1 - (x1 - x0) / d1 * rr, y1 - (y1 - y0) / d1 * rr)
        b = (x1 + (x2 - x1) / d2 * rr, y1 + (y2 - y1) / d2 * rr)
        verts += [a, (x1, y1), b]
        codes += [Path.LINETO, Path.CURVE3, Path.CURVE3]
    verts.append(pts[-1])
    codes.append(Path.LINETO)
    return Path(verts, codes)


def save(fig, name, dpi=170):
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=dpi, facecolor="white",
                bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


class Box:
    """Прямоугольная область: центр (x, y), ширина w, высота h."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def l(self):
        return self.x - self.w / 2

    @property
    def r(self):
        return self.x + self.w / 2

    @property
    def t(self):
        return self.y + self.h / 2

    @property
    def b(self):
        return self.y - self.h / 2

    def top(self, dx=0.0):
        return (self.x + dx, self.t)

    def bottom(self, dx=0.0):
        return (self.x + dx, self.b)

    def left(self, dy=0.0):
        return (self.l, self.y + dy)

    def right(self, dy=0.0):
        return (self.r, self.y + dy)


def label(ax, x, y, text, size=10, **kw):
    ax.text(
        x, y, text, ha="center", va="center", fontsize=size, zorder=6,
        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"), **kw,
    )


def arrow(ax, pts, text=None, at=None, size=10, dashed=False, lw=1.3, head=16, color=LINE, both=False,
          rnd=True):
    """Ломаная pts со скруглёнными изломами и стрелкой на последней точке (both — на обеих),
    подпись в точке at."""
    pts = [tuple(p) for p in pts]
    p = FancyArrowPatch(path=rounded_path(pts, ax.rnd if rnd else 0),
                        arrowstyle="<|-|>" if both else "-|>", mutation_scale=head, color=color, lw=lw,
                        ls=(0, (5, 3)) if dashed else "-", zorder=3, joinstyle="miter", capstyle="butt")
    ax.add_patch(p)
    if text:
        if at is None:
            (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
            at = ((x1 + x2) / 2, (y1 + y2) / 2)
        label(ax, at[0], at[1], text, size, color=(TEXT if color == LINE else color))


flow = arrow


def polyline(ax, pts, lw=1.2, color=LINE, rnd=True, **kw):
    ax.add_patch(PathPatch(rounded_path([tuple(p) for p in pts], ax.rnd if rnd else 0), fc="none", ec=color,
                           lw=lw, zorder=3, **kw))


# --------------------------------------------------------------------------
# нотация Гейна–Сарсона
# --------------------------------------------------------------------------
def ext_shape(ax, box, lw=1.2, fc=None):
    """Внешняя сущность Гейна–Сарсона: прямоугольник с тенью."""
    s = ax.shadow
    ax.add_patch(Rectangle((box.l + s, box.b - s), box.w, box.h, fc=PAL["shadow"], ec="none", zorder=1))
    ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=fc or FILL_EXT, ec=LINE, lw=lw, zorder=2))


def external(ax, box, text, size=12):
    ext_shape(ax, box)
    ax.text(box.x, box.y, text, ha="center", va="center", fontsize=size, weight=BOLD, zorder=5, linespacing=1.15)


def proc_shape(ax, box, band, rs, lw=1.2, sub_band=None):
    """Процесс Гейна–Сарсона: скруглённый прямоугольник, сверху цветная полоса с номером,
    снизу (необязательно) полоса подсистемы."""
    body = FancyBboxPatch((box.l, box.b), box.w, box.h, boxstyle=f"round,pad=0,rounding_size={rs}",
                          fc=FILL_PROC, ec="none", zorder=2)
    ax.add_patch(body)
    hd = Rectangle((box.l, box.t - band), box.w, band, fc=HEAD, ec="none", zorder=2.1)
    ax.add_patch(hd)
    hd.set_clip_path(body)
    ax.add_patch(FancyBboxPatch((box.l, box.b), box.w, box.h, boxstyle=f"round,pad=0,rounding_size={rs}",
                                fc="none", ec=LINE, lw=lw, zorder=3))
    ax.plot([box.l, box.r], [box.t - band, box.t - band], color=LINE, lw=lw * 0.8, zorder=3)
    if sub_band:
        ax.plot([box.l, box.r], [box.b + sub_band, box.b + sub_band], color=LINE, lw=lw * 0.6, zorder=3)


def process(ax, box, num, text, size=11, band=0.38, sub=None, color=None, sub_size=None, rs=0.18):
    """Процесс Гейна–Сарсона: сверху полоса с номером, снизу (необязательно) — подсистема."""
    proc_shape(ax, box, band, rs, sub_band=band if sub else None)
    ax.text(box.x, box.t - band / 2, num, ha="center", va="center", fontsize=size, weight=BOLD,
            zorder=5, color=color or TEXT)
    if sub:
        ax.text(box.x, box.b + band / 2, sub, ha="center", va="center", fontsize=sub_size or size - 3,
                style="italic", color=GREY, zorder=5)
        mid = (box.b + band + box.t - band) / 2
    else:
        mid = (box.b + box.t - band) / 2
    ax.text(box.x, mid, text, ha="center", va="center", fontsize=size, zorder=5, linespacing=1.15)


# подсистемы: номер процесса DFD → (название, цвет)
SUBS = {
    1: ("«Пользователи»", PAL["sub"][1]),
    2: ("«Проекты»", PAL["sub"][2]),
    3: ("«Проекты»", PAL["sub"][2]),
    4: ("«Задачи»", PAL["sub"][4]),
    5: ("«Обсуждения»", PAL["sub"][5]),
    6: ("«Отчётность»", PAL["sub"][6]),
}


def store(ax, box, sid, text, size=11, cell=0.55, dup=False):
    """Накопитель Гейна–Сарсона; dup — копия уже изображённого накопителя (дополнительная черта)."""
    ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_STORE, ec="none", zorder=1))
    if dup:
        ax.plot([box.l + cell * 0.2, box.l + cell * 0.2], [box.b, box.t], color=LINE, lw=1.0, zorder=3)
        cell_x = box.l + cell * 0.6
    else:
        cell_x = box.l + cell / 2
    ax.plot([box.r, box.l, box.l, box.r], [box.t, box.t, box.b, box.b], color=LINE, lw=1.2, zorder=3)
    ax.plot([box.l + cell, box.l + cell], [box.b, box.t], color=LINE, lw=1.0, zorder=3)
    ax.text(cell_x, box.y, sid, ha="center", va="center", fontsize=size, weight=BOLD, zorder=5)
    ax.text(box.l + cell + (box.w - cell) / 2, box.y, text, ha="center", va="center", fontsize=size, zorder=5)


def gs_legend(ax, x, y, s=1.0, size=10):
    """Легенда нотации Гейна–Сарсона; s — масштаб геометрии."""
    w, h = 4.6 * s, 3.35 * s
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec="#888888", lw=1, zorder=1))
    ax.text(x + 0.15 * s, y - 0.3 * s, "Обозначения", fontsize=size, weight=BOLD, va="center")
    external(ax, Box(x + 0.7 * s, y - 0.85 * s, 0.9 * s, 0.42 * s), "", 8)
    ax.text(x + 1.4 * s, y - 0.85 * s, "внешняя сущность", fontsize=size, va="center")
    process(ax, Box(x + 0.7 * s, y - 1.5 * s, 0.9 * s, 0.6 * s), "", "", 6, band=0.18 * s)
    ax.text(x + 1.4 * s, y - 1.5 * s, "процесс", fontsize=size, va="center")
    store(ax, Box(x + 0.7 * s, y - 2.07 * s, 0.9 * s, 0.32 * s), "", "", 6, cell=0.22 * s)
    ax.text(x + 1.4 * s, y - 2.07 * s, "накопитель данных", fontsize=size, va="center")
    store(ax, Box(x + 0.7 * s, y - 2.52 * s, 0.9 * s, 0.32 * s), "", "", 6, cell=0.22 * s, dup=True)
    ax.text(x + 1.4 * s, y - 2.52 * s, "копия накопителя", fontsize=size, va="center")
    flow(ax, [(x + 0.25 * s, y - 3.0 * s), (x + 1.15 * s, y - 3.0 * s)])
    ax.text(x + 1.4 * s, y - 3.0 * s, "поток данных", fontsize=size, va="center")


def data_assoc(ax, a, b, both=False, lw=1.0, head=0.17):
    """Ассоциация с данными BPMN: пунктир с открытой стрелкой — к хранилищу (запись)
    или от хранилища (чтение); both — чтение и запись."""
    ax.plot([a[0], b[0]], [a[1], b[1]], color=LINE, lw=lw, ls=(0, (2, 2)), zorder=3)

    def tip(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy) or 1.0
        ux, uy = dx / n, dy / n
        for sgn in (1, -1):
            ax.plot([q[0] - ux * head + sgn * (-uy) * head * 0.55, q[0]],
                    [q[1] - uy * head + sgn * ux * head * 0.55, q[1]], color=LINE, lw=lw * 1.2, zorder=8)
    tip(a, b)
    if both:
        tip(b, a)


def carrow(ax, a, b, rad=0.2, text=None, at=None, size=10, color=LINE, dashed=False, lw=1.4, head=16):
    """Дуговая стрелка от a к b."""
    from matplotlib.patches import FancyArrowPatch
    p = FancyArrowPatch(a, b, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>", mutation_scale=head,
                        color=color, lw=lw, ls=(0, (5, 3)) if dashed else "-", zorder=3,
                        shrinkA=0, shrinkB=0)
    ax.add_patch(p)
    if text:
        label(ax, at[0], at[1], text, size, color=("black" if color == LINE else color))


SUBS = {
    1: ("«Пользователи»", PAL["sub"][1]),
    2: ("«Проекты»", PAL["sub"][2]),
    3: ("«Проекты»", PAL["sub"][2]),
    4: ("«Задачи»", PAL["sub"][4]),
    5: ("«Обсуждения»", PAL["sub"][5]),
    6: ("«Отчётность»", PAL["sub"][6]),
}


def SC(i):
    return SUBS[i][1]


# --------------------------------------------------------------------------
# 1. Контекстная диаграмма
# --------------------------------------------------------------------------
def context_diagram():
    """Контекстная диаграмма (DFD уровня 0).

    Геометрия задана в дюймах печатного размера (k = 1): рисунок вставляется
    в записку шириной 6,5″, поэтому кегли равны печатным. Потоки совпадают
    с внешними потоками DFD уровня 1 (балансировка уровней)."""
    W, H = 6.6, 5.7
    fig, ax = canvas(W, H, k=1.0, rnd=0.06, shadow=0.035)
    L, E = 8.5, 9.5            # кегль подписей потоков и внешних сущностей
    LW, HD, SH = 0.8, 9, 0.035  # толщина потока, наконечник, тень

    def ext(box, name, note=None):
        ext_shape(ax, box, lw=0.9)
        if note is None:
            ax.text(box.x, box.y, name, ha="center", va="center", fontsize=E, weight=BOLD,
                    linespacing=1.15, zorder=5)
            return
        # блок «название + приписка» центрируется в рамке целиком
        h1 = (name.count("\n") + 1) * E * 1.15 / 72
        h2 = (note.count("\n") + 1) * (L - 1) * 1.15 / 72
        top = box.y + (h1 + 0.05 + h2) / 2
        ax.text(box.x, top, name, ha="center", va="top", fontsize=E, weight=BOLD,
                linespacing=1.15, zorder=5)
        ax.text(box.x, top - h1 - 0.05, note, ha="center", va="top", fontsize=L - 1, color=GREY,
                linespacing=1.15, zorder=5)

    def proc(box, num, text, band=0.3):
        proc_shape(ax, box, band, 0.08, lw=0.9)
        ax.text(box.x, box.t - band / 2, num, ha="center", va="center", fontsize=11, weight=BOLD, zorder=5)
        ax.text(box.x, (box.b + box.t - band) / 2, text, ha="center", va="center", fontsize=11,
                linespacing=1.2, zorder=5)

    def fl(pts):
        arrow(ax, pts, lw=LW, head=HD)

    def lab(x, y, text, above=True):
        ax.text(x, y + (0.04 if above else -0.04), text, ha="center", va="bottom" if above else "top",
                fontsize=L, linespacing=1.15, zorder=6)

    # ---------------------------------------------------------------- элементы
    XL, XR, BW = 0.8, 5.8, 1.5                    # центры и ширина боковых столбцов
    p = Box(3.3, 3.1, 1.2, 2.5)                  # процесс 0: x 2.7–3.9, y 1.85–4.35
    adm = Box(XL, 5.1, BW, 0.7)
    cat = Box(XR, 5.1, BW, 0.7)
    lead = Box(XL, 2.95, BW, 2.2)
    mem = Box(XR, 2.95, BW, 2.2)
    git = Box(XL, 1.1, BW, 1.05)
    ntf = Box(XR, 1.1, BW, 1.05)

    proc(p, "0", "Система\nуправления\nпроектами")
    ext(adm, "Администратор")
    ext(cat, "Каталог\nсотрудников", "единый вход (SSO)")
    ext(lead, "Руководитель\nпроекта")
    ext(mem, "Участник\nпроекта\n(исполнитель)")
    ext(git, "Git-хостинг", "репозитории\nпроектов")
    ext(ntf, "Сервис\nуведомлений", "почта, мессенджер,\nкалендарь")

    # ---------------------------------------------------------------- администратор и каталог
    fl([adm.right(0.12), (3.25, adm.y + 0.12), (3.25, p.t)])
    lab((adm.r + 2.95) / 2, adm.y + 0.12, "данные\nпользователя")
    fl([(2.95, p.t), (2.95, adm.y - 0.12), adm.right(-0.12)])
    lab((adm.r + 2.95) / 2, adm.y - 0.12, "подтверждение\nрегистрации", above=False)
    fl([cat.left(), (3.65, cat.y), (3.65, p.t)])
    lab((cat.l + 3.65) / 2, cat.y, "учётные записи\nсотрудников")

    # ---------------------------------------------------------------- руководитель (слева)
    ys = [lead.y + 0.95, lead.y + 0.33, lead.y - 0.33, lead.y - 0.95]
    yl = [lead.y + 1.0, lead.y + 0.55, lead.y + 0.05, lead.y - 0.5, lead.y - 0.98]
    xm = (lead.r + p.l) / 2
    fl([lead.right(yl[0] - lead.y), (p.l, yl[0])]);  lab(xm, yl[0], "проект, заказчик,\nдоговор")
    fl([lead.right(yl[1] - lead.y), (p.l, yl[1])]);  lab(xm, yl[1], "участник и роль")
    fl([lead.right(yl[2] - lead.y), (p.l, yl[2])]);  lab(xm, yl[2], "задачи (в т. ч.\nфайлом CSV),\nспринты")
    fl([lead.right(yl[3] - lead.y), (p.l, yl[3])]);  lab(xm, yl[3], "параметры\nотчёта")
    fl([(p.l, yl[4]), lead.right(yl[4] - lead.y)]);  lab(xm, yl[4], "перечни\nи отчёты")

    # ---------------------------------------------------------------- участник (справа)
    xm = (p.r + mem.l) / 2
    fl([(p.r, ys[0]), mem.left(ys[0] - mem.y)]);  lab(xm, ys[0], "назначенные\nзадачи")
    fl([mem.left(ys[1] - mem.y), (p.r, ys[1])]);  lab(xm, ys[1], "новый статус,\nтрудозатраты")
    fl([(p.r, ys[2]), mem.left(ys[2] - mem.y)]);  lab(xm, ys[2], "обсуждение")
    fl([mem.left(ys[3] - mem.y), (p.r, ys[3])]);  lab(xm, ys[3], "комментарий")

    # ---------------------------------------------------------------- Git и сервис уведомлений
    fl([git.right(), (2.85, git.y), (2.85, p.b)])
    lab((git.r + 2.85) / 2, git.y, "коммит с ключом\nзадачи (SHOP-42)")
    fl([(3.75, p.b), (3.75, ntf.y + 0.3), ntf.left(0.3)])
    lab((3.75 + ntf.l) / 2, ntf.y + 0.3, "назначение,\nэскалация")
    fl([(3.45, p.b), (3.45, ntf.y), ntf.left()])
    lab((3.45 + ntf.l) / 2, ntf.y, "отчёт заказчику")
    fl([(3.15, p.b), (3.15, ntf.y - 0.3), ntf.left(-0.3)])
    lab((3.15 + ntf.l) / 2, ntf.y - 0.3, "новый\nкомментарий", above=False)

    # ---------------------------------------------------------------- легенда (строкой)
    # элементы расставляются по измеренной ширине текста и центрируются по рисунку
    ly, gap, pad = 0.2, 0.08, 0.3
    rend = fig.canvas.get_renderer()

    def tw(t, **kw):
        tx = ax.text(0, 0, t, fontsize=L, **kw)
        w = tx.get_window_extent(rend).width / fig.dpi
        tx.remove()
        return w

    items = [("title", "Обозначения:", 0.0), ("ext", "внешняя сущность", 0.36),
             ("proc", "процесс", 0.36), ("flow", "поток данных", 0.42)]
    widths = [tw(t, weight=BOLD) if k == "title" else s + gap + tw(t) for k, t, s in items]
    total = sum(widths) + pad * (len(items) - 1)
    x = W / 2 - total / 2
    ax.add_patch(Rectangle((x - 0.15, ly - 0.17), total + 0.3, 0.34, fc="white", ec="#888888", lw=0.7, zorder=1))
    for (k, t, s), w in zip(items, widths):
        if k == "title":
            ax.text(x, ly, t, fontsize=L, weight=BOLD, va="center")
        else:
            if k == "ext":
                ax.shadow = 0.02
                ext_shape(ax, Box(x + s / 2, ly, s, 0.18), lw=0.8)
            elif k == "proc":
                proc_shape(ax, Box(x + s / 2, ly, s, 0.22), 0.07, 0.04, lw=0.8)
            else:
                arrow(ax, [(x, ly), (x + s, ly)], lw=LW, head=HD)
            ax.text(x + s + gap, ly, t, fontsize=L, va="center")
        x += w + pad

    save(fig, "context", dpi=300)


# --------------------------------------------------------------------------
# 2. DFD уровня 1
# --------------------------------------------------------------------------
def dfd_diagram():
    """DFD уровня 1. Накопители построены по принципу «один накопитель — одна таблица».
    D8 и D9 (метки) использует только процесс 4 — они показаны на его DFD уровня 2.
    Накопители стоят в два ряда со сдвигом на полшага, поэтому каждая запись и каждое
    чтение — прямая вертикаль без пересечений; накопитель, который пишет один процесс,
    а читает соседний, стоит на их границе."""
    W, H = 33.4, 17.0
    fig, ax = canvas(W, H, k=0.53)
    S, L = 16, 14

    def ext_copy(box, text, size=S):
        external(ax, box, text, size)
        c = 0.4
        ax.plot([box.r - c, box.r], [box.b, box.b + c], color=LINE, lw=1.2, zorder=4)

    def st(x0, x1, y, sid, name):
        b = Box((x0 + x1) / 2, y, x1 - x0, 1.1)
        store(ax, b, sid, name, L, cell=0.7)
        return b

    def v(x, y0, y1, text=None, at=None, both=False):
        flow(ax, [(x, y0), (x, y1)], text, at=at, size=L, both=both)

    # внешние сущности
    yE = 14.9
    adm = Box(2.9, yE, 3.6, 1.3); external(ax, adm, "Администратор", S)
    cat = Box(7.2, yE, 3.6, 1.3); external(ax, cat, "Каталог\nсотрудников", S)
    lead = Box(11.7, yE, 3.6, 1.3); external(ax, lead, "Руководитель\nпроекта", S)
    git = Box(16.7, yE, 3.0, 1.3); external(ax, git, "Git-хостинг", S)
    ntf = Box(21.5, yE, 3.6, 1.3); external(ax, ntf, "Сервис\nуведомлений", S)
    mem = Box(26.3, yE, 3.8, 1.3); external(ax, mem, "Участник проекта\n(исполнитель)", S)
    ntf2 = Box(30.1, yE, 3.0, 1.3); ext_copy(ntf2, "Сервис\nуведомлений", S)

    # процессы
    yP = 10.8
    P1 = Box(2.8, yP, 3.2, 2.4); process(ax, P1, "1", "Регистрация\nпользователей", S, band=0.45, sub=SUBS[1][0], sub_size=12)
    P2 = Box(8.8, yP, 7.2, 2.4); process(ax, P2, "2", "Ведение проектов\nи договоров", S, band=0.45, sub=SUBS[2][0], sub_size=12)
    P3 = Box(14.5, yP, 3.2, 2.4); process(ax, P3, "3", "Управление\nсоставом", S, band=0.45, sub=SUBS[3][0], sub_size=12)
    P4 = Box(21.45, yP, 9.5, 2.4); process(ax, P4, "4", "Управление задачами\nи спринтами", S, band=0.45, sub=SUBS[4][0], sub_size=12)
    P5 = Box(28.4, yP, 3.2, 2.4); process(ax, P5, "5", "Обсуждение\nзадач", S, band=0.45, sub=SUBS[5][0], sub_size=12)
    P6 = Box(17.75, 2.0, 27.9, 2.4); process(ax, P6, "6", "Формирование отчётов", S, band=0.45, sub=SUBS[6][0], sub_size=12)

    # накопители: ряд A (y = 7.4) и ряд B (y = 5.4), сдвинутый на полшага
    yA, yB = 7.4, 5.4
    D1 = st(3.2, 6.4, yA, "D1", "Пользователи")
    D4 = st(6.9, 10.1, yA, "D4", "Договоры")
    D3 = st(10.9, 14.1, yA, "D3", "Проекты")
    D5 = st(14.7, 17.9, yA, "D5", "Участники\nпроектов")
    D10 = st(19.6, 22.8, yA, "D10", "История\nстатусов")
    D7 = st(24.9, 28.1, yA, "D7", "Задачи")
    D12 = st(28.6, 31.5, yA, "D12", "Коммен-\nтарии")
    D2 = st(8.9, 12.1, yB, "D2", "Заказчики")
    D6 = st(17.15, 20.35, yB, "D6", "Спринты")
    D11 = st(22.25, 25.45, yB, "D11", "Трудо-\nзатраты")

    pb, at_ = P1.b, D1.t           # нижняя грань процессов и верх ряда A
    ya = (pb + at_) / 2            # подписи записи и чтения между процессами и рядом A
    yab = (D1.b + D2.t) / 2        # подписи между рядами
    ybp = (D2.b + P6.t) / 2        # подписи между рядом B и процессом 6

    # запись в накопители и чтение соседним процессом
    v(3.8, pb, D1.t, "новый\nсотрудник", at=(3.8, ya))
    v(5.85, D1.t, pb, "владелец", at=(5.85, ya))
    v(8.5, pb, D4.t, "договор", at=(8.5, ya))
    v(10.5, pb, D2.t, "заказчик", at=(10.5, yab))
    v(11.45, pb, D3.t, "проект", at=(11.45, ya))
    v(13.5, D3.t, pb, "проект", at=(13.5, ya))
    v(15.3, pb, D5.t, "участник,\nроль", at=(15.3, ya))
    v(17.35, D5.t, pb, "участники", at=(17.35, ya))
    v(18.75, pb, D6.t, "спринт", at=(18.75, yab), both=True)
    v(21.2, pb, D10.t, "история", at=(21.2, ya))
    v(23.85, pb, D11.t, "часы", at=(23.85, yab))
    v(25.5, pb, D7.t, "задача", at=(25.5, ya), both=True)
    v(27.5, D7.t, pb, "задача", at=(27.5, ya))
    v(29.4, pb, D12.t, "коммен-\nтарий", at=(29.4, ya))

    # чтение процессом 6
    for x, d, t, y in [(4.4, D1, "ФИО", yab), (7.6, D4, "договоры", yab), (13.0, D3, "проекты", yab),
                       (15.9, D5, "участники", yab), (21.3, D10, "история", yab), (26.8, D7, "задачи", yab),
                       (30.0, D12, "коммен-\nтарии", yab),
                       (10.5, D2, "заказчики", ybp), (18.75, D6, "спринты", ybp), (23.85, D11, "трудо-\nзатраты", ybp)]:
        v(x, d.b, P6.t, t, at=(x, y))

    # внешние сущности ↔ процессы
    yk = (P1.t + adm.b) / 2
    flow(ax, [adm.bottom(-1.0), (adm.x - 1.0, P1.t)], "данные\nпользователя", at=(adm.x - 1.0, yk + 0.45), size=L)
    flow(ax, [(adm.x + 0.6, P1.t), adm.bottom(0.6)], "подтвер-\nждение", at=(adm.x + 0.6, yk - 0.45), size=L)
    yc = yk + 0.1
    flow(ax, [cat.bottom(-0.9), (cat.x - 0.9, yc), (P1.r - 0.4, yc), (P1.r - 0.4, P1.t)], "учётные\nзаписи",
         at=(cat.x - 0.9, yc + 0.55), size=L)
    flow(ax, [lead.bottom(-1.3), (lead.x - 1.3, P2.t)], "проект,\nзаказчик,\nдоговор", at=(lead.x - 1.3, yk), size=L)
    flow(ax, [lead.bottom(1.3), (lead.x + 1.3, P3.t)], "участник\nи роль", at=(lead.x + 1.3, yk), size=L)
    yl = yk - 0.55
    flow(ax, [lead.right(0.3), (14.85, lead.y + 0.3), (14.85, yl), (17.1, yl), (17.1, P4.t)],
         "задачи\n(в т. ч. CSV),\nспринты", at=(14.85, yk + 0.35), size=L)
    flow(ax, [git.bottom(1.2), (git.x + 1.2, P4.t)], "коммит\nSHOP-42", at=(git.x + 1.2, yk + 0.3), size=L)
    flow(ax, [(ntf.x, P4.t), ntf.bottom()], "назначение,\nэскалация", at=(ntf.x, yk), size=L)
    flow(ax, [(mem.x - 1.4, P4.t), mem.bottom(-1.4)], "назначенные\nзадачи", at=(mem.x - 1.4, yk + 0.5), size=L)
    flow(ax, [mem.bottom(-0.5), (mem.x - 0.5, P4.t)], "статус,\nчасы", at=(mem.x - 0.5, yk - 0.5), size=L)
    flow(ax, [mem.bottom(0.9), (mem.x + 0.9, P5.t)], "коммен-\nтарий", at=(mem.x + 0.9, yk + 0.5), size=L)
    flow(ax, [(mem.x + 1.7, P5.t), mem.bottom(1.7)], "обсуж-\nдение", at=(mem.x + 1.7, yk - 0.5), size=L)
    flow(ax, [(ntf2.x - 0.3, P5.t), ntf2.bottom(-0.3)], "новый\nкоммен-\nтарий", at=(ntf2.x + 0.05, yk), size=L)

    # отчёты: петли по левому краю и вывод заказчику по правому
    flow(ax, [P6.left(-0.6), (0.25, P6.y - 0.6), (0.25, 16.6), (lead.x + 0.35, 16.6), lead.top(0.35)],
         "перечни и отчёты", at=(7.6, 16.6), size=L)
    flow(ax, [lead.top(-0.35), (lead.x - 0.35, 16.2), (0.65, 16.2), (0.65, P6.y + 0.5), P6.left(0.5)],
         "параметры отчёта", at=(3.3, 16.2), size=L)
    flow(ax, [P6.right(), (32.3, P6.y), (32.3, ntf2.y), ntf2.right()], "отчёт\nзаказчику", at=(32.3, 9.3), size=L)

    # обозначения
    lx, ly = 14.6, 16.5
    ax.text(lx, ly, "Обозначения:", fontsize=L, weight=BOLD, va="center")
    external(ax, Box(lx + 3.0, ly, 1.0, 0.5), "", 8)
    ax.text(lx + 3.65, ly, "внешняя сущность", fontsize=L, va="center")
    ext_copy(Box(lx + 7.6, ly, 1.0, 0.5), "", 8)
    ax.text(lx + 8.25, ly, "её копия", fontsize=L, va="center")
    process(ax, Box(lx + 10.7, ly, 1.0, 0.6), "", "", 6, band=0.18)
    ax.text(lx + 11.35, ly, "процесс", fontsize=L, va="center")
    store(ax, Box(lx + 13.8, ly, 1.1, 0.45), "", "", 6, cell=0.3)
    ax.text(lx + 14.5, ly, "накопитель", fontsize=L, va="center")
    save(fig, "dfd")


# --------------------------------------------------------------------------
# 2a. DFD уровня 2 для процесса 4 «Управление задачами и спринтами»
# --------------------------------------------------------------------------
def dfd2_diagram():
    """DFD уровня 2 процесса 4: 13 атомарных подпроцессов (4.10–4.13 добавлены в конец нумерации).
    Сверху — подпроцессы, которые пишут задачи (D7) и метки (D8, D9), снизу — спринты (D6) и приоритет,
    справа — назначение, смена статуса и трудозатраты (связь с участником). Копии сущностей
    и накопителей отмечены чертой."""
    W, H = 42.4, 19.6
    fig, ax = canvas(W, H, k=0.5)
    S, L = 16, 14
    pw, ph = 3.8, 2.3

    def ext_copy(box, text, size=S):
        external(ax, box, text, size)
        c = 0.4
        ax.plot([box.r - c, box.r], [box.b, box.b + c], color=LINE, lw=1.2, zorder=4)

    def proc(x, y, num, text):
        b = Box(x, y, pw, ph)
        process(ax, b, num, text, S, band=0.45)
        return b

    def st(x, y, sid, name, w=2.8, h=0.9, dup=False):
        b = Box(x, y, w, h)
        store(ax, b, sid, name, L, cell=0.7, dup=dup)
        return b

    y1, yB, y2 = 14.6, 10.6, 6.2
    xt = [2.5, 6.7, 10.9, 15.1, 19.3, 23.5]
    xb = [2.5, 7.0, 11.5, 15.7, 19.6, 23.8]
    xR, xS = 33.6, 40.0

    # внешние сущности
    r1 = Box(13.0, 18.4, 24.8, 1.3); external(ax, r1, "Руководитель проекта", S)
    r2 = Box(12.55, 1.3, 23.9, 1.3); ext_copy(r2, "Руководитель проекта", S)
    u1 = Box(xS, y1, 3.8, 1.3); external(ax, u1, "Участник\nпроекта", L)
    ntf = Box(xS, 11.7, 3.8, 1.3); external(ax, ntf, "Сервис\nуведомлений", L)
    u2 = Box(xS, 5.3, 3.8, 6.0); ext_copy(u2, "Участник\nпроекта", S)

    # подпроцессы
    p48 = proc(xt[0], y1, "4.8", "Пакетная\nзагрузка")
    p41 = proc(xt[1], y1, "4.1", "Создание\nзадачи")
    p410 = proc(xt[2], y1, "4.10", "Оценка\nтрудоёмкости")
    p44 = proc(xt[3], y1, "4.4", "Удаление\nзадачи")
    p45 = proc(xt[4], y1, "4.5", "Ведение\nметок")
    p412 = proc(xt[5], y1, "4.12", "Назначение\nметок задачам")
    p46 = proc(xb[0], y2, "4.6", "Ведение\nспринтов")
    p413 = proc(xb[2], y2, "4.13", "Планирование\nзадач в спринт")
    p47 = proc(xb[3], y2, "4.7", "Закрытие\nспринта")
    p411 = proc(xb[5], y2, "4.11", "Изменение\nприоритета")
    p42 = proc(xR, y1, "4.2", "Назначение\nисполнителя")
    p43 = proc(xR, 9.2, "4.3", "Смена\nстатуса")
    p49 = proc(xR, 3.0, "4.9", "Учёт\nтрудозатрат")
    git = Box(xR, 6.0, 3.0, 1.0); external(ax, git, "Git-хостинг", L)
    ntf2 = Box(29.2, y2, 3.3, 1.3); ext_copy(ntf2, "Сервис\nуведомлений", L - 1)

    # накопители
    d7 = Box((0.6 + 17.0) / 2, yB, 17.0 - 0.6, 1.25)
    store(ax, d7, "D7", "Задачи (tasks)", L, cell=0.7)
    d7c = st(30.2, 12.0, "D7", "Задачи", w=2.6, h=0.8, dup=True)
    d6 = st(xb[1], y2, "D6", "Спринты", w=2.7, h=1.1)
    d6c = st(xb[4], y2, "D6", "Спринты", w=2.5, h=0.9, dup=True)
    d6c2 = st(12.3, 12.35, "D6", "Спринты", w=2.3, h=0.7, dup=True)
    d8 = st(21.4, 12.3, "D8", "Метки", w=2.5, h=0.8)
    d9 = st(24.7, 10.4, "D9", "Метки\nзадач", w=2.6, h=1.0)
    d5 = st(35.2, 18.4, "D5", "Участники\nпроектов", w=3.8, h=1.25)
    d5c = st(xR, 0.75, "D5", "Участники", w=3.8, h=0.8, dup=True)
    d10 = st(29.5, 8.2, "D10", "История\nстатусов", h=1.0)
    d11 = st(29.5, 3.0, "D11", "Трудо-\nзатраты", h=1.0)

    # руководитель → подпроцессы
    ym = (r1.b + p48.t) / 2
    for b, lab in zip([p48, p41, p410, p44, p45, p412],
                      ["файл CSV", "задача", "оценка", "удаление\nзадачи", "метки", "метки\nзадачам"]):
        flow(ax, [(b.x, r1.b), b.top()], lab, at=(b.x, ym), size=L)
    flow(ax, [r1.right(), (xR - 1.3, r1.y), p42.top(-1.3)], "исполнитель, срок", at=(28.9, r1.y), size=L)
    ym2 = (r2.t + p46.b) / 2
    for b, lab in zip([p46, p413, p47, p411], ["спринт", "задачи\nв спринт", "закрытие\nспринта", "приоритет"]):
        flow(ax, [(b.x, r2.t), b.bottom()], lab, at=(b.x, ym2), size=L)

    # D7 «Задачи» — запись сверху и снизу
    yw = (p48.b + d7.t) / 2
    flow(ax, [p48.bottom(), (xt[0], d7.t)], "задачи\nпакета", at=(xt[0], yw), size=L)
    flow(ax, [p41.bottom(), (xt[1], d7.t)], "новая\nзадача", at=(xt[1], yw), size=L)
    flow(ax, [p410.bottom(-0.9), (xt[2] - 0.9, d7.t)], "оценка", at=(xt[2] - 0.9, yw), size=L)
    flow(ax, [(d6c2.x, d6c2.t), (d6c2.x, p410.b)], None)
    ax.text(d6c2.r + 0.12, d6c2.y + 0.45, "ёмкость", fontsize=L - 1.5, va="center", ha="left")
    flow(ax, [p44.bottom(), (xt[3], d7.t)], "удаление", at=(xt[3], yw), size=L)
    yr = (d7.b + p46.t) / 2
    flow(ax, [p413.top(), (xb[2], d7.b)], "спринт\nзадачи", at=(xb[2], yr), size=L)
    flow(ax, [p47.top(), (xb[3], d7.b)], "перенос\nзадач", at=(xb[3], yr), size=L, both=True)
    flow(ax, [p411.top(-1.3), (xb[5] - 1.3, yB), d7.right()], "приоритет", at=(19.0, yB), size=L)

    # D6 «Спринты»
    flow(ax, [p46.right(), d6.left()], "спринт", at=((p46.r + d6.l) / 2, d6.y + 0.5), size=L - 1)
    flow(ax, [d6.right(), p413.left()], "ёмкость", at=((d6.r + p413.l) / 2, d6.y + 0.5), size=L - 1)
    flow(ax, [p47.right(), d6c.left()], "статус", at=((p47.r + d6c.l) / 2, d6c.y + 0.5), size=L - 1.5, both=True)

    # D8, D9 — метки
    flow(ax, [p45.bottom(1.3), (xt[4] + 1.3, d8.t)], "метка", at=(xt[4] - 0.2, 12.9), size=L - 1.5)
    flow(ax, [(22.3, d8.t), (22.3, p412.b)], None)
    ax.text(22.45, d8.t + 0.32, "метки", fontsize=L - 1.5, va="center", ha="left")
    flow(ax, [p412.bottom(1.2), (xt[5] + 1.2, d9.t)], "метки\nзадач", at=(xt[5] + 1.2, 12.25), size=L - 1.5)

    # правый столбец: D7 (копия), D10, D11, D5
    flow(ax, [p42.left(-0.6), (d7c.x, p42.y - 0.6), d7c.top()], "исполнитель", at=(d7c.x, 13.3), size=L - 1.5)
    flow(ax, [p43.left(0.6), (d7c.x, p43.y + 0.6), d7c.bottom()], "статус", at=(d7c.x, 10.6), size=L - 1.5)
    flow(ax, [(p43.l, d10.y), d10.right()], "история", at=((p43.l + d10.r) / 2, d10.y - 0.45), size=L - 1.5)
    flow(ax, [(p49.l, d11.y), d11.right()], "часы", at=((p49.l + d11.r) / 2, d11.y + 0.4), size=L - 1.5)
    flow(ax, [(34.8, d5.b), p42.top(1.2)], "участники", at=(34.8, (d5.b + p42.t) / 2), size=L - 1)
    flow(ax, [d5c.top(), p49.bottom()], "участники", at=(xR + 1.0, (d5c.t + p49.b) / 2), size=L - 1.5)

    # участник, Git-хостинг, сервис уведомлений
    flow(ax, [p42.right(), u1.left()], "назначенные\nзадачи", at=((p42.r + u1.l) / 2, y1), size=L - 1)
    flow(ax, [p42.bottom(1.4), (xR + 1.4, ntf.y), ntf.left()], "назначение", at=(xR + 3.55, ntf.y + 0.45), size=L - 1.5)
    flow(ax, [p43.right(0.9), (xS - 1.1, p43.y + 0.9), (xS - 1.1, ntf.b)], "проверка",
         at=(xR + 3.4, p43.y + 0.9), size=L - 1.5)
    flow(ax, [(u2.l, 8.6), (p43.r, 8.6)], "новый\nстатус", at=((p43.r + u2.l) / 2, 8.0), size=L - 1.5)
    flow(ax, [git.top(), p43.bottom()], "коммит SHOP-42", at=(xR, (git.t + p43.b) / 2), size=L - 2)
    flow(ax, [(u2.l, p49.y), p49.right()], "трудо-\nзатраты", at=((p49.r + u2.l) / 2, p49.y), size=L - 1.5)
    flow(ax, [p411.right(), ntf2.left()], None)
    label(ax, (p411.r + ntf2.l) / 2, y2 + 0.4, "эскалация", L - 1.5)

    # обозначения копий
    lx, ly = 36.2, 1.15
    ax.text(lx, ly, "Копии:", fontsize=L - 1, va="center")
    ext_copy(Box(lx + 1.95, ly, 0.9, 0.45), "", 8)
    ax.text(lx + 2.55, ly, "сущности", fontsize=L - 1, va="center")
    store(ax, Box(lx + 1.95, ly - 0.7, 0.9, 0.4), "", "", 8, cell=0.28, dup=True)
    ax.text(lx + 2.55, ly - 0.7, "накопителя", fontsize=L - 1, va="center")

    save(fig, "dfd2")


# --------------------------------------------------------------------------
# 3. Диаграмма декомпозиции функций
# --------------------------------------------------------------------------
def fdd_diagram():
    """Дерево функций: 6 функций = процессы DFD-1, 35 подфункций = подпроцессы DFD-2 (атомарные:
    один инициатор, один момент, одни правила и накопители). Новые номера — в конце (2.7, 4.10–4.13).
    Функция 4 — в два столбца."""
    W = 28.6
    fig, ax = canvas(W, 11.9, k=0.58)
    ax.set_ylim(-1.7, 10.2)
    S, SS = 15, 13.5

    def rect(box, text, fc, size):
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=fc, ec=LINE, lw=1.2, zorder=2))
        ax.text(box.x, box.y, text, ha="center", va="center", fontsize=size, weight=BOLD, zorder=5,
                linespacing=1.12)

    root = Box(W / 2, 9.6, 9.0, 1.0)
    rect(root, "Система управления проектами", HEAD, 17)
    funcs = [
        ("1. Регистрация\nпользователей", [["1.1. Регистрация", "1.2. Изменение\nданных", "1.3. Удаление"]]),
        ("2. Ведение проектов\nи договоров",
         [["2.1. Создание\nпроекта", "2.2. Назначение\nвладельца", "2.3. Изменение\nпараметров проекта",
           "2.4. Удаление", "2.5. Ведение\nзаказчиков", "2.6. Договор\nс заказчиком",
           "2.7. Привязка\nзаказчика к проекту"]]),
        ("3. Управление\nсоставом",
         [["3.1. Добавление\nучастника", "3.2. Назначение\nроли", "3.3. Исключение\nучастника"]]),
        ("4. Управление задачами и спринтами",
         [["4.1. Создание\nзадачи", "4.2. Назначение\nисполнителя", "4.3. Смена\nстатуса", "4.4. Удаление",
           "4.5. Ведение\nметок", "4.6. Ведение\nспринтов", "4.7. Закрытие\nспринта"],
          ["4.8. Пакетная\nзагрузка", "4.9. Учёт\nтрудозатрат", "4.10. Оценка\nтрудоёмкости",
           "4.11. Изменение\nприоритета", "4.12. Назначение\nметок задачам", "4.13. Планирование\nзадач в спринт"]]),
        ("5. Обсуждение\nзадач",
         [["5.1. Добавление\nкомментария", "5.2. Просмотр\nобсуждения", "5.3. Удаление\nкомментария"]]),
        ("6. Формирование\nотчётов",
         [["6.1. Операционные\nперечни", "6.2. Анализ\nзагрузки команд", "6.3. Отчёт\nо рисках",
           "6.4. Отчёт\nзаказчику", "6.5. Отчёт\nпо договорам", "6.6. Показатели\nкоманды"]]),
    ]
    step, x0 = 4.04, 2.15
    bus_y, fy = 8.65, 7.75
    slot = 0
    centers = []
    for name, cols in funcs:
        n = len(cols)
        centers.append(x0 + (slot + (n - 1) / 2) * step)
        slot += n
    ax.plot([root.x, root.x], [root.b, bus_y], color=LINE, lw=1.2)
    ax.plot([centers[0], centers[-1]], [bus_y, bus_y], color=LINE, lw=1.2)
    slot = 0
    for x, (name, cols) in zip(centers, funcs):
        n = len(cols)
        f = Box(x, fy, 3.85 + (n - 1) * step, 1.15)
        ax.plot([x, x], [bus_y, f.t], color=LINE, lw=1.2)
        rect(f, name, FILL_PROC, S)
        for c, subs in enumerate(cols):
            spine = x0 + (slot + c) * step - 3.85 / 2 + 0.22
            ys = [6.4 - k * 1.2 for k in range(len(subs))]
            ax.plot([spine, spine], [f.b, ys[-1] + 0.2], color=LINE, lw=1.0)
            polyline(ax, [(spine, ys[-1] + 0.25), (spine, ys[-1]), (spine + 0.25, ys[-1])], lw=1.0)
            for y, t in zip(ys, subs):
                sb = Box(spine + 0.25 + 3.38 / 2, y, 3.38, 0.98)
                ax.plot([spine + (0.2 if y == ys[-1] else 0), sb.l], [y, y], color=LINE, lw=1.0)
                rect(sb, t, "white", SS)
        slot += n

    save(fig, "fdd")


# --------------------------------------------------------------------------
# 4. ER-диаграмма в нотации Чена
# --------------------------------------------------------------------------
def chen_kit(fig, ax, K, AS, cw=0.095):
    """Элементы нотации Чена: сущность (слабая — двойная рамка), атрибут (ключ подчёркнут,
    частичный ключ — пунктиром, производный — пунктирный эллипс), связь-ромб
    (идентифицирующая — двойной), линия участия (полное — двойная) и кратность."""
    renderer = fig.canvas.get_renderer()

    def entity(box, name, table, weak=False):
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_ENT, ec=LINE, lw=1.4, zorder=4))
        if weak:
            ax.add_patch(Rectangle((box.l + 0.12, box.b + 0.12), box.w - 0.24, box.h - 0.24,
                                   fc="none", ec=LINE, lw=1.0, zorder=5))
        ax.text(box.x, box.y + 0.17, name, ha="center", va="center", fontsize=13.5, weight=BOLD, zorder=6)
        ax.text(box.x, box.y - 0.3, f"({table})", ha="center", va="center", fontsize=12, color=GREY, zorder=6)

    def attr(x, y, text, ent, key=False, partial=False, derived=False):
        ax.plot([x, ent.x], [y, ent.y], color=LINE, lw=1.0, zorder=1)
        w = max(1.7, cw * len(text) / K + 0.55)
        ax.add_patch(Ellipse((x, y), w, 0.78, fc="white", ec=LINE, lw=1.0, zorder=4,
                             linestyle=(0, (4, 2.5)) if derived else "-"))
        t = ax.text(x, y, text, ha="center", va="center", fontsize=AS, zorder=6)
        if key or partial:
            bb = t.get_window_extent(renderer=renderer).transformed(ax.transData.inverted())
            ax.plot([bb.x0, bb.x1], [bb.y0 + 0.01, bb.y0 + 0.01], color=LINE, lw=1.1, zorder=6,
                    linestyle=(0, (3, 2)) if partial else "-")

    def rel(x, y, text, w=2.9, h=1.45, ident=False):
        ax.add_patch(Polygon([(x - w / 2, y), (x, y + h / 2), (x + w / 2, y), (x, y - h / 2)],
                             closed=True, fc=FILL_PROC, ec=LINE, lw=1.3, zorder=4))
        if ident:
            d = 0.22
            ax.add_patch(Polygon([(x - w / 2 + d * 1.6, y), (x, y + h / 2 - d), (x + w / 2 - d * 1.6, y),
                                  (x, y - h / 2 + d)], closed=True, fc="none", ec=LINE, lw=1.0, zorder=5))
        ax.text(x, y, text, ha="center", va="center", fontsize=11.5, weight=BOLD, zorder=6, linespacing=1.1)
        return (x, y)

    def link(a, b, total=False):
        (x1, y1), (x2, y2) = a, b
        if not total:
            ax.plot([x1, x2], [y1, y2], color=LINE, lw=1.2, zorder=2)
            return
        dx, dy = x2 - x1, y2 - y1
        n = (dx ** 2 + dy ** 2) ** 0.5
        ox, oy = -dy / n * 0.06, dx / n * 0.06
        for sgn in (1, -1):
            ax.plot([x1 + sgn * ox, x2 + sgn * ox], [y1 + sgn * oy, y2 + sgn * oy], color=LINE, lw=1.1, zorder=2)

    def card(x, y, text):
        ax.text(x, y, text, ha="center", va="center", fontsize=15, weight=BOLD, color=PAL["card"], zorder=7)

    def conn(ent_pt, rel_pt, text, total=False, side=1):
        """Связь сущность — ромб и кратность у сущности (сдвиг вдоль линии и вбок)."""
        link(ent_pt, rel_pt, total)
        (x1, y1), (x2, y2) = ent_pt, rel_pt
        dx, dy = x2 - x1, y2 - y1
        n = (dx ** 2 + dy ** 2) ** 0.5
        ux, uy = dx / n, dy / n
        card(x1 + ux * 0.55 - uy * 0.32 * side, y1 + uy * 0.55 + ux * 0.32 * side, text)

    return entity, attr, rel, conn


def chen_diagram():
    """ER-диаграмма в нотации Чена: 10 сущностей (одна слабая) и 14 связей."""
    K = 0.5
    SH = 3.4         # нижний блок (комментарии, история) сдвинут вниз, освобождая место трудозатратам
    fig, ax = canvas(30.5, 20.6 + SH, k=K)
    AS = 12.5       # кегль атрибутов

    entity, attr, rel, conn = chen_kit(fig, ax, K, AS)

    Z = Box(4.0, 17.6, 4.0, 1.2)
    P = Box(15.2, 14.6, 3.6, 1.2)
    D = Box(25.8, 17.4, 3.6, 1.2)
    S = Box(25.8, 10.6, 3.6, 1.2)
    U = Box(4.6, 9.4, 4.4, 1.2)
    T = Box(15.2, 7.8, 3.6, 1.2)
    M = Box(25.8, 3.6, 3.6, 1.2)
    C = Box(8.6, 4.2 - SH, 4.0, 1.2)
    H = Box(9.9, 1.0 - SH, 5.6, 1.2)
    W = Box(9.6, 4.4, 4.4, 1.2)
    entity(Z, "ЗАКАЗЧИК", "customers")
    entity(P, "ПРОЕКТ", "projects")
    entity(D, "ДОГОВОР", "contracts")
    entity(S, "СПРИНТ", "sprints")
    entity(U, "ПОЛЬЗОВАТЕЛЬ", "users")
    entity(T, "ЗАДАЧА", "tasks")
    entity(M, "МЕТКА", "marks")
    entity(C, "КОММЕНТАРИЙ", "comments")
    entity(H, "ИЗМЕНЕНИЕ СТАТУСА", "task_status_history", weak=True)
    entity(W, "ТРУДОЗАТРАТЫ", "worklogs")

    # --- проект и его окружение
    r = rel(9.0, 17.6, "ЗАКАЗЫВАЕТ", w=3.3)
    conn(Z.right(), (r[0] - 1.65, r[1]), "1")
    conn(P.top(-1.4), (r[0] + 1.65, r[1]), "N", side=-1)

    r = rel(9.9, 14.2, "ВЛАДЕЕТ")
    conn(U.top(1.2), (r[0] - 0.35, r[1] - 0.6), "1", side=-1)
    conn(P.left(0.15), (r[0] + 1.45, r[1]), "N", total=True, side=-1)

    r = rel(9.9, 11.7, "УЧАСТВУЕТ", w=3.3)
    conn(U.right(0.35), (r[0] - 1.65, r[1]), "M")
    conn(P.bottom(-1.3), (r[0] + 1.65, r[1]), "N")
    attr(7.6, 12.85, "role", Box(*r, 0, 0))
    attr(9.9, 10.3, "joined_at", Box(*r, 0, 0))

    r = rel(20.9, 16.9, "ОФОРМЛЕН", w=3.0)
    conn(P.right(0.3), (r[0] - 1.5, r[1]), "1")
    conn(D.left(-0.2), (r[0] + 1.5, r[1]), "1", total=True, side=-1)

    r = rel(20.9, 12.9, "ДЕЛИТСЯ\nНА", w=2.9, h=1.6)
    conn(P.right(-0.3), (r[0] - 1.45, r[1]), "1", side=-1)
    conn(S.top(-0.9), (r[0] + 1.45, r[1]), "N", total=True, side=-1)

    r = rel(15.2, 11.2, "СОДЕРЖИТ", w=3.1)
    conn(P.bottom(), (r[0], r[1] + 0.72), "1")
    conn(T.top(), (r[0], r[1] - 0.72), "N", total=True, side=-1)

    # --- задача
    r = rel(20.9, 9.4, "ВКЛЮЧАЕТ", w=3.1)
    conn(S.left(-0.2), (r[0] + 1.55, r[1]), "1", side=-1)
    conn(T.right(0.25), (r[0] - 1.55, r[1]), "N")

    r = rel(9.9, 7.6, "ИСПОЛНЯЕТ", w=3.2)
    conn(U.right(-0.35), (r[0] - 1.6, r[1]), "1", side=-1)
    conn(T.left(0.0), (r[0] + 1.6, r[1]), "N")

    r = rel(21.6, 4.9, "ПОМЕЧЕНА", w=3.1)
    conn(T.right(-0.5), (r[0] - 1.55, r[1]), "M", side=-1)
    conn(M.left(-0.2), (r[0] + 1.55, r[1]), "N", side=1)
    attr(21.6, 3.3, "date", Box(*r, 0, 0))

    r = rel(4.5, 6.0 - SH, "ПИШЕТ")
    conn(U.bottom(-0.1), (r[0], r[1] + 0.72), "1")
    conn(C.left(0.2), (r[0] + 0.5, r[1] - 0.45), "N", total=True)

    r = rel(12.9, 5.0 - SH, "ОТНОСИТСЯ\nК", w=3.0, h=1.6)
    conn(T.bottom(-1.0), (r[0], r[1] + 0.8), "1", side=1)
    conn(C.right(0.25), (r[0] - 1.5, r[1]), "N", total=True)

    r = rel(2.3, 4.2 - SH, "ИЗМЕНИЛ", w=2.8)
    conn(U.bottom(-1.6), (r[0], r[1] + 0.72), "1", side=-1)
    conn(H.left(0.2), (r[0], r[1] - 0.72), "N")

    r = rel(15.2, 3.4 - SH, "ИМЕЕТ\nИСТОРИЮ", w=3.2, h=1.7, ident=True)
    conn(T.bottom(), (r[0], r[1] + 0.85), "1", side=-1)
    conn(H.right(0.1), (r[0] - 1.6, r[1]), "N", total=True, side=-1)

    # --- атрибуты
    for (x, y, t, k) in [(1.3, 19.4, "customer_id", True), (4.2, 19.7, "name", False),
                         (7.4, 19.4, "contact_name", False), (1.4, 15.9, "email", False)]:
        attr(x, y, t, Z, k)
    for (x, y, t, k) in [(13.1, 17.5, "project_id", True), (14.8, 18.6, "name", False),
                         (16.8, 18.6, "code", False), (18.5, 17.75, "description", False),
                         (11.9, 15.75, "status", False), (18.1, 12.55, "start_date", False),
                         (18.4, 11.45, "end_date", False)]:
        attr(x, y, t, P, k)
    for (x, y, t, k) in [(23.5, 19.5, "number", True), (26.6, 19.6, "signed_on", False),
                         (29.0, 18.4, "amount", False), (28.6, 16.0, "budget_hours", False)]:
        attr(x, y, t, D, k)
    for (x, y, t, k) in [(28.4, 12.7, "sprint_id", True), (29.6, 11.8, "number", False),
                         (29.7, 10.8, "goal", False), (29.5, 9.8, "start_date", False),
                         (29.0, 8.75, "end_date", False), (25.9, 8.35, "capacity_hours", False),
                         (23.1, 8.2, "status", False)]:
        attr(x, y, t, S, k)
    for (x, y, t, k) in [(1.3, 11.5, "user_id", True), (1.1, 10.4, "full_name", False),
                         (1.1, 8.3, "email", False), (1.3, 7.2, "created_at", False)]:
        attr(x, y, t, U, k)
    for (x, y, t, k) in [(12.4, 9.45, "task_id", True), (13.6, 10.35, "title", False),
                         (17.4, 10.25, "status", False), (18.4, 9.05, "priority", False),
                         (11.5, 8.5, "description", False), (19.6, 7.75, "created_at", False),
                         (20.5, 6.7, "due_date", False), (18.6, 4.15, "estimate_hours", False),
                         (18.0, 2.75, "completed_at", False)]:
        attr(x, y, t, T, k)
    for (x, y, t, k) in [(5.9, 2.75 - SH, "comment_id", True), (8.6, 2.75 - SH, "body", False),
                         (11.2, 2.85 - SH, "created_at", False)]:
        attr(x, y, t, C, k)
    for (x, y, t, k, pk) in [(4.9, -0.15 - SH, "changed_at", False, True), (14.5, -0.15 - SH, "new_status", False, False),
                             (9.9, -0.5 - SH, "old_status", False, False)]:
        attr(x, y, t, H, k, partial=pk)
    for (x, y, t, k) in [(29.0, 4.8, "mark_id", True), (29.3, 3.6, "name", False), (28.8, 2.4, "color", False)]:
        attr(x, y, t, M, k)

    # --- трудозатраты: часы сотрудника по задаче за день
    r = rel(6.6, 6.2, "СПИСЫВАЕТ", w=3.2)
    conn(U.bottom(1.6), (r[0], r[1] + 0.72), "1", side=-1)
    conn(W.left(0.1), (r[0], r[1] - 0.72), "N", total=True)
    r = rel(11.7, 6.3, "ПОТРАЧЕНЫ\nНА", w=3.6, h=1.6)
    conn(T.bottom(-1.6), (r[0] + 1.8, r[1]), "1", side=-1)
    conn(W.top(1.9), (r[0], r[1] - 0.8), "N", total=True, side=-1)
    for (x, y, t, k) in [(5.8, 4.2, "worklog_id", True), (7.0, 2.85, "work_date", False),
                         (9.6, 2.6, "hours", False), (11.7, 2.75, "note", False),
                         (9.0, 5.65, "created_at", False)]:
        attr(x, y, t, W, k)

    ax.set_ylim(-1.0 - SH, 20.6)
    save(fig, "chen")


def quality_chen_diagram():
    """ER-диаграмма системы оценивания качества (схема quality): 4 сущности, 4 связи M : N.
    Пунктирные эллипсы — производные атрибуты: вычисляются запросом, а не хранятся."""
    K = 0.42
    fig, ax = canvas(26.6, 11.8, k=K)
    AS = 12.5

    entity, attr, rel, conn = chen_kit(fig, ax, K, AS, cw=0.104)

    I = Box(3.9, 8.0, 3.6, 1.2)
    R = Box(13.4, 8.0, 4.0, 1.2)
    C = Box(22.9, 8.0, 3.6, 1.2)
    G = Box(13.4, 2.4, 3.6, 1.2)
    entity(I, "ИСПЫТАНИЕ", "tests")
    entity(R, "ТРЕБОВАНИЕ", "requirements")
    entity(C, "КРИТЕРИЙ", "criteria")
    entity(G, "ПРОГОН", "runs")

    r = rel(8.55, 8.0, "ПРОВЕРЯЕТ", w=4.2, h=1.5)
    conn(I.right(), (r[0] - 2.1, r[1]), "M")
    conn(R.left(), (r[0] + 2.1, r[1]), "N", side=-1)

    r = rel(18.25, 8.0, "ОЦЕНИВАЕТ", w=4.2, h=1.5)
    conn(R.right(), (r[0] - 2.1, r[1]), "N", side=-1)
    conn(C.left(), (r[0] + 2.1, r[1]), "M")

    r = rel(3.9, 2.4, "ВЫПОЛНЯЕТ", w=3.9, h=1.5)
    conn(G.left(), (r[0] + 1.95, r[1]), "M")
    conn(I.bottom(), (r[0], r[1] + 0.75), "N", side=-1)
    attr(7.5, 4.1, "actual", Box(*r, 0, 0))
    attr(7.3, 0.6, "passed", Box(*r, 0, 0))

    r = rel(22.9, 2.4, "ИЗМЕРЯЕТ", w=3.7, h=1.5)
    conn(G.right(), (r[0] - 1.85, r[1]), "M", side=-1)
    conn(C.bottom(), (r[0], r[1] + 0.75), "N")
    attr(19.4, 4.1, "value", Box(*r, 0, 0))
    attr(26.3, 3.7, "met", Box(*r, 0, 0), derived=True)

    for (x, y, t, k) in [(1.5, 10.0, "test_code", True), (4.2, 10.75, "title", False),
                         (6.9, 10.2, "scenario", False), (1.5, 5.9, "expected", False)]:
        attr(x, y, t, I, k)
    for (x, y, t, k) in [(10.6, 10.0, "req_code", True), (13.4, 10.75, "kind", False),
                         (16.2, 10.0, "title", False)]:
        attr(x, y, t, R, k)
    attr(10.9, 5.9, "covered", R, derived=True)
    attr(15.9, 5.9, "satisfied", R, derived=True)
    for (x, y, t, k) in [(20.2, 10.1, "crit_code", True), (23.4, 10.8, "characteristic", False),
                         (26.1, 9.9, "metric", False), (26.4, 7.9, "unit", False),
                         (25.9, 5.9, "required_value", False), (20.0, 5.9, "direction", False)]:
        attr(x, y, t, C, k)
    for (x, y, t, k) in [(10.2, 0.5, "run_id", True), (11.9, -0.25, "run_at", False),
                         (14.8, -0.25, "environment", False), (17.7, 0.6, "db_version", False)]:
        attr(x, y, t, G, k)
    attr(13.4, 4.3, "accepted", G, derived=True)

    ax.set_xlim(-0.4, 28.0)
    ax.set_ylim(-0.8, 11.4)
    save(fig, "quality_chen")


# --------------------------------------------------------------------------
# 5. BPMN «Выполнение задачи проекта»
# --------------------------------------------------------------------------
def bpmn_diagram():
    import math
    W, H = 30.4, 12.7
    fig, ax = canvas(W, H, k=0.6)
    S = 12

    x0, x1 = 0.1, W - 0.1
    lanes = [("Руководитель\nпроекта", 10.0, 12.6), ("Исполнитель", 7.4, 10.0), ("Тестировщик", 5.0, 7.4),
             ("Система\n(СУБД, сервисы)", 0.1, 5.0)]
    ax.add_patch(Rectangle((x0, 0.1), x1 - x0, 12.5, fc="none", ec=LINE, lw=1.4, zorder=1))
    ax.plot([x0 + 0.6, x0 + 0.6], [0.1, 12.6], color=LINE, lw=1.2)
    ax.text(x0 + 0.3, 6.35, "Выполнение задачи проекта", rotation=90, ha="center", va="center",
            fontsize=S + 1, weight=BOLD)
    for name, lo, hi in lanes:
        ax.plot([x0 + 0.6, x1], [lo, lo], color=LINE, lw=1.1)
        ax.plot([x0 + 1.5, x0 + 1.5], [lo, hi], color=LINE, lw=1.0)
        ax.text(x0 + 1.05, (lo + hi) / 2, name, rotation=90, ha="center", va="center", fontsize=S)
    ax.add_patch(Rectangle((x0 + 1.5, 0.1), x1 - x0 - 1.5, 4.9, fc=PAL["lane"], ec="none", zorder=0))

    def user_icon(x, y):
        ax.add_patch(Circle((x, y + 0.08), 0.07, fc="white", ec=LINE, lw=0.9, zorder=7))
        ax.add_patch(matplotlib.patches.Wedge((x, y - 0.12), 0.14, 0, 180, fc="white", ec=LINE, lw=0.9, zorder=7))

    def gear_icon(x, y):
        for a in range(8):
            ang = a * math.pi / 4
            ax.plot([x + 0.07 * math.cos(ang), x + 0.15 * math.cos(ang)],
                    [y + 0.07 * math.sin(ang), y + 0.15 * math.sin(ang)], color=LINE, lw=1.6, zorder=7)
        ax.add_patch(Circle((x, y), 0.09, fc="white", ec=LINE, lw=0.9, zorder=8))

    def task(x, y, text, kind="user", w=2.1, h=1.3):
        b = Box(x, y, w, h)
        fc = PAL["bpmn_user"] if kind == "user" else PAL["bpmn_service"]
        ax.add_patch(FancyBboxPatch((b.l, b.b), w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                    fc=fc, ec=LINE, lw=1.2, zorder=4))
        (user_icon if kind == "user" else gear_icon)(b.l + 0.25, b.t - 0.25)
        ax.text(x + 0.15, y - 0.08, text, ha="center", va="center", fontsize=S - 1.5, zorder=6, linespacing=1.12)
        return b

    def event(x, y, kind, text, r=0.3, tx=None, ty=None, ha="center"):
        lw = {"start": 1.2, "end": 3.4, "inter": 1.2}[kind]
        ax.add_patch(Circle((x, y), r, fc="white", ec=LINE, lw=lw, zorder=5))
        if kind == "inter":
            ax.add_patch(Circle((x, y), r - 0.07, fc="white", ec=LINE, lw=1.2, ls=(0, (3, 2)), zorder=6))
            ax.add_patch(Circle((x, y), r - 0.14, fc="white", ec=LINE, lw=1.0, zorder=6))
            ax.plot([x, x], [y, y + 0.09], color=LINE, lw=1.0, zorder=7)
            ax.plot([x, x + 0.06], [y, y], color=LINE, lw=1.0, zorder=7)
        if text:
            ax.text(x if tx is None else tx, (y - r - 0.42) if ty is None else ty, text, ha=ha, va="center",
                    fontsize=S - 1.5, zorder=6, style="italic")
        return Box(x, y, 2 * r, 2 * r)

    def gateway(x, y, text, r=0.45, tdy=0.75):
        ax.add_patch(Polygon([(x - r, y), (x, y + r), (x + r, y), (x, y - r)], closed=True,
                             fc="white", ec=LINE, lw=1.2, zorder=5))
        ax.plot([x - 0.15, x + 0.15], [y - 0.15, y + 0.15], color=LINE, lw=2.0, zorder=6)
        ax.plot([x - 0.15, x + 0.15], [y + 0.15, y - 0.15], color=LINE, lw=2.0, zorder=6)
        ax.text(x, y + tdy, text, ha="center", va="center", fontsize=S - 1.5, zorder=6)
        return Box(x, y, 2 * r, 2 * r)

    def store(x, y, text):
        w, h, e = 0.8, 0.75, 0.16
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=4))
        ax.add_patch(Ellipse((x, y - h / 2), w, 2 * e, fc="white", ec=LINE, lw=1.2, zorder=4))
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=5))
        ax.plot([x - w / 2, x - w / 2], [y - h / 2, y + h / 2], color=LINE, lw=1.2, zorder=6)
        ax.plot([x + w / 2, x + w / 2], [y - h / 2, y + h / 2], color=LINE, lw=1.2, zorder=6)
        ax.add_patch(matplotlib.patches.Arc((x, y - h / 2), w, 2 * e, theta1=180, theta2=360, color=LINE, lw=1.2, zorder=6))
        ax.add_patch(Ellipse((x, y + h / 2), w, 2 * e, fc="white", ec=LINE, lw=1.2, zorder=6))
        ax.text(x, y - h / 2 - 0.22, text, ha="center", va="top", fontsize=S - 2.5, zorder=6, linespacing=1.05)
        return Box(x, y, w, h)

    def doc(x, y, text):
        w, h, c = 0.62, 0.8, 0.2
        ax.add_patch(Polygon([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2 - c),
                              (x + w / 2 - c, y + h / 2), (x - w / 2, y + h / 2)], closed=True,
                             fc="white", ec=LINE, lw=1.2, zorder=5))
        ax.plot([x + w / 2 - c, x + w / 2 - c, x + w / 2], [y + h / 2, y + h / 2 - c, y + h / 2 - c],
                color=LINE, lw=1.0, zorder=6)
        for k in range(3):
            ax.plot([x - w / 2 + 0.1, x + w / 2 - 0.12], [y + 0.12 - k * 0.15] * 2, color=GREY, lw=0.7, zorder=6)
        ax.text(x, y - h / 2 - 0.45, text, ha="center", va="center", fontsize=S - 2.5, zorder=6)
        return Box(x, y, w, h)

    def assoc(a, b):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=LINE, lw=1.0, ls=(0, (2, 2)), zorder=3)

    def seq(pts, text=None, at=None):
        arrow(ax, pts, text, at, size=S - 1.5, lw=1.2, head=13)

    yR, yE, yT, yS, yD = 11.3, 8.7, 6.2, 3.65, 1.25
    c = [2.45, 4.6, 7.0, 9.4, 11.8, 14.4, 17.0, 19.4, 22.0, 24.4]

    st = event(c[0], yR, "start", "Потребность\nв работе", ty=yR + 0.75)
    r1 = task(c[1], yR, "Создать\nзадачу")
    s1 = task(c[1], yS, "4.1 Записать\nзадачу [todo]", "service")
    g1 = gateway(c[2], yR, "Задача\nактуальна?")
    s7 = task(c[2], yS, "4.4 Удалить\nзадачу", "service", w=1.95)
    r2 = task(c[3], yR, "Оценить,\nназначить,\nвключить\nв спринт", h=1.55)
    s2 = task(c[3], yS, "4.10, 4.2, 4.13\nОценка, испол-\nнитель, ёмкость", "service", w=2.4, h=1.45)
    e1 = task(c[4], yE, "Взять\nв работу")
    s3 = task(c[4], yS, "4.3 Статус\nin_progress", "service")
    e2 = task(c[5], yE, "Выполнить\nработу, обсуж-\nдать, коммиты\nSHOP-42", w=2.4, h=1.55)
    e3 = task(c[6], yE, "Передать\nна проверку")
    s4 = task(c[6], yS, "4.3 Статус\nreview,\nуведомить", "service")
    t1 = task(c[7], yT, "Проверить\nрезультат")
    g2 = gateway(c[8], yT, "Принято?")
    s5 = task(c[8], yS, "5.1 Записать\nзамечания", "service")
    s6 = task(c[9], yS, "4.3 done +\ncompleted_at", "service", w=2.2)
    r3 = task(c[5], yR, "Эскалация:\nповысить\nприоритет")

    en1 = event(26.25, yS, "end", "Задача\nвыполнена\n(done)", ty=yS - 1.15)
    en2 = event(c[2], 1.55, "end", "Задача\nотменена", ty=0.65)
    s8 = task(28.6, yS, "4.11 Повысить\nприоритет", "service", w=2.2)
    en3 = event(28.0, yD, "end", "Приоритет\nповышен", ty=yD - 0.85)

    # поток управления
    seq([st.right(), r1.left()])
    seq([r1.bottom(), s1.top()])
    seq([s1.right(), (5.85, yS), (5.85, yR), g1.left()])
    seq([g1.right(), r2.left()], "да", at=(8.05, yR + 0.3))
    seq([g1.bottom(), s7.top()], "нет", at=(c[2] + 0.35, 9.1))
    seq([s7.bottom(), en2.top()])
    seq([r2.bottom(), s2.top()])
    seq([s2.right(), (10.6, yS), (10.6, yE), e1.left()])
    seq([e1.bottom(), s3.top()])
    seq([s3.right(), (13.0, yS), (13.0, yE), e2.left()])
    seq([e2.right(), e3.left()])
    seq([e3.bottom(), s4.top()])
    seq([s4.right(), (18.25, yS), (18.25, yT), t1.left()])
    seq([t1.right(), g2.left()])
    seq([g2.right(), (s6.x, yT), s6.top()], "да", at=(22.6, yT + 0.3))
    seq([g2.bottom(), s5.top()], "нет", at=(c[8] + 0.35, 5.2))
    seq([s5.left(), (20.8, yS), (20.8, 7.15), (15.3, 7.15), (15.3, e2.b)])
    seq([s6.right(), en1.left()])

    # граничный таймер: срок прошёл (непрерывающий)
    tm = event(e2.x - 0.55, e2.t, "inter", None, r=0.28)
    ax.text(tm.x - 0.38, e2.t + 0.22, "срок прошёл", ha="right", va="center", fontsize=S - 1.5, style="italic")
    seq([tm.top(), (tm.x, r3.b)])

    # граничное событие ошибки: ёмкость спринта превышена (PM004) — вернуть руководителю
    er = event(s2.r - 0.35, s2.t, "inter", None, r=0.26)
    ax.plot([er.x - 0.1, er.x - 0.02, er.x + 0.03, er.x + 0.12], [er.y - 0.13, er.y + 0.08, er.y - 0.04, er.y + 0.14],
            color=LINE, lw=1.3, zorder=7)
    ax.text(er.x - 0.3, er.t + 0.75, "ёмкость\nпревышена", ha="right", va="center", fontsize=S - 1.5, style="italic")
    seq([er.top(), (er.x, r2.b)])
    seq([r3.right(), (s8.x, yR), s8.top()])
    seq([s8.bottom(-0.6), en3.top()])

    # хранилища данных и электронные документы
    # стрелка к хранилищу — запись, от хранилища — чтение
    for t, both in ((s1, False), (s3, False), (s4, False), (s6, False)):
        d = store(t.x, yD, "D7\nЗадачи")
        data_assoc(ax, t.bottom(), (d.x, d.t + 0.17), both=both)
    d = store(s2.x - 0.6, yD, "D7\nЗадачи")
    data_assoc(ax, s2.bottom(-0.6), (d.x, d.t + 0.17), both=True)
    d = store(s2.x + 0.6, yD, "D6\nСпринты")
    data_assoc(ax, (d.x, d.t + 0.17), s2.bottom(0.6))
    d = store(s8.x + 0.7, yD, "D7\nЗадачи")
    data_assoc(ax, s8.bottom(0.7), (d.x, d.t + 0.17))
    d12 = store(s5.x, yD, "D12\nКомментарии")
    data_assoc(ax, s5.bottom(), (d12.x, d12.t + 0.17))
    for t, x, txt in ((s1, c[1] + 1.05, "Карточка\nзадачи"), (s4, c[6] + 1.4, "Уведомление\nтестировщику")):
        dd = doc(x, yD + 0.05, txt)
        data_assoc(ax, t.right(-0.45), (dd.x - 0.1, dd.t))

    save(fig, "bpmn")


def bpmn_overview_diagram():
    """Обзорная BPMN «Ведение проекта»: верхний уровень, задача — свёрнутый подпроцесс."""
    W, H = 28.6, 13.8
    fig, ax = canvas(W, H, k=0.6)
    S = 12
    x0, x1 = 0.1, W - 0.1

    # ---- пул заказчика (свёрнутый, «чёрный ящик»)
    cust = (12.95, 13.7)
    ax.add_patch(Rectangle((x0, cust[0]), x1 - x0, cust[1] - cust[0], fc="white", ec=LINE, lw=1.4, zorder=1))
    ax.text(W / 2, sum(cust) / 2, "Заказчик", ha="center", va="center", fontsize=S + 1)

    # ---- основной пул и дорожки
    top = 12.65
    lanes = [("Руководитель\nпроекта", 9.8, top), ("Админи-\nстратор", 8.1, 9.8),
             ("Команда\nпроекта", 5.6, 8.1), ("Система\n(СУБД, сервисы)", 0.1, 5.6)]
    ax.add_patch(Rectangle((x0, 0.1), x1 - x0, top - 0.1, fc="none", ec=LINE, lw=1.4, zorder=1))
    ax.plot([x0 + 0.6, x0 + 0.6], [0.1, top], color=LINE, lw=1.2)
    ax.text(x0 + 0.3, top / 2, "Ведение проекта", rotation=90, ha="center", va="center", fontsize=S + 1)
    for name, lo, hi in lanes:
        ax.plot([x0 + 0.6, x1], [lo, lo], color=LINE, lw=1.1)
        ax.plot([x0 + 1.5, x0 + 1.5], [lo, hi], color=LINE, lw=1.0)
        ax.text(x0 + 1.05, (lo + hi) / 2, name, rotation=90, ha="center", va="center", fontsize=S)
    ax.add_patch(Rectangle((x0 + 1.5, 0.1), x1 - x0 - 1.5, 5.5, fc=PAL["lane"], ec="none", zorder=0))

    def user_icon(x, y):
        ax.add_patch(Circle((x, y + 0.08), 0.07, fc="white", ec=LINE, lw=0.9, zorder=7))
        ax.add_patch(matplotlib.patches.Wedge((x, y - 0.12), 0.14, 0, 180, fc="white", ec=LINE, lw=0.9, zorder=7))

    def gear_icon(x, y):
        for a in range(8):
            ang = a * math.pi / 4
            ax.plot([x + 0.07 * math.cos(ang), x + 0.15 * math.cos(ang)],
                    [y + 0.07 * math.sin(ang), y + 0.15 * math.sin(ang)], color=LINE, lw=1.6, zorder=7)
        ax.add_patch(Circle((x, y), 0.09, fc="white", ec=LINE, lw=0.9, zorder=8))

    def task(x, y, text, kind="user", w=2.2, h=1.35, size=S - 1.5):
        b = Box(x, y, w, h)
        fc = {"user": PAL["bpmn_user"], "service": PAL["bpmn_service"], "sub": "white"}[kind]
        ax.add_patch(FancyBboxPatch((b.l, b.b), w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                    fc=fc, ec=LINE, lw=1.2, zorder=4))
        if kind == "user":
            user_icon(b.l + 0.25, b.t - 0.25)
        elif kind == "service":
            gear_icon(b.l + 0.25, b.t - 0.25)
        dx = 0.15 if kind != "sub" else 0
        dy = -0.08 if kind != "sub" else 0.15
        ax.text(x + dx, y + dy, text, ha="center", va="center", fontsize=size, zorder=6, linespacing=1.12)
        return b

    def subprocess(x, y, text, w=2.9, h=1.75):
        """Свёрнутый подпроцесс: маркер «+» и маркер параллельного множественного экземпляра."""
        b = task(x, y, text, "sub", w, h)
        m = 0.26
        ax.add_patch(Rectangle((x - m / 2 - 0.2, b.b + 0.05), m, m, fc="white", ec=LINE, lw=1.0, zorder=6))
        ax.plot([x - 0.2 - 0.08, x - 0.2 + 0.08], [b.b + 0.05 + m / 2] * 2, color=LINE, lw=1.1, zorder=7)
        ax.plot([x - 0.2, x - 0.2], [b.b + 0.05 + m / 2 - 0.08, b.b + 0.05 + m / 2 + 0.08], color=LINE, lw=1.1, zorder=7)
        for k in range(3):
            xx = x + 0.12 + k * 0.08
            ax.plot([xx, xx], [b.b + 0.07, b.b + 0.29], color=LINE, lw=1.3, zorder=7)
        return b

    def event(x, y, kind, text, r=0.3, tx=None, ty=None, ha="center", marker=None, dashed=False):
        lw = {"start": 1.2, "end": 3.4, "inter": 1.2}[kind]
        ax.add_patch(Circle((x, y), r, fc="white", ec=LINE, lw=lw, zorder=5, ls=(0, (3, 2)) if dashed else "-"))
        if marker == "msg":
            w, h = r * 1.0, r * 0.66
            fc = LINE if kind == "end" else "white"
            ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec=LINE, lw=1.0, zorder=6))
            ax.plot([x - w / 2, x, x + w / 2], [y + h / 2, y, y + h / 2], color="white" if kind == "end" else LINE,
                    lw=1.0, zorder=7)
        if marker == "timer":
            ax.add_patch(Circle((x, y), r - 0.08, fc="white", ec=LINE, lw=1.0, zorder=6))
            ax.plot([x, x], [y, y + 0.1], color=LINE, lw=1.0, zorder=7)
            ax.plot([x, x + 0.07], [y, y], color=LINE, lw=1.0, zorder=7)
        if text:
            ax.text(x if tx is None else tx, (y - r - 0.42) if ty is None else ty, text, ha=ha, va="center",
                    fontsize=S - 1.5, zorder=6, style="italic")
        return Box(x, y, 2 * r, 2 * r)

    def gateway(x, y, text, r=0.45, tdy=0.8, mark=True):
        ax.add_patch(Polygon([(x - r, y), (x, y + r), (x + r, y), (x, y - r)], closed=True,
                             fc="white", ec=LINE, lw=1.2, zorder=5))
        if mark:
            ax.plot([x - 0.15, x + 0.15], [y - 0.15, y + 0.15], color=LINE, lw=2.0, zorder=6)
            ax.plot([x - 0.15, x + 0.15], [y + 0.15, y - 0.15], color=LINE, lw=2.0, zorder=6)
        if text:
            ax.text(x, y + tdy, text, ha="center", va="center", fontsize=S - 1.5, zorder=6)
        return Box(x, y, 2 * r, 2 * r)

    def store(x, y, text):
        w, h, e = 0.8, 0.75, 0.16
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=4))
        ax.add_patch(Ellipse((x, y - h / 2), w, 2 * e, fc="white", ec=LINE, lw=1.2, zorder=4))
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=5))
        ax.plot([x - w / 2, x - w / 2], [y - h / 2, y + h / 2], color=LINE, lw=1.2, zorder=6)
        ax.plot([x + w / 2, x + w / 2], [y - h / 2, y + h / 2], color=LINE, lw=1.2, zorder=6)
        ax.add_patch(matplotlib.patches.Arc((x, y - h / 2), w, 2 * e, theta1=180, theta2=360, color=LINE, lw=1.2,
                                            zorder=6))
        ax.add_patch(Ellipse((x, y + h / 2), w, 2 * e, fc="white", ec=LINE, lw=1.2, zorder=6))
        ax.text(x, y - h / 2 - 0.22, text, ha="center", va="top", fontsize=S - 2.5, zorder=6, linespacing=1.05)
        return Box(x, y, w, h)

    def assoc(a, b):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=LINE, lw=1.0, ls=(0, (2, 2)), zorder=3)

    def seq(pts, text=None, at=None):
        arrow(ax, pts, text, at, size=S - 1.5, lw=1.2, head=13)

    def msg(a, b, text=None, tx=None, ty=None):
        """Поток сообщений: пунктир, кружок в начале, полая стрелка в конце (только вертикальный)."""
        (xa, ya), (xb, yb) = a, b
        sgn = 1 if yb > ya else -1
        hl, hw = 0.3, 0.14
        ax.plot([xa, xb], [ya, yb - sgn * hl], color=LINE, lw=1.1, ls=(0, (5, 3)), zorder=3)
        ax.add_patch(Circle((xa, ya + sgn * 0.08), 0.08, fc="white", ec=LINE, lw=1.0, zorder=6))
        ax.add_patch(Polygon([(xb, yb), (xb - hw, yb - sgn * hl), (xb + hw, yb - sgn * hl)], closed=True,
                             fc="white", ec=LINE, lw=1.0, zorder=6))
        if text:
            ax.text(xa + 0.15 if tx is None else tx, (ya + yb) / 2 if ty is None else ty, text, ha="left",
                    va="center", fontsize=S - 1.5, style="italic", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))


    yR, yA, yT, yS, yD = 11.15, 8.95, 6.85, 4.15, 1.55
    c = [2.4, 4.5, 7.0, 8.7, 10.8, 13.9, 16.8, 19.4, 22.0, 23.9, 26.1, 27.85]

    # ---- главный поток
    st = event(c[0], yR, "start", "Решение\nо проекте", marker="msg", ty=yR - 0.95)
    r1 = task(c[1], yR, "Создать проект,\nзаказчика\nи договор", h=1.5)
    s1 = task(c[1], yS, "2.1, 2.5, 2.6\nСоздать проект\nс договором", "service", h=1.5)
    g1 = gateway(c[2], yR, "Сотрудники\nзарегистри-\nрованы?", tdy=1.05)
    a1 = task(c[2], yA, "Зарегистри-\nровать\nсотрудника", w=1.9, h=1.4)
    s2 = task(c[2], yS, "1.1 Записать\nпользователя", "service", w=2.0)
    g2 = gateway(c[3], yR, None, mark=True)
    r2 = task(c[4], yR, "Сформировать\nкоманду, загру-\nзить бэклог", h=1.5)
    s3 = task(c[4], yS, "3.1, 3.2, 4.8\nУчастники, роли,\nimport_tasks", "service", h=1.5)
    r3 = task(c[5], yR, "Запланировать\nспринт")
    s4 = task(c[5], yS, "4.6 Создать\nспринт", "service")
    sp = subprocess(c[6], yT, "Выполнение\nзадачи проекта\n(рисунок В.5)")
    s5 = task(c[7], yS, "4.7 Закрыть\nспринт, пере-\nнести задачи", "service", h=1.5)
    s6 = task(c[8], yS, "6.3, 6.5 Отчёты\nо рисках\nи договорах", "service", h=1.5)
    r4 = task(c[8], yR, "Оценить\nриски и бюджет")
    g3 = gateway(c[9], yR, "Работы\nостались?", tdy=-0.85)
    r5 = task(c[10], yR, "Закрыть\nпроект", w=1.9)
    s7 = task(c[10], yS, "2.3, 6.4 Статус,\nотчёт заказчику", "service", w=2.3)
    en = event(c[11], yS, "end", "Проект\nзавершён", marker="msg", ty=yS - 0.95)

    seq([st.right(), r1.left()])
    seq([r1.bottom(), s1.top()])
    seq([s1.right(), (5.85, yS), (5.85, yR), g1.left()])
    seq([g1.right(), g2.left()], "да", at=(7.85, yR + 0.3))
    seq([g1.bottom(), a1.top()], "нет", at=(c[2] + 0.35, 9.95))
    seq([a1.bottom(), s2.top()])
    seq([s2.right(), (c[3], yS), g2.bottom()])
    seq([g2.right(), r2.left()])
    seq([r2.bottom(), s3.top()])
    seq([s3.right(), (12.35, yS), (12.35, yR), r3.left()])
    seq([r3.bottom(), s4.top()])
    seq([s4.right(), (15.0, yS), (15.0, yT), sp.left()])
    seq([sp.right(), (s5.x, yT), s5.top()])
    seq([s5.right(), s6.left()])
    seq([s6.top(), r4.bottom()])
    seq([r4.right(), g3.left()])
    seq([g3.top(), (c[9], 12.35), (c[5], 12.35), r3.top()], "да", at=(18.2, 12.35))
    seq([g3.right(), r5.left()], "нет", at=(24.75, yR + 0.3))
    seq([r5.bottom(), s7.top()])
    seq([s7.right(), en.left()])

    # ---- потоки сообщений с заказчиком
    msg((c[0], cust[0]), st.top(), "договор", ty=12.35)
    msg((r2.x, cust[0]), r2.top(), "бэклог (CSV)", ty=12.35)
    msg(en.top(), (en.x, cust[0]), "отчёт", tx=en.x - 0.95, ty=10.0)

    # ---- хранилища
    for t, sid in ((s2, "D1\nПользователи"), (s4, "D6\nСпринты")):
        d = store(t.x, yD, sid)
        data_assoc(ax, t.bottom(), (d.x, d.t + 0.17))
    for t, na, nb, both in ((s1, "D3\nПроекты", "D4\nДоговоры", False), (s3, "D5\nУчастники", "D7\nЗадачи", False),
                            (s5, "D6\nСпринты", "D7\nЗадачи", True)):
        da = store(t.x - 0.75, yD, na)
        db = store(t.x + 0.75, yD, nb)
        data_assoc(ax, t.bottom(-0.4), (da.x, da.t + 0.17), both=both)
        data_assoc(ax, t.bottom(0.4), (db.x, db.t + 0.17), both=both)

    # ---- событийный подпроцесс: регламентные операции планировщика
    ex = Box(24.5, 1.45, 7.7, 2.35)
    ax.add_patch(FancyBboxPatch((ex.l, ex.b), ex.w, ex.h, boxstyle="round,pad=0,rounding_size=0.25",
                                fc="none", ec=LINE, lw=1.1, ls=(0, (2, 2)), zorder=3))
    ax.text(ex.l + 0.2, ex.t - 0.25, "Регламентные операции", ha="left", va="center", fontsize=S - 1.5,
            style="italic")
    te = event(21.2, 1.25, "start", "ежедневно", r=0.3, marker="timer", dashed=True, ty=0.55)
    q1 = task(23.1, 1.25, "6.2 Обновить\nсводку", "service", w=2.0, h=1.15)
    q2 = task(25.6, 1.25, "6.1, 6.3 Про-\nсрочки, рассылка", "service", w=2.3, h=1.15)
    qe = event(27.65, 1.25, "end", None, r=0.27)
    seq([te.right(), q1.left()])
    seq([q1.right(), q2.left()])
    seq([q2.right(), qe.left()])

    save(fig, "bpmn_all")


# --------------------------------------------------------------------------
# 6. Логическая модель данных
# --------------------------------------------------------------------------
def logical_diagram():
    """Логическая модель: 12 таблиц, внешние ключи с правилами ON DELETE."""
    W, H = 23.4, 14.2
    fig, ax = canvas(W, H, k=0.62)
    S = 12
    RH, HH, TW = 0.42, 0.55, 3.4

    T = {}

    def table(name, x, top, rows):
        h = HH + RH * len(rows)
        ax.add_patch(Rectangle((x, top - h), TW, h, fc="white", ec=LINE, lw=1.2, zorder=3))
        ax.add_patch(Rectangle((x, top - HH), TW, HH, fc=FILL_ENT, ec=LINE, lw=1.2, zorder=3))
        ax.text(x + TW / 2, top - HH / 2, name, ha="center", va="center", fontsize=S + 0.5, weight=BOLD, zorder=5)
        ax.plot([x + 0.9, x + 0.9], [top - h, top - HH], color=LINE, lw=0.8, zorder=4)
        rowy = {}
        for i, (k, a) in enumerate(rows):
            y = top - HH - RH * (i + 0.5)
            rowy[a] = y
            ax.text(x + 0.45, y, k, ha="center", va="center", fontsize=S - 2.5, zorder=5,
                    color=PAL["pk"] if "PK" in k else PAL["fk"])
            ax.text(x + 1.02, y, a, ha="left", va="center", fontsize=S - 0.5, zorder=5)
            if i:
                ax.plot([x, x + TW], [y + RH / 2, y + RH / 2], color="#bbbbbb", lw=0.5, zorder=4)
        bx = Box(x + TW / 2, top - h / 2, TW, h)
        bx.row = rowy
        T[name] = bx

    c1, c2, c3, c4, c5 = 0.3, 5.0, 9.7, 14.4, 19.1
    top1, top2 = 13.6, 7.15
    table("users", c1, top1, [("PK", "user_id"), ("", "full_name"), ("U", "email"), ("", "created_at")])
    table("project_members", c2, top1, [("PK, FK", "project_id"), ("PK, FK", "user_id"),
                                        ("", "role"), ("", "joined_at")])
    table("projects", c3, top1, [("PK", "project_id"), ("U", "name"), ("U", "code"), ("", "description"),
                                 ("FK", "owner_id"), ("FK", "customer_id"), ("", "status"), ("", "start_date"),
                                 ("", "end_date")])
    table("customers", c4, top1, [("PK", "customer_id"), ("U", "name"), ("", "contact_name"), ("", "email")])
    table("contracts", c4, 10.85, [("PK, FK", "project_id"), ("FK", "customer_id"), ("U", "number"),
                                   ("", "signed_on"), ("", "amount"), ("", "budget_hours")])
    table("comments", c1, top2, [("PK", "comment_id"), ("FK", "task_id"), ("FK", "author_id"),
                                 ("", "body"), ("", "created_at")])
    table("task_status_history", c2, top2, [("PK", "history_id"), ("FK", "task_id"), ("", "old_status"),
                                            ("", "new_status"), ("", "changed_at"), ("FK", "changed_by")])
    table("tasks", c3, top2, [("PK", "task_id"), ("FK, U", "project_id"), ("FK", "assignee_id"),
                              ("FK", "sprint_id"), ("U", "title"), ("", "description"), ("", "status"),
                              ("", "priority"), ("", "created_at"), ("", "due_date"), ("", "estimate_hours"),
                              ("", "completed_at")])
    table("sprints", c4, top2, [("PK", "sprint_id"), ("FK, U", "project_id"), ("U", "number"), ("", "goal"),
                                ("", "start_date"), ("", "end_date"), ("", "capacity_hours"), ("", "status")])
    table("marks", c5, 6.2, [("PK", "mark_id"), ("U", "name"), ("", "color")])
    table("marks_tasks", c5, 3.55, [("PK, FK", "mark_id"), ("PK, FK", "task_id"), ("", "date")])
    table("worklogs", c1, 4.05, [("PK", "worklog_id"), ("FK, U", "task_id"), ("FK, U", "user_id"),
                                 ("U", "work_date"), ("", "hours"), ("", "note"), ("", "created_at")])

    def card(x, y, t):
        ax.text(x, y, t, fontsize=S, weight=BOLD, color=PAL["card"], ha="center", va="center", zorder=6)

    def rule(x, y, t):
        ax.text(x, y, t, fontsize=S - 2.5, color=GREY, ha="center", va="center", zorder=6, style="italic",
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))

    def rel(pts, one, many, rule_xy, text, one_text="1", many_text="N"):
        polyline(ax, pts, lw=1.1)
        card(*one, one_text)
        card(*many, many_text)
        rule(*rule_xy, text)

    U, PM, P, CU, CT = T["users"], T["project_members"], T["projects"], T["customers"], T["contracts"]
    C, HS, TK, SP, MK, MT = T["comments"], T["task_status_history"], T["tasks"], T["sprints"], T["marks"], T["marks_tasks"]

    # project_members → users, projects
    y = PM.row["user_id"]
    rel([(PM.l, y), (U.r, y)], (U.r + 0.2, y + 0.22), (PM.l - 0.2, y + 0.22), ((U.r + PM.l) / 2, y - 0.3), "CASCADE")
    y = PM.row["project_id"]
    rel([(PM.r, y), (P.l, y)], (P.l - 0.2, y + 0.22), (PM.r + 0.2, y + 0.22), ((PM.r + P.l) / 2, y - 0.3), "CASCADE")
    # projects.owner_id → users: поверх таблиц
    yt = top1 + 0.3
    rel([(P.x + 0.9, P.t), (P.x + 0.9, yt), (U.x, yt), (U.x, U.t)], (U.x + 0.2, U.t + 0.12),
        (P.x + 1.1, P.t + 0.12), (7.0, yt), "RESTRICT")
    # projects.customer_id → customers
    y = P.row["customer_id"]
    rel([(P.r, y), (13.75, y), (13.75, CU.y), (CU.l, CU.y)], (CU.l - 0.2, CU.y + 0.22),
        (P.r + 0.2, y + 0.22), (13.75, (y + CU.y) / 2), "RESTRICT")
    # contracts (project_id, customer_id) → projects: 1 : 1
    y = P.row["start_date"]
    rel([(CT.l, y), (P.r, y)], (P.r + 0.2, y + 0.22), (CT.l - 0.2, y + 0.22), ((P.r + CT.l) / 2 + 0.25, y - 0.22),
        "RESTRICT", many_text="1")
    # sprints.project_id → projects
    y = P.row["end_date"]
    ys = SP.row["project_id"]
    rel([(SP.l + 0.45, SP.t), (SP.l + 0.45, 7.47), (13.45, 7.47), (13.45, y), (P.r, y)],
        (P.r + 0.2, y - 0.24), (SP.l + 0.65, SP.t + 0.2), (13.45, 8.0), "CASCADE")
    # tasks.project_id → projects
    rel([(TK.x, TK.t), (TK.x, P.b)], (TK.x + 0.2, P.b - 0.2), (TK.x + 0.2, TK.t + 0.2),
        (TK.x, (TK.t + P.b) / 2), "CASCADE")
    # tasks (sprint_id, project_id) → sprints
    y = TK.row["sprint_id"]
    rel([(TK.r, y), (SP.l, y)], (SP.l - 0.2, y + 0.22), (TK.r + 0.2, y + 0.22), ((TK.r + SP.l) / 2, y - 0.3),
        "SET NULL")
    # tasks (project_id, assignee_id) → project_members
    y = TK.row["assignee_id"]
    rel([(TK.l + 0.5, TK.t), (TK.l + 0.5, 8.9), (7.6, 8.9), (7.6, PM.b)], (7.8, PM.b - 0.2), (TK.l + 0.7, TK.t + 0.2),
        (8.65, 8.9), "SET NULL")
    # comments → users, tasks
    rel([(U.x, C.t), (U.x, U.b)], (U.x + 0.2, U.b - 0.2), (U.x + 0.2, C.t + 0.2), (U.x, (C.t + U.b) / 2), "RESTRICT")
    yc = 3.75
    rel([(C.r, C.row["task_id"]), (4.15, C.row["task_id"]), (4.15, yc), (TK.l, yc)], (TK.l - 0.2, yc + 0.22),
        (C.r + 0.2, C.row["task_id"] + 0.22), (6.7, yc), "CASCADE")
    # history → tasks, users
    y = HS.row["task_id"]
    rel([(HS.r, y), (TK.l, y)], (TK.l - 0.2, y + 0.22), (HS.r + 0.2, y + 0.22), ((HS.r + TK.l) / 2, y - 0.3), "CASCADE")
    y = HS.row["changed_by"]
    rel([(HS.l, y), (4.65, y), (4.65, U.row["created_at"]), (U.r, U.row["created_at"])],
        (U.r + 0.2, U.row["created_at"] - 0.25), (HS.l - 0.2, y + 0.22), (4.65, 9.3), "SET NULL")
    # marks_tasks → tasks, marks
    y = MT.row["task_id"]
    rel([(MT.l, y), (TK.r, y)], (TK.r + 0.2, y + 0.22), (MT.l - 0.2, y + 0.22), (16.1, y - 0.3), "CASCADE")
    rel([(MT.x, MT.t), (MT.x, MK.b)], (MT.x + 0.2, MK.b - 0.2), (MT.x + 0.2, MT.t + 0.2),
        (MT.x, (MT.t + MK.b) / 2), "RESTRICT")
    # worklogs → tasks, users
    WL = T["worklogs"]
    y = WL.row["task_id"]
    rel([(WL.r, y), (TK.l, y)], (TK.l - 0.2, y + 0.22), (WL.r + 0.2, y + 0.22), (6.7, y - 0.3), "CASCADE")
    y = WL.row["user_id"]
    yu = U.row["user_id"]
    rel([(WL.l, y), (0.0, y), (0.0, yu), (U.l, yu)], (U.l - 0.15, yu + 0.25), (WL.l - 0.15, y + 0.25),
        (0.0, 8.2), "RESTRICT")

    lx, ly, lw_ = c5, top1, 4.0
    ax.add_patch(Rectangle((lx, ly - 4.1), lw_, 4.1, fc="white", ec="#888888", lw=1, zorder=1))
    items = [("PK", "первичный ключ", PAL["pk"]), ("FK", "внешний ключ", PAL["fk"]),
             ("U", "входит в UNIQUE", PAL["fk"])]
    for i, (k, t, col) in enumerate(items):
        ax.text(lx + 0.4, ly - 0.4 - i * 0.5, k, fontsize=S - 2, color=col, ha="center", va="center")
        ax.text(lx + 0.85, ly - 0.4 - i * 0.5, t, fontsize=S - 1, va="center")
    ax.text(lx + 0.2, ly - 1.95, "1, N — кардинальность", fontsize=S - 1, va="center")
    ax.text(lx + 0.2, ly - 2.45, "курсив — правило ON DELETE", fontsize=S - 1, va="center", style="italic")
    ax.text(lx + 0.2, ly - 3.05, "составные FK: tasks → sprints,", fontsize=S - 1.5, va="center")
    ax.text(lx + 0.2, ly - 3.5, "tasks → project_members,", fontsize=S - 1.5, va="center")
    ax.text(lx + 0.2, ly - 3.95, "contracts → projects", fontsize=S - 1.5, va="center")

    ax.set_xlim(-0.45, W)
    ax.set_ylim(0.4, H)
    save(fig, "logical")


# --------------------------------------------------------------------------
# 7. Архитектура ПО
# --------------------------------------------------------------------------
def arch_diagram():
    """Представление контейнеров в нотации C4 (уровень 2): пользователи, контейнеры системы
    с технологиями, внешние системы; на стрелках — действие и протокол."""
    W, H = 20.0, 15.4
    fig, ax = canvas(W, H, k=0.45, shadow=0.03)
    T, D = 12.5, 10                       # кегль названий и описаний
    C_PERSON, C_CONT, C_EXT = "#08427b", "#438dd5", "#8a8a8a"

    def block(x, y, name, kind, desc):
        n = 1 + kind.count("\n") + 1 + (desc.count("\n") + 1 if desc else 0)
        step = 0.36
        y0 = y + (n - 1) * step / 2
        ax.text(x, y0, name, ha="center", va="center", fontsize=T, color="white", zorder=6)
        y0 -= step * 1.1
        for t in kind.split("\n"):
            ax.text(x, y0, t, ha="center", va="center", fontsize=D - 1, color="white", zorder=6)
            y0 -= step
        if desc:
            for t in desc.split("\n"):
                ax.text(x, y0, t, ha="center", va="center", fontsize=D, color="white", zorder=6)
                y0 -= step

    def person(x, y, name, desc, w=4.2):
        body = Box(x, y - 0.25, w, 1.7)
        ax.add_patch(FancyBboxPatch((body.l, body.b), body.w, body.h, boxstyle="round,pad=0,rounding_size=0.4",
                                    fc=C_PERSON, ec="#073b6f", lw=1.0, zorder=4))
        ax.add_patch(Circle((x, body.t + 0.3), 0.48, fc=C_PERSON, ec="#073b6f", lw=1.0, zorder=5))
        block(x, body.y - 0.05, name, "[Person]", desc)
        return body

    def cont(b, name, kind, desc, fc=C_CONT):
        ax.add_patch(FancyBboxPatch((b.l, b.b), b.w, b.h, boxstyle="round,pad=0,rounding_size=0.22",
                                    fc=fc, ec="#2e6295" if fc == C_CONT else "#6b6b6b", lw=1.0, zorder=4))
        block(b.x, b.y, name, kind, desc)
        return b

    def rel(pts, text, at):
        arrow(ax, pts, lw=1.1, head=12, color="#444444")
        ax.text(at[0], at[1], text, ha="center", va="center", fontsize=D, zorder=7, color="#222222",
                linespacing=1.1, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))

    # пользователи
    adb = person(2.4, 13.9, "Администратор БД", "миграции, развёртывание")
    lead = person(7.2, 13.9, "Руководитель", "проекты, спринты, отчёты")
    mem = person(12.0, 13.9, "Участник проекта", "задачи, часы, обсуждение")
    adm = person(16.8, 13.9, "Администратор", "учётные записи")

    # граница системы
    sb = Box(7.75, 6.3, 13.7, 12.0)
    ax.add_patch(FancyBboxPatch((sb.l, sb.b), sb.w, sb.h, boxstyle="round,pad=0,rounding_size=0.3",
                                fc="none", ec="#777777", lw=1.2, ls=(0, (6, 4)), zorder=1))
    ax.text(sb.l + 0.3, sb.b + 0.62, "Система управления проектами", fontsize=T, va="center", color="#333333")
    ax.text(sb.l + 0.3, sb.b + 0.25, "[Software System]", fontsize=D - 1, va="center", color="#555555")

    # контейнеры
    ui = cont(Box(9.0, 10.3, 7.6, 1.7), "Веб-интерфейс", "[Container: Python, Streamlit]",
              "формы задач, спринтов и отчётов")
    api = cont(Box(5.3, 6.7, 7.2, 2.5), "Прикладной сервер (REST API)",
               "[Container: Python 3.12, FastAPI,\nPydantic, psycopg 3]",
               "вход через SSO, права, вызов функций БД;\nOpenAPI (Swagger)")
    integ = cont(Box(12.0, 6.7, 4.4, 2.5), "Модуль интеграции", "[Container: Python,\nFastAPI]",
                 "веб-хуки, каталог,\nрассылка")
    # база данных — цилиндр
    db = Box(7.6, 2.75, 10.0, 2.6)
    e = 0.35
    ax.add_patch(Rectangle((db.l, db.b + e), db.w, db.h - 2 * e, fc=C_CONT, ec="none", zorder=4))
    ax.add_patch(Ellipse((db.x, db.b + e), db.w, 2 * e, fc=C_CONT, ec="#2e6295", lw=1.0, zorder=3))
    ax.plot([db.l, db.l], [db.b + e, db.t - e], color="#2e6295", lw=1.0, zorder=5)
    ax.plot([db.r, db.r], [db.b + e, db.t - e], color="#2e6295", lw=1.0, zorder=5)
    ax.add_patch(Ellipse((db.x, db.t - e), db.w, 2 * e, fc="#5a9fe0", ec="#2e6295", lw=1.0, zorder=5))
    block(db.x, db.y - 0.2, "База данных project_mgmt", "[Container: PostgreSQL 16, pg_cron]",
          "12 таблиц (D1–D12), ограничения, триггеры, функции,\nпредставления; планировщик: сводка, просрочки")

    # внешние системы
    cat = cont(Box(17.6, 9.0, 4.0, 1.9), "Каталог сотрудников", "[Software System]", "SSO, OpenID Connect", fc=C_EXT)
    git = cont(Box(17.6, 6.1, 4.0, 1.4), "Git-хостинг", "[Software System]", "", fc=C_EXT)
    ntf = cont(Box(17.6, 3.2, 4.0, 1.9), "Сервис уведомлений", "[Software System]", "почта, мессенджер", fc=C_EXT)

    # связи
    rel([lead.bottom(), (lead.x, ui.t)], "работает [HTTPS]", (lead.x, 12.05))
    rel([mem.bottom(), (mem.x, ui.t)], "работает [HTTPS]", (mem.x, 12.05))
    rel([adm.bottom(), (adm.x, ui.y + 0.3), (ui.r, ui.y + 0.3)], "регистрирует\n[HTTPS]", (adm.x, 11.8))
    rel([adb.bottom(-1.0), (adb.x - 1.0, db.y), (db.l, db.y)], "init.sh,\nmigrate.sh\n[psql]", (adb.x - 1.0, 9.6))
    rel([(6.0, ui.b), (6.0, api.t)], "вызывает API\n[HTTP/JSON]", (6.0, 8.6))
    rel([(8.4, api.t), (8.4, 8.75), (cat.l - 0.3, 8.75), (cat.l - 0.3, cat.y - 0.35), (cat.l, cat.y - 0.35)],
        "вход [OpenID Connect]", (11.4, 8.75))
    rel([(api.x, api.b), (api.x, db.t)], "функции и запросы\n[SQL, роль pm_app]", (api.x, 4.75))
    rel([(integ.x - 1.0, integ.b), (integ.x - 1.0, db.t)], "статусы, учётные\nзаписи [SQL]", (integ.x - 1.0, 4.75))
    rel([git.left(), (integ.r, git.y)], "коммит с ключом\n[веб-хук, HTTPS]", (14.9, git.y + 0.62))
    rel([cat.bottom(-1.2), (cat.x - 1.2, 7.55), (integ.r, 7.55)], "сотрудники", (14.95, 7.55))
    rel([(integ.x + 1.2, integ.b), (integ.x + 1.2, ntf.y), ntf.left()], "уведомления\n[SMTP, HTTPS]",
        (14.4, ntf.y + 0.55))

    ax.set_ylim(-0.75, H)
    fig.set_size_inches(W * 0.45, (H + 0.75) * 0.45)
    ax.text(0.4, -0.7, "Обозначения: тёмно-синий — пользователь; голубой — контейнер системы; серый — внешняя "
            "система;\nпунктир — граница системы; стрелка — обращение, в скобках — технология.",
            fontsize=D - 0.5, va="bottom", color="#333333", linespacing=1.15)
    save(fig, "arch")


# --------------------------------------------------------------------------
# 8. Схема вычислений аналитического отчёта (report.sql)
# --------------------------------------------------------------------------
def report_diagram():
    W, H = 17.0, 7.7
    fig, ax = canvas(W, H, k=0.6)
    S = 13

    def node(b, title, sub, fc):
        ax.add_patch(FancyBboxPatch((b.l, b.b), b.w, b.h, boxstyle="round,pad=0,rounding_size=0.15",
                                    fc=fc, ec=LINE, lw=1.1, zorder=3))
        ax.text(b.x, b.y + (0.2 if sub else 0), title, ha="center", va="center", fontsize=S, weight=BOLD, zorder=5)
        if sub:
            ax.text(b.x, b.y - 0.28, sub, ha="center", va="center", fontsize=S - 2.5, zorder=5, color=GREY)

    for t, x in [("Исходные данные", 1.75), ("Промежуточные\nпоказатели", 5.6), ("Агрегация", 9.9),
                 ("Итоговый отчёт", 14.6)]:
        ax.text(x, 7.25, t, ha="center", va="center", fontsize=S, weight=BOLD, color=GREY)
    for xs in (3.6, 7.6, 12.2):
        ax.plot([xs, xs], [0.2, 7.7], color="#999999", lw=1, ls=(0, (4, 3)))

    src = {}
    for n, y, sub in [("params", 6.25, "дата отчёта"), ("tasks", 5.1, None), ("projects", 3.95, None),
                      ("project_members", 2.3, None), ("projects · users", 0.95, "владелец, исполнитель")]:
        b = Box(1.75, y, 3.15, 0.95)
        node(b, n, sub, FILL_STORE)
        src[n] = b
    tf = Box(5.6, 5.1, 3.4, 1.5)
    node(tf, "task_facts", "флаги и часы\nпо каждой задаче", FILL_PROC)
    ps = Box(9.9, 6.25, 3.9, 0.95)
    node(ps, "project_stats", "итоги по проекту", FILL_PROC)
    al = Box(9.9, 4.95, 3.9, 0.95)
    node(al, "assignee_load", "остаток по исполнителю", FILL_PROC)
    bn = Box(9.9, 3.65, 3.9, 0.95)
    node(bn, "bottleneck", "самый загруженный", FILL_PROC)
    tm = Box(9.9, 2.3, 3.9, 0.95)
    node(tm, "team", "размер команды", FILL_PROC)
    rp = Box(14.6, 4.2, 4.2, 4.6)
    node(rp, "report", None, FILL_ENT)
    ax.text(rp.x, rp.y - 0.75, "прогресс, %;\nтемп, ч/нед\nна человека;\nуровень риска", ha="center",
            va="center", fontsize=S - 2, zorder=5, color=GREY)

    A = dict(lw=1.2, head=13)
    arrow(ax, [src["params"].right(), (tf.x, src["params"].y), tf.top()], **A)
    arrow(ax, [src["tasks"].right(), tf.left()], **A)
    arrow(ax, [src["projects"].right(), (tf.x, src["projects"].y), tf.bottom()], **A)
    arrow(ax, [tf.right(0.45), (7.8, tf.y + 0.45), (7.8, ps.y), ps.left()], **A)
    arrow(ax, [(tf.r, al.y), al.left()], **A)
    arrow(ax, [al.bottom(), bn.top()], **A)
    arrow(ax, [src["project_members"].right(), tm.left()], **A)
    arrow(ax, [ps.right(), (rp.l, ps.y)], **A)
    arrow(ax, [bn.right(), (rp.l, bn.y)], **A)
    arrow(ax, [tm.right(), (rp.l, tm.y)], **A)
    arrow(ax, [src["projects · users"].right(), (rp.x, src["projects · users"].y), rp.bottom()], **A)
    ax.text(8.2, 1.25, "LEFT JOIN: проекты без задач тоже попадают в отчёт", fontsize=S - 2.5,
            ha="center", style="italic", color=GREY)

    save(fig, "report")


# --------------------------------------------------------------------------
# 9. Схема алгоритма самого медленного модуля (ГОСТ 19.701-90)
# --------------------------------------------------------------------------
def algo_diagram():
    W, H = 11.4, 15.6
    fig, ax = canvas(W, H, k=0.62)
    S = 13
    X, BW = 5.35, 7.0

    def terminator(y, text):
        b = Box(X, y, 3.2, 0.8)
        ax.add_patch(FancyBboxPatch((b.l, b.b), b.w, b.h, boxstyle="round,pad=0,rounding_size=0.4",
                                    fc="white", ec=LINE, lw=1.5, zorder=3))
        ax.text(X, y, text, ha="center", va="center", fontsize=S, zorder=5)
        return b

    def proc(y, text, h=1.25):
        b = Box(X, y, BW, h)
        ax.add_patch(Rectangle((b.l, b.b), b.w, b.h, fc="white", ec=LINE, lw=1.5, zorder=3))
        ax.text(X, y, text, ha="center", va="center", fontsize=S, zorder=5, linespacing=1.2)
        return b

    def loop(y, text, top=True, h=1.1):
        b = Box(X, y, BW, h)
        c = 0.45
        if top:
            pts = [(b.l + c, b.t), (b.r - c, b.t), (b.r, b.t - c), (b.r, b.b), (b.l, b.b), (b.l, b.t - c)]
        else:
            pts = [(b.l, b.t), (b.r, b.t), (b.r, b.b + c), (b.r - c, b.b), (b.l + c, b.b), (b.l, b.b + c)]
        ax.add_patch(Polygon(pts, closed=True, fc="white", ec=LINE, lw=1.5, zorder=3))
        ax.text(X, y, text, ha="center", va="center", fontsize=S, zorder=5, linespacing=1.2)
        return b

    def decision(y, text, w=6.4, h=2.0):
        ax.add_patch(Polygon([(X - w / 2, y), (X, y + h / 2), (X + w / 2, y), (X, y - h / 2)], closed=True,
                             fc="white", ec=LINE, lw=1.5, zorder=3))
        ax.text(X, y, text, ha="center", va="center", fontsize=S - 0.5, zorder=5, linespacing=1.15)
        return Box(X, y, w, h)

    def line(a, b):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=LINE, lw=1.4, zorder=2)

    b0 = terminator(15.0, "Начало")
    b1 = proc(13.6, "Соединить project_members, projects,\nusers: участники действующих\n"
                    "проектов", h=1.5)
    b2 = loop(11.95, "Цикл по участникам\n«проект p — сотрудник u»", top=True)
    b3 = proc(10.3, "Подзапросы 1, 2: число и часы\nнезавершённых задач u в p\n(tasks: project_id, assignee_id)",
              h=1.55)
    b4 = decision(8.15, "Есть комментарии\nu в задачах p?")
    b5 = proc(5.95, "Подзапрос 3: последний\nкомментарий u в задачах p\n(comments: author_id)", h=1.5)
    b6 = loop(4.3, "Конец цикла", top=False)
    b7 = proc(2.75, "Упорядочить по проекту\nи часам (по убыванию)", h=1.15)
    b8 = terminator(1.35, "Конец")

    for a, b in [(b0, b1), (b1, b2), (b2, b3), (b3, b4), (b4, b5), (b5, b6), (b6, b7), (b7, b8)]:
        line(a.bottom(), b.top())
    ax.text(X + 0.25, b4.b - 0.3, "да", fontsize=S, va="center")
    # «нет» — в обход блока добавления к концу цикла
    pts = [b4.right(), (9.65, b4.y), (9.65, 5.0), (X, 5.0)]
    polyline(ax, pts, lw=1.4, rnd=False)
    ax.text(b4.r + 0.15, b4.y + 0.3, "нет", fontsize=S, va="center")
    # символ «Комментарий» (ГОСТ 19.701): скобка, связанная пунктиром с поясняемым блоком
    bx, bh = 9.35, 1.3
    ax.plot([b3.r, bx], [b3.y, b3.y], color=LINE, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax.plot([bx + 0.25, bx, bx, bx + 0.25], [b3.y + bh / 2, b3.y + bh / 2, b3.y - bh / 2, b3.y - bh / 2],
            color=LINE, lw=1.4, zorder=3)
    ax.text(bx + 0.15, b3.y, "выполняется\nдля каждой\nстроки", fontsize=S - 2.5, va="center", ha="left",
            color="#333333", linespacing=1.15)
    # левое поле не нужно: схема начинается у x ≈ 1.85
    ax.set_xlim(1.6, W)
    fig.set_size_inches((W - 1.6) * 0.62, H * 0.62)

    save(fig, "algo")


# --------------------------------------------------------------------------
# Окружение системы и компонентное представление
# --------------------------------------------------------------------------
def env_diagram():
    W, H = 19.6, 12.8
    fig, ax = canvas(W, H, k=0.62)
    S = 12.5

    def svc(b, t, sub):
        ext_shape(ax, b, fc=PAL["svc"])
        ax.add_patch(Rectangle((b.l + 0.1, b.b + 0.1), b.w - 0.2, b.h - 0.2, fc="none", ec=LINE, lw=0.8, zorder=2))
        ax.text(b.x, b.y + 0.2, t, ha="center", va="center", fontsize=S, weight=BOLD, zorder=5)
        ax.text(b.x, b.y - 0.3, sub, ha="center", va="center", fontsize=S - 2.5, color=GREY, zorder=5)

    lead = Box(1.9, 9.9, 3.4, 1.3)
    mem = Box(1.9, 3.6, 3.4, 1.3)
    external(ax, lead, "Руководитель\nпроекта", S)
    external(ax, mem, "Участник\nпроекта", S)
    cust = Box(1.9, 7.45, 3.4, 1.1)
    external(ax, cust, "Заказчик\nпроекта", S)
    cat = Box(7.55, 11.0, 4.3, 1.25)
    ntf = Box(7.55, 6.7, 4.3, 1.25)
    git = Box(7.55, 1.55, 4.3, 1.25)
    svc(cat, "Каталог сотрудников", "SSO, учётные записи")
    svc(ntf, "Сервис уведомлений", "почта, мессенджер, календарь")
    svc(git, "Git-хостинг", "репозитории проектов")

    sysb = Box(15.55, 6.6, 7.7, 11.4)
    ax.add_patch(FancyBboxPatch((sysb.l, sysb.b), sysb.w, sysb.h, boxstyle="round,pad=0,rounding_size=0.3",
                                fc=PAL["sys_fill"], ec=PAL["sys_border"], lw=1.6, zorder=1))
    ax.text(sysb.l + 0.25, sysb.t - 0.42, "0   Система управления проектами", fontsize=S + 0.5, weight=BOLD,
            va="center", zorder=5)

    p1 = Box(13.9, 10.2, 3.3, 1.6)
    p4 = Box(13.9, 6.7, 3.3, 1.6)
    p5 = Box(13.9, 2.6, 3.3, 1.6)
    process(ax, p1, "1.0", "Регистрация\nпользователей", S - 0.5, band=0.42)
    process(ax, p4, "4.0", "Управление\nзадачами", S - 0.5, band=0.42)
    process(ax, p5, "5.0", "Обсуждение\nзадач", S - 0.5, band=0.42)
    db = Box(17.75, 6.7, 2.9, 1.1)
    store(ax, db, "БД", "project_mgmt\nD1–D12", S - 1, cell=0.6)
    p6 = Box(17.75, 4.6, 2.9, 1.3)
    process(ax, p6, "6.0", "Формирование\nотчётов", S - 0.5, band=0.42)

    # ортогональные потоки; пересечение одно — веб-хук (7) с отчётом заказчику (9)
    A = dict(size=S - 1.5, lw=1.3, head=14)
    arrow(ax, [cat.right(-0.3), (p1.l, cat.y - 0.3)], dashed=True, **A)
    label(ax, 10.8, 11.3, "1) учётная\nзапись", S - 1.5)
    arrow(ax, [lead.right(-0.2), (10.0, lead.y - 0.2), (10.0, p4.y + 0.35), p4.left(0.35)],
          "2) задача SHOP-42,\nисполнитель, срок", at=(6.75, lead.y - 0.2), **A)
    arrow(ax, [p4.right(), db.left()], "3)", at=(16.0, 6.95), **A)
    arrow(ax, [p4.left(-0.2), (ntf.r, p4.y - 0.2)], dashed=True, **A)
    label(ax, 10.85, 5.95, "4) назначена\nSHOP-42", S - 1.5)
    arrow(ax, [ntf.left(-0.3), (2.7, ntf.y - 0.3), (2.7, mem.t)], "5) письмо, событие\nв календаре",
          at=(4.15, 5.75), dashed=True, **A)
    arrow(ax, [mem.bottom(0.6), (mem.x + 0.6, git.y - 0.2), git.left(-0.2)], "6) коммит\n«SHOP-42: …»",
          at=(3.95, git.y - 0.2), dashed=True, **A)
    arrow(ax, [git.right(0.2), (10.4, git.y + 0.2), (10.4, 5.05), (p4.x - 0.9, 5.05), p4.bottom(-0.9)],
          "7) веб-хук:\nSHOP-42 → review", at=(10.4, 3.2), dashed=True, **A)
    arrow(ax, [mem.bottom(-0.8), (1.1, 0.35), (p5.x, 0.35), p5.bottom()], "8) комментарий к задаче",
          at=(10.6, 0.35), **A)

    # отчёт заказчику: заказчик вне системы, обмен идёт через руководителя и сервис уведомлений
    arrow(ax, [db.bottom(), p6.top()], **A)
    arrow(ax, [p6.left(), (8.6, p6.y), (8.6, ntf.b)], "9) отчёт заказчику", at=(13.9, p6.y), dashed=True, **A)
    arrow(ax, [ntf.left(0.3), (cust.r, ntf.y + 0.3)], dashed=True, **A)
    label(ax, 4.5, 7.55, "10) письмо\nс отчётом", S - 1.5)
    arrow(ax, [cust.top(), lead.bottom()], "требования", at=(cust.x, 8.62), color=GREY, **A)

    ax.text(0.15, 12.55, "Шаги 1–8 — путь задачи, 9–10 — отчёт заказчику; пунктир — обмен с внешним сервисом; "
            "серым — обмен вне системы", fontsize=S - 2.5, color=GREY, va="center")
    save(fig, "env")


def components_diagram():
    W, H = 27.3, 17.6
    fig, ax = canvas(W, H, k=0.58)
    S = 12

    sysb = Box(12.7, 8.55, 18.0, 13.3)
    ax.add_patch(FancyBboxPatch((sysb.l, sysb.b), sysb.w, sysb.h, boxstyle="round,pad=0,rounding_size=0.4",
                                fc=PAL["sys_fill"], ec=PAL["sys_border"], lw=1.6, zorder=0))
    ax.text(sysb.x, sysb.t - 0.42, "Система управления проектами", fontsize=S + 1, weight=BOLD,
            va="center", ha="center", color=GREY)

    def esb(b, code, t):
        ext_shape(ax, b)
        ax.text(b.x, b.y + 0.27, code, ha="center", va="center", fontsize=S, weight=BOLD, zorder=5)
        ax.text(b.x, b.y - 0.2, t, ha="center", va="center", fontsize=S - 1, zorder=5, linespacing=1.1)
        return b

    def comp(x, y, code, name, ops, i, rh=0.43):
        w, hh = 4.0, 0.62
        h = hh + rh * len(ops) + 0.15
        b = Box(x, y, w, h)
        proc_shape(ax, b, hh, 0.15)   # как процесс: оранжевая шапка, жёлтое тело
        ax.text(b.x, b.t - hh / 2, f"{code} {name}", ha="center", va="center", fontsize=S, weight=BOLD, zorder=5)
        for k, op in enumerate(ops):
            yy = b.t - hh - 0.08 - rh * (k + 0.5)
            ax.add_patch(Rectangle((b.l + 0.15, yy - rh / 2 + 0.03), w - 0.3, rh - 0.06, fc=PAL["op"], ec=GREY,
                                   lw=0.6, zorder=4))
            ax.text(b.l + 0.27, yy, op, ha="left", va="center", fontsize=S - 2, zorder=5)
        return b

    # информационный ресурс — БД в центре
    db = Box(12.7, 8.3, 5.6, 4.6)
    e = 0.45
    ax.add_patch(Rectangle((db.l, db.b + e), db.w, db.h - 2 * e, fc=FILL_STORE, ec="none", zorder=2))
    ax.add_patch(Ellipse((db.x, db.b + e), db.w, 2 * e, fc=FILL_STORE, ec=LINE, lw=1.2, zorder=2))
    ax.add_patch(Rectangle((db.l, db.b + e), db.w, db.h - 2 * e, fc=FILL_STORE, ec="none", zorder=2))
    ax.plot([db.l, db.l], [db.b + e, db.t - e], color=LINE, lw=1.2, zorder=3)
    ax.plot([db.r, db.r], [db.b + e, db.t - e], color=LINE, lw=1.2, zorder=3)
    ax.add_patch(matplotlib.patches.Arc((db.x, db.b + e), db.w, 2 * e, theta1=180, theta2=360, color=LINE, lw=1.2, zorder=3))
    ax.add_patch(Ellipse((db.x, db.t - e), db.w, 2 * e, fc=PAL["db_top"], ec=LINE, lw=1.2, zorder=3))
    ax.text(db.x, db.t - 1.25, "ИР: БД project_mgmt", ha="center", va="center", fontsize=S + 0.5, weight=BOLD, zorder=5)
    # по одной таблице на накопитель
    for col, items in enumerate([["D1 Пользователи", "D2 Заказчики", "D3 Проекты", "D4 Договоры", "D5 Участники",
                                  "D6 Спринты"],
                                 ["D7 Задачи", "D8 Метки", "D9 Метки задач", "D10 История", "D11 Трудозатраты",
                                  "D12 Комментарии"]]):
        for k, t in enumerate(items):
            ax.text(db.l + 0.25 + col * 2.75, db.t - 1.75 - k * 0.42, t, ha="left", va="center", fontsize=S - 2.5,
                    zorder=5)

    K2 = comp(8.0, 12.8, "К2", "Проекты", ["2.1 Создание проекта", "2.2 Владелец", "2.3 Параметры проекта",
                                         "2.4 Удаление", "2.5 Ведение заказчиков", "2.6 Договор",
                                         "2.7 Привязка заказчика"], 2, rh=0.41)
    K3 = comp(17.4, 13.0, "К3", "Команды", ["3.1 Добавление", "3.2 Назначение роли", "3.3 Исключение"], 3)
    K6 = comp(5.9, 8.3, "К6", "Отчётность", ["6.1 Операционные перечни", "6.2 Анализ загрузки команд",
                                             "6.3 Отчёт о рисках", "6.4 Отчёт заказчику",
                                             "6.5 Отчёт по договорам", "6.6 Показатели команды"], 6)
    K4 = comp(19.5, 8.3, "К4", "Задачи", ["4.1 Создание задачи", "4.2 Назначение", "4.3 Смена статуса",
                                          "4.4 Удаление", "4.5 Ведение меток", "4.6 Ведение спринтов",
                                          "4.7 Закрытие спринта", "4.8 Пакетная загрузка",
                                          "4.9 Учёт трудозатрат", "4.10 Оценка трудоёмкости",
                                          "4.11 Изменение приоритета", "4.12 Метки задач",
                                          "4.13 Планирование в спринт"], 4, rh=0.39)
    K1 = comp(8.0, 3.6, "К1", "Пользователи", ["1.1 Регистрация", "1.2 Изменение", "1.3 Удаление"], 1)
    K5 = comp(17.4, 3.6, "К5", "Обсуждения", ["5.1 Добавление", "5.2 Просмотр", "5.3 Удаление"], 5)

    E2 = esb(Box(12.7, 16.6, 3.6, 1.25), "Э2", "Руководитель проекта")
    E1 = esb(Box(1.85, 4.15, 3.3, 1.25), "Э1", "Администратор")
    E4 = esb(Box(1.85, 1.75, 3.3, 1.35), "Э4", "Каталог\nсотрудников")
    E5 = esb(Box(23.55, 9.2, 3.3, 1.25), "Э5", "Git-хостинг")
    E3 = esb(Box(23.55, 7.3, 3.3, 1.35), "Э3", "Участник\nпроекта")
    E6 = esb(Box(12.7, 0.75, 4.0, 1.25), "Э6", "Сервис уведомлений")

    L = S - 1
    # связи ЭСО ↔ компоненты
    arrow(ax, [E1.right(0.25), (K1.l, E1.y + 0.25)], "З1", at=(5.0, E1.y + 0.25), size=L, color=SC(1))
    arrow(ax, [(K1.l, E1.y - 0.25), E1.right(-0.25)], "О1", at=(5.0, E1.y - 0.25), size=L, color=SC(1))
    arrow(ax, [E4.right(), (5.0, E4.y), (5.0, 2.85), (K1.l, 2.85)], "З2", at=(4.25, E4.y), size=L, color=SC(1))
    arrow(ax, [E2.left(-0.3), (K2.x, E2.y - 0.3), K2.top()], "З3", at=(9.5, E2.y - 0.3), size=L, color=SC(2))
    arrow(ax, [E2.right(-0.3), (K3.x, E2.y - 0.3), K3.top()], "З4", at=(15.9, E2.y - 0.3), size=L, color=SC(3))
    arrow(ax, [E2.right(0.3), (20.6, E2.y + 0.3), (20.6, K4.t)], "З5", at=(20.6, 12.9), size=L, color=SC(4))
    arrow(ax, [K6.top(-0.9), (5.0, E2.y + 0.3), E2.left(0.3)], "О2", at=(5.0, 12.9), size=L, color=SC(6))
    arrow(ax, [E2.left(0.0), (5.6, E2.y), (5.6, K6.t)], "З9", at=(5.6, 14.6), size=L, color=SC(6))
    arrow(ax, [E5.left(), (K4.r, E5.y)], "З6", at=(21.7, E5.y + 0.32), size=L, color=SC(4))
    arrow(ax, [E3.left(0.35), (K4.r, E3.y + 0.35)], "З7", at=(21.7, E3.y + 0.67), size=L, color=SC(4))
    arrow(ax, [E3.bottom(-1.0), (22.55, 3.6), K5.right()], "З8", at=(21.6, 3.6), size=L, color=SC(5))
    arrow(ax, [K4.bottom(1.1), (20.6, 0.85), E6.right(0.1)], "О3", at=(20.6, 4.4), size=L, color=SC(4))
    arrow(ax, [K5.bottom(-0.8), (K5.x - 0.8, 1.25), E6.right(0.5)], "О4", at=(16.6, 1.9), size=L, color=SC(5))
    arrow(ax, [K6.bottom(1.5), (K6.x + 1.5, 5.25), (11.2, 5.25), (11.2, E6.t)], "О5", at=(8.2, 5.25), size=L,
          color=SC(6))
    arrow(ax, [E6.right(-0.35), (24.6, 0.4), E3.bottom(1.05)], "доставка\nуведомлений", at=(24.6, 3.2), size=L - 1,
          color=GREY, dashed=True)

    # связи компоненты ↔ ИР (запись/чтение)
    G = "#555555"
    # ортогонально: от компонента по вертикали, затем по горизонтали к стенке цилиндра
    for kb, dy, t, at in [(K1, -1.5, "D1", (9.0, 5.75)), (K2, 1.6, "D2–D4; D1", (9.0, 10.4)),
                          (K3, 1.6, "D5; D3", (16.4, 10.85)), (K4, 0.0, "D6–D11; D5", (16.55, 8.3)),
                          (K5, -1.5, "D12; D7", (16.4, 5.75)), (K6, 0.0, "D1–D12", (8.9, 8.3))]:
        left = kb.x < db.x
        pt = db.left(dy) if left else db.right(dy)
        if kb in (K4, K6):
            pts = [kb.right() if left else kb.left(), pt]
        else:
            x = kb.x + (1.0 if left else -1.0)
            pts = [(x, kb.b if kb in (K2, K3) else kb.t), (x, pt[1]), pt]
        arrow(ax, pts, lw=1.1, head=12, color=G, both=True)
        label(ax, at[0], at[1], t, S - 2, color=G)

    # легенда
    lx, ly = 22.1, 15.35
    ax.add_patch(Rectangle((lx, ly - 3.05), 5.1, 3.05, fc="white", ec="#888888", lw=1, zorder=1))
    ax.text(lx + 0.15, ly - 0.3, "Обозначения", fontsize=S - 1, weight=BOLD, va="center")
    ax.shadow = 0.05
    ext_shape(ax, Box(lx + 0.65, ly - 0.72, 0.8, 0.45), lw=1.0)
    ax.text(lx + 1.3, ly - 0.72, "ЭСО — элемент окружения", fontsize=S - 2.5, va="center")
    proc_shape(ax, Box(lx + 0.65, ly - 1.32, 0.8, 0.45), 0.16, 0.06, lw=1.0)
    ax.text(lx + 1.3, ly - 1.32, "К — программный компонент", fontsize=S - 2.5, va="center")
    ax.add_patch(Ellipse((lx + 0.65, ly - 1.95), 0.8, 0.3, fc=FILL_STORE, ec=LINE, lw=1.0))
    ax.text(lx + 1.3, ly - 1.95, "ИР — информационный ресурс", fontsize=S - 2.5, va="center")
    ax.annotate("", xy=(lx + 1.05, ly - 2.55), xytext=(lx + 0.25, ly - 2.55),
                arrowprops=dict(arrowstyle="-|>", color=LINE, lw=1.3, mutation_scale=13))
    ax.text(lx + 1.3, ly - 2.55, "З — вход, О — выход", fontsize=S - 2.5, va="center")

    save(fig, "components")


# ==========================================================================
# Приложения: DFD уровня 2 и BPMN для каждого процесса
# ==========================================================================
def ext_copy(ax, box, text, size):
    """Копия внешней сущности: косая черта в правом нижнем углу."""
    external(ax, box, text, size)
    c = 0.4
    ax.plot([box.r - c, box.r], [box.b, box.b + c], color=LINE, lw=1.2, zorder=4)


def dfd2_column(name, ext_name, procs, top_items, store_id, store_name, ext_extra=None):
    """DFD-2 небольшого процесса: внешняя сущность слева, подпроцессы столбцом,
    накопитель справа; сверху — дополнительные элементы (накопитель или сущность).
    procs: [(номер, текст, [(направление, подпись), ...] — потоки с внешней сущностью,
             (направление, подпись) — поток с накопителем)]."""
    W, H = 23.0, 11.4
    fig, ax = canvas(W, H, k=0.53)
    S, L = 16, 14
    xP, pw, ph = 12.0, 4.4, 2.0
    ys = [7.5, 4.6, 1.7]
    e = Box(3.0, 4.75, 3.8, 7.6)
    external(ax, e, ext_name, S)
    st = Box(19.8, ys[1], 3.9, 1.15)
    store(ax, st, store_id, store_name, L, cell=0.75)
    for i, (num, text, ext_flows, st_flow) in enumerate(procs):
        b = Box(xP, ys[i], pw, ph)
        process(ax, b, num, text, S, band=0.45)
        # потоки с внешней сущностью
        k = len(ext_flows)
        for j, (d, lab) in enumerate(ext_flows):
            y = b.y + (0.45 if k == 2 and j == 0 else -0.45 if k == 2 else 0.0)
            pts = [(e.r, y), (b.l, y)] if d == "in" else [(b.l, y), (e.r, y)]
            flow(ax, pts, lab, at=((e.r + b.l) / 2, y + 0.33), size=L)
        # поток с накопителем
        d, lab = st_flow
        if i == 1:
            pts = [b.right(), st.left()] if d != "read" else [st.left(), b.right()]
            flow(ax, pts, lab, at=((b.r + st.l) / 2, b.y + 0.35), size=L, both=(d == "both"))
        else:
            xv = st.x - 0.8 if i == 0 else st.x + 0.8
            yv = st.t if i == 0 else st.b
            pts = [b.right(), (xv, b.y), (xv, yv)]
            if d == "read":
                pts = pts[::-1]
            flow(ax, pts, lab, at=((b.r + xv) / 2, b.y + 0.35), size=L, both=(d == "both"))
    for item in top_items:
        item(ax, Box(xP, ys[0], pw, ph))
    if ext_extra:
        ext_extra(ax)
    return fig, ax


def dfd2_p1():
    fig, ax = dfd2_column("1", "Администратор", [
        ("1.1", "Регистрация", [("in", "новый\nсотрудник"), ("out", "подтверждение")], ("write", "сотрудник")),
        ("1.2", "Изменение\nданных", [("in", "изменения")], ("both", "данные")),
        ("1.3", "Удаление", [("in", "удаление")], ("write", "удаление")),
    ], [lambda ax, p: (external(ax, Box(p.x, 10.5, 4.6, 1.1), "Каталог сотрудников", 14),
                       flow(ax, [(p.x, 9.95), p.top()], "учётные записи", at=(p.x, 9.25), size=14))],
        "D1", "Пользователи")
    save(fig, "dfd2_p1")


def dfd2_p3():
    fig, ax = dfd2_column("3", "Руководитель\nпроекта", [
        ("3.1", "Добавление\nучастника", [("in", "участник")], ("write", "участник")),
        ("3.2", "Назначение\nроли", [("in", "роль")], ("both", "роль")),
        ("3.3", "Исключение\nучастника", [("in", "исключение")], ("write", "исключение")),
    ], [lambda ax, p: (store(ax, Box(p.x, 10.5, 4.6, 1.0), "D3", "Проекты", 14, cell=0.75),
                       flow(ax, [(p.x, 10.0), p.top()], "проект", at=(p.x, 9.25), size=14))],
        "D5", "Участники\nпроектов")
    save(fig, "dfd2_p3")


def dfd2_p5():
    def extra(ax):
        n = Box(19.8, 10.5, 4.6, 1.1)
        external(ax, n, "Сервис уведомлений", 14)
        flow(ax, [(13.4, 8.5), (13.4, 10.5), n.left()], "новый комментарий", at=(15.6, 10.5), size=14)
    fig, ax = dfd2_column("5", "Участник\nпроекта", [
        ("5.1", "Добавление\nкомментария", [("in", "комментарий")], ("write", "комментарий")),
        ("5.2", "Просмотр\nобсуждения", [("out", "обсуждение")], ("read", "комментарии")),
        ("5.3", "Удаление\nкомментария", [("in", "удаление")], ("write", "удаление")),
    ], [lambda ax, p: (store(ax, Box(p.x - 1.4, 10.5, 4.0, 1.0), "D7", "Задачи", 14, cell=0.75),
                       flow(ax, [(p.x - 1.4, 10.0), p.top(-1.4)], "задача", at=(p.x - 1.4, 9.25), size=14))],
        "D12", "Комментарии", ext_extra=extra)
    save(fig, "dfd2_p5")


def dfd2_band(top, bottom, top_stores, bottom_stores, top_links, bottom_links, extra=None, W=20.0, cols_t=None,
              cols_b=None, pw=5.6):
    """DFD-2 процесса из шести подпроцессов: два ряда подпроцессов, между ними — полоса
    «Руководитель проекта», накопители над верхним рядом и под нижним.
    top/bottom: [(номер, текст)] по столбцам; *_stores: [(x0, x1, id, имя, dup)];
    *_links: [(столбец, x_накопителя, направление, подпись)] — направление 'read' | 'write'."""
    H = 14.2
    fig, ax = canvas(W, H, k=0.53)
    S, L, LS = 16, 13, 12.5
    cols_t = cols_t or [3.4, 10.0, 16.6]
    cols_b = cols_b or cols_t
    ph = 2.2
    yTS, yT, yR, yB, yBS = 12.9, 10.2, 6.9, 3.6, 1.0
    r = Box(W / 2, yR, W - 1.2, 1.2)
    external(ax, r, "Руководитель проекта", S)
    PT = [Box(x, yT, pw, ph) for x in cols_t[:len(top)]]
    PB = [Box(x, yB, pw, ph) for x in cols_b[:len(bottom)]]
    for b, (num, text) in zip(PT, top):
        process(ax, b, num, text, S, band=0.45)
    for b, (num, text) in zip(PB, bottom):
        if num:
            process(ax, b, num, text, S, band=0.45)
    for (x0, x1, sid, name, dup) in top_stores:
        store(ax, Box((x0 + x1) / 2, yTS, x1 - x0, 1.0), sid, name, LS, cell=0.6, dup=dup)
    for (x0, x1, sid, name, dup) in bottom_stores:
        store(ax, Box((x0 + x1) / 2, yBS, x1 - x0, 1.0), sid, name, LS, cell=0.6, dup=dup)
    for (i, x, d, lab) in top_links:
        a, b = (x, yTS - 0.5), (x, PT[i].t)
        flow(ax, [a, b] if d == "read" else [b, a], lab, at=(x, (yTS - 0.5 + PT[i].t) / 2), size=L - 1.5)
    for (i, x, d, lab) in bottom_links:
        a, b = (x, yBS + 0.5), (x, PB[i].b)
        flow(ax, [a, b] if d == "read" else [b, a], lab, at=(x, (yBS + 0.5 + PB[i].b) / 2), size=L - 1.5)
    if extra:
        extra(ax, r, PT, PB, L)
    return fig, ax


def dfd2_p2():
    """Процесс 2: 7 атомарных подпроцессов. Сверху — работа с проектом (D3) и договор (D4),
    снизу — удаление (копия D3), привязка заказчика (пишет D3, читает D2) и ведение заказчиков (D2)."""
    def extra(ax, r, PT, PB, L):
        for b, lab in zip(PT, ["название,\nкод, сроки", "новый\nвладелец", "статус,\nсроки", "договор"]):
            flow(ax, [(b.x, r.t), b.bottom()], lab, at=(b.x, (r.t + b.b) / 2), size=L)
        for b, lab in zip(PB, ["удаление", "заказчик\nпроекта", "заказчик"]):
            flow(ax, [(b.x, r.b), b.top()], lab, at=(b.x, (r.b + b.t) / 2), size=L)
    cols = [3.2, 9.0, 14.8, 20.6]
    fig, ax = dfd2_band(
        [("2.1", "Создание\nпроекта"), ("2.2", "Назначение\nвладельца"), ("2.3", "Изменение\nпараметров\nпроекта"),
         ("2.6", "Договор\nс заказчиком")],
        [("2.4", "Удаление\nпроекта"), ("2.7", "Привязка\nзаказчика\nк проекту"), ("2.5", "Ведение\nзаказчиков")],
        [(0.6, 3.0, "D1", "Пользо-\nватели", False), (3.4, 17.4, "D3", "Проекты", False),
         (18.2, 23.2, "D4", "Договоры", False)],
        [(0.7, 8.6, "D3", "Проекты", True), (9.2, 17.4, "D2", "Заказчики", False)],
        [(0, 1.8, "read", "владелец"), (0, 4.6, "write", "проект"), (1, 9.0, "write", "владелец"),
         (2, 14.8, "write", "параметры"), (3, 20.6, "write", "договор")],
        [(0, 3.2, "write", "удаление"), (1, 7.7, "write", "привязка"), (1, 10.3, "read", "заказчик"),
         (2, 14.8, "write", "заказчик")],
        extra, W=23.8, cols_t=cols, cols_b=cols, pw=5.0)
    save(fig, "dfd2_p2")


def dfd2_p6():
    def extra(ax, r, PT, PB, L):
        for b, lab in zip(PT, ["перечни", "загрузка", "показатели"]):
            flow(ax, [(b.x - 1.2, r.t), b.bottom(-1.2)], "пара-\nметры", at=(b.x - 1.2, (r.t + b.b) / 2), size=L - 1)
            flow(ax, [b.bottom(1.2), (b.x + 1.2, r.t)], lab, at=(b.x + 1.2, (r.t + b.b) / 2), size=L - 1)
        for k in (0, 2):
            b = PB[k]
            lab = "отчёт\nо рисках" if k == 0 else "отчёт по\nдоговорам"
            flow(ax, [(b.x - 1.2, r.b), b.top(-1.2)], "пара-\nметры", at=(b.x - 1.2, (r.b + b.t) / 2), size=L - 1)
            flow(ax, [b.top(1.2), (b.x + 1.2, r.b)], lab, at=(b.x + 1.2, (r.b + b.t) / 2), size=L - 1)
        flow(ax, [PB[0].right(), PB[1].left()], "риски", at=((PB[0].r + PB[1].l) / 2, PB[1].y + 0.35), size=L - 1.5)
        flow(ax, [PB[2].left(), PB[1].right()], "договоры", at=((PB[2].l + PB[1].r) / 2, PB[1].y + 0.35),
             size=L - 1.5)
        n = Box(11.55, 1.0, 2.5, 1.2)
        external(ax, n, "Сервис\nуведом-\nлений", 11)
        flow(ax, [(11.55, PB[1].b), n.top()], None, size=L)
        ax.text(12.0, (PB[1].b + n.t) / 2, "отчёт\nзаказчику", fontsize=L - 2, ha="left", va="center")
    fig, ax = dfd2_band(
        [("6.1", "Операционные\nперечни"), ("6.2", "Анализ загрузки\nкоманд"), ("6.6", "Показатели\nкоманды")],
        [("6.3", "Отчёт\nо рисках"), ("6.4", "Отчёт\nзаказчику"), ("6.5", "Отчёт\nпо договорам")],
        [(0.6, 3.3, "D1", "Пользо-\nватели", False), (3.5, 6.2, "D7", "Задачи", False),
         (7.2, 9.9, "D5", "Участ-\nники", False), (10.1, 12.8, "D12", "Коммен-\nтарии", False),
         (13.8, 16.5, "D6", "Спринты", False), (16.7, 19.4, "D10", "История\nстатусов", False)],
        [(0.6, 3.3, "D3", "Проекты", False), (3.5, 6.2, "D7", "Задачи", True),
         (7.2, 9.9, "D2", "Заказ-\nчики", False),
         (13.8, 16.5, "D4", "Договоры", False), (16.7, 19.4, "D11", "Трудо-\nзатраты", False)],
        [(0, 1.95, "read", "ФИО"), (0, 4.85, "read", "задачи"), (1, 8.55, "read", "участники"),
         (1, 11.45, "read", "коммен-\nтарии"), (2, 15.15, "read", "спринты"), (2, 18.05, "read", "история")],
        [(0, 1.95, "read", "проекты"), (0, 4.85, "read", "задачи"), (1, 8.55, "read", "заказчики"),
         (2, 15.15, "read", "договоры"), (2, 18.05, "read", "часы")],
        extra)
    save(fig, "dfd2_p6")


# --------------------------------------------------------------------------
# BPMN отдельных процессов P1, P2, P3, P5, P6 (приложение Б)
# --------------------------------------------------------------------------
class BP:
    """Элементы BPMN на осях ax; S — кегль."""

    def __init__(self, ax, W, S=14):
        self.ax, self.W, self.S = ax, W, S
        self.x0, self.x1 = 0.1, W - 0.1

    def pool(self, y0, y1, title, lanes):
        """Пул с дорожками [(имя, низ, верх)]; последняя (система) затенена."""
        ax, S, x0, x1 = self.ax, self.S, self.x0, self.x1
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec=LINE, lw=1.4, zorder=1))
        ax.plot([x0 + 0.6] * 2, [y0, y1], color=LINE, lw=1.2)
        ax.text(x0 + 0.3, (y0 + y1) / 2, title, rotation=90, ha="center", va="center", fontsize=S + 1)
        for name, lo, hi in lanes:
            if lo > y0 + 1e-6:
                ax.plot([x0 + 0.6, x1], [lo, lo], color=LINE, lw=1.1)
            ax.plot([x0 + 1.5] * 2, [lo, hi], color=LINE, lw=1.0)
            ax.text(x0 + 1.05, (lo + hi) / 2, name, rotation=90, ha="center", va="center", fontsize=S,
                    linespacing=1.1)
        _, lo, hi = lanes[-1]
        ax.add_patch(Rectangle((x0 + 1.5, lo), x1 - x0 - 1.5, hi - lo, fc=PAL["lane"], ec="none", zorder=0))

    def black_pool(self, y0, y1, title):
        """Свёрнутый пул внешнего участника («чёрный ящик»)."""
        self.ax.add_patch(Rectangle((self.x0, y0), self.x1 - self.x0, y1 - y0, fc="white", ec=LINE, lw=1.4,
                                    zorder=1))
        self.ax.text(self.W / 2, (y0 + y1) / 2, title, ha="center", va="center", fontsize=self.S + 1)

    def _user_icon(self, x, y):
        ax = self.ax
        ax.add_patch(Circle((x, y + 0.08), 0.07, fc="white", ec=LINE, lw=0.9, zorder=7))
        ax.add_patch(matplotlib.patches.Wedge((x, y - 0.12), 0.14, 0, 180, fc="white", ec=LINE, lw=0.9, zorder=7))

    def _gear_icon(self, x, y):
        ax = self.ax
        for a in range(8):
            ang = a * math.pi / 4
            ax.plot([x + 0.07 * math.cos(ang), x + 0.15 * math.cos(ang)],
                    [y + 0.07 * math.sin(ang), y + 0.15 * math.sin(ang)], color=LINE, lw=1.6, zorder=7)
        ax.add_patch(Circle((x, y), 0.09, fc="white", ec=LINE, lw=0.9, zorder=8))

    def task(self, x, y, text, kind="user", w=2.9, h=1.35, size=None, tx=True):
        """Задача: user — пользовательская, service — сервисная; tx — транзакция (двойная рамка)."""
        ax, b = self.ax, Box(x, y, w, h)
        fc = PAL["bpmn_user"] if kind == "user" else PAL["bpmn_service"]
        ax.add_patch(FancyBboxPatch((b.l, b.b), w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                    fc=fc, ec=LINE, lw=1.2, zorder=4))
        if kind == "trans":
            ax.add_patch(FancyBboxPatch((b.l + 0.08, b.b + 0.08), w - 0.16, h - 0.16,
                                        boxstyle="round,pad=0,rounding_size=0.13", fc="none", ec=LINE, lw=1.0,
                                        zorder=4.5))
        (self._user_icon if kind == "user" else self._gear_icon)(b.l + 0.3, b.t - 0.3)
        ax.text(x + 0.12, y - 0.06, text, ha="center", va="center", fontsize=size or self.S - 1.5, zorder=6,
                linespacing=1.1)
        return b

    def _marker(self, x, y, r, marker, filled):
        ax = self.ax
        if marker == "msg":
            w, h = r * 1.05, r * 0.7
            ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=LINE if filled else "white", ec=LINE, lw=1.0,
                                   zorder=7))
            ax.plot([x - w / 2, x, x + w / 2], [y + h / 2, y, y + h / 2], color="white" if filled else LINE,
                    lw=1.0, zorder=8)
        elif marker == "timer":
            ax.add_patch(Circle((x, y), r - 0.08, fc="white", ec=LINE, lw=1.0, zorder=7))
            ax.plot([x, x], [y, y + 0.11], color=LINE, lw=1.0, zorder=8)
            ax.plot([x, x + 0.08], [y, y], color=LINE, lw=1.0, zorder=8)
        elif marker == "error":
            s = r / 0.3
            ax.add_patch(Polygon([(x - 0.13 * s, y - 0.14 * s), (x - 0.04 * s, y + 0.1 * s), (x + 0.03 * s, y - 0.02 * s),
                                  (x + 0.13 * s, y + 0.15 * s), (x + 0.05 * s, y - 0.1 * s), (x - 0.02 * s, y + 0.02 * s)],
                                 closed=True, fc=LINE if filled else "white", ec=LINE, lw=1.0, zorder=8))

    def event(self, x, y, kind, text=None, r=0.3, marker=None, tx=None, ty=None, ha="center", va="center"):
        """Событие: start — начальное, end — конечное, inter — промежуточное (граничное)."""
        ax = self.ax
        lw = {"start": 1.2, "end": 3.2, "inter": 1.2}[kind]
        ax.add_patch(Circle((x, y), r, fc="white", ec=LINE, lw=lw, zorder=5))
        if kind == "inter":
            ax.add_patch(Circle((x, y), r - 0.06, fc="white", ec=LINE, lw=1.0, zorder=6))
        if marker:
            self._marker(x, y, r, marker, kind == "end")
        if text:
            ax.text(x if tx is None else tx, (y - r - 0.45) if ty is None else ty, text, ha=ha, va=va,
                    fontsize=self.S - 1.5, zorder=6, style="italic", linespacing=1.05)
        return Box(x, y, 2 * r, 2 * r)

    def gateway(self, x, y, text=None, r=0.45, tx=None, ty=None, mark="x", ha="center"):
        ax = self.ax
        ax.add_patch(Polygon([(x - r, y), (x, y + r), (x + r, y), (x, y - r)], closed=True,
                             fc="white", ec=LINE, lw=1.2, zorder=5))
        if mark == "x":
            ax.plot([x - 0.15, x + 0.15], [y - 0.15, y + 0.15], color=LINE, lw=2.0, zorder=6)
            ax.plot([x - 0.15, x + 0.15], [y + 0.15, y - 0.15], color=LINE, lw=2.0, zorder=6)
        elif mark == "+":
            ax.plot([x - 0.2, x + 0.2], [y, y], color=LINE, lw=2.2, zorder=6)
            ax.plot([x, x], [y - 0.2, y + 0.2], color=LINE, lw=2.2, zorder=6)
        if text:
            ax.text(x if tx is None else tx, (y + r + 0.4) if ty is None else ty, text, ha=ha, va="center",
                    fontsize=self.S - 1.5, zorder=6, linespacing=1.05)
        return Box(x, y, 2 * r, 2 * r)

    def store(self, x, y, text):
        ax = self.ax
        w, h, e = 0.8, 0.75, 0.16
        ax.add_patch(Ellipse((x, y - h / 2), w, 2 * e, fc="white", ec=LINE, lw=1.2, zorder=4))
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=5))
        ax.plot([x - w / 2, x - w / 2], [y - h / 2, y + h / 2], color=LINE, lw=1.2, zorder=6)
        ax.plot([x + w / 2, x + w / 2], [y - h / 2, y + h / 2], color=LINE, lw=1.2, zorder=6)
        ax.add_patch(matplotlib.patches.Arc((x, y - h / 2), w, 2 * e, theta1=180, theta2=360, color=LINE, lw=1.2,
                                            zorder=6))
        ax.add_patch(Ellipse((x, y + h / 2), w, 2 * e, fc="white", ec=LINE, lw=1.2, zorder=6))
        ax.text(x, y - h / 2 - 0.22, text, ha="center", va="top", fontsize=self.S - 2.5, zorder=6, linespacing=1.05)
        return Box(x, y, w, h)

    def seq(self, pts, text=None, at=None):
        arrow(self.ax, pts, text, at, size=self.S - 1.5, lw=1.2, head=13)

    def msg(self, a, b, text=None, tx=None, ty=None, ha="left"):
        """Поток сообщений (вертикальный): пунктир, кружок в начале, полая стрелка в конце."""
        ax = self.ax
        (xa, ya), (xb, yb) = a, b
        sgn = 1 if yb > ya else -1
        hl, hw = 0.3, 0.14
        ax.plot([xa, xb], [ya, yb - sgn * hl], color=LINE, lw=1.1, ls=(0, (5, 3)), zorder=3)
        ax.add_patch(Circle((xa, ya + sgn * 0.08), 0.08, fc="white", ec=LINE, lw=1.0, zorder=6))
        ax.add_patch(Polygon([(xb, yb), (xb - hw, yb - sgn * hl), (xb + hw, yb - sgn * hl)], closed=True,
                             fc="white", ec=LINE, lw=1.0, zorder=6))
        if text:
            ax.text(xa + 0.18 if tx is None else tx, (ya + yb) / 2 if ty is None else ty, text, ha=ha,
                    va="center", fontsize=self.S - 1.5, style="italic", zorder=6, linespacing=1.05,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))

    def stores_under(self, t, items, y, step=1.3):
        """Под задачей t в ряд: хранилища [(текст, 'w'|'r'|'rw')] и прочие места (None);
        возвращает x каждого места."""
        n = len(items)
        xs = [t.x + (i - (n - 1) / 2) * step for i in range(n)]
        for x, it in zip(xs, items):
            if it is None:
                continue
            text, mode = it
            d = self.store(x, y, text)
            a, b = (min(max(x, t.l + 0.35), t.r - 0.35), t.b), (x, d.t + 0.17)
            data_assoc(self.ax, b if mode == "r" else a, a if mode == "r" else b, both=(mode == "rw"))
        return xs


def bpmn_choice(name, title, role, start, branches, top_pool=None, bottom_pool=None, lower_h=0.0, extra=None):
    """BPMN процесса из нескольких операций: начальное событие, шлюз «выбор операции», по каждой
    ветви — задача пользователя и сервисная задача с хранилищами и (необязательно) ошибкой.
    branches — снизу вверх: нижний ряд ведёт в левый столбец сервисных задач (лесенка без пересечений).
    Ветвь: dict(label, user, svc, stores, err, end, kind='service', msg_in, msg_out)."""
    W = 24.8
    base = 1.05 if bottom_pool else 0.1
    yD = base + lower_h + 1.5
    yS = yD + 2.25
    yL = yS + 1.4
    rows = [yL + 1.15 + 1.8 * i for i in range(len(branches))]
    top = rows[-1] + 1.2
    H = top + (0.95 if top_pool else 0.1)
    fig, ax = canvas(W, H, k=0.55)
    bp = BP(ax, W)
    bp.pool(base, top, title, [(role, yL, top), ("Система\n(СУБД, сервисы)", base, yL)])
    if top_pool:
        bp.black_pool(top + 0.15, H - 0.05, top_pool[0])
    if bottom_pool:
        bp.black_pool(0.05, base - 0.15, bottom_pool[0])
    rM = rows[len(rows) // 2]
    st = bp.event(2.4, rM, "start", start[0], marker=start[1] if len(start) > 1 else None)
    g = bp.gateway(4.25, rM, "Операция?", tx=4.5, ty=rM + 0.88, ha="left")
    bp.seq([st.right(), g.left()])
    xT, cols = 8.05, [10.55, 15.7, 20.85]
    res = {"st": st, "g": g, "yS": yS, "yD": yD, "yL": yL, "base": base, "top": top, "H": H, "bp": bp, "ax": ax}
    for i, (br, y, xs) in enumerate(zip(branches, rows, cols)):
        u = bp.task(xT, y, br["user"], w=3.1)
        if abs(y - rM) < 1e-6:
            bp.seq([g.right(), u.left()], br["label"], at=((g.r + u.l) / 2, y + 0.3))
        else:
            p0 = g.top() if y > rM else g.bottom()
            bp.seq([p0, (g.x, y), u.left()], br["label"], at=((g.x + u.l) / 2 + 0.15, y + 0.3))
        if br.get("custom"):          # ветвь продолжается в нижней полосе — рисует extra
            res[i] = (u, xs, y)
            continue
        s = bp.task(xs, yS, br["svc"], br.get("kind", "service"), w=br.get("w", 2.9), h=br.get("h", 1.35))
        bp.seq([u.right(), (xs, y), s.top()])
        e = bp.event(xs + 2.6, yS, "end", br["end"], marker="msg" if br.get("msg_out") else None,
                     ty=yS + 0.85)
        bp.seq([s.right(), e.left()])
        items = ([None] if br.get("err") else []) + list(br["stores"]) + ([None] if br.get("msg_in") else [])
        px = bp.stores_under(s, items, yD, step=1.3 if len(items) < 3 else 1.45 if len(items) > 3 else 1.5)
        if br.get("msg_in"):
            xm = px[-1]
            bp.msg((xm, base - 0.15), (xm, s.b), br["msg_in"], tx=xm + 0.15, ty=yD + 0.95)
        if br.get("err"):
            xe = px[0]
            bx = max(xe, s.l + 0.4)
            be = bp.event(bx, s.b, "inter", None, r=0.26, marker="error")
            ee = bp.event(xe, yD, "end", br["err"], tx=xe - 0.4, ty=yD, ha="right")
            bp.seq([be.bottom(), ee.top()] if bx == xe else [be.bottom(), (bx, yD), ee.right()])
        if br.get("msg_out"):
            bp.msg(e.bottom(), (e.x, base - 0.15), br["msg_out"], tx=e.x + 0.18, ty=yS - 1.25)
        res[i] = (u, s, e)
    if extra:
        extra(res)
    save(fig, name)


def bpmn_p1():
    bpmn_choice("bpmn_p1", "Регистрация пользователей", "Администратор", ("Кадровое\nсобытие",), [
        dict(label="приём", user="Принять\nучётную запись", svc="1.1 Записать\nпользователя",
             stores=[("D1\nПользователи", "w")], msg_in="учётная\nзапись", err="Отказ: почта\nзанята",
             end="Сотрудник\nдобавлен"),
        dict(label="изменение", user="Изменить\nданные", svc="1.2 Обновить\nданные",
             stores=[("D1\nПользователи", "rw")], end="Данные\nизменены"),
        dict(label="увольнение", user="Удалить\nсотрудника", svc="1.3 Удалить\nпользователя",
             stores=[("D1\nПользователи", "w")], err="Отказ: есть\nпроекты, часы", end="Сотрудник\nудалён"),
    ], bottom_pool=("Каталог сотрудников",))


def bpmn_p2():
    """Процесс 2. Создание проекта — в нижней полосе: шлюз «Заказчик в базе?» (2.5 — ведение заказчиков),
    затем транзакция create_project из отдельных сервисных задач 2.1 → 2.7 → 2.6."""
    def lower(r):
        bp, ax, base = r["bp"], r["ax"], r["base"]
        u, xs, y = r[0]
        yT, yD = base + 4.0, base + 1.5
        yH = yT + 1.55
        g1 = bp.gateway(2.7, yT, "Заказчик\nв базе?", tx=2.7, ty=yT - 1.05)
        bp.seq([u.right(), (xs, y), (xs, yH), (1.95, yH), (1.95, yT), g1.left()])
        t25 = bp.task(5.45, yT, "2.5 Записать\nзаказчика", "service", w=2.6)
        g2 = bp.gateway(8.1, yT, None, mark="x")
        bp.seq([g1.right(), t25.left()], "нет", at=(3.6, yT + 0.3))
        bp.seq([t25.right(), g2.left()])
        bp.seq([g1.top(), (g1.x, yT + 0.95), (g2.x, yT + 0.95), g2.top()], "да", at=(6.6, yT + 0.95))
        bp.stores_under(t25, [("D2\nЗаказчики", "w")], yD)
        # транзакция create_project (двойная рамка)
        tb = Box(15.25, yT + 0.15, 12.3, 2.3)
        for d, rs, lw in ((0.0, 0.25, 1.3), (0.1, 0.18, 1.0)):
            ax.add_patch(FancyBboxPatch((tb.l + d, tb.b + d), tb.w - 2 * d, tb.h - 2 * d,
                                        boxstyle=f"round,pad=0,rounding_size={rs}", fc="none", ec=LINE, lw=lw,
                                        zorder=3))
        ax.text(tb.l + 0.25, tb.t - 0.3, "Транзакция create_project", fontsize=bp.S - 2.5, style="italic",
                va="center", zorder=6)
        t21 = bp.task(11.3, yT, "2.1 Создать\nпроект", "service", w=2.7, h=1.25)
        t27 = bp.task(15.25, yT, "2.7 Привязать\nзаказчика", "service", w=2.7, h=1.25)
        t26 = bp.task(19.2, yT, "2.6 Оформить\nдоговор", "service", w=2.7, h=1.25)
        bp.seq([g2.right(), t21.left()])
        bp.seq([t21.right(), t27.left()])
        bp.seq([t27.right(), t26.left()])
        en = bp.event(22.75, yT, "end", "Проект\nсоздан", ty=yT + 0.9)
        bp.seq([t26.right(), en.left()])
        bp.stores_under(t21, [("D3\nПроекты", "w")], yD)
        bp.stores_under(t27, [("D2\nЗаказчики", "r"), ("D3\nПроекты", "w")], yD, step=1.4)
        bp.stores_under(t26, [("D4\nДоговоры", "w")], yD)
        be = bp.event(20.9, tb.b, "inter", None, r=0.26, marker="error")
        ee = bp.event(22.0, yD, "end", "Откат\nтранзакции", tx=22.4, ty=yD, ha="left")
        bp.seq([be.bottom(), (be.x, yD), ee.left()])
        bp.msg((r["st"].x, r["top"] + 0.15), r["st"].top(), "договор,\nзапрос", tx=r["st"].x + 0.18,
               ty=r["st"].y + 2.0)
    bpmn_choice("bpmn_p2", "Ведение проектов и договоров", "Руководитель\nпроекта", ("Запрос\nзаказчика", "msg"), [
        dict(label="новый", user="Ввести проект,\nзаказчика, договор", custom=True),
        dict(label="изменение", user="Изменить статус,\nсроки, владельца", svc="2.2, 2.3\nОбновить\nпроект",
             stores=[("D3\nПроекты", "rw")], end="Проект\nизменён"),
        dict(label="удаление", user="Удалить\nпроект", svc="2.4 Удалить\nпроект",
             stores=[("D3\nПроекты", "w")], err="Отказ: есть\nдоговор", end="Проект\nудалён"),
    ], top_pool=("Заказчик",), lower_h=5.9, extra=lower)


def bpmn_p3():
    bpmn_choice("bpmn_p3", "Управление составом", "Руководитель\nпроекта", ("Изменение\nкоманды",), [
        dict(label="добавление", user="Выбрать\nсотрудника, роль", svc="3.1 Добавить\nучастника",
             stores=[("D5\nУчастники", "w")], err="Отказ: уже\nв команде", end="Участник\nдобавлен"),
        dict(label="смена роли", user="Изменить\nроль", svc="3.2 Записать\nроль",
             stores=[("D5\nУчастники", "rw")], end="Роль\nизменена"),
        dict(label="исключение", user="Исключить\nучастника", svc="3.3 Исключить,\nснять задачи",
             stores=[("D5\nУчастники", "w"), ("D7\nЗадачи", "w")], end="Участник\nисключён"),
    ])


def bpmn_p5():
    bpmn_choice("bpmn_p5", "Обсуждение задач", "Участник\nпроекта", ("Нужно\nобсудить\nзадачу",), [
        dict(label="новый", user="Написать\nкомментарий", svc="5.1 Записать\nкомментарий",
             stores=[("D7\nЗадачи", "r"), ("D12\nКомментарии", "w")], err="Отказ:\nпустой текст",
             end="Участники\nуведомлены", msg_out="новый\nкомментарий"),
        dict(label="просмотр", user="Открыть\nобсуждение", svc="5.2 Выдать\nобсуждение",
             stores=[("D12\nКомментарии", "r")], end="Обсуждение\nпросмотрено"),
        dict(label="удаление", user="Удалить свой\nкомментарий", svc="5.3 Удалить\nкомментарий",
             stores=[("D12\nКомментарии", "w")], end="Комментарий\nудалён"),
    ], bottom_pool=("Сервис уведомлений",))


def bpmn_p6():
    def lower(r):
        bp, base = r["bp"], r["base"]
        yT, yD = base + 3.75, base + 1.55
        ts = bp.event(2.4, yT, "start", "еженедельно", marker="timer")
        t3 = bp.task(5.0, yT, "6.3 Отчёт\nо рисках", "service", w=2.6)
        t5 = bp.task(8.5, yT, "6.5 Отчёт\nпо договорам", "service", w=2.6)
        t4 = bp.task(12.0, yT, "6.4 Отчёт\nзаказчику", "service", w=2.6)
        en = bp.event(14.3, yT, "end", "Отчёт\nотправлен", marker="msg", tx=14.75, ty=yT + 0.1, ha="left")
        bp.seq([ts.right(), t3.left()])
        bp.seq([t3.right(), t5.left()])
        bp.seq([t5.right(), t4.left()])
        bp.seq([t4.right(), en.left()])
        bp.stores_under(t3, [("D3\nПроекты", "r"), ("D7\nЗадачи", "r")], yD)
        bp.stores_under(t5, [("D4\nДоговоры", "r"), ("D11\nТрудозатраты", "r")], yD, step=1.6)
        bp.stores_under(t4, [("D2\nЗаказчики", "r")], yD)
        bp.msg(en.bottom(), (en.x, base - 0.15), "отчёт\nзаказчику", tx=en.x + 0.18, ty=base + 1.5)
        r["ax"].plot([1.6, bp.x1], [base + 4.75] * 2, color=GREY, lw=0.8, ls=(0, (4, 3)), zorder=1)
    bpmn_choice("bpmn_p6", "Формирование отчётов", "Руководитель\nпроекта", ("Нужны\nданные\nо проекте",), [
        dict(label="перечни", user="Запросить\nперечень", svc="6.1 Выдать\nперечень",
             stores=[("D1\nПользователи", "r"), ("D7\nЗадачи", "r")], end="Перечень\nполучен"),
        dict(label="загрузка", user="Запросить\nзагрузку команды", svc="6.2 Анализ\nзагрузки",
             stores=[("D5\nУчастники", "r"), ("D12\nКомментарии", "r")], end="Загрузка\nполучена"),
        dict(label="показатели", user="Запросить\nпоказатели", svc="6.6 Рассчитать\nпоказатели",
             stores=[("D6\nСпринты", "r"), ("D10\nИстория", "r")], end="Показатели\nполучены"),
    ], bottom_pool=("Сервис уведомлений",), lower_h=4.8, extra=lower)


if __name__ == "__main__":
    context_diagram()
    dfd_diagram()
    dfd2_diagram()
    fdd_diagram()
    chen_diagram()
    quality_chen_diagram()
    bpmn_overview_diagram()
    bpmn_diagram()
    logical_diagram()
    arch_diagram()
    report_diagram()
    algo_diagram()
    env_diagram()
    components_diagram()
    for f in (dfd2_p1, dfd2_p2, dfd2_p3, dfd2_p5, dfd2_p6, bpmn_p1, bpmn_p2, bpmn_p3, bpmn_p5, bpmn_p6):
        f()
    print("готово:", OUT)
