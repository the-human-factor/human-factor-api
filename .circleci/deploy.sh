#!/bin/bash

fail() {
    echo "$*"
    exit 1
}

SERVICE=$1
NAMESPACE=$2


[[ -s $SERVICE ]] || fail "
Usage: ./deploy.sh <service> <namespace>
"

[[ -s $NAMESPACE ]] || fail "
Usage: ./deploy.sh <service> <namespace>
"

kubectl config set-context --curent --namespace=$NAMESPACE

kubectl describe service > service.txt

if grep -q 'color=blue' service.txt
   echo "Current deployment is blue"
   echo "Switching to green deployment"
   kubectl set image deployment human-api-deployment-green human-api=gcr.io/the-human-factor/human-api:$CIRCLE_SHA1 --record
   kubectl rollout status deplopyment human-api-deployment-green
   kubectl patch service human-api-service --patch "$(cat ${PWD}/)"
 elif
 fi
