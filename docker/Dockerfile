FROM python:3.7.4

# Prepare the image
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
    && apt-get install -y -qq --no-install-recommends wget tar build-essential openssh-client python-openssl python3-pip \
    && apt-get clean

# Install the Google Cloud SDK
ENV HOME /
ENV CLOUDSDK_PYTHON_SITEPACKAGES 1
RUN wget -O google-cloud-sdk.tar.gz https://storage.googleapis.com/cloud-sdk-release/google-cloud-sdk-276.0.0-linux-x86.tar.gz \
    && tar -xzf google-cloud-sdk.tar.gz \
    && google-cloud-sdk/install.sh \
        --usage-reporting=true --path-update=true --bash-completion=true --rc-path=/.bashrc --additional-components \
        app-engine-python app cloud-datastore-emulator app-engine-python-extras

RUN mkdir /.ssh
ENV PATH /google-cloud-sdk/bin:$PATH
VOLUME ["/.config"]

# Create directory for Bond in the container
RUN mkdir /app
WORKDIR app/

# Install dependencies.
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Copy the source files into the the container
COPY . .

# Bond Endpoints available on port 8080.  Admin interface not exposed
EXPOSE 8080
ENV FLASK_APP main.py
CMD flask run -h 0.0.0.0 -p 8080
