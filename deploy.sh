#!/usr/bin/env bash
set -e
set -x

VAULT_TOKEN=$1
GIT_BRANCH=$2

#need to get the environment from the branch name
if [ "$GIT_BRANCH" == "develop" ] || [ "$GIT_BRANCH" == "mb-deploy-sh" ]; then
	ENVIRONMENT="dev"
elif [ "$GIT_BRANCH" == "staging" ]; then
	ENVIRONMENT="staging"
elif [ "$GIT_BRANCH" == "master" ]; then
	ENVIRONMENT="prod"
else
	echo "Unknown Git branch $GIT_BRANCH"
	exit 1
fi

GOOGLE_PROJECT=broad-bond-$ENVIRONMENT

docker run --rm -e VAULT_TOKEN=$VAULT_TOKEN broadinstitute/dsde-toolbox vault read --format=json "secret/dsde/bond/$ENVIRONMENT/deploy-account.json" | jq .data > deploy_account.json

#activate as a service account that has the App Engine Deployer role
gcloud auth activate-service-account --key-file=deploy_account.json

# render the .ini
docker run -v $PWD:/app \
  -e INPUT_PATH=/app/configs-pre \
  -e OUT_PATH=/app/output \
  -e VAULT_TOKEN=$VAULT_TOKEN \
  -e ENVIRONMENT=$ENVIRONMENT \
  broadinstitute/dsde-toolbox render-templates.sh

#render the endpoints json
docker build -f docker/Dockerfile -t databiosphere/bond:deploy
docker run -v $PWD/output/config.ini:/app/config.ini \
    -v $PWD/startup.sh:/app/startup.sh \
    -v $PWD/output:/output \
    -e GOOGLE_PROJECT=$GOOGLE_PROJECT \
    databiosphere/bond:deploy /bin/bash -c "python lib/endpoints/endpointscfg.py get_openapi_spec main.BondApi --hostname $GOOGLE_PROJECT.appspot.com; cp linkv1openapi.json /output"


#deploy google endpoints
gcloud -q endpoints services deploy output/linkv1openapi.json --project $GOOGLE_PROJECT

SERVICE_VERSION="dummy"

#SERVICE_VERSION in app.yaml needs to match this
#NOTE: this is the proper way to do this. But for some reason gcloud doesn't output the full details of the service when using a service account.
#SERVICE_VERSION=`gcloud endpoints services describe $GOOGLE_PROJECT.appspot.com --format=json --project $GOOGLE_PROJECT | jq .serviceConfig.id`

#render app.yaml and config.ini for environment with SERVICE_VERSION and GOOGLE_PROJECT
docker run -v $PWD:/app \
  -e GOOGLE_PROJ=$GOOGLE_PROJECT \
  -e SERVICE_VERSION=$SERVICE_VERSION \
  -e INPUT_PATH=/app/configs-post \
  -e OUT_PATH=/app/output \
  -e VAULT_TOKEN=$VAULT_TOKEN \
  -e ENVIRONMENT=$ENVIRONMENT \
  broadinstitute/dsde-toolbox render-templates.sh

cp output/app.yaml .
cp output/config.ini .

CONTAINER_ID=`docker create databiosphere/bond:deploy`

docker cp $CONTAINER_ID:/app/lib .

#deploy the app to the specified project
gcloud -q app deploy app.yaml --project=$GOOGLE_PROJECT
