-- Пакетная загрузка задач из CSV средствами psql:
--   psql -v file=db/import/tasks_sample.csv -f db/import/import_tasks.sql
-- Формат файла: заголовок и столбцы
--   project_code,title,description,priority,estimate_hours,due_date,assignee_email
\set ON_ERROR_STOP on

INSERT INTO import_batches (file_name) VALUES (:'file') RETURNING batch_id AS batch \gset

-- Временная таблица с порядковым номером: так сохраняется номер строки файла.
CREATE TEMP TABLE raw_rows (
    n              serial,
    project_code   text, title text, description text, priority text,
    estimate_hours text, due_date text, assignee_email text
);
SELECT format('\copy raw_rows (project_code, title, description, priority, estimate_hours, due_date, assignee_email) FROM %L WITH (FORMAT csv, HEADER true)', :'file') AS copy_cmd \gset
:copy_cmd

INSERT INTO import_task_rows (batch_id, line_no, project_code, title, description, priority,
                              estimate_hours, due_date, assignee_email)
SELECT :batch, n + 1, project_code, title, description, priority, estimate_hours, due_date, assignee_email
FROM raw_rows;

SELECT * FROM import_tasks(:batch);

SELECT line_no, project_code, title, error
FROM import_task_rows
WHERE batch_id = :batch AND error IS NOT NULL
ORDER BY line_no;
