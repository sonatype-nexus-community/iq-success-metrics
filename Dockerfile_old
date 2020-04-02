ARG ALT_DOCKER_REGISTRY=quay.io
FROM $ALT_DOCKER_REGISTRY/plotly/orca

WORKDIR /usr/src/app

# Upgrade Installed Packages
RUN apt-get update && apt install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && apt-get update

# Install Python3.7, Pip3, Python3.7-dev and gcc
RUN apt-get install -y gcc && apt install -y python3.7 && apt install -y python3-pip && apt-get install -y python3.7-dev

# Register the version in alternatives
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

# Set python 3 as the default python
RUN update-alternatives --set python3 /usr/bin/python3.7

#ARG ALT_PYPI_REGISTRY=https://pypi.org/simple
COPY requirements.txt ./
RUN pip3 install --user --no-cache-dir -r requirements.txt
#RUN conda install --file requirements.txt


COPY . .
ENTRYPOINT ["python3"]
CMD ["success_metrics.py", "-h"]
