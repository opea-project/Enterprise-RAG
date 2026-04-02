#!/bin/bash

# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Get Keycloak client secret and store in Kubernetes secret
# Runs inside a Kubernetes Pod

set -e

# Configuration from environment variables
KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak-http:80}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-EnterpriseRAG}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}"
CLIENT_NAME="${CLIENT_NAME:-EnterpriseRAG-oidc-backend}"
SECRET_NAME="${SECRET_NAME:-keycloak-client-secret}"
SECRET_NAMESPACE="${SECRET_NAMESPACE:-auth}"
SECRET_KEY="${SECRET_KEY:-client-secret}"

log_info() { echo "[INFO] $1"; }
log_error() { echo "[ERROR] $1" >&2; }
log_success() { echo "[SUCCESS] $1"; }

# Get access token
get_access_token() {
  local url="${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
  local response

  response=$(curl -sf -X POST "$url" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${KEYCLOAK_ADMIN_USER}" \
    -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
    -d "grant_type=password" \
    -d "client_id=admin-cli")

  ACCESS_TOKEN=$(echo "$response" | jq -r .access_token)

  if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    log_error "Failed to get access token"
    exit 1
  fi
}

# Get client ID by name
get_client_id() {
  local url="${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients"
  
  CLIENT_ID=$(curl -sf -X GET "$url" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | \
    jq -r --arg name "$CLIENT_NAME" '.[] | select(.clientId == $name) | .id')

  if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" == "null" ]; then
    log_error "Client '$CLIENT_NAME' not found"
    exit 1
  fi
}

# Get existing client secret
get_client_secret() {
  local url="${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients/${CLIENT_ID}/client-secret"

  # Retrieve existing secret (GET does not rotate the secret, POST would regenerate it)
  local response
  response=$(curl -sf -X GET "$url" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json")

  CLIENT_SECRET=$(echo "$response" | jq -r .value)

  if [ -z "$CLIENT_SECRET" ] || [ "$CLIENT_SECRET" == "null" ]; then
    log_error "Failed to get client secret"
    exit 1
  fi
}

# Store secret in Kubernetes
store_secret() {
  log_info "Storing client secret to $SECRET_NAME in namespace $SECRET_NAMESPACE"

  kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $SECRET_NAMESPACE
  labels:
    app.kubernetes.io/name: keycloak-client
    app.kubernetes.io/component: oidc
type: Opaque
data:
  $SECRET_KEY: $(echo -n "$CLIENT_SECRET" | base64 -w0)
EOF

  log_success "Client secret stored successfully"
}

# Main
log_info "Getting client secret for '$CLIENT_NAME'"

# Wait for Keycloak
log_info "Waiting for Keycloak..."
for i in $(seq 1 30); do
  if curl -sf "${KEYCLOAK_URL}/realms/master" > /dev/null 2>&1; then
    break
  fi
  sleep 2
done

get_access_token
log_success "Authenticated with Keycloak"

get_client_id
log_info "Found client ID: $CLIENT_ID"

get_client_secret
log_success "Retrieved client secret"

store_secret

log_success "Client secret retrieval completed successfully"
