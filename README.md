# Market intelligence API

Этот проект представляет собой RESTful API для создания, хранения и удаления секретов.
Вы можете создать секрет, поделиться ссылкой и кодовой фразой. В течении определенного времени по этим параметрам
секрет будет доступен, но после первого же прочтения секрет будет удален.

## Оглавление

- [Установка и использование](#установка-и-использование)
- [Структура проекта](#структура-проекта)
- [API Эндпоинты](#api-эндпоинты)
- [Docker](#docker)
- [Тестирование](#тестирование)
- [Документация](#документация)
- [Celery](#celery)

## Установка и использование

1. Клонируйте репозиторий:
    ```sh
    git clone https://github.com/RedHotChilliHead/Market-intelligence.git
    cd Market_intelligence
    ```


2. Установите зависимости:

    ```sh

    pip install -r requirements.txt

    ```

3. Создайте том для сохранения данных приложения:

    ```sh

    docker volume create secret_postgres_data

    ```

4. Запуск всех контейнеров в режиме демона:

    ```sh

    docker-compose up -d

    ```

5. Примените миграции:

    ```sh

    docker-compose run secretapp python manage.py migrate

    ```


Сервер будет доступен по адресу `http://127.0.0.1:8000`.


## Структура проекта


- urls.py (корневой): Конфигурация маршрутизации URL проекта, включая маршруты для административного интерфейса и API-документации.

- urls.py (приложение): Конфигурация маршрутизации URL для приложения, включая генерацию секретных ключей
для доступа к секретам и отображение секретных сообщений.

- models.py: Определения модели секрета.

- views.py: Определения представлений для обработки запросов к API, включая генерацию секретных ключей
для доступа к секретам и отображение секретных сообщений.

- views.py: Тесты для API приложения.


## API Эндпоинты

#### Метод сохранения секрета, генерации секретного ключа и ссылки для доступа к секрету
Данный метод API принимает секрет (в виде текста), ключевую фразу и время жизни секрета (не обязательный параметр,
значение по умолчанию 7 дней),
Метод возвращает url-адрес для доступа к секрету и секретный ключ, который является частью url-адреса.
Время жизни секрета (TTL) - необязательный параметр, он должен принимать значения от 1 до 365 дней (в днях).

В данном моетоде также реализовано хэширование кодовой фразы и шифрование самого секрета, поэтому
все эти данные хранятся в базе данных в измененном виде.

Примечание:
Так как MongoDB не реляционная база данных, то Django и djangorestframework не полностью поддерживает ее функционал.
Поэтому для данного приложения в качестве базы данных была использована PostgreSQL.
Однако, PostgreSQL не поддерживает автоматическое удаление записей по истечении времени жизни (TTL), по сравнению с Mongo,
поэтому для этого приложения была разработана задача, воркер и планировщик задач на celery,
который раз в час проверяют базу данных на наличие таких записей и удаляет.
В качестве брокера используется сервер Redis.

#### URL

```http
http://127.0.0.1:8000/generate/
```
#### Пример запроса

```http
POST
Content-Type: application/json

Body: {
  "text": "It is a secret data",
  "passphrase": "Phrase",
  "TTL": 7
}
```
#### Пример ответа

```http
HTTP 201 Created
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "secret_key": "8q0862xlrevmf66jeojova7bmh1p2zf1",
    "url": "http://127.0.0.1:8000/secrets/8q0862xlrevmf66jeojova7bmh1p2zf1/"
}
```

#### Метод отображения секрета по ссылке и кодовой фразе
Данный метод API принимает кодовую фразу, хэширует ее, сравнивает с хэшем из базы данных и возвращает секрет.

#### URL

```http
http://127.0.0.1:8000/secrets/<str:secret_key>/
```
#### Пример запроса

```http
POST
Content-Type: application/json

Body: {
  "passphrase": "Phrase",
}
```
#### Пример ответа

```http
HTTP 200 OK
Allow: POST, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "secret": "It is a secret data"
}
```

#### Во всех методах реализована валидация полей

## Docker


Проект использует Docker для контейнеризации. Основные команды:


- Запуск всех контейнеров в режиме демона:

    ```sh
    docker-compose up -d
    ```
  
- Запуск всех контейнеров с пересборкой:

    ```sh
    docker-compose up -d --build
    ```

- Остановка всех контейнеров:

    ```sh
    docker-compose down
    ```
- Создание тома:

  ```sh
  docker volume create secret_postgres_data
  ```
- Удаление тома:

  ```sh
  docker volume rm secret_postgres_data
  ```

- Применение миграций:

    ```sh
    docker-compose run contentapp python manage.py migrate
    ```


## Тестирование


Проект содержит тесты для проверки функциональности API.

Тесты можно запускать следующей командой:

```sh
TEST_MODE=True docker compose up -d
docker compose exec secretapp python manage.py test
```

Покрытие тестами составляет 97%, что бы проверить необходимо выполнить следующие команды:
```sh
TEST_MODE=True docker compose up -d
docker compose exec secretapp coverage run manage.py test
docker compose exec secretapp coverage report
```

## Документация

К данному API подключена Swagger документация на английском языке и она доступна по адресу
http://127.0.0.1:8000/api/schema/swagger/

## Документация

Проект использует Celery для выполнения задач по удаления записей.
Основные команды для управления и мониторинга (при желании):

- Проверка состояния воркеров
```sh
celery -A Market_intelligence status
```

- Выключение воркера
```sh
celery -A Market_intelligence control shutdown
```

- Проверка выполняемых задач
```sh
celery -A Market_intelligence inspect active
```

- Проверка завершенных задач
```sh
celery -A Market_intelligence inspect reserved
```

- Получение списка активных очередей
```sh
celery -A Market_intelligence inspect active_queues
```