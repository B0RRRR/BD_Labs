-- =====================================================================
-- dml.sql — операции изменения данных (задание 1.2)
--
-- Пункты 1–4 выполняются в одной транзакции и фиксируются (COMMIT),
-- пункт 5 — отдельная транзакция, которая откатывается (ROLLBACK).
-- Запускать один раз после data.sql.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 4а. Сначала — что НЕ получится удалить (вне транзакции, ошибка ожидаема).
-- Петрова владеет проектами: projects.owner_id → users ON DELETE RESTRICT.
-- ERROR: update or delete on table "users" violates foreign key constraint
--        "projects_owner_id_fkey" on table "projects"
-- ---------------------------------------------------------------------
DELETE FROM users WHERE email = 'petrova@mail.ru';


BEGIN;

-- ---------------------------------------------------------------------
-- 1. INSERT: новый проект + его участники + задачи.
-- Новый сотрудник Григорьева получает первый проект.
-- id нового проекта неизвестен (SERIAL) — находим по уникальному названию.
-- ---------------------------------------------------------------------
INSERT INTO projects (name, description, owner_id, status, start_date, end_date)
VALUES ('Бронирование переговорных', 'Сервис записи на переговорные комнаты',
        (SELECT user_id FROM users WHERE email = 'nikolaev@mail.ru'),
        'planned', '2026-11-09', '2027-01-29');

INSERT INTO project_members (project_id, user_id, role, joined_at)
SELECT p.project_id, u.user_id, v.role, DATE '2026-10-30'
FROM (VALUES
    ('nikolaev@mail.ru',     'manager'),
    ('grigorieva@gmail.com', 'developer'),
    ('zakharova@gmail.com',  'tester')
) AS v(email, role)
JOIN users u    ON u.email = v.email
JOIN projects p ON p.name = 'Бронирование переговорных';

-- статус, приоритет и created_at не указаны у части задач — сработают DEFAULT
INSERT INTO tasks (project_id, assignee_id, title, priority, due_date, estimate_hours)
SELECT p.project_id, u.user_id, v.title, v.priority, v.due_date::date, v.estimate_hours::numeric
FROM (VALUES
    ('nikolaev@mail.ru',     'Собрать требования',      2, '2026-11-20', '8'),
    ('grigorieva@gmail.com', 'Спроектировать схему БД', 2, '2026-12-01', '12'),
    (NULL,                   'Интеграция с календарём', 3, NULL,         NULL)
) AS v(email, title, priority, due_date, estimate_hours)
JOIN projects   p ON p.name = 'Бронирование переговорных'
LEFT JOIN users u ON u.email = v.email;

SELECT t.title, t.status, t.priority, u.full_name AS assignee
FROM tasks t
JOIN projects p ON p.project_id = t.project_id
LEFT JOIN users u ON u.user_id = t.assignee_id
WHERE p.name = 'Бронирование переговорных';


-- ---------------------------------------------------------------------
-- 2. UPDATE состояния операции: ревью «Фильтров каталога» пройдено,
-- задача завершена. completed_at обязателен для done (chk_tasks_completed),
-- поэтому оба столбца меняются одним UPDATE.
-- ---------------------------------------------------------------------
UPDATE tasks
SET status       = 'done',
    completed_at = now()
WHERE project_id = (SELECT project_id FROM projects WHERE name = 'Интернет-магазин')
  AND title = 'Фильтры каталога'
  AND status = 'review'
RETURNING task_id, title, status, completed_at;


-- ---------------------------------------------------------------------
-- 3. Массовое изменение: эскалация просроченных задач.
-- Во всех активных проектах незавершённые задачи с истёкшим сроком
-- поднимаются на один уровень приоритета (1 — самый высокий, ниже не опускаем).
-- ---------------------------------------------------------------------
UPDATE tasks t
SET priority = GREATEST(t.priority - 1, 1)
FROM projects p
WHERE p.project_id = t.project_id
  AND p.status = 'active'
  AND t.status <> 'done'
  AND t.due_date < CURRENT_DATE
  AND t.priority > 1
RETURNING t.task_id, p.name AS project, t.title, t.due_date, t.priority AS new_priority;


-- ---------------------------------------------------------------------
-- 4. DELETE с учётом ограничений целостности.
-- Проект «Внутренний портал» отменён; задачи, к которым так и не
-- приступили (todo), неактуальны и удаляются.
-- comments.task_id → tasks ON DELETE CASCADE: комментарии к ним удалятся
-- автоматически. Задачи в работе/выполненные остаются как история.
-- ---------------------------------------------------------------------
SELECT t.title, count(c.comment_id) AS comments_before
FROM tasks t
JOIN projects p ON p.project_id = t.project_id
LEFT JOIN comments c ON c.task_id = t.task_id
WHERE p.name = 'Внутренний портал' AND t.status = 'todo'
GROUP BY t.title;

DELETE FROM tasks t
USING projects p
WHERE p.project_id = t.project_id
  AND p.status = 'cancelled'
  AND t.status = 'todo'
RETURNING t.task_id, t.title;

-- комментарий «Начну после авторизации» удалён каскадно
SELECT count(*) AS comments_left FROM comments WHERE body = 'Начну после авторизации';   -- 0

COMMIT;


-- ---------------------------------------------------------------------
-- 5. ROLLBACK: ошибочное удаление завершённого проекта.
-- Каскадом удаляются задачи, комментарии и участники проекта;
-- после ROLLBACK всё возвращается.
-- ---------------------------------------------------------------------
BEGIN;

SELECT
    (SELECT count(*) FROM tasks)           AS tasks,
    (SELECT count(*) FROM comments)        AS comments,
    (SELECT count(*) FROM project_members) AS members;

DELETE FROM projects WHERE name = 'Корпоративный сайт';

SELECT
    (SELECT count(*) FROM tasks)           AS tasks,
    (SELECT count(*) FROM comments)        AS comments,
    (SELECT count(*) FROM project_members) AS members;   -- меньше на 6 / 5 / 3

ROLLBACK;

SELECT
    (SELECT count(*) FROM tasks)           AS tasks,
    (SELECT count(*) FROM comments)        AS comments,
    (SELECT count(*) FROM project_members) AS members;   -- как до DELETE
SELECT name, status FROM projects WHERE name = 'Корпоративный сайт';  -- проект на месте
