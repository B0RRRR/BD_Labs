-- =====================================================================
-- report.sql — комплексный аналитический отчёт с CTE (часть 4)
--
-- Вопрос руководителя: «Успеют ли действующие проекты к сроку?
-- Каков прогресс, сколько просрочено, сколько часов работы осталось,
-- какой темп нужен команде и на ком из исполнителей узкое место?»
--
-- Схема вычислений:
--   params, tasks, projects, project_members         — исходные данные
--     → task_facts                                   — промежуточные показатели по задаче
--     → project_stats, team, assignee_load           — агрегация
--     → bottleneck                                   — самый загруженный исполнитель
--     → report                                       — итоговый отчёт с уровнем риска
-- =====================================================================
WITH
-- Этап 0. Параметр отчёта — дата, на которую оцениваем состояние
params AS (
    SELECT CURRENT_DATE AS report_date
),

-- Этап 1. Исходные данные → промежуточные показатели.
-- Вход: задачи действующих (planned/active) проектов.
-- Для каждой задачи вычисляются флаги и «вес» в часах; неоценённая задача
-- весит 0 часов, но помечается отдельно, чтобы не потерять её в отчёте.
task_facts AS (
    SELECT
        t.project_id,
        t.assignee_id,
        t.status = 'done'                                          AS is_done,
        COALESCE(t.estimate_hours, 0)                              AS hours,
        t.estimate_hours IS NULL                                   AS not_estimated,
        t.status <> 'done' AND t.due_date < pr.report_date         AS is_overdue,
        t.status = 'done'  AND t.completed_at::date > t.due_date   AS done_late,
        t.status <> 'done' AND t.assignee_id IS NULL               AS is_unassigned
    FROM tasks t
    JOIN projects p ON p.project_id = t.project_id
    CROSS JOIN params pr
    WHERE p.status IN ('planned', 'active')
),

-- Этап 2а. Агрегация по проекту.
-- Вход: task_facts. Выход: одна строка на проект — количество задач,
-- объём в часах (всего / выполнено / осталось), число проблемных задач.
project_stats AS (
    SELECT
        project_id,
        count(*)                                            AS tasks,
        count(*) FILTER (WHERE is_done)                     AS done_tasks,
        sum(hours)                                          AS total_hours,
        COALESCE(sum(hours) FILTER (WHERE is_done), 0)      AS done_hours,
        COALESCE(sum(hours) FILTER (WHERE NOT is_done), 0)  AS remaining_hours,
        count(*) FILTER (WHERE is_overdue)                  AS overdue,
        count(*) FILTER (WHERE done_late)                   AS done_late,
        count(*) FILTER (WHERE is_unassigned)               AS unassigned,
        count(*) FILTER (WHERE not_estimated)               AS not_estimated
    FROM task_facts
    GROUP BY project_id
),

-- Этап 2б. Размер команды: сколько в проекте исполнителей (без менеджеров).
-- Вход: project_members. Выход: одна строка на проект.
team AS (
    SELECT project_id, count(*) AS executors
    FROM project_members
    WHERE role <> 'manager'
    GROUP BY project_id
),

-- Этап 2в. Агрегация по исполнителю внутри проекта.
-- Вход: незавершённые назначенные задачи. Выход: остаток часов на человеке.
-- Нулевой остаток (только неоценённые задачи) узким местом не считаем.
assignee_load AS (
    SELECT project_id, assignee_id, sum(hours) AS remaining_hours
    FROM task_facts
    WHERE NOT is_done AND assignee_id IS NOT NULL
    GROUP BY project_id, assignee_id
    HAVING sum(hours) > 0
),

-- Этап 2г. Узкое место: в каждом проекте один исполнитель с наибольшим
-- остатком (DISTINCT ON оставляет первую строку каждой группы).
bottleneck AS (
    SELECT DISTINCT ON (project_id) project_id, assignee_id, remaining_hours
    FROM assignee_load
    ORDER BY project_id, remaining_hours DESC
),

-- Этап 3. Итоговый отчёт.
-- Вход: проекты + все агрегаты. LEFT JOIN — проект без задач и без
-- команды тоже показываем. Вычисляются прогресс в % по часам, дни до
-- дедлайна, требуемый темп (часов в неделю на одного исполнителя, чтобы
-- успеть к end_date) и уровень риска:
--   высокий — просрочено ≥ 2 задач или нужно > 20 ч/нед на человека
--             (люди совмещают проекты, больше половины недели — нереально);
--   средний — есть просроченная, неназначенная или неоценённая задача;
--   низкий  — проблем не найдено.
report AS (
    SELECT
        p.name                                                  AS project,
        p.status,
        owner.full_name                                         AS owner,
        p.end_date                                              AS deadline,
        p.end_date - pr.report_date                             AS days_left,
        COALESCE(s.tasks, 0)                                    AS tasks,
        COALESCE(s.done_tasks, 0)                               AS done,
        round(100.0 * s.done_hours / NULLIF(s.total_hours, 0)) AS progress_pct,
        COALESCE(s.remaining_hours, 0)                          AS hours_left,
        tm.executors,
        round(s.remaining_hours
              / NULLIF(tm.executors, 0)
              / NULLIF((p.end_date - pr.report_date) / 7.0, 0), 1) AS h_week_person,
        COALESCE(s.overdue, 0)                                  AS overdue,
        COALESCE(s.done_late, 0)                                AS done_late,
        COALESCE(s.unassigned, 0)                               AS unassigned,
        COALESCE(s.not_estimated, 0)                            AS not_estimated,
        bu.full_name || ' (' || b.remaining_hours || ' ч)'      AS bottleneck,
        CASE
            WHEN s.tasks IS NULL
                THEN 'нет задач'
            WHEN s.overdue >= 2
              OR s.remaining_hours / NULLIF(tm.executors, 0)
                 / NULLIF((p.end_date - pr.report_date) / 7.0, 0) > 20
                THEN 'высокий'
            WHEN s.overdue = 1 OR s.unassigned > 0 OR s.not_estimated > 0
                THEN 'средний'
            ELSE 'низкий'
        END                                                     AS risk
    FROM projects p
    CROSS JOIN params pr
    JOIN users owner          ON owner.user_id = p.owner_id
    LEFT JOIN project_stats s ON s.project_id = p.project_id
    LEFT JOIN team tm         ON tm.project_id = p.project_id
    LEFT JOIN bottleneck b    ON b.project_id = p.project_id
    LEFT JOIN users bu        ON bu.user_id = b.assignee_id
    WHERE p.status IN ('planned', 'active')
)

SELECT *
FROM report
ORDER BY CASE risk WHEN 'высокий' THEN 1 WHEN 'средний' THEN 2
                   WHEN 'низкий'  THEN 3 ELSE 4 END,
         days_left NULLS LAST;
