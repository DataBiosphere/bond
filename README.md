# Bond

Service for linking [Sam](https://github.com/broadinstitute/sam) User accounts with registered 3rd party services via
Oauth2. Bond is a Flask application written in Python 3.7 deployed on Google App Engine.

# Setup

In order to run tests or run the local development app server, you need to install Python 3.7, Pip, and [Google Cloud SDK](https://cloud.google.com/sdk/install).

## Virtualenv

[Virtualenv](https://virtualenv.pypa.io/en/stable/) is a tool that helps you manage multiple Python versions and your 
project dependencies.  We recommend you setup Virtualenv for development and testing of Bond.

1. Verify that you have Python 3.7 installed: `python --version`
(**Note**: The name of your Python 3.7 command may be something different like `python3` if you have multiple versions 
of Python installed)
1. Install virtualenv: `pip install virtualenv`
1. `cd` to the Bond root directory
1. Set up virtualenv for Bond: `virtualenv -p python env` 
(**Note**: Ensure that you pass the correct Python 3.7 executable to the [`-p` parameter](https://virtualenv.pypa.io/en/stable/reference/#cmdoption-p)) 
1. Activate virtualenv: `source env/bin/activate`
1. Install project dependencies: `pip install -r requirements.txt --ignore-installed`

You may now run tests or run the application server normally.

When you are ready to exit or deactivate your Bond virtualenv, just type the command `deactivate` on your command line.


# Running Tests

Bond has unit tests, integration tests, and automation tests. 

Bond supports test runners: [unittest](https://docs.python.org/3/library/unittest.html).

## Unit tests

`python -m unittest discover -s tests/unit -p "*_test.py"`

When writing new tests, do not put any tests in the root `tests/` directory.  Instead, write new unit tests in the 
`tests/unit` directory.

## Integration tests

To run integration tests, provide the `test-path` parameter to with the path to the integration tests:

`python -m unittest discover -s tests/integration -p "*_test.py"`

When writing new tests, do not put any tests in the root `tests/` directory.  Instead, write new integration tests in 
the `tests/integration` directory.

## Datastore Emulator tests
To run the integration tests that require the Datastore emulator locally, follow [the instructions in the readme](tests/datastore_emulator/README.md). 

# Running locally

## Render configs

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

### Run locally
After installing project dependencies, rendering configs, and setting up paths, start up a Datastore Emulator. We need
the emulator so that our local runs have a Datastore backend to talk to, and we do not want them to talk to real Google
Datastores.

Note that the following script must be run from a python2 virtualenv environment. See
[tests/datastore_emulator/README.md](tests/datastore_emulator/README.md)

```tests/datastore_emulator/run_emulator.sh```

Then, start a local flask server.

```run_local.sh```

You can check [http://127.0.0.1:8080/api/status/v1/status](http://127.0.0.1:8080/api/status/v1/status) to make sure you're up and running.

You can also check [http://0.0.0.0:8432](http://0.0.0.0:8432) which should show 'Ok' if the datastore emulator is working properly.


## Run in a Docker container

First, render configs (see above). If you try to run the docker compose before rendering, subsequent rendering may not
work. `docker-compose` may create directories when it tries to access configuration files that do not exist. Try
removing created directories (e.g. remove `config.ini` which should be created from `config.ini.ctmpl`) and
re-rendering.

Choose one of the options below:

A) To run an existing image:

1) Render configs.
2) Browse the available tags [here](https://quay.io/repository/databiosphere/bond?tag=latest&tab=tags)
3) With your tag of choice (such as `develop`), run `IMAGE_ID=quay.io/databiosphere/bond:{TAG} docker-compose -f docker/local-docker-compose.yml up`
4) Check http://127.0.0.1:8080/api/status/v1/status to make sure you're up and running

B) Run your local code:

1) Render configs.
2) Build your image: `docker build -f docker/Dockerfile .`
3) Grab the Image ID and run: `IMAGE_ID={your image id} docker-compose -f docker/local-docker-compose.yml up`
4) Check http://127.0.0.1:8080/api/status/v1/status to make sure you're up and running

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

## Production Deployment Checklist

When doing a production deployment, each step of the checklist must be performed.

### Production Deployment Preparation

- [ ] When the latest code passes tests in CircleCI, it is tagged `dev_tests_passed_[timestamp]` where `[timestamp]` is the
      epoch time when the tag was created.  Confirm that this tag was created for the commit you wish to deploy.
- [ ] Create and push a new [semver](https://semver.org/) tag for this same commit.  You should look at the existing tags 
      to ensure that the tag is incremented properly based on the last released version.  Tags should be plain semver numbers 
      like `1.0.0` and should not have any additional prefix like `v1.0.0` or `releases/1.0.0`.  Suffixes are permitted so 
      long as they conform to the [semver spec](https://semver.org/).
- [ ] In Jira, make sure the Bond Release exists or create a new one in the [Cloud Integration Project](https://broadworkbench.atlassian.net/projects/CA?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page)
      named like: `Bond-X.Y.Z` where `X.Y.Z` is the same semantic version number you created in the previous step.
- [ ] For each Jira Issue included in this release, set the `Fix Version` field to the release name you created in the
      previous step.  The status of each of these issues should be: "Merged to Dev".  If the status is something else,
      then either: the issue should not be included in the release, the release is not ready, or the issue has already 
      been released.

### Deploy and Test
You must deploy to each tier one-by-one and [manually test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
in each tier after you deploy to it.  Your deployment to a tier should not be considered complete until you have 
successfully executed each step of the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
on that tier.  To deploy the application code, navigate to the [Bond Manual Deploy](https://fc-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/)
job and click the "Build with Parameters" link.  Select the `TAG` that you just created during the preparation steps and
the `TIER` to which you want to deploy:
    
- [ ] `dev` deploy job succeeded and [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#) passed 
      - (Technically, this same commit is probably already running on `dev` courtesy of the automatic `dev` deployment 
      job. However, deploying again is an important step because someone else may have triggered a `dev` deployment and 
      we want to ensure that you understand the deployment process, the deployment tools are working properly, and that 
      everything is working as intended.)
- [ ] `alpha` deploy job succeeded and [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#) passed
- [ ] `staging` deploy job succeeded and [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#) passed
- [ ] `prod` deploy job succeeded and [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#) passed
      - In order to deploy to `prod`, you must be on the DSP Suitability Roster.  You will need to log into the 
      production Jenkins instance and use the "Bond Manual Deploy" job to release the same tag to production.

**NOTE:** 
* It is important that you deploy to all tiers.  Because Bond is an "indie service", we should strive to make sure
that all tiers other than `dev` are kept in sync and are running the same versions of code.  This is essential so that
as other DSP services are tested during their release process, they can ensure that their code will work properly with 
the latest version of Bond running in `prod`. 

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
