# Лабораторная работа 1

Тема: Django, модели, шаблоны, наследование шаблонов, встроенные и кастомные теги/фильтры.

Проект: простой каталог книг.

## Как запустить

Открыть PowerShell в папке проекта:

Установить Django, если еще не установлен:

```powershell
pip install -r requirements.txt
```

Применить миграции:

```powershell
python manage.py migrate
```

Запустить сервер:

```powershell
python manage.py runserver
```

Открыть сайт:

```text
http://127.0.0.1:8000/
```

Админ-панель:

```text
http://127.0.0.1:8000/admin/
```

Если нужен пользователь для админки:

```powershell
python manage.py createsuperuser
```

## Как использовать

1. Открыть главную страницу `/`.
2. Посмотреть список книг.
3. Посмотреть, что данные берутся из модели `Book`, а не просто написаны в HTML.
4. Открыть `catalog/models.py` и посмотреть модель книги.
5. Открыть `templates/catalog/book_list.html` и посмотреть `{% extends %}`.
6. Открыть `templates/includes/book_card.html` и посмотреть `{% include %}`.
7. Открыть `catalog/templatetags/book_extras.py` и посмотреть свои теги/фильтры.

## Где что лежит

- `catalog/models.py` - модель `Book`.
- `catalog/views.py` - вывод списка книг.
- `catalog/urls.py` - маршрут главной страницы.
- `catalog/migrations/0001_initial.py` - миграция и стартовые книги.
- `templates/base.html` - базовый шаблон.
- `templates/catalog/book_list.html` - страница списка книг.
- `templates/includes/book_card.html` - отдельная карточка книги.
- `catalog/templatetags/book_extras.py` - кастомные теги и фильтры.

## Соответствие ТЗ

- Создана модель `Book`.
- Сделана миграция.
- Данные выводятся в HTML-шаблоне.
- Используется наследование шаблонов: `{% extends "base.html" %}`.
- Используется подключение шаблона: `{% include "includes/book_card.html" %}`.
- Используются встроенные теги/фильтры:
  - `{% for %}`;
  - `{% empty %}`;
  - `{% if %}`;
  - `length`;
  - `date`;
  - `title`.
- Используются кастомные простые теги:
  - `catalog_title`;
  - `availability_label`;
  - `reading_time`.
- Используются кастомные фильтры:
  - `rubles`;
  - `initials`;
  - `badge`.

## Самопроверка

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

Ожидаемый результат:

```text
System check identified no issues
No changes detected
```
