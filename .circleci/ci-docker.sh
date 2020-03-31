#!/usr/bin/env bash
set -e

echo "$DOCKER_PASSWORD" | docker login -u $DOCKER_USERNAME --password-stdin
docker build -t sonatypecommunity/iq-success-metrics:$CIRCLE_TAG .
docker tag sonatypecommunity/iq-success-metrics:$CIRCLE_TAG sonatypecommunity/iq-success-metrics:latest
docker push sonatypecommunity/iq-success-metrics
