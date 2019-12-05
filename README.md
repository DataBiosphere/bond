# Bond

Service for linking [Sam](https://github.com/broadinstitute/sam) User accounts with registered 3rd party services via
Oauth2. Bond is a [Google Endpoints](https://cloud.google.com/endpoints/) application written in Python 2.7.

# Setup

In order to run tests or run the local development app server, you need to install Python 2.7, Pip, and [Google Cloud SDK](https://cloud.google.com/sdk/install).

## Virtualenv

[Virtualenv](https://virtualenv.pypa.io/en/stable/) is a tool that helps you manage multiple Python versions and your 
project dependencies.  We recommend you setup Virtualenv for development and testing of Bond.

1. Verify that you have Python 2.7 installed: `python --version`
(**Note**: The name of your Python 2.7 command may be something different like `python2` if you have multiple versions 
of Python installed)
1. Install virtualenv: `pip install virtualenv`
1. `cd` to the Bond root directory
1. Set up virtualenv for Bond: `virtualenv -p python env` 
(**Note**: Ensure that you pass the correct Python 2.7 executable to the [`-p` parameter](https://virtualenv.pypa.io/en/stable/reference/#cmdoption-p)) 
1. Activate virtualenv: `source env/bin/activate`
1. Install project dependencies: `pip install -r requirements.txt -t lib --ignore-installed`

You may now run tests or run the application server normally.

When you are ready to exit or deactivate your Bond virtualenv, just type the command `deactivate` on your command line.


# Running Tests

Bond supports test runners: [unittest](https://docs.python.org/2/library/unittest.html) and 
[nose](https://github.com/Trii/NoseGAE) 

## Unittest

There is a custom test runner created following the [gcloud documentation](https://cloud.google.com/appengine/docs/standard/python/tools/localunittesting#Python_Setting_up_a_testing_framework)

To run the tests you need to have the Google SDK installed and you need to pass the installation path to the test runner:

`python tests/test_runner.py $(gcloud info --format="value(installation.sdk_root)")`

When writing new tests, do not put any tests in the root `tests/` directory.  Instead, write new unit tests in the 
`tests/unit` directory.

## Integration tests

To run integration tests, provide the `test-path` parameter to with the path to the integration tests:

`python tests/test_runner.py $(gcloud info --format="value(installation.sdk_root)") --test-path=tests/integration`

When writing new tests, do not put any tests in the root `tests/` directory.  Instead, write new integration tests in 
the `tests/integration` directory.

## Nose
* `pip install nose nosegae nose-exclude`
* ```nosetests --with-gae --gae-lib-root=`gcloud info --format="value(installation.sdk_root)"`/platform/google_appengine --exclude-dir=lib```

# Running locally

## Docker

Before you run locally, you will need to render configs:

For Broad devs:

```
docker run -v $PWD:/app \
  -e GOOGLE_PROJ=broad-bond-dev \
  -e SERVICE_VERSION=2016-08-01r0 \
  -e INPUT_PATH=/app \
  -e OUT_PATH=/app \
  -e VAULT_TOKEN=$(cat ~/.vault-token) \
  -e ENVIRONMENT=dev \
  -e RUN_CONTEXT=local \
  -e DNS_DOMAIN=local \
  broadinstitute/dsde-toolbox:master render-templates.sh
```
  
For non-Broad, manually edit the config.ini and app.yaml files in the root of the project to use your desired values.

## Run on your local environment

After installing project dependencies and rendering configs, run the following command from the Bond root directory:

```dev_appserver.py .```

## Run in a Docker container

Choose one of the options below:

a) To run an existing image:

1) Browse the available tags [here](https://quay.io/repository/databiosphere/bond?tag=latest&tab=tags)
2) With your tag of choice, run `docker run -v $PWD/config.ini:/app/config.ini -v $PWD/app.yaml:/app/app.yaml -p=8080:8080 quay.io/databiosphere/bond:{TAG}`
3) Check http://localhost:8080/api/status/v1/status to make sure you're up and running

b) Run your local code:

1) Build your image: `docker build -f docker/Dockerfile .`
2) Grab the Image ID and run: `docker run -v $PWD/config.ini:/app/config.ini -v $PWD/app.yaml:/app/app.yaml -p=8080:8080 {IMAGE_ID}`
3) Check http://localhost:8080/api/status/v1/status to make sure you're up and running

# Deployment (for Broad only)

Deployments to non-production and production environments are performed in Jenkins.  In order to access Jenkins, you
will need to be on the Broad network or logged on to the Broad VPN.

## Deploy to the "dev" environment

A deployment to `dev` environment will be automatically triggered every time there is a commit or push to the 
[develop](https://github.com/DataBiosphere/bond/tree/develop) branch on Github.  If you would like to deploy a different 
branch or tag to the `dev` environment, you can do so by following the instructions below, but be aware that a new
deployment of the `develop` branch will be triggered if anyone commits or pushes to that branch.

## Deploy to non-production environments

1. Log in to [Jenkins](https://fc-jenkins.dsp-techops.broadinstitute.org/) 
1. Navigate to the [bond-manual-deploy](https://fc-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/)
   job
1. In the left menu, click [Build with Parameters](https://fc-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/build?delay=0sec)
   and select the `BRANCH_OR_TAG` that you want to deploy, the `TARGET` environment to which you want to deploy, and enter
   the `SLACK_CHANNEL` that you would like to receive notifications of the deploy jobs success/failure  
1. Click the `Build` button

## Deploy to the "prod" environment

Production deployments are very similar to deployments for any other environment.  The few differences are that you may 
only deploy to Production from the prod Jenkins instance, and you are only allowed to deploy tags, not branches.

1. Create a `git tag` for the commit that you want to release and push it to the [Bond repository on Github](https://github.com/DataBiosphere/bond)
1. Log in to [Prod Jenkins](https://fcprod-jenkins.dsp-techops.broadinstitute.org/)
1. Navigate to the [bond-manual-deploy](https://fcprod-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/)
   job
1. In the left menu, click [Build with Parameters](https://fcprod-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/build?delay=0sec)
   and select the `TAG` that you want to deploy, select `prod` as the `TARGET` environment to which you want to deploy, 
   and enter the `SLACK_CHANNEL` that you would like to receive notifications of the deploy 
   jobs success/failure  
1. Click the `Build` button

# Git Secrets

To run Bond you will need to modify `config.ini` to contain a few secrets that should never be committed into git.  To 
help protect you from accidentally committing secrets, we recommend that you download and install 
[git-secrets](https://github.com/awslabs/git-secrets).

Once installed, you can add the following patterns:

```
git secrets --add 'CLIENT_ID\s*=\s*.+'
git secrets --add 'CLIENT_SECRET\s*=\s*.+'
git secrets --add --allowed 'REPLACE_ME'
git secrets --add --allowed '\{\{ \$fenceSecrets\.Data\.client_id \}\}'
git secrets --add --allowed '\{\{ \$fenceSecrets\.Data\.client_secret \}\}'
```
