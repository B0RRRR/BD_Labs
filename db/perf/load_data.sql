-- Масштабируемый набор данных для исследования производительности.
-- Запускать на отдельной базе после db/init.sh (SEED_DEMO=0):
--   createdb pm_perf && PGDATABASE=pm_perf SEED_DEMO=0 db/init.sh
--   psql -d pm_perf -v n_tasks=100000 -f db/perf/load_data.sql
--
-- Объём задаётся числом задач n_tasks (по умолчанию 100 000), остальное пропорционально:
--   пользователи n/50, заказчики n/500, проекты n/100 (по 6 участников, до 8 спринтов),
--   задачи n, комментарии 2n, история статусов ≈ 3,4n, метки задач n/2.
-- Данные согласованы со всеми ограничениями (исполнитель — участник проекта,
-- спринт — того же проекта, ёмкость спринта не превышена).
\set ON_ERROR_STOP on
\if :{?n_tasks}
\else
    \set n_tasks 100000
\endif
SELECT :n_tasks / 50 AS n_users, :n_tasks / 500 AS n_customers, :n_tasks / 100 AS n_projects \gset

BEGIN;
-- начальное наполнение: аудит и история не нужны, история формируется ниже
ALTER TABLE tasks     DISABLE TRIGGER USER;
ALTER TABLE projects  DISABLE TRIGGER USER;
ALTER TABLE contracts DISABLE TRIGGER USER;

INSERT INTO users (full_name, email, created_at)
SELECT 'Сотрудник ' || i, 'load' || i || '@load.example', DATE '2025-01-01' + i % 500
FROM generate_series(1, :n_users) AS i;
CREATE TEMP TABLE lu AS
SELECT row_number() OVER (ORDER BY user_id) AS k, user_id
FROM users WHERE email LIKE 'load%@load.example';

INSERT INTO customers (name, email)
SELECT 'Нагрузочный заказчик ' || i, 'client' || i || '@load.example'
FROM generate_series(1, :n_customers) AS i;
CREATE TEMP TABLE lc AS
SELECT row_number() OVER (ORDER BY customer_id) AS k, customer_id
FROM customers WHERE name LIKE 'Нагрузочный заказчик %';

-- Проекты: 60 % действующих, 25 % завершённых, 10 % запланированных, 5 % отменённых.
-- У действующего проекта спринты 1–6 закрыты, 7-й идёт (содержит 14.11.2026), 8-й запланирован.
CREATE TEMP TABLE lp AS
SELECT i,
       CASE WHEN i % 20 = 0 THEN 'cancelled'
            WHEN i % 20 IN (1, 2) THEN 'planned'
            WHEN i % 20 BETWEEN 3 AND 7 THEN 'completed'
            ELSE 'active' END AS status,
       ((i - 1) * 6) % :n_users + 1 AS owner_k
FROM generate_series(1, :n_projects) AS i;
ALTER TABLE lp ADD COLUMN start_date date;
UPDATE lp SET start_date = CASE status
    WHEN 'active'  THEN DATE '2026-08-10' + i % 13
    WHEN 'planned' THEN DATE '2026-12-01' + i % 60
    ELSE DATE '2025-06-02' + i % 100 END;

INSERT INTO projects (name, code, owner_id, status, start_date, end_date, customer_id)
SELECT 'Нагрузочный проект ' || lp.i,
       'L' || lpad(lp.i::text, 4, '0'),
       lu.user_id,
       lp.status,
       lp.start_date,
       CASE WHEN lp.status = 'active' THEN lp.start_date + 8 * 14 + 30
            WHEN lp.status = 'planned' THEN NULL
            ELSE lp.start_date + 8 * 14 - 1 END,
       CASE WHEN lp.i % 2 = 0 THEN (SELECT customer_id FROM lc WHERE lc.k = (lp.i / 2) % :n_customers + 1) END
FROM lp JOIN lu ON lu.k = lp.owner_k;
ALTER TABLE lp ADD COLUMN project_id integer;
UPDATE lp SET project_id = p.project_id FROM projects p WHERE p.code = 'L' || lpad(lp.i::text, 4, '0');

INSERT INTO contracts (project_id, customer_id, number, signed_on, amount, budget_hours)
SELECT p.project_id, p.customer_id, 'НГ-' || lp.i, lp.start_date - 14, 3000000, 1000
FROM lp JOIN projects p ON p.project_id = lp.project_id
WHERE p.customer_id IS NOT NULL;

-- Участники: 6 подряд идущих сотрудников; 0 — руководитель (владелец), 1–3 — разработчики,
-- 4 — тестировщик, 5 — аналитик.
INSERT INTO project_members (project_id, user_id, role, joined_at)
SELECT lp.project_id, lu.user_id,
       (ARRAY['manager', 'developer', 'developer', 'developer', 'tester', 'analyst'])[m.k + 1],
       lp.start_date - 7
FROM lp
CROSS JOIN generate_series(0, 5) AS m(k)
JOIN lu ON lu.k = ((lp.i - 1) * 6 + m.k) % :n_users + 1;

INSERT INTO sprints (project_id, number, start_date, end_date, capacity_hours, status)
SELECT lp.project_id, s, lp.start_date + (s - 1) * 14, lp.start_date + (s - 1) * 14 + 13, 120,
       CASE WHEN lp.status <> 'active' OR s < 7 THEN 'closed'
            WHEN s = 7 THEN 'active' ELSE 'planned' END
FROM lp CROSS JOIN generate_series(1, 8) AS s
WHERE lp.status <> 'planned';

-- Задачи: j — номер задачи в проекте (0..n/P−1). Первые 96 задач по 12 входят в спринты
-- 1–8 (не более 106 ч при ёмкости 120 ч), остальные — бэклог.
CREATE TEMP TABLE lt AS
SELECT i, (i - 1) % :n_projects + 1 AS pi, (i - 1) / :n_projects AS j
FROM generate_series(1, :n_tasks) AS i;

INSERT INTO tasks (project_id, assignee_id, title, status, priority, created_at, due_date,
                   estimate_hours, completed_at, sprint_id)
SELECT lp.project_id,
       lu.user_id,
       'Нагрузочная задача ' || lt.i,
       st.status,
       lt.i % 5 + 1,
       COALESCE(s.start_date, lp.start_date) - 3 + (lt.j % 3) * interval '1 hour',
       s.end_date,
       (lt.j % 7 + 1) * 2,
       CASE WHEN st.status = 'done' THEN s.start_date + lt.j % 12 + interval '10 hours' END,
       s.sprint_id
FROM lt
JOIN lp ON lp.i = lt.pi
JOIN lu ON lu.k = ((lp.i - 1) * 6 + 1 + lt.j % 5) % :n_users + 1
LEFT JOIN sprints s ON s.project_id = lp.project_id AND lt.j < 96 AND s.number = lt.j / 12 + 1
CROSS JOIN LATERAL (SELECT CASE
        WHEN s.status = 'closed' THEN 'done'
        WHEN s.status = 'active' THEN (ARRAY['todo', 'in_progress', 'review', 'done'])[lt.j % 4 + 1]
        ELSE 'todo' END AS status) st;

-- История статусов: создание, взятие в работу, проверка, завершение.
INSERT INTO task_status_history (task_id, old_status, new_status, changed_at, changed_by)
SELECT t.task_id, h.old_status, h.new_status, h.at, t.assignee_id
FROM tasks t
JOIN projects p ON p.project_id = t.project_id AND p.code LIKE 'L%'
CROSS JOIN LATERAL (VALUES
    (1, NULL, 'todo', t.created_at),
    (2, 'todo', 'in_progress', t.created_at + interval '1 day'),
    (3, 'in_progress', 'review', t.created_at + interval '2 days'),
    (4, 'review', 'done', t.completed_at)
) AS h(step, old_status, new_status, at)
WHERE h.step = 1
   OR (h.step = 2 AND t.status IN ('in_progress', 'review', 'done'))
   OR (h.step = 3 AND t.status IN ('review', 'done'))
   OR (h.step = 4 AND t.status = 'done');

-- Комментарии: исполнителя и тестировщика проекта.
INSERT INTO comments (task_id, author_id, body, created_at)
SELECT t.task_id,
       CASE WHEN g = 1 THEN t.assignee_id
            ELSE (SELECT user_id FROM project_members m WHERE m.project_id = t.project_id AND m.role = 'tester') END,
       CASE WHEN g = 1 THEN 'Взял в работу.' ELSE 'Проверено.' END,
       t.created_at + g * interval '1 day'
FROM tasks t
JOIN projects p ON p.project_id = t.project_id AND p.code LIKE 'L%'
CROSS JOIN generate_series(1, 2) AS g;

INSERT INTO marks_tasks (mark_id, task_id, date)
SELECT (t.task_id / 2) % 5 + 1, t.task_id, t.created_at
FROM tasks t
JOIN projects p ON p.project_id = t.project_id AND p.code LIKE 'L%'
WHERE t.task_id % 2 = 0;

ALTER TABLE tasks     ENABLE TRIGGER USER;
ALTER TABLE projects  ENABLE TRIGGER USER;
ALTER TABLE contracts ENABLE TRIGGER USER;
COMMIT;

REFRESH MATERIALIZED VIEW mv_project_stats;
ANALYZE;
