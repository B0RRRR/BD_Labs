-- Комплексные аналитические отчёты.
-- Запуск: psql -f db/queries/reports.sql [-v today=2026-11-14]
\if :{?today}
\else
    SELECT CURRENT_DATE AS today \gset
\endif

-- =====================================================================
-- Отчёт 1. Риски срыва сроков действующих проектов (из ЛР № 2)
--
-- Вопрос руководителя: «Успеют ли действующие проекты к сроку? Каков прогресс,
-- сколько просрочено, сколько часов осталось, какой темп нужен команде и на ком
-- из исполнителей узкое место?»
--   params, tasks, projects, project_members  — исходные данные
--     → task_facts                            — показатели по задаче
--     → project_stats, team, assignee_load    — агрегация
--     → bottleneck                            — самый загруженный исполнитель
--     → report                                — итог с уровнем риска
-- =====================================================================
WITH
-- Этап 0. Параметр отчёта — дата, на которую оцениваем состояние
params AS (
    SELECT :'today'::date AS report_date
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


-- =====================================================================
-- Отчёт 2. Исполнение договоров: план/факт по бюджету, скорость и прогноз завершения
--
-- Вопрос руководства: «Уложатся ли внешние проекты в бюджет часов по договору с учётом
-- фактических трудозатрат и успеют ли к сроку при текущей скорости команды?»
--   worklogs           → fact       — фактически списанные часы по каждой задаче
--   tasks, fact        → spent      — факт и оценка выполненных задач, остаток оценок;
--                                     коэффициент точности оценок k = факт / оценка
--   tasks, spent       → remaining  — прогноз по незавершённым задачам: k × оценка,
--                                     но не меньше уже списанного
--   sprints, tasks     → sprint_v   — скорость каждого закрытого спринта,
--                                     номер спринта с конца (ROW_NUMBER)
--   sprint_v           → velocity   — средняя скорость трёх последних спринтов
--   contracts, ...     → forecast   — прогноз трудоёмкости, сколько спринтов осталось, дата завершения
--   forecast           → итог       — факт и прогноз против бюджета, стоимость часа, вердикт
-- Спринт длится две недели, поэтому прогноз = дата отчёта + оставшиеся спринты × 14 дней.
-- =====================================================================
WITH params AS (
    SELECT :'today'::date AS report_date
), fact AS (
    SELECT task_id, sum(hours) AS hours
    FROM worklogs
    GROUP BY task_id
), spent AS (
    SELECT t.project_id,
           COALESCE(sum(f.hours), 0)                                              AS fact_hours,
           COALESCE(sum(f.hours) FILTER (WHERE t.status = 'done'), 0)             AS fact_done,
           COALESCE(sum(t.estimate_hours) FILTER (WHERE t.status = 'done'), 0)   AS done_hours,
           COALESCE(sum(t.estimate_hours) FILTER (WHERE t.status <> 'done'), 0)  AS left_hours,
           count(*) FILTER (WHERE t.status <> 'done' AND t.estimate_hours IS NULL) AS not_estimated
    FROM tasks t
    LEFT JOIN fact f ON f.task_id = t.task_id
    GROUP BY t.project_id
), remaining AS (
    SELECT t.project_id,
           sum(GREATEST(COALESCE(f.hours, 0),
                        COALESCE(sp.fact_done / NULLIF(sp.done_hours, 0), 1) * COALESCE(t.estimate_hours, 0))) AS hours
    FROM tasks t
    JOIN spent sp     ON sp.project_id = t.project_id
    LEFT JOIN fact f  ON f.task_id = t.task_id
    WHERE t.status <> 'done'
    GROUP BY t.project_id
), sprint_v AS (
    SELECT s.project_id,
           COALESCE(sum(t.estimate_hours) FILTER (WHERE t.status = 'done'), 0) AS done_hours,
           ROW_NUMBER() OVER (PARTITION BY s.project_id ORDER BY s.end_date DESC) AS from_end
    FROM sprints s
    LEFT JOIN tasks t ON t.sprint_id = s.sprint_id
    WHERE s.status = 'closed'
    GROUP BY s.sprint_id
), velocity AS (
    SELECT project_id, avg(done_hours) AS hours_per_sprint
    FROM sprint_v
    WHERE from_end <= 3
    GROUP BY project_id
), forecast AS (
    SELECT c.project_id,
           cu.name                                         AS customer,
           p.code,
           p.status,
           p.end_date,
           c.number,
           c.amount,
           c.budget_hours,
           COALESCE(sp.fact_hours, 0)                      AS fact_hours,
           sp.fact_done / NULLIF(sp.done_hours, 0)         AS accuracy,
           COALESCE(sp.fact_done, 0) + COALESCE(rm.hours, 0) AS forecast_hours,
           COALESCE(sp.done_hours, 0)                      AS done_hours,
           COALESCE(sp.left_hours, 0)                      AS left_hours,
           COALESCE(sp.not_estimated, 0)                   AS not_estimated,
           v.hours_per_sprint,
           CASE WHEN p.status IN ('planned', 'active')
                THEN ceil(sp.left_hours / NULLIF(v.hours_per_sprint, 0)) END AS sprints_left,
           CASE WHEN p.status IN ('planned', 'active')
                THEN pr.report_date
                     + (14 * ceil(sp.left_hours / NULLIF(v.hours_per_sprint, 0)))::integer END AS forecast_end
    FROM contracts c
    JOIN projects p       ON p.project_id = c.project_id
    JOIN customers cu     ON cu.customer_id = c.customer_id
    CROSS JOIN params pr
    LEFT JOIN spent sp    ON sp.project_id = c.project_id
    LEFT JOIN remaining rm ON rm.project_id = c.project_id
    LEFT JOIN velocity v  ON v.project_id = c.project_id
)
SELECT customer,
       code,
       number,
       status,
       budget_hours,
       fact_hours,
       round(accuracy, 2)                                           AS accuracy,
       round(forecast_hours, 1)                                     AS forecast_hours,
       round(100 * forecast_hours / budget_hours, 1)                AS budget_pct,
       round(amount / budget_hours)                                 AS rub_per_hour,
       done_hours,
       left_hours,
       not_estimated,
       round(hours_per_sprint, 1)                                   AS velocity,
       sprints_left,
       forecast_end,
       end_date,
       CASE
           WHEN status IN ('completed', 'cancelled') AND fact_hours > budget_hours
                                                        THEN 'закрыт с перерасходом'
           WHEN status IN ('completed', 'cancelled')    THEN 'закрыт'
           WHEN forecast_hours > budget_hours           THEN 'перерасход бюджета'
           WHEN hours_per_sprint IS NULL                THEN 'нет данных о скорости'
           WHEN forecast_end > end_date                 THEN 'риск срыва срока'
           ELSE 'в норме'
       END                                                          AS verdict
FROM forecast
ORDER BY CASE WHEN status IN ('completed', 'cancelled') THEN 1 ELSE 0 END, forecast_end NULLS LAST;
