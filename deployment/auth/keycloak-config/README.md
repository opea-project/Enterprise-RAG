# Updating keycloak configuration
Follow this to apply the keycloak configuration when installed for the first time on the system and there is no 'EnterpriseRAG' realm in the keycloak.
</br>Below steps can be used to add following configurations to keycloak

1. Create a new realm 'EnterpriseRAG'
2. Create new client 'EnterpriseRAG-oidc' to the 'EnterpriseRAG' realm
3. Setup redirect URIs for the client 'EnterpriseRAG-oidc'
4. Create 2 new realm roles 'ERAG-admin' and 'ERAG-user' in the 'EnterpriseRAG' realm.
5. Create 2 new groups 'ERAG-admins' (associated with ERAG-admin realm role) and 'ERAG-users' (associated with ERAG-user realm role). The users added in a specific group will inherit all the roles belonging to the group. 
6. Add 'Group Membership' mapper in the client 'EnterpriseRAG-oidc' with the name 'groups'. This is to get the user's group info from userinfo.
7. Add 'realm roles' mapper in the client 'EnterpriseRAG-oidc' to get user's realm roles in the userinfo.
8. Create 2 new users. 'testuser' belonging to the group 'ERAG-users' and 'testadmin' belonging to the group 'ERAG-admins'. Password for both users is set to 'password'
9. After running all the below steps, run 'echo $CLIENT_SECRET' to get the client secret.

```sh
#Get keycloak access token
ACCESS_TOKEN=$(curl -X POST "http://<keycloak-service>/realms/master/protocol/openid-connect/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "client_id=admin-cli" \
-d "username=admin" \
-d "password=admin" \
-d "grant_type=password" | jq -r '.access_token')


#Add realm with the name EnterpriseRAG with saved config
curl -X POST \
     -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d @ERAG-realm-export.json \
     http://<keycloak-service>/admin/realms
	 
#Get ID of the client 
C_ID=$(curl -X GET "http://<keycloak-service>/admin/realms/EnterpriseRAG/clients" -H "Authorization: Bearer $ACCESS_TOKEN" -H "Accept: application/json" | jq -r --arg key "clientId" --arg value "EnterpriseRAG-oidc" '.[] | select(.[$key] == $value)' | jq -r '.id')

#Get client secret. This will be needed by APISIX and UI
CLIENT_SECRET=$(curl -X POST \
     -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     "http://<keycloak-service>/admin/realms/EnterpriseRAG/clients/$C_ID/client-secret" | \
     jq -r '.value')

	 
#Add test user in EnterpriseRAG realm
curl -X POST "http://<keycloak-service>/admin/realms/EnterpriseRAG/users" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "username": "testuser",
  "enabled": true,
  "emailVerified": true,
  "firstName": "Test",
  "lastName": "User",
  "email": "testuser@example.com",
  "groups": ["ERAG-users"],
  "credentials": [{
    "type": "password",
    "value": "password",
    "temporary": false
  }]
}'


#Add test admin in EnterpriseRAG realm
curl -X POST "http://<keycloak-service>/admin/realms/EnterpriseRAG/users" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "username": "testadmin",
  "enabled": true,
  "emailVerified": true,
  "firstName": "Test",
  "lastName": "Admin",
  "email": "testadmin@example.com",
  "groups": ["ERAG-admins"],
  "credentials": [{
    "type": "password",
    "value": "password",
    "temporary": false
  }]
}'
```

</br>

## Note

UI and APISIX apigateway needs the following parameters to work with keycloak
1. Realm name: EnterpriseRAG
2. Client Id: EnterpriseRAG-oidc
3. Client Secret: Output of 'echo $CLIENT_SECRET'
4. Keycloak well known configuration: `http://<keycloak-service>/realms/EnterpriseRAG/.well-known/openid-configuration`
5. Keycloak Authorize URL: `http://<keycloak-service>/realms/EnterpriseRAG/protocol/openid-connect/auth`
6. Keycloak Introspection URL: `http://<keycloak-service>/realms/EnterpriseRAG/protocol/openid-connect/token/introspect`
7. Keycloak Access Token URL: `http://<keycloak-service>/realms/EnterpriseRAG/protocol/openid-connect/token`
8. Keycloak JWKS URL: `http://<keycloak-service>/realms/EnterpriseRAG/protocol/openid-connect/certs`
9. Keycloak Logout URL: `http://<keycloak-service>/realms/EnterpriseRAG/protocol/openid-connect/logout?post_logout_redirect_uri={<UI_REDIRECT_URI>}&client_id={os.getenv('EnterpriseRAG')}`