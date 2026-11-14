-- 005. Спринты, договоры с заказчиками, история статусов задач.
-- Миграция меняет структуру заполненной базы и сохраняет данные:
-- существующим проектам и задачам назначаются спринты, договоры и начальная история.

CREATE EXTENSION IF NOT EXISTS btree_gist;   -- для ограничения EXCLUDE по (проект, период)

-- ---------------------------------------------------------------- спринты
-- Спринт — двухнедельная итерация проекта с ёмкостью в часах.
-- Периоды спринтов одного проекта не пересекаются, активный спринт у проекта один.
CREATE TABLE sprints (
    sprint_id      SERIAL       PRIMARY KEY,
    project_id     INTEGER      NOT NULL
                   REFERENCES projects (project_id) ON DELETE CASCADE,
    number         SMALLINT     NOT NULL,
    goal           VARCHAR(200),
    start_date     DATE         NOT NULL,
    end_date       DATE         NOT NULL,
    capacity_hours NUMERIC(6, 1) NOT NULL,
    status         VARCHAR(10)  NOT NULL DEFAULT 'planned',

    CONSTRAINT uq_sprints_number  UNIQUE (project_id, number),
    CONSTRAINT uq_sprints_project UNIQUE (sprint_id, project_id),   -- цель составного FK из tasks
    CONSTRAINT chk_sprints_number   CHECK (number > 0),
    CONSTRAINT chk_sprints_dates    CHECK (end_date > start_date),
    CONSTRAINT chk_sprints_capacity CHECK (capacity_hours > 0),
    CONSTRAINT chk_sprints_status   CHECK (status IN ('planned', 'active', 'closed')),
    CONSTRAINT excl_sprints_overlap EXCLUDE USING gist
        (project_id WITH =, daterange(start_date, end_date, '[]') WITH &&)
);
CREATE UNIQUE INDEX uq_sprints_one_active ON sprints (project_id) WHERE status = 'active';

-- Задача может входить в спринт только своего проекта и только оценённой.
ALTER TABLE tasks ADD COLUMN sprint_id INTEGER;
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_sprint
    FOREIGN KEY (sprint_id, project_id) REFERENCES sprints (sprint_id, project_id)
    ON DELETE SET NULL (sprint_id);
ALTER TABLE tasks ADD CONSTRAINT chk_tasks_sprint_estimated
    CHECK (sprint_id IS NULL OR estimate_hours IS NOT NULL);

-- Исполнитель задачи — участник её проекта. Прежний FK на users заменяется составным
-- FK на project_members: при исключении участника его задачи становятся неназначенными.
ALTER TABLE tasks DROP CONSTRAINT tasks_assignee_id_fkey;
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assignee_member
    FOREIGN KEY (project_id, assignee_id) REFERENCES project_members (project_id, user_id)
    ON DELETE SET NULL (assignee_id);

-- ---------------------------------------------------------------- договоры
-- Связь 1:1: у внешнего проекта не более одного договора, первичный ключ договора —
-- ключ проекта. customer_id дублирует projects.customer_id намеренно: составной FK
-- гарантирует, что договор заключён с заказчиком проекта. При смене заказчика
-- проекта он меняется и в договоре (ON UPDATE CASCADE), а сделать проект с договором
-- внутренним нельзя (NOT NULL). Проект с договором удалить нельзя (RESTRICT).
ALTER TABLE projects ADD CONSTRAINT uq_projects_customer UNIQUE (project_id, customer_id);

CREATE TABLE contracts (
    project_id   INTEGER       PRIMARY KEY,
    customer_id  INTEGER       NOT NULL,
    number       VARCHAR(30)   NOT NULL UNIQUE,
    signed_on    DATE          NOT NULL,
    amount       NUMERIC(12, 2) NOT NULL,
    budget_hours NUMERIC(7, 1) NOT NULL,

    CONSTRAINT fk_contracts_project FOREIGN KEY (project_id, customer_id)
        REFERENCES projects (project_id, customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_contracts_amount CHECK (amount >= 0),
    CONSTRAINT chk_contracts_budget CHECK (budget_hours > 0)
);

-- ---------------------------------------------------------------- история статусов
-- Каждая смена статуса задачи; заполняется триггером (миграция 007).
CREATE TABLE task_status_history (
    history_id BIGSERIAL   PRIMARY KEY,
    task_id    INTEGER     NOT NULL REFERENCES tasks (task_id) ON DELETE CASCADE,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP   NOT NULL DEFAULT now(),
    changed_by INTEGER     REFERENCES users (user_id) ON DELETE SET NULL,

    CONSTRAINT chk_history_status CHECK (
        new_status IN ('todo', 'in_progress', 'review', 'done')
        AND (old_status IS NULL OR old_status IN ('todo', 'in_progress', 'review', 'done'))),
    CONSTRAINT chk_history_change CHECK (old_status IS DISTINCT FROM new_status)
);

-- ---------------------------------------------------------------- перенос данных
-- Спринты введены с 9 ноября 2026 г.: у каждого активного проекта текущий спринт 1
-- и запланированный спринт 2. Задачи «в работе» и «на проверке» входят в спринт 1.
INSERT INTO sprints (project_id, number, goal, start_date, end_date, capacity_hours, status)
SELECT p.project_id, s.number, s.goal, s.start_date, s.end_date, 80, s.status
FROM projects p
CROSS JOIN (VALUES
    (1, 'Завершить начатые задачи', DATE '2026-11-09', DATE '2026-11-22', 'active'),
    (2, NULL,                       DATE '2026-11-23', DATE '2026-12-06', 'planned')
) AS s(number, goal, start_date, end_date, status)
WHERE p.status = 'active'
ORDER BY p.project_id, s.number;

UPDATE tasks t
SET sprint_id = s.sprint_id
FROM sprints s
WHERE s.project_id = t.project_id AND s.status = 'active'
  AND t.status IN ('in_progress', 'review');

-- Договоры внешних проектов (ищем проект по коду).
INSERT INTO contracts (project_id, customer_id, number, signed_on, amount, budget_hours)
SELECT p.project_id, p.customer_id, v.number, v.signed_on::date, v.amount::numeric, v.budget_hours::numeric
FROM (VALUES
    ('COR',  'Д-2026/003', '2026-02-16',  '450000.00', '160'),
    ('SHOP', 'Д-2026/009', '2026-06-18', '2100000.00', '700'),
    ('MOB',  'Д-2026/014', '2026-08-20', '1800000.00', '600'),
    ('CRM',  'Д-2026/021', '2026-10-15', '2400000.00', '800'),
    ('BOT',  'Д-2026/025', '2026-11-10',  '600000.00', '240')
) AS v(code, number, signed_on, amount, budget_hours)
JOIN projects p ON p.code = v.code
WHERE p.customer_id IS NOT NULL;

-- История ведётся с момента миграции: для каждой задачи записывается состояние,
-- в котором она находилась (более ранние переходы неизвестны).
INSERT INTO task_status_history (task_id, old_status, new_status, changed_at)
SELECT task_id, NULL, status, COALESCE(completed_at, created_at)
FROM tasks;
