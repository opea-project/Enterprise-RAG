# Helm Charts for UI

This directory contains Helm charts for deploying the UI components of the application.

## Adding a New UI Image

To add a new UI image to the existing Helm charts, follow these steps:

1. **Create a ConfigMap Template**: Create a new NGINX ConfigMap template similar to `chatqna-nginx-config-cm.yaml` in the `templates` directory. This template will be used for the new UI image based on the `values.yaml` field `type`.

2. **Update `values.yaml`**: Add the necessary configuration for the new UI image in the `values.yaml` file. This should include the endpoints, and any other required settings.

3. **Deploy the Helm Chart**: Use the Helm CLI to deploy the updated chart with the new UI image configuration.

For reference, check the existing `chatqna-nginx-config-cm.yaml` and `values.yaml` files.

## Example

Here is an example configuration for a new UI image:

```yaml
# values.yaml
extraNginxVars:
  newuiEndpoint: "http://newui-service"
  statusEndpoint: "http://new-status-service"
```
