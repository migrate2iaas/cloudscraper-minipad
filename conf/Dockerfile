FROM ubuntu:latest
# Download java 
RUN apt-get -qq update
RUN apt-get install curl -qq -y
RUN apt-get install python -qq -y
RUN apt-get -y install gcc python-dev libxml2-dev libxslt-dev git python-setuptools zlib1g-dev
RUN easy_install pip
RUN install lxml
RUN install shortuuid
RUN pip install psutil
RUN git clone https://git.assembla.com/cloudscraper.minpad.git

# Dockerfile to be applied to standard Ubuntu docker image
# it downloads and installs recovery agent to the image


# downloading the latest agent script
ENTRYPOINT python ./cloudscraper.minpad/src/server.py


