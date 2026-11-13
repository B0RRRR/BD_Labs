"""
bench.py — замер времени выполнения SQL-модулей (запросы ЛР №2 и отчёт).

Каждый запрос выполняется через EXPLAIN (ANALYZE, FORMAT JSON) несколько
раз; берётся медиана «Planning Time + Execution Time». Первый прогон —
прогрев кэша, в расчёт не идёт.

Запуск:
    python3 bench.py <база> [повторов] [таймаут_с]
    python3 bench.py project_db_load 5 600
"""
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

LABELS = [
    "2.1.1 Подробная информация о незавершённых задачах",
    "2.1.2 Участники без задач (LEFT JOIN + IS NULL)",
    "2.1.3 Задачи для эскалации",
    "2.2.1 Задачи проекта по статусам",
    "2.2.2 Перегруженные сотрудники (HAVING)",
    "2.2.3 Поток задач по месяцам",
    "3.1 Задачи дольше среднего по проекту",
    "3.2 Сотрудники с просрочкой (EXISTS)",
    "3.3 Проекты без тестировщика (NOT EXISTS)",
    "3.4 Загрузка участника в проекте (коррелированный)",
    "доп. Задачи без ответа исполнителя (коррелированный)",
    "доп. Порядок вступления в проект (ROW_NUMBER)",
    "доп. Доля участника в выполненных часах (окно)",
]


def statements(path):
    """Разбивает файл на SQL-операторы, выбрасывая строки-комментарии."""
    text = "\n".join(
        line for line in Path(path).read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )
    return [s.strip() for s in re.split(r";\s*\n", text + "\n") if s.strip()]


def run(db, sql, timeout_s):
    cmd = ["psql", "-X", "-q", "-A", "-t", "-d", db,
           "-c", f"SET statement_timeout = '{timeout_s}s'",
           "-c", f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        return None, out.stderr.strip().splitlines()[-1]
    plan = json.loads(out.stdout)[0]
    return plan["Planning Time"] + plan["Execution Time"], plan["Plan"].get("Actual Rows")


def main():
    db = sys.argv[1]
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    timeout_s = int(sys.argv[3]) if len(sys.argv) > 3 else 600

    modules = list(zip(LABELS, statements(ROOT / "Lab2" / "queries.sql")))
    modules.append(("4 Аналитический отчёт на CTE (report.sql)",
                    statements(ROOT / "Lab2" / "report.sql")[0]))

    print(f"{'модуль':<58} {'медиана, мс':>12} {'строк':>7}")
    for label, sql in modules:
        times, rows = [], None
        for attempt in range(repeats + 1):
            t, rows = run(db, sql, timeout_s)
            if t is None:
                break
            if attempt > 0 or t > 60_000:
                times.append(t)
            if t > 60_000:          # долгий запрос — достаточно одного замера
                break
        if not times:
            print(f"{label:<58} {'ОШИБКА':>12}  {rows}")
        else:
            print(f"{label:<58} {statistics.median(times):>12.2f} {rows:>7}", flush=True)


if __name__ == "__main__":
    main()
