<h1 align="center">Elchain</h1>
<p align="center"><b>Система учёта оптово-розничной торговли электронными компонентами</b></p>

---

Elchain — приложение с базой данных MySQL для автоматизации торговли электронными компонентами (микроконтроллеры, платы, радиодетали, сенсоры, кабели, разъёмы и сопутствующие товары). Проект реализует полный цикл торговых операций: от закупки и размещения товара на складе до оформления сделки, применения скидок, выдачи чека и формирования финансовой отчётности.

## Проблема и цель проекта

Компания, торгующая электронными компонентами оптом и в розницу, работает как с частными лицами (студенты, радиолюбители, инженеры), так и с организациями (производственные компании, разработчики электроники). Ручной учёт товаров, поставок и сделок в таких условиях приводит к ошибкам в расчётах, затрудняет контроль остатков и анализ продаж, а гибкая система скидок (по объёму и сумме заказа) требует автоматического расчёта.

**Цель проекта** — спроектировать и реализовать базу данных и приложение, которые:

- фиксируют товары, их категории и остатки на складе с привязкой к ячейкам хранения;
- регистрируют поставки по накладным с указанием закупочных цен;
- оформляют сделки, в рамках которых покупатель приобретает несколько товаров одновременно;
- автоматически подбирают наиболее выгодную скидку в зависимости от количества и суммы покупки;
- формируют документ (чек) по каждой сделке;
- генерируют ежемесячные и выборочные отчёты о продажах, поступлениях и прибыли;
- разграничивают права доступа между покупателями и сотрудниками разных должностей.

## Ключевые возможности

**Для покупателя**
- Каталог товаров с поиском, фильтрами по наличию и категории, сортировкой по цене и ID.
- Корзина/сделка с возможностью менять количество и удалять позиции до оплаты.
- Просмотр действующих акций и скидок, в том числе привязанных к конкретным товарам.
- Оплата заказа, отслеживание статуса (от «ожидает оплаты» до «получен покупателем»).
- История заказов и профиль с редактированием личных данных и телефонов.
- Формирование и сохранение кассового чека.

**Для сотрудников (в зависимости от роли)**
- Администратор — полный доступ ко всем таблицам и функциям системы.
- Работник склада — регистрация поставок, управление ячейками хранения и ответственными за них.
- Менеджер по транзакциям — создание, редактирование и отслеживание сделок, печать чеков.
- Бухгалтер / менеджер по продажам — управление скидками и ценами, формирование финансовых отчётов.
- Комплектовщик заказов — обновление статусов заказов, контроль наличия товара, печать чеков.
- Просмотр, поиск, сортировка и фильтрация записей в пределах прав роли; добавление/редактирование/удаление данных при наличии разрешения.

**Отчётность**
- Ежемесячный отчёт о продажах, поступлениях и возвратах с фильтрами по дате, товару и ячейке хранения.
- Подробный отчёт по отдельной транзакции (история изменений, данные покупателя, итоговая сумма).
- Подробный отчёт по покупателю/организации за произвольный период.
- Экспорт отчётов и чеков в PDF.

## Проектирование базы данных

### ER-диаграмма

Инфологическая модель предметной области — стержневые сущности **Товар** и **Покупатель**, ассоциативные/описательные — **Сделка** и **Сотрудник**.
<p align="center"><img width="629" height="659" alt="ER-диаграмма" src="https://github.com/user-attachments/assets/80855850-095c-4e49-a118-a21553eab914" /></p>

### Физическая схема

После нормализации (устранение аномалий вставки/обновления/удаления, приведение к 3NF) модель разворачивается в 16 таблиц:
<p align="center"><img width="1066" height="719" alt="Физическая схема базы данных" src="https://github.com/user-attachments/assets/a7dc6c9b-ca7d-4d9f-b728-403974426023" /></p>


### Таблицы базы данных

| Таблица | Назначение |
|---|---|
| `PRODUCT` | Товары: наименование, описание, категория, оптовая/розничная цена |
| `CATEGORY` | Категории товаров |
| `SUPPLY` | Поставки (дата, номер накладной) |
| `SUPPLY_DETAIL` | Позиции поставки: товар, количество, закупочная цена |
| `CELL` | Ячейки хранения на складе и ответственный сотрудник |
| `PRODUCT_CELL` | Остаток конкретного товара в конкретной ячейке |
| `CUSTOMER` | Покупатели: ФИО, организация, почта |
| `CUSTOMER_PHONE` | Телефоны покупателей (1:M) |
| `EMPLOYEE` | Сотрудники и их роль |
| `ROLE` | Справочник должностей/ролей |
| `DISCOUNT` | Скидки: процент, минимальная сумма/количество, срок действия |
| `DISCOUNT_PRODUCT` | Привязка скидки к конкретным товарам (если применимо) |
| `TRANSACTION` | Сделка: покупатель, применённая скидка, итоговая сумма |
| `TRANSACTION_DETAILS` | Позиции сделки: товар, количество, цена на момент покупки |
| `TRANSACTION_DATE` | История статусов сделки с датой/временем каждого перехода |
| `STATUS` | Справочник статусов сделки (0 — «нет в наличии» … 7 — «возврат») |

Статусы сделки, поддерживаемые системой:

| ID | Статус |
|---|---|
| 0 | Нет в наличии |
| 1 | Ожидает оплаты |
| 2 | Оплачен, в обработке |
| 3 | Принят в работу |
| 4 | На этапе сборки |
| 5 | Собран |
| 6 | Получен покупателем |
| 7 | Возврат |

## Ролевая модель и безопасность

Права спроектированы по принципу минимальных привилегий: каждая роль получает ровно тот набор операций, который необходим для работы, — ни больше, ни меньше.

| Роль | Доступ |
|---|---|
| **Покупатель** | Каталог товаров; собственные данные (`CUSTOMER_VIEW`, `CUSTOMER_USER_VIEW`, `CUSTOMER_PHONE_VIEW`) с запретом менять чужие записи; свои сделки и их статусы |
| **Администратор** | Полный доступ ко всем таблицам и операциям |
| **Работник склада** | Регистрация поставок, редактирование информации о них, управление ячейками и назначением ответственных |
| **Менеджер по транзакциям** | Создание/редактирование/отслеживание сделок, печать чеков |
| **Бухгалтер / менеджер по продажам** | Формирование отчётов, доступ к финансовой информации, управление скидками |
| **Комплектовщик заказов** | Обновление статусов сделок, просмотр наличия товара, печать чеков |

Механизмы защиты данных на уровне БД:

- **Представления (VIEW)** ограничивают видимость строк и столбцов — например, покупатель видит и редактирует только свою запись в `CUSTOMER`, но не может изменить чужие данные.
- **Триггеры** проверяют, является ли текущий пользователь администратором, и автоматически привязывают новые записи (например, номер телефона) к его собственному аккаунту; аналогичная проверка выполняется при удалении.
- **GRANT/REVOKE на уровне MySQL** назначают каждой роли ровно необходимый набор операций (`SELECT`/`INSERT`/`UPDATE`/`DELETE`) на конкретные таблицы и представления.
- **Индексы** добавлены по часто используемым для поиска и сортировки полям (категория, цены, даты поставки, статус, организация) — в работе зафиксировано ускорение выборок после индексирования по сравнению с полным сканированием таблицы.

## Бизнес-логика на стороне БД

Ключевая часть проекта — автоматизация скидок и статусов сделки полностью на уровне СУБД, без участия клиентского кода. Ниже — реальные фрагменты из проекта.

<details>
<summary><b>Функция подбора лучшей скидки — <code>FindBestDiscount</code></b></summary>

Скидка может действовать либо на конкретные товары, либо на сумму/количество всей сделки. Функция сравнивает все подходящие по сроку действия и условиям скидки и возвращает наиболее выгодную.

```sql
DROP FUNCTION FindBestDiscount;
DELIMITER //
CREATE FUNCTION FindBestDiscount(
    p_transaction_id INT,
    p_total_amount DECIMAL(10, 2),
    p_total_qty INT,
    p_product_ids TEXT
) RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE best_discount_id INT DEFAULT NULL;
    DECLARE max_discount_value DECIMAL(10, 2) DEFAULT 0;
    DECLARE current_discount_value DECIMAL(10, 2) DEFAULT 0;

    DROP TEMPORARY TABLE IF EXISTS temp_possible_discounts;
    CREATE TEMPORARY TABLE temp_possible_discounts (
        discount_id INT,
        discount_percent DECIMAL(5, 2),
        discount_value DECIMAL(10, 2),
        is_product_specific BOOLEAN
    );

    -- 1. Скидки на конкретные товары (если передан список товаров)
    IF p_product_ids IS NOT NULL THEN
        INSERT INTO temp_possible_discounts (discount_id, discount_percent, discount_value, is_product_specific)
        SELECT
            d.ID,
            d.Discount_Percent,
            CASE
                WHEN d.Qty_Required IS NOT NULL THEN
                    (SELECT SUM(td.Qty * td.Price) * d.Discount_Percent / 100
                     FROM Transaction_Details td
                     INNER JOIN Discount_Product dp ON td.Product_ID = dp.Product_ID
                     WHERE td.Transaction_ID = p_transaction_id
                       AND dp.Discount_ID = d.ID
                       AND td.Qty >= d.Qty_Required)
                WHEN d.Min_Amount IS NOT NULL THEN
                    (SELECT SUM(td.Qty * td.Price) * d.Discount_Percent / 100
                     FROM Transaction_Details td
                     INNER JOIN Discount_Product dp ON td.Product_ID = dp.Product_ID
                     WHERE td.Transaction_ID = p_transaction_id
                       AND dp.Discount_ID = d.ID
                       AND (td.Qty * td.Price) >= d.Min_Amount)
                ELSE 0
            END AS discount_value,
            TRUE
        FROM Discount d
        INNER JOIN Discount_Product dp ON d.ID = dp.Discount_ID
        WHERE d.Start_Date <= CURDATE()
          AND (d.End_Date IS NULL OR d.End_Date >= CURDATE())
          AND FIND_IN_SET(dp.Product_ID, p_product_ids) > 0;
    END IF;

    -- 2. Общие скидки (не привязанные к конкретным товарам)
    INSERT INTO temp_possible_discounts (discount_id, discount_percent, discount_value, is_product_specific)
    SELECT
        d.ID,
        d.Discount_Percent,
        CASE
            WHEN d.Qty_Required IS NOT NULL AND p_total_qty >= d.Qty_Required THEN
                p_total_amount * d.Discount_Percent / 100
            WHEN d.Min_Amount IS NOT NULL AND p_total_amount >= d.Min_Amount THEN
                p_total_amount * d.Discount_Percent / 100
            ELSE 0
        END AS discount_value,
        FALSE
    FROM Discount d
    WHERE d.Start_Date <= CURDATE()
      AND (d.End_Date IS NULL OR d.End_Date >= CURDATE())
      AND NOT EXISTS (SELECT 1 FROM Discount_Product dp WHERE dp.Discount_ID = d.ID);

    SELECT discount_id INTO best_discount_id
    FROM temp_possible_discounts
    WHERE discount_value > 0
    ORDER BY discount_value DESC, is_product_specific DESC
    LIMIT 1;

    DROP TEMPORARY TABLE IF EXISTS temp_possible_discounts;
    RETURN best_discount_id;
END //
DELIMITER ;
```

</details>

<details>
<summary><b>Триггер пересчёта сделки — <code>before_transaction_update</code></b></summary>

При каждом обновлении сделки триггер пересчитывает сумму, подбирает лучшую скидку через `FindBestDiscount` и запрещает изменение сделок, уже находящихся в продвинутом статусе.

```sql
DROP TRIGGER before_transaction_update;
DELIMITER //
CREATE TRIGGER before_transaction_update
BEFORE UPDATE ON `TRANSACTION`
FOR EACH ROW
BEGIN
    DECLARE total_product_cost DECIMAL(10, 2) DEFAULT 0.0;
    DECLARE discount_value DECIMAL(10, 2) DEFAULT 0.0;
    DECLARE discount_id INT DEFAULT NULL;
    DECLARE discount_percent DECIMAL(5, 2);
    DECLARE total_qty INT DEFAULT 0;
    DECLARE product_list TEXT DEFAULT NULL;
    DECLARE max_status INT DEFAULT 0;
    DECLARE status_updated BOOLEAN DEFAULT FALSE;

    -- Сделки со статусом >= 2 (уже оплачены/в работе) менять нельзя
    SELECT COALESCE(MAX(Status_ID), 0) INTO max_status
    FROM transaction_date WHERE Transaction_ID = OLD.ID;

    IF max_status >= 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Изменение запрещено: сделка имеет статус 2 или выше';
    END IF;

    -- Пересчёт суммы и количества товаров по деталям сделки
    SELECT COALESCE(SUM(td.Qty * td.Price), 0), COALESCE(SUM(td.Qty), 0)
    INTO total_product_cost, total_qty
    FROM Transaction_Details td WHERE td.Transaction_ID = NEW.ID;

    SELECT GROUP_CONCAT(DISTINCT td.Product_ID) INTO product_list
    FROM Transaction_Details td WHERE td.Transaction_ID = NEW.ID;

    -- Подбор лучшей скидки и её применение
    SET discount_id = FindBestDiscount(NEW.ID, total_product_cost, total_qty, product_list);

    IF discount_id IS NOT NULL THEN
        SELECT d.Discount_Percent INTO discount_percent FROM Discount d WHERE d.ID = discount_id;

        IF EXISTS (SELECT 1 FROM Discount_Product dp WHERE dp.Discount_ID = discount_id) THEN
            SELECT COALESCE(SUM(td.Qty * td.Price), 0) INTO discount_value
            FROM Transaction_Details td
            JOIN Discount_Product dp ON td.Product_ID = dp.Product_ID
            WHERE td.Transaction_ID = NEW.ID AND dp.Discount_ID = discount_id;
            SET discount_value = discount_value * discount_percent / 100;
        ELSE
            SET discount_value = total_product_cost * discount_percent / 100;
        END IF;

        SET total_product_cost = total_product_cost - discount_value;
    END IF;

    SET NEW.Total_Cost = total_product_cost;
    SET NEW.Discount_ID = discount_id;
    SET status_updated = UpdateTransactionStatus(NEW.ID);
END//
DELIMITER ;
```

</details>

<details>
<summary><b>Функция автоматического статуса сделки — <code>UpdateTransactionStatus</code></b></summary>

Определяет, можно ли перевести сделку в статус «ожидает оплаты» (1) или «нет в наличии» (0), проверяя остатки по каждому товару в деталях сделки.

```sql
DROP FUNCTION IF EXISTS UpdateTransactionStatus;
DELIMITER //
CREATE FUNCTION UpdateTransactionStatus(p_transaction_id INT)
RETURNS BOOLEAN
DETERMINISTIC
MODIFIES SQL DATA
BEGIN
    DECLARE current_max_status INT DEFAULT 0;
    DECLARE transaction_exists INT DEFAULT 0;
    DECLARE has_products INT DEFAULT 0;
    DECLARE any_product_missing INT DEFAULT 0;

    SELECT COUNT(*) INTO transaction_exists FROM `Transaction` WHERE ID = p_transaction_id;
    IF transaction_exists = 0 THEN RETURN FALSE; END IF;

    SELECT COALESCE(MAX(Status_ID), 0) INTO current_max_status
    FROM Transaction_Date WHERE Transaction_ID = p_transaction_id;

    -- Подтверждённые сделки (статус >= 2) статус больше не меняют автоматически
    IF current_max_status >= 2 THEN RETURN FALSE; END IF;

    SELECT COUNT(*) INTO has_products FROM Transaction_Details td WHERE td.Transaction_ID = p_transaction_id;
    IF has_products = 0 THEN
        DELETE FROM Transaction_Date WHERE Transaction_ID = p_transaction_id;
        INSERT INTO Transaction_Date (Transaction_ID, DateTime, Status_ID) VALUES (p_transaction_id, NOW(), 1);
        RETURN TRUE;
    END IF;

    SELECT COUNT(*) INTO any_product_missing
    FROM Transaction_Details td
    LEFT JOIN PRODUCT_CELL pc ON td.Product_ID = pc.Product_ID
    WHERE td.Transaction_ID = p_transaction_id
      AND (pc.Product_ID IS NULL OR pc.Qty_in_Stock < td.Qty);

    DELETE FROM Transaction_Date WHERE Transaction_ID = p_transaction_id AND Status_ID < 2;

    IF any_product_missing = 0 THEN
        INSERT INTO Transaction_Date (Transaction_ID, DateTime, Status_ID) VALUES (p_transaction_id, NOW(), 1);
    ELSE
        INSERT INTO Transaction_Date (Transaction_ID, DateTime, Status_ID) VALUES (p_transaction_id, NOW(), 0);
    END IF;
    RETURN TRUE;
END //
DELIMITER ;
```

</details>

<details>
<summary><b>Триггер оплаты и списания остатков — <code>before_insert_transaction_date</code></b></summary>

При переводе сделки в статус «оплачен» (2) триггер в один проход проверяет цену и наличие каждого товара, сверяет применённую скидку с лучшей доступной и только после успешных проверок списывает товар со склада — обеспечивая атомарность операции оплаты.

```sql
DROP TRIGGER IF EXISTS before_insert_transaction_date;
DELIMITER //
CREATE TRIGGER before_insert_transaction_date
BEFORE INSERT ON Transaction_Date
FOR EACH ROW
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE product_id_val INT;
    DECLARE product_name_val VARCHAR(255);
    DECLARE qty_val INT;
    DECLARE price_val DECIMAL(10,2);
    DECLARE current_stock INT;
    DECLARE latest_date DATETIME;
    DECLARE has_status_2 INT DEFAULT 0;
    DECLARE wholesale_price DECIMAL(10,2);
    DECLARE retail_price DECIMAL(10,2);
    DECLARE error_message VARCHAR(500);
    DECLARE total_amount DECIMAL(10,2);
    DECLARE total_qty INT;
    DECLARE product_ids TEXT;
    DECLARE best_discount_id INT;
    DECLARE applied_discount_id INT;
    DECLARE allow_update BOOLEAN DEFAULT TRUE;

    DECLARE cur CURSOR FOR
        SELECT td.Product_ID, p.Name, td.Qty, td.Price
        FROM Transaction_Details td
        JOIN PRODUCT p ON td.Product_ID = p.ID
        WHERE td.Transaction_ID = NEW.Transaction_ID;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Статус выше 2 нельзя установить, минуя статус 2
    IF NEW.Status_ID > 2 THEN
        SELECT COUNT(*) INTO has_status_2 FROM Transaction_Date
        WHERE Transaction_ID = NEW.Transaction_ID AND Status_ID = 2;
        IF has_status_2 = 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Нельзя установить статус больше 2, пока не будет установлен статус 2';
        END IF;
    END IF;

    IF NEW.DateTime IS NULL THEN SET NEW.DateTime = NOW(); END IF;

    -- Новый статус не может датироваться раньше последнего
    SELECT MAX(DateTime) INTO latest_date FROM Transaction_Date WHERE Transaction_ID = NEW.Transaction_ID;
    IF latest_date IS NOT NULL AND NEW.DateTime < latest_date THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Дата нового статуса не может быть раньше последнего существующего';
    END IF;

    IF NEW.Status_ID = 2 THEN
        -- Проход 1: проверка цены и остатков по каждому товару сделки
        OPEN cur;
        check_loop: LOOP
            FETCH cur INTO product_id_val, product_name_val, qty_val, price_val;
            IF done THEN LEAVE check_loop; END IF;

            SELECT Price_Wholesale, Price_Retail INTO wholesale_price, retail_price
            FROM PRODUCT WHERE ID = product_id_val;

            IF price_val != wholesale_price AND price_val != retail_price THEN
                SET error_message = CONCAT('Недопустимая цена для товара "', product_name_val, '". ',
                    'Допустимые цены: оптовая ', wholesale_price, ', розничная ', retail_price);
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
            END IF;

            SELECT Qty_in_Stock INTO current_stock FROM PRODUCT_CELL WHERE Product_ID = product_id_val LIMIT 1;
            IF current_stock < qty_val THEN
                SET error_message = CONCAT('Недостаточно товара "', product_name_val, '". ',
                    'В наличии: ', current_stock, ', требуется: ', qty_val);
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
            END IF;
        END LOOP check_loop;
        CLOSE cur;

        -- Проверка: применена ли к сделке лучшая доступная скидка
        IF allow_update THEN
            SELECT SUM(Qty * Price), SUM(Qty), GROUP_CONCAT(DISTINCT Product_ID)
            INTO total_amount, total_qty, product_ids
            FROM Transaction_Details WHERE Transaction_ID = NEW.Transaction_ID;

            SELECT Discount_ID INTO applied_discount_id FROM `Transaction` WHERE ID = NEW.Transaction_ID;
            SET best_discount_id = FindBestDiscount(NEW.Transaction_ID, total_amount, total_qty, product_ids);

            IF best_discount_id IS NOT NULL AND (applied_discount_id IS NULL OR applied_discount_id != best_discount_id) THEN
                SET allow_update = FALSE;
                SET error_message = CONCAT('Найдена лучшая скидка. ID лучшей скидки: ', best_discount_id);
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
            END IF;
        END IF;

        -- Проход 2: списание товара со склада — только если все проверки пройдены
        IF allow_update THEN
            SET done = FALSE;
            OPEN cur;
            update_loop: LOOP
                FETCH cur INTO product_id_val, product_name_val, qty_val, price_val;
                IF done THEN LEAVE update_loop; END IF;
                UPDATE PRODUCT_CELL SET Qty_in_Stock = Qty_in_Stock - qty_val WHERE Product_ID = product_id_val;
            END LOOP update_loop;
            CLOSE cur;
        END IF;
    END IF;
END//
DELIMITER ;
```

</details>

Помимо приведённых фрагментов, в базе реализованы: каскадное удаление через триггеры (там, где `ON DELETE CASCADE` недостаточно из-за дополнительных проверок), запрет изменения первичных ключей после создания записи, автоматическая привязка новых записей (телефонов, ролей) к текущему пользователю, а также индексы по полям, участвующим в частых выборках и сортировках (категория, цены, даты, статус, организация).

## Интерфейс приложения

### Покупатель

<table>
<thead>
  <tr>
    <th width="50%">Вход и каталог товаров</th>
    <th width="50%">Акции и скидки</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>
      <img width="311" height="451" alt="image" src="https://github.com/user-attachments/assets/fe416451-6a2c-4241-8cc8-79b3895195b6" />
      <img width="309" height="451" alt="image" src="https://github.com/user-attachments/assets/a72bd20d-5f2e-4620-aedb-6a389a302721" />
      <img width="309" height="252" alt="image" src="https://github.com/user-attachments/assets/e9794be4-da4b-48a9-965d-91a581255d98" />
      <br><br>
      <img width="952" height="503" alt="image" src="https://github.com/user-attachments/assets/40b294b9-e53a-4de0-9c32-efb499da8689" />
      <img width="812" height="514" alt="image" src="https://github.com/user-attachments/assets/100cdf89-0cfd-47fc-ae15-4bb2c652371b" />
    </td>
    <td>
      <img width="591" height="455" alt="image" src="https://github.com/user-attachments/assets/91399b40-0c89-4152-96e3-03525239cdc6" />
    </td>
  </tr>
  <tr>
    <td><strong>История заказов</strong><br>
      <img width="741" height="408" alt="image" src="https://github.com/user-attachments/assets/550a59b0-bd86-4733-9809-46971f146307" />
    </td>
    <td><strong>Профиль пользователя</strong><br>
      <img width="449" height="474" alt="image" src="https://github.com/user-attachments/assets/e2fe009c-e2d6-477a-afa8-f54289692432" />
    </td>
  </tr>
</tbody>
</table>

### Сотрудник

<table>
<thead>
  <tr>
    <th width="50%">Главное окно</th>
    <th width="50%">Добавление сделки</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>
      <img width="974" height="540" alt="image" src="https://github.com/user-attachments/assets/0788ee42-8d67-4cb4-a49f-c25661371873" />
    </td>
    <td>
      <img width="658" height="447" alt="image" src="https://github.com/user-attachments/assets/424e8108-209f-40b1-9408-40f6232050d1" />
    </td>
  </tr>
</tbody>
</table>

Интерфейсы разграничены по ролям: часть кнопок и таблиц недоступна сотрудникам без соответствующих прав, а данные, скрытые представлениями на уровне БД, физически не попадают в приложение.

## Отчётность и документы

<table>
<thead>
  <tr>
    <th width="33%">Кассовый чек</th>
    <th width="33%">Настройка ежемесячного отчёта</th>
    <th width="33%">Ежемесячный отчёт (PDF)</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>
      <img width="467" height="599" alt="image" src="https://github.com/user-attachments/assets/f22a92a4-74a5-4752-bf85-69b3b8d430e0" />
    </td>
    <td>
      <img width="557" height="510" alt="image" src="https://github.com/user-attachments/assets/9139f5df-b8b8-444e-b78c-e3a93084cdb3" />
    </td>
    <td>
      <img width="444" height="487" alt="image" src="https://github.com/user-attachments/assets/1bd4e616-ded8-453b-bdb2-f0e86c1a2ad2" />
      <img width="458" height="474" alt="image" src="https://github.com/user-attachments/assets/bfb4f693-7dd1-46a1-854d-2600a094fc15" />
    </td>
  </tr>
  <tr>
    <td><strong>Отчёт по транзакции</strong><br>
      <img width="419" height="460" alt="image" src="https://github.com/user-attachments/assets/27974cca-b3fe-4a74-b8f7-6278fe19d4e2" />
      <img width="484" height="482" alt="image" src="https://github.com/user-attachments/assets/2b77fe53-09e8-4b61-a26a-b1843f35b28e" />
    </td>
    <td><strong>Отчёт по организации</strong><br>
      <img width="477" height="522" alt="image" src="https://github.com/user-attachments/assets/232833de-5c49-46e0-b8c0-302c46e593f4" />
      <img width="512" height="802" alt="image" src="https://github.com/user-attachments/assets/ce4696d4-65ec-4e62-9c34-dc99efac4c34" />
    </td>
    <td></td>
  </tr>
</tbody>
</table>

Чек включает наименования товаров, количество, цену, скидку и итоговую сумму. Ежемесячный отчёт — все реализованные товары за период, количество и стоимость продаж, динамику реализации и общую прибыль. Отчёты по транзакции и по клиенту/организации позволяют анализировать поведение отдельных покупателей и историю изменений конкретной сделки.
