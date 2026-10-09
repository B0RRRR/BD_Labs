INSERT INTO users (full_name, email) VALUES
    ('Иванов Иван',      'ivanov@mail.ru'),
    ('Петрова Анна',     'petrova@mail.ru'),
    ('Сидоров Пётр',     'sidorov@gmail.com'),
    ('Кузнецова Мария',  'kuznetsova@yandex.ru'),
    ('Смирнов Алексей',  'smirnov@gmail.com'),
    ('Волкова Ольга',    'volkova@mail.ru');   -- пока ни в одном проекте

INSERT INTO projects (name, description, owner_id, status, start_date, end_date) VALUES
    ('Мобильное приложение', 'Приложение для заказа еды', 1, 'active',    '2026-09-01', '2026-12-31'),
    ('Корпоративный сайт',   'Редизайн сайта компании',   2, 'completed', '2026-03-01', '2026-06-30'),
    ('CRM-система',          NULL,                        1, 'planned',   '2026-11-01', NULL);

INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES
    (1, 1, 'manager',   '2026-09-01'),
    (1, 3, 'developer', '2026-09-01'),
    (1, 4, 'tester',    '2026-09-05'),
    (1, 5, 'analyst',   '2026-09-02'),
    (2, 2, 'manager',   '2026-03-01'),
    (2, 3, 'developer', '2026-03-01'),
    (2, 4, 'tester',    '2026-03-10'),
    (3, 1, 'manager',   '2026-10-01'),
    (3, 5, 'developer', '2026-10-01');

INSERT INTO tasks (project_id, assignee_id, title, status, priority, due_date) VALUES
    (1, 5,    'Собрать требования',          'done',        2, '2026-09-10'),
    (1, 3,    'Сверстать экран входа',       'in_progress', 1, '2026-10-15'),
    (1, 3,    'Интеграция с платёжной системой', 'todo',    1, '2026-11-01'),
    (1, 4,    'Написать тест-кейсы',         'review',      3, '2026-10-20'),
    (1, NULL, 'Настроить push-уведомления',  'todo',        4, NULL),   -- не назначена
    (2, 3,    'Сверстать главную страницу',  'done',        2, '2026-04-15'),
    (2, 4,    'Проверить адаптивность',      'done',        3, '2026-05-30'),
    (3, 5,    'Собрать требования',          'todo',        2, '2026-11-15');


INSERT INTO comments (task_id, author_id, body) VALUES
    (1, 1, 'Требования согласованы с заказчиком'),
    (2, 3, 'Макет взял из Figma, начал верстку'),
    (2, 1, 'Не забудь про тёмную тему'),
    (4, 4, 'Тест-кейсы готовы, жду ревью'),
    (6, 2, 'Отличная работа!'),
    (8, 5, 'Жду созвон с заказчиком');
