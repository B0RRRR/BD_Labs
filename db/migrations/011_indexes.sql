-- 011. Индексы по результатам исследования производительности (db/perf/bench.py).
--
-- PostgreSQL сам индексирует только PRIMARY KEY, UNIQUE и EXCLUDE. Внешние ключи
-- без индекса дают полный просмотр таблицы при поиске по ним, а ещё при каскадном
-- удалении и проверке RESTRICT у родительской таблицы. Индекс tasks(project_id) не
-- нужен: его роль играет уникальный индекс (project_id, title).

-- задачи спринта: загрузка спринта, проверка ёмкости в триггере, закрытие спринта
CREATE INDEX IF NOT EXISTS ix_tasks_sprint ON tasks (sprint_id);
-- задачи участника в проекте: нагрузка, составной FK на project_members
CREATE INDEX IF NOT EXISTS ix_tasks_project_assignee ON tasks (project_id, assignee_id);
-- комментарии задачи и комментарии автора (активность, RESTRICT при удалении пользователя)
CREATE INDEX IF NOT EXISTS ix_comments_task ON comments (task_id);
CREATE INDEX IF NOT EXISTS ix_comments_author ON comments (author_id);
-- история задачи в порядке времени
CREATE INDEX IF NOT EXISTS ix_history_task ON task_status_history (task_id, changed_at);
-- метки задачи (карточка задачи в v_task_cards)
CREATE INDEX IF NOT EXISTS ix_marks_tasks_task ON marks_tasks (task_id);
-- проекты пользователя, каскад при удалении пользователя
CREATE INDEX IF NOT EXISTS ix_members_user ON project_members (user_id);
