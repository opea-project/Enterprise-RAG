#!/bin/bash

# requires jq
# sudo apt install jq

# set -x

repo_path=$(realpath "$(pwd)/../../")

KEYCLOAK_REALM=EnterpriseRAG
KEYCLOAK_DEFAULT_REALM=master
KEYCLOAK_USER=admin
ADMIN_PASSWORD=${1:-admin}
KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:1234}
HTTP_CODE=""

SSOSESSIONMAXLIFESPAN=10800
SSOSESSIONIDLETIMEOUT=1800

source $repo_path/deployment/credentials_utils.sh

function print_header() {
    echo "$1"
    echo "-----------------------"
}

function print_log() {
    echo "-->$1"
}

function get_access_token() {

    ACCESS_TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${KEYCLOAK_USER}" \
        -d "password=${ADMIN_PASSWORD}" \
        -d 'grant_type=password' \
        -d 'client_id=admin-cli' | jq -r .access_token)
}

function curl_keycloak() {
    local url=$1
    local json=$2
    local method=${3:-POST}
    local response=""

    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$json")

    if [[ "$response" =~ ^2 ]]; then
        return 0
    elif [[ "$response" == 409 ]]; then
        HTTP_CODE=$response
        return 1
    elif [[ "$response" =~ ^4 ]]; then
        HTTP_CODE=$response
        return 1
    elif [[ "$response" =~ ^5 ]]; then
        HTTP_CODE=$response
        return 1
    else
        print_log "Unexpected status code: $response"
        exit 1
    fi
}

function get_client_id() {
    local realm_name=$1
    local client_name=$2
    local url="${KEYCLOAK_URL}/admin/realms/$realm_name/clients"

    local client_id=""
    client_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "clientId" --arg value "$client_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$client_id"
}

function get_group_id() {
    local realm_name=$1
    local group_name=$2
    local url="${KEYCLOAK_URL}/admin/realms/$realm_name/groups"

    local group_id=""
    group_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$group_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$group_id"
}

function get_realm_role_id() {
    local realm_name=$1
    local role_name=$2
    local url="${KEYCLOAK_URL}/admin/realms/$realm_name/roles"

    local role_id=""
    role_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$role_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$role_id"
}

function get_client_role_id() {
    local realm_name=$1
    local role_name=$2
    local client_name=$3

    client_id=$(get_client_id "$realm_name" "$client_name")
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/roles"

    local role_id=""
    role_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$role_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$role_id"
}

function get_user_id() {
    local realm_name=$1
    local username=$2
    local url="${KEYCLOAK_URL}/admin/realms/$realm_name/users"

    local user_id=""
    user_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "username" --arg value "$username" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$user_id"
}

function get_resource_id() {
    local realm_name=$1
    local client_name=$2
    local resource_name=$3

    local client_id=$(get_client_id "$realm_name" "$client_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/resource"

    local resource_id=""
    resource_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$resource_name" '.[] | select(.[$key] == $value)' | jq -r '._id')

    echo "$resource_id"
}

function get_policy_id() {
    local realm_name=$1
    local client_name=$2
    local policy_name=$3

    local client_id=$(get_client_id "$realm_name" "$client_name")
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/policy"

    local policy_id=""
    policy_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$policy_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$policy_id"
}

function get_global_client_scope_id() {
    local realm_name=$1
    local scope_name=$2

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/client-scopes"

    local scope_id=""
    scope_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$scope_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$scope_id"
}

function get_client_client_scope_id() {
    local realm_name=$1
    local scope_name=$2
    local client_name=$3

    local client_id=$(get_client_id "$realm_name" "$client_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/optional-client-scopes"

    local scope_id=""
    scope_id=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" | jq -r --arg key "name" --arg value "$scope_name" '.[] | select(.[$key] == $value)' | jq -r '.id')

    echo "$scope_id"
}

function create_realm() {
    local realm_name=$1
    local url="${KEYCLOAK_URL}/admin/realms"
    local response=""
    local password_policy="length(12) and digits(1) and upperCase(1) and lowerCase(1) and specialChars(1) and notUsername and passwordHistory(5)"

    NEW_REALM_JSON='{
        "realm": "'$realm_name'",
        "enabled": true,
        "displayName": "",
        "sslRequired": "none",
        "registrationAllowed": true,
        "passwordPolicy": "'$password_policy'"
    }'

    if curl_keycloak "$url" "$NEW_REALM_JSON"; then
        print_log "Realm '$realm_name' created"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Realm '$realm_name' already exists"
    else
        print_log "Failed to create realm '$realm_name' with '$HTTP_CODE'"
    fi
}

function prevent_bruteforce() {
    local realm_name=$1

    curl -s -X PUT "${KEYCLOAK_URL}/admin/realms/${realm_name}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "bruteForceProtected": true,
      "maxFailureWaitSeconds": 900,
      "minimumQuickLoginWaitSeconds": 60,
      "waitIncrementSeconds": 60,
      "quickLoginCheckMilliSeconds": 1000,
      "maxDeltaTimeSeconds": 86400,
      "failureFactor": 3
    }'
}


function delete_realm() {
    local realm_name=$1

    curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${realm_name}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" | jq
}

function create_client() {
    local realm_name=$1
    local client_name=$2
    local options="$3"
    local authorization=""
    local authentication=""
    local clientauthentication=""
    local rootUrl=""
    local baseUrl=""
    local redirectUris="*"
    local directAccess=true

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients"

    eval "$options"

    NEW_CLIENT_JSON='{
        "clientId": "'$client_name'",
        "enabled": true,
        "directAccessGrantsEnabled": '$directAccess',
        "authorizationServicesEnabled": '$authorization',
        "serviceAccountsEnabled": '$authentication',
        "publicClient": '$clientauthentication',
        "clientAuthenticatorType": "client-secret",
        "rootUrl": "'$rootUrl'",
        "baseUrl": "'$baseUrl'",
        "redirectUris": [ "'$redirectUris'" ],
        "webOrigins": [ "*" ],
        "protocol": "openid-connect",
        "frontchannelLogout": false
    }'

    if curl_keycloak "$url" "$NEW_CLIENT_JSON"; then
        print_log "Client '$client_name' created"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client '$client_name' already exists"
    else
        print_log "Failed to create client '$client_name' on '$realm_name' with '$HTTP_CODE'"
    fi

}

function create_role() {
    local realm_name=$1
    local role_name=$2
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/roles"

    NEW_ROLE_JSON='{
        "name": "'$role_name'",
        "description": "",
        "composite": false,
        "clientRole": false,
        "attributes": {}
    }'

    if curl_keycloak "$url" "$NEW_ROLE_JSON"; then
        print_log "Role '$role_name' created"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Role '$role_name' already exists"
    else
        print_log "Failed to create role '$role_name' on '$realm_name' with '$HTTP_CODE'"
    fi
}

function create_client_role() {
    local realm_name=$1
    local client_name=$2
    local role_name=$3
    local client_id=""

    client_id=$(get_client_id "$realm_name" "$client_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/roles"

    NEW_CLIENT_ROLE_JSON='{
        "name": "'$role_name'",
        "description": "",
        "composite": false,
        "clientRole": true,
        "attributes": {}
    }'

    if curl_keycloak "$url" "$NEW_CLIENT_ROLE_JSON"; then
        print_log "Client role '$role_name' created for client '$client_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client role '$role_name' already exists for client '$client_name'"
    else
        print_log "Failed to create client role '$role_name' for client '$client_name' with '$HTTP_CODE'"
    fi
}

function create_group() {
    local realm_name=$1
    local group_name=$2
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/groups"

    NEW_GROUP_JSON='{
        "name": "'$group_name'",
        "path": "'/$group_name'",
        "subGroups": [],
        "attributes": {}
   }'

    if curl_keycloak "$url" "$NEW_GROUP_JSON"; then
        print_log "Group '$group_name' created"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Group '$group_name' already exists"
    else
        print_log "Failed to create group '$group_name' on '$realm_name' with '$HTTP_CODE'"
    fi
}

function set_realm_timeouts() {
    local realm_name=$1
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}"

    TIMEOUT_REALM_JSON='{
    "ssoSessionIdleTimeout": '"$SSOSESSIONIDLETIMEOUT"',
    "ssoSessionMaxLifespan": '"$SSOSESSIONMAXLIFESPAN"'
    }'

    if curl_keycloak "$url" "$TIMEOUT_REALM_JSON" "PUT"; then
        print_log "Realm timeouts on '$realm_name' set"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Realm timeouts already set on '$realm_name'"
    else
        print_log "Failed to set realm timeouts with '$HTTP_CODE'"
    fi
}

function map_role_to_group() {
    local realm_name=$1
    local group_name=$2
    local role_name=$3
    local group_id=""
    local role_id=""

    group_id=$(get_group_id  "$realm_name" "$group_name")
    role_id=$(get_realm_role_id "$realm_name" "$role_name")

    local url="$KEYCLOAK_URL/admin/realms/$realm_name/groups/$group_id/role-mappings/realm"

    NEW_ROLE_MAPPING_JSON='[{
        "id": "'$role_id'",
        "name": "'$role_name'"
    }]'

    if curl_keycloak "$url" "$NEW_ROLE_MAPPING_JSON"; then
        print_log "Role '$role_name' mapped to group '$group_name' successfully"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Role '$role_name' already mapped to group '$group_name'"
    else
        print_log "Failed to map role '$role_name' to group '$group_name' on '$realm_name' with $HTTP_CODE"
    fi
}

function create_user() {
    local realm_name=$1
    local username=$2
    local email=$3
    local first_name=$4
    local last_name=$5
    local password=$6
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/users"

    NEW_USER_JSON='{
        "username": "'$username'",
        "enabled": true,
        "emailVerified": true,
        "firstName": "'$first_name'",
        "lastName": "'$last_name'",
        "email": "'$email'",
        "emailVerified": true,

        "credentials": [{
            "type": "password",
            "value": "'$password'",
            "temporary": true
        }]
    }'

    if curl_keycloak "$url" "$NEW_USER_JSON"; then
        print_log "User '$username' created"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "User '$username' already exists"
    else
        print_log "Failed to create '$username' with '$HTTP_CODE'"
    fi
}

function create_client_resource() {
    local realm_name=$1
    local client_name=$2
    local resource_name=$3
    local resource_scopes=$4

    local client_id=$(get_client_id "$realm_name" "$client_name")
    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/resource"

    NEW_RESOURCE_JSON='{
        "name": "'$resource_name'",
        "scopes": [
            {"name": "'$resource_scopes'"}
        ]
    }'

    if curl_keycloak "$url" "$NEW_RESOURCE_JSON"; then
        print_log "Client resource '$resource_name' created for client '$client_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client resource '$resource_name' already exists for client '$client_name'"
    else
        print_log "Failed to create client resource '$resource_name' for client '$client_name' with '$HTTP_CODE'"
    fi
}

function assign_user_realm_role() {
    local realm_name=$1
    local username=$2
    local role_name=$3

    local user_id=$(get_user_id "$realm_name" "$username")
    local role_id=$(get_realm_role_id "$realm_name" "$role_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/users/${user_id}/role-mappings/realm"

    NEW_ROLE_MAPPING_JSON='[{
        "id": "'$role_id'",
        "name": "'$role_name'"
    }]'

    if curl_keycloak "$url" "$NEW_ROLE_MAPPING_JSON"; then
        print_log "Realm role '$role_name' assigned to user '$username'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Realm role '$role_name' already assigned to user '$username'"
    else
        print_log "Failed to assign realm role '$role_name' to user '$username' with '$HTTP_CODE'"
    fi
}

function assign_user_client_role() {
    local realm_name=$1
    local username=$2
    local role_name=$3
    local client_name=$4
    local user_id=""
    local role_id=""
    local client_id=""

    user_id=$(get_user_id "$realm_name" "$username")
    role_id=$(get_client_role_id "$realm_name" "$role_name" "$client_name")
    client_id=$(get_client_id "$realm_name" "$client_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/users/${user_id}/role-mappings/clients/${client_id}"

    NEW_ROLE_MAPPING_JSON='[{
        "id": "'$role_id'",
        "name": "'$role_name'"
    }]'

    if curl_keycloak "$url" "$NEW_ROLE_MAPPING_JSON"; then
        print_log "$client_name role '$role_name' assigned to user '$username'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "$client_name r role '$role_name' already assigned to user '$username'"
    else
        print_log "Failed to assign client '$client_name' role '$role_name' to user '$username' with '$HTTP_CODE'"
    fi
}

function assign_client_scope() {
    local realm_name=$1
    local client_name=$2
    local scope_name=$3
    local client_id=""
    local scope_id=""

    client_id=$(get_client_id "$realm_name" "$client_name")
    scope_id=$(get_global_client_scope_id "$realm_name" "$scope_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/optional-client-scopes/${scope_id}"

    NEW_SCOPE_JSON='[{
        "id": "'$scope_id'",
        "name": "'$scope_name'"
    }]'

    if curl_keycloak "$url" "$NEW_SCOPE_JSON" "PUT"; then
        print_log "Client scope '$scope_name' assigned to client '$client_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client scope '$scope_name' already assigned to client '$client_name'"
    else
        print_log "Failed to assign client scope '$scope_name' to client '$client_name' with '$HTTP_CODE'"
    fi
}


function create_client_scope() {
    local realm_name=$1
    local scope_name=$2


    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/client-scopes"

    NEW_SCOPE_JSON='{
        "name": "'$scope_name'",
        "protocol": "openid-connect",
        "attributes": {
            "include.in.token.scope": "true",
            "display.on.consent.screen": "true"
        }
    }'

    if curl_keycloak "$url" "$NEW_SCOPE_JSON"; then
        print_log "Client scope '$scope_name' added to client '$client_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client scope '$scope_name' already exists for client '$client_name'"
    else
        print_log "Failed to add client scope '$scope_name' to client '$client_name' with '$HTTP_CODE'"
    fi
}

function add_client_scope_mapper() {
    local realm_name=$1
    local scope_name=$2
    local client_name=$3
    local token_claim_name=$4
    local mapper_name=$5

    local client_id=""
    local scope_id=""

    client_id=$(get_client_id "$realm_name" "$client_name")
    scope_id=$(get_client_client_scope_id "$realm_name" "$scope_name" "$client_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/protocol-mappers/add-models"

    NEW_MAPPER_JSON='[
		  {
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
				"usermodel.clientRoleMapping.clientId": "'$client_name'"
			}
		  }
		]'

    if curl_keycloak "$url" "$NEW_MAPPER_JSON"; then
        print_log "Client scope mapper added to client '$client_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client scope mapper already exists for client '$client_name'"
    else
        print_log "Failed to add client scope mapper to client '$client_name' with '$HTTP_CODE'"
    fi
}

function create_client_policy() {
    local realm_name=$1
    local client_name=$2
    local policy_name=$3
    local role_name=$4

    local client_id=""
    local role_id=""

    client_id=$(get_client_id "$realm_name" "$client_name")
    role_id=$(get_client_role_id "$realm_name" "$role_name" "$client_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/policy/role"

    NEW_POLICY_JSON='{
        "name": "'$policy_name'",
        "type": "role",
        "logic": "POSITIVE",
        "decisionStrategy": "UNANIMOUS",
        "roles": [{"id": "'$role_id'"}]
    }'

    if curl_keycloak "$url" "$NEW_POLICY_JSON"; then
        print_log "Client policy '$policy_name' created for role '$role_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client policy '$policy_name' already exists for role '$role_name'"
    else
        print_log "Failed to create client policy '$policy_name' for role '$role_name' with '$HTTP_CODE'"
    fi
}

function create_client_permission() {
    local realm_name=$1
    local client_name=$2
    local permission_name=$3
    local resource_name=$4
    local policy_name=$5

    local client_id=""
    local policy_id=""
    local resource_id=""

    client_id=$(get_client_id "$realm_name" "$client_name")
    policy_id=$(get_policy_id "$realm_name" "$client_name" "$policy_name")
    resource_id=$(get_resource_id "$realm_name" "$client_name" "$resource_name")

    local url="${KEYCLOAK_URL}/admin/realms/${realm_name}/clients/${client_id}/authz/resource-server/permission/resource"

    NEW_PERMISSION_JSON='{
        "name": "'$permission_name'",
        "type": "resource",
        "logic": "POSITIVE",
        "decisionStrategy": "UNANIMOUS",
        "resources": ["'$resource_id'"],
        "policies": ["'$policy_id'"]
    }'

    if curl_keycloak "$url" "$NEW_PERMISSION_JSON"; then
        print_log "Client permission '$permission_name' created for resource '$resource_name' with policy '$policy_name'"
    elif [[ $HTTP_CODE == 409 ]]; then
        print_log "Client permission '$permission_name' already exists for resource '$resource_name' with policy '$policy_name'"
    else
        print_log "Failed to create client permission '$permission_name' for resource '$resource_name' with policy '$policy_name' with '$HTTP_CODE'"
    fi
}

# Initial configuration
print_header "Configuring Keycloak"

get_access_token

create_realm "$KEYCLOAK_REALM"
prevent_bruteforce "$KEYCLOAK_REALM"
create_client "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "authorization='false' authentication='false' clientauthentication='true'"
create_client "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "authorization='true' authentication='true' clientauthentication='false'"

create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "ERAG-admin"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "ERAG-user"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "ERAG-admin"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc" "ERAG-user"

get_or_create_and_store_credentials KEYCLOAK_ERAG_ADMIN erag-admin ""
create_user "$KEYCLOAK_REALM" "erag-admin" "testadmin@example.com" "Test" "Admin" "${NEW_PASSWORD}"
get_or_create_and_store_credentials KEYCLOAK_ERAG_USER erag-user ""
create_user "$KEYCLOAK_REALM" "erag-user" "testuser@example.com" "Test" "User" "${NEW_PASSWORD}"

assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "ERAG-admin" "EnterpriseRAG-oidc"
assign_user_client_role "$KEYCLOAK_REALM" "erag-user" "ERAG-user" "EnterpriseRAG-oidc"

assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "ERAG-admin" "EnterpriseRAG-oidc-backend"
assign_user_client_role "$KEYCLOAK_REALM" "erag-user" "ERAG-user" "EnterpriseRAG-oidc-backend"

set_realm_timeouts "$KEYCLOAK_REALM"
set_realm_timeouts "$KEYCLOAK_DEFAULT_REALM"

# Minio
create_client "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "authorization='false' authentication='true' clientauthentication='true' directAccess='false' rootUrl='https://minio.erag.com' baseUrl='https://minio.erag.com' redirectUris='https://minio.erag.com/oauth_callback'"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "consoleAdmin"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "readonly"
create_client_role "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio" "readwrite"

add_client_scope_mapper "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-minio-dedicated" "EnterpriseRAG-oidc-minio" "minio_roles" "client roles"

assign_user_client_role "$KEYCLOAK_REALM" "erag-admin" "consoleAdmin" "EnterpriseRAG-oidc-minio"
assign_user_client_role "$KEYCLOAK_REALM" "erag-user" "readonly" "EnterpriseRAG-oidc-minio"

# RBAC
create_client_resource "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "admin" "admin-access"
create_client_resource "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "user" "user-access"
create_client_policy "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "admin-policy" "ERAG-admin"
create_client_policy "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "user-policy" "ERAG-user"
create_client_permission "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "admin-permission" "admin" "admin-policy"
create_client_permission "$KEYCLOAK_REALM" "EnterpriseRAG-oidc-backend" "user-permission" "user" "user-policy"
