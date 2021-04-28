# Bond

Service for linking [Sam](https://github.com/broadinstitute/sam) User accounts with registered 3rd party services via
Oauth2. Bond is a Flask application written in Python 3.7 deployed on Google App Engine.

# Swagger/OpenAPI Interface

The only user interface that Bond makes available is a Swagger UI for directly interacting with its endpoints.  The UI 
can be reached at the path:

`http://{your_host}/api/docs/`

## Authorization 
For endpoints that require authorization, you will need a Google Access Token that you can generate using the 
[gcloud](https://cloud.google.com/sdk/gcloud) command:

`gcloud auth print-access-token`

When you "authorize" in the Bond Swagger UI:

1. Click the `Authorize` button at the top right of the Swagger UI
1. Copy/paste the generated Access Token from the gcloud CLI into `Value` field
1. Click the `Authorize` button

Your token will authorize you to make requests for about 30 minutes, at which point you will need to repeat the 
authorization process.

# Setup

In order to run tests or run the local development app server, you need to install Python 3.7, Pip, and [Google Cloud SDK](https://cloud.google.com/sdk/install).

If you need to have multiple Python versions installed, we recommend using [pyenv](https://github.com/pyenv/pyenv).

## Virtualenv

[Virtualenv](https://virtualenv.pypa.io/en/stable/) is a tool that helps you manage multiple Python versions and your 
project dependencies.  We recommend you setup Virtualenv for development and testing of Bond.  If you are using 
[pyenv](https://github.com/pyenv/pyenv), be sure to specify to set that up prior to configuring virtualenv for Bond.  

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

### In IntelliJ

Follow the [instructions](https://www.jetbrains.com/help/idea/creating-virtual-environment.html) on the JetBrains site.

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

### Integration testing with real providers
Integration tests are written to be run against the [mock provider service](https://github.com/broadinstitute/mock-provider).
The mock provider service skips the authentication step of the oauth dance in order to make testing easier.  

If you want to test against _real_ providers, do the following:

1. Update `config.ini` to have all the requisite data for the real providers
1. At the top of `tests/integration/oauth_adapter_test.py`, set the variable `using_mock_providers =
False`. 
1. Run the Integration Tests the same way as described above.  The tests will stop and print instructions and a link to 
authenticate with each provider.  Follow the instructions and copy/paste the `auth_code` into the command line for each 
provider to complete the oauth dance.

Because the test execution will become an interactive experience, you **_must_** run these tests in an environment
where you can provide the required command line inputs.  In other words, you won't be able to run tests this way on a 
build server, but you will be able to run them in your local environment.

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

### Run locally from IntelliJ

These instructions are for running the app in IntelliJ specifically, not PyCharm.

- Go to `Run` -> `Edit Configurations` -> `Add New Configuration` -> `Flask Server`
- For `Target Type` choose: `Module Name`
- In the `Target` field enter: `main.py`
- Leave the `Application`, `Additional Options`, and `FLASK_ENV` fields blank
- If you want to debug the application, check the `FLASK_DEBUG` checkbox
- In the `Environment variables` field enter: `DATASTORE_EMULATOR_HOST=0.0.0.0:8432;FLASK_HOST=127.0.0.1`
- Click `OK`
- Try running the app by clicking `Run` -> `Run 'Flask (main.py)'` (or by clicking the `Run` button in the Toolbar)

*NOTE* - If you see an error like: `module 'enum' has no attribute 'IntFlag'` when trying to run the Flask Server,  try 
the following:

- Go to `File` -> `Project Structure` -> `Libraries`
- Remove the `Google App Engine` library

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
5) Navigate to http://127.0.0.1:8080/api/docs/ to interact with endpoints via Swagger

B) Run your local code:

1) Render configs.
2) Build your image: `docker build -f docker/Dockerfile .`
3) Grab the Image ID and run: `IMAGE_ID={your image id} docker-compose -f docker/local-docker-compose.yml up`
4) Check http://127.0.0.1:8080/api/status/v1/status to make sure you're up and running
5) Navigate to http://127.0.0.1:8080/api/docs/ to interact with endpoints via Swagger

# Development

This app is written in Python 3 as a Flask application intended to be run in Google App Engine.  It has runtime
dependencies on Google Datastore.

## Logging

Follow standard Python [logging instructions](https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial). 
Logging is configured for our application in `main.py` in the `setup_logging` method.  This method loads a logging
config defined in `log_config.yaml` and among other settings, allows us to specify the log level for specific modules 
and for the application in general.  

In order to use the logging config, you will need to load the right logger for your Python module (or class).  Calling
the logging methods on the `logging` module directly will log messages using the default logger, which is not bad, but 
it is not preferred either.  Instead, you should get the specific logger for your module so that the right configuration
from `log_config.yaml` will be applied to your module.  For example:

```python
import logging

logger = logging.getLogger(__name__)

class MyCoolClass:
    def __init__(self, base_url):
        logger.debug("Constructed an instance of MyCoolClass")

    def do_something(self):
        logger.info("Stuff is happening")

logger.warning("I like turtles")
```

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
- [ ] Pushing the new tag to the git origin repository will _not_ automatically tag the Docker image.  You will need to 
      manually tag the Docker image with the correct semver number.  Go to the [Bond project on Quay.io](https://quay.io/repository/databiosphere/bond?tab=tags)
      and navigate to the "Tags" menu.  You should see two new images for `latest` and `develop`.  Confirm that the ages
      of these images correspond to when you merged your changes into the `develop` branch.  On the right of one of
      these rows, click on the gear icon and select "Add New Tag".  Enter the semver number for your release.
- [ ] In Jira, make sure the Bond Release exists or create a new one in the [Cloud Integration Project](https://broadworkbench.atlassian.net/projects/CA?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page)
      named like: `Bond-X.Y.Z` where `X.Y.Z` is the same semantic version number you created in the previous step.
- [ ] For each Jira Issue included in this release, set the `Fix Version` field to the release name you created in the
      previous step.  The status of each of these issues should be: "Merged to Dev".  If the status is something else,
      then either: the issue should not be included in the release, the release is not ready, or the issue has already 
      been released. Each Jira issue must have a clear description of the change and its security impact.

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
- [ ] In Jira, transition all tickets in the Release to "Done"
- [ ] Navigate to the [Releases Page](https://broadworkbench.atlassian.net/projects/CA?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page)
      in Jira and mark the version as "Released"

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
git secrets --add --allowed 'ignored'
git secrets --add --allowed '\{\{ \$secrets\.Data\.client_id \}\}'
git secrets --add --allowed '\{\{ \$secrets\.Data\.client_secret \}\}'
git secrets --add --allowed '\{\{ \$secrets\.Data\.dcf_fence_client_id \}\}'
git secrets --add --allowed '\{\{ \$secrets\.Data\.dcf_fence_client_secret \}\}'
git secrets --add --allowed '\{\{ \$secrets\.Data\.anvil_client_id \}\}'
git secrets --add --allowed '\{\{ \$secrets\.Data\.anvil_secret \}\}'
```
