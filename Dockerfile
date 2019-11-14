ARG ALT_DOCKER_REGISTRY=docker.io
FROM $ALT_DOCKER_REGISTRY/python:3

WORKDIR /usr/src/app

ARG ALT_PYPI_REGISTRY=https://pypi.org/simple
RUN pip3 install -v --trusted-host host.docker.internal --no-cache-dir --index-url $ALT_PYPI_REGISTRY requests

COPY . .
ENTRYPOINT ["python3", "./success_metrics.py"]
CMD ["-h"]
