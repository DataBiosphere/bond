FROM python:2.7.15

# Prepare the image
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y -qq --no-install-recommends wget unzip python python-pip python-dev build-essential openssh-client python-openssl curl && apt-get clean

# Install the Google Cloud SDK
ENV HOME /
ENV CLOUDSDK_PYTHON_SITEPACKAGES 1
RUN wget https://dl.google.com/dl/cloudsdk/channels/rapid/google-cloud-sdk.zip && unzip google-cloud-sdk.zip && rm google-cloud-sdk.zip
RUN google-cloud-sdk/install.sh --usage-reporting=true --path-update=true --bash-completion=true --rc-path=/.bashrc --additional-components app-engine-python app cloud-datastore-emulator app-engine-python-extras

RUN mkdir /.ssh
ENV PATH /google-cloud-sdk/bin:$PATH
VOLUME ["/.config"]

ADD . app/
WORKDIR app/
RUN pip install -t lib/ -r requirements.txt

EXPOSE 8080 8000
CMD ["dev_appserver.py", "--host=0.0.0.0", "."]
