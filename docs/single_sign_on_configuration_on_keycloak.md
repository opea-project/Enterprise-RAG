# Single Sign-On Integration Using Microsoft Entra ID (formerly Azure Active Directory)

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Keycloak Configuration via Ansible](#keycloak-configuration-via-ansible)
3. [Keycloak Configuration via Keycloak Web-GUI](#keycloak-configuration-via-keycloak-web-gui)

---

## Prerequisites

1. Configured and working Microsoft Entra ID:
    - deployed Intel® AI for Enterprise RAG application
    - preconfigured and working SSO for other applications
    - two new groups - one for `erag-admins`, one for `erag-users` - save `Object ID` for these entities
    - defined user accounts that can be later added to either `erag-admins` or `erag-users` groups 
2. Registered a new Azure `App registration`:
    - configured with Redirect URI `https://auth.erag.com/realms/EnterpriseRAG/broker/oidc/endpoint`
    - in App registration -> Overview - save the `Application (client) ID` value
    - in App registration -> Overview -> Endpoints - save `OpenID Connect metadata document` value
    - in App registration -> Manage -> Certificates & secrets -> New client secret - create and save `Client secret` value
3. Users added to the newly created groups, either `erag-admins` or `erag-users` in Microsoft Entra ID

## Keycloak Configuration via Ansible

To automatically configure Keycloak during deployment to use SSO configure the following settings in `deployment/inventory/**/config.yaml`:

```yaml
keycloak:
  oidc:
    endpoint: ""
    alias: ""
    client_id: ""
    client_secret: ""
    admin_gid: ""
    user_gid: ""
```

`admin_gid` and `user_gid` fields are optional - you can configure them later if you do not want to use hardcoded groups.

## Keycloak Configuration via Keycloak Web-GUI

To configure Enterprise RAG SSO using Azure Single Sign-On, follow these steps:

1. Log in as `admin` user into Keycloak and select the `EnterpriseRAG` realm.
2. Choose `Identity providers` from the left menu.
3. Add a new `OpenID Connect Identity Provider` and configure:
     - Field `Alias` - enter your SSO alias, for example `enterprise-sso`
     - Field `Display name` - enter your link display name to redirect to external SSO, for example `Enterprise SSO`
     - Field `Discovery endpoint` - enter your `OpenID Connect metadata document`. Configuration fields should autopopulate
4. Choose `Groups` in the left menu. Then create the following groups:
     1. `erag-admin-group` should consist of the following groups from Keycloak:
          - `(EnterpriseRAG-oidc) ERAG-admin`
          - `(EnterpriseRAG-oidc-backend) ERAG-admin`
          - `(EnterpriseRAG-oidc-minio) consoleAdmin` # if using internal MinIO
     2. `erag-user-group` should consist of the following groups from Keycloak:
          - `(EnterpriseRAG-oidc) ERAG-user`
          - `(EnterpriseRAG-oidc-backend) ERAG-user`
          - `(EnterpriseRAG-oidc-minio) readonly` # if using internal MinIO
5. Configure two `Identity mappers` in `Mappers` under the created `Identity provider`:
     1. Add Identity Provider Mapper - for group `erag-admin-group`:
          - Field `Name` - this is the `Object ID` from `erag-admins` from Microsoft Entra ID
          - Field `Mapper type` - enter `Hardcoded Group`
          - Field `Group` - select `erag-admin-group`
     2. Add Identity Provider Mapper - for group `erag-user-group`:
          - Field `Name` - this is the `Object ID` from `erag-users` from Microsoft Entra ID
          - Field `Mapper type` - enter `Hardcoded Group`
          - Field `Group` - select `erag-user-group`

After this configuration, the Keycloak login page should have an additional link at the bottom of the login form - named `Enterprise SSO`. This should redirect you to the Azure login page.

Depending on users' group membership in Microsoft Entra ID (either `erag-admins` or `erag-users`), users will have appropriate permissions mapped. For example, `erag-admins` will have access to the admin panel.
