#!/bin/bash

# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Keycloak Configurator for in-cluster execution (Job-based)
# This script runs inside a Kubernetes Pod and stores credentials in K8s secrets

set -e

# Configuration from environment variables
KEYCLOAK_REALM="${KEYCLOAK_REALM:-EnterpriseRAG}"
KEYCLOAK_DEFAULT_REALM=master
KEYCLOAK_USER="${KEYCLOAK_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak-http:80}"
MINIO_DOMAIN="${MINIO_DOMAIN:-minio.erag.com}"
MINIO_PATH_PREFIX="${MINIO_PATH_PREFIX:-}"
CREDENTIALS_SECRET_NAME="${CREDENTIALS_SECRET_NAME:-erag-credentials}"
CREDENTIALS_SECRET_NAMESPACE="${CREDENTIALS_SECRET_NAMESPACE:-auth}"

# Ensure the Kubernetes API server is excluded from proxy to avoid TLS issues with kubectl
if [ -n "${KUBERNETES_SERVICE_HOST:-}" ] && [ -n "${no_proxy:-}" ]; then
  export no_proxy="${no_proxy},${KUBERNETES_SERVICE_HOST}"
fi

# OIDC Configuration
OIDC_ENDPOINT="${OIDC_ENDPOINT:-}"
OIDC_ALIAS="${OIDC_ALIAS:-}"
OIDC_CLIENT_ID="${OIDC_CLIENT_ID:-}"
OIDC_CLIENT_SECRET="${OIDC_CLIENT_SECRET:-}"
OIDC_ADMIN_GID="${OIDC_ADMIN_GID:-}"
OIDC_MAINTAINER_GID="${OIDC_MAINTAINER_GID:-}"
OIDC_USER_GID="${OIDC_USER_GID:-}"

# Federation Configuration
FEDERATION_ENDPOINT="${FEDERATION_ENDPOINT:-}"
FEDERATION_BIND_DN="${FEDERATION_BIND_DN:-}"
FEDERATION_BIND_PASSWORD="${FEDERATION_BIND_PASSWORD:-}"
FEDERATION_USERS_DN="${FEDERATION_USERS_DN:-}"
FEDERATION_USER_ATTRIBUTE="${FEDERATION_USER_ATTRIBUTE:-sAMAccountName}"
FEDERATION_GROUPS_DN="${FEDERATION_GROUPS_DN:-}"
FEDERATION_USER_GROUP_LDAP_FILTER="${FEDERATION_USER_GROUP_LDAP_FILTER:-(cn=erag-user-group)}"
FEDERATION_MAINTAINER_GROUP_LDAP_FILTER="${FEDERATION_MAINTAINER_GROUP_LDAP_FILTER:-(cn=erag-maintainer-group)}"
FEDERATION_ADMIN_GROUP_LDAP_FILTER="${FEDERATION_ADMIN_GROUP_LDAP_FILTER:-(cn=erag-admin-group)}"

# Session settings
SSO_SESSION_MAX_LIFESPAN=10800
SSO_SESSION_IDLE_TIMEOUT=1800
PAR_REQUEST_URI_LIFESPAN=240
CURL_RETRY_LIMIT=3
REALM_DEFAULT_SIGNATURE_ALGORITHM='"RS384"'
HTTP_CODE=""

# Logging
log_info() { echo "[INFO] $1"; }
log_error() { echo "[ERROR] $1" >&2; }
log_success() { echo "[SUCCESS] $1"; }

# Password generation
generate_random_password() {
  local LENGTH=12
  local password=""
  password+=$(tr -dc '0-9' < /dev/urandom | head -c 1)
  password+=$(tr -dc 'A-Z' < /dev/urandom | head -c 1)
  password+=$(tr -dc 'a-z' < /dev/urandom | head -c 1)
  password+=$(tr -dc '!_)' < /dev/urandom | head -c 1)
  password+=$(tr -dc 'A-Za-z0-9!_)' < /dev/urandom | head -c $(($LENGTH - 4)))
  echo "$password" | fold -w1 | shuf | tr -d '\n'
}

# Get or create credentials from/to Kubernetes secret
get_or_create_credential() {
  local target=$1
  local username=$2
  local password_key="${target}_PASSWORD"
  local username_key="${target}_USERNAME"
  local password=""

  # Try to get existing password from secret
  if kubectl get secret "$CREDENTIALS_SECRET_NAME" -n "$CREDENTIALS_SECRET_NAMESPACE" &>/dev/null; then
    password=$(kubectl get secret "$CREDENTIALS_SECRET_NAME" -n "$CREDENTIALS_SECRET_NAMESPACE" \
      -o jsonpath="{.data.${password_key}}" 2>/dev/null | base64 -d 2>/dev/null || echo "")
  fi

  # Generate new password if not found
  if [ -z "$password" ]; then
    log_info "Generating new password for $target"
    password=$(generate_random_password)
  else
    log_info "Using existing password for $target from secret"
  fi

  # Export for use in script
  export "${password_key}=${password}"
  export "${username_key}=${username}"
  NEW_PASSWORD="$password"
  NEW_USERNAME="$username"
}

# Store all credentials to Kubernetes secret
store_credentials_to_secret() {
  log_info "Storing credentials to secret $CREDENTIALS_SECRET_NAME"

  # Create or update secret
  kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: $CREDENTIALS_SECRET_NAME
  namespace: $CREDENTIALS_SECRET_NAMESPACE
  labels:
    app.kubernetes.io/name: keycloak-configurator
    app.kubernetes.io/component: credentials
type: Opaque
data:
  KEYCLOAK_ERAG_ADMIN_USERNAME: $(echo -n "$KEYCLOAK_ERAG_ADMIN_USERNAME" | base64 -w0)
  KEYCLOAK_ERAG_ADMIN_PASSWORD: $(echo -n "$KEYCLOAK_ERAG_ADMIN_PASSWORD" | base64 -w0)
  KEYCLOAK_ERAG_USER_USERNAME: $(echo -n "$KEYCLOAK_ERAG_USER_USERNAME" | base64 -w0)
  KEYCLOAK_ERAG_USER_PASSWORD: $(echo -n "$KEYCLOAK_ERAG_USER_PASSWORD" | base64 -w0)
  KEYCLOAK_ERAG_MAINTAINER_USERNAME: $(echo -n "$KEYCLOAK_ERAG_MAINTAINER_USERNAME" | base64 -w0)
  KEYCLOAK_ERAG_MAINTAINER_PASSWORD: $(echo -n "$KEYCLOAK_ERAG_MAINTAINER_PASSWORD" | base64 -w0)
EOF

  log_success "Credentials stored in secret"
}

# Get access token from Keycloak
get_access_token() {
  local url="${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
  local response
  local http_code
  local content

  for i in $(seq 1 $CURL_RETRY_LIMIT); do
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=${KEYCLOAK_USER}" \
      -d "password=${ADMIN_PASSWORD}" \
      -d 'grant_type=password' \
      -d 'client_id=admin-cli')

    http_code=$(echo "$response" | tail -n1)
    content=$(echo "$response" | sed '$d')

    if [[ "$http_code" =~ ^2 ]]; then
      ACCESS_TOKEN=$(echo "$content" | jq -r .access_token)
      if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
        return 0
      fi
    fi
    log_info "Retry $i/$CURL_RETRY_LIMIT getting access token (HTTP $http_code)"
    sleep 2
  done

  log_error "Failed to get access token after $CURL_RETRY_LIMIT attempts"
  exit 1
}

# Generic Keycloak API call
curl_keycloak() {
  local url=$1
  local json=$2
  local method=${3:-POST}
  local retry_count=${4:-0}

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$json")

  if [[ "$http_code" =~ ^2 ]]; then
    return 0
  elif [[ "$http_code" == 401 && "$retry_count" -lt "$CURL_RETRY_LIMIT" ]]; then
    get_access_token
    curl_keycloak "$url" "$json" "$method" $((retry_count + 1))
  elif [[ "$http_code" == 409 ]]; then
    HTTP_CODE=$http_code
    return 1
  else
    HTTP_CODE=$http_code
    return 1
  fi
}

# GET request with response
curl_get() {
  local url=$1
  curl -s -X GET "$url" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json"
}

# Get client ID by name
get_client_id() {
  local realm_name=$1
  local client_name=$2
  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/clients"
  curl_get "$url" | jq -r --arg name "$client_name" '.[] | select(.clientId == $name) | .id'
}

# Get group ID by name
get_group_id() {
  local realm_name=$1
  local group_name=$2
  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/groups"
  curl_get "$url" | jq -r --arg name "$group_name" '.[] | select(.name == $name) | .id'
}

# Get client role ID
get_client_role_id() {
  local realm_name=$1
  local role_name=$2
  local client_name=$3
  local client_id=$(get_client_id "$realm_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/roles"
  curl_get "$url" | jq -r --arg name "$role_name" '.[] | select(.name == $name) | .id'
}

# Get user ID
get_user_id() {
  local realm_name=$1
  local username=$2
  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/users"
  curl_get "$url" | jq -r --arg name "$username" '.[] | select(.username == $name) | .id'
}

# Get resource ID
get_resource_id() {
  local realm_name=$1
  local client_name=$2
  local resource_name=$3
  local client_id=$(get_client_id "$realm_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/resource"
  curl_get "$url" | jq -r --arg name "$resource_name" '.[] | select(.name == $name) | ._id'
}

# Get policy ID
get_policy_id() {
  local realm_name=$1
  local client_name=$2
  local policy_name=$3
  local client_id=$(get_client_id "$realm_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/policy"
  curl_get "$url" | jq -r --arg name "$policy_name" '.[] | select(.name == $name) | .id'
}

# Get realm role ID
get_realm_role_id() {
  local realm_name=$1
  local role_name=$2
  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/roles"
  curl_get "$url" | jq -r --arg name "$role_name" '.[] | select(.name == $name) | .id'
}

# Get federation ID
get_federation_id() {
  local realm_name=$1
  local federation_name=$2
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/components"
  curl_get "$url" | jq -r --arg name "$federation_name" '.[] | select(.name == $name) | .id'
}

# Create realm-level role
create_role() {
  local realm_name=$1
  local role_name=$2
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/roles"

  local json='{
    "name": "'$role_name'",
    "description": "",
    "composite": false,
    "clientRole": false,
    "attributes": {}
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Realm role '$role_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Realm role '$role_name' already exists"
  else
    log_error "Failed to create realm role '$role_name' (HTTP $HTTP_CODE)"
  fi
}

# Assign client role as composite to a realm role
assign_role_realm_role() {
  local realm_name=$1
  local realm_role_name=$2
  local client_name=$3
  local role_name=$4

  local role_id=$(get_client_role_id "$realm_name" "$role_name" "$client_name")
  local realm_role_id=$(get_realm_role_id "$realm_name" "$realm_role_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/roles-by-id/${realm_role_id}/composites"

  local json='[{"id": "'$role_id'", "name": "'$role_name'"}]'

  if curl_keycloak "$url" "$json"; then
    log_success "Client role '$role_name' assigned to realm role '$realm_role_name'"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Client role '$role_name' already assigned to realm role '$realm_role_name'"
  else
    log_error "Failed to assign client role '$role_name' to realm role '$realm_role_name' (HTTP $HTTP_CODE)"
  fi
}

# Create realm
create_realm() {
  local realm_name=$1
  local url="${KEYCLOAK_URL}/admin/realms"
  local password_policy="length(12) and digits(1) and upperCase(1) and lowerCase(1) and specialChars(1) and notUsername and passwordHistory(5)"

  local json='{
    "realm": "'$realm_name'",
    "enabled": true,
    "sslRequired": "none",
    "registrationAllowed": false,
    "passwordPolicy": "'$password_policy'"
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Realm '$realm_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Realm '$realm_name' already exists"
  else
    log_error "Failed to create realm '$realm_name' (HTTP $HTTP_CODE)"
  fi
}

# Enable brute force protection
prevent_bruteforce() {
  local realm_name=$1
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}"

  curl_keycloak "$url" '{
    "bruteForceProtected": true,
    "maxFailureWaitSeconds": 900,
    "minimumQuickLoginWaitSeconds": 60,
    "waitIncrementSeconds": 60,
    "quickLoginCheckMilliSeconds": 1000,
    "maxDeltaTimeSeconds": 86400,
    "failureFactor": 3
  }' "PUT"
}

# Create client
create_client() {
  local realm_name=$1
  local client_name=$2
  local authorization=${3:-false}
  local authentication=${4:-false}
  local public_client=${5:-true}
  local root_url=${6:-}
  local redirect_uris=${7:-*}
  local direct_access=${8:-true}

  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients"

  local json='{
    "clientId": "'$client_name'",
    "enabled": true,
    "directAccessGrantsEnabled": '$direct_access',
    "authorizationServicesEnabled": '$authorization',
    "serviceAccountsEnabled": '$authentication',
    "publicClient": '$public_client',
    "clientAuthenticatorType": "client-secret",
    "rootUrl": "'$root_url'",
    "baseUrl": "'$root_url'",
    "redirectUris": ["'$redirect_uris'"],
    "webOrigins": ["*"],
    "protocol": "openid-connect",
    "frontchannelLogout": false
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Client '$client_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Client '$client_name' already exists - ensuring correct configuration"
    local client_uuid
    client_uuid=$(get_client_id "$realm_name" "$client_name")
    local update_url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_uuid}"
    local update_json='{
      "publicClient": '$public_client',
      "serviceAccountsEnabled": '$authentication',
      "directAccessGrantsEnabled": '$direct_access',
      "authorizationServicesEnabled": '$authorization'
    }'
    if curl_keycloak "$update_url" "$update_json" PUT; then
      log_success "Client '$client_name' updated to desired configuration"
    else
      log_error "Failed to update existing client '$client_name' (HTTP $HTTP_CODE)"
    fi
  else
    log_error "Failed to create client '$client_name' (HTTP $HTTP_CODE)"
  fi
}

# Create client role
create_client_role() {
  local realm_name=$1
  local client_name=$2
  local role_name=$3
  local client_id=$(get_client_id "$realm_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/roles"

  local json='{"name": "'$role_name'", "clientRole": true}'

  if curl_keycloak "$url" "$json"; then
    log_success "Client role '$role_name' created for '$client_name'"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Client role '$role_name' already exists"
  else
    log_error "Failed to create client role '$role_name' (HTTP $HTTP_CODE)"
  fi
}

# Create user
create_user() {
  local realm_name=$1
  local username=$2
  local email=$3
  local first_name=$4
  local last_name=$5
  local password=$6
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/users"

  local json='{
    "username": "'$username'",
    "email": "'$email'",
    "firstName": "'$first_name'",
    "lastName": "'$last_name'",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{"type": "password", "value": "'$password'", "temporary": true}]
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "User '$username' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "User '$username' already exists"
  else
    log_error "Failed to create user '$username' (HTTP $HTTP_CODE)"
  fi
}

# Assign client role to user
assign_user_client_role() {
  local realm_name=$1
  local username=$2
  local role_name=$3
  local client_name=$4

  local user_id=$(get_user_id "$realm_name" "$username")
  local client_id=$(get_client_id "$realm_name" "$client_name")
  local role_id=$(get_client_role_id "$realm_name" "$role_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/users/${user_id}/role-mappings/clients/${client_id}"

  local json='[{"id": "'$role_id'", "name": "'$role_name'"}]'

  if curl_keycloak "$url" "$json"; then
    log_success "Role '$role_name' assigned to user '$username'"
  else
    log_info "Role '$role_name' may already be assigned to '$username'"
  fi
}

# Create group
create_group() {
  local realm_name=$1
  local group_name=$2
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/groups"

  local json='{"name": "'$group_name'", "path": "/'$group_name'"}'

  if curl_keycloak "$url" "$json"; then
    log_success "Group '$group_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Group '$group_name' already exists"
  else
    log_error "Failed to create group '$group_name' (HTTP $HTTP_CODE)"
  fi
}

# Map client role to group
map_client_role_to_group() {
  local realm_name=$1
  local group_name=$2
  local client_name=$3
  local role_name=$4

  local group_id=$(get_group_id "$realm_name" "$group_name")
  local client_id=$(get_client_id "$realm_name" "$client_name")
  local role_id=$(get_client_role_id "$realm_name" "$role_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/groups/${group_id}/role-mappings/clients/${client_id}"

  local json='[{"id": "'$role_id'", "name": "'$role_name'"}]'

  if curl_keycloak "$url" "$json"; then
    log_success "Role '$role_name' mapped to group '$group_name'"
  else
    log_info "Role '$role_name' may already be mapped to group '$group_name'"
  fi
}

# Set realm timeouts
set_realm_timeouts() {
  local realm_name=$1
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}"

  local json='{
    "ssoSessionIdleTimeout": '$SSO_SESSION_IDLE_TIMEOUT',
    "ssoSessionMaxLifespan": '$SSO_SESSION_MAX_LIFESPAN',
    "clientSessionIdleTimeout": '$SSO_SESSION_IDLE_TIMEOUT',
    "clientSessionMaxLifespan": '$SSO_SESSION_MAX_LIFESPAN',
    "attributes": {"parRequestUriLifespan": '$PAR_REQUEST_URI_LIFESPAN'}
  }'

  if curl_keycloak "$url" "$json" "PUT"; then
    log_success "Realm timeouts set for '$realm_name'"
  fi
}

# Set realm signature algorithm
set_realm_signature_algorithms() {
  local realm_name=$1
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}"

  local json='{"defaultSignatureAlgorithm": '$REALM_DEFAULT_SIGNATURE_ALGORITHM'}'

  if curl_keycloak "$url" "$json" "PUT"; then
    log_success "Signature algorithm set for '$realm_name'"
  fi
}

# Add client scope mapper for roles
add_client_scope_mapper() {
  local realm_name=$1
  local scope_name=$2
  local client_name=$3
  local token_claim_name=$4
  local mapper_name=$5
  local mapper_client_name=$6

  local client_id=$(get_client_id "$realm_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/protocol-mappers/add-models"

  local json='[{
    "name": "'$mapper_name'",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-usermodel-client-role-mapper",
    "consentRequired": false,
    "config": {
      "introspection.token.claim": "true",
      "multivalued": "true",
      "userinfo.token.claim": "false",
      "user.attribute": "client_roles",
      "id.token.claim": "true",
      "lightweight.claim": "false",
      "access.token.claim": "true",
      "claim.name": "'$token_claim_name'",
      "jsonType.label": "String",
      "usermodel.clientRoleMapping.clientId": "'$mapper_client_name'"
    }
  }]'

  if curl_keycloak "$url" "$json"; then
    log_success "Mapper '$mapper_name' created for '$client_name'"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Mapper '$mapper_name' already exists"
  else
    log_error "Failed to create mapper '$mapper_name' (HTTP $HTTP_CODE)"
  fi
}

# Create client resource (for RBAC)
create_client_resource() {
  local realm_name=$1
  local client_name=$2
  local resource_name=$3
  local resource_scopes=$4

  local client_id=$(get_client_id "$realm_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/resource"

  local json='{
    "name": "'$resource_name'",
    "scopes": [{"name": "'$resource_scopes'"}]
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Resource '$resource_name' created for '$client_name'"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Resource '$resource_name' already exists"
  else
    log_error "Failed to create resource '$resource_name' (HTTP $HTTP_CODE)"
  fi
}

# Create client policy (for RBAC)
create_client_policy() {
  local realm_name=$1
  local client_name=$2
  local policy_name=$3
  local role_name=$4

  local client_id=$(get_client_id "$realm_name" "$client_name")
  local role_id=$(get_client_role_id "$realm_name" "$role_name" "$client_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/policy/role"

  local json='{
    "name": "'$policy_name'",
    "type": "role",
    "logic": "POSITIVE",
    "decisionStrategy": "UNANIMOUS",
    "roles": [{"id": "'$role_id'"}]
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Policy '$policy_name' created for role '$role_name'"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Policy '$policy_name' already exists"
  else
    log_error "Failed to create policy '$policy_name' (HTTP $HTTP_CODE)"
  fi
}

# Create client permission (for RBAC)
create_client_permission() {
  local realm_name=$1
  local client_name=$2
  local permission_name=$3
  local resource_name=$4
  local policy_name=$5

  local client_id=$(get_client_id "$realm_name" "$client_name")
  local policy_id=$(get_policy_id "$realm_name" "$client_name" "$policy_name")
  local resource_id=$(get_resource_id "$realm_name" "$client_name" "$resource_name")
  local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/permission/resource"

  local json='{
    "name": "'$permission_name'",
    "type": "resource",
    "logic": "POSITIVE",
    "decisionStrategy": "UNANIMOUS",
    "resources": ["'$resource_id'"],
    "policies": ["'$policy_id'"]
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Permission '$permission_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Permission '$permission_name' already exists"
  else
    log_error "Failed to create permission '$permission_name' (HTTP $HTTP_CODE)"
  fi
}

# Create OIDC identity provider
create_oidc_config() {
  local realm_name=$1
  local endpoint=$2
  local oidc_alias=$3
  local oidc_display_name=$4
  local oidc_client_id=$5
  local oidc_client_secret=$6

  # Retrieve OIDC URLs from endpoint
  local oidc_metadata=$(curl -s -X GET "${endpoint}")
  local oidc_authorization_url="$(echo $oidc_metadata | jq -r .authorization_endpoint)"
  local oidc_token_url="$(echo $oidc_metadata | jq -r .token_endpoint)"
  local oidc_logout_url="$(echo $oidc_metadata | jq -r .end_session_endpoint)"
  local oidc_user_info_url="$(echo $oidc_metadata | jq -r .userinfo_endpoint)"
  local oidc_issuer="$(echo $oidc_metadata | jq -r .issuer)"
  local oidc_jwks_url="$(echo $oidc_metadata | jq -r .jwks_uri)"

  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/identity-provider/instances"

  local json='{
    "alias": "'$oidc_alias'",
    "displayName": "'$oidc_display_name'",
    "config": {
      "authorizationUrl": "'$oidc_authorization_url'",
      "tokenUrl": "'$oidc_token_url'",
      "logoutUrl": "'$oidc_logout_url'",
      "userInfoUrl": "'$oidc_user_info_url'",
      "issuer": "'$oidc_issuer'",
      "validateSignature": "true",
      "pkceEnabled": "false",
      "clientAuthMethod": "client_secret_post",
      "clientId": "'$oidc_client_id'",
      "clientSecret": "'$oidc_client_secret'",
      "metadataDescriptorUrl": "'$endpoint'",
      "jwksUrl": "'$oidc_jwks_url'",
      "useJwksUrl": "true"
    },
    "providerId": "oidc",
    "storeToken": "true",
    "addReadTokenRoleOnCreate": "true"
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "OIDC identity provider '$oidc_alias' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "OIDC identity provider '$oidc_alias' already exists"
  else
    log_error "Failed to create OIDC identity provider (HTTP $HTTP_CODE)"
  fi
}

# Create OIDC mapper for group assignment
create_oidc_mapper() {
  local realm_name=$1
  local oidc_alias=$2
  local group_id=$3
  local group_name=$4

  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/identity-provider/instances/$oidc_alias/mappers"

  # Check if mapper already exists
  local existing
  existing=$(curl_get "$url" | jq -r --arg name "$group_id" '.[] | select(.name == $name) | .name')
  if [[ -n "$existing" ]]; then
    log_info "OIDC mapper '$group_id' already exists, skipping"
    return 0
  fi

  local json='{
    "config": {
      "group": "/'$group_name'",
      "syncMode": "INHERIT"
    },
    "identityProviderAlias": "'$oidc_alias'",
    "identityProviderMapper": "oidc-hardcoded-group-idp-mapper",
    "name": "'$group_id'"
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "OIDC mapper for group '$group_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "OIDC mapper '$group_id' already exists"
  else
    log_error "Failed to create OIDC mapper '$group_id' (HTTP $HTTP_CODE)"
  fi
}

# Create OIDC role-based mapper (for SSO claim-to-role mapping)
create_oidc_role_mapper() {
  local realm_name=$1
  local oidc_alias=$2
  local mapper_name=$3
  local claim_name=$4
  local claim_value=$5
  local role_name=$6

  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/identity-provider/instances/$oidc_alias/mappers"

  # Check if mapper already exists (Keycloak returns 400 not 409 for duplicate IdP mappers)
  local existing
  existing=$(curl_get "$url" | jq -r --arg name "$mapper_name" '.[] | select(.name == $name) | .name')
  if [[ -n "$existing" ]]; then
    log_info "OIDC role mapper '$mapper_name' already exists, skipping"
    return 0
  fi

  local json='{
    "config": {
      "claim": "'$claim_name'",
      "claim.value": "'$claim_value'",
      "role": "'$role_name'",
      "syncMode": "FORCE"
    },
    "identityProviderAlias": "'$oidc_alias'",
    "identityProviderMapper": "oidc-role-idp-mapper",
    "name": "'$mapper_name'"
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "OIDC role mapper '$mapper_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "OIDC role mapper '$mapper_name' already exists"
  else
    log_error "Failed to create OIDC role mapper '$mapper_name' (HTTP $HTTP_CODE)"
  fi
}

# Create AD Federation
create_ad_federation() {
  local realm_name=$1
  local ad_endpoint=$2
  local ad_bind_dn=$3
  local ad_bind_password=$4
  local ad_users_dn=$5
  local ad_username_attribute=$6

  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/components"

  local json='{
    "config": {
      "enabled": ["true"],
      "vendor": ["ad"],
      "connectionUrl": ["'$ad_endpoint'"],
      "startTls": ["false"],
      "useTruststoreSpi": ["always"],
      "connectionPooling": ["false"],
      "authType": ["simple"],
      "bindDn": ["'$ad_bind_dn'"],
      "bindCredential": ["'$ad_bind_password'"],
      "editMode": ["READ_ONLY"],
      "usersDn": ["'$ad_users_dn'"],
      "usernameLDAPAttribute": ["'$ad_username_attribute'"],
      "rdnLDAPAttribute": ["cn"],
      "uuidLDAPAttribute": ["objectGUID"],
      "userObjectClasses": ["person, organizationalPerson, user"],
      "searchScope": ["1"],
      "importEnabled": ["true"],
      "syncRegistrations": ["true"],
      "cachePolicy": ["NO_CACHE"],
      "trustEmail": ["true"],
      "fullSyncPeriod": ["604800"],
      "changedSyncPeriod": ["86400"]
    },
    "providerId": "ldap",
    "providerType": "org.keycloak.storage.UserStorageProvider",
    "name": "Active Directory Federation"
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "AD Federation created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "AD Federation already exists"
  else
    log_error "Failed to create AD Federation (HTTP $HTTP_CODE)"
  fi
}

# Create federation mapper for role assignment
create_federation_mapper() {
  local realm_name=$1
  local federation_name=$2
  local mapper_name=$3
  local users_role_dn=$4
  local ldap_filter=$5
  local client_name=$6

  local federation_id=$(get_federation_id "$realm_name" "$federation_name")
  local url="${KEYCLOAK_URL}/admin/realms/$realm_name/components"

  local json='{
    "parentId": "'$federation_id'",
    "providerType": "org.keycloak.storage.ldap.mappers.LDAPStorageMapper",
    "name": "'$mapper_name'",
    "providerId": "role-ldap-mapper",
    "config": {
      "membership.attribute.type": ["DN"],
      "mode": ["READ_ONLY"],
      "user.roles.retrieve.strategy": ["LOAD_ROLES_BY_MEMBER_ATTRIBUTE"],
      "roles.dn": ["'$users_role_dn'"],
      "role.name.ldap.attribute": ["cn"],
      "role.object.classes": ["group"],
      "membership.ldap.attribute": ["member"],
      "membership.user.ldap.attribute": ["sAMAccountName"],
      "roles.ldap.filter": ["'$ldap_filter'"],
      "memberof.ldap.attribute": ["memberOf"],
      "use.realm.roles.mapping": ["false"],
      "client.id": ["'$client_name'"]
    }
  }'

  if curl_keycloak "$url" "$json"; then
    log_success "Federation mapper '$mapper_name' created"
  elif [[ $HTTP_CODE == 409 ]]; then
    log_info "Federation mapper '$mapper_name' already exists"
  else
    log_error "Failed to create federation mapper '$mapper_name' (HTTP $HTTP_CODE)"
  fi
}

# =====================================================
# Main execution
# =====================================================

log_info "Starting Keycloak configuration"
log_info "Keycloak URL: $KEYCLOAK_URL"
log_info "MinIO domain: $MINIO_DOMAIN"

# Wait for Keycloak to be ready
log_info "Waiting for Keycloak to be ready..."
for i in $(seq 1 60); do
  if curl -sf "${KEYCLOAK_URL}/realms/master" > /dev/null 2>&1; then
    log_success "Keycloak is ready"
    break
  fi
  if [ $i -eq 60 ]; then
    log_error "Keycloak not ready after 5 minutes"
    exit 1
  fi
  sleep 5
done

# Get access token
log_info "Authenticating with Keycloak..."
get_access_token
log_success "Authentication successful"

# Create realm
log_info "Creating realm..."
create_realm "$KEYCLOAK_REALM"
prevent_bruteforce "$KEYCLOAK_REALM"

# Create clients
log_info "Creating clients..."
create_client "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "false" "false" "true"
create_client "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "true" "true" "false"

# Create client roles
log_info "Creating roles..."
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "ERAG-admin"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "ERAG-user"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "ERAG-admin"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "ERAG-user"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "ERAG-maintainer"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "ERAG-maintainer"

# Create users
log_info "Creating users..."
get_or_create_credential "KEYCLOAK_ERAG_ADMIN" "erag-admin"
create_user "$KEYCLOAK_REALM" "erag-admin" "testadmin@example.com" "Test" "Admin" "$NEW_PASSWORD"

get_or_create_credential "KEYCLOAK_ERAG_USER" "erag-user"
create_user "$KEYCLOAK_REALM" "erag-user" "testuser@example.com" "Test" "User" "$NEW_PASSWORD"

get_or_create_credential "KEYCLOAK_ERAG_MAINTAINER" "erag-maintainer"
create_user "$KEYCLOAK_REALM" "erag-maintainer" "maintainer@example.com" "Test" "Maintainer" "$NEW_PASSWORD"

# Assign roles to users
log_info "Assigning roles to users..."
assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "ERAG-admin" "EnterpriseRAG-oidc"
assign_user_client_role "$KEYCLOAK_REALM" "erag-user" "ERAG-user" "EnterpriseRAG-oidc"
assign_user_client_role "$KEYCLOAK_REALM" "erag-maintainer" "ERAG-user" "EnterpriseRAG-oidc"
assign_user_client_role "$KEYCLOAK_REALM" "erag-maintainer" "ERAG-maintainer" "EnterpriseRAG-oidc"
assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "ERAG-admin" "EnterpriseRAG-oidc-backend"
assign_user_client_role "$KEYCLOAK_REALM" "erag-user" "ERAG-user" "EnterpriseRAG-oidc-backend"
assign_user_client_role "$KEYCLOAK_REALM" "erag-maintainer" "ERAG-user" "EnterpriseRAG-oidc-backend"
assign_user_client_role "$KEYCLOAK_REALM" "erag-maintainer" "ERAG-maintainer" "EnterpriseRAG-oidc-backend"

# Set realm settings
log_info "Configuring realm settings..."
set_realm_signature_algorithms "$KEYCLOAK_REALM"
set_realm_signature_algorithms "$KEYCLOAK_DEFAULT_REALM"

# When SSO is enabled, Microsoft enforces a ~4800s token timeout that cannot be changed
# and Keycloak does not yet support automatic token refreshes, so cap the session lifespan
# to 4200s to avoid stale sessions.
if [[ "$OIDC_ENDPOINT" =~ ^https?:// ]]; then
  SSO_SESSION_MAX_LIFESPAN=4200
fi
set_realm_timeouts "$KEYCLOAK_REALM"
set_realm_timeouts "$KEYCLOAK_DEFAULT_REALM"

# MinIO client
log_info "Creating MinIO client..."
if [ -n "$MINIO_PATH_PREFIX" ]; then
  minio_base_url="https://${MINIO_DOMAIN}${MINIO_PATH_PREFIX}"
  minio_redirect_uri="https://${MINIO_DOMAIN}${MINIO_PATH_PREFIX}/oauth_callback"
else
  minio_base_url="https://$MINIO_DOMAIN"
  minio_redirect_uri="https://$MINIO_DOMAIN/oauth_callback"
fi
create_client "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "false" "true" "false" "$minio_base_url" "$minio_redirect_uri" "false"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "consoleAdmin"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "readwrite"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "erag-admin-group"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "erag-user-group"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "erag-maintainer-group"

# Add mappers
log_info "Creating client scope mappers..."
add_client_scope_mapper "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio-dedicated" "EnterpriseRAG-oidc-minio" "minio_roles" "minio_roles" "EnterpriseRAG-oidc-minio"
add_client_scope_mapper "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-dedicated" "EnterpriseRAG-oidc" "minio_roles" "minio_roles" "EnterpriseRAG-oidc-minio"

# Assign MinIO roles
log_info "Assigning MinIO roles..."
assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "consoleAdmin" "EnterpriseRAG-oidc-minio"
assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "erag-admin-group" "EnterpriseRAG-oidc-minio"
assign_user_client_role "$KEYCLOAK_REALM" "erag-maintainer" "erag-user-group" "EnterpriseRAG-oidc-minio"
assign_user_client_role "$KEYCLOAK_REALM" "erag-maintainer" "erag-maintainer-group" "EnterpriseRAG-oidc-minio"
assign_user_client_role "$KEYCLOAK_REALM" "erag-user" "erag-user-group" "EnterpriseRAG-oidc-minio"

# Groups
log_info "Creating groups..."
create_group "$KEYCLOAK_REALM" "erag-user-group"
create_group "$KEYCLOAK_REALM" "erag-admin-group"
create_group "$KEYCLOAK_REALM" "erag-maintainer-group"

# Map roles to groups
log_info "Mapping roles to groups..."
map_client_role_to_group "$KEYCLOAK_REALM" "erag-admin-group" "EnterpriseRAG-oidc" "ERAG-admin"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-admin-group" "EnterpriseRAG-oidc-backend" "ERAG-admin"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-admin-group" "EnterpriseRAG-oidc-minio" "consoleAdmin"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-user-group" "EnterpriseRAG-oidc" "ERAG-user"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-user-group" "EnterpriseRAG-oidc-backend" "ERAG-user"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-maintainer-group" "EnterpriseRAG-oidc" "ERAG-maintainer"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-maintainer-group" "EnterpriseRAG-oidc" "ERAG-user"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-maintainer-group" "EnterpriseRAG-oidc-backend" "ERAG-maintainer"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-maintainer-group" "EnterpriseRAG-oidc-backend" "ERAG-user"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-maintainer-group" "EnterpriseRAG-oidc-minio" "erag-user-group"
map_client_role_to_group "$KEYCLOAK_REALM" "erag-maintainer-group" "EnterpriseRAG-oidc-minio" "erag-maintainer-group"

# OIDC Identity Provider (if configured)
if [[ "$OIDC_ENDPOINT" =~ ^https?:// ]]; then
  log_info "Configuring OIDC identity provider..."
  create_oidc_config "$KEYCLOAK_REALM" "$OIDC_ENDPOINT" "$OIDC_ALIAS" "Enterprise SSO Login" "$OIDC_CLIENT_ID" "$OIDC_CLIENT_SECRET"

  # Create SSO realm roles and map them to client roles
  create_role "$KEYCLOAK_REALM" "ERAG-SSO-Admin"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Admin" "EnterpriseRAG-oidc" "ERAG-admin"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Admin" "EnterpriseRAG-oidc-backend" "ERAG-admin"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Admin" "EnterpriseRAG-oidc-minio" "erag-admin-group"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Admin" "EnterpriseRAG-oidc-minio" "consoleAdmin"

  create_role "$KEYCLOAK_REALM" "ERAG-SSO-User"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-User" "EnterpriseRAG-oidc" "ERAG-user"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-User" "EnterpriseRAG-oidc-backend" "ERAG-user"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-User" "EnterpriseRAG-oidc-minio" "erag-user-group"

  create_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer" "EnterpriseRAG-oidc" "ERAG-user"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer" "EnterpriseRAG-oidc" "ERAG-maintainer"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer" "EnterpriseRAG-oidc-backend" "ERAG-user"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer" "EnterpriseRAG-oidc-backend" "ERAG-maintainer"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer" "EnterpriseRAG-oidc-minio" "erag-user-group"
  assign_role_realm_role "$KEYCLOAK_REALM" "ERAG-SSO-Maintainer" "EnterpriseRAG-oidc-minio" "erag-maintainer-group"

  # Create SSO claim-to-role mappers
  create_oidc_role_mapper "$KEYCLOAK_REALM" "$OIDC_ALIAS" "SSO-Admin-Mapper" "roles" "EnterpriseRAG.AdminAccess" "ERAG-SSO-Admin"
  create_oidc_role_mapper "$KEYCLOAK_REALM" "$OIDC_ALIAS" "SSO-User-Mapper" "roles" "EnterpriseRAG.UserAccess" "ERAG-SSO-User"
  create_oidc_role_mapper "$KEYCLOAK_REALM" "$OIDC_ALIAS" "SSO-Maintainer-Mapper" "roles" "EnterpriseRAG.MaintainerAccess" "ERAG-SSO-Maintainer"

  # Validate OIDC identity provider
  log_info "Validating OIDC identity provider '$OIDC_ALIAS'..."
  get_access_token
  HTTP_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/${OIDC_ALIAS}")
  if [[ "$HTTP_STATUS" == "200" ]]; then
    log_success "OIDC identity provider '$OIDC_ALIAS' validated successfully"
  else
    log_error "OIDC identity provider validation returned HTTP $HTTP_STATUS. Check the alias and Keycloak logs."
  fi

  # Group-based OIDC mappers
  if [[ -n "$OIDC_ADMIN_GID" ]]; then
    create_oidc_mapper "$KEYCLOAK_REALM" "$OIDC_ALIAS" "$OIDC_ADMIN_GID" "erag-admin-group"
  fi
  if [[ -n "$OIDC_MAINTAINER_GID" ]]; then
    create_oidc_mapper "$KEYCLOAK_REALM" "$OIDC_ALIAS" "$OIDC_MAINTAINER_GID" "erag-maintainer-group"
  fi
  if [[ -n "$OIDC_USER_GID" ]]; then
    create_oidc_mapper "$KEYCLOAK_REALM" "$OIDC_ALIAS" "$OIDC_USER_GID" "erag-user-group"
  fi

  # Validate upstream OIDC metadata endpoint
  METADATA_STATUS=$(curl -sk --max-time 10 -o /dev/null -w "%{http_code}" "${OIDC_ENDPOINT}" || true)
  if [[ "$METADATA_STATUS" == "200" ]]; then
    log_info "Upstream OIDC metadata endpoint is reachable (HTTP 200)"
  else
    log_error "Upstream OIDC metadata endpoint returned HTTP $METADATA_STATUS. SSO logins may fail if Keycloak cannot reach Entra ID."
  fi
fi

# RBAC Configuration
log_info "Configuring RBAC..."
create_client_resource "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "admin" "admin-access"
create_client_resource "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "user" "user-access"
create_client_resource "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "maintainer" "maintainer-access"
create_client_policy "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "admin-policy" "ERAG-admin"
create_client_policy "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "user-policy" "ERAG-user"
create_client_policy "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "maintainer-policy" "ERAG-maintainer"
create_client_permission "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "admin-permission" "admin" "admin-policy"
create_client_permission "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "user-permission" "user" "user-policy"
create_client_permission "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "maintainer-permission" "maintainer" "maintainer-policy"

# Active Directory Federation (if configured)
if [[ "$FEDERATION_ENDPOINT" =~ ^ldaps?:// ]]; then
  log_info "Configuring AD Federation..."
  create_ad_federation "$KEYCLOAK_REALM" "$FEDERATION_ENDPOINT" "$FEDERATION_BIND_DN" "$FEDERATION_BIND_PASSWORD" "$FEDERATION_USERS_DN" "$FEDERATION_USER_ATTRIBUTE"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "ERAG-admin-oidc" "$FEDERATION_GROUPS_DN" "$FEDERATION_ADMIN_GROUP_LDAP_FILTER" "EnterpriseRAG-oidc"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "ERAG-user-oidc" "$FEDERATION_GROUPS_DN" "$FEDERATION_USER_GROUP_LDAP_FILTER" "EnterpriseRAG-oidc"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "ERAG-admin-oidc-backend" "$FEDERATION_GROUPS_DN" "$FEDERATION_ADMIN_GROUP_LDAP_FILTER" "EnterpriseRAG-oidc-backend"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "ERAG-user-oidc-backend" "$FEDERATION_GROUPS_DN" "$FEDERATION_USER_GROUP_LDAP_FILTER" "EnterpriseRAG-oidc-backend"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "consoleAdmin-oidc-minio" "$FEDERATION_GROUPS_DN" "(cn=consoleAdmin)" "EnterpriseRAG-oidc-minio"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "ERAG-maintainer-oidc" "$FEDERATION_GROUPS_DN" "$FEDERATION_MAINTAINER_GROUP_LDAP_FILTER" "EnterpriseRAG-oidc"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "ERAG-maintainer-oidc-backend" "$FEDERATION_GROUPS_DN" "$FEDERATION_MAINTAINER_GROUP_LDAP_FILTER" "EnterpriseRAG-oidc-backend"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "erag-admin-group-oidc-minio" "$FEDERATION_GROUPS_DN" "(cn=erag-admin-group)" "EnterpriseRAG-oidc-minio"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "erag-user-group-oidc-minio" "$FEDERATION_GROUPS_DN" "(cn=erag-user-group)" "EnterpriseRAG-oidc-minio"
  create_federation_mapper "$KEYCLOAK_REALM" "Active Directory Federation" "erag-maintainer-group-oidc-minio" "$FEDERATION_GROUPS_DN" "(cn=erag-maintainer-group)" "EnterpriseRAG-oidc-minio"
fi

# Store credentials to Kubernetes secret
store_credentials_to_secret

log_success "Keycloak configuration completed successfully!"
