-- 013. Учёт фактических трудозатрат.
-- Сотрудник списывает часы, потраченные на задачу; по сумме списанных часов отчёт
-- по договорам сравнивает факт с бюджетом договора (план/факт).
-- Учёт ведётся с момента миграции: прошлые трудозатраты неизвестны, переноса данных нет.
--
-- Новые коды ошибок:
--   PM006 — превышен суточный лимит 24 ч на сотрудника;
--   PM007 — списание недопустимо: задача не в работе, сотрудник не участник проекта
--           или дата работ вне периода от создания задачи до сегодня.

CREATE TABLE worklogs (
    worklog_id SERIAL       PRIMARY KEY,
    task_id    INTEGER      NOT NULL
               REFERENCES tasks (task_id) ON DELETE CASCADE,
    user_id    INTEGER      NOT NULL
               REFERENCES users (user_id) ON DELETE RESTRICT,   -- факт трудозатрат не теряется
    work_date  DATE         NOT NULL,
    hours      NUMERIC(3, 1) NOT NULL,
    note       VARCHAR(200),
    created_at TIMESTAMP    NOT NULL DEFAULT now(),

    -- за день по задаче у сотрудника одна запись; повторное списание её изменяет
    CONSTRAINT uq_worklogs_day   UNIQUE (task_id, user_id, work_date),
    CONSTRAINT chk_worklogs_hours CHECK (hours > 0 AND hours <= 24)
);
-- сумма часов сотрудника за день (проверка лимита), RESTRICT при удалении пользователя
CREATE INDEX ix_worklogs_user_day ON worklogs (user_id, work_date);

-- Правила списания. Членство в проекте проверяется на момент списания: если участника
-- потом исключат из проекта, его часы останутся в истории проекта.
-- Суточный лимит: строка сотрудника блокируется (FOR NO KEY UPDATE), поэтому параллельные
-- списания одного сотрудника выполняются по очереди и каждое видит часы предыдущего
-- (как блокировка строки спринта при проверке ёмкости, уровень READ COMMITTED).
-- После завершения задачи её часы не меняются: правило проверяется и при изменении записи.
CREATE FUNCTION worklog_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    t      tasks%ROWTYPE;
    booked numeric;
BEGIN
    SELECT * INTO t FROM tasks WHERE task_id = NEW.task_id;
    IF t.status NOT IN ('in_progress', 'review') THEN
        RAISE EXCEPTION 'Задача % в статусе %: часы списываются только на задачу в работе или на проверке',
                        t.task_id, t.status
            USING ERRCODE = 'PM007';
    END IF;
    IF NOT EXISTS (SELECT FROM project_members
                   WHERE project_id = t.project_id AND user_id = NEW.user_id) THEN
        RAISE EXCEPTION 'Сотрудник % не участвует в проекте задачи %', NEW.user_id, t.task_id
            USING ERRCODE = 'PM007';
    END IF;
    IF NEW.work_date > CURRENT_DATE OR NEW.work_date < t.created_at::date THEN
        RAISE EXCEPTION 'Дата работ % вне периода от создания задачи % до сегодня', NEW.work_date, t.task_id
            USING ERRCODE = 'PM007';
    END IF;

    PERFORM FROM users WHERE user_id = NEW.user_id FOR NO KEY UPDATE;
    SELECT COALESCE(sum(hours), 0) INTO booked
    FROM worklogs
    WHERE user_id = NEW.user_id AND work_date = NEW.work_date AND worklog_id <> NEW.worklog_id;
    IF booked + NEW.hours > 24 THEN
        RAISE EXCEPTION 'Сотрудник % за % уже списал % ч: ещё % ч превысят 24 ч в сутки',
                        NEW.user_id, NEW.work_date, booked, NEW.hours
            USING ERRCODE = 'PM006';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_worklogs_guard BEFORE INSERT OR UPDATE ON worklogs
    FOR EACH ROW EXECUTE FUNCTION worklog_guard();

GRANT SELECT, INSERT, UPDATE, DELETE ON worklogs TO pm_app;
GRANT USAGE ON SEQUENCE worklogs_worklog_id_seq TO pm_app;
