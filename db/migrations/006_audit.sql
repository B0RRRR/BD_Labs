-- 006. Аудит изменений проектов, задач и договоров.
-- Журнал служебный: пишет только триггер, приложение может его лишь читать.

CREATE TABLE audit_log (
    audit_id    BIGSERIAL   PRIMARY KEY,
    table_name  TEXT        NOT NULL,
    operation   VARCHAR(6)  NOT NULL,
    row_key     TEXT        NOT NULL,          -- значение первичного ключа строки
    changed_at  TIMESTAMP   NOT NULL DEFAULT now(),
    db_user     TEXT        NOT NULL DEFAULT session_user,
    app_user_id INTEGER,                       -- пользователь приложения; без FK — журнал
                                               -- хранит действия и удалённых пользователей
    old_data    JSONB,                         -- для UPDATE — только изменённые поля
    new_data    JSONB,

    CONSTRAINT chk_audit_operation CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
);
CREATE INDEX ix_audit_row ON audit_log (table_name, row_key);

-- Пользователь приложения передаётся в транзакцию параметром app.user_id
-- (SELECT set_config('app.user_id', '3', true)); вне приложения он не задан.
CREATE FUNCTION app_user_id() RETURNS integer
LANGUAGE sql STABLE AS $$
    SELECT nullif(current_setting('app.user_id', true), '')::integer
$$;

-- TG_ARGV[0] — имя столбца первичного ключа.
-- SECURITY DEFINER: журнал пишется с правами владельца, у роли приложения
-- права на запись в audit_log нет.
CREATE FUNCTION audit_row() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    o jsonb := CASE WHEN TG_OP <> 'INSERT' THEN to_jsonb(OLD) END;
    n jsonb := CASE WHEN TG_OP <> 'DELETE' THEN to_jsonb(NEW) END;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        SELECT jsonb_object_agg(key, o -> key), jsonb_object_agg(key, value)
        INTO o, n
        FROM jsonb_each(n)
        WHERE o -> key IS DISTINCT FROM value;
        IF n IS NULL THEN
            RETURN NULL;                       -- значения не изменились
        END IF;
    END IF;
    INSERT INTO audit_log (table_name, operation, row_key, app_user_id, old_data, new_data)
    VALUES (TG_TABLE_NAME, TG_OP,
            COALESCE(to_jsonb(NEW), to_jsonb(OLD)) ->> TG_ARGV[0],
            app_user_id(), o, n);
    RETURN NULL;
END $$;

CREATE TRIGGER trg_projects_audit AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION audit_row('project_id');
CREATE TRIGGER trg_tasks_audit AFTER INSERT OR UPDATE OR DELETE ON tasks
    FOR EACH ROW EXECUTE FUNCTION audit_row('task_id');
CREATE TRIGGER trg_contracts_audit AFTER INSERT OR UPDATE OR DELETE ON contracts
    FOR EACH ROW EXECUTE FUNCTION audit_row('project_id');
