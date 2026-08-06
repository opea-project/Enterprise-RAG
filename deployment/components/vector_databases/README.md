# Vector Databases

This helm chart allows creation of selected vector databases. Those are optional if you wish to use external vector databases with Enterprise RAG. If you do not have any external and supported by `VectorStore` databases, feel free to enable one of the currently available ones. 

Currently supported databases:
- [Redis-cluster 8.2.2](#redis-cluster)
- [Microsoft SQL Server 2025](#microsoft-sql-server-2025)

Experimental, not supported for production use:
- [Qdrant 1.19.0](#qdrant)

> [!NOTE]
> For production deployments, we strongly recommend using your own managed vector databases. This ensures alignment with your organization's security controls, backup and disaster recovery policies, and access management requirements. Integrating with existing infrastructure allows you to leverage established monitoring, auditing, and compliance processes, reducing operational risk and improving data governance.

# Redis Cluster

If enabled, this chart deploys a 3-node Redis Cluster with RediSearch and RedisJSON modules using official Redis images.

## Architecture

The Redis Cluster consists of:
- **3 Redis nodes** in a StatefulSet (master-only configuration)
- **16384 hash slots** distributed across nodes
- **DNS-based topology** for stable cluster formation
- **RediSearch and RedisJSON modules** (included in Redis 8.x)
- **Prometheus metrics exporter** for monitoring

## Prerequisites

Redis password is automatically generated during deployment. The password is stored in the `vector-database-config` secret.

## Configuration

Redis Cluster is deployed via Ansible playbook. The configuration is managed through inventory variables in [`inventory/sample/config.yaml`](../../inventory/sample/config.yaml):

```yaml
vector_databases:
  vector_store: redis-cluster
```

### Helm Chart Configuration

Redis Cluster configuration is managed through [`values.yaml`](values.yaml). You can customize:
- Number of Redis nodes (replica count)
- Resource requests and limits (CPU, memory)
- Redis configuration parameters (maxmemory, eviction policy, timeouts)
- Persistence settings (PVC size, storage class)
- Metrics exporter settings

Refer to [`values.yaml`](values.yaml) for all available configuration options and their default values.

### Features

- **Automated cluster initialization** via init job
- **DNS-based node discovery** (no IP-based topology issues)
- **Persistent storage** with PVCs (default 8Gi per node)
- **Security contexts** (non-root, capability dropping, seccomp)
- **ServiceAccount integration** for Istio AuthorizationPolicy
- **Prometheus monitoring** with redis_exporter sidecar

### Monitoring

Metrics are exposed on port `9121` and scraped by Prometheus. View metrics in Grafana dashboard: **VectorDB/Redis**

Available metrics:
- Cluster health (`redis_cluster_state`)
- Memory usage (`redis_memory_used_bytes`)
- Connected clients (`redis_connected_clients`)
- Command throughput (`redis_commands_processed_total`)
- RediSearch indexes and operations

### Documentation

- **Redis**: https://github.com/redis/redis
- **Redis Cluster Tutorial**: https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/
- **RediSearch**: https://redis.io/docs/latest/develop/interact/search-and-query/
- **RedisJSON**: https://redis.io/docs/latest/develop/data-types/json/
- **Redis Exporter**: https://github.com/oliver006/redis_exporter
- **Redis Docker Image**: https://hub.docker.com/_/redis

### Verification

Check cluster health:
```bash
# Get password
REDIS_PASSWORD=$(kubectl get secret vector-database-config -n vdb -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d)

# Check cluster info
kubectl exec -n vdb vdb-redis-cluster-0 -- redis-cli -a $REDIS_PASSWORD CLUSTER INFO

# Expected output:
# cluster_state:ok
# cluster_slots_assigned:16384
# cluster_known_nodes:3

# Verify nodes use DNS hostnames
kubectl exec -n vdb vdb-redis-cluster-0 -- redis-cli -a $REDIS_PASSWORD CLUSTER NODES

# Test RediSearch and RedisJSON modules (available in Redis 8.x)
kubectl exec -n vdb vdb-redis-cluster-0 -- redis-cli -a $REDIS_PASSWORD MODULE LIST

# Test RedisJSON functionality
kubectl exec -n vdb vdb-redis-cluster-0 -- redis-cli -a $REDIS_PASSWORD JSON.SET test . '{"hello":"world"}'
kubectl exec -n vdb vdb-redis-cluster-0 -- redis-cli -a $REDIS_PASSWORD JSON.GET test
```

# Qdrant

> [!IMPORTANT]
> Qdrant support is EXPERIMENTAL for this release and is not supported for production use.
>
> Backup and restore are not covered by this release. Re-ingesting the source
> documents through the data preparation pipeline is the only recovery path.

## Architecture

A single Qdrant node in a StatefulSet with two persistent volumes, one for storage and one for snapshots. Clustering is disabled. The HTTP API and the Prometheus metrics endpoint share port `6333`, gRPC uses port `6334`.

Qdrant is templated in this chart under [`templates/qdrant/`](templates/qdrant), the same way Redis, pgvector and MSSQL are, and the server is pinned to `v1.19.0`, which is the version the disk quota settings under `config.storage.quotas` require.

## Prerequisites

A block or node-local StorageClass backed by SSD has to exist on the cluster before Qdrant is deployed, and `vector_databases.qdrant.persistence.storageClass` has to name it. Qdrant does not support network storage such as NFS, and the provisioner is an operator-provided prerequisite that this repository does not install.

Two API keys are automatically generated during deployment and stored in the `vector-database-config` secret. See [API keys](#api-keys).

## Configuration

Qdrant is deployed via Ansible playbook. The configuration is managed through inventory variables in [`inventory/sample/config.yaml`](../../inventory/sample/config.yaml):

```yaml
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: qdrant
  qdrant:
    persistence:
      storageClass: "local-path"
      size: "20Gi"
    snapshotPersistence:
      enabled: true
      storageClass: "local-path"   # falls back to persistence.storageClass when empty
      size: "20Gi"
```

### Volume sizing

The reference scale documented for this release is 1M vectors at 768 dimensions, which needs roughly 5Gi of steady state data. It is a reference point for sizing, not a tested ceiling and not an enforced limit.

Both volumes default to 20Gi, which leaves headroom for optimizer temporary segments, the write-ahead log and a snapshot restore, which needs twice the disk currently used by the collection.

### API keys

Two API keys are generated during deployment and stored in the `vector-database-config` Secret:

| Secret key | Privilege | Consumer |
|------------|-----------|----------|
| `QDRANT_API_KEY` | Read-write | Writers, that is the data preparation pipeline ingestion service |
| `QDRANT_READ_ONLY_API_KEY` | Read-only | The retriever, and the Prometheus `ServiceMonitor` scrape |

The connector reads only `QDRANT_API_KEY`. The retriever Deployment therefore adds an explicit `env` entry that sources `QDRANT_API_KEY` from the `QDRANT_READ_ONLY_API_KEY` Secret key, which takes precedence over the `envFrom` value, so a compromised retriever cannot write to or drop the collection.

The Qdrant server itself receives both keys as the `QDRANT__SERVICE__API_KEY` and `QDRANT__SERVICE__READ_ONLY_API_KEY` environment variables, sourced from the same Secret with `valueFrom.secretKeyRef`. This chart ships no API key Secret of its own. The upstream chart offers `apiKey` and `readOnlyApiKey` values that resolve a Secret with a Helm `lookup`, which returns nothing during `helm template`, `--dry-run` and the pre-upgrade render, so the chart emits a Secret with an empty `data` block and starts Qdrant with no authentication at all. With `valueFrom` there is no `lookup` and no second copy of the keys, and a missing Secret or key holds the pod in `CreateContainerConfigError` instead of starting an unauthenticated Qdrant.

### Upgrade constraints

[`deployment/upgrade/rules/vdb.yaml`](../../upgrade/rules/vdb.yaml) evaluates changes on first match. For Qdrant:

| Change | Result | Reason |
|--------|--------|--------|
| `resources.requests`, `resources.limits` | Approved | Performance and cost tuning |
| `persistence.size`, `snapshotPersistence.size` | Rejected | A StatefulSet update cannot resize existing PVCs |
| `persistence.storageClassName`, `snapshotPersistence.storageClassName` | Rejected | Same, the class of a bound PVC is immutable |
| `image.tag` | Rejected | A server version change needs an explicit migration decision, and a downgrade cannot read a newer storage format |
| `config.storage.on_disk_payload` | Rejected | Rewrites the storage layout of every existing collection |
| `config.cluster` | Rejected | Clustering needs a resharding plan, not a StatefulSet update |
| Any other Qdrant value | Approved | - |

A rejected change means the upgrade stops. Applying one requires a deliberate reinstall and re-ingestion, not an upgrade.

The pre-upgrade data consistency check sums `points_count` across every collection rather than looking up one name, because the collection name is derived from the embedding model and the vector settings. A transport or authentication failure fails the check instead of reporting zero, so a populated database can never look empty to a destructive upgrade.

### Monitoring

Metrics are exposed on the API port `6333` at `/metrics` and scraped by Prometheus using the read-only API key.

### Documentation

- **Qdrant**: https://github.com/qdrant/qdrant
- **Qdrant Helm chart**: https://github.com/qdrant/qdrant-helm (upstream reference the templates under `templates/qdrant/` were derived from, at chart version 1.18.2)
- **Storage and memory**: https://qdrant.tech/documentation/concepts/storage/
- **Qdrant Docker image**: https://hub.docker.com/r/qdrant/qdrant

### Verification

Check that the collection is reachable:
```bash
# Get read-only API key
QDRANT_KEY=$(kubectl get secret vector-database-config -n vdb -o jsonpath='{.data.QDRANT_READ_ONLY_API_KEY}' | base64 -d)

# Port-forward and query the collection list
kubectl port-forward -n vdb svc/vdb-qdrant 6333:6333 &
curl -s -H "api-key: $QDRANT_KEY" http://localhost:6333/collections
```

# Microsoft SQL Server 2025

Enterprise RAG includes optional support for Microsoft SQL Server Express Edition as a vector store backend, which is subject to feature and capacity limits (e.g., 10 GB database size). In the course of using Enterprise RAG users deploy SQL Server via Microsoft’s official container images and are responsible for acknowledging and accepting applicable Microsoft licensing terms, available at https://www.microsoft.com/en-us/useterms.

## Architecture

A single instance Microsoft SQL Server Express Edition using official Microsoft container images available at https://mcr.microsoft.com/en-us/artifact/mar/mssql/server/.

This instance includes awaragi/prometheus-mssql-exporter for exporting prometheus metrics.

## Prerequisites

SA password is automatically generated during deployment. The password is stored in the `vector-database-config` secret.

## Configuration

Microsoft SQL Server is deployed via Ansible playbook. The configuration is managed through inventory variables in [`inventory/sample/config.yaml`](../../inventory/sample/config.yaml):

```yaml
vector_databases:
  vector_store: mssql
```

### Helm Chart Configuration

Microsoft SQL Server configuration is managed through [`values.yaml`](values.yaml). You can customize:
- Resource requests and limits (CPU, memory)
- Persistence settings (PVC size, storage class)
- Metrics exporter (optional, enabled by default)

Refer to [`values.yaml`](values.yaml) for all available configuration options and their default values.

### Deployment

If you choose to deploy `mssql` vector store option, ansible deployment will pause and wait for user input for accepting the Microsoft SQL Server terms and conditions.

```bash
[vector_databases : Ask the operator to accept the EULA]
Do you accept the Microsoft SQL Server 2025 Express Edition EULA? [Y/N]
Type Y to accept, N to decline. Press ENTER to confirm.
```

Press `y` and then `ENTER` to accept the term and proceed with the installation process. Setup will *not* continue unless those terms are accepted.

### Features

- **Automated database initialization** via built-in init scripts
- **Persistent storage** with PVCs (default 10Gi)
- **Security contexts** (non-root, restricted capabilities, seccomp)
- **ServiceAccount integration** for Istio AuthorizationPolicy
- **Prometheus monitoring** with prometheus-mssql-exporter sidecar

### Monitoring

Metrics are exposed on port `4000` and scraped by Prometheus. View metrics in Grafana dashboard: **VectorDB/Microsoft SQL Server**
