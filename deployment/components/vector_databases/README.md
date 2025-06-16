# Vector Databases

Currently supported databases:
- redis >=8.0.2
- redis-cluster >=8.0.2

As of now, redis and redis-cluster charts use a custom, newer than included in the chart by default, version of bitnami's redis and redis-cluster container.

# Prerequisites

You should prepare a kubernetes secret containing password beforehand. Examples, depending on which database you selected, are located in `templates` folder.

To select any of the supported databases, set it's value in `values.yaml` file. For example:
```
redis-cluster:
  enabled: true
```

This can be also set directly by using helm:
```
helm install --set redis-cluster.enabled=true .
```

## Redis

Use redis when you want to deploy a small vector database. This is also good for demo and evaluation. This is the default configuration.

### Documentation

https://github.com/bitnami/containers/blob/main/bitnami/redis
https://github.com/bitnami/charts/tree/main/bitnami/redis

## Redis Cluster

Use redis-cluster when you want maximum performance from your vector database. Databases >1M vectors should use this.

### Documentation

https://github.com/bitnami/containers/blob/main/bitnami/redis-cluster
https://github.com/bitnami/charts/tree/main/bitnami/redis-cluster
