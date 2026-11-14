-- 010. Роль приложения с минимально необходимыми правами.
-- Пароль в репозитории не хранится: его задаёт db/init.sh из переменной APP_DB_PASSWORD.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pm_app') THEN
        CREATE ROLE pm_app LOGIN;
    END IF;
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO pm_app', current_database());
END $$;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;   -- создавать объекты может только владелец
GRANT USAGE ON SCHEMA public TO pm_app;

-- Рабочие таблицы: чтение и изменение. DDL, TRUNCATE и владение — нет.
GRANT SELECT, INSERT, UPDATE, DELETE
    ON users, customers, projects, project_members, tasks, comments,
       marks, marks_tasks, sprints, contracts
    TO pm_app;

-- История и аудит пишут только триггеры (SECURITY DEFINER), приложению — только чтение.
GRANT SELECT ON task_status_history, audit_log TO pm_app;

-- Пакетная загрузка: приложение создаёт пакет и копирует строки, проверяет их import_tasks.
GRANT SELECT, INSERT ON import_batches, import_task_rows TO pm_app;
GRANT UPDATE (error, task_id) ON import_task_rows TO pm_app;
GRANT UPDATE (status, loaded, rejected, error) ON import_batches TO pm_app;

GRANT SELECT ON v_task_cards, v_sprint_load, mv_project_stats TO pm_app;

GRANT USAGE ON SEQUENCE users_user_id_seq, customers_customer_id_seq, projects_project_id_seq,
                        tasks_task_id_seq, comments_comment_id_seq, marks_mark_id_seq,
                        sprints_sprint_id_seq, import_batches_batch_id_seq
    TO pm_app;
