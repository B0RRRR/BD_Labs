-- =====================================================================
-- load_data.sql — генерация нагрузочных данных для оценки
-- производительности SQL-модулей (раздел «Оценка качества» записки).
--
-- Запуск (на копии базы после всех скриптов ЛР1 и ЛР2, НЕ на рабочей):
--   createdb -T project_db project_db_load
--   psql -d project_db_load -v n_tasks=100000 -f load_data.sql
--
-- Объём задаётся числом задач n_tasks, остальное — пропорционально:
--   пользователей  n_tasks / 50
--   проектов       n_tasks / 100  (≈ 100 задач на проект)
--   участников     3–8 на проект
--   комментариев   3 на задачу
--   меток          у каждой третьей задачи, у каждой десятой — вторая
--
-- Данные удовлетворяют всем ограничениям схемы. setseed — чтобы при
-- повторном запуске получался тот же набор.
-- =====================================================================
\set ON_ERROR_STOP on

SELECT :n_tasks / 50  AS n_users,
       :n_tasks / 100 AS n_projects,
       :n_tasks * 3   AS n_comments
\gset

BEGIN;
SELECT setseed(0.42);

-- 1. Пользователи --------------------------------------------------------
INSERT INTO users (full_name, email, created_at)
SELECT 'Нагрузочный пользователь ' || i,
       'load' || i || '@load.test',
       timestamp '2025-01-01' + random() * interval '365 days'
FROM generate_series(1, :n_users) AS i;

CREATE TEMP TABLE lu AS
SELECT row_number() OVER (ORDER BY user_id) AS i, user_id
FROM users
WHERE email LIKE '%@load.test';
CREATE INDEX ON lu (i);
ANALYZE lu;

-- 2. Проекты: 50 % active, 20 % planned, 20 % completed, 10 % cancelled --
INSERT INTO projects (name, owner_id, status, start_date, end_date, code)
SELECT 'Нагрузочный проект ' || g.i,
       lu.user_id,
       CASE WHEN g.i % 10 < 5 THEN 'active'
            WHEN g.i % 10 < 7 THEN 'planned'
            WHEN g.i % 10 < 9 THEN 'completed'
            ELSE 'cancelled' END,
       g.start_date,
       CASE WHEN random() < 0.2 THEN NULL
            ELSE g.start_date + 30 + (random() * 300)::int END,
       'L' || g.i
FROM (SELECT i, date '2025-06-01' + (random() * 500)::int AS start_date
      FROM generate_series(1, :n_projects) AS i) AS g
JOIN lu ON lu.i = 1 + (g.i * 7) % :n_users;

CREATE TEMP TABLE lp AS
SELECT row_number() OVER (ORDER BY project_id) AS i,
       project_id, status, start_date,
       3 + (row_number() OVER (ORDER BY project_id)) % 6 AS team_size  -- 3..8
FROM projects
WHERE name LIKE 'Нагрузочный проект %';
CREATE INDEX ON lp (i);
CREATE INDEX ON lp (project_id);
ANALYZE lp;

-- 3. Участники: первый — менеджер; тестировщик есть только в командах
--    от 6 человек (для запроса «проекты без тестировщика») ---------------
INSERT INTO project_members (project_id, user_id, role, joined_at)
SELECT lp.project_id,
       lu.user_id,
       CASE WHEN k = 0 THEN 'manager'
            WHEN k <= 4 THEN 'developer'
            WHEN k <= 6 THEN 'tester'
            ELSE 'analyst' END,
       lp.start_date
FROM lp
CROSS JOIN LATERAL generate_series(0, lp.team_size - 1) AS k
JOIN lu ON lu.i = 1 + (lp.i * 8 + k) % :n_users;

CREATE TEMP TABLE lm AS
SELECT lp.i AS pi, row_number() OVER (PARTITION BY pm.project_id ORDER BY pm.user_id) - 1 AS k,
       pm.user_id
FROM project_members pm
JOIN lp ON lp.project_id = pm.project_id;
CREATE INDEX ON lm (pi, k);
ANALYZE lm;

-- 4. Задачи ------------------------------------------------------------
INSERT INTO tasks (project_id, assignee_id, title, status, priority,
                   created_at, due_date, estimate_hours, completed_at)
SELECT t.project_id,
       CASE WHEN t.r_assignee < 0.1 THEN NULL ELSE lm.user_id END,
       'Нагрузочная задача ' || t.i,
       t.status,
       t.priority,
       t.created_at,
       CASE WHEN t.r_due < 0.1 THEN NULL
            ELSE t.created_at::date + 7 + (t.r_due * 53)::int END,
       CASE WHEN t.r_est < 0.1 THEN NULL ELSE round((t.r_est * 40)::numeric, 1) END,
       CASE WHEN t.status = 'done'
            THEN t.created_at + interval '2 hours' + t.r_done * interval '60 days' END
FROM (
    SELECT g.i, lp.i AS pi, lp.project_id, lp.team_size,
           CASE WHEN lp.status = 'completed' THEN 'done'
                WHEN r.s < 0.30 THEN 'todo'
                WHEN r.s < 0.55 THEN 'in_progress'
                WHEN r.s < 0.65 THEN 'review'
                ELSE 'done' END AS status,
           1 + floor(random() * 5)::int AS priority,
           lp.start_date + random() * interval '120 days' AS created_at,
           random() AS r_assignee, random() AS r_due,
           random() AS r_est,      random() AS r_done
    FROM generate_series(1, :n_tasks) AS g(i)
    JOIN lp ON lp.i = 1 + g.i % :n_projects
    CROSS JOIN LATERAL (SELECT random() + g.i * 0 AS s) AS r
) AS t
JOIN lm ON lm.pi = t.pi AND lm.k = t.i % t.team_size;

CREATE TEMP TABLE lt AS
SELECT row_number() OVER (ORDER BY task_id) AS i, task_id, project_id, created_at
FROM tasks
WHERE title LIKE 'Нагрузочная задача %';
CREATE INDEX ON lt (i);
ANALYZE lt;

-- 5. Комментарии: автор — участник проекта задачи ------------------------
INSERT INTO comments (task_id, author_id, body, created_at)
SELECT lt.task_id,
       lm.user_id,
       'Нагрузочный комментарий ' || c.i,
       lt.created_at + random() * interval '30 days'
FROM generate_series(1, :n_comments) AS c(i)
JOIN lt ON lt.i = 1 + (c.i::bigint * 7919) % :n_tasks
JOIN lp ON lp.project_id = lt.project_id
JOIN lm ON lm.pi = lp.i AND lm.k = c.i % lp.team_size;

-- 6. Метки -----------------------------------------------------------
CREATE TEMP TABLE lmk AS
SELECT row_number() OVER (ORDER BY mark_id) - 1 AS k, mark_id FROM marks;
ANALYZE lmk;

INSERT INTO marks_tasks (mark_id, task_id)
SELECT lmk.mark_id, lt.task_id
FROM lt JOIN lmk ON lmk.k = lt.i % 5
WHERE lt.i % 3 = 0
UNION ALL
SELECT lmk.mark_id, lt.task_id
FROM lt JOIN lmk ON lmk.k = (lt.i + 1) % 5
WHERE lt.i % 3 = 0 AND lt.i % 10 = 0;

COMMIT;

ANALYZE;

SELECT 'users' AS tbl, count(*) FROM users
UNION ALL SELECT 'projects', count(*) FROM projects
UNION ALL SELECT 'project_members', count(*) FROM project_members
UNION ALL SELECT 'tasks', count(*) FROM tasks
UNION ALL SELECT 'comments', count(*) FROM comments
UNION ALL SELECT 'marks_tasks', count(*) FROM marks_tasks;
