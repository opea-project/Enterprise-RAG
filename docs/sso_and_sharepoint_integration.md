# Single Sign-On and SharePoint Integration Using Microsoft Entra ID

## Table of Contents

### Single Sign-On (SSO)

1. [SSO Prerequisites](#sso-prerequisites)
2. [Keycloak Configuration via Ansible](#keycloak-configuration-via-ansible)
3. [Keycloak Configuration via Keycloak Web-GUI](#keycloak-configuration-via-keycloak-web-gui)

### SharePoint Integration

4. [Overview](#sharepoint-integration-overview)
5. [SharePoint Prerequisites](#sharepoint-prerequisites)
6. [Deploying with SharePoint Enabled](#deploying-with-sharepoint-enabled)
7. [Managing SharePoint Sites](#managing-sharepoint-sites)
8. [Scheduled Synchronization](#scheduled-synchronization)
9. [Role-Based Access Control (RBAC) with SharePoint](#role-based-access-control-rbac-with-sharepoint)

---

# Part 1 — Single Sign-On (SSO)

## SSO Prerequisites

> [!WARNING]
> **App Registration is required for every Intel® AI for Enterprise RAG deployment that uses SSO.** Even if your organisation already has Entra ID SSO configured for other applications, you must create a dedicated App Registration for Enterprise RAG so that Keycloak can act as an OIDC client towards Entra ID.

1. Configured and working Microsoft Entra ID:
    - three new groups - one for `erag-admins`, one for `erag-users`, and one for `erag-maintainers`
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
    | `tenant_id` | **App registrations → [your app] → Overview** → `Directory (tenant) ID` |

    The `alias` is a free-form identifier you choose yourself (e.g. `enterprise-sso`), but be sure to match the element of redirect URL inputed in App Registration.

3. App roles created for Enterprise RAG Admin, User, and Maintainer. Field `Value` should match `EnterpriseRAG.AdminAccess` for Admin role, `EnterpriseRAG.UserAccess` for User role, and `EnterpriseRAG.MaintainerAccess` for Maintainer role (any custom value changes require modifications in [keycloak_configurator.sh](../deployment/roles/application/keycloak/files/keycloak_configurator_job.sh)). Check out following instructions for more details: [here](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps#assign-users-and-groups-to-roles).
4. Assignments created between the app and the groups based on appropriate app roles. Check out instructions from the previous point.
5. Users added to the newly created groups - `erag-admins`, `erag-users`, or `erag-maintainers` - in Microsoft Entra ID.

## Keycloak Configuration via Ansible

To automatically configure Keycloak during deployment to use SSO configure the following settings in `deployment/inventory/**/config.yaml`:

```yaml
keycloak:
  oidc:
    endpoint: ""       # OpenID Connect metadata document URL from App registration → Overview → Endpoints → OpenID Connect metadata document
    alias: ""          # Free-form identifier shown as the SSO link on the Keycloak login page (e.g. enterprise-sso)
    client_id: ""      # Application (client) ID from App registration → Overview
    client_secret: ""  # Secret Value from App registration → Certificates & secrets
    tenant_id: ""      # Directory (tenant) ID from App registration → Overview
```

## Keycloak Configuration via Keycloak Web-GUI

To configure Intel® AI for Enterprise RAG SSO using Azure Single Sign-On, follow these steps:

1. Log in as `admin` user into Keycloak and select the `EnterpriseRAG` realm.
2. Choose `Identity providers` from the left menu.
3. Add a new `OpenID Connect Identity Provider` and configure:
     - Field `Alias` - enter your SSO alias, for example `enterprise-sso`
     - Field `Display name` - enter your link display name to redirect to external SSO, for example `Enterprise SSO`
     - Field `Discovery endpoint` - enter your `OpenID Connect metadata document`. Configuration fields should autopopulate
4. Create three `Realm roles` in the left menu.
     1. `ERAG-SSO-Admin` and assign following roles:
          - `(EnterpriseRAG-oidc) ERAG-admin`
          - `(EnterpriseRAG-oidc-backend) ERAG-admin`
          - `(EnterpriseRAG-oidc-minio) erag-admin-group`
          - `(EnterpriseRAG-oidc-minio) consoleAdmin` # if using internal SeaweedFS
     2. `ERAG-SSO-User` and assign following roles:
          - `(EnterpriseRAG-oidc) ERAG-user`
          - `(EnterpriseRAG-oidc-backend) ERAG-user`
          - `(EnterpriseRAG-oidc-minio) erag-user-group`
     3. `ERAG-SSO-Maintainer` and assign following roles:
          - `(EnterpriseRAG-oidc) ERAG-user`
          - `(EnterpriseRAG-oidc) ERAG-maintainer`
          - `(EnterpriseRAG-oidc-backend) ERAG-user`
          - `(EnterpriseRAG-oidc-backend) ERAG-maintainer`
          - `(EnterpriseRAG-oidc-minio) erag-user-group`
          - `(EnterpriseRAG-oidc-minio) erag-maintainer-group`
5. Configure three `Identity mappers` in `Mappers` under the created `Identity provider`:
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
     3. Add Identity Provider Mapper - for realm role `ERAG-SSO-Maintainer`:
          - Field `Name` - type in your mapper name
          - Field `Sync mode override` - select `Force`
          - Field `Mapper type` - enter `Claim to Role`
          - Filed `Claim` - enter `roles`
          - Field `Group` - select `ERAG-SSO-Maintainer`

After this configuration, the Keycloak login page should have an additional link at the bottom of the login form - named `Enterprise SSO`. This should redirect you to the Azure login page.

Depending on users' group membership in Microsoft Entra ID (`erag-admins`, `erag-users`, or `erag-maintainers`), users will have appropriate permissions mapped. For example, `erag-admins` will have full access to the admin panel, while `erag-maintainers` will have access to the upload panel and read-only status view of microservices.

---

# Part 2 — SharePoint Integration

## SharePoint Integration Overview

Intel® AI for Enterprise RAG can integrate with Microsoft SharePoint Online to ingest documents directly from SharePoint sites into the knowledge base. The integration works under the following premises:

- **Site-level access model.** Microsoft Graph API does not expose an endpoint to list all SharePoint sites an application has been granted access to. Because of this, sites must be **manually added to the tracking list** inside Intel® AI for Enterprise RAG. When adding a site, the system verifies that the registered App Registration has the required permissions; if access is denied, the site cannot be added.
- **SharePoint is the source of truth.** SharePoint remains the authoritative source for file content. When synchronization runs, the system compares files in tracked SharePoint sites against its own database (PostgreSQL `FileStatus` records with `site_name` set) and downloads new or updated files on demand for processing and embedding. Files that have been deleted on SharePoint are removed from the knowledge base.
- **File upload to SharePoint.** Users can upload files directly to a SharePoint site via the UI or API. Uploaded files appear in the site's default document library.
- **RBAC support.** When RBAC is enabled, Intel® AI for Enterprise RAG can verify per-user SharePoint access. Only users who have access to a given SharePoint site (verified via their delegated Microsoft token through Keycloak broker) will see files from that site in their search results.

## SharePoint Prerequisites

> [!IMPORTANT]
> SharePoint integration requires a working SSO setup as described in [Part 1](#part-1--single-sign-on-sso). The same App Registration is used for both SSO and SharePoint access.

In addition to the SSO prerequisites, the following are required:

1. **API Permissions** — the App Registration must have the following Microsoft Graph **application permissions** granted (with admin consent):

    | Permission | Type | Purpose |
    |---|---|---|
    | `Sites.Selected` | Application | Read and write items in all SharePoint site collections |
    | `Sites.Selected` | Delegated | Read and write items in all SharePoint site collections on behalf of the signed-in user |
    | `User.Read` | Delegated | Sign in and read user profile |

    To configure API permissions, go to **Microsoft Entra ID → App registrations → [your app] → API permissions → Add a permission**.

2. **Site-level access** — each SharePoint site you want to integrate must grant read/write access to the App Registration. This is done via the SharePoint admin center or through the Microsoft Graph Sites.Selected permission model:
    - Grant the application access to specific sites using the **Microsoft Graph API** `sites/{site-id}/permissions` endpoint, or
    - Use the **SharePoint admin center** to manage app access to sites.

    For detailed instructions, see [Granting access via Sites.Selected](https://learn.microsoft.com/en-us/graph/api/site-post-permissions).

## Deploying with SharePoint Enabled

SharePoint integration is automatically enabled when the `keycloak.oidc` block is configured in `deployment/inventory/**/config.yaml`. The same parameters used for SSO are also used for SharePoint access.

During deployment, Ansible maps these values to Kubernetes secrets consumed by the EDP backend and Celery workers:

| `config.yaml` field | Environment variable |
|---|---|
| `keycloak.oidc.tenant_id` | `SHAREPOINT_TENANT_ID` |
| `keycloak.oidc.client_id` | `SHAREPOINT_CLIENT_ID` |
| `keycloak.oidc.client_secret` | `SHAREPOINT_CLIENT_SECRET` |
| `keycloak.oidc.alias` | `KEYCLOAK_BROKER_IDP_ALIAS` |

If all three SharePoint environment variables (`SHAREPOINT_TENANT_ID`, `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET`) are set and non-empty, the SharePoint integration is active. Otherwise, SharePoint API endpoints return `404`.

## Managing SharePoint Sites

### Adding a Site

> [!NOTE]
> `<FQDN>` refers to the `FQDN` parameter defined in `deployment/inventory/**/config.yaml`. By default it is `erag.com`.

Once Intel® AI for Enterprise RAG is deployed with SharePoint enabled, sites can be added via the UI or the API:

```
POST https://<FQDN>/api/v1/edp/sharepoint/sites
{
  "site_url": "https://contoso.sharepoint.com/sites/my-team-site"
}
```

The system will:
1. Resolve the site URL via Microsoft Graph to obtain the site's graph ID.
2. Verify the App Registration has access to the site.
3. Create a tracking record in the database.

If the app does not have access to the site, the request will fail with a `403 Forbidden` error. Ensure the site has granted access to the App Registration as described in [SharePoint Prerequisites](#sharepoint-prerequisites).

### Synchronizing Files

After a site is tracked, trigger a synchronization to download its files:

- **Preview changes:** `GET https://<FQDN>/api/v1/edp/sharepoint/sync` — returns a list of actions (add, update, delete, no action) without applying them.
- **Apply sync:** `POST https://<FQDN>/api/v1/edp/sharepoint/sync` — downloads new and updated files from SharePoint into the knowledge base and removes files that no longer exist on the site.

During synchronization, files are downloaded from SharePoint, processed, and ingested into the vector knowledge base. Each file is identified by its `site_name` and `object_name` (e.g., `Documents/Reports/Q1.pdf`).

### Uploading Files via UI

Users can upload files directly to a tracked SharePoint site through the Intel® AI for Enterprise RAG UI or via the API. Files uploaded this way are stored in the SharePoint site's default document library (`Documents/`). A synchronization must be triggered separately for the uploaded file to appear in the knowledge base.

**API request:**
```
POST https://<FQDN>/api/v1/edp/sharepoint/files?site_id=<graph_site_id>
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <binary>
```

| Parameter | Location | Description |
|---|---|---|
| `site_id` | Query string | The Microsoft Graph site ID of the tracked SharePoint site |
| `file` | Form data | The file to upload |

**Response:**
```json
{
  "message": "File 'report.pdf' uploaded to SharePoint site.",
  "web_url": "https://contoso.sharepoint.com/sites/my-team-site/Shared%20Documents/report.pdf"
}
```

> [!NOTE]
> This differs from S3 bucket uploads, which use presigned URLs. SharePoint file uploads go through the EDP backend, which forwards them to the Microsoft Graph API to handler any permission validation.

### Fetching a File URL

For files originating from SharePoint, the system provides a web URL that opens the file directly on the SharePoint site. The returned URL points to the file on the SharePoint site. Access control is handled by SharePoint itself — only users with appropriate permissions on the site can open the file.

**API request:**
```
POST https://<FQDN>/api/v1/edp/sharepoint/file-url
Content-Type: application/json
Authorization: Bearer <token>

{
  "site_name": "My Team Site",
  "object_name": "Documents/Reports/Q1.pdf"
}
```

| Field | Description |
|---|---|
| `site_name` | The display name of the tracked SharePoint site |
| `object_name` | The path of the file within the site, in the format `{drive_name}/{relative_path}` |

**Response:**
```json
{
  "url": "https://contoso.sharepoint.com/sites/my-team-site/Shared%20Documents/Reports/Q1.pdf"
}
```

### Removing a File

Deleting a SharePoint file via the UI or API removes it from both the vector knowledge base and the SharePoint site itself.

**API request:**
```
DELETE https://<FQDN>/api/v1/edp/sharepoint/files
Content-Type: application/json
Authorization: Bearer <token>

{
  "site_name": "My Team Site",
  "object_name": "Documents/Reports/Q1.pdf"
}
```

### Disconnecting a Site

Disconnecting a site from tracking:
- Deletes all files from the knowledge base (vector database) that came from that site.
- Removes the tracking record from the database.
- **Does not** delete any files from the SharePoint site itself — the site remains intact.

## Scheduled Synchronization

By default, synchronization is manual (triggered via the UI or API). To enable automatic periodic synchronization, configure the following in `deployment/inventory/**/config.yaml`:

```yaml
edp:
  scheduledSync:
    enabled: true
    syncPeriodSeconds: "60"                  # General bucket sync interval (seconds)
    sharepointSyncPeriodSeconds: "60"        # SharePoint-specific sync interval (seconds)
```

| Parameter | Default | Description |
|---|---|---|
| `enabled` | `false` | Enable or disable scheduled synchronization |
| `syncPeriodSeconds` | `"60"` | Interval in seconds between general storage sync tasks |
| `sharepointSyncPeriodSeconds` | `"60"` | Interval in seconds between SharePoint sync tasks. Falls back to `syncPeriodSeconds` if not set |

When enabled, the Celery worker periodically runs the sync task to keep the knowledge base up to date with SharePoint without manual intervention.

## Role-Based Access Control (RBAC) with SharePoint

When RBAC is enabled in Intel® AI for Enterprise RAG (`edp.rbac.enabled: true`), SharePoint site access is checked per user:

- The user's Keycloak session token is exchanged for their Microsoft Graph token via the Keycloak broker.
- For each tracked SharePoint site, the system checks whether the user has access to that site.
- Only files from accessible sites (and permitted S3 buckets) are returned in search results and file listings. The `/api/list_bucket_with_permissions` endpoint returns both `buckets` and `sites` lists.

This ensures that SharePoint document-level permissions are respected within Intel® AI for Enterprise RAG.

To enable RBAC, add the following to `config.yaml`:

```yaml
edp:
  rbac:
    enabled: true
```
