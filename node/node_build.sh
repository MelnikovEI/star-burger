#!/bin/bash
set -e
cd "$(dirname "$0")"
docker build -t="star_burger_node" .
container_id=$(docker create star_burger_node)
docker cp $container_id:/usr/app/bundles .
docker rm -v $container_id
docker rmi star_burger_node
