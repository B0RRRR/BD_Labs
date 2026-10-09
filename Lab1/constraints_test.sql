
-- у пользователя не указано ФИО
INSERT INTO users (full_name, email) VALUES (NULL, 'noname@mail.ru');

-- email уже занят
INSERT INTO users (full_name, email) VALUES ('Иванов Иван 2', 'ivanov@mail.ru');

-- email без символа @
INSERT INTO users (full_name, email) VALUES ('Без почты', 'not-an-email');

-- дата окончания раньше даты начала
INSERT INTO projects (name, owner_id, start_date, end_date)
VALUES ('Машина времени', 1, '2026-10-01', '2026-01-01');

-- недопустимый статус проекта
UPDATE projects SET status = 'frozen' WHERE project_id = 1;

-- приоритет задачи вне диапазона 1..5
UPDATE tasks SET priority = 10 WHERE task_id = 1;

-- задача с таким названием уже есть в проекте 1
INSERT INTO tasks (project_id, title) VALUES (1, 'Собрать требования');

-- пользователь 3 уже участник проекта 1
INSERT INTO project_members (project_id, user_id, role) VALUES (1, 3, 'tester');

-- недопустимая роль участника
INSERT INTO project_members (project_id, user_id, role) VALUES (3, 6, 'boss');

-- задача в несуществующем проекте
INSERT INTO tasks (project_id, title) VALUES (999, 'Задача)');

-- нельзя удалить пользователя, который владеет проектом
DELETE FROM users WHERE user_id = 1;

-- пустой комментарий
INSERT INTO comments (task_id, author_id, body) VALUES (1, 1, '   ');


-- не дают ошибку:
BEGIN;

-- назначаем задачу 5 на пользователя 6 и удаляем его.
-- Задача остаётся, но становится не назначенной.
UPDATE tasks SET assignee_id = 6 WHERE task_id = 5;
DELETE FROM users WHERE user_id = 6;
SELECT task_id, title, assignee_id FROM tasks WHERE task_id = 5;   -- assignee_id = NULL

-- удаляем проект 2 - удаляются его задачи, комментарии и участники
DELETE FROM projects WHERE project_id = 2;
SELECT count(*) AS tasks_of_project_2   FROM tasks           WHERE project_id = 2;  -- 0
SELECT count(*) AS members_of_project_2 FROM project_members WHERE project_id = 2;  -- 0

ROLLBACK;
