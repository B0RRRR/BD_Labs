-- Операционные и аналитические запросы системы управления проектами.
-- Запуск: psql -f db/queries/queries.sql [-v today=2026-11-14] [-v project=MBANK]
-- today — дата, на которую строятся показатели (по умолчанию текущая),
-- project — код проекта для запросов 1 и 7 (по умолчанию TRACK).
\if :{?today}
\else
    SELECT CURRENT_DATE AS today \gset
\endif
\if :{?project}
\else
    \set project TRACK
\endif

-- =====================================================================
-- 1. Доска текущего спринта проекта (многотабличное соединение, внешние соединения)
-- Вопрос руководителя на ежедневной встрече: что в спринте, у кого, в каком
-- состоянии, сколько обсуждают. Задача без исполнителя и без комментариев
-- тоже показывается — поэтому LEFT JOIN.
-- =====================================================================
SELECT p.code || '-' || t.task_id                   AS task_key,
       t.title,
       t.status,
       t.priority,
       t.estimate_hours,
       COALESCE(u.full_name, '— не назначена —')    AS assignee,
       m.role                                       AS assignee_role,
       count(c.comment_id)                          AS comments,
       max(c.created_at)::date                      AS last_comment
FROM sprints s
JOIN projects p              ON p.project_id = s.project_id
JOIN tasks t                 ON t.sprint_id = s.sprint_id
LEFT JOIN users u            ON u.user_id = t.assignee_id
LEFT JOIN project_members m  ON m.project_id = t.project_id AND m.user_id = t.assignee_id
LEFT JOIN comments c         ON c.task_id = t.task_id
WHERE p.code = :'project' AND s.status = 'active'
GROUP BY p.code, t.task_id, u.full_name, m.role
ORDER BY array_position(ARRAY['todo', 'in_progress', 'review', 'done'], t.status::text), t.priority;

-- =====================================================================
-- 2. Задачи для эскалации руководителю (условия по нескольким таблицам)
-- Незавершённые задачи высокого приоритета (1–2) действующих проектов, срок которых
-- прошёл или наступит в ближайшие 7 дней. Руководитель берётся из участников проекта.
-- =====================================================================
SELECT p.code || '-' || t.task_id                AS task_key,
       t.title,
       t.priority,
       t.status,
       t.due_date,
       t.due_date - :'today'::date               AS days_left,
       mgr.full_name                             AS manager,
       COALESCE(a.full_name, '— не назначена —') AS assignee
FROM tasks t
JOIN projects p         ON p.project_id = t.project_id
JOIN project_members pm ON pm.project_id = p.project_id AND pm.role = 'manager'
JOIN users mgr          ON mgr.user_id = pm.user_id
LEFT JOIN users a       ON a.user_id = t.assignee_id
WHERE p.status = 'active'
  AND t.status <> 'done'
  AND t.priority <= 2
  AND t.due_date <= :'today'::date + 7
ORDER BY days_left, t.priority;

-- =====================================================================
-- 3. Перегруженные сотрудники (агрегаты, GROUP BY, HAVING)
-- Часы незавершённых задач в действующих проектах; показываются те, у кого
-- больше 40 ч. Неоценённые задачи SUM не учитывает — их число выводится отдельно.
-- =====================================================================
SELECT u.full_name                         AS employee,
       count(*)                            AS open_tasks,
       count(DISTINCT t.project_id)        AS projects,
       sum(t.estimate_hours)               AS open_hours,
       count(*) - count(t.estimate_hours)  AS not_estimated,
       min(t.due_date)                     AS nearest_due
FROM tasks t
JOIN users u    ON u.user_id = t.assignee_id
JOIN projects p ON p.project_id = t.project_id
WHERE t.status <> 'done'
  AND p.status IN ('planned', 'active')
GROUP BY u.user_id
HAVING sum(t.estimate_hours) > 40
ORDER BY open_hours DESC;

-- =====================================================================
-- 4. Сотрудники с просроченными задачами (EXISTS)
-- Нужен только факт наличия хотя бы одной просроченной задачи, а не их число.
-- =====================================================================
SELECT u.full_name, u.email
FROM users u
WHERE EXISTS (
    SELECT 1
    FROM tasks t
    JOIN projects p ON p.project_id = t.project_id
    WHERE t.assignee_id = u.user_id
      AND p.status = 'active'
      AND t.status <> 'done'
      AND t.due_date < :'today'::date
)
ORDER BY u.full_name;

-- =====================================================================
-- 5. Действующие проекты без тестировщика (NOT EXISTS)
-- Задачи таких проектов некому проверять на этапе review.
-- =====================================================================
SELECT p.code,
       p.name,
       p.status,
       (SELECT count(*) FROM tasks t WHERE t.project_id = p.project_id AND t.status = 'review') AS waiting_review
FROM projects p
WHERE p.status IN ('planned', 'active')
  AND NOT EXISTS (SELECT 1 FROM project_members pm
                  WHERE pm.project_id = p.project_id AND pm.role = 'tester')
ORDER BY p.start_date;

-- =====================================================================
-- 6. Участники без задач в своём проекте (внешнее соединение + IS NULL)
-- Незадействованные исполнители действующих проектов (руководители не исполняют задачи).
-- =====================================================================
SELECT p.code, u.full_name AS member, pm.role, pm.joined_at
FROM project_members pm
JOIN projects p   ON p.project_id = pm.project_id
JOIN users u      ON u.user_id = pm.user_id
LEFT JOIN tasks t ON t.project_id = pm.project_id AND t.assignee_id = pm.user_id
WHERE p.status IN ('planned', 'active')
  AND pm.role <> 'manager'
  AND t.task_id IS NULL
ORDER BY p.code, pm.role, u.full_name;

-- =====================================================================
-- 7. Скорость команды по спринтам (оконные функции LAG, AVG OVER, RANK)
-- Скорость — часы задач, выполненных в закрытом спринте. Изменение к прошлому
-- спринту (LAG), скользящее среднее за три спринта — база для планирования
-- следующего спринта, место спринта по скорости в проекте (RANK).
-- =====================================================================
WITH v AS (
    SELECT s.project_id, s.number, s.end_date, s.capacity_hours,
           COALESCE(sum(t.estimate_hours) FILTER (WHERE t.status = 'done'), 0) AS done_hours
    FROM sprints s
    JOIN projects p   ON p.project_id = s.project_id
    LEFT JOIN tasks t ON t.sprint_id = s.sprint_id
    WHERE s.status = 'closed' AND p.code = :'project'
    GROUP BY s.sprint_id
)
SELECT number,
       end_date,
       capacity_hours,
       done_hours,
       round(100 * done_hours / capacity_hours)                                AS focus_pct,
       done_hours - LAG(done_hours) OVER w                                     AS delta,
       round(avg(done_hours) OVER (w ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS avg_3,
       RANK() OVER (PARTITION BY project_id ORDER BY done_hours DESC)          AS rank_in_project
FROM v
WINDOW w AS (PARTITION BY project_id ORDER BY number)
ORDER BY number;

-- =====================================================================
-- 8. Время цикла и возвраты на доработку по истории статусов (многоэтапный CTE)
-- Этап 1 — начало работы над задачей (первый переход в in_progress);
-- этап 2 — число возвратов review → in_progress;
-- этап 3 — время цикла завершённых задач;
-- этап 4 — медиана, 85-й процентиль и доля задач с возвратами по проекту.
-- 85-й процентиль — срок, который можно обещать заказчику для типовой задачи.
-- =====================================================================
WITH starts AS (
    SELECT task_id, min(changed_at) AS started
    FROM task_status_history
    WHERE new_status = 'in_progress'
    GROUP BY task_id
), returns AS (
    SELECT task_id, count(*) AS returns
    FROM task_status_history
    WHERE old_status = 'review' AND new_status = 'in_progress'
    GROUP BY task_id
), cycle AS (
    SELECT t.project_id,
           EXTRACT(epoch FROM t.completed_at - s.started) / 86400 AS days,
           COALESCE(r.returns, 0)                               AS returns
    FROM tasks t
    JOIN starts s        ON s.task_id = t.task_id
    LEFT JOIN returns r  ON r.task_id = t.task_id
    WHERE t.status = 'done'
)
SELECT p.code,
       count(*)                                                                    AS done_tasks,
       round(percentile_cont(0.5)  WITHIN GROUP (ORDER BY c.days)::numeric, 1)     AS median_days,
       round(percentile_cont(0.85) WITHIN GROUP (ORDER BY c.days)::numeric, 1)     AS p85_days,
       round(100.0 * count(*) FILTER (WHERE c.returns > 0) / count(*), 1)          AS returned_pct
FROM cycle c
JOIN projects p ON p.project_id = c.project_id
GROUP BY p.code
HAVING count(*) >= 10                              -- по малой выборке процентиль не показателен
ORDER BY p85_days DESC;

-- =====================================================================
-- 9. Вклад исполнителей за последние 30 дней (RANK и доля через SUM OVER)
-- Часы выполненных задач каждого исполнителя, его место и доля в проекте.
-- =====================================================================
WITH done AS (
    SELECT project_id, assignee_id, count(*) AS tasks, sum(estimate_hours) AS hours
    FROM tasks
    WHERE status = 'done'
      AND completed_at >= :'today'::date - 30
      AND completed_at <  :'today'::date + 1
    GROUP BY project_id, assignee_id
)
SELECT p.code,
       u.full_name                                                           AS assignee,
       d.tasks,
       d.hours,
       RANK() OVER (PARTITION BY d.project_id ORDER BY d.hours DESC)        AS rank,
       round(100 * d.hours / sum(d.hours) OVER (PARTITION BY d.project_id), 1) AS share_pct
FROM done d
JOIN projects p ON p.project_id = d.project_id
JOIN users u    ON u.user_id = d.assignee_id
ORDER BY p.code, rank;

-- =====================================================================
-- 10. Нагрузка и активность участника в проекте (коррелированные подзапросы)
-- Для каждого участника действующего проекта подзапросы берут проект и
-- сотрудника из текущей строки внешнего запроса и считают его незавершённые
-- задачи, их часы и время последнего комментария в этом проекте.
-- =====================================================================
SELECT p.code,
       u.full_name                                          AS member,
       pm.role,
       (SELECT count(*) FROM tasks t
         WHERE t.project_id = pm.project_id AND t.assignee_id = pm.user_id
           AND t.status <> 'done')                          AS open_tasks,
       (SELECT COALESCE(sum(t.estimate_hours), 0) FROM tasks t
         WHERE t.project_id = pm.project_id AND t.assignee_id = pm.user_id
           AND t.status <> 'done')                          AS open_hours,
       (SELECT max(c.created_at)::date FROM comments c JOIN tasks t ON t.task_id = c.task_id
         WHERE t.project_id = pm.project_id AND c.author_id = pm.user_id) AS last_comment
FROM project_members pm
JOIN projects p ON p.project_id = pm.project_id
JOIN users u    ON u.user_id = pm.user_id
WHERE p.status = 'active'
ORDER BY p.code, open_hours DESC;
