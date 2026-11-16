#!/bin/sh
# Развёртывание базы с нуля (в пустую БД):
#   1) миграции 001–004 — схема лабораторных работ;
#   2) контрольный набор данных (seed/control.sql);
#   3) миграции 005 и далее — они переносят уже загруженные данные;
#   4) контрольные трудозатраты (seed/control_worklogs.sql) и база данных качества
#      (seed/quality.sql): требования, критерии, испытания;
#   5) демонстрационный набор (seed/demo.sql), если SEED_DEMO не равен 0;
#   6) пароль роли приложения из APP_DB_PASSWORD.
# Подключение — переменными PGHOST, PGUSER, PGPASSWORD, PGDATABASE.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)

"$DIR/migrate.sh" 004
psql -q -X -v ON_ERROR_STOP=1 -f "$DIR/seed/control.sql" >/dev/null
"$DIR/migrate.sh"
psql -q -X -v ON_ERROR_STOP=1 -f "$DIR/seed/control_worklogs.sql" >/dev/null
psql -q -X -v ON_ERROR_STOP=1 -f "$DIR/seed/quality.sql" >/dev/null
if [ "${SEED_DEMO:-1}" != "0" ]; then
    echo "демонстрационные данные"
    psql -q -X -v ON_ERROR_STOP=1 -f "$DIR/seed/demo.sql" >/dev/null
fi
if [ -n "${APP_DB_PASSWORD:-}" ]; then
    echo "ALTER ROLE pm_app PASSWORD :'pw'" | psql -q -X -v ON_ERROR_STOP=1 -v pw="$APP_DB_PASSWORD"
fi
echo "база готова"
