-- Заказчики проектов.
-- Заказчик — организация или подразделение, для которых выполняется проект.
-- С системой он не работает: требования передаёт руководителю проекта,
-- а отчёт о ходе проекта получает по почте через сервис уведомлений.
-- Миграция выполняется последней, после migration_tags.sql.
BEGIN;

CREATE TABLE customers (
    customer_id  SERIAL       PRIMARY KEY,
    name         VARCHAR(150) NOT NULL UNIQUE,
    contact_name VARCHAR(100),
    email        VARCHAR(100) NOT NULL,

    CONSTRAINT chk_customers_email CHECK (email LIKE '%_@_%._%')
);

-- У внутреннего проекта заказчика нет, поэтому столбец необязателен (NULL).
-- Заказчика, у которого есть проекты, удалить нельзя (RESTRICT).
ALTER TABLE projects
    ADD COLUMN customer_id INTEGER REFERENCES customers (customer_id) ON DELETE RESTRICT;

INSERT INTO customers (name, contact_name, email) VALUES
    ('ООО «Сфера Ритейл»', 'Белова Анна', 'belova@sfera-retail.example'),
    ('АО «Вектор»',        'Громов Илья', 'gromov@vector.example'),
    ('ООО «Медиа Плюс»',   NULL,          'info@mediaplus.example');

-- Заказчика указываем по уникальному названию проекта. Внутренние проекты
-- (портал, аналитическая платформа, бронирование переговорных) остаются
-- без заказчика. Названий, которых нет в базе, UPDATE не найдёт — скрипт
-- работает и на базе ЛР1, и на базе после ЛР2.
UPDATE projects p
SET customer_id = c.customer_id
FROM (VALUES
    ('Мобильное приложение', 'ООО «Сфера Ритейл»'),
    ('Интернет-магазин',     'ООО «Сфера Ритейл»'),
    ('CRM-система',          'АО «Вектор»'),
    ('Корпоративный сайт',   'АО «Вектор»'),
    ('Чат-бот поддержки',    'ООО «Медиа Плюс»')
) AS v(project, customer)
JOIN customers c ON c.name = v.customer
WHERE p.name = v.project;

COMMIT;


-- Проверка ограничений: каждая команда должна завершиться ошибкой (3 ошибки — ожидаемо).
INSERT INTO customers (name, email) VALUES ('АО «Вектор»', 'office@vector.example');  -- повтор названия (UNIQUE)
INSERT INTO customers (name, email) VALUES ('ООО «Нова»', 'nova-at-mail');             -- некорректный адрес (CHECK)
DELETE FROM customers WHERE name = 'ООО «Сфера Ритейл»';                               -- у заказчика есть проекты (FK, RESTRICT)
