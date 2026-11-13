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

Рисунки:
  context.png   — контекстная диаграмма (DFD уровня 0), нотация Гейна–Сарсона
  dfd.png       — DFD уровня 1
  fdd.png       — диаграмма декомпозиции функций
  chen.png      — ER-диаграмма в нотации Чена
  bpmn.png      — процессная модель BPMN «Выполнение задачи проекта»
  logical.png   — логическая модель данных (таблицы, ключи, связи)
  arch.png      — архитектура программного обеспечения
  report.png    — схема вычислений аналитического отчёта (report.sql)
  algo.png      — схема алгоритма самого медленного модуля (ГОСТ 19.701)

Запуск:  python3 diagrams.py
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams["font.family"] = "DejaVu Sans"

LINE = "#222222"
FILL_EXT = "#e8eef7"
FILL_PROC = "#fdf3e1"
FILL_STORE = "#eaf5ea"
FILL_ENT = "#d9e4f2"
GREY = "#555555"


# --------------------------------------------------------------------------
# общее
# --------------------------------------------------------------------------
def canvas(w, h, k=1.0):
    """Холст w × h условных единиц; физический размер — (w·k) × (h·k) дюймов.
    При k < 1 текст и линии становятся относительно крупнее."""
    fig = plt.figure(figsize=(w * k, h * k))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


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


def arrow(ax, pts, text=None, at=None, size=10, dashed=False, lw=1.3, head=16, color=LINE):
    """Ломаная pts со стрелкой на последней точке, подпись в точке at."""
    xs, ys = zip(*pts)
    ls = (0, (5, 3)) if dashed else "-"
    ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, zorder=3, ls=ls)
    ax.annotate(
        "", xy=pts[-1], xytext=pts[-2], zorder=4,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=head,
                        shrinkA=0, shrinkB=0, ls=ls),
    )
    if text:
        if at is None:
            (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
            at = ((x1 + x2) / 2, (y1 + y2) / 2)
        label(ax, at[0], at[1], text, size, color=("black" if color == LINE else color))


flow = arrow


def polyline(ax, pts, lw=1.2, color=LINE, **kw):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, zorder=3, **kw)


# --------------------------------------------------------------------------
# нотация Гейна–Сарсона
# --------------------------------------------------------------------------
def external(ax, box, text, size=12):
    ax.add_patch(Rectangle((box.l + 0.08, box.b - 0.08), box.w, box.h, fc="#9aa5b5", ec="none", zorder=1))
    ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_EXT, ec=LINE, lw=1.6, zorder=2))
    ax.text(box.x, box.y, text, ha="center", va="center", fontsize=size, weight="bold", zorder=5)


def process(ax, box, num, text, size=11, band=0.38, sub=None, color=None, sub_size=None):
    """Процесс Гейна–Сарсона: сверху полоса с номером, снизу (необязательно) — подсистема."""
    ax.add_patch(FancyBboxPatch((box.l, box.b), box.w, box.h,
                                boxstyle="round,pad=0,rounding_size=0.18",
                                fc=FILL_PROC, ec=LINE, lw=1.6, zorder=2))
    ax.plot([box.l, box.r], [box.t - band, box.t - band], color=LINE, lw=1.2, zorder=3)
    ax.text(box.x, box.t - band / 2, num, ha="center", va="center", fontsize=size, weight="bold",
            zorder=5, color=color or "black")
    if sub:
        ax.plot([box.l, box.r], [box.b + band, box.b + band], color=LINE, lw=0.9, zorder=3)
        ax.text(box.x, box.b + band / 2, sub, ha="center", va="center", fontsize=sub_size or size - 3,
                style="italic", color=color or GREY, zorder=5)
        mid = (box.b + band + box.t - band) / 2
    else:
        mid = (box.b + box.t - band) / 2
    ax.text(box.x, mid, text, ha="center", va="center", fontsize=size, zorder=5)


# подсистемы: номер процесса DFD → (название, цвет)
SUBS = {
    1: ("«Пользователи»", "#6a3d9a"),
    2: ("«Проекты»", "#1b7f5c"),
    3: ("«Проекты»", "#1b7f5c"),
    4: ("«Задачи»", "#1f5fbf"),
    5: ("«Обсуждения»", "#c25e00"),
    6: ("«Отчётность»", "#b0306a"),
}


def store(ax, box, sid, text, size=11, cell=0.55):
    ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_STORE, ec="none", zorder=1))
    ax.plot([box.r, box.l, box.l, box.r], [box.t, box.t, box.b, box.b], color=LINE, lw=1.6, zorder=3)
    ax.plot([box.l + cell, box.l + cell], [box.b, box.t], color=LINE, lw=1.2, zorder=3)
    ax.text(box.l + cell / 2, box.y, sid, ha="center", va="center", fontsize=size, weight="bold", zorder=5)
    ax.text(box.l + cell + (box.w - cell) / 2, box.y, text, ha="center", va="center", fontsize=size, zorder=5)


def gs_legend(ax, x, y, s=1.0, size=10):
    """Легенда нотации Гейна–Сарсона; s — масштаб геометрии."""
    w, h = 4.6 * s, 2.9 * s
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec="#888888", lw=1, zorder=1))
    ax.text(x + 0.15 * s, y - 0.3 * s, "Обозначения", fontsize=size, weight="bold", va="center")
    external(ax, Box(x + 0.7 * s, y - 0.85 * s, 0.9 * s, 0.42 * s), "", 8)
    ax.text(x + 1.4 * s, y - 0.85 * s, "внешняя сущность", fontsize=size, va="center")
    process(ax, Box(x + 0.7 * s, y - 1.5 * s, 0.9 * s, 0.6 * s), "", "", 6, band=0.18 * s)
    ax.text(x + 1.4 * s, y - 1.5 * s, "процесс", fontsize=size, va="center")
    store(ax, Box(x + 0.7 * s, y - 2.07 * s, 0.9 * s, 0.32 * s), "", "", 6, cell=0.22 * s)
    ax.text(x + 1.4 * s, y - 2.07 * s, "накопитель данных", fontsize=size, va="center")
    flow(ax, [(x + 0.25 * s, y - 2.55 * s), (x + 1.15 * s, y - 2.55 * s)])
    ax.text(x + 1.4 * s, y - 2.55 * s, "поток данных", fontsize=size, va="center")


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
    1: ("«Пользователи»", "#6a3d9a"),
    2: ("«Проекты»", "#1b7f5c"),
    3: ("«Проекты»", "#1b7f5c"),
    4: ("«Задачи»", "#1f5fbf"),
    5: ("«Обсуждения»", "#c25e00"),
    6: ("«Отчётность»", "#b0306a"),
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
    fig, ax = canvas(W, H, k=1.0)
    L, E = 8.5, 9.5            # кегль подписей потоков и внешних сущностей
    LW, HD, SH = 0.8, 9, 0.035  # толщина потока, наконечник, тень

    def ext(box, name, note=None):
        ax.add_patch(Rectangle((box.l + SH, box.b - SH), box.w, box.h, fc="#9aa5b5", ec="none", zorder=1))
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_EXT, ec=LINE, lw=1.0, zorder=2))
        if note is None:
            ax.text(box.x, box.y, name, ha="center", va="center", fontsize=E, weight="bold",
                    linespacing=1.15, zorder=5)
            return
        # блок «название + приписка» центрируется в рамке целиком
        h1 = (name.count("\n") + 1) * E * 1.15 / 72
        h2 = (note.count("\n") + 1) * (L - 1) * 1.15 / 72
        top = box.y + (h1 + 0.05 + h2) / 2
        ax.text(box.x, top, name, ha="center", va="top", fontsize=E, weight="bold",
                linespacing=1.15, zorder=5)
        ax.text(box.x, top - h1 - 0.05, note, ha="center", va="top", fontsize=L - 1, color=GREY,
                linespacing=1.15, zorder=5)

    def proc(box, num, text, band=0.3):
        ax.add_patch(FancyBboxPatch((box.l, box.b), box.w, box.h, boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=FILL_PROC, ec=LINE, lw=1.0, zorder=2))
        ax.plot([box.l, box.r], [box.t - band, box.t - band], color=LINE, lw=0.8, zorder=3)
        ax.text(box.x, box.t - band / 2, num, ha="center", va="center", fontsize=11, weight="bold", zorder=5)
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
    git = Box(XL, 1.05, BW, 0.85)
    ntf = Box(XR, 1.05, BW, 0.85)

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
    xm = (lead.r + p.l) / 2
    fl([lead.right(ys[0] - lead.y), (p.l, ys[0])]);  lab(xm, ys[0], "данные проекта")
    fl([lead.right(ys[1] - lead.y), (p.l, ys[1])]);  lab(xm, ys[1], "участник и роль")
    fl([lead.right(ys[2] - lead.y), (p.l, ys[2])]);  lab(xm, ys[2], "задача,\nисполнитель,\nсрок, метки")
    fl([(p.l, ys[3]), lead.right(ys[3] - lead.y)]);  lab(xm, ys[3], "отчёт о ходе\nпроекта")

    # ---------------------------------------------------------------- участник (справа)
    xm = (p.r + mem.l) / 2
    fl([(p.r, ys[0]), mem.left(ys[0] - mem.y)]);  lab(xm, ys[0], "назначенные\nзадачи")
    fl([mem.left(ys[1] - mem.y), (p.r, ys[1])]);  lab(xm, ys[1], "новый статус")
    fl([(p.r, ys[2]), mem.left(ys[2] - mem.y)]);  lab(xm, ys[2], "обсуждение")
    fl([mem.left(ys[3] - mem.y), (p.r, ys[3])]);  lab(xm, ys[3], "комментарий")

    # ---------------------------------------------------------------- Git и сервис уведомлений
    fl([git.right(), (2.95, git.y), (2.95, p.b)])
    lab((git.r + 2.95) / 2, git.y, "коммит с ключом\nзадачи (SHOP-42)")
    fl([(3.65, p.b), (3.65, ntf.y + 0.15), ntf.left(0.15)])
    lab((3.65 + ntf.l) / 2, ntf.y + 0.15, "назначение,\nэскалация")
    fl([(3.35, p.b), (3.35, ntf.y - 0.15), ntf.left(-0.15)])
    lab((3.35 + ntf.l) / 2, ntf.y - 0.15, "новый\nкомментарий", above=False)

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
    widths = [tw(t, weight="bold") if k == "title" else s + gap + tw(t) for k, t, s in items]
    total = sum(widths) + pad * (len(items) - 1)
    x = W / 2 - total / 2
    ax.add_patch(Rectangle((x - 0.15, ly - 0.17), total + 0.3, 0.34, fc="white", ec="#888888", lw=0.7, zorder=1))
    for (k, t, s), w in zip(items, widths):
        if k == "title":
            ax.text(x, ly, t, fontsize=L, weight="bold", va="center")
        else:
            if k == "ext":
                ax.add_patch(Rectangle((x + 0.02, ly - 0.11), s, 0.18, fc="#9aa5b5", ec="none", zorder=2))
                ax.add_patch(Rectangle((x, ly - 0.09), s, 0.18, fc=FILL_EXT, ec=LINE, lw=0.8, zorder=3))
            elif k == "proc":
                ax.add_patch(FancyBboxPatch((x, ly - 0.11), s, 0.22, boxstyle="round,pad=0,rounding_size=0.04",
                                            fc=FILL_PROC, ec=LINE, lw=0.8, zorder=3))
                ax.plot([x, x + s], [ly + 0.04, ly + 0.04], color=LINE, lw=0.6, zorder=4)
            else:
                arrow(ax, [(x, ly), (x + s, ly)], lw=LW, head=HD)
            ax.text(x + s + gap, ly, t, fontsize=L, va="center")
        x += w + pad

    save(fig, "context", dpi=300)


# --------------------------------------------------------------------------
# 2. DFD уровня 1
# --------------------------------------------------------------------------
def dfd_diagram():
    fig, ax = canvas(26.4, 16.3, k=0.56)
    S, L = 15, 13.5

    xs = [3.1, 7.9, 12.7, 17.5, 22.3]
    pw, ph = 3.9, 2.45
    sw, sh = 4.0, 1.25
    yE, yP, yD = 13.75, 9.0, 4.7

    adm = Box(xs[0], yE, 3.6, 1.3)
    cat = Box(xs[1], yE, 3.7, 1.3)
    lead = Box(xs[2], yE, 3.6, 1.3)
    git = Box(xs[3], yE, 3.3, 1.3)
    mem = Box(xs[4], yE, 3.9, 1.3)
    external(ax, adm, "Администратор", S)
    external(ax, cat, "Каталог\nсотрудников", S)
    external(ax, lead, "Руководитель\nпроекта", S)
    external(ax, git, "Git-хостинг", S)
    external(ax, mem, "Участник проекта\n(исполнитель)", S)

    names_p = ["Регистрация\nпользователей", "Ведение\nпроектов", "Управление\nсоставом\nпроекта",
               "Управление\nзадачами\nи метками", "Обсуждение\nзадач"]
    P = [Box(x, yP, pw, ph) for x in xs]
    for i, (b, n) in enumerate(zip(P, names_p), start=1):
        process(ax, b, str(i), n, S, band=0.45, sub=SUBS[i][0], color=SC(i), sub_size=11.5)
    p6 = Box(xs[2], 1.75, pw, 2.1)
    process(ax, p6, "6", "Формирование\nотчётов", S, band=0.45, sub=SUBS[6][0], color=SC(6), sub_size=11.5)

    names_d = ["Пользователи", "Проекты", "Участники\nпроектов", "Задачи\nи метки", "Комментарии"]
    D = [Box(x, yD, sw, sh) for x in xs]
    for i, (b, n) in enumerate(zip(D, names_d), start=1):
        store(ax, b, f"D{i}", n, S, cell=0.65)

    ntf = Box(xs[4], 1.7, 3.9, 1.5)
    external(ax, ntf, "Сервис\nуведомлений", S)

    # внешние сущности ↔ процессы
    flow(ax, [adm.bottom(-0.45), P[0].top(-0.45)], "данные\nпользователя", at=(xs[0] - 1.35, 11.4), size=L, color=SC(1))
    flow(ax, [P[0].top(0.45), adm.bottom(0.45)], "подтвер-\nждение", at=(xs[0] + 1.2, 11.75), size=L, color=SC(1))
    flow(ax, [cat.bottom(-0.9), P[0].top(1.35)], "учётные\nзаписи", at=(6.05, 11.25), size=L, color=SC(1))

    flow(ax, [lead.bottom(-1.1), P[1].top(0.75)], "данные\nпроекта", at=(10.0, 11.35), size=L, color=SC(2))
    flow(ax, [lead.bottom(0.0), P[2].top(0.0)], "участник\nи роль", at=(xs[2], 11.35), size=L, color=SC(3))
    flow(ax, [lead.bottom(1.1), P[3].top(-0.95)], "задача,\nисполни-\nтель, срок,\nметки", at=(15.05, 11.35), size=L, color=SC(4))

    flow(ax, [git.bottom(), P[3].top(0.0)], "коммит\nSHOP-42", at=(xs[3], 11.85), size=L, color=SC(4))
    flow(ax, [mem.bottom(-1.2), P[3].top(1.25)], "новый\nстатус", at=(20.85, 11.55), size=L, color=SC(4))
    flow(ax, [P[3].top(0.6), mem.bottom(-1.75)], "назна-\nченные\nзадачи", at=(19.25, 10.95), size=L, color=SC(4))
    flow(ax, [mem.bottom(0.15), P[4].top(0.15)], "коммен-\nтарий", at=(xs[4] + 0.15, 11.35), size=L, color=SC(5))
    flow(ax, [P[4].top(1.2), mem.bottom(1.2)], "обсуж-\nдение", at=(xs[4] + 1.6, 11.35), size=L, color=SC(5))

    # запись в накопители
    writes = ["новый\nпользователь", "проект", "участник,\nроль", "задача,\nстатус,\nметки", "коммен-\nтарий"]
    for i, (p, d, t) in enumerate(zip(P, D, writes), start=1):
        flow(ax, [p.bottom(), d.top()], t, at=(p.x, (p.b + d.t) / 2), size=L, color=SC(i))
    # чтение из соседнего накопителя
    reads = ["владелец", "проект", "участники", "задача"]
    for i, t in enumerate(reads):
        d, p = D[i], P[i + 1]
        a, b = (d.r - 0.15, d.t), (p.l + 0.15, p.b)
        flow(ax, [a, b], t, at=((a[0] + b[0]) / 2 + 0.25, (a[1] + b[1]) / 2 - 0.3), size=L, color=SC(i + 2))

    # отчёты
    flow(ax, [D[1].bottom(0.8), p6.left(0.4)], "проекты", at=(9.55, 2.95), size=L, color=SC(6))
    flow(ax, [D[2].bottom(), p6.top()], "участники", at=(xs[2], 3.45), size=L, color=SC(6))
    flow(ax, [D[3].bottom(-0.8), p6.right(0.4)], "задачи", at=(15.85, 2.95), size=L, color=SC(6))
    flow(ax, [p6.bottom(-0.6), (p6.x - 0.6, 0.2), (0.25, 0.2), (0.25, 15.75), (lead.x, 15.75), lead.top()],
         "отчёт о ходе проекта", at=(6.6, 15.75), size=L, color=SC(6))

    # уведомления
    flow(ax, [P[3].right(-0.7), (19.95, P[3].y - 0.7), (19.95, ntf.y + 0.3), ntf.left(0.3)],
         "назначение,\nэскалация", at=(19.95, 3.6), size=L, color=SC(4))
    flow(ax, [P[4].right(-0.7), (25.25, P[4].y - 0.7), (25.25, ntf.y), ntf.right()],
         "новый\nкоммен-\nтарий", at=(25.25, 3.1), size=L, color=SC(5))

    gs_legend(ax, 0.75, 3.75, s=1.0, size=12.5)
    save(fig, "dfd")


# --------------------------------------------------------------------------
# 3. Диаграмма декомпозиции функций
# --------------------------------------------------------------------------
def fdd_diagram():
    fig, ax = canvas(24.5, 10.2, k=0.58)
    S = 15

    def rect(box, text, fc, size, bold=False):
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=fc, ec=LINE, lw=1.4, zorder=2))
        ax.text(box.x, box.y, text, ha="center", va="center", fontsize=size,
                weight="bold" if bold else "normal", zorder=5)

    root = Box(12.25, 9.6, 9.0, 1.0)
    rect(root, "Система управления проектами", FILL_ENT, 17, True)

    funcs = [
        ("1. Управление\nпользователями",
         ["1.1. Регистрация", "1.2. Изменение\nданных", "1.3. Удаление"]),
        ("2. Управление\nпроектами",
         ["2.1. Создание,\nкод проекта", "2.2. Назначение\nвладельца", "2.3. Статус\nи сроки", "2.4. Удаление"]),
        ("3. Управление\nсоставом",
         ["3.1. Добавление\nучастника", "3.2. Назначение\nроли", "3.3. Исключение\nучастника"]),
        ("4. Управление\nзадачами",
         ["4.1. Создание\nи оценка", "4.2. Назначение\nисполнителя", "4.3. Статус\nи приоритет",
          "4.4. Удаление", "4.5. Метки"]),
        ("5. Обсуждение\nзадач",
         ["5.1. Добавление\nкомментария", "5.2. Просмотр\nобсуждения", "5.3. Удаление\nкомментария"]),
        ("6. Формирование\nотчётов",
         ["6.1. Запросы\nпо операциям", "6.2. Агрегаты\nи подзапросы", "6.3. Отчёт\nо рисках"]),
    ]

    xs = [2.15 + i * 4.04 for i in range(6)]
    bus_y, fy = 8.65, 7.75
    ax.plot([root.x, root.x], [root.b, bus_y], color=LINE, lw=1.4)
    ax.plot([xs[0], xs[-1]], [bus_y, bus_y], color=LINE, lw=1.4)

    for x, (name, subs) in zip(xs, funcs):
        f = Box(x, fy, 3.85, 1.15)
        ax.plot([x, x], [bus_y, f.t], color=LINE, lw=1.4)
        rect(f, name, FILL_PROC, S, True)
        spine = f.l + 0.22
        ys = [6.35 - k * 1.35 for k in range(len(subs))]
        ax.plot([spine, spine], [f.b, ys[-1]], color=LINE, lw=1.2)
        for y, s in zip(ys, subs):
            sb = Box(spine + 0.25 + 3.38 / 2, y, 3.38, 1.05)
            ax.plot([spine, sb.l], [y, y], color=LINE, lw=1.2)
            rect(sb, s, "white", 14)

    save(fig, "fdd")


# --------------------------------------------------------------------------
# 4. ER-диаграмма в нотации Чена
# --------------------------------------------------------------------------
def chen_diagram():
    K = 0.5
    DY = 2.4
    fig, ax = canvas(23.5, 18.9, k=K)
    renderer = fig.canvas.get_renderer()
    AS = 12.5       # кегль атрибутов

    def entity(box, name, table):
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_ENT, ec=LINE, lw=1.8, zorder=4))
        ax.text(box.x, box.y + 0.17, name, ha="center", va="center", fontsize=14, weight="bold", zorder=6)
        ax.text(box.x, box.y - 0.3, f"({table})", ha="center", va="center", fontsize=12, color="#333333", zorder=6)

    def attr(x, y, text, ent, key=False):
        ax.plot([x, ent.x], [y, ent.y], color=LINE, lw=1.0, zorder=1)
        w = max(1.7, 0.095 * len(text) / K + 0.55)
        ax.add_patch(Ellipse((x, y), w, 0.78, fc="white", ec=LINE, lw=1.2, zorder=4))
        t = ax.text(x, y, text, ha="center", va="center", fontsize=AS, zorder=6)
        if key:
            bb = t.get_window_extent(renderer=renderer).transformed(ax.transData.inverted())
            ax.plot([bb.x0, bb.x1], [bb.y0 + 0.01, bb.y0 + 0.01], color=LINE, lw=1.1, zorder=6)

    def rel(x, y, text, w=2.9, h=1.45):
        ax.add_patch(Polygon([(x - w / 2, y), (x, y + h / 2), (x + w / 2, y), (x, y - h / 2)],
                             closed=True, fc=FILL_PROC, ec=LINE, lw=1.6, zorder=4))
        ax.text(x, y, text, ha="center", va="center", fontsize=12.5, weight="bold", zorder=6)
        return (x, y)

    def link(a, b, total=False):
        (x1, y1), (x2, y2) = a, b
        if not total:
            ax.plot([x1, x2], [y1, y2], color=LINE, lw=1.4, zorder=2)
            return
        dx, dy = x2 - x1, y2 - y1
        n = (dx ** 2 + dy ** 2) ** 0.5
        ox, oy = -dy / n * 0.06, dx / n * 0.06
        for s in (1, -1):
            ax.plot([x1 + s * ox, x2 + s * ox], [y1 + s * oy, y2 + s * oy], color=LINE, lw=1.3, zorder=2)

    def card(x, y, text):
        ax.text(x, y, text, ha="center", va="center", fontsize=16, weight="bold", color="#b03030", zorder=7)

    U = Box(4.3, 8.4 + DY, 4.3, 1.2)
    P = Box(15.6, 12.3 + DY, 3.3, 1.2)
    T = Box(15.6, 5.2 + DY, 3.3, 1.2)
    C = Box(7.6, 2.3 + DY, 4.0, 1.2)
    M = Box(15.6, 1.35, 3.3, 1.2)
    entity(U, "ПОЛЬЗОВАТЕЛЬ", "users")
    entity(P, "ПРОЕКТ", "projects")
    entity(T, "ЗАДАЧА", "tasks")
    entity(C, "КОММЕНТАРИЙ", "comments")
    entity(M, "МЕТКА", "marks")

    own = rel(9.9, 13.3 + DY, "ВЛАДЕЕТ")
    link(U.top(0.6), own)
    link(own, P.left(0.25), total=True)
    card(5.55, 9.6 + DY, "1")
    card(13.55, 12.95 + DY, "N")

    part = rel(9.9, 10.55 + DY, "УЧАСТВУЕТ", w=3.3)
    link(U.right(0.3), part)
    link(part, P.left(-0.25))
    card(6.75, 9.1 + DY, "M")
    card(13.55, 11.65 + DY, "N")
    attr(8.55, 9.0 + DY, "role", Box(*part, 0, 0))
    attr(11.3, 9.0 + DY, "joined_at", Box(*part, 0, 0))

    cont = rel(15.6, 8.75 + DY, "СОДЕРЖИТ", w=3.1)
    link(P.bottom(), cont)
    link(cont, T.top(), total=True)
    card(16.0, 11.35 + DY, "1")
    card(16.0, 6.15 + DY, "N")

    execs = rel(10.0, 6.4 + DY, "ИСПОЛНЯЕТ", w=3.3)
    link(U.right(-0.3), execs)
    link(execs, T.left(0.2))
    card(6.75, 7.6 + DY, "1")
    card(13.55, 5.8 + DY, "N")

    has = rel(12.0, 2.3 + DY, "ОТНОСИТСЯ\nК", w=3.0, h=1.6)
    link(T.bottom(-0.6), has)
    link(has, C.right(), total=True)
    card(14.3, 4.5 + DY, "1")
    card(10.05, 2.75 + DY, "N")

    writes = rel(4.3, 4.85 + DY, "ПИШЕТ")
    link(U.bottom(), writes)
    link(writes, C.left(0.2), total=True)
    card(4.65, 7.5 + DY, "1")
    card(5.3, 3.1 + DY, "N")

    tag = rel(15.6, 3.85, "ПОМЕЧЕНА", w=3.2)
    link(T.bottom(), tag)
    link(tag, M.top())
    card(16.0, 6.0, "M")
    card(16.0, 2.25, "N")
    attr(12.75, 3.05, "date", Box(*tag, 0, 0))

    for (x, y, t, k) in [(1.2, 10.85, "user_id", True), (1.15, 9.4, "full_name", False),
                         (1.0, 7.75, "email", False), (1.25, 6.2, "created_at", False)]:
        attr(x, y + DY, t, U, k)

    for (x, y, t, k) in [(12.4, 14.85, "project_id", True), (14.55, 15.6, "name", False),
                         (16.75, 15.6, "code", False), (19.1, 15.15, "description", False),
                         (20.6, 13.75, "status", False), (21.0, 12.35, "start_date", False),
                         (20.6, 10.95, "end_date", False)]:
        attr(x, y + DY, t, P, k)

    for (x, y, t, k) in [(19.15, 8.75, "task_id", True), (20.75, 7.85, "title", False),
                         (21.45, 6.9, "description", False), (21.65, 5.95, "status", False),
                         (21.65, 5.0, "priority", False), (21.45, 4.05, "created_at", False),
                         (21.0, 3.1, "due_date", False), (20.4, 2.15, "estimate_hours", False),
                         (19.6, 1.2, "completed_at", False)]:
        attr(x, y + DY, t, T, k)

    for (x, y, t, k) in [(4.6, 0.85, "comment_id", True), (7.6, 0.6, "body", False),
                         (10.6, 0.85, "created_at", False)]:
        attr(x, y + DY, t, C, k)

    for (x, y, t, k) in [(12.35, 0.55, "mark_id", True), (12.6, 1.95, "name", False),
                         (19.0, 0.55, "color", False)]:
        attr(x, y, t, M, k)

    save(fig, "chen")


# --------------------------------------------------------------------------
# 5. BPMN «Выполнение задачи проекта»
# --------------------------------------------------------------------------
def bpmn_diagram():
    import math
    W, H = 27.0, 12.7
    fig, ax = canvas(W, H, k=0.6)
    S = 12

    x0, x1 = 0.1, W - 0.1
    lanes = [("Руководитель\nпроекта", 10.0, 12.6), ("Исполнитель", 7.4, 10.0), ("Тестировщик", 5.0, 7.4),
             ("Система\n(СУБД, сервисы)", 0.1, 5.0)]
    ax.add_patch(Rectangle((x0, 0.1), x1 - x0, 12.5, fc="none", ec=LINE, lw=1.8, zorder=1))
    ax.plot([x0 + 0.6, x0 + 0.6], [0.1, 12.6], color=LINE, lw=1.5)
    ax.text(x0 + 0.3, 6.35, "Выполнение задачи проекта", rotation=90, ha="center", va="center",
            fontsize=S + 1, weight="bold")
    for name, lo, hi in lanes:
        ax.plot([x0 + 0.6, x1], [lo, lo], color=LINE, lw=1.3)
        ax.plot([x0 + 1.5, x0 + 1.5], [lo, hi], color=LINE, lw=1.2)
        ax.text(x0 + 1.05, (lo + hi) / 2, name, rotation=90, ha="center", va="center", fontsize=S)
    ax.add_patch(Rectangle((x0 + 1.5, 0.1), x1 - x0 - 1.5, 4.9, fc="#f3f6fb", ec="none", zorder=0))

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
        fc = "#fffbe6" if kind == "user" else "#e6eefb"
        ax.add_patch(FancyBboxPatch((b.l, b.b), w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                    fc=fc, ec=LINE, lw=1.5, zorder=4))
        (user_icon if kind == "user" else gear_icon)(b.l + 0.25, b.t - 0.25)
        ax.text(x + 0.15, y - 0.08, text, ha="center", va="center", fontsize=S - 1.5, zorder=6, linespacing=1.12)
        return b

    def event(x, y, kind, text, r=0.3, tx=None, ty=None, ha="center"):
        lw = {"start": 1.5, "end": 4.0, "inter": 1.5}[kind]
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
                             fc="white", ec=LINE, lw=1.5, zorder=5))
        ax.plot([x - 0.15, x + 0.15], [y - 0.15, y + 0.15], color=LINE, lw=2.2, zorder=6)
        ax.plot([x - 0.15, x + 0.15], [y + 0.15, y - 0.15], color=LINE, lw=2.2, zorder=6)
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
        ax.text(x, y - h / 2 - 0.3, text, ha="center", va="center", fontsize=S - 2, zorder=6)
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
        arrow(ax, pts, text, at, size=S - 1.5, lw=1.4, head=14)

    yR, yE, yT, yS, yD = 11.3, 8.7, 6.2, 3.65, 1.25
    c = [2.45, 4.6, 7.0, 9.4, 11.8, 14.4, 17.0, 19.4, 22.0, 24.4]

    st = event(c[0], yR, "start", "Потребность\nв работе", ty=yR + 0.75)
    r1 = task(c[1], yR, "Создать\nзадачу")
    s1 = task(c[1], yS, "4.1 Записать\nзадачу [todo]", "service")
    g1 = gateway(c[2], yR, "Задача\nактуальна?")
    s7 = task(c[2], yS, "4.4 Удалить\nзадачу", "service", w=1.95)
    r2 = task(c[3], yR, "Оценить,\nназначить\nисполнителя,\nсрок, метки", h=1.55)
    s2 = task(c[3], yS, "4.2 Записать\nназначение,\nуведомить", "service")
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
    en3 = event(c[6] + 0.3, yR, "end", "Приоритет\nповышен", ty=yR - 0.95)

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
    seq([r3.right(), en3.left()])

    # хранилища данных и электронные документы
    for t in (s1, s2, s3, s4, s6):
        d = store(t.x, yD, "D4")
        assoc(t.bottom(), d.top())
    d5 = store(s5.x, yD, "D5")
    assoc(s5.bottom(), d5.top())
    for t, x, txt in ((s1, c[1] + 1.05, "Карточка\nзадачи"), (s2, c[3] + 1.05, "Уведомление\nисполнителю"),
                      (s4, c[6] + 1.05, "Уведомление\nтестировщику")):
        dd = doc(x, yD + 0.05, txt)
        assoc(t.right(-0.45), (dd.x - 0.1, dd.t))

    save(fig, "bpmn")


# --------------------------------------------------------------------------
# 6. Логическая модель данных
# --------------------------------------------------------------------------
def logical_diagram():
    W, H = 17.3, 12.0
    fig, ax = canvas(W, H, k=0.7)
    S = 12
    RH, HH, TW = 0.42, 0.55, 3.3

    T = {}

    def table(name, x, top, rows):
        h = HH + RH * len(rows)
        ax.add_patch(Rectangle((x, top - h), TW, h, fc="white", ec=LINE, lw=1.6, zorder=3))
        ax.add_patch(Rectangle((x, top - HH), TW, HH, fc=FILL_ENT, ec=LINE, lw=1.6, zorder=3))
        ax.text(x + TW / 2, top - HH / 2, name, ha="center", va="center", fontsize=S + 1, weight="bold", zorder=5)
        ax.plot([x + 0.85, x + 0.85], [top - h, top - HH], color=LINE, lw=0.8, zorder=4)
        for i, (k, a) in enumerate(rows):
            y = top - HH - RH * (i + 0.5)
            ax.text(x + 0.42, y, k, ha="center", va="center", fontsize=S - 2, weight="bold", zorder=5,
                    color="#8a1c1c" if "PK" in k else "#1c3f8a")
            ax.text(x + 1.0, y, a, ha="left", va="center", fontsize=S, zorder=5,
                    weight="bold" if "PK" in k else "normal")
            if i:
                ax.plot([x, x + TW], [y + RH / 2, y + RH / 2], color="#bbbbbb", lw=0.5, zorder=4)
        T[name] = Box(x + TW / 2, top - h / 2, TW, h)

    c1, c2, c3, c4 = 0.3, 4.7, 9.1, 13.7
    top1, top2 = 11.6, 6.6
    table("users", c1, top1, [("PK", "user_id"), ("", "full_name"), ("U", "email"), ("", "created_at")])
    table("project_members", c2, top1, [("PK, FK", "project_id"), ("PK, FK", "user_id"),
                                        ("", "role"), ("", "joined_at")])
    table("projects", c3, top1, [("PK", "project_id"), ("U", "name"), ("U", "code"), ("", "description"),
                                 ("FK", "owner_id"), ("", "status"), ("", "start_date"), ("", "end_date")])
    table("marks", c4, top1, [("PK", "mark_id"), ("U", "name"), ("", "color")])
    table("comments", c1, top2, [("PK", "comment_id"), ("FK", "task_id"), ("FK", "author_id"),
                                 ("", "body"), ("", "created_at")])
    table("tasks", c3, top2, [("PK", "task_id"), ("FK, U", "project_id"), ("FK", "assignee_id"),
                              ("U", "title"), ("", "description"), ("", "status"), ("", "priority"),
                              ("", "created_at"), ("", "due_date"), ("", "estimate_hours"), ("", "completed_at")])
    table("marks_tasks", c4, top2, [("PK, FK", "mark_id"), ("PK, FK", "task_id"), ("", "date")])

    def card(x, y, t):
        ax.text(x, y, t, fontsize=S, weight="bold", color="#b03030", ha="center", va="center", zorder=6)

    def rule(x, y, t):
        ax.text(x, y, t, fontsize=S - 2.5, color=GREY, ha="center", va="center", zorder=6, style="italic",
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))

    def rel(pts, one, many, rule_xy, text):
        polyline(ax, pts, lw=1.3)
        card(*one, "1")
        card(*many, "N")
        rule(*rule_xy, text)

    U, PM, P, MK = T["users"], T["project_members"], T["projects"], T["marks"]
    C, TK, MT = T["comments"], T["tasks"], T["marks_tasks"]

    y = PM.y + 0.25
    rel([(PM.l, y), (U.r, y)], (U.r + 0.18, y + 0.22), (PM.l - 0.2, y + 0.22), ((U.r + PM.l) / 2, y - 0.3), "CASCADE")
    rel([(PM.r, y), (P.l, y)], (P.l - 0.18, y + 0.22), (PM.r + 0.2, y + 0.22), ((PM.r + P.l) / 2, y - 0.3), "CASCADE")
    # projects.owner_id → users: поверх таблиц
    yt = top1 + 0.3
    rel([(P.x + 0.9, P.t), (P.x + 0.9, yt), (U.x, yt), (U.x, U.t)], (U.x + 0.2, U.t + 0.12),
        (P.x + 1.1, P.t + 0.12), (8.4, yt), "RESTRICT")
    # tasks.project_id → projects
    rel([(TK.x, TK.t), (TK.x, P.b)], (TK.x + 0.2, P.b - 0.2), (TK.x + 0.2, TK.t + 0.2),
        (TK.x, (TK.t + P.b) / 2), "CASCADE")
    # tasks.assignee_id → users
    ya = TK.t - 0.75
    rel([(TK.l, ya), (U.r + 0.55, ya), (U.r + 0.55, U.b + 0.35), (U.r, U.b + 0.35)],
        (U.r + 0.18, U.b + 0.57), (TK.l - 0.2, ya + 0.22), (6.8, ya), "SET NULL")
    # comments.author_id → users
    rel([(U.x, C.t), (U.x, U.b)], (U.x + 0.2, U.b - 0.2), (U.x + 0.2, C.t + 0.2), (U.x, (C.t + U.b) / 2), "RESTRICT")
    # comments.task_id → tasks
    yc = C.y - 0.2
    rel([(C.r, yc), (TK.l, yc)], (TK.l - 0.18, yc + 0.22), (C.r + 0.2, yc + 0.22), (6.8, yc), "CASCADE")
    # marks_tasks.task_id → tasks, marks_tasks.mark_id → marks
    ym = MT.y
    rel([(MT.l, ym), (TK.r, ym)], (TK.r + 0.18, ym + 0.22), (MT.l - 0.2, ym + 0.22), ((TK.r + MT.l) / 2, ym - 0.3), "CASCADE")
    rel([(MT.x, MT.t), (MT.x, MK.b)], (MT.x + 0.2, MK.b - 0.2), (MT.x + 0.2, MT.t + 0.2),
        (MT.x, (MT.t + MK.b) / 2), "RESTRICT")

    lx, ly, lw_ = c2 - 0.1, 3.3, 4.2
    ax.add_patch(Rectangle((lx, ly - 2.85), lw_, 2.85, fc="white", ec="#888888", lw=1, zorder=1))
    items = [("PK", "первичный ключ", "#8a1c1c"), ("FK", "внешний ключ", "#1c3f8a"),
             ("U", "входит в UNIQUE", "#1c3f8a")]
    for i, (k, t, col) in enumerate(items):
        ax.text(lx + 0.4, ly - 0.35 - i * 0.48, k, fontsize=S - 2, weight="bold", color=col, ha="center", va="center")
        ax.text(lx + 0.85, ly - 0.35 - i * 0.48, t, fontsize=S - 1, va="center")
    ax.text(lx + 0.2, ly - 1.95, "1, N — кардинальность", fontsize=S - 1, va="center")
    ax.text(lx + 0.2, ly - 2.45, "курсив — правило ON DELETE", fontsize=S - 1, va="center", style="italic")

    save(fig, "logical")


# --------------------------------------------------------------------------
# 7. Архитектура ПО
# --------------------------------------------------------------------------
def arch_diagram():
    W, H = 16.6, 12.6
    fig, ax = canvas(W, H, k=0.6)
    S = 12.5

    def box(b, text, fc="white", size=S, bold=False, ec=LINE, lw=1.4, ls="-", va_top=False, round_=True):
        style = "round,pad=0,rounding_size=0.15" if round_ else "square,pad=0"
        ax.add_patch(FancyBboxPatch((b.l, b.b), b.w, b.h, boxstyle=style, fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
        if text:
            if va_top:
                ax.text(b.x, b.t - 0.3, text, ha="center", va="center", fontsize=size,
                        weight="bold" if bold else "normal", zorder=5)
            else:
                ax.text(b.x, b.y, text, ha="center", va="center", fontsize=size,
                        weight="bold" if bold else "normal", zorder=5, linespacing=1.2)

    env = Box(6.55, 5.6, 12.7, 11.0)
    box(env, None, fc="#f6f6f6", ec="#777777", lw=1.2, ls=(0, (6, 3)), round_=False)
    ax.text(env.x, env.t - 0.3, "Узел системы: ОС Ubuntu 24.04", fontsize=S - 1.5, style="italic",
            color="#333333", va="center", ha="center")

    for t, x in [("Администратор\nБД", 2.2), ("Руководитель\nпроекта", 6.55), ("Участник\nпроекта", 10.9)]:
        box(Box(x, 11.95, 3.3, 1.0), t, fc=FILL_EXT, bold=True, size=S - 0.5)
        arrow(ax, [(x, 11.45), (x, 9.95)], lw=1.4)

    cl = Box(6.55, 8.75, 12.2, 2.4)
    box(cl, "Клиентский уровень", fc="#eef4fb", bold=True, va_top=True)
    box(Box(2.4, 8.4, 3.6, 1.3), "Клиент psql,\npgAdmin", size=S - 1)
    box(Box(6.4, 8.4, 3.8, 1.3), "SQL-модули\n(сценарии *.sql)", size=S - 1)
    integ = Box(10.55, 8.4, 3.9, 1.3)
    box(integ, "Модуль интеграции\n(веб-хуки, рассылка)", size=S - 1)

    sv = Box(6.55, 4.95, 12.2, 4.6)
    box(sv, "Сервер СУБД PostgreSQL 16", fc=FILL_PROC, bold=True, va_top=True)
    comps = [("Обработка\nзапросов", 1.95), ("Транзакции\n(MVCC)", 4.95), ("Контроль\nцелостности", 8.0),
             ("Планировщик\n(pg_cron)", 11.05)]
    for t, x in comps:
        box(Box(x, 5.85, 2.75, 1.45), t, size=S - 1.5)
    db = Box(6.55, 3.45, 11.4, 1.25)
    box(db, "База данных project_db: 7 таблиц, 33 ограничения, индексы", fc=FILL_STORE, size=S - 1)
    for t, x in comps:
        arrow(ax, [(x, 5.12), (x, db.t)], lw=1.1)
    for x in (2.4, 6.4, 10.55):
        arrow(ax, [(x, 7.75), (x, sv.t)], lw=1.3)
    ax.text(8.45, 7.38, "SQL, порт 5432", fontsize=S - 2.5, style="italic",
            ha="center", va="center", bbox=dict(boxstyle="round,pad=0.1", fc="#f6f6f6", ec="none"), zorder=6)

    fs = Box(6.55, 1.05, 12.2, 1.0)
    box(fs, "Файловая система: каталог данных PostgreSQL (таблицы, индексы, журнал WAL)", size=S - 1.5)
    arrow(ax, [(6.55, sv.b), (6.55, fs.t)], lw=1.3)

    ext = [("Каталог\nсотрудников (SSO)", 10.15), ("Git-хостинг", 8.6), ("Сервис\nуведомлений", 7.05)]
    for t, y in ext:
        external(ax, Box(14.95, y, 3.1, 1.15), t, S - 1.5)
    arrow(ax, [(13.4, 10.15), (integ.r, integ.y + 0.4)], lw=1.3)
    arrow(ax, [(13.4, 8.6), (integ.r, integ.y)], lw=1.3)
    arrow(ax, [(integ.r, integ.y - 0.4), (13.4, 7.05)], lw=1.3)
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
                                    fc=fc, ec=LINE, lw=1.4, zorder=3))
        ax.text(b.x, b.y + (0.2 if sub else 0), title, ha="center", va="center", fontsize=S, weight="bold", zorder=5)
        if sub:
            ax.text(b.x, b.y - 0.28, sub, ha="center", va="center", fontsize=S - 2.5, zorder=5, color="#333333")

    for t, x in [("Исходные данные", 1.75), ("Промежуточные\nпоказатели", 5.6), ("Агрегация", 9.9),
                 ("Итоговый отчёт", 14.6)]:
        ax.text(x, 7.25, t, ha="center", va="center", fontsize=S, weight="bold", color="#333333")
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
    rp = Box(14.6, 4.1, 4.2, 4.3)
    node(rp, "report", None, FILL_ENT)
    ax.text(rp.x, rp.y - 0.75, "прогресс, %;\nтемп, ч/нед\nна человека;\nуровень риска", ha="center",
            va="center", fontsize=S - 2, zorder=5, color="#333333")

    A = dict(lw=1.3, head=14)
    arrow(ax, [src["params"].right(), (tf.l, tf.y + 0.5)], **A)
    arrow(ax, [src["tasks"].right(), tf.left()], **A)
    arrow(ax, [src["projects"].right(), (tf.l, tf.y - 0.5)], **A)
    arrow(ax, [tf.right(0.35), ps.left()], **A)
    arrow(ax, [tf.right(-0.35), al.left()], **A)
    arrow(ax, [al.bottom(), bn.top()], **A)
    arrow(ax, [src["project_members"].right(), tm.left()], **A)
    arrow(ax, [ps.right(), (rp.l, rp.y + 1.6)], **A)
    arrow(ax, [bn.right(), (rp.l, bn.y)], **A)
    arrow(ax, [tm.right(), (rp.l, rp.y - 1.6)], **A)
    arrow(ax, [src["projects · users"].right(), (rp.x, src["projects · users"].y), rp.bottom()], **A)
    ax.text(8.2, 1.25, "LEFT JOIN: проекты без задач тоже попадают в отчёт", fontsize=S - 2.5,
            ha="center", style="italic", color="#333333")

    save(fig, "report")


# --------------------------------------------------------------------------
# 9. Схема алгоритма самого медленного модуля (ГОСТ 19.701-90)
# --------------------------------------------------------------------------
def algo_diagram():
    W, H = 10.0, 15.6
    fig, ax = canvas(W, H, k=0.62)
    S = 13
    X, BW = 5.0, 7.0

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
    b1 = proc(13.6, "Соединить tasks, projects, users, comments:\nактивные проекты, задача не done,\n"
                    "исполнитель назначен", h=1.5)
    b2 = loop(11.95, "Цикл по парам\n«задача t — комментарий c»", top=True)
    b3 = proc(10.3, "Подзапрос: последняя дата\nкомментария задачи t\nmax(c2.created_at), c2.task_id = t.task_id",
              h=1.55)
    b4 = decision(8.15, "c.created_at = последняя\nи автор c ≠\nисполнитель t?")
    b5 = proc(5.95, "Добавить строку: проект, задача,\nисполнитель, автор, текст,\nдней без ответа", h=1.5)
    b6 = loop(4.3, "Конец цикла", top=False)
    b7 = proc(2.75, "Упорядочить по числу\nдней без ответа (по убыванию)", h=1.15)
    b8 = terminator(1.35, "Конец")

    for a, b in [(b0, b1), (b1, b2), (b2, b3), (b3, b4), (b4, b5), (b5, b6), (b6, b7), (b7, b8)]:
        line(a.bottom(), b.top())
    ax.text(X + 0.25, b4.b - 0.3, "да", fontsize=S, va="center")
    # «нет» — в обход блока добавления к концу цикла
    pts = [b4.right(), (9.3, b4.y), (9.3, 5.0), (X, 5.0)]
    polyline(ax, pts, lw=1.4)
    ax.text(b4.r + 0.15, b4.y + 0.3, "нет", fontsize=S, va="center")
    ax.text(0.15, 10.3, "выполняется\nдля каждой\nстроки", fontsize=S - 2.5, va="center", style="italic",
            color="#333333")

    save(fig, "algo")


# --------------------------------------------------------------------------
# Окружение системы и компонентное представление
# --------------------------------------------------------------------------
def env_diagram():
    W, H = 19.6, 12.8
    fig, ax = canvas(W, H, k=0.62)
    S = 12.5

    def svc(b, t, sub):
        ax.add_patch(Rectangle((b.l + 0.08, b.b - 0.08), b.w, b.h, fc="#9aa5b5", ec="none", zorder=1))
        ax.add_patch(Rectangle((b.l, b.b), b.w, b.h, fc="#e7f3ef", ec=LINE, lw=1.6, zorder=2))
        ax.add_patch(Rectangle((b.l + 0.1, b.b + 0.1), b.w - 0.2, b.h - 0.2, fc="none", ec=LINE, lw=0.9, zorder=2))
        ax.text(b.x, b.y + 0.2, t, ha="center", va="center", fontsize=S, weight="bold", zorder=5)
        ax.text(b.x, b.y - 0.3, sub, ha="center", va="center", fontsize=S - 2.5, color=GREY, zorder=5)

    lead = Box(1.9, 9.9, 3.4, 1.3)
    mem = Box(1.9, 3.6, 3.4, 1.3)
    external(ax, lead, "Руководитель\nпроекта", S)
    external(ax, mem, "Участник\nпроекта", S)
    cat = Box(7.55, 11.0, 4.3, 1.25)
    ntf = Box(7.55, 6.7, 4.3, 1.25)
    git = Box(7.55, 1.55, 4.3, 1.25)
    svc(cat, "Каталог сотрудников", "SSO, учётные записи")
    svc(ntf, "Сервис уведомлений", "почта, мессенджер, календарь")
    svc(git, "Git-хостинг", "репозитории проектов")

    sysb = Box(15.3, 6.6, 8.2, 11.4)
    ax.add_patch(FancyBboxPatch((sysb.l, sysb.b), sysb.w, sysb.h, boxstyle="round,pad=0,rounding_size=0.3",
                                fc="#f7f9fd", ec="#1d3a8a", lw=2.2, zorder=1))
    ax.text(sysb.l + 0.25, sysb.t - 0.42, "0   Система управления проектами", fontsize=S + 0.5, weight="bold",
            va="center", zorder=5)

    p1 = Box(13.9, 10.2, 3.3, 1.6)
    p4 = Box(13.9, 6.7, 3.3, 1.6)
    p5 = Box(13.9, 2.6, 3.3, 1.6)
    process(ax, p1, "1.0", "Регистрация\nпользователей", S - 0.5, band=0.42, color=SC(1))
    process(ax, p4, "4.0", "Управление\nзадачами", S - 0.5, band=0.42, color=SC(4))
    process(ax, p5, "5.0", "Обсуждение\nзадач", S - 0.5, band=0.42, color=SC(5))
    db = Box(17.75, 6.7, 2.9, 1.1)
    store(ax, db, "БД", "project_db\nD1–D5", S - 1, cell=0.6)

    A = dict(size=S - 1.5, lw=1.6, head=15)
    arrow(ax, [cat.right(-0.25), p1.left(0.5)], color=SC(1), dashed=True, **A)
    label(ax, 10.55, 10.15, "① учётная\nзапись", S - 1.5, color=SC(1))
    carrow(ax, lead.right(-0.2), p4.left(0.35), rad=0.1, text="② задача SHOP-42,\nисполнитель, срок",
           at=(6.9, 8.7), color=SC(4), size=S - 1.5)
    arrow(ax, [p4.right(), db.left()], "③", at=(16.0, 6.95), color=SC(4), **A)
    arrow(ax, [p4.left(-0.2), (ntf.r, ntf.y - 0.0)], color=SC(4), dashed=True, **A)
    label(ax, 10.75, 6.05, "④ назначена\nSHOP-42", S - 1.5, color=SC(4))
    arrow(ax, [ntf.left(-0.3), (2.7, ntf.y - 0.3), (2.7, mem.t)], "⑤ письмо, событие\nв календаре",
          at=(4.15, 5.75), color=SC(4), dashed=True, **A)
    carrow(ax, mem.bottom(0.6), git.left(-0.2), rad=0.25, text="⑥ коммит\n«SHOP-42: …»", at=(3.85, 1.25),
           color=SC(4), dashed=True, size=S - 1.5)
    carrow(ax, git.right(0.2), p4.bottom(-0.9), rad=-0.25, text="⑦ веб-хук:\nSHOP-42 → review",
           at=(10.8, 3.65), color=SC(4), dashed=True, size=S - 1.5)
    arrow(ax, [mem.bottom(-0.8), (1.1, 0.35), (p5.x, 0.35), p5.bottom()], "⑧ комментарий к задаче",
          at=(10.6, 0.35), color=SC(5), **A)

    ax.text(0.15, 12.55, "①–⑧ — порядок шагов; пунктир — обмен с внешним сервисом", fontsize=S - 2.5,
            color=GREY, va="center")
    save(fig, "env")


def components_diagram():
    W, H = 27.3, 17.6
    fig, ax = canvas(W, H, k=0.58)
    S = 12

    sysb = Box(12.7, 8.55, 18.0, 13.3)
    ax.add_patch(FancyBboxPatch((sysb.l, sysb.b), sysb.w, sysb.h, boxstyle="round,pad=0,rounding_size=0.4",
                                fc="#f7f9fd", ec="#1d3a8a", lw=2.2, zorder=0))
    ax.text(sysb.x, sysb.t - 0.42, "Система управления проектами", fontsize=S + 1, weight="bold",
            va="center", ha="center", color="#1d3a8a")

    def esb(b, code, t):
        ax.add_patch(Rectangle((b.l + 0.08, b.b - 0.08), b.w, b.h, fc="#9aa5b5", ec="none", zorder=1))
        ax.add_patch(Rectangle((b.l, b.b), b.w, b.h, fc=FILL_EXT, ec=LINE, lw=1.6, zorder=2))
        ax.text(b.x, b.y + 0.27, code, ha="center", va="center", fontsize=S, weight="bold", zorder=5)
        ax.text(b.x, b.y - 0.2, t, ha="center", va="center", fontsize=S - 1, zorder=5, linespacing=1.1)
        return b

    def comp(x, y, code, name, ops, i):
        w, hh, rh = 4.0, 0.62, 0.43
        h = hh + rh * len(ops) + 0.15
        b = Box(x, y, w, h)
        col = SC(i)
        ax.add_patch(FancyBboxPatch((b.l, b.b), w, h, boxstyle="round,pad=0,rounding_size=0.15",
                                    fc="white", ec=col, lw=2.0, zorder=3))
        ax.add_patch(FancyBboxPatch((b.l, b.t - hh), w, hh, boxstyle="round,pad=0,rounding_size=0.15",
                                    fc=col, ec=col, lw=2.0, zorder=3))
        ax.text(b.x, b.t - hh / 2, f"{code} {name}", ha="center", va="center", fontsize=S, weight="bold",
                color="white", zorder=5)
        for k, op in enumerate(ops):
            yy = b.t - hh - 0.08 - rh * (k + 0.5)
            ax.add_patch(Rectangle((b.l + 0.15, yy - rh / 2 + 0.03), w - 0.3, rh - 0.06, fc="#f4f4f4", ec=GREY,
                                   lw=0.7, zorder=4))
            ax.text(b.l + 0.27, yy, op, ha="left", va="center", fontsize=S - 2, zorder=5)
        return b

    # информационный ресурс — БД в центре
    db = Box(12.7, 8.3, 5.6, 4.6)
    e = 0.45
    ax.add_patch(Rectangle((db.l, db.b + e), db.w, db.h - 2 * e, fc=FILL_STORE, ec="none", zorder=2))
    ax.add_patch(Ellipse((db.x, db.b + e), db.w, 2 * e, fc=FILL_STORE, ec=LINE, lw=1.6, zorder=2))
    ax.add_patch(Rectangle((db.l, db.b + e), db.w, db.h - 2 * e, fc=FILL_STORE, ec="none", zorder=2))
    ax.plot([db.l, db.l], [db.b + e, db.t - e], color=LINE, lw=1.6, zorder=3)
    ax.plot([db.r, db.r], [db.b + e, db.t - e], color=LINE, lw=1.6, zorder=3)
    ax.add_patch(matplotlib.patches.Arc((db.x, db.b + e), db.w, 2 * e, theta1=180, theta2=360, color=LINE, lw=1.6, zorder=3))
    ax.add_patch(Ellipse((db.x, db.t - e), db.w, 2 * e, fc="#d6ecd6", ec=LINE, lw=1.6, zorder=3))
    ax.text(db.x, db.t - 1.25, "ИР: БД project_db", ha="center", va="center", fontsize=S + 0.5, weight="bold", zorder=5)
    for k, t in enumerate(["D1 Пользователи (users)", "D2 Проекты (projects)", "D3 Участники (project_members)",
                           "D4 Задачи и метки (tasks, marks, …)", "D5 Комментарии (comments)"]):
        ax.text(db.l + 0.35, db.t - 1.85 - k * 0.46, t, ha="left", va="center", fontsize=S - 2, zorder=5)

    K2 = comp(8.0, 13.0, "К2", "Проекты", ["2.1 Создание, код", "2.2 Владелец", "2.3 Статус, сроки", "2.4 Удаление"], 2)
    K3 = comp(17.4, 13.0, "К3", "Команды", ["3.1 Добавление", "3.2 Назначение роли", "3.3 Исключение"], 3)
    K6 = comp(5.9, 8.3, "К6", "Отчётность", ["6.1 Операционные запросы", "6.2 Агрегаты, подзапросы",
                                             "6.3 Отчёт о рисках"], 6)
    K4 = comp(19.5, 8.3, "К4", "Задачи", ["4.1 Создание, оценка", "4.2 Назначение", "4.3 Статус, приоритет",
                                          "4.4 Удаление", "4.5 Метки"], 4)
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
    arrow(ax, [E4.right(), (K1.l, 2.85)], "З2", at=(5.0, 2.41), size=L, color=SC(1))
    arrow(ax, [E2.left(-0.3), (K2.x, E2.y - 0.3), K2.top()], "З3", at=(9.5, E2.y - 0.3), size=L, color=SC(2))
    arrow(ax, [E2.right(-0.3), (K3.x, E2.y - 0.3), K3.top()], "З4", at=(15.9, E2.y - 0.3), size=L, color=SC(3))
    arrow(ax, [E2.right(0.3), (20.6, E2.y + 0.3), (20.6, K4.t)], "З5", at=(20.6, 12.9), size=L, color=SC(4))
    arrow(ax, [K6.top(-0.9), (5.0, E2.y + 0.3), E2.left(0.3)], "О2", at=(5.0, 12.9), size=L, color=SC(6))
    arrow(ax, [E5.left(), (K4.r, E5.y)], "З6", at=(21.7, E5.y + 0.32), size=L, color=SC(4))
    arrow(ax, [E3.left(0.35), (K4.r, E3.y + 0.35)], "З7", at=(21.7, E3.y + 0.67), size=L, color=SC(4))
    arrow(ax, [E3.bottom(-1.0), (22.55, 3.6), K5.right()], "З8", at=(21.6, 3.6), size=L, color=SC(5))
    arrow(ax, [K4.bottom(1.1), (20.6, 0.85), E6.right(0.1)], "О3", at=(20.6, 5.4), size=L, color=SC(4))
    arrow(ax, [K5.bottom(-0.8), (K5.x - 0.8, 1.25), E6.right(0.5)], "О4", at=(16.6, 1.9), size=L, color=SC(5))
    arrow(ax, [E6.right(-0.35), (24.6, 0.4), E3.bottom(1.05)], "доставка\nуведомлений", at=(24.6, 3.2), size=L - 1,
          color=GREY, dashed=True)

    # связи компоненты ↔ ИР (запись/чтение)
    G = "#555555"
    for kb, pt, t, at in [(K1, db.left(-1.5), "D1", (9.45, 5.7)), (K2, db.left(1.6), "D2; D1", (9.45, 10.85)),
                          (K3, db.right(1.6), "D3; D2", (15.95, 10.85)), (K4, db.right(0.0), "D4; D3", (16.5, 8.3)),
                          (K5, db.right(-1.5), "D5; D4", (15.95, 5.7)), (K6, db.left(0.0), "D2–D5", (8.9, 8.3))]:
        a = kb.right() if kb.x < db.x else kb.left()
        if kb in (K2, K3):
            a = kb.bottom(1.0 if kb.x < db.x else -1.0)
        if kb in (K1, K5):
            a = kb.top(1.0 if kb.x < db.x else -1.0)
        ax.annotate("", xy=pt, xytext=a, zorder=2,
                    arrowprops=dict(arrowstyle="<|-|>", color=G, lw=1.3, mutation_scale=13, shrinkA=0, shrinkB=0))
        label(ax, at[0], at[1], t, S - 2, color=G)

    # легенда
    lx, ly = 22.1, 15.35
    ax.add_patch(Rectangle((lx, ly - 3.05), 5.1, 3.05, fc="white", ec="#888888", lw=1, zorder=1))
    ax.text(lx + 0.15, ly - 0.3, "Обозначения", fontsize=S - 1, weight="bold", va="center")
    ax.add_patch(Rectangle((lx + 0.25, ly - 0.95), 0.8, 0.45, fc=FILL_EXT, ec=LINE, lw=1.2))
    ax.text(lx + 1.3, ly - 0.72, "ЭСО — элемент окружения", fontsize=S - 2.5, va="center")
    ax.add_patch(Rectangle((lx + 0.25, ly - 1.55), 0.8, 0.45, fc="white", ec="#1f5fbf", lw=1.6))
    ax.add_patch(Rectangle((lx + 0.25, ly - 1.25), 0.8, 0.15, fc="#1f5fbf", ec="#1f5fbf", lw=1.6))
    ax.text(lx + 1.3, ly - 1.32, "К — программный компонент", fontsize=S - 2.5, va="center")
    ax.add_patch(Ellipse((lx + 0.65, ly - 1.95), 0.8, 0.3, fc=FILL_STORE, ec=LINE, lw=1.1))
    ax.text(lx + 1.3, ly - 1.95, "ИР — информационный ресурс", fontsize=S - 2.5, va="center")
    ax.annotate("", xy=(lx + 1.05, ly - 2.55), xytext=(lx + 0.25, ly - 2.55),
                arrowprops=dict(arrowstyle="-|>", color=LINE, lw=1.3, mutation_scale=13))
    ax.text(lx + 1.3, ly - 2.55, "З — вход, О — выход", fontsize=S - 2.5, va="center")

    save(fig, "components")


if __name__ == "__main__":
    context_diagram()
    dfd_diagram()
    fdd_diagram()
    chen_diagram()
    bpmn_diagram()
    logical_diagram()
    arch_diagram()
    report_diagram()
    algo_diagram()
    env_diagram()
    components_diagram()
    print("готово:", OUT)
