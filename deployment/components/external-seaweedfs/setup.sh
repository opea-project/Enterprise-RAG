#!/usr/bin/env bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# setup.sh - External SeaweedFS for Velero BSL (off-cluster S3 storage).
# NOTE: Deploys SeaweedFS for evaluation purposes only, not production-ready
#       backup storage. Any S3-compatible service supported by velero-plugin-for-aws
#       can be used instead; this script is not required (see README.md).
# Commands:    --install, --uninstall, --patch-coredns, --unpatch-coredns
# Requirements: docker, docker-compose-plugin, openssl, nc
# Optional:     kubectl (for --patch-coredns / --unpatch-coredns)
# Run without arguments for usage.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Defaults
HOST="${HOST:-$(hostname -I | awk '{print $1}')}"
S3_PORT="${S3_PORT:-8333}"
BUCKET="${BUCKET:-velero}"
SEAWEEDFS_HOSTNAME=""
LOCAL_VOLUMES=false
BASE_PATH="."
DO_INSTALL=false
DO_UNINSTALL=false
PATCH_COREDNS=false
UNPATCH_COREDNS=false
CLEAN_VOLUMES=false

GENERATED_FILES=(s3config.json cloud-credentials docker-compose.override.yml)
GENERATED_DIRS=(certs)

# Usage
usage() {
  cat <<'EOF'
Usage: ./setup.sh <command> [options]

Commands:
  --install              Deploy SeaweedFS containers and generate credentials
  --uninstall            Stop containers and remove generated files
  --patch-coredns        Add hostname->IP entry in CoreDNS (needs --hostname)
  --unpatch-coredns      Remove hosts block from CoreDNS

Options (--install):
  --hostname <name>      Enable TLS (nginx terminator + self-signed cert)
  --host <ip>            Server IP (default: auto-detected)
  --bucket <name>        S3 bucket (default: velero)
  --port <port>          S3 port (default: 8333)
  --local-volumes        Bind-mount data dirs instead of Docker volumes
  --base-path <dir>      Root for local volume dirs (default: .)
  --patch-coredns        Also patch CoreDNS after install

Options (--uninstall):
  --clean-volumes        Also remove Docker volumes and local data dirs

Examples:
  ./setup.sh --install                                     # plain HTTP
  ./setup.sh --install --hostname s3.internal              # TLS + hostname
  ./setup.sh --install --hostname s3.internal --patch-coredns
  ./setup.sh --uninstall --clean-volumes
  ./setup.sh --patch-coredns --hostname s3.internal --host 10.0.0.1
  ./setup.sh --unpatch-coredns

Requirements: docker, docker-compose-plugin, openssl, nc
Optional:     kubectl (for --patch-coredns / --unpatch-coredns)
              aws CLI or compatible (for direct bucket access)
EOF
  exit "${1:-0}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install)         DO_INSTALL=true;      shift ;;
    --uninstall)       DO_UNINSTALL=true;    shift ;;
    --patch-coredns)   PATCH_COREDNS=true;   shift ;;
    --unpatch-coredns) UNPATCH_COREDNS=true; shift ;;
    --host)            HOST="$2";            shift 2 ;;
    --hostname)        SEAWEEDFS_HOSTNAME="$2"; shift 2 ;;
    --bucket)          BUCKET="$2";          shift 2 ;;
    --port)            S3_PORT="$2";         shift 2 ;;
    --local-volumes)   LOCAL_VOLUMES=true;   shift ;;
    --base-path)       BASE_PATH="$2";       shift 2 ;;
    --clean-volumes)   CLEAN_VOLUMES=true;   shift ;;
    -h|--help)         usage 0 ;;
    *)                 echo "Unknown option: $1"; usage 1 ;;
  esac
done

if ! $DO_INSTALL && ! $DO_UNINSTALL && ! $PATCH_COREDNS && ! $UNPATCH_COREDNS; then
  usage 0
fi

# Derived values
USE_TLS=false
[[ -n "${SEAWEEDFS_HOSTNAME}" ]] && USE_TLS=true

if [[ "${USE_TLS}" == "true" ]]; then
  S3_URL="https://${SEAWEEDFS_HOSTNAME}:${S3_PORT}"
else
  S3_URL="http://${HOST}:${S3_PORT}"
fi

# Proxy bypass for local commands
_NP="${HOST}"
[[ -n "${SEAWEEDFS_HOSTNAME}" ]] && _NP="${_NP},${SEAWEEDFS_HOSTNAME}"
export NO_PROXY="${NO_PROXY:+${NO_PROXY},}${_NP}"
export no_proxy="${no_proxy:+${no_proxy},}${_NP}"

# Helper: write local-volume service entry for docker-compose override
_write_local_vol() {
  echo "  $1:"
  echo "    volumes:"
  echo "      - ${BASE_PATH}/$2:/data"
}

do_uninstall() {
  echo "==> Stopping containers ..."
  if $CLEAN_VOLUMES; then
    docker compose down -v --remove-orphans 2>/dev/null || true
  else
    docker compose down 2>/dev/null || true
  fi

  echo "==> Removing generated files ..."
  rm -f "${GENERATED_FILES[@]}"
  rm -rf "${GENERATED_DIRS[@]}"

  if $CLEAN_VOLUMES; then
    for d in master-data volume-data filer-data; do
      [[ -d "${BASE_PATH}/${d}" ]] && rm -rf "${BASE_PATH}/${d}" && echo "    Removed ${BASE_PATH}/${d}"
    done
  fi
  echo "    Done."
}

do_install() {
  echo "==> Generating S3 credentials ..."
  local access_key secret_access_key
  access_key="$(openssl rand -hex 16)"
  secret_access_key="$(openssl rand -hex 32)"

  cat > s3config.json <<EOF
{
  "identities": [{
    "name": "velero",
    "credentials": [{"accessKey": "${access_key}", "secretKey": "${secret_access_key}"}],
    "actions": ["Read", "Write", "List", "Tagging", "Admin"]
  }]
}
EOF

  # Credentials file in AWS INI format (consumed by Ansible credentials_file_path)
  printf '[default]\naws_access_key_id = %s\naws_secret_access_key = %s\n' "${access_key}" "${secret_access_key}" > cloud-credentials
  chmod 600 cloud-credentials
  echo "    cloud-credentials written."

  if [[ "${USE_TLS}" == "true" ]]; then
    _gen_tls_override
  elif $LOCAL_VOLUMES; then
    _gen_localvol_override
  else
    _gen_plain_override
  fi

  echo "==> Starting SeaweedFS ..."
  docker compose up -d

  echo "==> Waiting for S3 endpoint ..."
  local waited=0
  until nc -z 127.0.0.1 "${S3_PORT}" 2>/dev/null && nc -z 127.0.0.1 8888 2>/dev/null; do
    if [[ ${waited} -ge 150 ]]; then
      echo "ERROR: ports not ready within 150s"
      docker compose logs --tail=30
      exit 1
    fi
    sleep 2; waited=$((waited + 2))
  done
  sleep 3
  echo "    Ready after ${waited}s."

  echo "==> Creating bucket '${BUCKET}' ..."
  local filer="http://127.0.0.1:8888"
  if curl -sf --max-time 5 "${filer}/buckets/${BUCKET}/" 2>/dev/null | grep -q '"name"'; then
    echo "    Bucket already exists."
  else
    curl -sf --max-time 5 -X POST "${filer}/buckets/${BUCKET}/" >/dev/null 2>&1 \
      && echo "    Bucket created." \
      || echo "WARNING: bucket creation may have failed; verify: curl -X POST ${filer}/buckets/${BUCKET}/"
  fi

  echo ""
  echo "======================================================================"
  if [[ "${USE_TLS}" == "true" ]]; then
    echo " SeaweedFS ready  [TLS mode]"
    echo " Endpoint   : ${S3_URL}"
    echo " Hostname   : ${SEAWEEDFS_HOSTNAME}"
    echo " Server IP  : ${HOST}"
  else
    echo " SeaweedFS ready  [plain HTTP]"
    echo " Endpoint   : ${S3_URL}"
  fi
  echo " Bucket     : ${BUCKET}"
  echo " Credentials: cloud-credentials"
  echo "======================================================================"

  echo ""
  echo "-- Paste into config.yaml (under velero:) --"
  if [[ "${USE_TLS}" == "true" ]]; then
cat <<SNIPPET
    external_bsl:
      enabled: true
      s3_url: "${S3_URL}"
      bucket: "${BUCKET}"
      credentials_file_path: "{{ playbook_dir }}/../components/external-seaweedfs/cloud-credentials"
      region: "us-east-1"
      s3_force_path_style: "true"
      tls:
        enabled: true
        hostname: "${SEAWEEDFS_HOSTNAME}"
        host_ip: "${HOST}"
        ca_cert_path: "{{ playbook_dir }}/../components/external-seaweedfs/certs/tls.crt"
SNIPPET
  else
cat <<SNIPPET
    external_bsl:
      enabled: true
      s3_url: "${S3_URL}"
      bucket: "${BUCKET}"
      credentials_file_path: "{{ playbook_dir }}/../components/external-seaweedfs/cloud-credentials"
      region: "us-east-1"
      s3_force_path_style: "true"
      tls:
        enabled: false
SNIPPET
  fi
  echo ""
  echo "-- Apply: ansible-playbook playbooks/infrastructure.yaml -t post-install"
  echo ""

  if [[ "${USE_TLS}" == "true" ]]; then
    echo "-- TLS certificate --"
    openssl x509 -in certs/tls.crt -noout -subject -dates -ext subjectAltName 2>&1 | sed 's/^/  /'
    echo ""
  fi
}

# Generate TLS override: nginx terminates TLS -> filer HTTP :8444
_gen_tls_override() {
  # nginx terminates TLS cleanly (SeaweedFS native TLS has a TLS 1.3 HRR hang).
  echo "==> Generating TLS cert for '${SEAWEEDFS_HOSTNAME}' ..."
  mkdir -p certs
  openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
    -keyout certs/tls.key -out certs/tls.crt \
    -subj "/CN=${SEAWEEDFS_HOSTNAME}" \
    -addext "subjectAltName=DNS:${SEAWEEDFS_HOSTNAME},IP:${HOST}" 2>&1 \
    | grep -v "^Generating\|^writing\|\.\.\." || true
  chmod 600 certs/tls.key

  cat > certs/nginx.conf <<NGINXCONF
worker_processes 1;
events { worker_connections 1024; }
http {
  client_max_body_size 0;
  server {
    listen ${S3_PORT} ssl;
    ssl_certificate     /tls/tls.crt;
    ssl_certificate_key /tls/tls.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    location / {
      proxy_pass http://filer:8444;
      proxy_set_header Host \$http_host;
      proxy_set_header X-Real-IP \$remote_addr;
      proxy_read_timeout 300s;
      proxy_send_timeout 300s;
    }
  }
}
NGINXCONF

  echo "==> Generating docker-compose.override.yml (TLS) ..."
  cat > docker-compose.override.yml <<'HDR'
# Auto-generated by setup.sh - do not edit manually.
# nginx (TLS :8333) -> filer (HTTP :8444)
HDR

  local np="localhost,127.0.0.1,master,volume,filer,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,${SEAWEEDFS_HOSTNAME}"
  {
    echo "services:"
    $LOCAL_VOLUMES && _write_local_vol master master-data
    $LOCAL_VOLUMES && _write_local_vol volume volume-data
    echo "  filer:"
    echo "    command: >"
    echo "      filer -master=master:9333 -s3 -s3.port=8444 -s3.config=/config/s3config.json"
    if $LOCAL_VOLUMES; then
      echo "    volumes:"
      echo "      - ${BASE_PATH}/filer-data:/data"
      echo "      - ./s3config.json:/config/s3config.json:ro"
    fi
    echo "    environment:"
    echo "      - no_proxy=${np}"
    echo "      - NO_PROXY=${np}"
    echo "    healthcheck:"
    echo "      test: [\"CMD-SHELL\", \"nc -z \$(hostname -i) 8444\"]"
    echo "      interval: 10s"
    echo "      timeout: 5s"
    echo "      retries: 18"
    echo "  nginx:"
    echo "    image: nginx:alpine"
    echo "    container_name: seaweedfs-nginx"
    echo "    ports:"
    echo "      - \"${S3_PORT}:${S3_PORT}\""
    echo "    volumes:"
    echo "      - ./certs/nginx.conf:/etc/nginx/nginx.conf:ro"
    echo "      - ./certs/tls.crt:/tls/tls.crt:ro"
    echo "      - ./certs/tls.key:/tls/tls.key:ro"
    echo "    depends_on:"
    echo "      filer:"
    echo "        condition: service_healthy"
    echo "    networks:"
    echo "      - seaweedfs"
    echo "    restart: unless-stopped"
    echo "    environment:"
    echo "      - no_proxy=${np}"
    echo "      - NO_PROXY=${np}"
    echo "    healthcheck:"
    echo "      test: [\"CMD-SHELL\", \"nc -z localhost ${S3_PORT}\"]"
    echo "      interval: 10s"
    echo "      timeout: 5s"
    echo "      retries: 12"
  } >> docker-compose.override.yml
}

# Generate plain HTTP + local volumes override
_gen_localvol_override() {
  echo "==> Generating docker-compose.override.yml (local volumes) ..."
  cat > docker-compose.override.yml <<'HDR'
# Auto-generated by setup.sh - do not edit manually.
HDR
  {
    echo "services:"
    _write_local_vol master master-data
    _write_local_vol volume volume-data
    echo "  filer:"
    echo "    volumes:"
    echo "      - ${BASE_PATH}/filer-data:/data"
    echo "    ports:"
    echo "      - \"${S3_PORT}:${S3_PORT}\""
  } >> docker-compose.override.yml
}

# Generate plain HTTP override (port exposure only)
_gen_plain_override() {
  echo "==> Generating docker-compose.override.yml (plain HTTP) ..."
  cat > docker-compose.override.yml <<'HDR'
# Auto-generated by setup.sh - do not edit manually.
HDR
  {
    echo "services:"
    echo "  filer:"
    echo "    ports:"
    echo "      - \"${S3_PORT}:${S3_PORT}\""
  } >> docker-compose.override.yml
}

do_patch_coredns() {
  [[ -z "${SEAWEEDFS_HOSTNAME}" ]] && { echo "ERROR: --hostname required for --patch-coredns"; exit 1; }
  command -v kubectl &>/dev/null || { echo "ERROR: kubectl not found"; exit 1; }

  echo "==> Patching CoreDNS: ${SEAWEEDFS_HOSTNAME} -> ${HOST}"
  local current patched patch_json
  current=$(kubectl get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}')

  patched=$(COREFILE="${current}" HOST_IP="${HOST}" HOSTNAME_VAL="${SEAWEEDFS_HOSTNAME}" python3 << 'PYEOF'
import os, sys
corefile = os.environ["COREFILE"]
host_ip = os.environ["HOST_IP"]
hostname = os.environ["HOSTNAME_VAL"]
entry = f"        {host_ip} {hostname}"
if "hosts {" in corefile:
    if entry.strip() in corefile:
        print(corefile, end=""); sys.exit(0)
    corefile = corefile.replace("        fallthrough", entry + "\n        fallthrough")
else:
    block = f"    hosts {{\n{entry}\n        fallthrough\n    }}"
    corefile = corefile.replace(".:53 {", ".:53 {\n" + block, 1)
print(corefile, end="")
PYEOF
  )

  patch_json=$(COREFILE="${patched}" python3 -c 'import json,os; print(json.dumps({"data":{"Corefile": os.environ["COREFILE"]}}))')
  kubectl patch configmap coredns -n kube-system --type=merge -p "${patch_json}"
  kubectl delete pods -n kube-system -l k8s-app=kube-dns --wait=false 2>/dev/null || true
  echo "    CoreDNS patched. Pods restarting."
}

do_unpatch_coredns() {
  command -v kubectl &>/dev/null || { echo "ERROR: kubectl not found"; exit 1; }

  echo "==> Removing CoreDNS hosts block ..."
  local current patched patch_json
  current=$(kubectl get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}')

  patched=$(COREFILE="${current}" python3 << 'PYEOF'
import os, re
corefile = os.environ["COREFILE"]
corefile = re.sub(r"\n? *hosts *\{[^}]*\}\n?", "\n", corefile)
corefile = re.sub(r"\n{3,}", "\n\n", corefile)
print(corefile, end="")
PYEOF
  )

  patch_json=$(COREFILE="${patched}" python3 -c 'import json,os; print(json.dumps({"data":{"Corefile": os.environ["COREFILE"]}}))')
  kubectl patch configmap coredns -n kube-system --type=merge -p "${patch_json}"
  kubectl delete pods -n kube-system -l k8s-app=kube-dns --wait=false 2>/dev/null || true
  echo "    CoreDNS hosts block removed. Pods restarting."
}

# Main
if $DO_UNINSTALL; then do_uninstall; fi
if $DO_INSTALL; then do_install; fi
if $PATCH_COREDNS; then do_patch_coredns; fi
if $UNPATCH_COREDNS; then do_unpatch_coredns; fi
