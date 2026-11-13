-- =====================================================================
-- window_tasks.sql — возможные доп. задания на оконные функции
--
-- Подготовка к защите, в сдачу не входит. Запускать на базе после
-- dml.sql (порядок запуска — в README.md).
--
-- Шпаргалка:
--   функция(...) OVER (
--       PARTITION BY ...  -- на какие группы делить (как GROUP BY, но строки не схлопываются)
--       ORDER BY ...      -- порядок внутри группы (нужен для рангов, LAG, нарастающих итогов)
--       ROWS BETWEEN ...  -- рамка: какие соседние строки брать (по умолчанию — от начала до текущей)
--   )
--
--   «рейтинг, место»                   → RANK / DENSE_RANK / ROW_NUMBER
--   «топ-N в каждой группе»            → ROW_NUMBER() OVER (PARTITION BY ...) + фильтр снаружи
--   «доля от общего»                   → x / sum(x) OVER ()
--   «сравнить со средним по группе»    → avg(x) OVER (PARTITION BY ...)
--   «нарастающий итог»                 → sum(x) OVER (ORDER BY ...)
--   «по сравнению с предыдущим»        → LAG(x) OVER (ORDER BY ...)
--   «скользящее среднее за N»          → avg(x) OVER (ORDER BY ... ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW)
--   «разбить на N равных групп»        → NTILE(N) OVER (ORDER BY ...)
--
-- Помнить:
--   * в WHERE оконную функцию писать нельзя — считать в подзапросе/CTE,
--     фильтровать снаружи;
--   * при ORDER BY ... DESC значения NULL идут первыми — писать NULLS LAST;
--   * оконные функции считаются после GROUP BY, поэтому можно
--     sum(sum(x)) OVER () и RANK() OVER (ORDER BY count(*)).
-- =====================================================================


-- =====================================================================
-- Задание 1. Рейтинг сотрудников
-- Составить рейтинг сотрудников по числу выполненных задач.
-- Показать место тремя способами и объяснить разницу.
-- =====================================================================
SELECT
    u.full_name,
    count(*)                                     AS done_tasks,
    RANK()       OVER (ORDER BY count(*) DESC)   AS rank,
    DENSE_RANK() OVER (ORDER BY count(*) DESC)   AS dense_rank,
    ROW_NUMBER() OVER (ORDER BY count(*) DESC)   AS row_number
FROM tasks t
JOIN users u ON u.user_id = t.assignee_id
WHERE t.status = 'done'
GROUP BY u.user_id, u.full_name
ORDER BY done_tasks DESC;
-- Пояснение:
--   сначала GROUP BY считает count(*) на человека, затем окно ранжирует;
--   RANK       — у равных одно место, следующее место пропускается: 1, 2, 2, 4;
--   DENSE_RANK — у равных одно место, без пропусков:                 1, 2, 2, 3;
--   ROW_NUMBER — просто номер строки, у равных разные номера:         1, 2, 3, 4.


-- =====================================================================
-- Задание 2. Топ-2 в каждой группе
-- Для каждого проекта вывести две самые трудоёмкие задачи.
-- =====================================================================
SELECT project, title, estimate_hours, place
FROM (
    SELECT
        p.name AS project,
        t.title,
        t.estimate_hours,
        ROW_NUMBER() OVER (PARTITION BY t.project_id
                           ORDER BY t.estimate_hours DESC, t.title) AS place
    FROM tasks t
    JOIN projects p ON p.project_id = t.project_id
    WHERE t.estimate_hours IS NOT NULL
) ranked
WHERE place <= 2
ORDER BY project, place;
-- Пояснение:
--   PARTITION BY project_id — нумерация начинается заново в каждом проекте;
--   неоценённые задачи отброшены: при DESC NULL встал бы на 1-е место,
--   а «трудоёмкость неизвестна» ≠ «самая трудоёмкая» (у CRM-системы все
--   задачи не оценены — её в результате нет);
--   t.title вторым ключом — при равных часах порядок предсказуем;
--   WHERE place <= 2 — снаружи: в WHERE того же уровня окно ещё не посчитано.


-- =====================================================================
-- Задание 3. Доля от общего
-- Для каждого проекта показать объём работ в часах и его долю (%)
-- в общем объёме всех проектов.
-- =====================================================================
SELECT
    p.name                                                           AS project,
    COALESCE(sum(t.estimate_hours), 0)                               AS hours,
    round(100.0 * COALESCE(sum(t.estimate_hours), 0)
                / sum(sum(t.estimate_hours)) OVER (), 1)             AS share_pct
FROM projects p
LEFT JOIN tasks t ON t.project_id = p.project_id
GROUP BY p.project_id, p.name
ORDER BY hours DESC;
-- Пояснение:
--   sum(t.estimate_hours)            — обычный агрегат: часы одного проекта;
--   sum(sum(...)) OVER ()            — оконный: складывает часы всех проектов;
--   OVER () без PARTITION BY         — окно = весь результат;
--   сумма столбца share_pct ≈ 100.


-- =====================================================================
-- Задание 4. Сравнение со средним по группе
-- Вывести задачи, оценка которых выше средней оценки задач того же
-- проекта, и на сколько часов выше.
-- (Тот же смысл, что запрос 3.1, но без подзапроса со средними в FROM.)
-- =====================================================================
SELECT project, title, estimate_hours, project_avg,
       estimate_hours - project_avg AS above_avg
FROM (
    SELECT
        p.name AS project,
        t.title,
        t.estimate_hours,
        round(avg(t.estimate_hours) OVER (PARTITION BY t.project_id), 1) AS project_avg
    FROM tasks t
    JOIN projects p ON p.project_id = t.project_id
) x
WHERE estimate_hours > project_avg
ORDER BY project, above_avg DESC;
-- Пояснение:
--   avg(...) OVER (PARTITION BY project_id) ставит рядом с каждой задачей
--   среднее по её проекту, строки не схлопываются (в отличие от GROUP BY).
--   ВАЖНО: если добавить ORDER BY внутрь OVER, среднее станет нарастающим
--   (от первой строки до текущей) — здесь это было бы ошибкой.


-- =====================================================================
-- Задание 5. Нарастающий итог
-- По месяцам завершения задач показать: сколько задач закрыто за месяц,
-- сколько часов, и сколько задач/часов закрыто всего с начала года.
-- =====================================================================
SELECT
    to_char(month, 'YYYY-MM')                AS month,
    done_tasks,
    done_hours,
    sum(done_tasks) OVER (ORDER BY month)    AS tasks_total,
    sum(done_hours) OVER (ORDER BY month)    AS hours_total
FROM (
    SELECT date_trunc('month', completed_at) AS month,
           count(*)                          AS done_tasks,
           sum(estimate_hours)               AS done_hours
    FROM tasks
    WHERE status = 'done'
    GROUP BY 1
) m
ORDER BY month;
-- Пояснение:
--   ORDER BY внутри OVER → рамка «от первой строки до текущей»,
--   поэтому sum даёт накопленную сумму; последняя строка = общий итог.


-- =====================================================================
-- Задание 6. Сравнение с предыдущим периодом
-- По месяцам создания задач: сколько задач создано, сколько в
-- предыдущем месяце и изменение в процентах.
-- =====================================================================
SELECT
    to_char(month, 'YYYY-MM')                              AS month,
    created,
    LAG(created) OVER (ORDER BY month)                     AS prev_month,
    round(100.0 * (created - LAG(created) OVER (ORDER BY month))
                / LAG(created) OVER (ORDER BY month))      AS change_pct
FROM (
    SELECT date_trunc('month', created_at) AS month, count(*) AS created
    FROM tasks
    GROUP BY 1
) m
ORDER BY month;
-- Пояснение:
--   LAG(x) — значение x из предыдущей строки окна; у первой строки NULL
--   (предыдущей нет), поэтому и процент у первого месяца пустой;
--   LEAD(x) — то же, но из следующей строки;
--   «предыдущая» — это предыдущая СТРОКА: июня в данных нет, поэтому
--   для июля предыдущим окажется май.


-- =====================================================================
-- Задание 7. Паузы в обсуждении
-- Найти задачи, в которых между двумя соседними комментариями прошло
-- больше 10 дней («обсуждение замирало»), и показать самую долгую паузу.
-- =====================================================================
WITH gaps AS (
    SELECT
        c.task_id,
        c.created_at,
        c.created_at::date
          - LAG(c.created_at::date) OVER (PARTITION BY c.task_id
                                          ORDER BY c.created_at) AS days_since_prev
    FROM comments c
)
SELECT
    p.name                   AS project,
    t.title                  AS task,
    count(*) + 1             AS comments_in_chain,   -- у первого комментария паузы нет
    max(g.days_since_prev)   AS max_pause_days
FROM gaps g
JOIN tasks t    ON t.task_id = g.task_id
JOIN projects p ON p.project_id = t.project_id
WHERE g.days_since_prev IS NOT NULL
GROUP BY p.name, t.task_id, t.title
HAVING max(g.days_since_prev) > 10
ORDER BY max_pause_days DESC;
-- Пояснение:
--   1) в CTE окно с LAG считает паузу перед каждым комментарием своей задачи;
--   2) снаружи обычный GROUP BY + HAVING берёт максимальную паузу.
--   Окно и агрегат в разных шагах: сначала «по строкам», потом «по группам».


-- =====================================================================
-- Задание 8. Порядковый номер внутри группы
-- Пронумеровать задачи каждого проекта в порядке создания
-- («задача №1 проекта», «задача №2 …») и показать, сколько всего задач
-- в проекте, не используя GROUP BY.
-- =====================================================================
SELECT
    p.name                                                        AS project,
    ROW_NUMBER() OVER (PARTITION BY t.project_id
                       ORDER BY t.created_at, t.task_id)          AS task_no,
    count(*)     OVER (PARTITION BY t.project_id)                 AS tasks_in_project,
    t.title,
    t.created_at::date                                            AS created
FROM tasks t
JOIN projects p ON p.project_id = t.project_id
ORDER BY project, task_no;
-- Пояснение:
--   count(*) OVER (PARTITION BY ...) — количество строк группы рядом с
--   каждой строкой; GROUP BY здесь не подошёл бы: он оставил бы одну
--   строку на проект.


-- =====================================================================
-- Задание 9. Скользящее среднее
-- Для каждой выполненной задачи (по порядку завершения внутри проекта)
-- показать время выполнения в днях и среднее время по ней и двум
-- предыдущим выполненным задачам того же проекта.
-- =====================================================================
SELECT
    project,
    title,
    completed,
    lead_days,
    round(avg(lead_days) OVER (PARTITION BY project
                               ORDER BY completed
                               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS avg_last_3
FROM (
    SELECT
        p.name                                                        AS project,
        t.title,
        t.completed_at::date                                          AS completed,
        round(EXTRACT(EPOCH FROM t.completed_at - t.created_at) / 86400, 1) AS lead_days
    FROM tasks t
    JOIN projects p ON p.project_id = t.project_id
    WHERE t.status = 'done'
) d
ORDER BY project, completed;
-- Пояснение:
--   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW — окно из текущей строки и
--   двух предыдущих; у первых строк проекта берётся сколько есть (1 или 2).
--   Так видно, ускоряется команда или замедляется.


-- =====================================================================
-- Задание 10. Разбиение на группы
-- Разделить все оценённые задачи на 4 группы по трудоёмкости
-- (1 — самые лёгкие, 4 — самые тяжёлые) и для каждой группы показать
-- диапазон часов и число задач.
-- =====================================================================
SELECT
    quartile,
    count(*)            AS tasks,
    min(estimate_hours) AS min_hours,
    max(estimate_hours) AS max_hours,
    round(avg(estimate_hours), 1) AS avg_hours
FROM (
    SELECT estimate_hours,
           NTILE(4) OVER (ORDER BY estimate_hours) AS quartile
    FROM tasks
    WHERE estimate_hours IS NOT NULL
) q
GROUP BY quartile
ORDER BY quartile;
-- Пояснение:
--   NTILE(4) делит упорядоченные строки на 4 почти равные по количеству
--   части и возвращает номер части (1..4).
--   Делит по количеству строк, а не по значениям: задачи с одинаковой
--   оценкой (12 ч, 20 ч) могут попасть в соседние группы — поэтому
--   max одной группы совпадает с min следующей.


SELECT
    u.full_name,
    t.title,
    t.completed_at::date                                      AS completed,
    LAG(t.title) OVER w                                       AS prev_task,
    t.completed_at::date - LAG(t.completed_at::date) OVER w   AS days_since_prev
FROM tasks t
JOIN users u ON u.user_id = t.assignee_id
WHERE t.status = 'done'
WINDOW w AS (PARTITION BY u.user_id ORDER BY t.completed_at)
ORDER BY u.full_name, completed;


SELECT
u.full_name AS employee,
count(*) AS tasks_in_progress,
avg(count(*)) OVER () AS avg_tasks_in_progress,
round(count(*) - avg(count(*)) OVER (), 1)  AS diff,
RANK() OVER (ORDER BY count(*) DESC) AS place
FROM tasks t
JOIN users u ON u.user_id = t.assignee_id
WHERE t.status <> 'done'
GROUP BY u.user_id, u.full_name
ORDER BY place, employee;

SELECT
project,
employee,
total_estimate_hours,
project_hours,
round(100.0 * total_estimate_hours / project_hours, 1) AS share_pct
FROM (
    SELECT
u.full_name AS employee,
p.name AS project,
sum(t.estimate_hours) AS total_estimate_hours,
sum(sum(t.estimate_hours)) OVER (PARTITION BY p.project_id) AS project_hours,
RANK() OVER (PARTITION BY p.project_id ORDER BY sum(t.estimate_hours) DESC) AS place

FROM projects p
JOIN tasks t ON t.project_id = p.project_id
JOIN users u ON u.user_id = t.assignee_id
WHERE t.status <> 'done' AND t.estimate_hours IS NOT NULL
GROUP BY u.user_id, u.full_name, p.project_id, p.name
) ts
WHERE place = 1
ORDER BY share_pct DESC;




SELECT
    employee,
    count(*)              AS done_tasks,
    round(avg(pause), 1)  AS avg_pause,
    max(pause)            AS max_pause
FROM (
    SELECT
    u.user_id,
    u.full_name AS employee,
    t.completed_at::date
      - LAG(t.completed_at::date) OVER (PARTITION BY u.user_id ORDER BY t.completed_at) AS pause
FROM tasks t
JOIN users u ON u.user_id = t.assignee_id
WHERE t.status = 'done'

) q
GROUP BY user_id, employee
HAVING count(*) >= 2
ORDER BY avg_pause;


SELECT 
p.name as project,
t.title as title,
date_trunc('day', created_at)::date AS day,
date_trunc('day', created_at)::date - FIRST_VALUE(date_trunc('day', created_at)::date) OVER(PARTITION BY p.project_id ORDER BY t.created_at) AS days_from,

FIRST_VALUE(title) OVER(PARTITION BY p.project_id ORDER BY t.created_at) as first_task,
LAST_VALUE(title) OVER(PARTITION BY p.project_id ORDER BY t.created_at) as last_task
FROM projects p
JOIN tasks t ON p.project_id = t.project_id
WHERE p.status = 'active'
ORDER BY p.project_id, t.created_at, t.task_id

SELECT project, title, hours, place, tasks_in_project, share_pct
FROM (
SELECT
p.name as project,
t.title as title,
t.estimate_hours as hours,
RANK() OVER(PARTITION BY p.project_id ORDER BY t.estimate_hours DESC) as place,
count(t.estimate_hours) OVER(PARTITION BY p.project_id) tasks_in_project,
round(t.estimate_hours / sum(t.estimate_hours) OVER (PARTITION BY p.project_id) * 100, 2) as share_pct

FROM projects p
JOIN tasks t ON p.project_id = t.project_id
WHERE t.estimate_hours IS NOT NULL
)
WHERE place < 4
ORDER BY project, place, title