# Istio service mesh in Intel&reg; AI for Enterprise RAG

This document reviews the implementation of a service mesh for project Intel&reg; AI for Enterprise RAG (RAG).

## Table of Contents

1. [Reasons for Introducing Istio Service Mesh (Istio) into RAG](#reasons-for-introducing-istio-service-mesh-istio-into-rag)
2. [Components of Istio configuration](#components-of-istio-configuration)
    1. [Istio data-plane - ztunnel](#istio-data-plane---ztunnel)
    1. [Plugging Workloads into Mesh](#plugging-workloads-into-mesh)
    1. [Istio Mechanisms - PeerAuthentication](#istio-mechanisms---peerauthentication)
    1. [Istio Mechanisms - AuthorizationPolicy](#istio-mechanisms---authorizationpolicy)
        1. [AuthorizationPolicy and serviceIdentity](#authorizationpolicy-and-serviceidentity)
        1. [AuthorizationPolicy caveats](#authorizationpolicy-caveats)
3. [Deploying Istio in RAG](#deploying-istio-in-rag)
    1. [Configuring PeerAuthentication](#configuring-peerauthentication)
    1. [Configuring AuthorizationPolicy](#configuring-authorizationpolicy)
4. [Istio Operator's Handbook](#istio-operators-handbook)
    1. [Verify that AuthorizationPolicy was Applied](#verify-that-authorizationpolicy-was-applied)
    1. [Introduce New Service into Mesh](#introduce-new-service-into-mesh)
    1. [Kinds of Issues Observed in Ztunnel Log](#kinds-of-issues-observed-in-ztunnel-log)
    1. [Useful Scripts](#useful-scripts)


## Reasons for Introducing Istio Service Mesh (Istio) into RAG

The main reasons to introduce Istio into RAG are:
* Ensuring authentication with mutual TLS (mTLS):
  * Shields services from the outside - Istio won't allow traffic to enter from outside except for specific entry points.
  * Protects traffic within the solution by encrypting all communication.
* Enforcing authorization of services:
  * Limits attack surfaces, as only authorized services can communicate.
  * Allows flexible definition of authorized traffic routes.


## Components of Istio configuration

Common mode of operation for service mesh solutions is to instrument the services with a myriad of proxies that monitor or intercept traffic to offer additional services.

For the RAG project, a new _ambient_ data plane mode of Istio was selected. This approach brings several benefits immediately apparent in the solution:
* Minimal impact on resources in the cluster - there is only a single proxy instance per cluster node.
* Improved configuration response - changes made to Istio rules are reflected immediately by the component not tied to the lifecycle of service pods.

To learn more about Istio ambient mode follow this link: https://istio.io/latest/docs/ambient/overview.


### Istio data-plane - ztunnel

Ztunnel is the component that is closest to the workloads.

It's acting as a proxy for each of the workloads. It's deployed once per each node, but thanks to Istio architecture, it is injected into each workload's network routes.

Ztunnel has the knowledge and responsibility to apply all authentication and authorization policies configured for workloads.

To learn more about ztunnel's operation follow this link: https://istio.io/latest/docs/ambient/architecture/traffic-redirection/.


### Plugging Workloads into Mesh

When Istio is deployed, it has all of its mechanisms ready.<br/>
Workloads need to be simply plugged into the mesh.

The easiest way to achieve this is to apply labels from ambient mode:
* Label the namespace with entry `istio.io/dataplane-mode=ambient` to add all current and future workloads into mesh.
* Label the pod with entry `istio.io/dataplane-mode=ambient` to introduce specific workload into mesh.
* In specific cases, exclude a pod from the mesh with a label `istio.io/dataplane-mode=none` (which would override the namespace setting).


### Istio Mechanisms - PeerAuthentication

`PeerAuthentication` is an Istio custom resource that defines how a workload can be accessed by peers in the mesh.

It is used to enable and enforce mTLS in communication with workloads:

* It's applied mesh-wide, namespace-wide, or at the workload level.
* mTLS is necessary to enable authorization.

What happens without it:
* Mesh default policy is `PERMISSIVE`, which means mTLS is not enforced.

What happens with it (and what can't happen):
* Enables `STRICT` mTLS mode for workload (only allow other mTLS connections).
* May configure `PERMISSIVE` mode (allow some workloads to connect in plain text).
* Individual workloads may set different modes - also at the individual port level.
* No plain text connection will be possible if `STRICT` mode is enforced in the end.

To learn more about `PeerAuthentication` follow this link: https://istio.io/latest/docs/reference/config/security/peer_authentication/.


### Istio Mechanisms - AuthorizationPolicy

`AuthorizationPolicy` is an Istio custom resource that defines rules governing the authorization of traffic between workloads in the mesh.

Basic rules of authorization with `AuthorizationPolicy` resources:
* Authorization is enforced at ztunnel (ztunnel knows and evaluates all the rules).
* Multiple conditions may be applied for fine-grained authorization control.
  * Most useful concept used for authorization is `serviceIdentity`.
* mTLS in `STRICT` mode is needed to allow effective use of the policies.
  * ... or some conditions won’t work (namely `namespace`, `principals`).
* Policies may be defined at namespace level for generic rules and at workload level for fine-grained authorization.

To learn more about `AuthorizationPolicy` follow this link: https://istio.io/latest/docs/reference/config/security/authorization-policy/.


#### `AuthorizationPolicy` and `serviceIdentity`

Istio assigns each workload an identity formed from the trust domain (cluster name), namespace and `ServiceAccount` name.
```yaml
  # namespace edp, ServiceAccount edp-chart
  - cluster.local/ns/edp/sa/edp-chart
```

In case a workload doesn’t have a dedicated ServiceAccount, Kubernetes assigns it a default service account in that namespace.
```yaml
  # namespace edp, ServiceAccount default
  - cluster.local/ns/chatqa/sa/default
```
Workloads may share a `ServiceAccount` only within the same namespace (`ServiceAccount` resource is namespace-scoped).


#### `AuthorizationPolicy` caveats:

* Need to keep workload selectors (the target) in sync.
  * Otherwise workloads may be rendered unprotected.
* Need to keep principals (the source) in sync.
  * Some workloads are stuck at the default `serviceIdentity`, for instance the routers.
  * Development might change `serviceIdentity`.


## Deploying Istio in RAG


### Configuring PeerAuthentication

Authentication configuration is defined in files stored under path: `deployment/components/istio` in the project.
* At present, the authentication is enforced for all namespaces, one namespace at a time, by an installer script.
* Each namespace with pure `STRICT` mTLS mode gets a `PeerAuthentication` resource applied based on file `mTLS-strict.yaml`.
* If any specific authentication rules are needed, they should be placed in a file named `mTLS-strict-*NAMESPACE*.yaml`. Installation utilities will apply this file instead.

Sample authentication policy applied in RAG for `ingress-nginx` namespace:
```yaml
## deployment/istio/mTLS-strict-ingress-nginx.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  # namespace: ingress-nginx
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
  mtls:
    mode: STRICT
  portLevelMtls:
    443: # workload, not service port
      mode: PERMISSIVE
```

* Namespace `ingress-nginx` enforces mTLS `STRICT` mode.
* For the workload `ingress-nginx`, there is an exception on a single port:
  * The port `443` is set in `PERMISSIVE` mode which allows incoming plain text requests.


### Configuring AuthorizationPolicy

* Authorization configuration is defined in files stored under path: `deployment/components/istio/authz`.<br/>
* Each namespace has its own file named `authz-*NAMESPACE*.yaml`. Each of the files may contain multiple instances of `AuthorizationPolicy` for specific workloads.
* All authorization rules are built on a `DENY`-by-default principle.
* For the time being, it’s necessary to review the resources periodically.
  * Alternatively, hints at needed updates show up in logs.


Sample authorization policy applied in RAG:
```yaml
## deployment/istio/authz/authz-edp.yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: edp-postgresql
  namespace: edp
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: postgresql
  action: DENY
  rules:
  - from:
    - source:
        notPrincipals:
        - cluster.local/ns/edp/sa/edp-chart
```

* Policy will be applied in namespace `edp`.
* Workload will be matched by the selector of a label: `app.kubernetes.io/name: postgresql`.
* Policy will `DENY` all traffic directed at the workload.
* Traffic allowed needs to originate from a workload designated by service identity `cluster.local/ns/edp/sa/edp-chart`.


## Istio Operator's Handbook

This chapter provides a handful of resources and information useful for managing Istio configuration in RAG.


### Verify that AuthorizationPolicy was Applied

It's essential to look at ztunnel logs.
* Set up the log filter:
  ```bash
  kubectl logs -f -n istio-system -l=app=ztunnel | grep edp
  ```
* Parsing the log sample:
  ```log
    23:25:37.932494Z     info    
    access  connection complete
    src.addr=10.233.102.158:41772  src.workload="edp-celery-59bdb56886-fx4kt"  src.namespace="edp"
    src.identity="spiffe://cluster.local/ns/edp/sa/edp-chart"
    dst.addr=10.233.102.148:15008  dst.hbone_addr=10.233.102.148:6379
    dst.service="edp-redis-master.edp.svc.cluster.local"  dst.workload="edp-redis-master-0"
    dst.namespace="edp"  dst.identity="spiffe://cluster.local/ns/edp/sa/edp-redis-master"
    direction="inbound" bytes_sent=22 bytes_recv=170 duration="164ms"
  ```
  * `info` on success, `error` for connection issue.
  * `connection complete` - seen most often.
  * `src.identity` is the source principal in policies.
  * `dst.addr` - that’s the address of a ztunnel proxy port for the destination workload.
  * `dst.hbone_addr` - the real address that was requested by the source service.
  * `dst.workload` - identifies the target of the communication.


### Introduce New Service into Mesh

Building on pieces of information provided in this document, the following instruction can be followed to introduce a new service to RAG:
* Identify the new and altered routes in the mesh.
* Identify workloads (Pods) that need to communicate with other parts of the solution (the outbound direction)
  * Ensure each of the workloads has a well-defined `ServiceAccount` associated. Use `default` service account as a last resort.
  * Use the `ServiceAccount` names to build a list of `serviceIdentities` bound as the source of the outbound traffic routes.
  * Modify authorization policies:
    * Include the list of source `serviceIdentities` in the list of allowed principals of the destination workloads.
* Identify workloads of the new service that will receive requests from different workloads in the mesh.
  * Ensure each workload has a stable set of labels to apply as selectors, e.g.: `app.kubernetes.io/name: APP_NAME`.
  * Identify `serviceIdentities` that are allowed to contact workload of the new service.
  * Define new `AuthorizationPolicy` for each of the workloads using the selectors found earlier and authorizing `serviceIdentities` identified in previous steps.

To verify correct operation, the possible actions include:
* Verify that the authorization policies were applied - follow the previous section of this document.
* Verify that the workloads are correctly identified - temporarily apply an empty rules object (which will result in deny-all traffic to the workloads):
  ```yaml
  kind: AuthorizationPolicy
  metadata:
    name: newservice-target
    namespace: newservice
  spec:
    selector:
      matchLabels:
        app.kubernetes.io/name: target
    action: DENY
    rules:
    - {}
  ```
  After that observe ztunnel logs to make sure all requests targeting workload `target-` are denied.


### Kinds of Issues Observed in Ztunnel Log

* Denial by `AuthorizationPolicy`:
  ```log
    error="connection closed due to policy rejection: explicitly denied by: chatqa/chatqa-prompt-tmpl-usvc"
    error="http status: 401 Unauthorized"
  ```
  * Explicit `DENY` policy doesn’t let the source identity to pass through.
  * FIX: find the authorization policy for `dst.namespace` and add the `src.identity` from the log statement to the list of `notPrincipals`.

* Port blocked – possibly by Kubernetes `NetworkPolicy`:
  ```log
    error="io error: deadline has elapsed" error="connection timed out maybe a NetworkPolicy is blocking HBONE port 15008
  ```
  * This does suggest an existing `NetworkPolicy` that allows specific ports, but doesn’t include Istio port 15008.
  * Common case for several helm charts, see: `../deployment/components/keycloak/values.yaml`, `../deployment/components/edp/values.yaml`, `../deployment/components/fingerprint/values.yaml`.

* Denial by `PeerAuthentication`:
  ```log
    error="connection closed due to policy rejection: explicitly denied by: istio-system/istio_converted_static_strict"
  ```
  * Observed when a service without mTLS or outside of the mesh attempts a plain text request to a service under `STRICT` mTLS policy.
  * If impossible to fix otherwise, a port-level exception might be necessary in `PeerAuthentication`.
    * Idea is to configure an mTLS policy in `PERMISSIVE` mode for a given workload port.
  * Create or update a file `mTLS-strict-*NAMESPACE*.yaml` to include an exception for specific port.
  * Start with the contents of `mTLS-strict.yaml` and add another section for the target workload.
    ```yaml
      selector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx
      mtls:
        mode: STRICT
      portLevelMtls:
        443: # workload, not service port
          mode: PERMISSIVE
    ```

* Http 401
  ```log
    401 Unauthorized
  ```
  * Request was rejected by `AuthorizationPolicy` rules.

* Http 503
  ```log
    503 Service Unavailable
  ```
  * The actual target might be unhealthy or unavailable (e.g.: 0 replicas).
  * Review the health of the service.

* Different kinds of issues.
  * Refer to Istio troubleshooting guides – which is updated with new information at least for new releases.
    * https://istio.io/latest/docs/ambient/usage/troubleshoot-ztunnel/.
    * https://github.com/istio/istio/wiki/Troubleshooting-Istio-Ambient.


### Useful Scripts

* Obtain the `istioctl` tool.
  ```bash
  curl -sL https://istio.io/downloadIstioctl | sh -
  ```
  * or visit https://istio.io/latest/docs/ops/diagnostic-tools/istioctl

* Confirm Istio was configured for workload.
  * Check pod for annotation:
    ```yaml
      annotations:
        ambient.istio.io/redirection: enabled
    ```
  * This gets set as soon as Istio configures ztunnel correctly for a pod.

* List workload configuration in mesh with istioctl:
  ```bash
  istioctl ztunnel-config workload
  # ...
  ingress-nginx      ingress-nginx-controller-67bf647946-l4qtg             10.233.102.131 node1 None     HBONE
  istio-system       istio-cni-node-lbcmx                                  
  ```
  * HBONE should be shown for every workload within mesh
  * TCP is left for system or host-network pods

* View all service identities in mesh (to validate AuthorizationPolicies) along with their certificates
  ```bash
  istioctl ztunnel-config services
  # ...
  spiffe://cluster.local/ns/edp/sa/edp-redis-master
  spiffe://cluster.local/ns/fingerprint/sa/fingerprint
  ```

* See or set the ztunnel current log level:
  ```bash
  istioctl zc log ztunnel-kgc87
  ztunnel-kgc87.istio-system:
  current log level is hickory_server::server::server_future=off,access=info,info

  istioctl zc log ztunnel-kgc87 --level=info,access=debug
  ztunnel-kgc87.istio-system:
  current log level is hickory_server::server::server_future=off,access=debug,info
  ```

* For details on `istioctl` tool follow this link: https://istio.io/latest/docs/reference/commands/istioctl/.

* Verify TCP/HTTP connection gets rejected by `AuthorizationPolicy` when requested from outside of the mesh:
    ```bash
    kubectl create ns outofmesh &>/dev/nullecho "$(kubectl run --rm -ti -n outofmesh -q --image nicolaka/netshoot --restart=Never curl -- curl retriever-svc.chatqa.svc.cluster.local:6620 -s -S -w "%{http_code}" -o /dev/null 2>/dev/null)"; kubectl delete ns outofmesh &>/dev/null

    000
    (000 means error, so authorization policy correctly *blocked* connection)
        - includes("000" (?- && "Connection reset"))
    ```
