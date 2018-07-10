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

# Running locally in Docker
* `docker run -p=8080:8080 -p=8000:8000 quay.io/databiosphere/bond:latest`

# Deployment (for Broad only)

`dev` environment (branch: `develop`):
1) Merge to `develop` branch
2) Jenkins will kick off a deploy to the `dev` environemnt
3) CircleCI will run unit tests against `develop`. If tests pass, `develop` will be tagged with the tag name `dev_tests_passed_<TIMESTAMP>`

`staging` environment (branch: `staging`):
1) Choose the latest tag that you want to release
2) `get fetch --tags origin`
3) `git checkout staging`
4) `git merge dev_tests_passed_<TIMESTAMP>`
5) `git checkout -b dev_tests_passed_<TIMESTAMP>_release`
6) `git push --set-upstream origin dev_tests_passed_<TIMESTAMP>_release`
7) Open a PR merging your `dev_tests_passed_<TIMESTAMP>_release` branch into the `staging` branch
8) Jenkins will kick off a deploy to the `staging` environemnt

`prod` environment (branch: `master`):
1) Open a PR merging your `dev_tests_passed_<TIMESTAMP>_release` branch into the `master` branch
2) Jenkins will kick off a deploy to the `prod` environment
