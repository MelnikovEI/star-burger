#!/bin/bash
set -e

steps=8

echo ---Обновление кода---
git pull
echo  1/$steps: Код обновлён

echo ---Установка библиотек python---
./venv/bin/pip3 install -r requirements.txt
echo  2/$steps: Библиотеки python установлены

echo ---Установка библиотек node.js---
npm ci --dev
echo  3/$steps: Библиотеки Node.js установлены

echo ---Сборка JS---
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
echo  4/$steps: Сборка JS завершена

echo ---Сборка статики django---
./venv/bin/python3 manage.py collectstatic --noinput
echo  5/$steps: Статика пересобрана

echo ---Миграции БД---
./venv/bin/python3 manage.py migrate --noinput
echo  6/$steps: Миграции БД завершены

echo ---Перезапуск службы сайта---
systemctl restart star-burger.service
echo  7/$steps: Служба сайта перезапущена

echo ---Перезапуск сервера---
systemctl reload nginx.service
echo  8/$steps: Сервер перезапущен
echo  Успех, сайт обновлён!


echo ---Регистрация deploy в сервисе Rollbar---
commit_hash=$(git rev-parse HEAD)
source .env
export ROLLBAR_ACCESS_TOKEN

curl --http1.1 -X POST \
  https://api.rollbar.com/api/1/deploy \
  -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"environment": "production", "revision": "'"$commit_hash"'", "local_username": "'"$USER"'", "comment": "Deployed new version", "status": "succeeded"}'

echo ---Завершено---