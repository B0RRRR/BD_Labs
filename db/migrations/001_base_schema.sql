-- 001. Базовая схема (ЛР № 1): пользователи, проекты, участники, задачи, комментарии.
-- Исходный сценарий с тестовыми данными — Lab1/schema.sql, Lab1/data.sql.

CREATE TABLE users (
    user_id    SERIAL       PRIMARY KEY,
    full_name  VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT chk_users_email CHECK (email LIKE '%_@_%._%')
);

CREATE TABLE projects (
    project_id  SERIAL       PRIMARY KEY,
    name        VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    owner_id    INTEGER      NOT NULL
                REFERENCES users (user_id) ON DELETE RESTRICT,
    status      VARCHAR(20)  NOT NULL DEFAULT 'planned',
    start_date  DATE         NOT NULL,
    end_date    DATE,

    CONSTRAINT chk_projects_status
        CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    CONSTRAINT chk_projects_dates
        CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE project_members (
    project_id INTEGER     NOT NULL
               REFERENCES projects (project_id) ON DELETE CASCADE,
    user_id    INTEGER     NOT NULL
               REFERENCES users (user_id) ON DELETE CASCADE,
    role       VARCHAR(20) NOT NULL DEFAULT 'developer',
    joined_at  DATE        NOT NULL DEFAULT CURRENT_DATE,

    PRIMARY KEY (project_id, user_id),
    CONSTRAINT chk_members_role
        CHECK (role IN ('manager', 'developer', 'tester', 'analyst'))
);

CREATE TABLE tasks (
    task_id     SERIAL       PRIMARY KEY,
    project_id  INTEGER      NOT NULL
                REFERENCES projects (project_id) ON DELETE CASCADE,
    assignee_id INTEGER
                REFERENCES users (user_id) ON DELETE SET NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    status      VARCHAR(20)  NOT NULL DEFAULT 'todo',
    priority    SMALLINT     NOT NULL DEFAULT 3,
    created_at  TIMESTAMP    NOT NULL DEFAULT now(),
    due_date    DATE,

    CONSTRAINT uq_tasks_project_title UNIQUE (project_id, title),
    CONSTRAINT chk_tasks_status
        CHECK (status IN ('todo', 'in_progress', 'review', 'done')),
    CONSTRAINT chk_tasks_priority
        CHECK (priority BETWEEN 1 AND 5)
);

CREATE TABLE comments (
    comment_id SERIAL    PRIMARY KEY,
    task_id    INTEGER   NOT NULL
               REFERENCES tasks (task_id) ON DELETE CASCADE,
    author_id  INTEGER   NOT NULL
               REFERENCES users (user_id) ON DELETE RESTRICT,
    body       TEXT      NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT chk_comments_body CHECK (length(trim(body)) > 0)
);
