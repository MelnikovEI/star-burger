#!/bin/bash
set -e

steps=10

git pull
echo  1/$steps: Код обновлён

./venv/bin/pip3 install -r requirements.txt
echo  2/$steps: Библиотеки python установлены

npm ci --dev
echo  3/$steps: Библиотеки Node.js установлены

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
echo  4/$steps: Сборка JS завершена

./venv/bin/python3 manage.py collectstatic --noinput
echo  5/$steps: Статика пересобрана

./venv/bin/python3 manage.py migrate --noinput
echo  6/$steps: Миграции БД завершены

systemctl restart star-burger.service
echo  7/$steps: Служба сайта перезапущена

systemctl reload nginx.service
echo  8/$steps: Сервер перезапущен
echo  Успех, сайт обновлён!