BEGIN;
CREATE TABLE marks (
	mark_id SERIAL PRIMARY KEY,
	name TEXT NOT NULL UNIQUE,
	color VARCHAR(20),

    CHECK (color LIKE '#______')     -- формат цвета; NULL (нет цвета) CHECK пропускает
);

CREATE TABLE marks_tasks (
	mark_id INTEGER NOT NULL REFERENCES marks(mark_id) ON DELETE RESTRICT,
	task_id INTEGER NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    date TIMESTAMP NOT NULL DEFAULT now(),
	PRIMARY KEY (mark_id, task_id)
);

ALTER TABLE projects ADD COLUMN code VARCHAR(5) UNIQUE;

-- код задаём каждому существующему проекту (ищем по уникальному названию),
-- иначе SET NOT NULL ниже упадёт. Названий, которых нет в базе, UPDATE
-- просто не найдёт — скрипт работает и на базе ЛР1, и на базе после ЛР2.
UPDATE projects p
SET code = v.code
FROM (VALUES
    ('Мобильное приложение',      'MOB'),
    ('Корпоративный сайт',        'COR'),
    ('CRM-система',               'CRM'),
    ('Внутренний портал',         'PORT'),
    ('Интернет-магазин',          'SHOP'),
    ('Аналитическая платформа',   'DATA'),
    ('Чат-бот поддержки',         'BOT'),
    ('Бронирование переговорных', 'ROOM')
) AS v(name, code)
WHERE p.name = v.name;

ALTER TABLE projects ADD CONSTRAINT chk_code CHECK (length(code) BETWEEN 2 AND 5 AND code = upper(code));

ALTER TABLE projects ALTER COLUMN code SET NOT NULL;


-- Тестовые данные.
--   * у «backend» и «docs» нет цвета (цвет необязателен);
--   * «docs» не висит ни на одной задаче — для запроса «неиспользуемые метки»
--     и проверки, что такую метку удалить можно;
--   * на задаче 2 три метки, на задаче 3 две — «много меток у задачи»;
--   * «bug» висит на трёх задачах — «одна метка на многих задачах».
INSERT INTO marks (name, color) VALUES
    ('bug',      '#FF0000'),
    ('frontend', '#3366FF'),
    ('backend',  NULL),
    ('срочно',   '#FFAA00'),
    ('docs',     NULL);

-- id меток берём по названию (оно уникально), а не числами вручную
INSERT INTO marks_tasks (mark_id, task_id) VALUES
    ((SELECT mark_id FROM marks WHERE name = 'frontend'), 2),
    ((SELECT mark_id FROM marks WHERE name = 'срочно'),   2),
    ((SELECT mark_id FROM marks WHERE name = 'bug'),      2),
    ((SELECT mark_id FROM marks WHERE name = 'backend'),  3),
    ((SELECT mark_id FROM marks WHERE name = 'bug'),      3),
    ((SELECT mark_id FROM marks WHERE name = 'bug'),      4),
    ((SELECT mark_id FROM marks WHERE name = 'backend'),  5),
    ((SELECT mark_id FROM marks WHERE name = 'frontend'), 6);

COMMIT;                          -- NOT NULL estimate_hours
