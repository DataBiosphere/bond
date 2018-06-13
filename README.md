# bond
Account linking service

# Running Tests
* `pip install nose nosegae nose-exclude`
* ```nosetests --with-gae --gae-lib-root=`gcloud info --format="value(installation.sdk_root)"`/platform/google_appengine --exclude-dir=lib```

# Running locally in Docker
* `docker run -p=8080:8080 -p=8000:8000 quay.io/databiosphere/bond:latest`
