# bond
Account linking service

# Running Tests
* pip install nose nosegae nose-exclude
* nosetests --with-gae --gae-lib-root=`gcloud info --format="value(installation.sdk_root)"`/platform/google_appengine --exclude-dir=lib