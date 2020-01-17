FROM python:2.7.15

# Prepare the image
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
    && apt-get install -y -qq --no-install-recommends wget tar build-essential openssh-client python-openssl \
    && apt-get clean

# Install the Google Cloud SDK
ENV HOME /
ENV CLOUDSDK_PYTHON_SITEPACKAGES 1
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > google-cloud-sdk.tar.gz \
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

# Install dependencies and set the PYTHONPATH appropriately so that dependencies can be found by the runtime
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -t lib/ -r requirements.txt
ENV PYTHONPATH /app/lib

# Copy the source files into the the container
COPY . .

# Bond Endpoints available on port 8080.  Admin interface not exposed
EXPOSE 8080
ENTRYPOINT ["dev_appserver.py", "--host=0.0.0.0", "--enable_host_checking=false", "."]
