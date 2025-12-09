# Component Update Script

Python script to update `appVersion` and optionally `version` fields in Chart.yaml files for all ERAG application components.

## Usage

```bash
# Update appVersion only (keep chart versions unchanged)
python deployment/scripts/update_components.py \
  --app-version 2.2.0 \
  --no-increment-chart-version

# Update appVersion and increment chart versions (default behavior)
python deployment/scripts/update_components.py \
  --app-version 2.2.0

# Dry run to preview changes
python deployment/scripts/update_components.py \
  --app-version 2.2.0 \
  --dry-run
```

## Options

- `--app-version` (required): New appVersion to set for all components
- `--increment-chart-version`: Increment chart version patch number (default: true)
- `--no-increment-chart-version`: Keep chart versions unchanged
- `--dry-run`: Preview changes without modifying files
- `--root-dir`: Override repository root directory (auto-detected by default)

## Components Updated

The script updates all application component charts:
- apisix-routes
- apisix
- chat_history
- edp
- fingerprint
- gmc (pipeline controller)
- ingress (umbrella chart)
- keycloak
- postgresql
- telemetry
- ui
- rag-utils
- vector_databases

## Chart Version Increment

When `--increment-chart-version` is used, the patch version is incremented:
- 1.0.0 → 1.0.1
- 2.5.3 → 2.5.4

## Requirements

- Python 3.6+
- PyYAML package

Install requirements:
```bash
pip install pyyaml
```
