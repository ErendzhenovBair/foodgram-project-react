# Продуктовый помощник - FOODGRAM

![Foodgram workflow](https://github.com/ErendzhenovBair/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## Описание проекта

Привет! Foodgram - это полезное приложение, где пользователи могут делиться своими любимыми рецептами, добавлять их в избранное и подписываться на публикации других авторов. А ещё, у нас есть удобный сервис «Список покупок», который позволяет пользователям создавать список продуктов, необходимых для приготовления выбранных блюд. И самое интересное, вы можете экспортировать этот список в файл формата .txt, чтобы легко иметь его под рукой в магазине. Нам очень важно, чтобы наши пользователи могли наслаждаться приготовлением вкусных блюд без лишних хлопот.


### Технологии

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)

- Python 3.10.5
- Django 3.2.15
- Django Rest Framework 3.12.4
- React,
- JavaScript
- Authtoken
- Docker
- Docker-compose
- PostgreSQL
- Gunicorn
- Nginx
- GitHub Actions

### Запуск проекта из образов с Docker hub

Для запуска необходимо создать папку проекта foodgram и перейти в нее:

```
mkdir foodgram
cd foodgram
```
В папку проекта скачиваем файл docker-compose.production.yml и запускаем его:

```
sudo docker compose -f docker-compose.production.yml up -d
```
Произойдет скачивание образов, создание и включение контейнеров, создание томов и сети.

### Запуск проекта локально 

Клонируем себе репозиторий:

```
git clone https://github.com/ErendzhenovBair/foodgram-project-react.git
```
Cоздаем и активируем виртуальное окружение:

Команда для установки виртуального окружения на Mac или Linux:

```bash
   python3 -m venv env
   source env/bin/activate
```

Команда для Windows:

```bash
   python -m venv venv
   source venv/Scripts/activate
```

Устанавливаем зависимости из файла requirements.txt:

```bash
   cd ..
   cd backend
   pip install -r requirements.txt
```

- Перейти в директорию infra:

```bash
   cd infra
```
- Выполнить команду для доступа к документации:

```bash
   docker-compose up 
```

### После запуска: Миграции, сбор статистики

После запуска необходимо выполнить сбор статистики и миграции бэкенда. Статистика фронтенда собирается во время запуска контейнера, после чего он останавливается.
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend cp -r /app/static/. /backend_static/static/
```
#### Документация к API доступна по адресу <http://localhost/api/docs/> после локального запуска проекта

После этого проект доступен на:
```
https://myfoodgram790.hopto.org
```

### Остановка контейнеров

В окне, где был запуск Ctrl+С или в другом окне:
```
sudo docker compose -f docker-compose.yml down
```

### Заполнение env

Для проекта Foodgram секреты подключаются из файла .env. 
Создайте файл .env и заполните его своими данными. Перечень данных указан в корневой директории проекта в файле .env.example .env.

Проект доступен по адресу: <https://myfoodgram790.hopto.org/>


#### Установка на удалённом сервере

- Выполнить вход на удаленный сервер
- Установить docker:

```bash
   sudo apt install docker.io
   ```

- Установить docker-compose:

``` bash
    sudo apt install docker-compose     
```

- Находясь локально в директории infra/, скопировать файлы docker-compose.production.yml и nginx.conf на удаленный сервер.

- Находясь на сервере создайте директорию foodgram и перейдите в нее.
```
mkdir foodgram
cd foodgram
```

- После этого запускайте сервис и выполните миграции.
```
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python3 manage.py migrate
```
- Суперпользователя можно создать следующей командой.
```
sudo docker compose -f docker-compose.production.yml exec backend python3 manage.py createsuperuser
```

#### Полный список запросов API находятся в документации

Доступ в админку:

```bash
   email - admin@mail.ru
   пароль - abc12345
```
### Автор проекта

Автор этого проекта - Эрендженов Баир. 
Если у вас есть вопросы, предложения или просто поделитесь своим мнением о проекте, не стесняйтесь обращаться ко мне.
- Электронная почта: erendzhenovbair1990@yandex.ru
- Telegram: @BairErendzhenov