# Single Sign-On Integration Using Microsoft Entra ID (formerly Azure Active Directory)

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Keycloak Configuration via Ansible](#keycloak-configuration-via-ansible)
3. [Keycloak Configuration via Keycloak Web-GUI](#keycloak-configuration-via-keycloak-web-gui)

---

## Prerequisites

> [!WARNING]
> **App Registration is required for every Intel® AI for Enterprise RAG deployment that uses SSO.** Even if your organisation already has Entra ID SSO configured for other applications, you must create a dedicated App Registration for Enterprise RAG so that Keycloak can act as an OIDC client towards Entra ID.

1. Configured and working Microsoft Entra ID:
    - two new groups - one for `erag-admins`, one for `erag-users`
2. Registered a new Azure `App registration`:
    - In **Microsoft Entra ID → App registrations → New registration**:
        - Set a name (e.g. `Enterprise RAG`)
        - Under **Redirect URL**, select platform `Web` and enter `https://auth.erag.com/realms/EnterpriseRAG/broker/<alias_name>/endpoint`, where `alias_name` would be the name of SSO identifier in Keycloak e.g. `enterprise-sso`.
    - After creation, collect the following values:

    | Config parameter | Where to find it in the Azure portal |
    |---|---|
    | `client_id` | **App registrations → [your app] → Overview** → `Application (client) ID` |
    | `endpoint` | **App registrations → [your app] → Overview → Endpoints** (top bar button) → `OpenID Connect metadata document` URL |
    | `client_secret` | **App registrations → [your app] → Certificates & secrets → Client secrets → New client secret** → copy the `Value` field immediately after creation (it is only shown once) |

    The `alias` is a free-form identifier you choose yourself (e.g. `enterprise-sso`), but be sure to match the element of redirect URL inputed in App Registration.

3. App roles created both for Enterprise RAG Admin and for Enterprise RAG User. Field `Value` should match `EnterpriseRAG.AdminAccess` for Admin role and `EnterpriseRAG.UserAccess` for User role (any custom value changes require modifications in [keycloak_configurator.sh line 1140](../deployment/roles/application/keycloak/files/keycloak_configurator.sh)). Check out following instructions for more details: [here](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps#assign-users-and-groups-to-roles).
4. Assignments created between the app and the groups based on appropriate app roles. Check out instructions from the previous point.
5. Users added to the newly created groups, either `erag-admins` or `erag-users` in Microsoft Entra ID.

## Keycloak Configuration via Ansible

To automatically configure Keycloak during deployment to use SSO configure the following settings in `deployment/inventory/**/config.yaml`:

```yaml
keycloak:
  oidc:
    endpoint: ""       # OpenID Connect metadata document URL from App registration → Overview → Endpoints → OpenID Connect metadata document
    alias: ""          # Free-form identifier shown as the SSO link on the Keycloak login page (e.g. enterprise-sso)
    client_id: ""      # Application (client) ID from App registration → Overview
    client_secret: ""  # Secret Value from App registration → Certificates & secrets
```

## Keycloak Configuration via Keycloak Web-GUI

To configure Intel® AI for Enterprise RAG SSO using Azure Single Sign-On, follow these steps:

1. Log in as `admin` user into Keycloak and select the `EnterpriseRAG` realm.
2. Choose `Identity providers` from the left menu.
3. Add a new `OpenID Connect Identity Provider` and configure:
     - Field `Alias` - enter your SSO alias, for example `enterprise-sso`
     - Field `Display name` - enter your link display name to redirect to external SSO, for example `Enterprise SSO`
     - Field `Discovery endpoint` - enter your `OpenID Connect metadata document`. Configuration fields should autopopulate
4. Create two `Realm roles` in the left menu.
     1. `ERAG-SSO-Admin` and assign following roles:
          - `(EnterpriseRAG-oidc) ERAG-admin`
          - `(EnterpriseRAG-oidc-backend) ERAG-admin`
          - `(EnterpriseRAG-oidc-minio) erag-admin-group`
          - `(EnterpriseRAG-oidc-minio) consoleAdmin` # if using internal SeaweedFS
     2. `ERAG-SSO-User` and assign following roles:
          - `(EnterpriseRAG-oidc) ERAG-user`
          - `(EnterpriseRAG-oidc-backend) ERAG-user`
          - `(EnterpriseRAG-oidc-minio) erag-user-group`
5. Configure two `Identity mappers` in `Mappers` under the created `Identity provider`:
     1. Add Identity Provider Mapper - for realm role `ERAG-SSO-Admin`:
          - Field `Name` - type in your mapper name
          - Field `Sync mode override` - select `Force`
          - Field `Mapper type` - enter `Claim to Role`
          - Filed `Claim` - enter `roles`
          - Field `Group` - select `ERAG-SSO-Admin`
     2. Add Identity Provider Mapper - for realm role `ERAG-SSO-User`:
          - Field `Name` - type in your mapper name
          - Field `Sync mode override` - select `Force`
          - Field `Mapper type` - enter `Claim to Role`
          - Filed `Claim` - enter `roles`
          - Field `Group` - select `ERAG-SSO-User`

After this configuration, the Keycloak login page should have an additional link at the bottom of the login form - named `Enterprise SSO`. This should redirect you to the Azure login page.

Depending on users' group membership in Microsoft Entra ID (either `erag-admins` or `erag-users`), users will have appropriate permissions mapped. For example, `erag-admins` will have access to the admin panel.
