"""
Диаграммы для ЛР №1 «Система управления проектами» (исходная БД, без migration.sql).

  context.png — контекстная диаграмма (DFD уровня 0), нотация Гейна–Сарсона
  dfd.png     — диаграмма потоков данных уровня 1, нотация Гейна–Сарсона
  fdd.png     — диаграмма декомпозиции функций
  chen.png    — ER-диаграмма в нотации Чена

Запуск:  python3 diagrams.py   (рядом появятся .png и .svg)
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["svg.fonttype"] = "none"

LINE = "#222222"
FILL_EXT = "#e8eef7"
FILL_PROC = "#fdf3e1"
FILL_STORE = "#eaf5ea"


# --------------------------------------------------------------------------
# общее
# --------------------------------------------------------------------------
def canvas(w, h, title):
    """Холст, где 1 единица координат = 1 дюйм."""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.text(w / 2, h - 0.35, title, ha="center", va="center", fontsize=17, weight="bold")
    return fig, ax


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=150, facecolor="white")
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
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"), **kw,
    )


def flow(ax, pts, text=None, at=None, size=10):
    """Поток данных: ломаная pts, стрелка на последней точке, подпись в точке at."""
    xs, ys = zip(*pts)
    ax.plot(xs[:-1], ys[:-1], color=LINE, lw=1.3, zorder=3)
    ax.annotate(
        "", xy=pts[-1], xytext=pts[-2], zorder=4,
        arrowprops=dict(arrowstyle="-|>", color=LINE, lw=1.3, mutation_scale=16,
                        shrinkA=0, shrinkB=0),
    )
    if text:
        if at is None:
            (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
            at = ((x1 + x2) / 2, (y1 + y2) / 2)
        label(ax, at[0], at[1], text, size)


# --------------------------------------------------------------------------
# нотация Гейна–Сарсона
# --------------------------------------------------------------------------
def external(ax, box, text, size=12):
    """Внешняя сущность: прямоугольник с тенью."""
    ax.add_patch(Rectangle((box.l + 0.08, box.b - 0.08), box.w, box.h, fc="#9aa5b5", ec="none", zorder=1))
    ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_EXT, ec=LINE, lw=1.6, zorder=2))
    ax.text(box.x, box.y, text, ha="center", va="center", fontsize=size, weight="bold", zorder=5)


def process(ax, box, num, text, size=11):
    """Процесс: скруглённый прямоугольник, сверху — полоса с номером."""
    ax.add_patch(FancyBboxPatch((box.l, box.b), box.w, box.h,
                                boxstyle="round,pad=0,rounding_size=0.18",
                                fc=FILL_PROC, ec=LINE, lw=1.6, zorder=2))
    band = 0.38
    ax.plot([box.l, box.r], [box.t - band, box.t - band], color=LINE, lw=1.2, zorder=3)
    ax.text(box.x, box.t - band / 2, num, ha="center", va="center", fontsize=size, weight="bold", zorder=5)
    ax.text(box.x, (box.b + box.t - band) / 2, text, ha="center", va="center", fontsize=size, zorder=5)


def store(ax, box, sid, text, size=11):
    """Накопитель данных: прямоугольник, открытый справа, слева — ячейка с номером."""
    ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=FILL_STORE, ec="none", zorder=1))
    cell = 0.55
    ax.plot([box.r, box.l, box.l, box.r], [box.t, box.t, box.b, box.b], color=LINE, lw=1.6, zorder=3)
    ax.plot([box.l + cell, box.l + cell], [box.b, box.t], color=LINE, lw=1.2, zorder=3)
    ax.text(box.l + cell / 2, box.y, sid, ha="center", va="center", fontsize=size, weight="bold", zorder=5)
    ax.text(box.l + cell + (box.w - cell) / 2, box.y, text, ha="center", va="center", fontsize=size, zorder=5)


def gs_legend(ax, x, y):
    """Легенда нотации Гейна–Сарсона (левый верхний угол в (x, y))."""
    ax.add_patch(Rectangle((x, y - 2.55), 3.9, 2.55, fc="white", ec="#888888", lw=1, zorder=1))
    ax.text(x + 0.15, y - 0.25, "Обозначения", fontsize=10, weight="bold", va="center")
    external(ax, Box(x + 0.7, y - 0.75, 0.9, 0.42), "", 8)
    ax.text(x + 1.4, y - 0.75, "внешняя сущность", fontsize=9, va="center")
    process(ax, Box(x + 0.7, y - 1.35, 0.9, 0.55), "", "", 6)
    ax.text(x + 1.4, y - 1.35, "процесс", fontsize=9, va="center")
    store(ax, Box(x + 0.7, y - 1.85, 0.9, 0.3), "", "", 6)
    ax.text(x + 1.4, y - 1.85, "накопитель данных", fontsize=9, va="center")
    flow(ax, [(x + 0.25, y - 2.27), (x + 1.15, y - 2.27)])
    ax.text(x + 1.4, y - 2.27, "поток данных", fontsize=9, va="center")


# --------------------------------------------------------------------------
# 1. Контекстная диаграмма
# --------------------------------------------------------------------------
def context_diagram():
    fig, ax = canvas(17, 9.5, "Контекстная диаграмма (DFD уровня 0) — Система управления проектами")

    sys0 = Box(8.5, 4.6, 4.2, 2.4)
    adm = Box(2.4, 7.3, 3.4, 1.1)
    lead = Box(2.4, 1.9, 3.4, 1.1)
    mem = Box(14.6, 4.6, 3.4, 1.1)

    process(ax, sys0, "0", "Система управления\nпроектами", 14)
    external(ax, adm, "Администратор")
    external(ax, lead, "Руководитель\nпроекта")
    external(ax, mem, "Участник проекта\n(исполнитель)")

    # Администратор
    flow(ax, [adm.right(0.25), (7.6, adm.y + 0.25), sys0.top(-0.9)],
         "данные новых пользователей", at=(5.4, adm.y + 0.55))
    flow(ax, [sys0.top(-1.6), (6.9, adm.y - 0.2), adm.right(-0.2)],
         "подтверждение регистрации", at=(5.55, adm.y - 0.5))

    # Руководитель проекта
    flow(ax, [lead.right(-0.25), (7.6, lead.y - 0.25), sys0.bottom(-0.9)],
         "данные проектов, состав участников,\nзадачи и назначения исполнителей", at=(5.5, lead.y - 0.8))
    flow(ax, [sys0.bottom(-1.6), (6.9, lead.y + 0.2), lead.right(0.2)],
         "отчёты о ходе проектов", at=(5.15, lead.y + 0.5))

    # Участник проекта
    flow(ax, [mem.left(0.3), sys0.right(0.3)],
         "изменение статуса задачи,\nкомментарии", at=(11.75, mem.y + 0.85))
    flow(ax, [sys0.right(-0.3), mem.left(-0.3)],
         "назначенные задачи,\nобсуждения задач", at=(11.75, mem.y - 0.85))

    gs_legend(ax, 12.85, 9.0)
    save(fig, "context")


# --------------------------------------------------------------------------
# 2. DFD уровня 1
# --------------------------------------------------------------------------
def dfd_diagram():
    fig, ax = canvas(24.5, 16, "Диаграмма потоков данных (DFD уровня 1) — Система управления проектами")

    xs = [2.4, 7.2, 12.0, 16.8, 21.6]
    pw, ph = 3.3, 1.8
    sw, sh = 3.4, 0.85
    yE, yP, yD = 12.9, 8.6, 4.5

    adm = Box(xs[0], yE, 3.2, 1.15)
    lead = Box(xs[2], yE, 3.2, 1.15)
    mem = Box(xs[4], yE, 3.2, 1.15)
    external(ax, adm, "Администратор")
    external(ax, lead, "Руководитель\nпроекта")
    external(ax, mem, "Участник проекта\n(исполнитель)")

    names_p = ["Регистрация\nпользователей", "Ведение\nпроектов", "Управление\nсоставом проекта",
               "Управление\nзадачами", "Обсуждение\nзадач"]
    P = [Box(x, yP, pw, ph) for x in xs]
    for i, (b, n) in enumerate(zip(P, names_p), start=1):
        process(ax, b, str(i), n)
    p6 = Box(xs[2], 1.25, pw, 1.55)
    process(ax, p6, "6", "Формирование\nотчётов")

    names_d = ["Пользователи\n(users)", "Проекты\n(projects)", "Участники проектов\n(project_members)",
               "Задачи\n(tasks)", "Комментарии\n(comments)"]
    D = [Box(x, yD, sw, sh) for x in xs]
    for i, (b, n) in enumerate(zip(D, names_d), start=1):
        store(ax, b, f"D{i}", n, 10)

    # --- внешние сущности ↔ процессы
    flow(ax, [adm.bottom(-0.35), P[0].top(-0.35)], "данные\nпользователя", at=(xs[0] - 1.25, 10.75))
    flow(ax, [P[0].top(0.35), adm.bottom(0.35)], "подтверждение\nрегистрации", at=(xs[0] + 1.3, 10.75))

    flow(ax, [lead.bottom(-0.9), P[1].top(0.6)], "данные проекта", at=(9.15, 10.95))
    flow(ax, [lead.bottom(0.0), P[2].top(0.0)], "участник\nи роль", at=(xs[2], 10.75))
    flow(ax, [lead.bottom(0.9), P[3].top(-0.6)], "задача, исполнитель,\nсрок", at=(14.85, 10.95))

    flow(ax, [mem.bottom(-0.9), P[3].top(1.0)], "новый статус\nзадачи", at=(20.45, 10.85))
    flow(ax, [P[3].top(0.45), mem.bottom(-1.35)], "назначенные\nзадачи", at=(17.35, 10.6))
    flow(ax, [mem.bottom(0.15), P[4].top(0.15)], "комментарий", at=(xs[4] + 0.15, 10.75))
    flow(ax, [P[4].top(0.85), mem.bottom(0.85)], "обсуждение\nзадачи", at=(xs[4] + 1.65, 10.4))

    # --- запись в накопители (процесс → свой накопитель)
    writes = ["новый\nпользователь", "проект", "участник,\nроль", "задача,\nстатус", "комментарий"]
    for p, d, t in zip(P, D, writes):
        flow(ax, [p.bottom(), d.top()], t, at=(p.x, (p.b + d.t) / 2))

    # --- чтение из соседнего накопителя (диагонали)
    reads = ["сведения\nо владельце", "проект", "участники\nпроекта", "задача"]
    for i, t in enumerate(reads):
        d, p = D[i], P[i + 1]
        a, b = (d.r - 0.15, d.t), (p.l + 0.15, p.b)
        flow(ax, [a, b], t, at=((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))

    # --- отчёты: чтение D2, D3, D4 → процесс 6
    flow(ax, [D[1].bottom(0.6), p6.left(0.35)], "проекты", at=(9.0, 2.75))
    flow(ax, [D[2].bottom(), p6.top()], "участники", at=(xs[2], 2.95))
    flow(ax, [D[3].bottom(-0.6), p6.right(0.35)], "задачи", at=(15.0, 2.75))
    # процесс 6 → руководитель: обходим схему по левому краю
    flow(ax, [p6.left(-0.35), (0.35, p6.y - 0.35), (0.35, 15.05), (lead.x, 15.05), lead.top()],
         "отчёт о ходе проекта", at=(6.2, 15.05))

    gs_legend(ax, 20.3, 3.1)
    save(fig, "dfd")


# --------------------------------------------------------------------------
# 3. Диаграмма декомпозиции функций
# --------------------------------------------------------------------------
def fdd_diagram():
    fig, ax = canvas(24.5, 10.6, "Диаграмма декомпозиции функций — Система управления проектами")

    def rect(box, text, fc, size, bold=False):
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc=fc, ec=LINE, lw=1.4, zorder=2))
        ax.text(box.x, box.y, text, ha="center", va="center", fontsize=size,
                weight="bold" if bold else "normal", zorder=5)

    root = Box(12.25, 9.25, 6.2, 0.9)
    rect(root, "Система управления проектами", "#d9e4f2", 14, True)

    funcs = [
        ("1. Управление\nпользователями",
         ["1.1. Регистрация\nпользователя", "1.2. Изменение данных\nпользователя", "1.3. Удаление\nпользователя"]),
        ("2. Управление\nпроектами",
         ["2.1. Создание проекта", "2.2. Назначение\nвладельца", "2.3. Изменение статуса\nи сроков", "2.4. Удаление проекта"]),
        ("3. Управление составом\nпроекта",
         ["3.1. Добавление\nучастника", "3.2. Назначение роли", "3.3. Исключение\nучастника"]),
        ("4. Управление\nзадачами",
         ["4.1. Создание задачи", "4.2. Назначение\nисполнителя", "4.3. Изменение статуса\nи приоритета", "4.4. Удаление задачи"]),
        ("5. Обсуждение\nзадач",
         ["5.1. Добавление\nкомментария", "5.2. Просмотр\nобсуждения", "5.3. Удаление\nкомментария"]),
        ("6. Формирование\nотчётов",
         ["6.1. Задачи\nпо статусам", "6.2. Просроченные\nзадачи", "6.3. Загрузка\nучастников"]),
    ]

    xs = [2.15 + i * 4.04 for i in range(6)]
    bus_y, fy = 8.35, 7.45
    ax.plot([root.x, root.x], [root.b, bus_y], color=LINE, lw=1.4)
    ax.plot([xs[0], xs[-1]], [bus_y, bus_y], color=LINE, lw=1.4)

    for x, (name, subs) in zip(xs, funcs):
        f = Box(x, fy, 3.6, 1.0)
        ax.plot([x, x], [bus_y, f.t], color=LINE, lw=1.4)
        rect(f, name, "#fdf3e1", 11.5, True)
        spine = f.l + 0.25
        ys = [6.2 - k * 1.15 for k in range(len(subs))]
        ax.plot([spine, spine], [f.b, ys[-1]], color=LINE, lw=1.2)
        for y, s in zip(ys, subs):
            sb = Box(spine + 0.3 + 3.05 / 2, y, 3.05, 0.85)   # правый край = правый край функции
            ax.plot([spine, sb.l], [y, y], color=LINE, lw=1.2)
            rect(sb, s, "white", 10.5)

    ax.text(0.3, 1.9, "Нумерация функций верхнего уровня совпадает с номерами процессов на DFD уровня 1.",
            fontsize=10, style="italic", color="#444444", va="center")
    # обрезаем пустое поле снизу, сохраняя масштаб 1 единица = 1 дюйм
    fig.set_size_inches(24.5, 9.0)
    ax.set_ylim(1.6, 10.6)
    save(fig, "fdd")


# --------------------------------------------------------------------------
# 4. ER-диаграмма в нотации Чена
# --------------------------------------------------------------------------
def chen_diagram():
    fig, ax = canvas(23, 16.5, "ER-диаграмма в нотации Чена — Система управления проектами")
    renderer = fig.canvas.get_renderer()

    def entity(box, name, table):
        ax.add_patch(Rectangle((box.l, box.b), box.w, box.h, fc="#d9e4f2", ec=LINE, lw=1.8, zorder=4))
        ax.text(box.x, box.y + 0.13, name, ha="center", va="center", fontsize=13, weight="bold", zorder=6)
        ax.text(box.x, box.y - 0.24, f"({table})", ha="center", va="center", fontsize=9.5, color="#333333", zorder=6)

    def attr(x, y, text, ent, key=False):
        ax.plot([x, ent.x], [y, ent.y], color=LINE, lw=1.0, zorder=1)
        w = max(1.55, 0.115 * len(text) + 0.55)
        ax.add_patch(Ellipse((x, y), w, 0.62, fc="white", ec=LINE, lw=1.2, zorder=4))
        t = ax.text(x, y, text, ha="center", va="center", fontsize=10, zorder=6)
        if key:  # ключевой атрибут — подчёркнут
            bb = t.get_window_extent(renderer=renderer).transformed(ax.transData.inverted())
            ax.plot([bb.x0, bb.x1], [bb.y0 + 0.01, bb.y0 + 0.01], color=LINE, lw=1.0, zorder=6)

    def rel(x, y, text, w=2.5, h=1.3):
        ax.add_patch(Polygon([(x - w / 2, y), (x, y + h / 2), (x + w / 2, y), (x, y - h / 2)],
                             closed=True, fc="#fdf3e1", ec=LINE, lw=1.6, zorder=4))
        ax.text(x, y, text, ha="center", va="center", fontsize=10.5, weight="bold", zorder=6)
        return (x, y)

    def link(a, b, total=False):
        """Линия связи; total=True — двойная линия (полное участие)."""
        (x1, y1), (x2, y2) = a, b
        if not total:
            ax.plot([x1, x2], [y1, y2], color=LINE, lw=1.4, zorder=2)
            return
        dx, dy = x2 - x1, y2 - y1
        n = (dx ** 2 + dy ** 2) ** 0.5
        ox, oy = -dy / n * 0.05, dx / n * 0.05
        for s in (1, -1):
            ax.plot([x1 + s * ox, x2 + s * ox], [y1 + s * oy, y2 + s * oy], color=LINE, lw=1.3, zorder=2)

    def card(x, y, text):
        ax.text(x, y, text, ha="center", va="center", fontsize=13, weight="bold", color="#b03030", zorder=7)

    U = Box(4.3, 8.4, 2.9, 1.05)
    P = Box(15.6, 12.3, 2.9, 1.05)
    T = Box(15.6, 5.2, 2.9, 1.05)
    C = Box(7.6, 2.3, 2.9, 1.05)
    entity(U, "ПОЛЬЗОВАТЕЛЬ", "users")
    entity(P, "ПРОЕКТ", "projects")
    entity(T, "ЗАДАЧА", "tasks")
    entity(C, "КОММЕНТАРИЙ", "comments")

    # --- связи
    own = rel(9.9, 13.3, "ВЛАДЕЕТ")
    link(U.top(0.6), own)
    link(own, P.left(0.25), total=True)
    card(5.6, 9.45, "1")
    card(13.75, 12.85, "N")

    part = rel(9.9, 10.55, "УЧАСТВУЕТ", w=2.8)
    link(U.right(0.3), part)
    link(part, P.left(-0.25))
    card(6.25, 8.95, "M")
    card(13.75, 11.7, "N")
    attr(8.75, 9.05, "role", Box(*part, 0, 0))
    attr(11.15, 9.05, "joined_at", Box(*part, 0, 0))

    cont = rel(15.6, 8.75, "СОДЕРЖИТ", w=2.7)
    link(P.bottom(), cont)
    link(cont, T.top(), total=True)
    card(15.95, 11.45, "1")
    card(15.95, 6.05, "N")

    execs = rel(10.0, 6.4, "ИСПОЛНЯЕТ", w=2.8)
    link(U.right(-0.3), execs)
    link(execs, T.left(0.2))
    card(6.25, 7.75, "1")
    card(13.75, 5.75, "N")

    has = rel(12.4, 2.3, "ОТНОСИТСЯ\nК", w=2.7, h=1.4)
    link(T.bottom(-0.5), has)
    link(has, C.right(), total=True)
    card(14.65, 4.3, "1")
    card(9.4, 2.65, "N")

    writes = rel(4.3, 4.7, "ПИШЕТ")
    link(U.bottom(), writes)
    link(writes, C.left(0.2), total=True)
    card(4.6, 7.55, "1")
    card(6.0, 2.85, "N")

    # --- атрибуты (первичный ключ подчёркнут)
    for (x, y, t, k) in [(1.3, 10.7, "user_id", True), (1.15, 9.2, "full_name", False),
                         (1.15, 7.65, "email", False), (1.3, 6.15, "created_at", False)]:
        attr(x, y, t, U, k)

    for (x, y, t, k) in [(13.4, 14.75, "project_id", True), (15.9, 15.1, "name", False),
                         (18.4, 14.75, "description", False), (19.9, 13.35, "status", False),
                         (20.15, 12.2, "start_date", False), (19.9, 11.05, "end_date", False)]:
        attr(x, y, t, P, k)

    for (x, y, t, k) in [(19.2, 8.35, "task_id", True), (20.5, 7.4, "title", False),
                         (20.9, 6.4, "description", False), (20.9, 5.25, "status", False),
                         (20.9, 4.15, "priority", False), (20.5, 3.15, "created_at", False),
                         (19.0, 2.2, "due_date", False)]:
        attr(x, y, t, T, k)

    for (x, y, t, k) in [(4.9, 0.95, "comment_id", True), (7.6, 0.75, "body", False),
                         (10.3, 0.95, "created_at", False)]:
        attr(x, y, t, C, k)

    # --- легенда
    lx, ly = 0.35, 15.55
    ax.add_patch(Rectangle((lx, ly - 3.75), 5.2, 3.75, fc="white", ec="#888888", lw=1, zorder=1))
    ax.text(lx + 0.15, ly - 0.25, "Обозначения", fontsize=10, weight="bold", va="center")
    ax.add_patch(Rectangle((lx + 0.2, ly - 0.75), 1.0, 0.4, fc="#d9e4f2", ec=LINE, lw=1.4))
    ax.text(lx + 1.45, ly - 0.55, "сущность (таблица)", fontsize=9, va="center")
    ax.add_patch(Ellipse((lx + 0.7, ly - 1.1), 1.0, 0.38, fc="white", ec=LINE, lw=1.1))
    ax.text(lx + 1.45, ly - 1.1, "атрибут", fontsize=9, va="center")
    ax.add_patch(Ellipse((lx + 0.7, ly - 1.6), 1.0, 0.38, fc="white", ec=LINE, lw=1.1))
    ax.text(lx + 0.7, ly - 1.6, "key", fontsize=8, ha="center", va="center")
    ax.plot([lx + 0.55, lx + 0.85], [ly - 1.69, ly - 1.69], color=LINE, lw=0.9)
    ax.text(lx + 1.45, ly - 1.6, "первичный ключ (подчёркнут)", fontsize=9, va="center")
    ax.add_patch(Polygon([(lx + 0.2, ly - 2.15), (lx + 0.7, ly - 1.95), (lx + 1.2, ly - 2.15), (lx + 0.7, ly - 2.35)],
                         closed=True, fc="#fdf3e1", ec=LINE, lw=1.2))
    ax.text(lx + 1.45, ly - 2.15, "связь", fontsize=9, va="center")
    ax.plot([lx + 0.2, lx + 1.2], [ly - 2.65, ly - 2.65], color=LINE, lw=1.3)
    ax.text(lx + 1.45, ly - 2.65, "частичное участие (может не быть)", fontsize=9, va="center")
    for o in (0.05, -0.05):
        ax.plot([lx + 0.2, lx + 1.2], [ly - 3.15 + o, ly - 3.15 + o], color=LINE, lw=1.2)
    ax.text(lx + 1.45, ly - 3.15, "полное участие (обязательно)", fontsize=9, va="center")
    ax.text(lx + 0.15, ly - 3.55, "1, N, M — кардинальность связи", fontsize=9, va="center", color="#b03030")

    save(fig, "chen")


if __name__ == "__main__":
    context_diagram()
    dfd_diagram()
    fdd_diagram()
    chen_diagram()
    print("готово:", OUT)
