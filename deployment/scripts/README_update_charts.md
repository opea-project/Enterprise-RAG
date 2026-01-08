# update_charts.py

Updates `appVersion` and `version` fields in Helm Chart.yaml files for ERAG components.

## Introduction

This tool addresses two critical requirements:
- **Solution versioning** - automates updating all component charts with the solution version, enabling version-controlled upgrades and simplified deployment maintenance.
- **Dependency synchronization** - regenerates `Chart.lock` files when dependency helm charts are updated.

## Requirements

- Python 3.x
- `helm` CLI (for dependency updates)
- `grep` command

## Use Cases

### 1. Update All Charts for New RAG Version (Recommended)

Increment chart versions when releasing a new ERAG version:

```bash
./update_charts.py --app-version 2.1.0
```

**Default behavior:**
- Sets `appVersion: 2.1.0` in all component Chart.yaml files
- Increments `version` field (e.g., `1.0.5` → `1.0.6`)
- Runs `helm dependency update` for charts with dependencies

### 2. Update Single Chart (Keep Current RAG Version)

Update specific chart without incrementing version (e.g., after dependency upgrade):

```bash
# By chart name
./update_charts.py --app-version 2.0.5 --charts telemetry --no-increment-chart-version

# By directory name
./update_charts.py --app-version 2.0.5 --dirs telemetry --no-increment-chart-version

# Multiple charts
./update_charts.py --app-version 2.0.5 --charts "telemetry,ui,edp" --no-increment-chart-version
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--app-version` | Required | New appVersion for components |
| `--increment-chart-version`, `--inc` | `true` | Increment chart version (patch +1) |
| `--no-increment-chart-version`, `--no-inc` | - | Skip chart version increment |
| `--dep-update` | `true` | Run helm dependency update |
| `--no-dep-update` | - | Skip dependency updates |
| `--dry-run` | `false` | Preview changes without applying |
| `--chart-dir` | `deployment/components` | Base directory for charts |
| `--dirs` | All | Comma-separated list of chart directories |
| `--charts` | All | Comma-separated list of chart names |

## Examples

**Dry run before release:**
```bash
./update_charts.py --app-version 2.2.0 --dry-run
```

**Update without helm dependency refresh:**
```bash
./update_charts.py --app-version 2.1.0 --no-dep-update
```

**Update only telemetry and monitoring charts:**
```bash
./update_charts.py --app-version 2.0.5 --charts "telemetry,monitoring"
```

**Fix appVersion without changing chart version:**
```bash
./update_charts.py --app-version 2.0.5 --no-increment-chart-version
```

## Chart Selection

Script identifies ERAG charts by annotation:
```yaml
annotations:
  app.kubernetes.io/part-of: ERAG
```

## Version Increment Logic

Chart version follows semantic versioning (MAJOR.MINOR.PATCH):
- Only PATCH is incremented: `1.0.5` → `1.0.6`
- MAJOR/MINOR versions require manual editing

## Error Handling

- Exits with code 1 on errors
- Validates chart directory existence
- Checks helm dependency update success
- Reports all errors in summary
