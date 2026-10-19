# cyberoad

## Опис і призначення

**cyberoad** це roadmap для підготовки до ctf-змагань, на кожну категорію має типи завдань і до кожного типу містить посилання на статті / відео на ютубі щоб вивчити цю тему. 

## Як запустити проєкт

Потрібен Python 3.12 або новіший.

1. Склонуйте репозиторій і перейдіть у теку:

   ```bash
   git clone https://github.com/limitation-perception/cybersec_roadmap.git
   cd cybersec_roadmap
   ```

2. Створіть віртуальне оточення і встановіть залежності:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Застосуйте міграції:

   ```bash
   python manage.py migrate
   ```

4. Запустіть сервер:

   ```bash
   python manage.py runserver
   ```

API буде доступне за адресою http://127.0.0.1:8000.

Фронтенд лежить в окремому репозиторії [cyberoad_front](https://github.com/limitation-perception/cyberoad_front) і запускається на http://localhost:5173. CORS на бекенді дозволяє запити з `http://localhost:5173` і `http://127.0.0.1:5173`.

## Postman

Колекція з усіма ендпоінтами лежить у [postman/cyberoad.postman_collection.json](postman/cyberoad.postman_collection.json) (формат Collection v2.1).

- Імпортуйте її в Postman: **Import** → оберіть файл.
- Адреса сервера задана в змінній колекції `{{base_url}}` (за замовчуванням `http://127.0.0.1:8000`).
- Запускайте папки по черзі або всю колекцію через **Run collection**: запити на створення зберігають `id` у змінні `category_id`, `task_type_id` і `resource_id`.
- Папка **Errors** містить запити, що повертають помилки `400`, `404` і `409`.

## Формат помилок

Усі помилки повертаються в однаковому форматі з ключем `detail`.

Невалідні дані (`400 Bad Request`), помилки по кожному полю в `errors`:

```json
{
  "detail": "Invalid data.",
  "errors": {
    "url": ["Enter a valid URL."],
    "type": ["\"podcast\" is not a valid choice."]
  }
}
```

Об'єкт не знайдено (`404 Not Found`):

```json
{ "detail": "No Category matches the given query." }
```

Видалення, яке порушує зв'язки (`409 Conflict`). Категорію не можна видалити, поки в ній є типи завдань, а тип завдання, поки до нього прив'язані ресурси:

```json
{ "detail": "Cannot delete category: it has 3 task type(s). Delete them first." }
```

Чому `409`: сам запит коректний і об'єкт існує, але видалення конфліктує з поточним станом даних, бо до об'єкта прив'язані інші записи.

## Ендпоінти

#### `GET /categories` - список усіх категорій

- **Response:** `200 OK`

```json
[
  { "id": 1, "name": "Web", "description": "Вразливості вебзастосунків" },
  { "id": 2, "name": "Crypto", "description": "Криптографія" }
]
```

#### `GET /categories/{id}` - поточна категорія

- **Response:** `200 OK`, `404 Not Found`

```json
{ "id": 1, "name": "Web", "description": "Вразливості вебзастосунків" }
```

#### `POST /categories` - додати категорію

- **Request body:**

```json
{ "name": "Web", "description": "Вразливості вебзастосунків" }
```

- **Response:** `201 Created`, `400 Bad Request`

```json
{ "id": 1, "name": "Web", "description": "Вразливості вебзастосунків" }
```

#### `PUT /categories/{id}` - редагувати категорію

- **Request body:**

```json
{ "name": "Web", "description": "Новий опис" }
```

- **Response:** `200 OK`, `400 Bad Request`, `404 Not Found`

```json
{ "id": 1, "name": "Web", "description": "Новий опис" }
```

#### `DELETE /categories/{id}` - видалити категорію

- **Response:** `204 No Content`, `404 Not Found`, `409 Conflict` (у категорії є типи завдань)

#### `GET /categories/{id}/task-types` - типи завдань однієї категорії

- **Response:** `200 OK`, `404 Not Found`

```json
[
  { "id": 1, "category": 1, "name": "SQL Injection", "description": "Впровадження SQL-коду в запит" },
  { "id": 2, "category": 1, "name": "XSS", "description": "Впровадження JavaScript на сторінку" }
]
```

#### `GET /task-types` - список усіх типів завдань

- **Response:** `200 OK`

```json
[
  { "id": 1, "category": 1, "name": "SQL Injection", "description": "Впровадження SQL-коду в запит" },
  { "id": 2, "category": 2, "name": "RSA", "description": "Атаки на RSA" }
]
```

#### `GET /task-types/{id}` - один тип завдання

- **Response:** `200 OK`, `404 Not Found`

```json
{ "id": 1, "category": 1, "name": "SQL Injection", "description": "Впровадження SQL-коду в запит" }
```

#### `POST /task-types` - додати тип завдання в категорію

- **Request body:**

```json
{ "category": 1, "name": "SQL Injection", "description": "Впровадження SQL-коду в запит" }
```

- **Response:** `201 Created`, `400 Bad Request`

```json
{ "id": 1, "category": 1, "name": "SQL Injection", "description": "Впровадження SQL-коду в запит" }
```

#### `PUT /task-types/{id}` - редагувати тип завдання

- **Request body:**

```json
{ "category": 1, "name": "SQL Injection", "description": "Новий опис" }
```

- **Response:** `200 OK`, `400 Bad Request`, `404 Not Found`

```json
{ "id": 1, "category": 1, "name": "SQL Injection", "description": "Новий опис" }
```

#### `DELETE /task-types/{id}` - видалити тип завдання

- **Response:** `204 No Content`, `404 Not Found`, `409 Conflict` (у типу завдання є ресурси)

#### `GET /task-types/{id}/resources` - статті й відео до типу завдання

- **Response:** `200 OK`, `404 Not Found`

```json
[
  { "id": 1, "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" },
  { "id": 2, "task_type": 1, "title": "SQL Injection for beginners", "url": "https://www.youtube.com/watch?v=...", "type": "video" }
]
```

#### `GET /resources` - список усіх ресурсів

- **Response:** `200 OK`

```json
[
  { "id": 1, "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" },
  { "id": 2, "task_type": 2, "title": "RSA attacks", "url": "https://www.youtube.com/watch?v=...", "type": "video" }
]
```

#### `GET /resources/{id}` - один ресурс

- **Response:** `200 OK`, `404 Not Found`

```json
{ "id": 1, "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" }
```

#### `POST /resources` - додати статтю чи відео до типу завдання

- **Request body:**

```json
{ "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" }
```

- **Response:** `201 Created`, `400 Bad Request`

```json
{ "id": 1, "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" }
```

#### `PUT /resources/{id}` - редагувати ресурс

- **Request body:**

```json
{ "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" }
```

- **Response:** `200 OK`, `400 Bad Request`, `404 Not Found`

```json
{ "id": 1, "task_type": 1, "title": "SQL injection", "url": "https://portswigger.net/web-security/sql-injection", "type": "article" }
```

#### `DELETE /resources/{id}` - видалити ресурс

- **Response:** `204 No Content`, `404 Not Found`

## Схема бази даних

![Схема бази даних](db-schema.png)
