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
