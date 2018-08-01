# bond
Account linking service

# Running Tests

Bond supports test runners: [unittest](https://docs.python.org/2/library/unittest.html) and 
[nose](https://github.com/Trii/NoseGAE) 

## Unittest

* Determine the path to your Google SDK installation by running: `gcloud info --format="value(installation.sdk_root)"`
* From the Bond root directory: `python tests/test_runner.py {path-to-google-sdk}`

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
  broadinstitute/dsde-toolbox render-templates.sh
```
  
For non-Broad, manually edit the config.ini and app.yaml files in the root of the project to use your desired values.

Then choose one of the options below:

a) To run an existing image:

1) Browse the available tags [here](https://quay.io/repository/databiosphere/bond?tag=latest&tab=tags)
2) With your tag of choice, run `docker run -v $PWD/config.ini:/app/config.ini -p=8080:8080 -p=8000:8000 quay.io/databiosphere/bond:{TAG}`
3) Check http://localhost:8080/api/status/v1/ to make sure you're up and running

b) Run your local code:

1) Build your image: `docker build -f docker/Dockerfile .`
2) Grab the Image ID and run: `docker run -v $PWD/config.ini:/app/config.ini -p=8080:8080 -p=8000:8000 {IMAGE_ID}`
3) Check http://localhost:8080/api/status/v1/ to make sure you're up and running

# Deployment (for Broad only)

`dev` environment (branch: `develop`):
1) Merge to `develop` branch
2) Jenkins will kick off a deploy to the `dev` environemnt
3) CircleCI will run unit tests against `develop`. If tests pass, `develop` will be tagged with the tag name `dev_tests_passed_<TIMESTAMP>`

`alpha` environment (branch: `alpha`):
1) Choose the latest tag that you want to release
2) `get fetch --tags origin`
3) `git checkout alpha`
4) `git merge dev_tests_passed_<TIMESTAMP>`
5) `git checkout -b dev_tests_passed_<TIMESTAMP>_release`
6) `git push --set-upstream origin dev_tests_passed_<TIMESTAMP>_release`
7) Open a PR merging your `dev_tests_passed_<TIMESTAMP>_release` branch into the `alpha` branch
8) Jenkins will kick off a deploy to the `alpha` environemnt


`staging` environment (branch: `staging`):
1) Open a PR merging your `dev_tests_passed_<TIMESTAMP>_release` branch into the `staging` branch
2) Jenkins will kick off a deploy to the `staging` environment

`prod` environment (branch: `master`):
1) Open a PR merging your `dev_tests_passed_<TIMESTAMP>_release` branch into the `master` branch
2) Jenkins will kick off a deploy to the `prod` environment

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