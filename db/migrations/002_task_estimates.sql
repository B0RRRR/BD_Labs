-- 002. Оценка и завершение задач (ЛР № 2).
-- estimate_hours — плановая трудоёмкость (NULL — задача не оценена);
-- completed_at — момент завершения, заполнен тогда и только тогда, когда задача выполнена.
-- Исходный сценарий с переносом данных ЛР № 1 — Lab2/migration.sql.

ALTER TABLE tasks ADD COLUMN estimate_hours NUMERIC(5, 1);
ALTER TABLE tasks ADD COLUMN completed_at   TIMESTAMP;

ALTER TABLE tasks ADD CONSTRAINT chk_tasks_estimate
    CHECK (estimate_hours >= 0);
ALTER TABLE tasks ADD CONSTRAINT chk_tasks_completed
    CHECK ((status = 'done') = (completed_at IS NOT NULL));
ALTER TABLE tasks ADD CONSTRAINT chk_tasks_completed_after_created
    CHECK (completed_at IS NULL OR completed_at >= created_at);
