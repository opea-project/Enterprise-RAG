#!/bin/bash

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#==============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

#==============================================================================
# GLOBAL CONFIGURATION
#==============================================================================

# Script metadata
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/home/$USER/enterprise-rag-install.log"

# Repository configuration
REPO_URL="https://github.com/opea-project/Enterprise-RAG.git"
REPO_DIR="/tmp/Enterprise-RAG"
GIT_BRANCH="internal_main"
DEPLOYMENT_DIR="${REPO_DIR}/deployment"
INVENTORY_DIR="${DEPLOYMENT_DIR}/inventory"
CLUSTER_CONFIG_DIR="${INVENTORY_DIR}/cluster"

# Kubernetes configuration
KUBECONFIG_PATH="${CLUSTER_CONFIG_DIR}/artifacts/admin.conf"

# Storage configuration
STORAGE_DEVICE="/dev/nvme1n1"
STORAGE_MOUNT_POINT="/mnt/nvme1"
CONTAINERD_STORAGE_DIR="${STORAGE_MOUNT_POINT}/containerd"
LOCAL_PATH_STORAGE_DIR="${STORAGE_MOUNT_POINT}/local-path-provisioner"
ETCD_DATA_DIR="${STORAGE_MOUNT_POINT}/etcd"

# Hardware configuration
HABANA_DRIVER_VERSION="1.21.1"
HABANA_RUNTIME_VERSION="1.21.1-16"
FIRMWARE_DIR="/lib/firmware"

# Python environment
PYTHON_VENV_NAME="erag-venv"
PYTHON_VENV_PATH="${DEPLOYMENT_DIR}/${PYTHON_VENV_NAME}"

# Authentication
HUGGING_FACE_TOKEN="${1:-${HUGGING_TOKEN:-}}"

# Additional
DEBUG_TOOLS=true

#==============================================================================
# LOGGING AND ERROR HANDLING
#==============================================================================

setup_logging() {
    # Create log file with proper permissions
    touch "${LOG_FILE}"
    chmod 644 "${LOG_FILE}"

    # Redirect all output to both console and log file
    exec 1> >(tee -a "${LOG_FILE}")
    exec 2> >(tee -a "${LOG_FILE}" >&2)
}

log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_warn() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $*" >&2
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2
}

log_fatal() {
    log_error "$*"
    exit 1
}

cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script failed with exit code: $exit_code"
        log_info "Check log file for details: ${LOG_FILE}"
    fi
    exit $exit_code
}

#==============================================================================
# VALIDATION FUNCTIONS
#==============================================================================

validate_prerequisites() {
    log_info "Validating system prerequisites..."

    # Check if running as non-root user with sudo access
    if [[ $EUID -eq 0 ]]; then
        log_fatal "This script should not be run as root. Please run as a regular user with sudo access."
    fi

    # Verify sudo access
    if ! sudo -n true 2>/dev/null; then
        log_fatal "This script requires sudo access. Please ensure passwordless sudo is configured."
    fi

    # Check required commands
    local required_commands=("git" "python3" "parted" "mkfs.ext4")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_fatal "Required command not found: $cmd"
        fi
    done

    # Validate storage device
    if [[ ! -b "$STORAGE_DEVICE" ]]; then
        log_fatal "Storage device not found: $STORAGE_DEVICE"
    fi

    log_info "Prerequisites validation completed successfully"
}

#==============================================================================
# SYSTEM SETUP FUNCTIONS
#==============================================================================

install_system_dependencies() {
    log_info "Installing system dependencies..."

    # Update package lists
    sudo apt-get update || log_fatal "Failed to update package lists"

    # Install required packages
    local packages=("python3-venv" "python3-pip" "parted" "git")
    sudo apt-get install -y "${packages[@]}" || log_fatal "Failed to install system packages"

    log_info "System dependencies installed successfully"
}

setup_firmware_directory() {
    log_info "Setting up firmware directory for Habana AI operator..."
    sudo mkdir -p "$FIRMWARE_DIR" || log_fatal "Failed to create firmware directory"
    log_info "Firmware directory created: $FIRMWARE_DIR"
}

#==============================================================================
# REPOSITORY MANAGEMENT
#==============================================================================

prepare_repository() {
    log_info "Preparing Enterprise RAG repository..."

    # Clean up existing repository
    if [[ -d "$REPO_DIR" ]]; then
        log_info "Removing existing repository: $REPO_DIR"
        rm -rf "$REPO_DIR"
    fi

    # Clone repository
    log_info "Cloning repository from: $REPO_URL"
    git clone "$REPO_URL" "$REPO_DIR" || log_fatal "Failed to clone repository"

    # Change branch if not main
    if [[ "$GIT_BRANCH" != "main" ]]; then
        cd "$REPO_DIR" || log_fatal "Failed to change to repository directory: $REPO_DIR"
        git fetch -a
        git checkout "$GIT_BRANCH" || log_fatal "Failed to checkout branch: $GIT_BRANCH"
        cd -
    fi

    log_info "Repository prepared successfully"
}

setup_ansible_configuration() {
    log_info "Setting up Ansible configuration..."

    # Change to deployment directory
    cd "$DEPLOYMENT_DIR" || log_fatal "Failed to change to deployment directory: $DEPLOYMENT_DIR"

    # Copy sample configuration
    if [[ ! -d "${INVENTORY_DIR}/sample" ]]; then
        log_fatal "Sample configuration directory not found: ${INVENTORY_DIR}/sample"
    fi

    cp -r "${INVENTORY_DIR}/sample/" "$CLUSTER_CONFIG_DIR" || log_fatal "Failed to copy sample configuration"

    # Copy inventory file
    if [[ ! -f "/tmp/inventory.ini" ]]; then
        log_fatal "Inventory file not found: /tmp/inventory.ini"
    fi

    cp /tmp/inventory.ini "${CLUSTER_CONFIG_DIR}/inventory.ini" || log_fatal "Failed to copy inventory file"

    # Copy config-override.yaml
    if [[ ! -f "/tmp/config-override.yaml" ]]; then
        log_fatal "Config override file not found: /tmp/config-override.yaml"
    fi

    cp /tmp/config-override.yaml "${CLUSTER_CONFIG_DIR}/config-override.yaml" || log_fatal "Failed to copy config override file"

    log_info "Ansible configuration setup completed"
}

#==============================================================================
# PYTHON ENVIRONMENT SETUP
#==============================================================================

setup_python_environment() {
    log_info "Setting up Python virtual environment..."

    # Create virtual environment
    python3 -m venv "$PYTHON_VENV_PATH" || log_fatal "Failed to create Python virtual environment"

    # Activate virtual environment
    # shellcheck source=/dev/null
    source "${PYTHON_VENV_PATH}/bin/activate" || log_fatal "Failed to activate Python virtual environment"

    # Upgrade pip
    pip install --upgrade pip || log_fatal "Failed to upgrade pip"

    # Install Python requirements
    if [[ ! -f "requirements.txt" ]]; then
        log_fatal "Python requirements file not found: requirements.txt"
    fi

    pip install -r requirements.txt || log_fatal "Failed to install Python requirements"

    # Install Ansible Galaxy requirements
    if [[ ! -f "requirements.yaml" ]]; then
        log_fatal "Ansible Galaxy requirements file not found: requirements.yaml"
    fi

    ansible-galaxy collection install -r requirements.yaml --upgrade || log_fatal "Failed to install Ansible Galaxy requirements"

    log_info "Python environment setup completed"
}

#==============================================================================
# STORAGE MANAGEMENT
#==============================================================================

create_partition_and_format_storage() {
    local device="$1"
    local mount_point="$2"

    log_info "Setting up storage on device: $device"

    # Determine partition device name
    local partition_device
    if [[ "$device" == *"nvme"* ]]; then
        partition_device="${device}p1"
    else
        partition_device="${device}1"
    fi

    # Check if partition already exists
    if [[ -b "$partition_device" ]]; then
        log_info "Partition already exists: $partition_device"
    else
        log_info "Creating partition on: $device"

        # Create GPT partition table and single partition
        sudo parted -s "$device" mklabel gpt || log_fatal "Failed to create partition table"
        sudo parted -s "$device" mkpart primary ext4 0% 100% || log_fatal "Failed to create partition"
        sudo partprobe "$device" || log_fatal "Failed to probe partitions"

        # Wait for partition to be available
        sleep 3

        if [[ ! -b "$partition_device" ]]; then
            log_fatal "Partition device not found after creation: $partition_device"
        fi
    fi

    # Format partition if needed
    if ! sudo blkid "$partition_device" | grep -q ext4; then
        log_info "Formatting partition with ext4: $partition_device"
        sudo mkfs.ext4 -F "$partition_device" || log_fatal "Failed to format partition"
    else
        log_info "Partition already formatted with ext4: $partition_device"
    fi

    # Create mount point
    sudo mkdir -p "$mount_point" || log_fatal "Failed to create mount point: $mount_point"

    # Mount partition if not already mounted
    if ! mountpoint -q "$mount_point"; then
        log_info "Mounting partition: $partition_device -> $mount_point"
        sudo mount "$partition_device" "$mount_point" || log_fatal "Failed to mount partition"

        # Add to fstab for persistent mounting
        if ! grep -q "$partition_device" /etc/fstab; then
            log_info "Adding to /etc/fstab for persistent mounting"
            echo "$partition_device $mount_point ext4 defaults 0 2" | sudo tee -a /etc/fstab
        fi
    else
        log_info "Mount point already mounted: $mount_point"
    fi

    # Set appropriate permissions
    sudo chown -R "$USER:$USER" "$mount_point" 2>/dev/null || log_warn "Failed to change ownership of mount point"

    log_info "Storage setup completed successfully"
}

setup_storage_directories() {
    log_info "Setting up storage directories..."

    # Create storage subdirectories
    local storage_dirs=("$CONTAINERD_STORAGE_DIR" "$LOCAL_PATH_STORAGE_DIR" "$ETCD_DATA_DIR")

    for dir in "${storage_dirs[@]}"; do
        sudo mkdir -p "$dir" || log_fatal "Failed to create storage directory: $dir"
        log_info "Created storage directory: $dir"
    done

    log_info "Storage directories setup completed"
}

verify_storage_mount() {
    log_info "Verifying storage mount..."

    if mountpoint -q "$STORAGE_MOUNT_POINT"; then
        log_info "Storage successfully mounted at: $STORAGE_MOUNT_POINT"

        # Display mount information
        df -h "$STORAGE_MOUNT_POINT" | tail -1 | while read -r filesystem size used avail use_percent mount; do
            log_info "Storage info - Size: $size, Used: $used, Available: $avail, Use: $use_percent"
        done
    else
        log_fatal "Storage mount verification failed: $STORAGE_MOUNT_POINT"
    fi
}

#==============================================================================
# ANSIBLE PLAYBOOK EXECUTION
#==============================================================================

run_setup_playbook() {
    log_info "Running Ansible setup playbook..."

    # Set Kubernetes configuration
    export KUBECONFIG="$KUBECONFIG_PATH"

    # Execute setup playbook
    ansible-playbook playbooks/setup.yaml \
        --tags configure \
        -i "${CLUSTER_CONFIG_DIR}/inventory.ini" \
        -e "@${CLUSTER_CONFIG_DIR}/config.yaml" \
        -e "@${CLUSTER_CONFIG_DIR}/config-override.yaml" \
        || log_fatal "Setup playbook execution failed"

    log_info "Setup playbook completed successfully"
}

run_infrastructure_playbook() {
    log_info "Running Ansible infrastructure playbook..."

    # Define infrastructure parameters
    local -a infrastructure_params=(
        "--tags" "install"
        "-i" "${CLUSTER_CONFIG_DIR}/inventory.ini"
        "-e" "@${CLUSTER_CONFIG_DIR}/config.yaml"
        "-e" "@${CLUSTER_CONFIG_DIR}/config-override.yaml"
        "-e" "kubeconfig=${KUBECONFIG_PATH}"
        "-e" "local_path_provisioner_claim_root=${LOCAL_PATH_STORAGE_DIR}"
        "-e" "containerd_storage_dir=${CONTAINERD_STORAGE_DIR}"
        "-e" "deploy_k8s=true"
        "-e" "etcd_data_dir=${ETCD_DATA_DIR}"
        "-e" "install_csi=local-path-provisioner"
    )

    # Execute infrastructure playbook
    ansible-playbook playbooks/infrastructure.yaml "${infrastructure_params[@]}" \
        || log_fatal "Infrastructure playbook execution failed"

    log_info "Infrastructure playbook completed successfully"
}

run_application_playbook() {
    log_info "Running Ansible application playbook..."

    # Define application parameters
    local -a application_params=(
        "--tags" "install"
        "-e" "@${CLUSTER_CONFIG_DIR}/config.yaml"
        "-e" "@${CLUSTER_CONFIG_DIR}/config-override.yaml"
        "-e" "kubeconfig=${KUBECONFIG_PATH}"
    )

    # Execute application playbook
    ansible-playbook playbooks/application.yaml "${application_params[@]}" \
        || log_fatal "Application playbook execution failed"

    log_info "Application playbook completed successfully"
}

#==============================================================================
# SYSTEM CONFIGURATION
#==============================================================================
configure_system_limits() {
    log_info "Configuring system limits for bare metal deployment..."

    # Configure sysctl parameters for inotify and file limits
    log_info "Setting up sysctl parameters..."

    cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes.conf
# Kubernetes optimizations for bare metal
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
fs.file-max = 2097152
EOF

    # Apply sysctl changes immediately
    sudo sysctl --system || log_fatal "Failed to apply sysctl parameters"

    # Configure user limits
    log_info "Setting up user limits..."

    cat <<EOF | sudo tee /etc/security/limits.d/99-kubernetes.conf
# Kubernetes limits for bare metal
*               soft    nofile          1048576
*               hard    nofile          1048576
*               soft    nproc           1048576
*               hard    nproc           1048576
root            soft    nofile          1048576
root            hard    nofile          1048576
root            soft    nproc           1048576
root            hard    nproc           1048576
EOF

    # Configure PAM limits to ensure limits are applied
    if ! grep -q "pam_limits.so" /etc/pam.d/common-session; then
        log_info "Adding pam_limits.so to PAM configuration..."
        echo "session required pam_limits.so" | sudo tee -a /etc/pam.d/common-session
    fi

    log_info "System limits configuration completed"
    log_info "Current file descriptor limit: $(ulimit -n)"
    log_info "fs.inotify.max_user_instances: $(sysctl -n fs.inotify.max_user_instances)"
    log_info "fs.inotify.max_user_watches: $(sysctl -n fs.inotify.max_user_watches)"
}

#==============================================================================
# HABANA AI DRIVER INSTALLATION
#==============================================================================

install_habana_driver() {
    log_info "Installing Habana AI driver and container runtime..."

    # Download Habana driver installer
    log_info "Downloading Habana driver installer version: $HABANA_DRIVER_VERSION"
    wget -nv "https://vault.habana.ai/artifactory/gaudi-installer/$HABANA_DRIVER_VERSION/habanalabs-installer.sh" \
        || log_fatal "Failed to download Habana driver installer"

    # Make installer executable and run it
    chmod +x habanalabs-installer.sh
    log_info "Installing Habana driver (base installation)..."
    ./habanalabs-installer.sh install --type base -y \
        || log_fatal "Failed to install Habana driver"

    # Install Habana container runtime
    log_info "Installing Habana container runtime version: $HABANA_RUNTIME_VERSION"
    sudo apt install "habanalabs-container-runtime=$HABANA_RUNTIME_VERSION" -y \
        || log_fatal "Failed to install Habana container runtime"

    # Backup existing containerd configuration
    log_info "Backing up existing containerd configuration..."
    sudo mv /etc/containerd/config.toml /etc/containerd/config.toml.bak \
        || log_warn "Failed to backup existing containerd config"

    # Configure containerd for Habana runtime
    log_info "Configuring containerd for Habana runtime..."
    cat <<EOF | sudo tee /etc/containerd/config.toml
root = "$CONTAINERD_STORAGE_DIR"
state = "/run/containerd"
oom_score = 0
disabled_plugins = []
version = 2
[plugins]
  [plugins."io.containerd.grpc.v1.cri"]
    sandbox_image = "registry.k8s.io/pause:3.10"
    max_container_log_line_size = 16384
    enable_unprivileged_ports = false
    enable_unprivileged_icmp = false
    enable_selinux = false
    disable_apparmor = false
    tolerate_missing_hugetlb_controller = true
    disable_hugetlb_controller = true
    image_pull_progress_timeout = "5m"
    [plugins."io.containerd.grpc.v1.cri".containerd]
      default_runtime_name = "habana"
      snapshotter = "overlayfs"
      discard_unpacked_layers = true
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.habana]
          runtime_type = "io.containerd.runc.v2"
          runtime_engine = ""
          runtime_root = ""
          base_runtime_spec = "/etc/containerd/cri-base.json"
          [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.habana.options]
            BinaryName = "/usr/bin/habana-container-runtime"
    [plugins."io.containerd.grpc.v1.cri".registry]
      config_path = "/etc/containerd/certs.d"
EOF

    # Restart containerd service
    log_info "Restarting containerd service..."
    sudo systemctl restart containerd \
        || log_fatal "Failed to restart containerd service"

    # Deploy Habana device plugin to Kubernetes
    log_info "Deploying Habana Kubernetes device plugin..."
    kubectl create -f https://vault.habana.ai/artifactory/docker-k8s-device-plugin/habana-k8s-device-plugin.yaml \
        || log_fatal "Failed to deploy Habana device plugin"

    # Clean up installer file
    rm -f habanalabs-installer.sh || log_warn "Failed to clean up installer file"

    log_info "Habana AI driver installation completed successfully"
}

#==============================================================================
# MAIN EXECUTION FLOW
#==============================================================================

main() {
    # Set up error handling
    trap cleanup_on_exit EXIT

    # Initialize logging
    setup_logging

    log_info "=== Starting Enterprise RAG Installation ==="
    log_info "Script: $SCRIPT_NAME"
    log_info "Started at: $(date)"
    log_info "Log file: $LOG_FILE"

    # Validation phase
    validate_prerequisites

    # System setup phase
    install_system_dependencies
    setup_firmware_directory

    # Repository setup phase
    prepare_repository
    setup_ansible_configuration

    # Python environment setup
    setup_python_environment

    # Configure system limits
    configure_system_limits

    # Storage setup phase
    create_partition_and_format_storage "$STORAGE_DEVICE" "$STORAGE_MOUNT_POINT"
    setup_storage_directories
    verify_storage_mount

    # Prepare ssh connection for Ansible
    echo -e 'y\n' | ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/ansible -q && cat ~/.ssh/ansible.pub >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys

    # Ansible execution phase
    run_setup_playbook
    run_infrastructure_playbook

    # Install additional tools (k9s)
    if $DEBUG_TOOLS; then
        wget https://github.com/derailed/k9s/releases/download/v0.50.9/k9s_Linux_amd64.tar.gz
        tar xf k9s_Linux_amd64.tar.gz
        sudo mv k9s /usr/local/bin/
        rm k9s_Linux_amd64.tar.gz
    fi

    # Setup kubeconfig
    mkdir -p ~/.kube/ && cp "$KUBECONFIG_PATH" ~/.kube/config

    # Install Habana AI driver and runtime
    install_habana_driver

    # Run application deployment
    run_application_playbook

    cp -r $DEPLOYMENT_DIR/ansible-logs /home/$USER/ansible-logs

    log_info "=== Enterprise RAG Installation Completed Successfully ==="
    log_info "Completed at: $(date)"
}

# Execute main function
main "$@"
