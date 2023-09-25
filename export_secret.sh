#!/bin/bash

NAMESPACE="default"
APP="healthchecks"
SECRET_NAME="healthchecks-secret"

# Get the secret data
SECRET_DATA=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o json | jq -r '.data | to_entries[] | "\(.key):\(.value)"')

# Create the secret manifest YAML file
echo "apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $NAMESPACE
  labels:
    app: $APP
stringData:" > secret.yaml

# Loop through the secret data and append it to the manifest file
while IFS=':' read -r key value; do
  echo "  $key: $(echo $value | base64 --decode)" >> secret.yaml
done <<< "$SECRET_DATA"

echo "Secret manifest file generated successfully!"
