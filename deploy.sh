#!/usr/bin/env bash
set -e
set -x

VAULT_TOKEN=$1
GIT_BRANCH=$2
TARGET_ENV=$3

#need to get the environment from the branch name
if [ "$TARGET_ENV" == "dev" ] || [ "$TARGET_ENV" == "develop" ]; then
    ENVIRONMENT="dev"
elif [ "$TARGET_ENV" == "alpha" ]; then
    ENVIRONMENT="alpha"
elif [ "$TARGET_ENV" == "perf" ]; then
    ENVIRONMENT="perf"
elif [ "$TARGET_ENV" == "staging" ]; then
    ENVIRONMENT="staging"
elif [ "$TARGET_ENV" == "prod" ] || [ "$TARGET_ENV" == "master" ]; then
    ENVIRONMENT="prod"
else
    echo "Unknown environment: $TARGET_ENV - must be one of [dev, alpha, perf, staging, prod]"
    exit 1
fi

GOOGLE_PROJECT=broad-bond-${ENVIRONMENT}
BOND_IMAGE=quay.io/databiosphere/bond:${GIT_BRANCH}

#pull the credentials for the service account
docker run --rm -e VAULT_TOKEN=${VAULT_TOKEN} broadinstitute/dsde-toolbox vault read --format=json "secret/dsde/bond/$ENVIRONMENT/deploy-account.json" | jq .data > deploy_account.json

#build the docker image so we can deploy
docker pull ${BOND_IMAGE}

#render the endpoints json and then deploy it
docker run -v $PWD/startup.sh:/app/startup.sh \
    -v $PWD/output:/output \
    -v $PWD/deploy_account.json:/deploy_account.json \
    -e GOOGLE_PROJECT=${GOOGLE_PROJECT} \
    --entrypoint "/bin/bash" \
    ${BOND_IMAGE} \
    -c "gcloud auth activate-service-account --key-file=deploy_account.json; python lib/endpoints/endpointscfg.py get_openapi_spec main.BondApi main.BondStatusApi --hostname $GOOGLE_PROJECT.appspot.com --x-google-api-name; gcloud -q endpoints services deploy linkv1openapi.json statusv1openapi.json --project $GOOGLE_PROJECT"

#SERVICE_VERSION in app.yaml needs to match the output of the curl call below
export BUILD_TMP="${HOME}/deploy-bond-${TARGET_ENV}"
mkdir -p ${BUILD_TMP}
export CLOUDSDK_CONFIG=${BUILD_TMP}

gcloud auth activate-service-account --key-file=deploy_account.json
SERVICE_VERSION=$(curl --silent --header "Authorization: Bearer `gcloud auth print-access-token`" https://servicemanagement.googleapis.com/v1/services/$GOOGLE_PROJECT.appspot.com/config | jq --raw-output .id)

#render config.ini and app.yaml for environment with SERVICE_VERSION and GOOGLE_PROJECT
docker run -v $PWD:/app \
  -e GOOGLE_PROJ=${GOOGLE_PROJECT} \
  -e SERVICE_VERSION=${SERVICE_VERSION} \
  -e INPUT_PATH=/app \
  -e OUT_PATH=/app \
  -e VAULT_TOKEN=${VAULT_TOKEN} \
  -e ENVIRONMENT=${ENVIRONMENT} \
  -e RUN_CONTEXT=live \
  -e DNS_DOMAIN=NULL \
  broadinstitute/dsde-toolbox render-templates.sh

#deploy the app to the specified project
docker run -v $PWD/startup.sh:/app/startup.sh \
    -v $PWD/app.yaml:/app/app.yaml \
    -v $PWD/config.ini:/app/config.ini \
    -v $PWD/deploy_account.json:/deploy_account.json \
    -e GOOGLE_PROJECT=${GOOGLE_PROJECT} \
    --entrypoint "/bin/bash" \
    ${BOND_IMAGE} \
    -c "gcloud auth activate-service-account --key-file=deploy_account.json; gcloud -q app deploy app.yaml --project=$GOOGLE_PROJECT"
