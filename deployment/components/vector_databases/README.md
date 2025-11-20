# Vector Databases

Currently supported databases:
- redis-cluster 8.2.2

This chart deploys a 3-node Redis Cluster with RediSearch and RedisJSON modules using official Redis images.

# Architecture

The Redis Cluster consists of:
- **3 Redis nodes** in a StatefulSet (master-only configuration)
- **16384 hash slots** distributed across nodes
- **DNS-based topology** for stable cluster formation
- **RediSearch and RedisJSON modules** (included in Redis 8.x)
- **Prometheus metrics exporter** for monitoring

# Prerequisites

Redis password is automatically generated during deployment. The password is stored in the `vector-database-config` secret.

# Configuration

Redis Cluster is deployed via Ansible playbook. The configuration is managed through inventory variables in [`inventory/sample/config.yaml`](../../inventory/sample/config.yaml):

```yaml
vector_databases:
  vector_store: redis-cluster
```

## Redis Cluster

This chart deploys a high-performance Redis Cluster suitable for vector databases with >1M vectors.

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
