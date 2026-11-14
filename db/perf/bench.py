"""Исследование производительности: запросы и операции записи до и после индексов
миграции 011_indexes.sql.

Каждая команда выполняется через EXPLAIN (ANALYZE, BUFFERS): первый прогон — прогрев
кэша, затем берётся медиана времени из нескольких прогонов. Изменяющие команды
выполняются внутри BEGIN ... ROLLBACK и данных не меняют. Планы сохраняются в
db/perf/plans/, сводка — в db/perf/results.md.

Запуск (на базе с нагрузочными данными, см. load_data.sql):
    python3 db/perf/bench.py pm_perf [повторов]
Нужен только psql; подключение — переменными PGHOST, PGUSER, PGPASSWORD.
"""
import re
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIGRATION = HERE.parent / "migrations" / "011_indexes.sql"
SLOW_MS = 30_000            # долгую команду достаточно выполнить один раз

# Параметры подставляются из базы (см. params()): {pid} — действующий проект,
# {sprint} — его активный спринт, {task} — задача бэклога, помещающаяся в спринт,
# {hist_task} — завершённая задача, {pid_del} — проект для каскадного удаления задач.
QUERIES = [
    ("Q1", "Открытые задачи проекта, первая страница списка (v_task_cards)", """
        SELECT task_key, title, status, priority, due_date, assignee_name, marks
        FROM v_task_cards
        WHERE project_id = {pid} AND status <> 'done'
        ORDER BY priority, due_date NULLS LAST, task_id
        LIMIT 20"""),
    ("Q2", "Загрузка спринтов проекта (v_sprint_load)", """
        SELECT number, status, capacity_hours, planned_hours, done_hours, load_pct
        FROM v_sprint_load WHERE project_id = {pid} ORDER BY number"""),
    ("Q3", "Планирование задачи в спринт (UPDATE + триггер проверки ёмкости)", """
        UPDATE tasks SET sprint_id = {sprint} WHERE task_id = {task}"""),   # с откатом, см. ROLLBACK_KEYS
    ("Q4", "История статусов задачи (карточка задачи)", """
        SELECT old_status, new_status, changed_at, changed_by
        FROM task_status_history WHERE task_id = {hist_task} ORDER BY changed_at"""),
    ("Q5", "Нагрузка и активность участников действующих проектов (коррелированные подзапросы)", """
        SELECT p.code, u.full_name, pm.role,
               (SELECT count(*) FROM tasks t
                 WHERE t.project_id = pm.project_id AND t.assignee_id = pm.user_id
                   AND t.status <> 'done') AS open_tasks,
               (SELECT COALESCE(sum(t.estimate_hours), 0) FROM tasks t
                 WHERE t.project_id = pm.project_id AND t.assignee_id = pm.user_id
                   AND t.status <> 'done') AS open_hours,
               (SELECT max(c.created_at) FROM comments c JOIN tasks t ON t.task_id = c.task_id
                 WHERE t.project_id = pm.project_id AND c.author_id = pm.user_id) AS last_comment
        FROM project_members pm
        JOIN projects p ON p.project_id = pm.project_id
        JOIN users u ON u.user_id = pm.user_id
        WHERE p.status = 'active'"""),
    ("Q6", "Отчёт о рисках по всем действующим проектам (reports.sql, отчёт 1)", None),
]
ROLLBACK_KEYS = {"Q3"}       # изменяющие команды из списка запросов выполняются с откатом
WRITES = [
    ("W1", "Вставка 10 000 задач (с триггерами истории и аудита)", """
        INSERT INTO tasks (project_id, title, estimate_hours, priority)
        SELECT {pid}, 'Пакетная задача ' || g, 4, 3 FROM generate_series(1, 10000) AS g"""),
    ("W2", "Изменение приоритета 10 000 задач (неиндексированный столбец)", """
        UPDATE tasks SET priority = priority % 5 + 1
        WHERE task_id IN (SELECT task_id FROM tasks ORDER BY task_id LIMIT 10000)"""),
    ("W3", "Вынос 10 000 задач из спринтов (индексированный столбец sprint_id)", """
        UPDATE tasks SET sprint_id = NULL
        WHERE task_id IN (SELECT task_id FROM tasks WHERE sprint_id IS NOT NULL ORDER BY task_id LIMIT 10000)"""),
    ("W4", "Удаление 100 задач проекта с каскадом на комментарии, историю и метки", """
        DELETE FROM tasks WHERE project_id = {pid_del}"""),
]


def psql(db, *commands, timeout=900):
    args = ["psql", "-X", "-q", "-A", "-t", "-d", db]
    for c in commands:
        args += ["-c", c]
    out = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return out.stdout.strip()


def params(db):
    row = psql(db, """
        WITH p AS (SELECT project_id FROM projects WHERE code = 'L0508'),
             s AS (SELECT sprint_id FROM sprints WHERE project_id = (SELECT project_id FROM p) AND status = 'active')
        SELECT (SELECT project_id FROM p),
               (SELECT sprint_id FROM s),
               (SELECT min(task_id) FROM tasks WHERE project_id = (SELECT project_id FROM p)
                  AND sprint_id IS NULL AND estimate_hours <= 12),
               (SELECT min(task_id) FROM tasks WHERE project_id = (SELECT project_id FROM p) AND status = 'done'),
               (SELECT project_id FROM projects WHERE code = 'L0509')""")
    pid, sprint, task, hist_task, pid_del = row.split("|")
    return dict(pid=pid, sprint=sprint, task=task, hist_task=hist_task, pid_del=pid_del)


def risk_report():
    text = (HERE.parent / "queries" / "reports.sql").read_text(encoding="utf-8")
    start = text.index("WITH\n")
    end = text.index(";", text.index("ORDER BY CASE risk"))
    return text[start:end].replace(":'today'::date", "DATE '2026-11-14'")


def explain(db, sql, write):
    stmt = f"EXPLAIN (ANALYZE, BUFFERS) {sql}"
    cmds = ["SET statement_timeout = '15min'"]
    cmds += ["BEGIN", stmt, "ROLLBACK"] if write else [stmt]
    plan = psql(db, *cmds)
    ms = float(re.search(r"Execution Time: ([\d.]+) ms", plan).group(1))
    ms += float(re.search(r"Planning Time: ([\d.]+) ms", plan).group(1))
    buf = re.search(r"Buffers: shared(?: hit=(\d+))?(?: read=(\d+))?", plan)
    blocks = (int(buf.group(1) or 0) + int(buf.group(2) or 0)) if buf else 0
    return ms, blocks, plan


def measure(db, items, prm, repeats, phase, write):
    res = {}
    for key, title, sql in items:
        sql = (sql or risk_report()).format(**prm)
        times, last = [], None
        for attempt in range(repeats + 1):
            ms, blocks, plan = explain(db, sql, write or key in ROLLBACK_KEYS)
            last = (blocks, plan)
            if attempt > 0 or ms > SLOW_MS:
                times.append(ms)
            if ms > SLOW_MS:
                break
        res[key] = (statistics.median(times), last[0])
        (HERE / "plans" / f"{key}_{phase}.txt").write_text(sql.strip() + "\n\n" + last[1] + "\n", encoding="utf-8")
        print(f"  {phase:6} {key}: {res[key][0]:10.2f} мс, блоков {res[key][1]}", flush=True)
    return res


def main():
    db = sys.argv[1]
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    (HERE / "plans").mkdir(exist_ok=True)
    names = re.findall(r"CREATE INDEX IF NOT EXISTS (\w+)", MIGRATION.read_text(encoding="utf-8"))
    prm = params(db)
    sizes = psql(db, "SELECT count(*) FROM tasks", "SELECT count(*) FROM comments",
                 "SELECT count(*) FROM task_status_history").split("\n")

    psql(db, *[f"DROP INDEX IF EXISTS {n}" for n in names], "ANALYZE")
    before = measure(db, QUERIES, prm, repeats, "before", False)
    before_w = measure(db, WRITES, prm, 3, "before", True)

    psql(db, MIGRATION.read_text(encoding="utf-8"), "ANALYZE")
    size = psql(db, "SELECT pg_size_pretty(sum(pg_relation_size(c.oid))) FROM pg_class c "
                    f"WHERE c.relname IN ({', '.join(repr(n) for n in names)})")
    after = measure(db, QUERIES, prm, repeats, "after", False)
    after_w = measure(db, WRITES, prm, 3, "after", True)

    def table(items, b, a):
        rows = ["| № | Команда | До, мс | После, мс | Ускорение | Блоков до | Блоков после |",
                "|---|---|---:|---:|---:|---:|---:|"]
        for key, title, _ in items:
            (tb, bb), (ta, ba) = b[key], a[key]
            rows.append(f"| {key} | {title} | {tb:.2f} | {ta:.2f} | {tb / ta:.1f} | {bb} | {ba} |")
        return "\n".join(rows)

    md = [f"# Результаты исследования производительности\n",
          f"Данные: задач {sizes[0]}, комментариев {sizes[1]}, записей истории {sizes[2]}. "
          f"Медиана из {repeats} прогонов после прогрева (команды дольше {SLOW_MS // 1000} с — один прогон). "
          f"Индексы миграции 011: {', '.join(names)}; их размер {size}.\n",
          "## Запросы\n", table(QUERIES, before, after),
          "\n## Операции записи (BEGIN … ROLLBACK)\n", table(WRITES, before_w, after_w),
          "\nПланы выполнения — в каталоге plans/ (суффиксы _before и _after).\n"]
    (HERE / "results.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
