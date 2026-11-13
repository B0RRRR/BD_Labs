-- =====================================================================
-- migration.sql — «Учёт техники компании»
--
-- Требования заказчика (таблицы и связи выделить самостоятельно):
--
-- Компания покупает технику: ноутбуки, мониторы и телефоны.
--
-- * У каждого устройства есть инвентарный номер и серийный номер — оба
--   обязательны и не повторяются. Известны дата покупки и цена (цена не
--   может быть отрицательной).
-- * Каждое устройство — конкретная модель (например, «ThinkPad T14»).
--   Модель выпускает производитель; у производителя много моделей.
--   У разных производителей названия моделей могут совпадать, у одного — нет.
--   Тип (ноутбук / монитор / телефон) определяется моделью.
-- * У производителя известны название (не повторяется) и страна
--   (может быть неизвестна).
-- * Устройство может быть выдано сотруднику или лежать на складе.
--   За сотрудником может числиться несколько устройств (ноутбук + монитор).
--   Если устройство выдано — обязательно известна дата выдачи; если оно
--   на складе — даты выдачи нет.
-- * На устройство может быть оформлена гарантия — не более одной на
--   устройство: номер договора и дата окончания (обязательны).
-- * На устройства устанавливаются программы. Одна программа стоит на многих
--   устройствах, на устройстве много программ. Для установки хранится дата
--   (по умолчанию — сегодня) и лицензионный ключ (может отсутствовать —
--   у бесплатных программ; если есть — не повторяется).
--
-- Правила удаления:
-- * нельзя удалить производителя, у которого есть модели;
-- * нельзя удалить модель, если есть устройства этой модели;
-- * нельзя удалить сотрудника, за которым числится техника;
-- * нельзя удалить программу, которая где-то установлена;
-- * при списании (удалении) устройства удаляются его гарантия и установки.
--
-- Существующие таблицы не меняются — только CREATE TABLE.
-- Всё в одной транзакции.
-- =====================================================================
BEGIN;

CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    country         VARCHAR(100)
);

CREATE TABLE models (
    model_id SERIAL PRIMARY KEY,
    manufacturer_id INT NOT NULL REFERENCES manufacturers(manufacturer_id) ON DELETE RESTRICT,
    name            VARCHAR(100) NOT NULL,
    type            VARCHAR(20) NOT NULL,

    UNIQUE (manufacturer_id, name),
    CHECK (type IN ('laptop', 'monitor', 'phone'))
);

CREATE TABLE devices (
    device_id       SERIAL PRIMARY KEY,
    model_id        INT NOT NULL REFERENCES models(model_id) ON DELETE RESTRICT,
    inventory_number VARCHAR(50) NOT NULL UNIQUE,
    serial_number    VARCHAR(50) NOT NULL UNIQUE,
    purchase_date    DATE NOT NULL,
    price            NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    employee_id      INT REFERENCES users(user_id) ON DELETE RESTRICT,
    issue_date       DATE,
    CHECK ((user_id IS NULL) = (issue_data IS NULL))

);

CREATE TABLE warranties (
    warranty_id SERIAL PRIMARY KEY,
    device_id   INT NOT NULL UNIQUE REFERENCES devices(device_id) ON DELETE CASCADE,
    contract_number VARCHAR(50) NOT NULL,
    expiration_date DATE NOT NULL
);

CREATE TABLE programs (
    program_id SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE device_programs (
    device_id   INT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    program_id  INT NOT NULL REFERENCES programs(program_id) ON DELETE RESTRICT,
    install_date DATE NOT NULL DEFAULT CURRENT_DATE,
    license_key  VARCHAR(100) UNIQUE,

    PRIMARY KEY (device_id, program_id)
);

COMMIT;
