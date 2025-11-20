# Contributing to Vector Stores

Adding a new vector store support is separated into two phases:
1. [Adding a new vector database connector](#1-adding-a-new-vector-database)
    - 1.1. [Create a New Connector](#11-create-a-new-connector)
    - 1.2. [Update Connector Mapping](#12-update-connector-mapping)
    - 1.3. [Requirements](#13-requirements)
    - 1.4. [Testing](#14-testing)
2. [Implementing database configuration and deployment](#2-implementing-database-configuration-and-deployment)
    - 2.1 [Kubernetes deployment requirements](#21-kubernetes-deployment-requirements)
    - 2.2 [(Optional) Implement telemetry](#22-optional-implement-telemetry)
    - 2.3 [(Optional) Implement backup](#23-optional-implement-backup)
    - 2.4 [Test deployment](#24-test-deployment)

## 1. Adding a New Vector Database

To add support for a new vector database, you need to implement two main components.

### 1.1 Create a New Connector

Create a new connector file in the `utils/connectors` folder:

```
utils/
├── connectors/
    ├── connector_your_db.py
```

Your connector should:
- Implement the required interface methods based on [VectorStoreConnector](../../comps/vectorstores/utils/connectors/connector.py) abstract class
- Handle connection management using a client using the database's python bindings
- Configure the database endpoint using ENV variables
- Provide methods for adding and removing data
- Configure the vector algorithm using ENV variables
- Provide methods for creating vector database/indexes
- Provide methods for searching vector store based on passed embeddings

### 1.2. Update Connector Mapping

Add your connector to the connector mapping in the `utils/opea_vectorstore.py` file:

```python
# register the additional vector store and implement the loading class
self._SUPPORTED_VECTOR_STORES = {
    "redis": self._import_redis,
    "redis-cluster": self._import_redis,
    "your-db": self._import_your_db,
}

def _import_your_db(self):
    """
    Imports the ConnectorYourDB connector.
    """
    try:
        from comps.vectorstores.utils.connectors.connector_your_db import ConnectorYourDB
        self.vector_store = ConnectorYourDB()
    except ModuleNotFoundError:
        logger.exception("exception when loading ConnectorYourDB")
```

This mapping name is used when loading the proper connector at runtime based on `VECTOR_STORE` ENV variable.

For example, if you set `VECTOR_STORE=your-db` in your microservice environment, it will load and use your connector implementation for all vector store operations.

### 1.3. Requirements

- Follow existing code patterns and style
- Include comprehensive error handling
- Add appropriate type hints
- Test your implementation thoroughly

### 1.4. Testing

- Create unit tests for your connector in [src/tests/unit/vectorstores](../../tests/unit/vectorstores/)
- Test connection scenarios
- Verify vector operations work correctly (add_text, similarity_search etc.)
- Test error conditions

## 2. Implementing database configuration and deployment

The database server needs to be deployed within EnterpriseRAG, which requires implementing an additional Helm deployment configuration option; refer to the [deployment/components/vector_databases](../../../deployment/components/vector_databases/) folder for guidance.

## 2.1 Kubernetes deployment requirements

Currently, two microservices are using the vectorstores code: 
- [ingestion](../../../deployment/components/edp/templates/ingestion/) (in `edp` namespace)
- [retriever](../../../deployment/components/gmc/manifests_common/retriever-usvc.yaml.tpl) (in `chatqna` namespace)

You would have to:
- include an external helm chart that deploys the database OR define the deployment+secret yourself
- generate a block in [values.yaml](../../../deployment/components/vector_databases/values.yaml) that configures your database
- gate your database configuration/deployment with an appropriate `enabled` flag.
    - if using helm chart:
        - ensure that the database is only deployed only when explicitly enabled via `condition` in [Chart.yaml](../../../deployment/components/vector_databases/Chart.yaml)
    - if using custom deployment
        - define the deployment in a separate folder under `deployment/components/vector_databases/templates/<your-db>`
        - it is recommended to define and mount a PersistentVolumeClaim for data storage
- ensure that the initialization data (for example - root password) is referenced from a secret
- update the [vector_databases/README.md](../../../deployment/components/vector_databases/README.md) file with the newly added database in the support table
- implement the `vector_database` ansible task [here](../../../deployment/roles/application/vector_databases/):
    - create an additional block, similar to `name: Configure Redis-like vector store`, so that:
        - password(s) are generated and stored
        - configuration values are generated and stored
        - keep in mind to use correct `when` conditions that match your vector_store name for that block
    - create an additional task, similar to `name: Create redis compatible vector store configs for services in namespaces`, so that:
        - it creates a secret (`vector-database-config`) that will be shared with services that implement the vector_store in python. This secret values should configure the `ConnectorYourDB` to connect to the DB
        - keep in mind to use correct `when` conditions that match your vector_store name for that block
- implement proper init containers in elements that use the vector_store
    - for GMC deployed microservices:
        - add init container definition [here](../../../deployment/components/gmc/templates/init_containers/)
        - add conditional logic for that container [here](../../../deployment/components/gmc/manifests_common/retriever-usvc.yaml.tpl)
    - for other microservices (for example - EDP):
        - add init container definition [here](../../../deployment/components/edp/templates/init_containers/)
        - add conditional logic for that container [here](../../../deployment/components/edp/templates/ingestion/ingestion-configmap.yaml)
- remember to include pod/deployment security contexts so that containers run as non-root users, they drop not needed capabilities and apply proper seccomp profiles
- add comment about additional vector_store support in [deployment/inventory/sample/config.yaml](../../../deployment/inventory/sample/config.yaml)
- implement proper [ansible values.yaml override file](../../../deployment/roles/application/vector_databases/templates/values.yaml.j2) that generates a compatible `values.yaml` file  to the second bullet point via ansible 
- verify that the `vector_database` component is deployable by configuring and deploying the solution via [config.yaml](../../../deployment/inventory/sample/config.yaml)
- for istio enabled environments, please add an additional [`AuthorizationPolicy`](../../../deployment/components/istio/authz/authz-vdb.yaml) similar to other vector databases.

## 2.2 (Optional) Implement telemetry
Some vector databases provide built-in Prometheus metrics endpoints for monitoring database performance, resource usage, and query statistics. When implementing your vector database, check if it supports native Prometheus metrics export.

If your database supports Prometheus monitoring:
- Configure the database to expose metrics on a dedicated port (typically `/metrics` endpoint)
- Ensure the metrics endpoint is accessible by the cluster's monitoring stack
- Add appropriate service monitor configurations in your Helm templates to enable automatic metrics discovery
- Document any database-specific metrics that may be useful for monitoring vector store performance

This native monitoring can complement EnterpriseRAG's [telemetry](../../../deployment/components/telemetry/) system to provide comprehensive observability of your vector database operations.

##  2.3 (Optional) Implement backup
Some vector databases provide built-in backup capabilities or support external backup tools. When implementing new database suppport, consider implementing backup support to ensure data persistence and disaster recovery.

If your database supports backup operations:
- Configure backup schedules and retention policies appropriate for your use case
- Ensure backup storage is accessible and properly secured
- Add backup configurations in your Helm templates with appropriate volume mounts and permissions
- Consider implementing both full and incremental backup strategies where supported

This project uses [Velero](../../../deployment/components/velero/) for Kubernetes-native backup and restore operations. When possible, integrate your vector database backup strategy with Velero:
- Configure Velero annotations on persistent volumes used by your database
- Implement pre-backup hooks if your database requires consistent snapshots
- Test restore procedures to ensure backup integrity
- Document backup and restore procedures specific to your vector database implementation

## 2.4 Test deployment
After implementing your vector database configuration and deployment, thoroughly test the integration to ensure it works correctly across all supported scenarios.

### Testing Requirements

1. **Basic Database Operations**
    - Verify database deployment and initialization
    - Test connection establishment from microservices
    - Confirm proper authentication and authorization

2. **Vector Store Operations**
    - Test document ingestion with various content types and sizes
    - Verify vector embeddings are correctly stored and indexed
    - Test similarity search with different query parameters
    - Validate metadata filtering and retrieval accuracy

3. **Configuration Compatibility**
    This project supports numerous configuration options that may expose missing implementations in your connector. Pay special attention to:
    - Different embedding models and dimensions
    - Different deployment topologies (single node, cluster, etc.)
    - Performance tuning parameters
    - Security configurations (TLS, access controls)

4. **Integration Testing**
    - Test the complete ingestion pipeline from document upload to vector storage
    - Verify end-to-end query functionality from user input to retrieved results
    - Test error handling and recovery scenarios
    - Validate performance under expected load conditions

5. **Test Coverage**
    Run the comprehensive end-to-end tests that cover critical functionalities:
    - [E2E Test Suite](../../../src/tests/e2e/)
    - [Unit Tests](../../../src/tests/unit/)
    
    These tests simulate real-world usage patterns and will help identify any gaps in your connector implementation.

Document any configuration limitations or known issues discovered during testing.
