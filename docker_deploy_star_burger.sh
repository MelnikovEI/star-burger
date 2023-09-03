#!/bin/bash
set -e

steps=6

echo ---Обновление кода---
git pull
echo  1/$steps: Код обновлён

echo ---Сборка frontend---
./node/node_build.sh
echo  2/$steps: Сборка frontend завершена

echo ---Cборка образов---
docker-compose -f docker-compose.prod.yml build
echo  3/$steps: Образы созданы

echo ---Запуск контейнеров---
docker-compose -f docker-compose.prod.yml up -d
echo  4/$steps: Контейнеры запущены

echo ---Миграции БД---
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
echo  5/$steps: Миграции БД завершены

echo ---Сборка статики django---
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear
echo  6/$steps: Статика пересобрана


echo ---Завершено---