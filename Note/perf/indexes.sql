-- =====================================================================
-- indexes.sql — предлагаемая оптимизация по результатам нагрузочного
-- тестирования (раздел «Оценка качества» записки).
--
-- PostgreSQL автоматически создаёт индексы только для PRIMARY KEY и
-- UNIQUE. Внешние ключи остаются без индексов, поэтому поиск
-- «комментарии задачи», «комментарии автора», «задачи исполнителя»
-- выполняется полным просмотром таблицы. В коррелированных подзапросах
-- такой просмотр повторяется для каждой строки внешнего запроса.
--
-- Индекс tasks(project_id) не нужен: его роль выполняет составной
-- уникальный индекс uq_tasks_project_title (project_id, title) —
-- project_id стоит в нём первым.
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_comments_task      ON comments (task_id);
CREATE INDEX IF NOT EXISTS idx_comments_author    ON comments (author_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee     ON tasks (assignee_id);
CREATE INDEX IF NOT EXISTS idx_members_user       ON project_members (user_id);
CREATE INDEX IF NOT EXISTS idx_marks_tasks_task   ON marks_tasks (task_id);

ANALYZE;
