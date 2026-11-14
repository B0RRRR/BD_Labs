"""Генератор демонстрационного набора данных db/seed/demo.sql.

Набор детерминирован (фиксированное зерно), поэтому файл demo.sql хранится в
репозитории, а Python при развёртывании не нужен. Перегенерация:
    python3 db/seed/gen_demo.py

Моделируется история компании с сентября 2025 по 14 ноября 2026 г.:
14 проектов в разных состояниях, двухнедельные спринты с ограниченной ёмкостью,
перенос незавершённых задач в следующий спринт, возвраты задач на доработку,
просрочки, неоценённые и неназначенные задачи, комментарии и метки.
"""
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

R = random.Random(2026)
TODAY = date(2026, 11, 14)
NOW = datetime.combine(TODAY, time(12, 0))

# ------------------------------------------------------------------ люди
SURNAMES = [
    ("Абрамов", "Абрамова"), ("Белов", "Белова"), ("Васильев", "Васильева"), ("Гаврилов", "Гаврилова"),
    ("Демидов", "Демидова"), ("Егоров", "Егорова"), ("Жуков", "Жукова"), ("Зайцев", "Зайцева"),
    ("Ильин", "Ильина"), ("Карпов", "Карпова"), ("Лебедев", "Лебедева"), ("Макаров", "Макарова"),
    ("Никитин", "Никитина"), ("Орлов", "Орлова"), ("Павлов", "Павлова"), ("Романов", "Романова"),
    ("Соловьёв", "Соловьёва"), ("Тарасов", "Тарасова"), ("Уваров", "Уварова"), ("Фёдоров", "Фёдорова"),
    ("Харитонов", "Харитонова"), ("Цветков", "Цветкова"), ("Чернов", "Чернова"), ("Шаров", "Шарова"),
    ("Щербаков", "Щербакова"), ("Яковлев", "Яковлева"), ("Голубев", "Голубева"), ("Комаров", "Комарова"),
    ("Медведев", "Медведева"), ("Новиков", "Новикова"), ("Осипов", "Осипова"), ("Поляков", "Полякова"),
    ("Савин", "Савина"), ("Титов", "Титова"), ("Фролов", "Фролова"), ("Широков", "Широкова"),
]
MALE = ["Алексей", "Андрей", "Артём", "Борис", "Владимир", "Глеб", "Дмитрий", "Евгений", "Иван", "Кирилл",
        "Максим", "Никита", "Олег", "Роман", "Сергей", "Тимур", "Фёдор", "Ярослав"]
FEMALE = ["Алина", "Анна", "Валерия", "Дарья", "Екатерина", "Елена", "Ирина", "Ксения", "Марина",
          "Наталья", "Ольга", "Полина", "Светлана", "Татьяна", "Юлия"]
TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
              ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t",
               "u", "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya"]))


def translit(s):
    return "".join(TR.get(c, c) for c in s.lower())


# основные роли сотрудников (роль в конкретном проекте берётся отсюда)
ROLE_PLAN = ["manager"] * 6 + ["developer"] * 22 + ["tester"] * 9 + ["analyst"] * 9
users = []          # (id, full_name, email, created_at, role)
used_emails = set()
pairs = R.sample([(s, female) for s in SURNAMES for female in (False, True)], len(ROLE_PLAN))
for i, (role, (sur, female)) in enumerate(zip(ROLE_PLAN, pairs)):
    uid = 101 + i
    first = R.choice(FEMALE if female else MALE)
    surname = sur[1] if female else sur[0]
    base = f"{translit(surname)}.{translit(first)[0]}"
    email = f"{base}@company.example"
    k = 2
    while email in used_emails:
        email = f"{base}{k}@company.example"
        k += 1
    used_emails.add(email)
    hired = date(2025, 1, 13) + timedelta(days=R.randint(0, 560))
    users.append((uid, f"{surname} {first}", email, datetime.combine(hired, time(9, R.randint(0, 59))), role))
by_role = {r: [u for u in users if u[4] == r] for r in set(ROLE_PLAN)}

# ------------------------------------------------------------------ заказчики и проекты
customers = [
    (101, "ООО «Альфа Логистик»", "Котова Мария", "kotova@alfa-log.example"),
    (102, "АО «ТрансСеть»", "Руденко Павел", "office@transset.example"),
    (103, "ООО «ФинТех Решения»", "Лаврова Ольга", "lavrova@fintech-r.example"),
    (104, "ООО «ЭкоДом»", None, "info@ecodom.example"),
    (105, "АО «Северные Технологии»", "Мишин Игорь", "mishin@sevtech.example"),
    (106, "ИП Кузнецов А. В.", "Кузнецов Алексей", "kuznetsov.av@mail.example"),   # заказчик без проектов
]

# (id, name, code, status, start, end, customer, contract(number, signed, amount, hours) | None, domain)
PROJECTS = [
    (101, "Сайт службы доставки", "LOG", "completed", date(2025, 10, 6), date(2026, 2, 27), 101,
     ("Д-2025/041", date(2025, 9, 22), 1350000, 520), "web"),
    (102, "Личный кабинет клиента банка", "FINLK", "completed", date(2025, 11, 3), date(2026, 5, 29), 103,
     ("Д-2025/047", date(2025, 10, 20), 3200000, 1100), "web"),
    (103, "Миграция почтовых серверов", "MAIL", "completed", date(2026, 1, 12), date(2026, 3, 20), None, None, "infra"),
    (104, "Каталог продукции", "CAT", "completed", date(2026, 2, 2), date(2026, 6, 26), 104,
     ("Д-2026/005", date(2026, 1, 21), 980000, 380), "web"),
    (105, "Система учёта заявок", "HELP", "completed", date(2026, 3, 2), date(2026, 7, 31), None, None, "web"),
    (106, "Мобильный банк", "MBANK", "active", date(2026, 6, 1), date(2027, 2, 26), 103,
     ("Д-2026/011", date(2026, 5, 18), 5400000, 1800), "mobile"),
    (107, "Трекинг грузов", "TRACK", "active", date(2026, 7, 6), date(2026, 12, 25), 102,
     ("Д-2026/013", date(2026, 6, 24), 2600000, 900), "web"),
    (108, "Платформа обучения сотрудников", "LMS", "active", date(2026, 8, 3), date(2027, 1, 29), None, None, "web"),
    (109, "Интеграция с 1С", "ERP", "active", date(2026, 9, 7), date(2027, 3, 31), 105,
     ("Д-2026/017", date(2026, 8, 26), 1900000, 700), "integration"),
    (110, "Редизайн корпоративного портала", "UX", "active", date(2026, 10, 5), date(2026, 12, 18), None, None, "web"),
    (111, "Голосовой помощник", "VOICE", "planned", date(2026, 12, 7), None, 103,
     ("Д-2026/024", date(2026, 11, 9), 2100000, 750), "mobile"),
    (112, "Портал поставщиков", "SUPP", "planned", date(2027, 1, 11), date(2027, 6, 30), 102, None, "web"),
    (113, "Маркетплейс услуг", "MARKT", "cancelled", date(2026, 4, 6), date(2026, 7, 17), 104,
     ("Д-2026/008", date(2026, 3, 25), 2800000, 950), "web"),
    (114, "Внутренний чат", "CHAT", "cancelled", date(2026, 5, 4), date(2026, 6, 12), None, None, "web"),
]

OBJECTS = {
    "web": ["главную страницу", "форму регистрации", "форму входа", "личный кабинет", "корзину", "каталог",
            "карточку товара", "поиск", "фильтры", "страницу оплаты", "уведомления по почте", "профиль пользователя",
            "административную панель", "отчёт по заказам", "импорт данных", "экспорт в Excel", "журнал действий",
            "страницу контактов", "систему ролей", "восстановление пароля", "мобильную вёрстку", "ленту новостей",
            "раздел помощи", "интеграцию с платёжным шлюзом", "карту офисов", "чат поддержки", "рейтинг и отзывы",
            "историю заказов", "календарь событий", "загрузку файлов"],
    "mobile": ["экран входа", "экран переводов", "экран истории операций", "push-уведомления", "биометрический вход",
               "экран карт", "экран вкладов", "оплату по QR-коду", "офлайн-режим", "экран настроек", "онбординг",
               "чат с поддержкой", "экран курсов валют", "шаблоны платежей", "выписку по счёту", "экран кешбэка",
               "смену PIN-кода", "голосовые команды", "распознавание речи", "сценарии диалога"],
    "infra": ["почтовый сервер", "резервное копирование", "антиспам-фильтр", "миграцию ящиков", "мониторинг",
              "DNS-записи", "сертификаты TLS", "журналирование", "отказоустойчивый кластер", "архив писем"],
    "integration": ["обмен справочниками", "выгрузку заказов", "загрузку остатков", "обмен контрагентами",
                    "синхронизацию цен", "журнал обмена", "обработку ошибок обмена", "расписание обмена",
                    "сверку документов", "выгрузку счетов", "мониторинг обмена", "API шлюза"],
}
VERBS = [("Реализовать", "developer", ["backend"]), ("Сверстать", "developer", ["frontend"]),
         ("Доработать", "developer", []), ("Исправить ошибку: ", "developer", ["bug"]),
         ("Протестировать", "tester", []), ("Описать требования: ", "analyst", ["docs"]),
         ("Оптимизировать", "developer", ["backend"]), ("Настроить", "developer", [])]
ESTIMATES = [2, 4, 4, 6, 8, 8, 12, 12, 16, 16, 24, 32]

COMMENTS = {
    "start": ["Взял в работу.", "Начинаю, к вечеру будет первая версия.", "Приступил, уточню детали у аналитика."],
    "question": ["Есть вопрос по требованиям: какой формат даты ожидает заказчик?",
                 "Не хватает макета для мобильной версии, кто может прислать?",
                 "Нужны тестовые данные, без них не проверить сценарий.",
                 "Уточните, пожалуйста, приоритет — задача блокирует релиз?"],
    "answer": ["Формат ДД.ММ.ГГГГ, как в остальных формах.", "Макет добавил в описание задачи.",
               "Тестовые данные выложил в общую папку.", "Да, нужно успеть до конца спринта."],
    "review": ["Готово, передаю на проверку.", "Исправил замечания, посмотрите ещё раз.",
               "Сделал, покрыл тестами основные сценарии."],
    "return": ["Возвращаю: при пустом поле падает ошибка 500.", "Не работает на мобильном, вёрстка съезжает.",
               "Проверка не прошла: не сохраняются изменения после перезагрузки."],
    "done": ["Проверено, замечаний нет.", "Принято, закрываю.", "Всё работает, спасибо!"],
    "carry": ["Не успеваем в этом спринте, переносим в следующий.", "Переношу: ждём ответа заказчика."],
    "overdue": ["Срок прошёл, какие новости?", "Задача просрочена, нужна новая оценка срока."],
}
MARK_NAMES = {"bug": 1, "frontend": 2, "backend": 3, "срочно": 4, "docs": 5}   # метки контрольного набора

# ------------------------------------------------------------------ генерация
members, sprints, tasks, history, comments, marks_tasks, contracts = [], [], [], [], [], [], []
sprint_id, task_id, comment_id = 101, 1001, 10001


def rand_dt(a, b):
    """Случайный момент рабочего дня между датами-временем a и b (a <= b)."""
    if b <= a:
        return a
    t = a + timedelta(seconds=R.randint(0, int((b - a).total_seconds())))
    return t.replace(second=0, microsecond=0)


def day_start(d):
    return datetime.combine(d, time(9, 0))


def day_end(d):
    return datetime.combine(d, time(19, 0))


for (pid, pname, code, pstatus, start, end, cust, contract, domain) in PROJECTS:
    if contract:
        contracts.append((pid, cust, *contract))
    # команда: руководитель, 2–5 разработчиков, 1–2 тестировщика, 0–1 аналитик
    owner = R.choice(by_role["manager"])
    team = {"manager": [owner], "developer": R.sample(by_role["developer"], R.randint(2, 5)),
            "tester": R.sample(by_role["tester"], R.randint(1, 2)),
            "analyst": R.sample(by_role["analyst"], R.randint(0, 1))}
    joined = start - timedelta(days=R.randint(3, 14))
    for role, people in team.items():
        for u in people:
            members.append((pid, u[0], role, joined))
    pdata = {"id": pid, "owner": owner[0], "team": team}
    PROJECTS_EXT = pdata

    if pstatus == "planned":
        # бэклог будущего проекта: несколько задач без спринта, часть не оценена
        n_backlog = 0 if code == "SUPP" else R.randint(6, 10)        # SUPP — проект пока без задач
    else:
        n_backlog = R.randint(3, 9) if pstatus == "active" else 0

    titles = set()

    def new_title(kind_role=None):
        for _ in range(200):
            verb, role, marks = R.choice(VERBS)
            if kind_role and role != kind_role:
                continue
            title = f"{verb} {R.choice(OBJECTS[domain])}".replace(":  ", ": ")
            if title not in titles:
                titles.add(title)
                return title, role, marks
        title = f"Доработать {R.choice(OBJECTS[domain])} (этап {len(titles)})"
        titles.add(title)
        return title, "developer", []

    def make_task(sprint, created, role_hint=None):
        global task_id
        title, role, marks = new_title(role_hint)
        assignee = R.choice(team[role] or team["developer"])[0]
        t = {"id": task_id, "project": pid, "title": title, "role": role, "marks": list(marks),
             "estimate": R.choice(ESTIMATES), "priority": R.choices([1, 2, 3, 4, 5], [1, 3, 5, 2, 1])[0],
             "created": created, "assignee": assignee, "sprint": sprint, "status": "todo",
             "events": [], "due": None, "completed": None}
        task_id += 1
        tasks.append(t)
        return t

    def work(t, s_start, s_end, finish, limit):
        """Ход работы над задачей в пределах спринта [s_start, s_end] и не позже limit:
        в работу, на проверку (иногда с возвратом на доработку), завершение (если finish).
        Продолжает с текущего статуса — задача могла перейти из прошлого спринта."""
        testers = [u[0] for u in team["tester"]] or [owner[0]]
        a = max(t["created"] + timedelta(hours=2), day_start(s_start))
        if t["events"]:
            a = max(a, t["events"][-1][2] + timedelta(hours=1))
        b = min(day_end(s_end), limit)
        if a >= b:
            return
        if t["status"] == "todo":
            t1 = rand_dt(a, a + (b - a) * 0.4)
            t["events"].append(("todo", "in_progress", t1, t["assignee"]))
            t["status"] = "in_progress"
        if t["status"] == "in_progress":
            if not finish and R.random() >= 0.85:
                return
            last = t["events"][-1][2]
            t2 = (last + (b - last) * R.uniform(0.2, 0.6)).replace(second=0, microsecond=0)
            if t2 <= last:
                return
            t["events"].append(("in_progress", "review", t2, t["assignee"]))
            t["status"] = "review"
            if R.random() < 0.2:          # возврат на доработку
                t3 = rand_dt(t2 + timedelta(hours=1), t2 + timedelta(days=1))
                t4 = rand_dt(t3 + timedelta(hours=2), t3 + timedelta(days=2))
                if t4 < b - timedelta(hours=1):
                    t["events"].append(("review", "in_progress", t3, R.choice(testers)))
                    t["events"].append(("in_progress", "review", t4, t["assignee"]))
        if t["status"] == "review" and finish:
            last = t["events"][-1][2]
            t5 = (last + (b - last) * R.uniform(0.2, 0.9)).replace(second=0, microsecond=0)
            if t5 <= last:
                return
            t["events"].append(("review", "done", t5, R.choice(testers)))
            t["status"] = "done"
            t["completed"] = t5

    # ---- спринты
    if pstatus in ("completed", "active", "cancelled"):
        s_start, number, carried = start, 1, []
        last_day = end if pstatus != "active" else TODAY + timedelta(days=13)
        while s_start <= last_day:
            s_end = s_start + timedelta(days=13)
            if pstatus == "active" and s_start > TODAY:
                s_status = "planned"
            elif pstatus == "active" and s_start <= TODAY <= s_end:
                s_status = "active"
            else:
                s_status = "closed"
            workers = len(team["developer"]) + len(team["tester"]) + len(team["analyst"])
            capacity = 20 * workers + R.choice([0, 10, 20])
            sid = sprint_id
            sprint_id += 1
            sprints.append([sid, pid, number, None, s_start, s_end, capacity, s_status])

            planned = [t for t in carried]
            for t in carried:
                t["sprint"] = sid
                if t["due"] and R.random() < 0.75:
                    t["due"] = s_end                   # при переносе срок обычно пересматривают
            load = sum(t["estimate"] for t in planned)
            # граница: активный спринт «Трекинга грузов» заполнен ровно на 100 %
            fill = 1.0 if (pid == 107 and s_status == "active") else R.uniform(0.7, 0.95)
            if s_status == "planned":
                fill = R.uniform(0.3, 0.6)
            while True:
                t = None
                created = min(rand_dt(day_start(s_start - timedelta(days=10)), day_start(s_start - timedelta(days=1))),
                              NOW - timedelta(hours=1))
                cand_est = R.choice(ESTIMATES)
                if load + cand_est > capacity * fill:
                    # добиваем ровно до ёмкости там, где это нужно для пограничного случая
                    rest = capacity * fill - load
                    if fill == 1.0 and rest >= 1:
                        t = make_task(sid, created)
                        t["estimate"] = int(rest)
                        load += t["estimate"]
                        planned.append(t)
                    break
                t = make_task(sid, created)
                t["estimate"] = cand_est
                load += cand_est
                planned.append(t)

            # ход спринта
            carried = []
            final_sprint = s_end >= end if end else False
            for t in planned:
                if s_status == "closed":
                    if pstatus == "completed" and final_sprint:
                        finish = True
                    else:
                        finish = R.random() < 0.85
                    work(t, s_start, s_end, finish, NOW)
                    if t["status"] != "done":
                        carried.append(t)
                elif s_status == "active":
                    r = R.random()
                    if r < 0.3:
                        work(t, s_start, s_end, True, NOW)
                    elif r < 0.75:
                        work(t, s_start, s_end, False, NOW)
                    # иначе задача ещё не начата
                if t["due"] is None and R.random() < 0.65:
                    t["due"] = s_end
            if s_status == "closed" and carried and (pstatus != "cancelled" or s_end < end):
                for t in carried:
                    t.setdefault("carried_at", []).append(day_end(s_end))
            if pstatus == "cancelled" and s_end >= end:
                # проект отменён: последний спринт закрыт, незавершённые задачи вернулись в бэклог
                for t in carried:
                    t["sprint"] = None
                break
            if s_status in ("active", "planned"):
                if s_status == "planned":
                    break
            s_start = s_end + timedelta(days=1)
            number += 1
            if pstatus == "completed" and s_start > end:
                break

    # ---- бэклог (без спринта)
    for _ in range(n_backlog):
        created = rand_dt(day_start(max(start - timedelta(days=20), date(2025, 9, 1))), NOW - timedelta(days=1))
        if pstatus == "planned":
            created = rand_dt(day_start(date(2026, 10, 1)), NOW - timedelta(days=1))
        t = make_task(None, created)
        r = R.random()
        if r < 0.3:
            t["estimate"] = None                       # ещё не оценена
        if R.random() < 0.35:
            t["assignee"] = None                       # ещё не назначена
        if R.random() < 0.4:
            # срок: часть сроков уже прошла — просроченные задачи бэклога
            t["due"] = (created + timedelta(days=R.randint(5, 40))).date()

for t in tasks:
    if t["estimate"] == 2 and R.random() < 0.05:
        t["estimate"] = 0                                  # пренебрежимо малая задача

# ------------------------------------------------------------------ бюджеты договоров
# Бюджет часов — от фактического объёма задач проекта: у действующих проектов с запасом
# на будущие задачи, у завершённых — близко к факту; у «Каталога продукции» намеренно
# перерасход (пограничный случай для отчёта по договорам).
FACTOR = {"completed": (1.0, 1.15), "active": (1.25, 1.5), "cancelled": (1.6, 2.0), "planned": (1.0, 1.0)}
for i, (pid, cust, number, signed, amount, hours) in enumerate(contracts):
    status = next(p[3] for p in PROJECTS if p[0] == pid)
    total = sum(t["estimate"] or 0 for t in tasks if t["project"] == pid)
    if status == "planned" or total == 0:
        budget = hours
    elif pid == 104:
        budget = round(total * 0.85 / 10) * 10
    else:
        budget = round(total * R.uniform(*FACTOR[status]) / 10) * 10
    rate = R.choice([2500, 2700, 2800, 3000, 3200])
    contracts[i] = (pid, cust, number, signed, budget * rate, budget)

# ------------------------------------------------------------------ история, комментарии, метки
for t in tasks:
    history.append((t["id"], None, "todo", t["created"], None))
    for (old, new, at, who) in t["events"]:
        history.append((t["id"], old, new, at, who))
    team_ids = [m[1] for m in members if m[0] == t["project"]]
    # комментарии по ходу работы
    evs = t["events"]
    pool = []
    if evs:
        pool.append((evs[0][2] + timedelta(minutes=R.randint(5, 90)), t["assignee"], R.choice(COMMENTS["start"])))
        if R.random() < 0.35:
            q_at = evs[0][2] + timedelta(hours=R.randint(2, 20))
            pool.append((q_at, t["assignee"], R.choice(COMMENTS["question"])))
            pool.append((q_at + timedelta(hours=R.randint(1, 6)), R.choice(team_ids), R.choice(COMMENTS["answer"])))
        for (old, new, at, who) in evs:
            if new == "review":
                pool.append((at, t["assignee"], R.choice(COMMENTS["review"])))
            elif old == "review" and new == "in_progress":
                pool.append((at, who, R.choice(COMMENTS["return"])))
            elif new == "done" and R.random() < 0.6:
                pool.append((at, who, R.choice(COMMENTS["done"])))
    for at in t.get("carried_at", []):
        pool.append((at - timedelta(hours=R.randint(1, 5)), t["assignee"] or R.choice(team_ids), R.choice(COMMENTS["carry"])))
    if t["status"] != "done" and t["due"] and t["due"] < TODAY and R.random() < 0.6:
        pool.append((day_start(t["due"] + timedelta(days=1)), R.choice(team_ids), R.choice(COMMENTS["overdue"])))
    limit = t["completed"] or NOW
    for (at, who, body) in sorted(pool, key=lambda x: x[0]):
        if at <= limit and at >= t["created"] and who is not None:
            comments.append((comment_id, t["id"], who, body, at))
            comment_id += 1
    # метки
    m = set(t["marks"])
    if t["priority"] == 1:
        m.add("срочно")
    if R.random() < 0.15:
        m.add(R.choice(list(MARK_NAMES)))
    for name in sorted(m):
        marks_tasks.append((MARK_NAMES[name], t["id"], t["created"] + timedelta(minutes=R.randint(1, 120))))


# ------------------------------------------------------------------ вывод SQL
def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, datetime):
        return f"'{v:%Y-%m-%d %H:%M}'"
    if isinstance(v, date):
        return f"'{v:%Y-%m-%d}'"
    return "'" + str(v).replace("'", "''") + "'"


out = []


def insert(table, cols, rows, chunk=200):
    out.append(f"\n-- {table}: {len(rows)}")
    for i in range(0, len(rows), chunk):
        part = rows[i:i + chunk]
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")
        out.append(",\n".join("    (" + ", ".join(lit(v) for v in r) + ")" for r in part) + ";")


out.append("""-- Демонстрационный набор данных. Сгенерирован db/seed/gen_demo.py (зерно 2026),
-- не редактировать вручную. Загружается после всех миграций (db/init.sh).
--
-- Пользовательские триггеры задач, проектов и договоров на время загрузки отключены:
-- это начальное наполнение, а не изменения пользователей, — аудит не нужен, а историю
-- статусов генератор формирует сам с исторически достоверными моментами времени.
-- Ограничения целостности (PK, FK, UNIQUE, CHECK, EXCLUDE) при этом проверяются.
BEGIN;
ALTER TABLE tasks DISABLE TRIGGER USER;
ALTER TABLE projects DISABLE TRIGGER USER;
ALTER TABLE contracts DISABLE TRIGGER USER;""")

insert("users", ["user_id", "full_name", "email", "created_at"], [u[:4] for u in users])
insert("customers", ["customer_id", "name", "contact_name", "email"], customers)
insert("projects", ["project_id", "name", "code", "status", "start_date", "end_date", "customer_id", "owner_id",
                    "description"],
       [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], next(m[1] for m in members if m[0] == p[0] and m[2] == "manager"),
         None) for p in PROJECTS])
insert("project_members", ["project_id", "user_id", "role", "joined_at"], members)
insert("contracts", ["project_id", "customer_id", "number", "signed_on", "amount", "budget_hours"], contracts)
insert("sprints", ["sprint_id", "project_id", "number", "goal", "start_date", "end_date", "capacity_hours", "status"],
       sprints)
insert("tasks", ["task_id", "project_id", "assignee_id", "title", "status", "priority", "created_at", "due_date",
                 "estimate_hours", "completed_at", "sprint_id"],
       [(t["id"], t["project"], t["assignee"], t["title"], t["status"], t["priority"], t["created"], t["due"],
         t["estimate"], t["completed"], t["sprint"]) for t in tasks])
insert("task_status_history", ["task_id", "old_status", "new_status", "changed_at", "changed_by"], history)
insert("comments", ["comment_id", "task_id", "author_id", "body", "created_at"], comments)
insert("marks_tasks", ["mark_id", "task_id", "date"], marks_tasks)

out.append("""
ALTER TABLE tasks ENABLE TRIGGER USER;
ALTER TABLE projects ENABLE TRIGGER USER;
ALTER TABLE contracts ENABLE TRIGGER USER;

SELECT setval('users_user_id_seq', (SELECT max(user_id) FROM users));
SELECT setval('customers_customer_id_seq', (SELECT max(customer_id) FROM customers));
SELECT setval('projects_project_id_seq', (SELECT max(project_id) FROM projects));
SELECT setval('sprints_sprint_id_seq', (SELECT max(sprint_id) FROM sprints));
SELECT setval('tasks_task_id_seq', (SELECT max(task_id) FROM tasks));
SELECT setval('comments_comment_id_seq', (SELECT max(comment_id) FROM comments));
COMMIT;

REFRESH MATERIALIZED VIEW mv_project_stats;
""")

path = Path(__file__).with_name("demo.sql")
path.write_text("\n".join(out), encoding="utf-8")
print(f"{path}: users {len(users)}, customers {len(customers)}, projects {len(PROJECTS)}, members {len(members)}, "
      f"contracts {len(contracts)}, sprints {len(sprints)}, tasks {len(tasks)}, history {len(history)}, "
      f"comments {len(comments)}, marks_tasks {len(marks_tasks)}")
