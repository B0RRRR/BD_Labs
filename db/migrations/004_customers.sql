-- 004. Заказчики проектов. У внутреннего проекта заказчика нет (NULL);
-- заказчика с проектами удалить нельзя (RESTRICT).
-- Исходный сценарий с переносом данных — Lab1/migration_customers.sql.

CREATE TABLE customers (
    customer_id  SERIAL       PRIMARY KEY,
    name         VARCHAR(150) NOT NULL UNIQUE,
    contact_name VARCHAR(100),
    email        VARCHAR(100) NOT NULL,

    CONSTRAINT chk_customers_email CHECK (email LIKE '%_@_%._%')
);

ALTER TABLE projects
    ADD COLUMN customer_id INTEGER REFERENCES customers (customer_id) ON DELETE RESTRICT;
