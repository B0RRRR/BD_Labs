#!/bin/bash
# Исследование конкурентного доступа: два руководителя одновременно планируют
# задачи в один спринт. Инвариант: сумма оценок задач спринта ≤ его ёмкости.
#
# Запуск: PGDATABASE=project_mgmt db/demo/concurrency.sh
# Работает на временной копии базы pm_conc_demo и удаляет её в конце.
#
# Сценарии (спринт 10 ч, задачи A и B по 6 ч — вместе не помещаются):
#   1) проверка без блокировки, READ COMMITTED — аномалия: обе транзакции видят
#      свободные 10 ч, обе фиксируются, в спринте 12 ч;
#   2) рабочая версия: триггер блокирует строку спринта (FOR UPDATE) — вторая
#      транзакция ждёт первую, видит её задачу и получает ошибку PM004;
#   3) проверка без блокировки, SERIALIZABLE — СУБД обнаруживает конфликт, одна
#      транзакция получает ошибку сериализации 40001, клиент повторяет её,
#      повтор видит чужую задачу и получает PM004.
set -u
SRC=${PGDATABASE:?задайте PGDATABASE — базу, копию которой использовать}
DB=pm_conc_demo
DIR=$(cd "$(dirname "$0")" && pwd)
export PGDATABASE=$DB

dropdb --if-exists $DB 2>/dev/null
createdb -T "$SRC" $DB || exit 1
q() { psql -X -q -At -v ON_ERROR_STOP=1 "$@"; }
ts() { date +%T.%3N; }

# ---------------------------------------------------------------- подготовка
read -r SPRINT TA TB <<<"$(q <<'SQL'
SELECT create_project('Демо: конкурентное планирование', 'CONC', 1, '2026-11-16', NULL, NULL, NULL,
                      '[{"user_id": 3}, {"user_id": 4}]') \gset
INSERT INTO sprints (project_id, number, start_date, end_date, capacity_hours, status)
VALUES (:create_project, 1, '2026-11-16', '2026-11-29', 10, 'active');
INSERT INTO tasks (project_id, title, estimate_hours, assignee_id) VALUES
    (:create_project, 'Задача A', 6, 3),
    (:create_project, 'Задача B', 6, 4);
SELECT (SELECT sprint_id FROM sprints WHERE project_id = :create_project) || ' ' ||
       (SELECT task_id FROM tasks WHERE project_id = :create_project AND title = 'Задача A') || ' ' ||
       (SELECT task_id FROM tasks WHERE project_id = :create_project AND title = 'Задача B');
SQL
)"

reset() { q -c "UPDATE tasks SET sprint_id = NULL WHERE task_id IN ($TA, $TB)"; }
state() {
    q -c "SELECT 'итог: в спринте ' || planned_hours || ' ч при ёмкости ' || capacity_hours ||
                 CASE WHEN planned_hours > capacity_hours THEN ' — ИНВАРИАНТ НАРУШЕН' ELSE ' — инвариант соблюдён' END
          FROM v_sprint_load WHERE sprint_id = $SPRINT"
}

# Сессия: $1 — имя, $2 — уровень изоляции, $3 — задача, $4 — пауза перед COMMIT (с).
# Возвращает 40 при ошибке сериализации, 1 — при другой ошибке.
session() {
    local out
    out=$(psql -X -q -At -v ON_ERROR_STOP=1 -v VERBOSITY=verbose 2>&1 <<SQL
BEGIN ISOLATION LEVEL $2;
SELECT to_char(clock_timestamp(), 'HH24:MI:SS.MS') || ' планирую задачу $3 в спринт $SPRINT';
UPDATE tasks SET sprint_id = $SPRINT WHERE task_id = $3;
SELECT to_char(clock_timestamp(), 'HH24:MI:SS.MS') || ' проверка пройдена, вижу в спринте '
       || (SELECT sum(estimate_hours) FROM tasks WHERE sprint_id = $SPRINT) || ' ч';
SELECT pg_sleep($4);
COMMIT;
SQL
    )
    local rc=$?
    echo "$out" | grep -v '^$' | grep -v '^LOCATION' | sed "s/^/  [$1] /"
    if [ $rc -ne 0 ]; then
        echo "  [$1] $(ts) транзакция отменена"
        echo "$out" | grep -q '40001' && return 40
        return 1
    fi
    echo "  [$1] $(ts) COMMIT"
}

# Сессия с повтором при ошибке сериализации (как это делает приложение).
session_retry() {
    local attempt
    for attempt in 1 2 3; do
        session "$@"
        [ $? -ne 40 ] && return
        echo "  [$1] ошибка сериализации 40001 — повтор, попытка $((attempt + 1))"
    done
}

run_pair() {   # $1 — уровень изоляции, $2 — функция сессии
    reset
    $2 A "$1" "$TA" 2 &
    sleep 0.5
    $2 B "$1" "$TB" 0 &
    wait
    state
}

# Наивная версия триггера — та же проверка без блокировки строки спринта.
GUARD=$(mktemp)
q -c "SELECT pg_get_functiondef('sprint_capacity_guard'::regproc)" > "$GUARD"
NAIVE=$(sed 's/FROM sprints WHERE sprint_id = NEW.sprint_id FOR UPDATE;/FROM sprints WHERE sprint_id = NEW.sprint_id;/' "$GUARD")

echo "=== 1. Проверка без блокировки, READ COMMITTED ==="
echo "$NAIVE" | q
run_pair "READ COMMITTED" session

echo
echo "=== 2. Рабочая версия: блокировка строки спринта (FOR UPDATE), READ COMMITTED ==="
q -f "$GUARD"
run_pair "READ COMMITTED" session

echo
echo "=== 3. Проверка без блокировки, SERIALIZABLE, повтор при ошибке 40001 ==="
echo "$NAIVE" | q
run_pair "SERIALIZABLE" session_retry

rm -f "$GUARD"
dropdb $DB
