-- Демонстрация атомарности составных бизнес-операций: успешное выполнение
-- и полный откат при ошибке. Запускать на демонстрационной копии базы:
--   psql -d pm_demo -f db/demo/transactions.sql
-- Ошибки в сценарии ожидаемы: после каждой показывается, что данные не изменились.
\set ON_ERROR_STOP off
\pset footer off
SELECT set_config('app.user_id', (SELECT user_id::text FROM users WHERE email = 'ivanov@mail.ru'), false) \g /dev/null

\echo '=== 1. Создание проекта с командой и договором: успех ==='
SELECT create_project(
    'Демо: портал дилеров', 'DEMO', (SELECT user_id FROM users WHERE email = 'ivanov@mail.ru'),
    '2026-11-16', '2027-02-26', (SELECT customer_id FROM customers WHERE name = 'АО «Вектор»'), NULL,
    '[{"user_id": 3, "role": "developer"}, {"user_id": 4, "role": "tester"}]',
    '{"number": "Д-2026/090", "signed_on": "2026-11-12", "amount": 750000, "budget_hours": 250}'
) AS project_id \gset
SELECT p.code, p.status,
       (SELECT count(*) FROM project_members m WHERE m.project_id = p.project_id) AS members,
       c.number AS contract
FROM projects p LEFT JOIN contracts c USING (project_id)
WHERE p.project_id = :project_id;

\echo '=== 2. Создание проекта: ошибка на последнем шаге (номер договора занят) ==='
\echo '    проект и команда уже вставлены функцией, но откатываются вместе с договором'
SELECT create_project(
    'Демо: второй портал', 'DEMO2', (SELECT user_id FROM users WHERE email = 'ivanov@mail.ru'),
    '2026-11-16', NULL, (SELECT customer_id FROM customers WHERE name = 'АО «Вектор»'), NULL,
    '[{"user_id": 3, "role": "developer"}]',
    '{"number": "Д-2026/090", "signed_on": "2026-11-12", "amount": 1, "budget_hours": 1}');
SELECT count(*) AS "проектов DEMO2 (ожидается 0)" FROM projects WHERE code = 'DEMO2';

\echo '=== Подготовка: спринт 1 (активный) и спринт 2 (запланирован, ёмкость 15 ч) ==='
INSERT INTO sprints (project_id, number, start_date, end_date, capacity_hours, status) VALUES
    (:project_id, 1, '2026-11-16', '2026-11-29', 40, 'active'),
    (:project_id, 2, '2026-11-30', '2026-12-13', 15, 'planned');
INSERT INTO tasks (project_id, title, status, estimate_hours, assignee_id, sprint_id, completed_at)
SELECT :project_id, v.title, v.status, v.hours, 3,
       (SELECT sprint_id FROM sprints WHERE project_id = :project_id AND number = 1),
       CASE WHEN v.status = 'done' THEN now() END
FROM (VALUES ('Макет каталога дилеров', 'done', 16),
             ('API заказов дилера',     'in_progress', 12),
             ('Форма заявки дилера',    'review', 8)) AS v(title, status, hours);
SELECT number, status, capacity_hours, planned_hours, tasks
FROM v_sprint_load WHERE project_id = :project_id ORDER BY number;

\echo '=== 3. Закрытие спринта: незавершённые 20 ч не помещаются в спринт 2 (15 ч) ==='
SELECT close_sprint((SELECT sprint_id FROM sprints WHERE project_id = :project_id AND number = 1));
\echo '    состояние не изменилось: спринт 1 активен, задачи на месте'
SELECT number, status, capacity_hours, planned_hours, tasks
FROM v_sprint_load WHERE project_id = :project_id ORDER BY number;

\echo '=== 4. Ёмкость спринта 2 увеличена до 30 ч — закрытие проходит ==='
UPDATE sprints SET capacity_hours = 30 WHERE project_id = :project_id AND number = 2;
SELECT close_sprint((SELECT sprint_id FROM sprints WHERE project_id = :project_id AND number = 1)) AS moved_tasks;
SELECT number, status, capacity_hours, planned_hours, tasks, tasks_done
FROM v_sprint_load WHERE project_id = :project_id ORDER BY number;

\echo '=== 5. Транзакция приложения из нескольких команд: задача сдана на проверку с комментарием ==='
\echo '    комментарий пустой → CHECK → откатывается и смена статуса'
BEGIN;
UPDATE tasks SET status = 'review'
WHERE project_id = :project_id AND title = 'API заказов дилера';
INSERT INTO comments (task_id, author_id, body)
SELECT task_id, 3, '   ' FROM tasks WHERE project_id = :project_id AND title = 'API заказов дилера';
COMMIT;
SELECT title, status AS "статус (ожидается in_progress)"
FROM tasks WHERE project_id = :project_id AND title = 'API заказов дилера';

\echo '=== 6. Что записали триггеры: история статусов и аудит ==='
SELECT h.changed_at::timestamp(0), t.title, h.old_status, h.new_status, h.changed_by
FROM task_status_history h JOIN tasks t USING (task_id)
WHERE t.project_id = :project_id ORDER BY h.history_id;
SELECT a.table_name, a.operation, a.row_key, a.app_user_id, a.old_data, a.new_data
FROM audit_log a
WHERE (a.table_name = 'tasks' AND a.row_key IN (SELECT task_id::text FROM tasks WHERE project_id = :project_id))
   OR (a.table_name IN ('projects', 'contracts') AND a.row_key = :'project_id')
ORDER BY a.audit_id;
