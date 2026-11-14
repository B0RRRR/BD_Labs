-- 003. Метки задач и коды проектов.
-- Код проекта — короткий префикс ключа задачи (SHOP-42).
-- Исходный сценарий с переносом данных — Lab1/migration_tags.sql.

CREATE TABLE marks (
    mark_id SERIAL PRIMARY KEY,
    name    TEXT   NOT NULL UNIQUE,
    color   VARCHAR(20),

    CHECK (color LIKE '#______')
);

CREATE TABLE marks_tasks (
    mark_id INTEGER   NOT NULL REFERENCES marks (mark_id) ON DELETE RESTRICT,
    task_id INTEGER   NOT NULL REFERENCES tasks (task_id) ON DELETE CASCADE,
    date    TIMESTAMP NOT NULL DEFAULT now(),

    PRIMARY KEY (mark_id, task_id)
);

ALTER TABLE projects ADD COLUMN code VARCHAR(5) UNIQUE;
ALTER TABLE projects ADD CONSTRAINT chk_code
    CHECK (length(code) BETWEEN 2 AND 5 AND code = upper(code));
ALTER TABLE projects ALTER COLUMN code SET NOT NULL;
