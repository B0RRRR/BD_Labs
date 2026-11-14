-- Сквозной сценарий процесса «Выполнение задачи проекта» (модель BPMN):
-- создать задачу → оценить, назначить, включить в спринт → взять в работу →
-- передать на проверку → вернуть с замечанием → снова на проверку → принять.
-- Запуск на копии базы: psql -d pm_demo -f db/demo/scenario.sql
\set ON_ERROR_STOP on
\pset footer off
-- руководитель MOB
SELECT set_config('app.user_id', '1', false) \g /dev/null

INSERT INTO tasks (project_id, title, priority)
SELECT project_id, 'Экран оплаты подпиской', 2 FROM projects WHERE code = 'MOB'
RETURNING task_id AS t \gset

UPDATE tasks SET estimate_hours = 8, assignee_id = 3, due_date = '2026-11-20',
                 sprint_id = (SELECT sprint_id FROM sprints s JOIN projects p USING (project_id)
                              WHERE p.code = 'MOB' AND s.status = 'active')
WHERE task_id = :t;

-- исполнитель
SELECT set_config('app.user_id', '3', false) \g /dev/null
UPDATE tasks SET status = 'in_progress' WHERE task_id = :t;
INSERT INTO comments (task_id, author_id, body) VALUES (:t, 3, 'Взял в работу.');
UPDATE tasks SET status = 'review' WHERE task_id = :t;

-- тестировщик
SELECT set_config('app.user_id', '4', false) \g /dev/null
INSERT INTO comments (task_id, author_id, body) VALUES (:t, 4, 'Не проходит оплата картой МИР.');
UPDATE tasks SET status = 'in_progress' WHERE task_id = :t;

SELECT set_config('app.user_id', '3', false) \g /dev/null
UPDATE tasks SET status = 'review' WHERE task_id = :t;

SELECT set_config('app.user_id', '4', false) \g /dev/null
UPDATE tasks SET status = 'done' WHERE task_id = :t;

\echo 'Карточка задачи'
SELECT task_key, status, sprint_number, assignee_name, estimate_hours, completed_at IS NOT NULL AS completed
FROM v_task_cards WHERE task_id = :t;
\echo 'История статусов'
SELECT old_status, new_status, changed_by FROM task_status_history WHERE task_id = :t ORDER BY history_id;
\echo 'Аудит задачи: число записей по операциям'
SELECT operation, count(*) FROM audit_log WHERE table_name = 'tasks' AND row_key = :'t' GROUP BY operation ORDER BY 1;
