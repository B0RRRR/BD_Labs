-- Проверка бизнес-ограничений: каждая команда должна завершиться ошибкой.
-- Запуск на копии базы: psql -d pm_demo -f db/demo/constraints.sql
-- Ожидается 17 ошибок; данные не меняются.
\set ON_ERROR_STOP off
\set VERBOSITY terse
\echo '1. Пользователь с некорректным адресом почты (CHECK)'
INSERT INTO users (full_name, email) VALUES ('Тест', 'test-at-mail');
\echo '2. Повтор кода проекта (UNIQUE)'
INSERT INTO projects (name, code, owner_id, start_date) VALUES ('Повтор кода', 'MOB', 1, '2026-12-01');
\echo '3. Окончание проекта раньше начала (CHECK)'
UPDATE projects SET end_date = '2026-01-01' WHERE code = 'MOB';
\echo '4. Приоритет задачи вне диапазона 1–5 (CHECK)'
UPDATE tasks SET priority = 7 WHERE task_id = 3;
\echo '5. Исполнитель не участвует в проекте (составной FK)'
UPDATE tasks SET assignee_id = 9 WHERE task_id = 3;
\echo '6. Переход статуса todo → done (триггер, PM001)'
UPDATE tasks SET status = 'done' WHERE task_id = 3;
\echo '7. Взять в работу неназначенную задачу (триггер, PM002)'
UPDATE tasks SET status = 'in_progress' WHERE task_id = 5;
\echo '8. Неоценённая задача в спринте (CHECK)'
UPDATE tasks SET sprint_id = 1 WHERE task_id = 5;
\echo '9. Задача в спринте чужого проекта (составной FK)'
UPDATE tasks SET sprint_id = (SELECT sprint_id FROM sprints s JOIN projects p USING (project_id) WHERE p.code = 'SHOP' AND s.number = 1) WHERE task_id = 14;
\echo '10. Превышение ёмкости спринта (триггер, PM004)'
UPDATE tasks SET estimate_hours = 60 WHERE task_id = 2;
\echo '11. Пересечение спринтов одного проекта (EXCLUDE)'
INSERT INTO sprints (project_id, number, start_date, end_date, capacity_hours) VALUES (1, 3, '2026-11-30', '2026-12-13', 80);
\echo '12. Второй активный спринт проекта (частичный уникальный индекс)'
UPDATE sprints SET status = 'active' WHERE project_id = 1 AND number = 2;
\echo '13. Проект с договором нельзя сделать внутренним (FK ON UPDATE CASCADE + NOT NULL)'
UPDATE projects SET customer_id = NULL WHERE code = 'MOB';
\echo '14. Второй договор у проекта (PRIMARY KEY, связь 1:1)'
INSERT INTO contracts (project_id, customer_id, number, signed_on, amount, budget_hours)
SELECT project_id, customer_id, 'Д-ТЕСТ', '2026-11-01', 1, 1 FROM projects WHERE code = 'MOB';
\echo '15. Удаление заказчика, у которого есть проекты (FK RESTRICT)'
DELETE FROM customers WHERE name = 'АО «Вектор»';
\echo '16. Пустой комментарий (CHECK)'
INSERT INTO comments (task_id, author_id, body) VALUES (3, 3, '   ');
\echo '17. Удаление метки, назначенной задачам (FK RESTRICT)'
DELETE FROM marks WHERE name = 'bug';
