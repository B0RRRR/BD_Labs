-- Учёт трудозатрат (испытание И15): правила списания часов и факт по договору.
-- Запуск на копии базы с контрольными данными: psql -d pm_demo -f db/demo/worklogs.sql
-- Ожидается 9 ошибок (команды 2–10); в конце транзакция откатывается, данные не меняются.
\set ON_ERROR_STOP off
\set ON_ERROR_ROLLBACK on
\set VERBOSITY terse
BEGIN;
\echo '1. Исполнитель списывает 6 ч на задачу в работе, новый участник проекта помогает ему 3 ч — успешно'
INSERT INTO users (user_id, full_name, email) VALUES (99, 'Новиков Олег', 'novikov@mail.ru');
INSERT INTO project_members (project_id, user_id, role) VALUES (1, 99, 'developer');
INSERT INTO worklogs (task_id, user_id, work_date, hours, note)
VALUES (2, 3, '2026-11-13', 6, 'вёрстка формы'), (2, 99, '2026-11-13', 3, 'проверка на iOS')
RETURNING task_id, user_id, work_date, hours;
\echo '2. Списание на задачу, не взятую в работу (триггер, PM007)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (3, 3, '2026-11-13', 2);
\echo '3. Списание на завершённую задачу (триггер, PM007)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (1, 5, '2026-11-13', 2);
\echo '4. Списание сотрудником, не участвующим в проекте (триггер, PM007)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (2, 10, '2026-11-13', 2);
\echo '5. Списание будущим днём (триггер, PM007)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (2, 3, CURRENT_DATE + 1, 2);
\echo '6. Дата работ раньше создания задачи (триггер, PM007)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (2, 3, '2026-09-01', 2);
\echo '7. Нулевое число часов (CHECK)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (35, 3, '2026-11-13', 0);
\echo '8. Больше 24 ч в сутки: к 6 ч по задаче 2 ещё 20 ч по задаче 35 (триггер, PM006)'
INSERT INTO worklogs (task_id, user_id, work_date, hours) VALUES (35, 3, '2026-11-13', 20);
\echo '9. Исправление часов завершённой задачи задним числом (триггер, PM007)'
UPDATE worklogs SET hours = 10 WHERE task_id = 1 AND work_date = '2026-09-02';
\echo '10. Удаление сотрудника со списанными часами (FK RESTRICT)'
DELETE FROM users WHERE user_id = 99;
\echo '11. Факт по договорам: у MOB 54 + 6 + 3 = 63 ч'
SELECT p.code, sum(w.hours) AS fact_hours
FROM worklogs w JOIN tasks t USING (task_id) JOIN projects p USING (project_id)
GROUP BY p.code ORDER BY p.code;
ROLLBACK;
