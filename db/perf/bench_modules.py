"""Время выполнения всех SQL-модулей (запросы queries.sql и отчёты reports.sql).

Каждый модуль выполняется через EXPLAIN (ANALYZE): первый прогон — прогрев,
затем медиана трёх прогонов (модуль дольше 30 с — один прогон).
Переменные psql подставляются: today = 2026-11-14, project — код проекта.

    python3 db/perf/bench_modules.py <база> <метка> [код_проекта]
Результат — db/perf/modules_<метка>.json: {"номер модуля": [мс, строк]}.
"""
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
Q = HERE.parent / "queries"


def statements(path):
    lines = [l for l in path.read_text(encoding="utf-8").splitlines()
             if not l.lstrip().startswith("--") and not l.lstrip().startswith("\\") and "\\gset" not in l]
    text = "\n".join(lines)
    return [s.strip() for s in re.split(r";\s*\n", text + "\n") if s.strip()]


def run(db, sql):
    out = subprocess.run(["psql", "-X", "-q", "-A", "-t", "-d", db,
                          "-c", "SET statement_timeout = '20min'",
                          "-c", f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    plan = json.loads(out.stdout)[0]
    return plan["Planning Time"] + plan["Execution Time"], plan["Plan"].get("Actual Rows")


def main():
    db, label = sys.argv[1], sys.argv[2]
    project = sys.argv[3] if len(sys.argv) > 3 else "TRACK"
    mods = statements(Q / "queries.sql") + statements(Q / "reports.sql")
    names = [str(i) for i in range(1, len(mods) - 1)] + ["О1", "О2"]
    res = {}
    for name, sql in zip(names, mods):
        sql = sql.replace(":'today'::date", "DATE '2026-11-14'").replace(":'project'", f"'{project}'")
        times, rows = [], None
        for attempt in range(4):
            t, rows = run(db, sql)
            if attempt > 0 or t > 30_000:
                times.append(t)
            if t > 30_000:
                break
        res[name] = [round(statistics.median(times), 2), rows]
        print(f"{label:6} {name:3} {res[name][0]:12.2f} мс  строк {rows}", flush=True)
    (HERE / f"modules_{label}.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
