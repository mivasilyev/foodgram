![main workflow](https://github.com/mivasilyev/foodgram/actions/workflows/main.yml/badge.svg)

## Описание
Дипломный проект студента курса Python-разработчик (Яндекс.Практикум).
Фудграм - сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Установка

Для локального запуска проекта в контейнерах необходимо:

Клонировать его на компьютер и перейти в папку
```
git clone git@github.com:mivasilyev/foodgram.git
cd foodgram
```
создать виртуальное окружение и установить зависимости
```
python3.9 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```
переименовать файл .env.example в .env и прописать переменные окружения
```
mv .env.example .env
nano .env
```
запустить проект
```
sudo docker compose up --build
```
в отдельном окне терминала выполнить миграции и импорт json-фикстур с продуктами и тегами, сбор и копирование статики
```
sudo docker exec foodgram-backend python manage.py migrate
sudo docker exec foodgram-backend python manage.py loaddata tags.json ingredients.json
sudo docker exec foodgram-backend python manage.py collectstatic
sudo docker exec foodgram-backend cp -r /app/backend_static/. /backend_static/static/

```
После запуска проект доступен [здесь](http://localhost/), админ-зона [здесь](http://localhost/admin/).

[Деплой на](https://foodg.run.place/), [админ-зона](https://foodg.run.place/admin/).

## Использованные технологии

При разработке проекта использовались Django, взаимодействие фронтенда и бекэнда осуществляется через api написанное на основе djangorestframework. Работа с пользователями организована на основе djoser, фильтрация на django-filter, за обработку графики отвечает Pillow. База данных - PostgreSQL через psycopg2-binary.

Для развертывания проекта на сервере и автоматизации этого процесса использованы Docker (запуск приложения в контейнерах), Docker Hub (библиотека контейнеров), Github Workflow (инструмент автоматизации развертывания).

Фронтенд с документацией, коллекция Postman-тестов и сервер для деплоя предоставлены Яндекс.Практикумом.

## Автор

[Михаил Васильев](https://github.com/mivasilyev), студент Яндекс.Практикум, 2025.

## Благодарности

Автор выражает благодарность преподавателям, ревьюверам, кураторам и другим причастным к образовательному процессу за возможность пройти этот путь до конца.