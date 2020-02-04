#!/usr/bin/env bash
set -e
set -x

VAULT_TOKEN=$1
GIT_BRANCH=$2
TARGET_ENV=$3

set +x
if [ -z "$TARGET_ENV" ]; then
    echo "TARGET_ENV argument not supplied; inferring from GIT_BRANCH '$GIT_BRANCH'."

    if [ "$GIT_BRANCH" == "develop" ]; then
        TARGET_ENV="dev"
    elif [ "$GIT_BRANCH" == "alpha" ]; then
        TARGET_ENV="alpha"
    elif [ "$GIT_BRANCH" == "perf" ]; then
        TARGET_ENV="perf"
    elif [ "$GIT_BRANCH" == "staging" ]; then
        TARGET_ENV="staging"
    elif [ "$GIT_BRANCH" == "master" ]; then
        TARGET_ENV="prod"
    else
        echo "Git branch '$GIT_BRANCH' is not configured to automatically deploy to a target environment"
        exit 1
    fi
fi

if [[ "$TARGET_ENV" =~ ^(dev|alpha|perf|staging|prod)$ ]]; then
    ENVIRONMENT=${TARGET_ENV}
else
    echo "Unknown environment: $TARGET_ENV - must be one of [dev, alpha, perf, staging, prod]"
    exit 1
fi

echo "Deploying branch '${GIT_BRANCH}' to ${ENVIRONMENT}"
set -x

GOOGLE_PROJECT=broad-bond-${ENVIRONMENT}
BOND_IMAGE=quay.io/databiosphere/bond:${GIT_BRANCH}

#pull the credentials for the service account
docker run --rm -e VAULT_TOKEN=${VAULT_TOKEN} broadinstitute/dsde-toolbox vault read --format=json "secret/dsde/bond/$ENVIRONMENT/deploy-account.json" | jq .data > deploy_account.json

if [ ! -s deploy_account.json ]; then
    echo "Failed to create deploy_account.json"
    exit 1
fi

#build the docker image so we can deploy
docker pull ${BOND_IMAGE}

#SERVICE_VERSION in app.yaml needs to match the output of the curl call below
export BUILD_TMP="${HOME}/deploy-bond-${TARGET_ENV}"
mkdir -p ${BUILD_TMP}
export CLOUDSDK_CONFIG=${BUILD_TMP}

gcloud auth activate-service-account --key-file=deploy_account.json
SERVICE_VERSION=$(curl --silent --header "Authorization: Bearer `gcloud auth print-access-token`" https://servicemanagement.googleapis.com/v1/services/$GOOGLE_PROJECT.appspot.com/config | jq --raw-output .id)

export DSDE_TOOLBOX_DOCKER_IMG=broadinstitute/dsde-toolbox:consul-0.20.0
docker pull $DSDE_TOOLBOX_DOCKER_IMG
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
  $DSDE_TOOLBOX_DOCKER_IMG render-templates.sh

#deploy the app to the specified project
docker run -v $PWD/app.yaml:/app/app.yaml \
    -v $PWD/config.ini:/app/config.ini \
    -v $PWD/deploy_account.json:/app/deploy_account.json \
    -e GOOGLE_PROJECT=${GOOGLE_PROJECT} \
    --entrypoint "/bin/bash" \
    ${BOND_IMAGE} \
    -c "gcloud auth activate-service-account --key-file=deploy_account.json; gcloud -q app deploy app.yaml --project=$GOOGLE_PROJECT; gcloud -q app deploy cron.yaml --project=$GOOGLE_PROJECT"
