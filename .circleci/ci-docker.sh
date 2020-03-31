#!/usr/bin/env bash
set -e

docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
docker build -t sonatypecommunity/iq-success-metrics:$CIRCLE_TAG .
docker tag sonatypecommunity/iq-success-metrics:$CIRCLE_TAG sonatypecommunity/iq-success-metrics:latest
docker push sonatypecommunity/iq-success-metrics
