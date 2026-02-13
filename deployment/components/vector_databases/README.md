# Vector Databases

This helm chart allows creation of selected vector databases. Those are optional if you wish to use external vector databases with Enterprise RAG. If you do not have any external and supported by `VectorStore` databases, feel free to enable one of the currently available ones. 

Currently supported databases:
- [Redis-cluster 8.2.2](#redis-cluster)
- [Microsoft SQL Server 2025](#microsoft-sql-server-2025)

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
