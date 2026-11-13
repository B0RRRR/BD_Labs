
SELECT
    p.name AS project,
    owner.full_name AS project_owner,
    t.title AS task,
    t.status,
    t.priority,
    COALESCE(a.full_name, '— не назначена —') AS assignee,
    pm.role AS assignee_role,
    t.due_date,
    CASE
        WHEN t.due_date IS NULL THEN 'нет срока'
        WHEN t.due_date < CURRENT_DATE THEN 'просрочена'
        ELSE 'в срок'
    END AS deadline_state,
    count(c.comment_id) AS comments
FROM tasks t
JOIN projects p ON p.project_id = t.project_id
JOIN users owner ON owner.user_id = p.owner_id
LEFT JOIN users a ON a.user_id = t.assignee_id
LEFT JOIN project_members pm
       ON pm.project_id = t.project_id AND pm.user_id = t.assignee_id
LEFT JOIN comments c ON c.task_id = t.task_id
WHERE p.status = 'active'
  AND t.status <> 'done'
GROUP BY p.name, owner.full_name, t.task_id, t.title, t.status, t.priority,
         a.full_name, pm.role, t.due_date
ORDER BY p.name, t.priority, t.due_date NULLS LAST;


-- =====================================================================
-- 2.1.2. Объекты без связанных записей
-- Вопрос: «Кто из исполнителей действующих проектов не получил в своём
-- проекте ни одной задачи?» — незадействованные ресурсы.
-- Менеджеры задач не исполняют, поэтому их не рассматриваем.
-- LEFT JOIN tasks + IS NULL: строки участника, для которых пара
-- (проект, исполнитель) в tasks не нашлась.
-- =====================================================================
SELECT
    p.name      AS project,
    p.status    AS project_status,
    u.full_name AS member,
    pm.role,
    pm.joined_at
FROM project_members pm
JOIN projects p   ON p.project_id = pm.project_id
JOIN users u      ON u.user_id = pm.user_id
LEFT JOIN tasks t ON t.project_id = pm.project_id
                 AND t.assignee_id = pm.user_id
WHERE p.status IN ('planned', 'active')
  AND pm.role <> 'manager'
  AND t.task_id IS NULL
ORDER BY p.name, pm.role, u.full_name;


-- =====================================================================
-- 2.1.3. Объекты, удовлетворяющие нескольким взаимосвязанным условиям
-- Вопрос: «Какие задачи нужно эскалировать менеджеру?»
-- Условия связаны через разные таблицы:
--   * проект активен (projects);
--   * задача не завершена и имеет приоритет 1–2 (tasks);
--   * срок уже прошёл или наступит в ближайшие 7 дней (tasks);
--   * у проекта есть менеджер — ему и эскалируем (project_members + users).
-- Исполнитель необязателен: задача без исполнителя — тоже повод эскалации.
-- =====================================================================
SELECT
    p.name                       AS project,
    mgr.full_name                AS manager,
    t.title                      AS task,
    t.priority,
    t.status,
    t.due_date,
    t.due_date - CURRENT_DATE    AS days_left,
    COALESCE(a.full_name, '— не назначена —') AS assignee
FROM tasks t
JOIN projects p         ON p.project_id = t.project_id
JOIN project_members pm ON pm.project_id = p.project_id AND pm.role = 'manager'
JOIN users mgr          ON mgr.user_id = pm.user_id
LEFT JOIN users a       ON a.user_id = t.assignee_id
WHERE p.status = 'active'
  AND t.status <> 'done'
  AND t.priority <= 2
  AND t.due_date <= CURRENT_DATE + 7
ORDER BY days_left, t.priority;


-- =====================================================================
-- 2.2.1. Количественные показатели по группам
-- Вопрос: «Сколько задач в каждом проекте и на какой они стадии?»
-- LEFT JOIN — проекты без задач тоже попадают в отчёт (с нулями).
-- COUNT(t.task_id), а не COUNT(*): иначе у проекта без задач было бы 1.
-- =====================================================================
SELECT
    p.name                                                   AS project,
    p.status                                                 AS project_status,
    count(t.task_id)                                         AS total,
    count(t.task_id) FILTER (WHERE t.status = 'todo')        AS todo,
    count(t.task_id) FILTER (WHERE t.status = 'in_progress') AS in_progress,
    count(t.task_id) FILTER (WHERE t.status = 'review')      AS review,
    count(t.task_id) FILTER (WHERE t.status = 'done')        AS done,
    count(t.task_id) FILTER (WHERE t.assignee_id IS NULL)    AS unassigned
FROM projects p
LEFT JOIN tasks t ON t.project_id = p.project_id
GROUP BY p.project_id, p.name, p.status
ORDER BY total DESC, p.name;


-- =====================================================================
-- 2.2.2. Суммарные/средние показатели с фильтрацией групп (HAVING)
-- Вопрос: «Кто из сотрудников перегружен — сколько часов незавершённой
-- работы на нём висит?» Показываем тех, у кого больше 30 часов.
-- SUM/AVG игнорируют NULL, поэтому отдельно считаем неоценённые задачи:
-- реальная нагрузка у таких сотрудников ещё больше.
-- =====================================================================
SELECT
    u.full_name                               AS employee,
    count(*)                                  AS open_tasks,
    count(DISTINCT t.project_id)              AS projects,
    sum(t.estimate_hours)                     AS open_hours,
    round(avg(t.estimate_hours), 1)           AS avg_task_hours,
    count(*) - count(t.estimate_hours)        AS not_estimated,
    min(t.due_date)                           AS nearest_due
FROM tasks t
JOIN users u    ON u.user_id = t.assignee_id
JOIN projects p ON p.project_id = t.project_id
WHERE t.status <> 'done'
  AND p.status IN ('planned', 'active')        -- задачи отменённых проектов — не нагрузка
GROUP BY u.user_id, u.full_name
HAVING sum(t.estimate_hours) > 30
ORDER BY open_hours DESC;


-- =====================================================================
-- 2.2.3. Сравнение показателей между временными периодами
-- Вопрос: «Как меняется поток задач по месяцам: сколько создали, сколько
-- из них уже закрыли, какой объём заложили и как быстро закрывали?»
-- Срок выполнения = completed_at - created_at в днях (только для done).
-- =====================================================================
SELECT
    to_char(date_trunc('month', t.created_at), 'YYYY-MM')            AS month,
    count(*)                                                         AS created,
    count(*) FILTER (WHERE t.status = 'done')                        AS done,
    round(100.0 * count(*) FILTER (WHERE t.status = 'done') / count(*)) AS done_pct,
    sum(t.estimate_hours)                                            AS planned_hours,
    round(avg(EXTRACT(EPOCH FROM t.completed_at - t.created_at) / 86400), 1) AS avg_days,
    round(min(EXTRACT(EPOCH FROM t.completed_at - t.created_at) / 86400), 1) AS min_days,
    round(max(EXTRACT(EPOCH FROM t.completed_at - t.created_at) / 86400), 1) AS max_days,
    count(*) FILTER (WHERE t.completed_at::date > t.due_date)        AS done_late
FROM tasks t
GROUP BY date_trunc('month', t.created_at)
ORDER BY month;


-- =====================================================================
-- 3.1. Сравнение с вычисляемым показателем группы
-- Вопрос: «Какие завершённые задачи выполнялись дольше, чем в среднем
-- задачи того же проекта?» — узкие места процесса.
-- Группа сравнения — проект: темп работы у проектов разный, сравнивать
-- задачу магазина со средним по всей компании некорректно.
-- Подзапрос в FROM считает среднее по каждому проекту один раз.
-- =====================================================================
SELECT
    p.name                                                      AS project,
    t.title                                                     AS task,
    t.estimate_hours,
    round(EXTRACT(EPOCH FROM t.completed_at - t.created_at) / 86400, 1) AS lead_days,
    round(pa.avg_lead_days, 1)                                  AS project_avg_days
FROM tasks t
JOIN projects p ON p.project_id = t.project_id
JOIN (
    SELECT project_id,
           avg(EXTRACT(EPOCH FROM completed_at - created_at) / 86400) AS avg_lead_days
    FROM tasks
    WHERE status = 'done'
    GROUP BY project_id
) pa ON pa.project_id = t.project_id
WHERE t.status = 'done'
  AND EXTRACT(EPOCH FROM t.completed_at - t.created_at) / 86400 > pa.avg_lead_days
ORDER BY p.name, lead_days DESC;


-- =====================================================================
-- 3.2. EXISTS — есть хотя бы одна связанная запись с условием
-- Вопрос: «У кого из сотрудников есть хотя бы одна просроченная
-- незавершённая задача в действующем проекте?»
-- EXISTS останавливается на первой найденной строке — нам не нужно
-- количество, только факт.
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
      AND t.due_date < CURRENT_DATE
)
ORDER BY u.full_name;


-- =====================================================================
-- 3.3. NOT EXISTS — поиск отсутствующих событий
-- Вопрос: «Какие действующие проекты остались без тестировщика?»
-- Смысл: задачи таких проектов некому проверять перед сдачей, менеджеру
-- нужно включить в команду тестировщика.
-- =====================================================================
SELECT
    p.name,
    p.status,
    p.start_date,
    (SELECT count(*) FROM tasks t WHERE t.project_id = p.project_id) AS tasks
FROM projects p
WHERE p.status IN ('planned', 'active')
  AND NOT EXISTS (
      SELECT 1
      FROM project_members pm
      WHERE pm.project_id = p.project_id
        AND pm.role = 'tester'
  )
ORDER BY p.start_date;


-- =====================================================================
-- 3.4. Коррелированный подзапрос
-- Вопрос: «Насколько загружен и активен каждый участник в своём проекте?»
-- Для каждой строки project_members внутренние запросы берут проект и
-- пользователя из ТЕКУЩЕЙ строки внешнего запроса (pm.project_id, pm.user_id)
-- и считают индивидуальные показатели именно этого участника в этом проекте:
--   * число его незавершённых задач в проекте;
--   * их суммарная оценка в часах;
--   * когда он последний раз писал комментарий в задачах этого проекта.
-- =====================================================================
SELECT
    p.name      AS project,
    u.full_name AS member,
    pm.role,
    (SELECT count(*)
     FROM tasks t
     WHERE t.project_id = pm.project_id
       AND t.assignee_id = pm.user_id
       AND t.status <> 'done')                           AS open_tasks,
    (SELECT COALESCE(sum(t.estimate_hours), 0)
     FROM tasks t
     WHERE t.project_id = pm.project_id
       AND t.assignee_id = pm.user_id
       AND t.status <> 'done')                           AS open_hours,
    (SELECT max(c.created_at)::date
     FROM comments c
     JOIN tasks t ON t.task_id = c.task_id
     WHERE t.project_id = pm.project_id
       AND c.author_id = pm.user_id)                     AS last_comment
FROM project_members pm
JOIN projects p ON p.project_id = pm.project_id
JOIN users u    ON u.user_id = pm.user_id
WHERE p.status = 'active'
ORDER BY p.name, open_hours DESC;


SELECT
    p.name                              AS project,
    t.title                             AS task,
    a.full_name                         AS assignee,
    au.full_name                        AS last_author,
    c.body                              AS last_comment,
    c.created_at::date                  AS written,
    CURRENT_DATE - c.created_at::date   AS days_without_answer
FROM tasks t
JOIN projects p  ON p.project_id = t.project_id
JOIN users a     ON a.user_id = t.assignee_id
JOIN comments c  ON c.task_id = t.task_id
JOIN users au    ON au.user_id = c.author_id
WHERE p.status = 'active'
  AND t.status <> 'done'
  AND c.created_at = (SELECT max(c2.created_at)
                      FROM comments c2
                      WHERE c2.task_id = t.task_id)
  AND c.author_id <> t.assignee_id
ORDER BY days_without_answer DESC;

SELECT
    p.name        AS project,
    u.full_name   AS member,
    pm.role,
    pm.joined_at,
    ROW_NUMBER() OVER (PARTITION BY pm.project_id
                       ORDER BY pm.joined_at, u.full_name) AS join_order
FROM project_members pm
JOIN projects p ON p.project_id = pm.project_id
JOIN users u    ON u.user_id = pm.user_id
ORDER BY project, join_order;



SELECT
    p.name                                                          AS project,
    u.full_name                                                     AS employee,
    sum(t.estimate_hours)                                           AS done_hours,
    round(100.0 * sum(t.estimate_hours)
                / sum(sum(t.estimate_hours)) OVER (PARTITION BY p.project_id), 1) AS share_pct,
    RANK() OVER (PARTITION BY p.project_id
                 ORDER BY sum(t.estimate_hours) DESC)               AS place
FROM tasks t
JOIN projects p ON p.project_id = t.project_id
JOIN users u    ON u.user_id = t.assignee_id
WHERE t.status = 'done'
  AND t.estimate_hours IS NOT NULL
GROUP BY p.project_id, p.name, u.user_id, u.full_name
ORDER BY project, place;

