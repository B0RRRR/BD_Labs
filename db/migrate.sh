#!/bin/sh
# Применяет ещё не применённые миграции db/migrations/NNN_*.sql по порядку номеров.
# Каждая миграция выполняется в отдельной транзакции и записывается в schema_migrations.
# Подключение — стандартными переменными PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE.
#
#   ./migrate.sh        — все миграции
#   ./migrate.sh 004    — только до 004 включительно
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
LAST=${1:-999}

psql -q -X -v ON_ERROR_STOP=1 -c "SET client_min_messages = warning" -c "CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT      PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT now())"

for f in "$DIR"/migrations/[0-9][0-9][0-9]_*.sql; do
    v=$(basename "$f" .sql)
    num=${v%%_*}
    [ "$num" -gt "$LAST" ] && break
    if [ -z "$(psql -X -At -c "SELECT 1 FROM schema_migrations WHERE version = '$v'")" ]; then
        echo "миграция $v"
        psql -q -X -v ON_ERROR_STOP=1 -1 -f "$f" \
             -c "INSERT INTO schema_migrations (version) VALUES ('$v')"
    fi
done
