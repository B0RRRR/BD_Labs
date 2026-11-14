-- Контрольный набор данных: состояние базы после всех сценариев ЛР № 1 и № 2
-- (Lab1/data.sql, Lab2/data2.sql, Lab2/dml.sql, миграции кодов и заказчиков).
-- Загружается после миграции 004, до миграции 005. На этих данных
-- автотесты проверяют аналитические запросы с заранее известным результатом.
BEGIN;


-- Заказчики
INSERT INTO customers (customer_id, name, contact_name, email) VALUES (1, 'ООО «Сфера Ритейл»', 'Белова Анна', 'belova@sfera-retail.example');
INSERT INTO customers (customer_id, name, contact_name, email) VALUES (2, 'АО «Вектор»', 'Громов Илья', 'gromov@vector.example');
INSERT INTO customers (customer_id, name, contact_name, email) VALUES (3, 'ООО «Медиа Плюс»', NULL, 'info@mediaplus.example');

-- Пользователи
INSERT INTO users (user_id, full_name, email, created_at) VALUES (1, 'Иванов Иван', 'ivanov@mail.ru', '2026-01-15 09:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (2, 'Петрова Анна', 'petrova@mail.ru', '2026-01-20 09:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (3, 'Сидоров Пётр', 'sidorov@gmail.com', '2026-02-02 10:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (4, 'Кузнецова Мария', 'kuznetsova@yandex.ru', '2026-02-10 10:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (5, 'Смирнов Алексей', 'smirnov@gmail.com', '2026-02-16 11:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (6, 'Волкова Ольга', 'volkova@mail.ru', '2026-09-28 12:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (10, 'Николаев Дмитрий', 'nikolaev@mail.ru', '2026-04-01 09:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (11, 'Орлова Екатерина', 'orlova@yandex.ru', '2026-04-15 09:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (12, 'Фёдоров Максим', 'fedorov@gmail.com', '2026-05-12 10:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (13, 'Морозова Светлана', 'morozova@mail.ru', '2026-05-05 10:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (14, 'Лебедев Артём', 'lebedev@yandex.ru', '2026-06-20 11:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (15, 'Григорьева Наталья', 'grigorieva@gmail.com', '2026-10-26 09:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (16, 'Павлов Игорь', 'pavlov@mail.ru', '2026-04-20 10:00:00');
INSERT INTO users (user_id, full_name, email, created_at) VALUES (17, 'Захарова Юлия', 'zakharova@gmail.com', '2026-08-25 10:00:00');

-- Проекты
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (5, 'Внутренний портал', 'Портал для сотрудников', 2, 'cancelled', '2026-05-01', '2026-07-15', 'PORT', NULL);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (7, 'Аналитическая платформа', 'Отчёты по продажам и складу', 10, 'active', '2026-08-01', NULL, 'DATA', NULL);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (9, 'Бронирование переговорных', 'Сервис записи на переговорные комнаты', 10, 'planned', '2026-11-09', '2027-01-29', 'ROOM', NULL);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (6, 'Интернет-магазин', 'Магазин бытовой техники', 2, 'active', '2026-07-01', '2026-12-15', 'SHOP', 1);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (1, 'Мобильное приложение', 'Приложение для заказа еды', 1, 'active', '2026-09-01', '2026-12-31', 'MOB', 1);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (2, 'Корпоративный сайт', 'Редизайн сайта компании', 2, 'completed', '2026-03-01', '2026-06-30', 'COR', 2);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (3, 'CRM-система', NULL, 1, 'planned', '2026-11-01', NULL, 'CRM', 2);
INSERT INTO projects (project_id, name, description, owner_id, status, start_date, end_date, code, customer_id) VALUES (8, 'Чат-бот поддержки', NULL, 11, 'planned', '2026-12-01', NULL, 'BOT', 3);

-- Задачи
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (4, 1, 4, 'Написать тест-кейсы', NULL, 'review', 2, '2026-09-20 14:00:00', '2026-10-20', 8.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (14, 1, 4, 'Тестирование экрана входа', NULL, 'todo', 2, '2026-10-10 10:00:00', '2026-11-10', 4.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (5, 1, NULL, 'Настроить push-уведомления', NULL, 'todo', 4, '2026-10-05 10:00:00', NULL, NULL, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (3, 1, 3, 'Интеграция с платёжной системой', NULL, 'todo', 1, '2026-09-15 09:30:00', '2026-11-01', 24.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (2, 1, 3, 'Сверстать экран входа', NULL, 'in_progress', 1, '2026-09-12 11:00:00', '2026-10-15', 12.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (1, 1, 5, 'Собрать требования', NULL, 'done', 2, '2026-09-01 10:00:00', '2026-09-10', 16.0, '2026-09-09 17:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (7, 2, 4, 'Проверить адаптивность', NULL, 'done', 3, '2026-04-20 12:00:00', '2026-05-30', 6.0, '2026-06-03 16:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (6, 2, 3, 'Сверстать главную страницу', NULL, 'done', 2, '2026-03-05 10:00:00', '2026-04-15', 20.0, '2026-04-14 18:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (8, 3, 5, 'Собрать требования', NULL, 'todo', 2, '2026-10-02 10:00:00', '2026-11-15', NULL, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (12, 1, 12, 'Экран корзины', NULL, 'todo', 2, '2026-10-01 10:00:00', '2026-11-20', 16.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (13, 1, 5, 'Описать сценарии оплаты', NULL, 'done', 2, '2026-09-12 10:00:00', '2026-09-25', 6.0, '2026-09-24 17:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (15, 2, 4, 'Провести нагрузочное тестирование', NULL, 'done', 3, '2026-05-15 10:00:00', '2026-06-20', 10.0, '2026-06-18 18:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (16, 2, 3, 'Настроить хостинг', NULL, 'done', 2, '2026-03-03 10:00:00', '2026-03-20', 4.0, '2026-03-18 17:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (17, 2, 3, 'Обновить ссылки в футере', NULL, 'done', 5, '2026-04-10 10:00:00', '2026-05-10', 0.0, '2026-04-10 12:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (18, 2, 2, 'Согласовать макеты', NULL, 'done', 1, '2026-03-02 09:00:00', '2026-03-15', 6.0, '2026-03-20 15:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (19, 3, NULL, 'Выбрать CRM-платформу', NULL, 'todo', 1, '2026-10-15 10:00:00', '2026-11-10', NULL, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (20, 5, 16, 'Прототип главной страницы', NULL, 'done', 2, '2026-05-05 10:00:00', '2026-05-25', 12.0, '2026-05-24 18:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (21, 5, 16, 'Авторизация через AD', NULL, 'in_progress', 1, '2026-05-20 10:00:00', '2026-06-30', 24.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (23, 5, 2, 'Согласовать структуру разделов', NULL, 'done', 2, '2026-05-02 10:00:00', '2026-05-15', 4.0, '2026-05-14 17:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (24, 6, NULL, 'Интеграция со службой доставки', NULL, 'todo', 1, '2026-10-12 10:00:00', '2026-12-01', 24.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (25, 6, 14, 'Описать каталог товаров', NULL, 'done', 2, '2026-07-02 10:00:00', '2026-07-15', 12.0, '2026-07-14 17:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (26, 6, 13, 'Тестирование корзины', NULL, 'done', 2, '2026-08-20 10:00:00', '2026-09-01', 8.0, '2026-08-30 15:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (27, 6, 13, 'Регрессионное тестирование', NULL, 'todo', 2, '2026-10-01 10:00:00', '2026-11-30', 16.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (28, 6, 12, 'Сверстать карточку товара', NULL, 'done', 2, '2026-07-22 10:00:00', '2026-08-15', 14.0, '2026-08-12 16:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (29, 6, 12, 'Сверстать каталог', NULL, 'done', 2, '2026-08-01 10:00:00', '2026-08-31', 20.0, '2026-09-05 13:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (31, 6, 10, 'Спроектировать базу данных', NULL, 'done', 1, '2026-07-03 10:00:00', '2026-07-20', 16.0, '2026-07-25 12:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (32, 6, 10, 'Реализовать корзину', NULL, 'done', 1, '2026-07-21 09:00:00', '2026-08-20', 32.0, '2026-08-19 18:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (33, 6, 10, 'Исправить ошибку округления цен', NULL, 'done', 1, '2026-09-20 09:00:00', '2026-09-22', 2.0, '2026-09-21 11:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (34, 6, 10, 'Подключить онлайн-оплату', NULL, 'in_progress', 1, '2026-09-01 10:00:00', '2026-10-10', 40.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (35, 6, 3, 'Личный кабинет покупателя', NULL, 'in_progress', 2, '2026-09-10 10:00:00', '2026-11-20', 30.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (36, 6, 3, 'Оптимизировать загрузку изображений', NULL, 'todo', 4, '2026-10-20 10:00:00', NULL, NULL, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (37, 7, NULL, 'Настроить резервное копирование', NULL, 'todo', 2, '2026-10-15 10:00:00', NULL, 6.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (40, 7, 16, 'Разработать дашборд склада', NULL, 'todo', 3, '2026-09-20 10:00:00', '2026-11-30', 30.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (41, 7, 14, 'Настроить ETL-процесс', NULL, 'done', 1, '2026-08-10 10:00:00', '2026-09-15', 40.0, '2026-09-30 19:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (42, 7, 14, 'Исправить дубли в загрузке', NULL, 'done', 1, '2026-10-05 09:00:00', '2026-10-07', 3.0, '2026-10-06 12:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (44, 7, 11, 'Собрать требования к отчётам', NULL, 'done', 2, '2026-08-02 10:00:00', '2026-08-20', 20.0, '2026-08-18 17:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (45, 7, 11, 'Описать витрину данных', NULL, 'done', 3, '2026-08-20 10:00:00', '2026-09-10', 8.0, '2026-09-08 16:00:00');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (46, 9, 10, 'Собрать требования', NULL, 'todo', 2, '2026-11-14 22:36:55.964402', '2026-11-20', 8.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (47, 9, 15, 'Спроектировать схему БД', NULL, 'todo', 2, '2026-11-14 22:36:55.964402', '2026-12-01', 12.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (48, 9, NULL, 'Интеграция с календарём', NULL, 'todo', 3, '2026-11-14 22:36:55.964402', NULL, NULL, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (30, 6, 12, 'Фильтры каталога', NULL, 'done', 3, '2026-09-15 10:00:00', '2026-10-25', 12.0, '2026-11-14 22:36:55.964402');
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (11, 1, 12, 'Экран каталога блюд', NULL, 'in_progress', 1, '2026-09-15 10:00:00', '2026-11-05', 18.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (43, 7, 14, 'Настроить права доступа', NULL, 'review', 1, '2026-09-25 10:00:00', '2026-10-20', 10.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (39, 7, 16, 'Разработать дашборд продаж', NULL, 'in_progress', 1, '2026-09-01 10:00:00', '2026-11-06', 36.0, NULL);
INSERT INTO tasks (task_id, project_id, assignee_id, title, description, status, priority, created_at, due_date, estimate_hours, completed_at) VALUES (38, 7, 17, 'Тест-план платформы', NULL, 'in_progress', 2, '2026-09-05 10:00:00', '2026-10-28', 12.0, NULL);

-- Комментарии
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (1, 1, 1, 'Требования согласованы с заказчиком', '2026-09-09 18:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (2, 2, 3, 'Макет взял из Figma, начал верстку', '2026-09-13 10:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (3, 2, 1, 'Не забудь про тёмную тему', '2026-09-14 12:30:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (4, 4, 4, 'Тест-кейсы готовы, жду ревью', '2026-10-18 16:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (5, 6, 2, 'Отличная работа!', '2026-04-15 11:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (6, 8, 5, 'Жду созвон с заказчиком', '2026-10-03 09:30:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (8, 13, 1, 'Сценарии утверждены', '2026-09-24 18:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (9, 11, 12, 'Жду иконки от дизайнера', '2026-10-05 11:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (10, 15, 4, 'Сайт выдерживает 500 RPS', '2026-06-18 15:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (11, 18, 3, 'Макеты согласованы, начинаю вёрстку', '2026-03-20 10:30:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (12, 18, 2, 'Заказчик попросил ещё одну итерацию макетов', '2026-03-14 16:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (13, 16, 3, 'Хостинг оплачен на год', '2026-03-18 12:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (15, 21, 2, 'Проект закрыт решением руководства', '2026-07-15 17:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (16, 21, 16, 'Нет доступа к тестовому AD', '2026-06-10 10:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (17, 33, 13, 'Проверила, цены округляются верно', '2026-09-21 16:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (18, 30, 12, 'Фильтры готовы, отправил на ревью', '2026-10-24 19:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (19, 35, 3, 'Сделал регистрацию, осталась история заказов', '2026-10-15 17:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (20, 34, 13, 'Готова тестировать, как только будет стенд', '2026-10-20 13:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (21, 34, 10, 'Ключи получены, продолжаю', '2026-10-02 09:15:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (22, 34, 2, 'Банк обещал ключи к концу месяца', '2026-09-20 18:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (23, 34, 10, 'Ждём тестовые ключи от банка', '2026-09-15 12:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (24, 29, 2, 'Срок сорван, переносим демо', '2026-09-01 10:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (25, 32, 10, 'Исправил', '2026-08-19 10:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (26, 32, 13, 'Ошибка при оформлении пустой корзины', '2026-08-18 14:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (27, 31, 2, 'Добавь таблицу скидок', '2026-07-23 09:40:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (28, 31, 10, 'Схема готова, жду ревью', '2026-07-22 11:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (29, 38, 17, 'Тест-план согласован наполовину', '2026-10-01 12:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (30, 43, 10, 'Нужно закрыть доступ к финансовым отчётам', '2026-10-21 10:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (31, 39, 16, 'Первая версия дашборда на стенде', '2026-10-22 18:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (32, 41, 10, 'Это критично для дашбордов', '2026-09-11 09:00:00');
INSERT INTO comments (comment_id, task_id, author_id, body, created_at) VALUES (33, 41, 14, 'Источник отдаёт дубли, разбираюсь', '2026-09-10 11:00:00');

-- Метки
INSERT INTO marks (mark_id, name, color) VALUES (1, 'bug', '#FF0000');
INSERT INTO marks (mark_id, name, color) VALUES (2, 'frontend', '#3366FF');
INSERT INTO marks (mark_id, name, color) VALUES (3, 'backend', NULL);
INSERT INTO marks (mark_id, name, color) VALUES (4, 'срочно', '#FFAA00');
INSERT INTO marks (mark_id, name, color) VALUES (5, 'docs', NULL);

-- Метки задач
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (2, 2, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (4, 2, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (1, 2, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (3, 3, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (1, 3, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (1, 4, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (3, 5, '2026-11-14 22:36:55.998919');
INSERT INTO marks_tasks (mark_id, task_id, date) VALUES (2, 6, '2026-11-14 22:36:55.998919');

-- Участники проектов
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (1, 1, 'manager', '2026-09-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (1, 3, 'developer', '2026-09-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (1, 4, 'tester', '2026-09-05');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (1, 5, 'analyst', '2026-09-02');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (2, 2, 'manager', '2026-03-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (2, 3, 'developer', '2026-03-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (2, 4, 'tester', '2026-03-10');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (3, 1, 'manager', '2026-10-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (3, 5, 'developer', '2026-10-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (1, 13, 'tester', '2026-10-15');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (1, 12, 'developer', '2026-09-10');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (5, 16, 'developer', '2026-05-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (5, 13, 'tester', '2026-05-10');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (5, 2, 'manager', '2026-05-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (6, 14, 'analyst', '2026-07-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (6, 13, 'tester', '2026-07-15');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (6, 12, 'developer', '2026-07-05');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (6, 10, 'developer', '2026-07-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (6, 3, 'developer', '2026-09-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (6, 2, 'manager', '2026-07-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (7, 17, 'tester', '2026-09-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (7, 16, 'developer', '2026-08-10');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (7, 14, 'developer', '2026-08-05');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (7, 11, 'analyst', '2026-08-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (7, 10, 'manager', '2026-08-01');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (8, 11, 'manager', '2026-10-20');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (9, 10, 'manager', '2026-10-30');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (9, 15, 'developer', '2026-10-30');
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (9, 17, 'tester', '2026-10-30');

SELECT setval('comments_comment_id_seq', 33, true);
SELECT setval('customers_customer_id_seq', 5, true);
SELECT setval('marks_mark_id_seq', 5, true);
SELECT setval('projects_project_id_seq', 9, true);
SELECT setval('tasks_task_id_seq', 48, true);
SELECT setval('users_user_id_seq', 17, true);

COMMIT;
