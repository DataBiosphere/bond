#!/usr/bin/env bash
set -e
set -x

VAULT_TOKEN=$1
GIT_BRANCH=$2

#need to get the environment from the branch name
if [ "$GIT_BRANCH" == "develop" ]; then
	ENVIRONMENT="dev"
elif [ "$GIT_BRANCH" == "alpha" ]; then
        ENVIRONMENT="alpha"
elif [ "$GIT_BRANCH" == "staging" ]; then
	ENVIRONMENT="staging"
elif [ "$GIT_BRANCH" == "master" ]; then
	ENVIRONMENT="prod"
else
	echo "Unknown Git branch $GIT_BRANCH"
	exit 1
fi

GOOGLE_PROJECT=broad-bond-$ENVIRONMENT

#pull the credentials for the service account
docker run --rm -e VAULT_TOKEN=$VAULT_TOKEN broadinstitute/dsde-toolbox vault read --format=json "secret/dsde/bond/$ENVIRONMENT/deploy-account.json" | jq .data > deploy_account.json

#build the docker image so we can deploy
docker build -f docker/Dockerfile -t databiosphere/bond:deploy .

#render the endpoints json and then deploy it
docker run -v $PWD/startup.sh:/app/startup.sh \
    -v $PWD/output:/output \
    -v $PWD/deploy_account.json:/deploy_account.json \
    -e GOOGLE_PROJECT=$GOOGLE_PROJECT \
    databiosphere/bond:deploy /bin/bash -c \
    "gcloud auth activate-service-account --key-file=deploy_account.json; python lib/endpoints/endpointscfg.py get_openapi_spec main.BondApi --hostname $GOOGLE_PROJECT.appspot.com; gcloud -q endpoints services deploy linkv1openapi.json --project $GOOGLE_PROJECT"

#SERVICE_VERSION in app.yaml needs to match this
#SERVICE_VERSION=`gcloud endpoints services describe $GOOGLE_PROJECT.appspot.com --format=json --project $GOOGLE_PROJECT | jq .serviceConfig.id` #todo: gcloud returns different response when calling as a service account and google doesn't know why
SERVICE_VERSION=`date +%Y-%m-%d`r0 #todo: until google fixes the above gcloud command, we will use this. it will work a max of once per day (because it only uses r0 for each date)

#render config.ini and app.yaml for environment with SERVICE_VERSION and GOOGLE_PROJECT
docker run -v $PWD:/app \
  -e GOOGLE_PROJ=$GOOGLE_PROJECT \
  -e SERVICE_VERSION=$SERVICE_VERSION \
  -e INPUT_PATH=/app \
  -e OUT_PATH=/app \
  -e VAULT_TOKEN=$VAULT_TOKEN \
  -e ENVIRONMENT=$ENVIRONMENT \
  broadinstitute/dsde-toolbox render-templates.sh

#deploy the app to the specified project
docker run -v $PWD/startup.sh:/app/startup.sh \
    -v $PWD/app.yaml:/app/app.yaml \
    -v $PWD/config.ini:/app/config.ini \
    -v $PWD/deploy_account.json:/deploy_account.json \
    -e GOOGLE_PROJECT=$GOOGLE_PROJECT \
    databiosphere/bond:deploy /bin/bash -c \
    "gcloud auth activate-service-account --key-file=deploy_account.json; gcloud -q app deploy app.yaml --project=$GOOGLE_PROJECT"
