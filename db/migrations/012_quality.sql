-- 012. Система оценивания качества: требования, критерии качества, испытания,
-- прогоны испытаний и их результаты. Отдельная схема quality — «база данных качества»:
-- по ней запросом проверяется полнота прослеживаемости «требование → испытание»
-- и соответствие программы требованиям.

CREATE SCHEMA quality;

-- Требование к программе: назначения (ТН), функциональное (ФТ),
-- функционально-техническое (ФТТ), техническое (ТТ).
CREATE TABLE quality.requirements (
    req_code VARCHAR(10) PRIMARY KEY,
    kind     VARCHAR(3)  NOT NULL,
    title    TEXT        NOT NULL,

    CONSTRAINT chk_req_kind CHECK (kind IN ('ТН', 'ФТ', 'ФТТ', 'ТТ')),
    CONSTRAINT chk_req_code CHECK (req_code ~ ('^' || kind || '-[0-9]+$'))
);

-- Критерий качества по ГОСТ Р ИСО/МЭК 25010: метрика и требуемое значение.
-- direction: '>=' — «больше — лучше», '<=' — «меньше — лучше».
CREATE TABLE quality.criteria (
    crit_code      VARCHAR(5)  PRIMARY KEY,
    characteristic TEXT        NOT NULL,
    metric         TEXT        NOT NULL,
    unit           VARCHAR(10) NOT NULL,
    required_value NUMERIC     NOT NULL,
    direction      VARCHAR(2)  NOT NULL,

    CONSTRAINT chk_crit_code      CHECK (crit_code ~ '^К[0-9]+$'),
    CONSTRAINT chk_crit_direction CHECK (direction IN ('>=', '<='))
);

-- Испытание программы методики испытаний: сценарий и ожидаемый результат.
CREATE TABLE quality.tests (
    test_code VARCHAR(5) PRIMARY KEY,
    title     TEXT       NOT NULL,
    scenario  TEXT       NOT NULL,
    expected  TEXT       NOT NULL,

    CONSTRAINT chk_test_code CHECK (test_code ~ '^И[0-9]+$')
);

-- Требование проверяется испытаниями (M : N).
CREATE TABLE quality.requirement_tests (
    req_code  VARCHAR(10) NOT NULL REFERENCES quality.requirements ON DELETE CASCADE ON UPDATE CASCADE,
    test_code VARCHAR(5)  NOT NULL REFERENCES quality.tests ON DELETE RESTRICT ON UPDATE CASCADE,
    PRIMARY KEY (req_code, test_code)
);

-- Требование оценивается критериями качества (M : N).
CREATE TABLE quality.requirement_criteria (
    req_code  VARCHAR(10) NOT NULL REFERENCES quality.requirements ON DELETE CASCADE ON UPDATE CASCADE,
    crit_code VARCHAR(5)  NOT NULL REFERENCES quality.criteria ON DELETE RESTRICT ON UPDATE CASCADE,
    PRIMARY KEY (req_code, crit_code)
);

-- Прогон испытаний и условия, при которых он выполнен (состав обстоятельств).
CREATE TABLE quality.runs (
    run_id      SERIAL    PRIMARY KEY,
    run_at      TIMESTAMP NOT NULL DEFAULT now(),
    environment TEXT      NOT NULL,
    db_version  TEXT      NOT NULL          -- последняя применённая миграция
);

-- Результат испытания в прогоне (M : N «прогон — испытание» с атрибутами).
CREATE TABLE quality.test_results (
    run_id    INTEGER    NOT NULL REFERENCES quality.runs ON DELETE CASCADE,
    test_code VARCHAR(5) NOT NULL REFERENCES quality.tests ON DELETE RESTRICT ON UPDATE CASCADE,
    actual    TEXT       NOT NULL,
    passed    BOOLEAN    NOT NULL,
    PRIMARY KEY (run_id, test_code)
);

-- Измеренное значение критерия в прогоне (M : N «прогон — критерий» с атрибутом).
-- Выполнен ли критерий, не хранится: это вычисляется из значения (представление v_criteria).
CREATE TABLE quality.criterion_values (
    run_id    INTEGER    NOT NULL REFERENCES quality.runs ON DELETE CASCADE,
    crit_code VARCHAR(5) NOT NULL REFERENCES quality.criteria ON DELETE RESTRICT ON UPDATE CASCADE,
    value     NUMERIC    NOT NULL,
    PRIMARY KEY (run_id, crit_code)
);

-- Выполнение критериев в каждом прогоне.
CREATE VIEW quality.v_criteria AS
SELECT v.run_id, c.crit_code, c.characteristic, c.metric, c.unit, c.required_value, c.direction, v.value,
       CASE c.direction WHEN '>=' THEN v.value >= c.required_value
                        ELSE v.value <= c.required_value END AS met
FROM quality.criteria c
JOIN quality.criterion_values v ON v.crit_code = c.crit_code;

-- Прослеживаемость требований и их выполнение в последнем прогоне:
-- covered — у требования есть испытание или критерий;
-- satisfied — требование покрыто, все его испытания пройдены и все критерии выполнены.
CREATE VIEW quality.v_requirements AS
WITH last_run AS (
    SELECT max(run_id) AS run_id FROM quality.runs
), coverage AS (
    SELECT r.req_code,
           (SELECT string_agg(t.test_code, ', ' ORDER BY substring(t.test_code FROM 2)::int)
            FROM quality.requirement_tests t WHERE t.req_code = r.req_code)     AS tests,
           (SELECT string_agg(k.crit_code, ', ' ORDER BY substring(k.crit_code FROM 2)::int)
            FROM quality.requirement_criteria k WHERE k.req_code = r.req_code)  AS criteria,
           (SELECT count(*) FROM quality.requirement_tests t
            LEFT JOIN quality.test_results tr
                   ON tr.test_code = t.test_code AND tr.run_id = (SELECT run_id FROM last_run)
            WHERE t.req_code = r.req_code AND tr.passed IS NOT TRUE)            AS failed_tests,
           (SELECT count(*) FROM quality.requirement_criteria k
            LEFT JOIN quality.v_criteria vc
                   ON vc.crit_code = k.crit_code AND vc.run_id = (SELECT run_id FROM last_run)
            WHERE k.req_code = r.req_code AND vc.met IS NOT TRUE)               AS failed_criteria
    FROM quality.requirements r
)
SELECT r.req_code, r.kind, r.title, c.tests, c.criteria,
       (c.tests IS NOT NULL OR c.criteria IS NOT NULL)                          AS covered,
       (c.tests IS NOT NULL OR c.criteria IS NOT NULL)
         AND c.failed_tests = 0 AND c.failed_criteria = 0                       AS satisfied
FROM quality.requirements r
JOIN coverage c ON c.req_code = r.req_code;

-- Итог прогона: прогон принят, если выполнены все испытания и измерены и выполнены все критерии.
CREATE VIEW quality.v_runs AS
SELECT r.run_id, r.run_at, r.db_version,
       count(DISTINCT tr.test_code)                                    AS tests_run,
       count(DISTINCT tr.test_code) FILTER (WHERE tr.passed)           AS tests_passed,
       count(DISTINCT vc.crit_code)                                    AS criteria_measured,
       count(DISTINCT vc.crit_code) FILTER (WHERE vc.met)              AS criteria_met,
       count(DISTINCT tr.test_code) FILTER (WHERE tr.passed) = (SELECT count(*) FROM quality.tests)
         AND count(DISTINCT vc.crit_code) FILTER (WHERE vc.met) = (SELECT count(*) FROM quality.criteria)
                                                                       AS accepted
FROM quality.runs r
LEFT JOIN quality.test_results tr ON tr.run_id = r.run_id
LEFT JOIN quality.v_criteria vc   ON vc.run_id = r.run_id
GROUP BY r.run_id;

-- Роль приложения читает результаты оценки качества, но не меняет их.
GRANT USAGE ON SCHEMA quality TO pm_app;
GRANT SELECT ON ALL TABLES IN SCHEMA quality TO pm_app;
