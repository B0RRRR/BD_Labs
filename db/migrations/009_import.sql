-- 009. Пакетная загрузка задач (например, бэклога от заказчика из CSV).
-- Строки файла сначала копируются в промежуточную таблицу как текст (COPY),
-- затем import_tasks проверяет их, загружает корректные и сохраняет причину
-- отказа для остальных. Таблицы служебные.

CREATE TABLE import_batches (
    batch_id   SERIAL      PRIMARY KEY,
    file_name  TEXT        NOT NULL,
    created_at TIMESTAMP   NOT NULL DEFAULT now(),
    status     VARCHAR(10) NOT NULL DEFAULT 'new',
    loaded     INTEGER,
    rejected   INTEGER,
    error      TEXT,

    CONSTRAINT chk_import_status CHECK (status IN ('new', 'done', 'failed'))
);

CREATE TABLE import_task_rows (
    batch_id       INTEGER NOT NULL REFERENCES import_batches (batch_id) ON DELETE CASCADE,
    line_no        INTEGER NOT NULL,
    project_code   TEXT,
    title          TEXT,
    description    TEXT,
    priority       TEXT,
    estimate_hours TEXT,
    due_date       TEXT,
    assignee_email TEXT,
    error          TEXT,                    -- причина отказа; NULL — строка корректна
    task_id        INTEGER,                 -- созданная задача

    PRIMARY KEY (batch_id, line_no)
);

-- Дата из текста или NULL, если текст не является датой (2026-02-30 и т. п.).
CREATE FUNCTION try_date(s text) RETURNS date
LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN s::date;
EXCEPTION WHEN others THEN
    RETURN NULL;
END $$;

CREATE FUNCTION import_tasks(p_batch integer)
RETURNS TABLE (loaded integer, rejected integer)
LANGUAGE plpgsql AS $$
DECLARE
    n_ok  integer;
    n_bad integer;
BEGIN
    PERFORM 1 FROM import_batches WHERE batch_id = p_batch AND status = 'new' FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Пакет % не найден или уже обработан', p_batch USING ERRCODE = 'no_data_found';
    END IF;

    -- 1. Проверки. Каждая записывает причину только тем строкам, у которых её ещё нет,
    --    поэтому у строки остаётся первая найденная ошибка.
    UPDATE import_task_rows r SET error = 'неизвестный код проекта'
    WHERE batch_id = p_batch AND error IS NULL
      AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.code = upper(trim(r.project_code)));

    UPDATE import_task_rows r SET error = 'проект завершён или отменён'
    WHERE batch_id = p_batch AND error IS NULL
      AND EXISTS (SELECT 1 FROM projects p WHERE p.code = upper(trim(r.project_code))
                  AND p.status IN ('completed', 'cancelled'));

    UPDATE import_task_rows SET error = 'пустое или слишком длинное название'
    WHERE batch_id = p_batch AND error IS NULL
      AND (trim(COALESCE(title, '')) = '' OR length(trim(title)) > 200);

    UPDATE import_task_rows SET error = 'приоритет должен быть целым от 1 до 5'
    WHERE batch_id = p_batch AND error IS NULL
      AND trim(COALESCE(priority, '')) <> '' AND trim(priority) !~ '^[1-5]$';

    UPDATE import_task_rows SET error = 'оценка должна быть числом часов от 0 до 9999,9'
    WHERE batch_id = p_batch AND error IS NULL
      AND trim(COALESCE(estimate_hours, '')) <> ''
      AND replace(trim(estimate_hours), ',', '.') !~ '^\d{1,4}(\.\d)?$';

    UPDATE import_task_rows SET error = 'срок не является датой ГГГГ-ММ-ДД'
    WHERE batch_id = p_batch AND error IS NULL
      AND trim(COALESCE(due_date, '')) <> ''
      AND (trim(due_date) !~ '^\d{4}-\d{2}-\d{2}$' OR try_date(trim(due_date)) IS NULL);

    UPDATE import_task_rows r SET error = 'исполнитель не участвует в проекте'
    WHERE batch_id = p_batch AND error IS NULL
      AND trim(COALESCE(assignee_email, '')) <> ''
      AND NOT EXISTS (SELECT 1 FROM users u
                      JOIN project_members m ON m.user_id = u.user_id
                      JOIN projects p ON p.project_id = m.project_id
                      WHERE lower(u.email) = lower(trim(r.assignee_email))
                        AND p.code = upper(trim(r.project_code)));

    UPDATE import_task_rows r SET error = 'задача с таким названием уже есть в проекте'
    WHERE batch_id = p_batch AND error IS NULL
      AND EXISTS (SELECT 1 FROM tasks t JOIN projects p ON p.project_id = t.project_id
                  WHERE p.code = upper(trim(r.project_code)) AND t.title = trim(r.title));

    UPDATE import_task_rows r SET error = 'название повторяется в файле (строка ' || d.first_line || ')'
    FROM (SELECT line_no,
                 min(line_no) OVER (PARTITION BY upper(trim(project_code)), trim(title)) AS first_line
          FROM import_task_rows
          WHERE batch_id = p_batch AND error IS NULL) d
    WHERE r.batch_id = p_batch AND r.line_no = d.line_no AND d.line_no > d.first_line;

    -- 2. Загрузка корректных строк одной командой. Если она всё же упадёт
    --    (например, параллельно создали задачу с тем же названием), блок EXCEPTION
    --    откатит все вставки пакета, а пакет будет помечен как неуспешный.
    BEGIN
        WITH ins AS (
            INSERT INTO tasks (project_id, title, description, priority, estimate_hours, due_date, assignee_id)
            SELECT p.project_id,
                   trim(r.title),
                   nullif(trim(r.description), ''),
                   COALESCE(nullif(trim(r.priority), '')::smallint, 3),
                   nullif(replace(trim(r.estimate_hours), ',', '.'), '')::numeric,
                   nullif(trim(r.due_date), '')::date,
                   u.user_id
            FROM import_task_rows r
            JOIN projects p ON p.code = upper(trim(r.project_code))
            LEFT JOIN users u ON lower(u.email) = lower(nullif(trim(r.assignee_email), ''))
            WHERE r.batch_id = p_batch AND r.error IS NULL
            ORDER BY r.line_no
            RETURNING task_id, project_id, title
        )
        UPDATE import_task_rows r SET task_id = ins.task_id
        FROM ins JOIN projects p ON p.project_id = ins.project_id
        WHERE r.batch_id = p_batch AND r.error IS NULL
          AND upper(trim(r.project_code)) = p.code AND trim(r.title) = ins.title;
    EXCEPTION WHEN others THEN
        UPDATE import_batches SET status = 'failed', loaded = 0, error = SQLERRM
        WHERE batch_id = p_batch;
        SELECT count(*) INTO n_bad FROM import_task_rows WHERE batch_id = p_batch;
        RETURN QUERY SELECT 0, n_bad;
        RETURN;
    END;

    SELECT count(*) FILTER (WHERE error IS NULL), count(*) FILTER (WHERE error IS NOT NULL)
    INTO n_ok, n_bad
    FROM import_task_rows WHERE batch_id = p_batch;

    UPDATE import_batches SET status = 'done', loaded = n_ok, rejected = n_bad
    WHERE batch_id = p_batch;
    RETURN QUERY SELECT n_ok, n_bad;
END $$;
