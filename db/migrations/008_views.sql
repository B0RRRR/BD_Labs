-- 008. Представления для приложения и материализованная сводка по проектам.

-- Карточка задачи: ключ, проект, исполнитель, спринт, метки, признак просрочки.
-- Через неё приложение выдаёт списки задач с фильтрацией, сортировкой и пагинацией.
CREATE VIEW v_task_cards AS
SELECT t.task_id,
       p.code || '-' || t.task_id               AS task_key,
       t.project_id,
       p.code                                   AS project_code,
       t.title,
       t.status,
       t.priority,
       t.estimate_hours,
       t.due_date,
       t.status <> 'done' AND t.due_date < CURRENT_DATE AS overdue,
       t.assignee_id,
       u.full_name                              AS assignee_name,
       t.sprint_id,
       s.number                                 AS sprint_number,
       t.created_at,
       t.completed_at,
       COALESCE((SELECT array_agg(m.name ORDER BY m.name)
                 FROM marks_tasks mt JOIN marks m USING (mark_id)
                 WHERE mt.task_id = t.task_id), '{}') AS marks
FROM tasks t
JOIN projects p      ON p.project_id = t.project_id
LEFT JOIN users u    ON u.user_id = t.assignee_id
LEFT JOIN sprints s  ON s.sprint_id = t.sprint_id;

-- Загрузка спринтов: запланировано и выполнено часов относительно ёмкости.
CREATE VIEW v_sprint_load AS
SELECT s.sprint_id,
       s.project_id,
       p.code                                                    AS project_code,
       s.number,
       s.status,
       s.start_date,
       s.end_date,
       s.capacity_hours,
       COALESCE(sum(t.estimate_hours), 0)                        AS planned_hours,
       COALESCE(sum(t.estimate_hours) FILTER (WHERE t.status = 'done'), 0) AS done_hours,
       count(t.task_id)                                          AS tasks,
       count(t.task_id) FILTER (WHERE t.status = 'done')         AS tasks_done,
       round(100 * COALESCE(sum(t.estimate_hours), 0) / s.capacity_hours, 1) AS load_pct
FROM sprints s
JOIN projects p    ON p.project_id = s.project_id
LEFT JOIN tasks t  ON t.sprint_id = s.sprint_id
GROUP BY s.sprint_id, p.project_id;

-- Сводка по проектам для руководства. Расчёт читает задачи, историю и договоры
-- целиком, поэтому результат материализуется и обновляется по запросу
-- (refresh_project_stats) или приложением по расписанию.
CREATE MATERIALIZED VIEW mv_project_stats AS
WITH t AS (
    SELECT project_id,
           count(*)                                              AS tasks_total,
           count(*) FILTER (WHERE status = 'done')               AS tasks_done,
           count(*) FILTER (WHERE status <> 'done' AND due_date < CURRENT_DATE) AS tasks_overdue,
           COALESCE(sum(estimate_hours), 0)                      AS hours_planned,
           COALESCE(sum(estimate_hours) FILTER (WHERE status = 'done'), 0) AS hours_done
    FROM tasks
    GROUP BY project_id
), cycle AS (                       -- время цикла: от первого взятия в работу до завершения
    SELECT t.project_id,
           round(avg(EXTRACT(epoch FROM t.completed_at - h.started) / 86400)::numeric, 1) AS avg_cycle_days
    FROM tasks t
    JOIN (SELECT task_id, min(changed_at) AS started
          FROM task_status_history
          WHERE new_status = 'in_progress'
          GROUP BY task_id) h ON h.task_id = t.task_id
    WHERE t.status = 'done'
    GROUP BY t.project_id
)
SELECT p.project_id,
       p.code,
       p.name,
       p.status,
       COALESCE(t.tasks_total, 0)    AS tasks_total,
       COALESCE(t.tasks_done, 0)     AS tasks_done,
       COALESCE(t.tasks_overdue, 0)  AS tasks_overdue,
       COALESCE(t.hours_planned, 0)  AS hours_planned,
       COALESCE(t.hours_done, 0)     AS hours_done,
       c.budget_hours,
       round(100 * t.hours_planned / c.budget_hours, 1) AS budget_planned_pct,
       cy.avg_cycle_days,
       now()::timestamp(0)           AS refreshed_at
FROM projects p
LEFT JOIN t         ON t.project_id = p.project_id
LEFT JOIN contracts c  ON c.project_id = p.project_id
LEFT JOIN cycle cy  ON cy.project_id = p.project_id;

CREATE UNIQUE INDEX uq_mv_project_stats ON mv_project_stats (project_id);   -- нужен для CONCURRENTLY

-- Обновление без блокировки читателей. SECURITY DEFINER: обновлять представление
-- может только его владелец, роли приложения дано право вызвать эту функцию.
CREATE FUNCTION refresh_project_stats() RETURNS timestamp
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_stats;
    RETURN (SELECT max(refreshed_at) FROM mv_project_stats);
END $$;
