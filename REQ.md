
## 📜 ТЕХНИЧЕСКОЕ ЗАДАНИЕ (ТЗ)

Разработка модуля управления электронной структурой изделия (ЭСИ / BOM) с поддержкой 150% BOM и версионирования

---

## 1. НАЗНАЧЕНИЕ СИСТЕМЫ И ЦЕЛЬ РАЗРАБОТКИ

Модуль предназначен для централизованного хранения, управления и конфигурирования структуры изделий компании. Система обеспечивает разделение инженерного представления данных (удобные человекочитаемые артикулы) и реляционных связей внутри СУБД, гарантируя целостность данных при изменении статусов объектов, ревизий и составов изделий во времени.

 Соглашение о поименовании и конвенция артикулов

Система использует строгую маску для визуального отображения артикулов инженерам: **xxY.zz.nnnnn**
* **xx** — Префикс проекта / кампании `[A-Z]{2}`.
* **Y** — Тип составной части:
  * `P` — Продукт (изделие целиком, имеет серийный номер).
  * `A` — Сборка (механический CAD-узел).
  * `D` — Детали (механические элементы без подключения проводов).
  * `E` — Электрика (схемы, датчики, кнопки, моторы).
  * `B` — Платы (печатные платы с топологией).
  * `C` — Кабели (кабельные сборки и жгуты).
  * `G` — Мануалы (инструкции и документация).
* **zz** — Группа составных частей `[A-Z0-9]{2}`.
* **nnnnn** — Порядковый номер `[0-99999]`.

---

---

## 2. АРХИТЕКТУРА И СХЕМА БАЗЫ ДАННЫХ (PostgreSQL)


В основе архитектуры лежит паттерн разделения **бизнес-ключа** (строковый артикул для инженеров) и **суррогатного ключа** (целочисленный идентификатор `id` для связей). Строковый артикул генерируется СУБД автоматически на лету с помощью `GENERATED ALWAYS AS`.

```sql
-- Таблица 1. Мастер-запись элемента (Определяет уникальность артикула)
CREATE TABLE item_master (
    item_id SERIAL PRIMARY KEY,
    project_code CHAR(2) NOT NULL,         -- xx (Диапазон [A-Z]{2})
    item_type CHAR(1) NOT NULL,            -- Y  (P, A, D, E, B, C, G)
    group_code CHAR(2) NOT NULL,           -- zz (Диапазон [A-Z0-9]{2})
    sequence_number INT NOT NULL,          -- nnnnn (Диапазон 0-99999)
    
    -- АВТОМАТИЧЕСКИ ВЫЧИСЛЯЕМОЕ ПОЛЕ (Бизнес-артикул)
    display_sku VARCHAR(20) GENERATED ALWAYS AS (
        project_code || item_type || '.' || group_code || '.' || LPAD(sequence_number::text, 5, '0')
    ) STORED,

    UNIQUE(project_code, item_type, group_code, sequence_number),
    CONSTRAINT chk_project_code CHECK (project_code ~ '^[A-Z]{2}$'),
    CONSTRAINT chk_item_type CHECK (item_type IN ('P', 'A', 'D', 'E', 'B', 'C', 'G')),
    CONSTRAINT chk_group_code CHECK (group_code ~ '^[A-Z0-9]{2}$'),
    CONSTRAINT chk_seq_num CHECK (sequence_number BETWEEN 0 AND 99999)
);

CREATE UNIQUE INDEX idx_item_display_sku ON item_master(display_sku);


-- Таблица 2. Ревизии элемента (Хранит изменяемую геометрию и файлы)
CREATE TABLE item_revisions (
    revision_id SERIAL PRIMARY KEY,
    item_id INT REFERENCES item_master(item_id) ON DELETE CASCADE,
    revision_code VARCHAR(5) NOT NULL DEFAULT '01',-- Код ревизии ('01', '02'...)
    name VARCHAR(255) NOT NULL,                    -- Наименование компонента
    status VARCHAR(20) NOT NULL DEFAULT 'In_Development',-- 'In_Development', 'Approved', 'Archived'
    cad_file_path TEXT,                                 -- Путь к файлу геометрии
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    UNIQUE(item_id, revision_code),
    CONSTRAINT chk_status CHECK (status IN ('In_Development', 'Approved', 'Archived'))
);


-- Таблица 3. Структура 150% BOM (Связи между ревизией родителя и артикулом потомка)
CREATE TABLE product_structure_150 (
    parent_rev_id INT REFERENCES item_revisions(revision_id) ON DELETE CASCADE,
    child_id INT REFERENCES item_master(item_id) ON DELETE RESTRICT,
    quantity NUMERIC(10, 3) NOT NULL DEFAULT 1.000,
    
    -- Дополнительные метаданные для мехатроники и интеграций
    source_system VARCHAR(10) NOT NULL DEFAULT 'MCAD',  -- 'MCAD', 'ECAD'
    ref_des VARCHAR(20) DEFAULT NULL,                   -- Позиционное обозначение (например, 'M1', 'R15')
    
    -- Логическое правило применимости (например, 'WINTER_PACK and not REAR_CAMERA')
    selection_rule TEXT DEFAULT NULL,
    
    -- Временное версионирование состава (Жизненный цикл связей)
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT NULL,                     -- NULL = актуально по сей день
    eco_number VARCHAR(20) DEFAULT NULL,                 -- Номер Извещения об Изменении
    
    PRIMARY KEY (parent_rev_id, child_id, valid_from),
    CONSTRAINT chk_source_system CHECK (source_system IN ('MCAD', 'ECAD'))
);
```

---

## 3. БИЗНЕС-ЛОГИКА И АЛГОРИТМЫ ВАЛИДАЦИИ (Для Python бэкенда)

## 3.1. Генерация очередного порядкового номера `nnnnn`

При создании новой позиции (например, инженеру нужна новая деталь `D` в группе `32` для проекта `GA`), система должна автоматически вычислять следующий свободный номер.

```python
# Псевдокод / Логика репозитория на Python:
def get_next_sequence_number(project_code: str, item_type: str, group_code: str) -> int:
    # Запрос ищет максимальный текущий номер для данной тройки параметров
    query = """
        SELECT COALESCE(MAX(sequence_number), -1) + 1 
        FROM item_master 
        WHERE project_code = :project_code 
          AND item_type = :item_type 
          AND group_code = :group_code
    """
    # Результат используется для вставки новой записи. Диапазон ограничен [0, 99999]
```

## 3.2. Концепция управления изменениями (Ревизии vs Артикулы)

Разработчики должны заложить в интерфейсы и бизнес-логику жесткое разделение на базе правила Fit, Form, Function (Форма, Посадка, Функция):

1. Создание новой ревизии (`item_revisions`): Разрешено, если деталь изменяется конструктивно, но полностью взаимозаменяема со старой (например, изменилась марка клея или скругление фаски). Артикул (`display_sku`) не меняется.
2. Создание нового артикула (`item_master`): Обязательно, если деталь теряет взаимозаменяемость (изменились габариты, точки крепления, критические электропараметры). Старая связь в `product_structure_150`закрывается текущим временем (`valid_to = datetime.now()`), а новая деталь добавляется с `valid_from = datetime.now()`.

---

## 4. АЛГОРИТМЫ ОБРАБОТКИ И ФИЛЬТРАЦИИ СТРУКТУРЫ

## 4.1. Фильтрация 150% BOM в 100% BOM (Конфигуратор)

Когда пользователь запрашивает состав изделия под конкретный коммерческий заказ с выбранным массивом опций (например, `active_options = {"WINTER_PACK": True, "REAR_CAMERA": False}`), бэкенд должен выполнить рекурсивный запрос состава на определенную дату, а затем отфильтровать строки по правилам применимости.

```python
import ast

def evaluate_selection_rule(rule_string: str, active_options: dict) -> bool:
    """
    Безопасное вычисление булева выражения правила применимости.
    Синтаксис правила должен соответствовать Python (and, or, not).
    Пример: "WINTER_PACK and not REAR_CAMERA"
    """
    if not rule_string:
        return True # Базовый компонент, включается всегда
        
    try:
        # Валидация строки правила через абстрактное синтаксическое дерево (защита от code injection)
        code = compile(rule_string, "<string>", "eval")
        # Вычисление в изолированном контексте переданных опций
        return bool(eval(code, {"__builtins__": None}, active_options))
    except Exception as e:
        # В случае ошибки синтаксиса правило считается невыполненным, логируется ошибка
        return False
```

## 4.2. Алгоритм склейки механики (MCAD) и электрики (ECAD)

Поскольку мехатронные изделия (например, шаговый двигатель `GAE.AV.01002`) присутствуют и в 3D-модели (MCAD), и на схеме (ECAD), бэкенд при формировании итогового перечня закупки должен производить консолидацию:

1. Из дерева состава извлекаются все элементы для сборки.
2. Проводится группировка по `item_id` (или `display_sku`).
3. Правило подсчета количества:
    
    - Если у компонента тип (`item_type`) относится к механике (`D`, `A`), количество суммируется без условий.
    - Если тип компонента относится к электрике/платам (`E`, `B`, `C`) и он обнаружен в обеих системах-источниках (`source_system`): количество (quantity) берется строго из записей MCAD, так как конструктор физически разместил точное число устройств на раме.
    
4. Правило сбора метаданных: Позиционные обозначения (`ref_des`) из всех записей системы `ECAD`собираются в массив или строку через запятую (например, `M1, M2`) и привязываются к итоговой складской позиции.

---

## 5. ТРЕБОВАНИЯ К ИНТЕГРАЦИОННОМУ API (Эндпоинты)

Бэкенд должен предоставить как минимум следующие REST API эндпоинты для внешних утилит (включая будущие скрипты выгрузки из КОМПАС-3D):

- `POST /api/v1/items/` — Создание новой мастер-записи элемента. Бэкенд сам рассчитывает и возвращает сгенерированный `display_sku`.
- `POST /api/v1/items/{item_id}/revisions/` — Создание новой ревизии для существующего артикула (перевод в статус "В разработке", фиксация пути к файлу).
- `POST /api/v1/bom/import` — Прием структуры изделия из CAD. Принимает массив связей (родитель, потомок, количество, система-источник, RefDes).
- `GET /api/v1/bom/configured` — Получение отконфигурированного 100% BOM. Принимает параметры: `parent_sku`, `target_date`, и массив `options`. Возвращает плоский или древовидный чистый список деталей для производства.


## 6. Процедуры ECO / ECR (Запросы и Извещения об изменениях)

Любое изменение структуры проходит строгий бюрократический и технический цикл:

1. ECR (Engineering Change Request): Запрос на изменение. Инженер или поставщик предлагает заменить деталь (например, из-за поломки кронштейна на тестах).
2. Анализ последствий (Impact Analysis): Система проверяет, на какие еще модели автомобилей повлияет изменение этой детали.
3. ECO (Engineering Change Order): Извещение об изменении. Документ, который подписывается всеми службами (конструкторы, технологи, закупки, логисты). Только после утверждения ECO изменения вступают в силу в базе данных.


## 4. Регламент заполнения свойств в КОМПАС-3D

Данные считываются скриптом напрямую из свойств файлов `.m3d` и `.a3d`. Ввод текстовых спецификаций вручную запрещен.

1. **Обозначение:** Строго соответствует маске `xxY.zz.nnnnn` (например, `GAA.GF.00534`).
2. **Наименование:** Понятное русское название («Кронштейн двигателя»).
3. **Источник данных:** Кастомное свойство-список: `MCAD` или `ECAD`. Для мехатроники всегда ставится `MCAD`.
4. **Поз. обозначение:** Заполняется для элементов электрики. Строго соответствует обозначению на схеме (`M1`, `M2`, `S1`). Каждая физическая единица детали в дереве должна иметь свой уникальный `RefDes`.

---

## 5. Программный код скрипта выгрузки (КОМПАС-3D COM API)

Ниже приведен примерный скрипт интеграции для выгрузки структуры активной сборки.

```python
import sys
import requests
from win32com.client import Dispatch, gencache

PLM_API_URL = "http://localhost:8000/api/v1/bom/import"
PROP_MARK = 1.0        
PROP_NAME = 2.0        
PROP_SOURCE = 10001.0  
PROP_REFDES = 10002.0  

def connect_to_kompas():
    try:
        kompas = Dispatch("KOMPAS.Application.7")
        kompas.Visible = True
        return kompas
    except Exception as e:
        print(f"[-] Ошибка подключения к КОМПАС-3D: {e}")
        sys.exit(1)

def get_property_value(part, prop_id):
    try:
        prop_keeper = part.QueryInterface(gencache.CLSIDFromString("{62AF0A25-B410-4A3C-BEE4-BD036B69BB22}"))
        return prop_keeper.GetPropertyValue(prop_id)
    except Exception:
        return None

def parse_assembly_structure(kompas):
    active_doc = kompas.ActiveDocument
    if not active_doc or active_doc.DocumentType != 3:
        print("[-] Ошибка: Откройте сборку (.a3d) в КОМПАС-3D!")
        return None, []

    doc_3d = active_doc.TopPart
    parent_sku = get_property_value(doc_3d, PROP_MARK)
    
    components = doc_3d.Parts
    bom_items = []

    for i in range(components.Count):
        part = components.Part(i)
        if part.Excluded:
            continue

        sku = get_property_value(part, PROP_MARK)
        name = get_property_value(part, PROP_NAME)
        source_system = get_property_value(part, PROP_SOURCE) or "MCAD"
        ref_des = get_property_value(part, PROP_REFDES)

        if not sku:
            continue

        bom_items.append({
            "child_sku": sku,
            "name": name,
            "quantity": 1.0,
            "source_system": source_system,
            "ref_des": ref_des
        })
    return parent_sku, bom_items

def send_to_plm(parent_sku, bom_items):
    if not parent_sku or not bom_items:
        return
    payload = {"parent_sku": parent_sku, "items": bom_items}
    try:
        response = requests.post(PLM_API_URL, json=payload, timeout=10)
        print(f"[+] Синхронизация: Код {response.status_code}")
    except Exception as e:
        print(f"[-] Ошибка отправки: {e}")

if __name__ == "__main__":
    kompas_app = connect_to_kompas()
    parent_sku, items = parse_assembly_structure(kompas_app)
    if parent_sku:
        send_to_plm(parent_sku, items)
```


### 3.3. Склейка MCAD и ECAD (Reconciliation)
Для мехатронных компонентов (моторы, датчики, разъемы) количество считывается строго из механического состава (`source_system = 'MCAD'`), а позиционные обозначения (`ref_des`) склеиваются текстовой строкой из состава электрических схем (`source_system = 'ECAD'`). В итоговый закупочный BOM попадает объединенная позиция с корректным количеством.



## 1. Эффективность по дате или VIN (Effectivity Date / VIN Effectivity)

В автопроме структуру изделия практически никогда не удаляют и не перезаписывают. Вместо этого используют механизмы применимости (условия, при которых деталь идет на конвейер).  
В таблицу связей BOM добавляются временные метрики или номера кузовов:

- Date Effectivity: В структуре указывается `Valid From` (Дата начала установки) и `Valid To` (Дата окончания). Когда внедряется новая деталь, у старой выставляется дата окончания, а у новой — дата начала.
- Serial / VIN Effectivity: Изменение привязывается к конкретному номеру шасси или VIN. Например: _«Данный блок управления двигателем ставится начиная с VIN ...H100500»_.


Концепция 150% BOM (Configurable BOM) — это вершина инженерного учета в автопроме. Вместо того чтобы создавать 100 отдельных спецификаций для 100 разных комплектаций одной машины, создается одна мега-структура (150% BOM), которая содержит вообще _все_ возможные детали.

Когда клиент в автосалоне выбирает комплектацию, конфигуратор отсекает лишнее и собирает индивидуальный 100% BOM (Manufacturing BOM) для производства конкретного автомобиля.

Давайте разберем, как эта магия устроена изнутри и как правильно спроектировать ее в вашей базе данных.

---

## 1. Архитектура: Три кита конфигуратора

Чтобы система заработала, нам понадобятся три сущности:

1. Словарь Опций (Features/Options): Список всех доступных функций (например, `WINTER_PACK`, `ENGINE_V6`, `LEATHER_SEATS`).
2. Конфигурация Продукта (Product Configuration): Набор опций, выбранный для конкретного экземпляра устройства.
3. Логические правила применимости (Effectivity Rules): Условия, при которых деталь попадает в сборку.


## 4. Как это решает проблему изменений?

Вернемся к вашему примеру с заменой платы подогрева руля `GAB.ZY.10000`. В 150% BOM-подходе это изменение изолировано:

1. Если плата меняется для всех будущих "зимних пакетов": Мы просто используем временную применимость (Date Effectivity) _внутри_ правила опции. Старая плата имеет правило `WINTER_PACK` и `valid_to = '2026-09-28'`, новая — `WINTER_PACK` и `valid_from = '2026-09-29'`.
2. Если плата меняется из-за смены поставщика чипов для конкретного рынка: Мы не трогаем механику и другие платы. Мы просто уточняем правило применимости:
    
    - Было: `WINTER_PACK`
    - Стало для старой платы: `WINTER_PACK AND NOT CHIP_V2`
    - Стало для новой платы: `WINTER_PACK AND CHIP_V2`
    

Таким образом, инженеры могут параллельно развивать и изменять электрику, кабели или мануалы под разные конфигурации, абсолютно не ломая общую структуру базового продукта.
