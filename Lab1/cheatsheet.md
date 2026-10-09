# Шпаргалка к защите ЛР №1 (вариант 11 — управление проектами)

## 0. Как показать работу

```bash
createdb project_db                        # создать БД
psql -d project_db -f schema.sql           # структура
psql -d project_db -f data.sql             # данные
psql -d project_db -f constraints_test.sql # все запросы падают с ERROR — так и надо
psql -d project_db -f migration.sql        # изменение структуры
```

Полезное внутри `psql`:

| Команда | Что делает |
|---|---|
| `\dt` | список таблиц |
| `\d tasks` | структура таблицы: столбцы, типы, ограничения, внешние ключи |
| `\i schema.sql` | выполнить файл |
| `\x` | вертикальный вывод (удобно для широких строк) |
| `\q` | выход |

Узнать имена всех ограничений (нужно для `DROP CONSTRAINT`):

```sql
SELECT conrelid::regclass AS table_name, conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY 1, 2;
```

Автоматические имена PostgreSQL строит так: `таблица_столбец_key` (UNIQUE),
`таблица_столбец_fkey` (FK), `таблица_pkey` (PK). Например `users_email_key`,
`tasks_assignee_id_fkey`, `project_members_pkey`.

---

## 1. Рассказ на 30 секунд

> 5 таблиц: `users`, `projects`, `project_members`, `tasks`, `comments`.
> Пользователь владеет проектами (1:N) и участвует в проектах с ролью (M:N через
> `project_members`). В проекте есть задачи (1:N), у задачи — необязательный исполнитель и
> комментарии. Модель в 3НФ: в каждой таблице хранятся только свои данные, на чужие —
> ссылка по id.

Требования задания → где выполнены:

| Требование | Где |
|---|---|
| ≥ 5 таблиц | 5 таблиц |
| ≥ 2 UNIQUE | `users.email`, `projects.name`, `tasks(project_id, title)` |
| ≥ 3 CHECK | 7 штук: email, статус проекта, даты проекта, роль, статус задачи, приоритет, текст комментария |
| ≥ 1 составное | `PRIMARY KEY (project_id, user_id)`, `UNIQUE (project_id, title)`, `CHECK (end_date >= start_date)` |
| NOT NULL | на всех обязательных полях |
| ≥ 5 некорректных запросов | 12 в `constraints_test.sql` |

---

## 2. Разбор конструкций из кода

| Конструкция | Объяснение |
|---|---|
| `SERIAL` | целое число с автоинкрементом. Под капотом: `INTEGER` + последовательность (sequence) + `DEFAULT nextval(...)` |
| `PRIMARY KEY` | = `UNIQUE` + `NOT NULL`, в таблице только один. Автоматически создаётся индекс |
| `REFERENCES users (user_id)` | внешний ключ: значение должно существовать в `users.user_id` (или быть NULL) |
| `VARCHAR(100)` | строка до 100 символов; длиннее — ошибка |
| `TEXT` | строка любой длины |
| `NUMERIC(5,1)` | точное число: всего 5 цифр, из них 1 после запятой (до 9999.9) |
| `SMALLINT` | целое 2 байта (−32768..32767) |
| `TIMESTAMP` / `DATE` | дата+время / только дата |
| `DEFAULT now()` | если значение не указано в INSERT — подставится текущее время |
| `CONSTRAINT имя CHECK (...)` | именованное ограничение; имя видно в тексте ошибки и нужно для `DROP CONSTRAINT` |
| `email LIKE '%_@_%._%'` | `%` — любое кол-во символов, `_` — ровно один символ. Значит: хотя бы 1 символ, `@`, хотя бы 1 символ, точка, хотя бы 1 символ |
| `CHECK (end_date IS NULL OR end_date >= start_date)` | дата окончания может быть неизвестна; если известна — не раньше начала |
| `length(trim(body)) > 0` | `trim` убирает пробелы по краям — комментарий из одних пробелов запрещён |
| `DROP TABLE IF EXISTS ... CASCADE` | удалить, если есть (без ошибки, если нет); CASCADE удаляет и внешние ключи, ссылающиеся на таблицу |
| `BEGIN; ... ROLLBACK;` | транзакция, изменения отменяются — так в `constraints_test.sql` показаны CASCADE/SET NULL без порчи данных |
| `BEGIN; ... COMMIT;` в миграции | если хоть одна команда упадёт, не применится ничего |

---

## 3. Вопросы по теории

**Что такое 1НФ, 2НФ, 3НФ?**
- **1НФ** — значения атомарны (нет списков в ячейке), нет повторяющихся групп, есть ключ.
- **2НФ** — 1НФ + каждый неключевой атрибут зависит от *всего* составного ключа, а не от его части.
- **3НФ** — 2НФ + нет транзитивных зависимостей: неключевой атрибут не зависит от другого неключевого.
- Пример нарушения 3НФ: хранить в `tasks` столбец `project_name` (`task_id → project_id → project_name`).
- Пример нарушения 2НФ: хранить в `project_members` столбец `user_email` — зависит только от `user_id`, части ключа.
- Пример нарушения 1НФ: `projects.members = 'Иванов, Петров'`.

**Чем PRIMARY KEY отличается от UNIQUE?** PK — один на таблицу, NOT NULL, на него ссылаются FK.
UNIQUE может быть несколько, и NULL в UNIQUE-столбце допускается (причём несколько NULL — тоже).

**Правила ON DELETE:**
- `CASCADE` — удалить зависимые строки вместе с родителем;
- `SET NULL` — в зависимых строках поставить NULL (столбец должен допускать NULL!);
- `RESTRICT` / `NO ACTION` (по умолчанию) — запретить удаление, пока есть ссылки.
  Разница: `RESTRICT` проверяет сразу, `NO ACTION` — в конце оператора (можно отложить через `DEFERRABLE`).
- `SET DEFAULT` — поставить значение по умолчанию.

**Почему у `assignee_id` SET NULL, а не CASCADE?** Если уволили сотрудника, задача не должна
исчезнуть — её просто переназначат.

**Почему у `comments.author_id` RESTRICT?** Чтобы случайно не стереть историю обсуждений.
Сначала нужно явно решить, что делать с комментариями.

**Почему `assignee_id` без NOT NULL?** Задача может быть ещё никому не назначена.

**Что будет, если в CHECK попадёт NULL?** CHECK пропускает строку, если условие TRUE **или NULL**.
Поэтому `CHECK (priority BETWEEN 1 AND 5)` пропустит NULL — от NULL защищает только `NOT NULL`.

**Что такое составное ограничение?** Ограничение на несколько столбцов сразу:
`PRIMARY KEY (project_id, user_id)`, `UNIQUE (project_id, title)`, `CHECK (end_date >= start_date)`.

**Зачем таблица `project_members`?** Связь M:N в реляционной модели реализуется только через
промежуточную таблицу. Плюс у связи есть свои атрибуты — `role`, `joined_at`.

**Почему суррогатный ключ (`id`), а не email?** Email может измениться — тогда пришлось бы
обновлять все ссылки. `id` никогда не меняется и короче.

**SERIAL vs IDENTITY?** `GENERATED ALWAYS AS IDENTITY` — стандарт SQL, более новый способ.
`SERIAL` — классический способ PostgreSQL, работает так же для наших целей.

**Чем DDL отличается от DML?** DDL — структура (`CREATE`, `ALTER`, `DROP`). DML — данные
(`INSERT`, `UPDATE`, `DELETE`, `SELECT`).

### PRIMARY KEY и FOREIGN KEY — когда что

| | **PRIMARY KEY** | **FOREIGN KEY** |
|---|---|---|
| Отвечает на вопрос | «как отличить эту строку от других **в этой** таблице?» | «к какой строке **другой** таблицы относится эта строка?» |
| Сколько в таблице | ровно один, всегда | сколько нужно: 0, 1, 2… |
| Значения | уникальные, не NULL | могут повторяться; NULL можно, если нет NOT NULL |
| Синтаксис | `PRIMARY KEY` | `REFERENCES таблица (столбец)` |

Пример: в `tasks` `task_id` — PK (номер самой задачи), `project_id` — FK (номер проекта, к
которому она относится; у многих задач он одинаковый).

**Какой PK выбрать:**

| Таблица | PK | Пример |
|---|---|---|
| Сущность | `xxx_id SERIAL PRIMARY KEY` | `users.user_id`, `projects.project_id` |
| Таблица связи M:N | составной из двух FK — заодно запрещает дубли | `PRIMARY KEY (project_id, user_id)` |
| Справочник с кодом | сам код | `code VARCHAR(20) PRIMARY KEY` |

Email / название — уникальны, но это `UNIQUE`, а не PK: PK один, UNIQUE — сколько угодно.

**Где ставить FK — по формулировке требования:**

| Фраза | Связь | Куда FK |
|---|---|---|
| «задача относится к проекту», «у проекта много задач» | 1:N | на стороне «много»: `tasks.project_id` |
| «много X у Y **и** много Y у X» | M:N | новая таблица связи с **двумя** FK |
| «у сотрудника один профиль» | 1:1 | FK + `UNIQUE` на нём |
| «задача может быть подзадачей другой задачи» | на себя | `parent_task_id REFERENCES tasks` |
| «обязательно есть» / «может быть» | — | FK `NOT NULL` / без `NOT NULL` |
| «удаляются вместе» / «ссылка очищается» / «удалить нельзя» | — | `CASCADE` / `SET NULL` / `RESTRICT` |

**Частые ошибки:**
1. Ссылка на несуществующее имя: `REFERENCES users (id)` вместо `users (user_id)`.
2. FK типа `SERIAL` — неверно. FK хранит **уже существующий** номер → `INTEGER`.
3. FK можно направить только на PK или `UNIQUE`-столбец.
4. Таблицу, на которую ссылаются, создают **раньше** (`meetings` → потом `users_on_meetings`).
5. Столбец может быть одновременно FK и частью PK — это норма для таблицы связи.

**Быстрый алгоритм на защите:**
1. Что отличает одну строку от другой? → PK.
2. Столбец `..._id` — **мой** номер или **чужой**? Мой → PK, чужой → FK.
3. Сколько B у одного A и сколько A у одного B? «много–один» → FK на стороне «много»;
   «много–много» → таблица связи.

**`CREATE TABLE` vs `ALTER TABLE`:**

| | `CREATE TABLE t ( ... );` | `ALTER TABLE t ...;` |
|---|---|---|
| Когда | таблицы ещё нет | таблица уже есть |
| Скобки после имени | да | **нет** |
| Столбец | `имя ТИП ...` | `ADD COLUMN имя ТИП ...` |
| Ограничение | `CONSTRAINT имя ...` | `ADD CONSTRAINT имя ...` |

---

## 4. Если преподаватель просит изменить условия

### Алгоритм (говорить вслух)

1. Понять, что меняется: новый атрибут? новая сущность? тип связи? ограничение?
2. Пересоздавать БД нельзя → только `ALTER TABLE` / `CREATE TABLE`, всё в `BEGIN ... COMMIT`.
3. Если новое ограничение противоречит **существующим данным** — сначала `UPDATE`
   данных, потом добавить ограничение (иначе PostgreSQL выдаст ошибку).
4. Проверить: `\d таблица` + `SELECT` + запрос, который теперь должен падать.

Все рецепты ниже проверены на этой БД. Готовый пример полной миграции — `migration.sql`.

---

### 4.1. Добавить атрибут (столбец)

«У проекта должен быть бюджет», «у пользователя — телефон»:

```sql
ALTER TABLE projects ADD COLUMN budget NUMERIC(12, 2) CHECK (budget >= 0);
ALTER TABLE users    ADD COLUMN phone  VARCHAR(20) UNIQUE;
```

Старые строки получат NULL — это нормально, раз столбец необязательный.

### 4.2. Добавить ОБЯЗАТЕЛЬНЫЙ столбец (NOT NULL) в таблицу с данными

Вариант 1 — есть разумное значение по умолчанию:
```sql
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
```

Вариант 2 — значение надо вычислить (в 3 шага):
```sql
-- «У задачи должен быть автор (кто её создал)»
ALTER TABLE tasks ADD COLUMN created_by INTEGER REFERENCES users (user_id);
UPDATE tasks t SET created_by = p.owner_id          -- старым задачам — владельца проекта
FROM projects p WHERE p.project_id = t.project_id;
ALTER TABLE tasks ALTER COLUMN created_by SET NOT NULL;
```

### 4.3. Изменить список допустимых значений (CHECK)

«У проекта добавляется статус on_hold». CHECK нельзя изменить — только удалить и создать заново:
```sql
ALTER TABLE projects DROP CONSTRAINT chk_projects_status;
ALTER TABLE projects ADD CONSTRAINT chk_projects_status
    CHECK (status IN ('planned', 'active', 'on_hold', 'completed', 'cancelled'));
```

### 4.4. Добавить ограничение, которому старые данные не соответствуют

«Срок у задачи теперь обязателен»:
```sql
-- сразу SET NOT NULL упадёт: у задачи 5 due_date = NULL
UPDATE tasks SET due_date = CURRENT_DATE + 30 WHERE due_date IS NULL;
ALTER TABLE tasks ALTER COLUMN due_date SET NOT NULL;
```
Альтернатива для CHECK/FK — `ADD CONSTRAINT ... NOT VALID`: проверяет только новые строки.

### 4.5. Переименовать / изменить тип

```sql
ALTER TABLE tasks    RENAME COLUMN due_date TO deadline;
ALTER TABLE comments RENAME TO task_comments;
ALTER TABLE users    ALTER COLUMN full_name TYPE VARCHAR(200);
ALTER TABLE tasks    ALTER COLUMN priority  TYPE INTEGER;
-- если тип несовместим: ... TYPE INTEGER USING столбец::INTEGER
```

### 4.6. Изменить / убрать значение по умолчанию

```sql
ALTER TABLE tasks ALTER COLUMN priority SET DEFAULT 2;
ALTER TABLE tasks ALTER COLUMN priority DROP DEFAULT;
```

### 4.7. Изменить правило ON DELETE

«При удалении пользователя его комментарии тоже удаляются». FK тоже нельзя изменить — только пересоздать:
```sql
ALTER TABLE comments DROP CONSTRAINT comments_author_id_fkey;
ALTER TABLE comments ADD CONSTRAINT comments_author_id_fkey
    FOREIGN KEY (author_id) REFERENCES users (user_id) ON DELETE CASCADE;
```

### 4.8. Изменить UNIQUE

«Названия проектов уникальны только в пределах одного владельца»:
```sql
ALTER TABLE projects DROP CONSTRAINT projects_name_key;
ALTER TABLE projects ADD CONSTRAINT uq_projects_owner_name UNIQUE (owner_id, name);
```

### 4.9. Новая сущность со связью M:N — теги задач

```sql
CREATE TABLE tags (
    tag_id SERIAL      PRIMARY KEY,
    name   VARCHAR(50) NOT NULL UNIQUE
);
CREATE TABLE task_tags (
    task_id INTEGER NOT NULL REFERENCES tasks (task_id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tags (tag_id)  ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);
INSERT INTO tags (name) VALUES ('frontend'), ('backend'), ('bug');
INSERT INTO task_tags VALUES (2, 1), (3, 2);
```

### 4.10. Связь 1:N превращается в M:N — «у задачи может быть несколько исполнителей»

Главное — **перенести существующие данные**, потом удалить старый столбец:
```sql
CREATE TABLE task_assignees (
    task_id INTEGER NOT NULL REFERENCES tasks (task_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, user_id)
);
INSERT INTO task_assignees (task_id, user_id)
SELECT task_id, assignee_id FROM tasks WHERE assignee_id IS NOT NULL;
ALTER TABLE tasks DROP COLUMN assignee_id;
```

### 4.11. Вынести статус в справочник (отдельную таблицу)

«Статусы задач должны храниться в отдельной таблице»:
```sql
CREATE TABLE task_statuses (
    status_id SERIAL      PRIMARY KEY,
    name      VARCHAR(20) NOT NULL UNIQUE
);
INSERT INTO task_statuses (name) VALUES ('todo'), ('in_progress'), ('review'), ('done');

ALTER TABLE tasks ADD COLUMN status_id INTEGER REFERENCES task_statuses (status_id);
UPDATE tasks t SET status_id = s.status_id
FROM task_statuses s WHERE s.name = t.status;          -- перенос данных
ALTER TABLE tasks ALTER COLUMN status_id SET NOT NULL;
ALTER TABLE tasks DROP COLUMN status;                   -- CHECK удалится вместе со столбцом
```

### 4.12. Подзадачи (связь таблицы с самой собой)

```sql
ALTER TABLE tasks
    ADD COLUMN parent_task_id INTEGER REFERENCES tasks (task_id) ON DELETE CASCADE;
ALTER TABLE tasks
    ADD CONSTRAINT chk_tasks_not_self_parent CHECK (parent_task_id <> task_id);
UPDATE tasks SET parent_task_id = 2 WHERE task_id = 3;   -- задача 3 — подзадача задачи 2
```

### 4.13. «Исполнитель задачи должен быть участником её проекта» (составной FK)

```sql
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_assignee_member
    FOREIGN KEY (project_id, assignee_id)
    REFERENCES project_members (project_id, user_id);
-- теперь назначить на задачу проекта 1 пользователя 2 (не участник) — ошибка
```
Если `assignee_id` = NULL, составной FK не проверяется — неназначенные задачи разрешены.

### 4.14. Учёт времени / трудозатрат

Полностью сделано в `migration.sql`: столбец `tasks.estimated_hours` + таблица `time_logs`
с `CHECK (hours > 0 AND hours <= 24)` и `UNIQUE (task_id, user_id, work_date)`.

### 4.15. Удалить столбец / таблицу

```sql
ALTER TABLE tasks DROP COLUMN description;
DROP TABLE comments;
```
(Лучше уточнить у преподавателя — это теряет данные.)

---

## 5. Шаблон migration.sql под новое требование

```sql
-- Требование: <записать формулировку преподавателя>
BEGIN;

-- 1. Структура: ALTER TABLE ... ADD COLUMN / CREATE TABLE ...
-- 2. Перенос/заполнение существующих данных: UPDATE / INSERT ... SELECT
-- 3. Ограничения: SET NOT NULL / ADD CONSTRAINT ...
-- 4. Удаление старого (если нужно): DROP COLUMN ...

COMMIT;

-- Проверка
\d имя_таблицы
SELECT ... ;
-- запрос, который теперь должен падать
```

Запишите формулировку преподавателя и определите тип изменения:

Формулировка звучит как…	Это значит	Что делать (рецепт в cheatsheet.md)
«у X должно быть ещё поле Y»	новый атрибут	ADD COLUMN (4.1, 4.2)
«появляются отделы, теги, спринты…»	новая сущность	CREATE TABLE + FK (4.9)
«у задачи может быть несколько исполнителей»	связь 1:N → M:N	таблица связи + перенос данных (4.10)
«добавить статус / роль»	изменился CHECK	DROP CONSTRAINT + ADD CONSTRAINT (4.3)
«поле теперь обязательное»	NOT NULL	заполнить пустые строки, потом SET NOT NULL (4.4)
«при удалении X удалять / не удалять Y»	ON DELETE	пересоздать FK (4.7)
«уникально в пределах…»	UNIQUE	DROP / ADD CONSTRAINT (4.8)
«статусы хранить в отдельной таблице»	справочник	4.11
«у задачи бывают подзадачи»	связь таблицы с самой собой	4.12