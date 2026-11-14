-- 007. Серверная логика: триггеры бизнес-правил и бизнес-операции.
--
-- Собственные коды ошибок (класс PM) приложение превращает в понятные ответы API:
--   PM001 — недопустимый переход статуса задачи;
--   PM002 — задачу без исполнителя нельзя взять в работу;
--   PM003 — операция недопустима в текущем состоянии спринта;
--   PM004 — превышена ёмкость спринта;
--   PM005 — договор возможен только у проекта с заказчиком.

-- ---------------------------------------------------------------- статусы задач
-- Жизненный цикл: todo → in_progress → review → done;
-- возвраты: in_progress → todo, review → in_progress (замечания), done → in_progress (переоткрытие).
CREATE FUNCTION task_status_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;
    IF (OLD.status, NEW.status) NOT IN (
        ('todo', 'in_progress'), ('in_progress', 'review'), ('review', 'done'),
        ('in_progress', 'todo'), ('review', 'in_progress'), ('done', 'in_progress')
    ) THEN
        RAISE EXCEPTION 'Недопустимый переход статуса задачи %: % → %',
                        OLD.task_id, OLD.status, NEW.status
            USING ERRCODE = 'PM001',
                  HINT = 'Порядок: todo → in_progress → review → done.';
    END IF;
    IF NEW.status = 'in_progress' AND NEW.assignee_id IS NULL THEN
        RAISE EXCEPTION 'Задача % не назначена: взять её в работу нельзя', OLD.task_id
            USING ERRCODE = 'PM002';
    END IF;
    -- момент завершения ставится автоматически и снимается при переоткрытии
    IF NEW.status = 'done' THEN
        NEW.completed_at := COALESCE(NEW.completed_at, now());
    ELSIF OLD.status = 'done' THEN
        NEW.completed_at := NULL;
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_tasks_status_guard BEFORE UPDATE OF status ON tasks
    FOR EACH ROW EXECUTE FUNCTION task_status_guard();

-- История статусов. SECURITY DEFINER: историю пишет только триггер.
CREATE FUNCTION task_status_log() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
    IF TG_OP = 'INSERT' OR NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO task_status_history (task_id, old_status, new_status, changed_at, changed_by)
        VALUES (NEW.task_id,
                CASE WHEN TG_OP = 'UPDATE' THEN OLD.status END,
                NEW.status,
                CASE WHEN TG_OP = 'INSERT' THEN NEW.created_at
                     WHEN NEW.status = 'done' THEN NEW.completed_at
                     ELSE now() END,
                app_user_id());
    END IF;
    RETURN NULL;
END $$;

CREATE TRIGGER trg_tasks_status_log AFTER INSERT OR UPDATE OF status ON tasks
    FOR EACH ROW EXECUTE FUNCTION task_status_log();

-- ---------------------------------------------------------------- ёмкость спринта
-- Сумма оценок задач спринта не превышает его ёмкость. Строка спринта блокируется
-- (FOR UPDATE), поэтому параллельные планирования в один спринт выполняются по очереди,
-- и каждое видит задачи, добавленные предыдущим (уровень изоляции READ COMMITTED).
CREATE FUNCTION sprint_capacity_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    s       sprints%ROWTYPE;
    planned numeric;
BEGIN
    IF NEW.sprint_id IS NULL THEN
        RETURN NEW;
    END IF;
    IF TG_OP = 'UPDATE' AND NEW.sprint_id = OLD.sprint_id
       AND NEW.estimate_hours <= OLD.estimate_hours THEN
        RETURN NEW;                            -- уменьшение оценки ёмкость не нарушает
    END IF;

    SELECT * INTO s FROM sprints WHERE sprint_id = NEW.sprint_id FOR UPDATE;
    IF s.status = 'closed' THEN
        RAISE EXCEPTION 'Спринт % закрыт: планировать в него задачи нельзя', s.sprint_id
            USING ERRCODE = 'PM003';
    END IF;

    SELECT COALESCE(sum(estimate_hours), 0) INTO planned
    FROM tasks
    WHERE sprint_id = NEW.sprint_id AND task_id <> NEW.task_id;

    IF planned + NEW.estimate_hours > s.capacity_hours THEN
        RAISE EXCEPTION 'Ёмкость спринта % превышена: занято % ч из %, задаче % нужно % ч',
                        s.sprint_id, planned, s.capacity_hours, NEW.task_id, NEW.estimate_hours
            USING ERRCODE = 'PM004';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_tasks_sprint_capacity BEFORE INSERT OR UPDATE OF sprint_id, estimate_hours ON tasks
    FOR EACH ROW EXECUTE FUNCTION sprint_capacity_guard();

-- Ёмкость нельзя уменьшить ниже уже запланированного объёма.
CREATE FUNCTION sprint_capacity_shrink_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    planned numeric;
BEGIN
    SELECT COALESCE(sum(estimate_hours), 0) INTO planned
    FROM tasks WHERE sprint_id = NEW.sprint_id;
    IF NEW.capacity_hours < planned THEN
        RAISE EXCEPTION 'Ёмкость спринта % не может быть меньше запланированных % ч',
                        NEW.sprint_id, planned
            USING ERRCODE = 'PM004';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_sprints_capacity BEFORE UPDATE OF capacity_hours ON sprints
    FOR EACH ROW EXECUTE FUNCTION sprint_capacity_shrink_guard();

-- ---------------------------------------------------------------- бизнес-операции
-- Создание проекта: проект, владелец как руководитель, команда и договор — атомарно.
-- p_members: [{"user_id": 3, "role": "developer"}, ...]
-- p_contract: {"number": "Д-2026/030", "signed_on": "2026-11-20", "amount": 900000, "budget_hours": 300}
CREATE FUNCTION create_project(
    p_name        text,
    p_code        text,
    p_owner       integer,
    p_start       date,
    p_end         date    DEFAULT NULL,
    p_customer    integer DEFAULT NULL,
    p_description text    DEFAULT NULL,
    p_members     jsonb   DEFAULT '[]',
    p_contract    jsonb   DEFAULT NULL
) RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    pid integer;
BEGIN
    IF p_contract IS NOT NULL AND p_customer IS NULL THEN
        RAISE EXCEPTION 'Договор возможен только у проекта с заказчиком' USING ERRCODE = 'PM005';
    END IF;

    INSERT INTO projects (name, code, description, owner_id, start_date, end_date, customer_id)
    VALUES (p_name, p_code, p_description, p_owner, p_start, p_end, p_customer)
    RETURNING project_id INTO pid;

    INSERT INTO project_members (project_id, user_id, role, joined_at)
    VALUES (pid, p_owner, 'manager', p_start);

    INSERT INTO project_members (project_id, user_id, role, joined_at)
    SELECT pid, m.user_id, COALESCE(m.role, 'developer'), p_start
    FROM jsonb_to_recordset(p_members) AS m(user_id integer, role text)
    WHERE m.user_id <> p_owner;

    IF p_contract IS NOT NULL THEN
        INSERT INTO contracts (project_id, customer_id, number, signed_on, amount, budget_hours)
        SELECT pid, p_customer, c.number, c.signed_on, c.amount, c.budget_hours
        FROM jsonb_to_record(p_contract)
             AS c(number text, signed_on date, amount numeric, budget_hours numeric);
    END IF;
    RETURN pid;
END $$;

-- Закрытие спринта: активный спринт закрывается, следующий запланированный спринт
-- проекта становится активным, незавершённые задачи переходят в него (если следующего
-- нет — возвращаются в бэклог). Если задачи не помещаются в следующий спринт,
-- операция отменяется целиком. Возвращает число перенесённых задач.
CREATE FUNCTION close_sprint(p_sprint integer) RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    s     sprints%ROWTYPE;
    nxt   integer;
    moved integer;
BEGIN
    SELECT * INTO s FROM sprints WHERE sprint_id = p_sprint FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Спринт % не найден', p_sprint USING ERRCODE = 'no_data_found';
    END IF;
    IF s.status <> 'active' THEN
        RAISE EXCEPTION 'Закрыть можно только активный спринт, спринт % — %', p_sprint, s.status
            USING ERRCODE = 'PM003';
    END IF;

    SELECT sprint_id INTO nxt
    FROM sprints
    WHERE project_id = s.project_id AND status = 'planned' AND start_date > s.start_date
    ORDER BY start_date
    LIMIT 1
    FOR UPDATE;

    UPDATE sprints SET status = 'closed' WHERE sprint_id = p_sprint;
    UPDATE sprints SET status = 'active' WHERE sprint_id = nxt;

    UPDATE tasks SET sprint_id = nxt
    WHERE sprint_id = p_sprint AND status <> 'done';
    GET DIAGNOSTICS moved = ROW_COUNT;
    RETURN moved;
END $$;

-- Диаграмма сгорания спринта: остаток работы (часы незавершённых задач) на конец
-- каждого дня и идеальная линия равномерного сгорания.
CREATE FUNCTION sprint_burndown(p_sprint integer)
RETURNS TABLE (day date, remaining_hours numeric, ideal_hours numeric)
LANGUAGE sql STABLE AS $$
    WITH s AS (
        SELECT start_date, end_date, end_date - start_date AS days
        FROM sprints WHERE sprint_id = p_sprint
    ), t AS (
        SELECT estimate_hours, completed_at::date AS done_on
        FROM tasks WHERE sprint_id = p_sprint
    ), total AS (
        SELECT COALESCE(sum(estimate_hours), 0) AS hours FROM t
    )
    SELECT d::date,
           total.hours - COALESCE((SELECT sum(estimate_hours) FROM t WHERE done_on <= d::date), 0),
           round(total.hours * (1 - (d::date - s.start_date)::numeric / s.days), 1)
    FROM s, total, generate_series(s.start_date, s.end_date, interval '1 day') AS d
    ORDER BY 1
$$;
