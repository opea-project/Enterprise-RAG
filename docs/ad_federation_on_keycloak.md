# Microsoft Active Directory Integration

Active Directory Federation enables seamless integration between Microsoft Active Directory and your application, allowing users to log in using their existing domain credentials. By federating with Active Directory, you can centrally manage authentication and authorization, leveraging AD groups to control access to application features and resources. This approach simplifies user management, enhances security, and ensures that access policies are consistent with your organization's existing identity infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment configuration](#deployment-configuration)
   1. [LDAP over SSL](#ldap-over-ssl)
3. [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. Deployment of ADFS
Microsoft Active Directory Federation Services (ADFS) deployed to enable federated identity management.
Network access from keycloak to ADFS server using `ldap` protocol on port `389` or using `ldaps` on port `636` is required.

2. Service Account for LDAP Bind
A dedicated service account is required to serve as the Bind DN. This account is used for authenticated LDAP queries from Keycloak. Credentials are configured via yaml as `bind_dn` and `bind_password`. This account does not require any group assignment.

3. Organizational Unit for Groups
A specific Organizational Unit (OU) created to contain the groups used for access control. This OU serves as the base DN for group searches.

4. Group Creation and Mapping
LDAP groups created within the designated OU and configured using appropriate LDAP filters. These groups are mapped directly to application-specific roles and policies as follows:
  - Enterprise RAG user role mappings
    - `ERAG-admin` → Administrative privileges within ERAG
    - `ERAG-user` → Standard user privileges within ERAG
  - SeaweedFS policy mappings (if using SeaweedFS)
    - `erag-admin-group` → access to all buckets
    - `erag-user-group` → restriced access only to selected buckets

> [!NOTE]
> The group names in Active Directory must exactly match the group names configured in both Keycloak and SeaweedFS policies. This ensures that group-based access controls function correctly and users are assigned the appropriate roles and permissions.
> Only direct group memberships are supported when integrating Active Directory with Keycloak via federation. Users must be explicitly listed in the member attribute of the target AD group. Group nesting (i.e., indirect membership via nested groups) is not resolved and will not be recognized by Keycloak during authentication or role mapping.

To get full DN names you can use the following PowerShell commands:

```powershell
Get-ADUser -Identity <user_name> -Properties DistinguishedName | Select-Object DistinguishedName
Get-ADGroup -Identity <group_name> -Properties DistinguishedName | Select-Object DistinguishedName
```

## Deployment configuration

To automatically configure Keycloak during deployment to use SSO configure the following settings in [deployment/inventory/sample/config.yaml](../deployment/inventory/sample/config.yaml):

```yaml
keycloak:
  federation:
    endpoint: "ldap://10.0.0.1:389" # Must begin with ldap://
    bind_dn: ""
    bind_password: ""
    users_dn: ""
    groups_dn: ""
    user_attribute: "" # (Optional) default = sAMAccountName
    user_group_ldap_filter: "" # (Optional) default = (cn=ERAG-user) # remember that parentheses are required
    admin_group_ldap_filter: "" # (Optional) default = (cn=ERAG-admin) # remember that parentheses are required
```

### Additional configuration

The installation scripts automatically create LDAP group mappers that link Active Directory groups to Keycloak client roles. To integrate additional AD groups beyond the default `ERAG-user` and `ERAG-admin` (groups for portal access) and `erag-user-group` and `erag-admin-group` (groups for storage access policies), you may need to modify the default mapper's LDAP filter. For example, you can use a wildcard-based filter to match multiple groups dynamically. Note that each Keycloak realm client supports only one group mapper, so all desired groups must be included in a single, properly configured LDAP filter expression.

Similarly, when integrating with storage systems (such as SeaweedFS), you must create or update access policies to control bucket permissions. Ensure that policy names exactly match the role names defined in the `EnterpriseRAG-oidc-minio` Keycloak realm client. When provisioning new buckets, add them to the appropriate policy to maintain consistent access control aligned with your AD group mappings.

### LDAP over SSL

To configure LDAP over SSL (LDAPS), follow these steps:

1. **Enable LDAPS in Microsoft Active Directory** - Refer to this https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/enable-ldap-over-ssl-3rd-certification-authority to enable the LDAPS protocol.
2. **Export the Certificate Authority (CA) Certificate** - Instructions are available https://learn.microsoft.com/en-us/troubleshoot/windows-server/certificates-and-public-key-infrastructure-pki/export-root-certification-authority-certificate.

Once exported, place the certificate file in the [deployment/components/keycloak/certs](../deployment/components/keycloak/certs/) directory. Files in this location will be included in a Kubernetes Secret.

Next, update the LDAP endpoint in your configuration file at [deployment/inventory/sample/config.yaml](../deployment/inventory/sample/config.yaml) to use the `ldaps://` scheme.

> [!NOTE]
> Certificates exported from Windows Server are typically issued for domain names rather than IP addresses. If this is the case, you can define additional `hostAliases` (static DNS entries) as shown in an example below. This allows keycloak to connect to your server and validate the certificate using the domain name.

```yaml
keycloak:
  federation:
    endpoint: "ldaps://dc.example.com:636" # Must begin with ldaps://
    bind_dn: ""
    bind_password: ""
    users_dn: ""
    groups_dn: ""
    user_attribute: "" # (Optional) default = sAMAccountName
    user_group_ldap_filter: "" # (Optional) default = (cn=ERAG-user) # remember that parentheses are required
    admin_group_ldap_filter: "" # (Optional) default = (cn=ERAG-admin) # remember that parentheses are required
  hostAliases:
    - ip: "10.0.0.1"
      hostnames:
        - "dc.example.com" # use lowercase only
```

## Troubleshooting

Keycloak provides basic diagnostic capabilities through its Web UI. Administrators can:

- Test LDAP Connection: Verify connectivity to the Active Directory server.
- Test Authentication: Confirm that user credentials are correctly validated against AD.

For deeper troubleshooting:

- Review Keycloak Container Logs: Inspect runtime logs for errors or warnings related to LDAP integration, authentication failures, or group mapping issues.
- Consult Official Documentation: For advanced debugging techniques, configuration parameters, and known issues, refer to the https://www.keycloak.org/documentation.
