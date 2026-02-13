#!/bin/bash

# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#==============================================================================
# Enterprise RAG Installation Script
# Unified script for AWS and IBM Cloud deployments with configurable options
#==============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

#==============================================================================
# SCRIPT METADATA AND DEFAULTS
#==============================================================================

SCRIPT_NAME="$(basename "$0")"
SCRIPT_VERSION="2.1.0"
LOG_FILE="/home/$USER/enterprise-rag-install.log"

#==============================================================================
# CONFIGURABLE OPTIONS (can be overridden by flags)
#==============================================================================

# Platform configuration
PLATFORM=""                    # aws, ibm (auto-detected if not specified)
INSTALL_GAUDI_DRIVER=false     # Install Intel Gaudi drivers and runtime
CONFIGURE_STORAGE=true         # Configure storage (partition, mount, directories)
INSTALL_DEBUG_TOOLS=false      # Install debug tools (k9s, etc.)

# Repository configuration
REPO_URL="https://github.com/opea-project/Enterprise-RAG.git"
REPO_DIR="$HOME/Enterprise-RAG"
GIT_VERSION="release-2.1.0"       # Git version to checkout - can be tag or branch (default: 'release-2.1.0')
DEPLOYMENT_DIR="${REPO_DIR}/deployment"
INVENTORY_DIR="${DEPLOYMENT_DIR}/inventory"
CLUSTER_CONFIG_DIR="${INVENTORY_DIR}/cluster"

# Kubernetes configuration
KUBECONFIG_PATH="${CLUSTER_CONFIG_DIR}/artifacts/admin.conf"

# Installation stage configuration
INSTALLATION_STAGE=""          # system, cluster, application, or empty for full install
STATE_DIR="/home/$USER/.erag-install-state"
FORCE_STAGE=false              # Force re-run of a completed stage

# Python environment
PYTHON_VENV_NAME="erag-venv"
PYTHON_VENV_PATH="${HOME}/${PYTHON_VENV_NAME}"

# Timeout
HELM_TIMEOUT=30m00s

#==============================================================================
# PLATFORM-SPECIFIC DEFAULTS
#==============================================================================

# Storage configuration (will be set based on platform)
STORAGE_DEVICE=""
STORAGE_MOUNT_POINT=""
CONTAINERD_STORAGE_DIR=""
LOCAL_PATH_STORAGE_DIR=""
ETCD_DATA_DIR=""

# Hardware configuration (Gaudi-specific)
HABANA_VERSION=""
HABANA_VERSION_MINOR="" # version up to minor, e.g.1.22.3-32 --> 1.22.3
#==============================================================================
# USAGE AND HELP
#==============================================================================

show_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Enterprise RAG Installation Script v${SCRIPT_VERSION}
Unified installer for AWS and IBM Cloud deployments

OPTIONAL FLAGS:
    -p, --platform PLATFORM       Target platform: aws, ibm
    -g, --gaudi                   Install Intel Gaudi drivers and runtime
    --habana-version VERSION      Habana driver/runtime version (required with --gaudi)
    -s, --skip-storage            Skip storage configuration
    -d, --debug                   Install debug tools (k9s, htop, etc.)
    --stage STAGE                 Run specific stage: system, cluster, application
    --force                       Force re-run of completed stage
    -v, --version VERSION         Git version to checkout - can be tag or branch (default: release-2.0.0)
    -t, --tag TAG                 Alias for --version (for backwards compatibility)
    --help                        Show this help message

STAGES:
    system                        System preparation (storage, dependencies, drivers)
    cluster                       Kubernetes cluster installation
    application                   Application deployment and configuration
    (no stage)                    Run full installation

EXAMPLES:
    # Full installation
    $SCRIPT_NAME --platform aws --gaudi --habana-version 1.22.2-32

    # Run only system preparation stage
    $SCRIPT_NAME --platform aws --stage system

    # Force re-run cluster stage after failure
    $SCRIPT_NAME --platform aws --stage cluster --force

    # Installation with debug tools enabled
    $SCRIPT_NAME --debug

NOTES:
    - Storage configuration includes partitioning, mounting, and directory setup
    - Gaudi drivers are only installed if explicitly requested
    - Debug tools include k9s, htop, iotop, and other monitoring utilities

EOF
}

#==============================================================================
# ARGUMENT PARSING
#==============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--platform)
                PLATFORM="$2"
                shift 2
                ;;
            -g|--gaudi)
                INSTALL_GAUDI_DRIVER=true
                shift
                ;;
            --habana-version)
                HABANA_VERSION="$2"
                HABANA_VERSION_MINOR=$(echo "$HABANA_VERSION" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')
                shift 2
                ;;
            -s|--skip-storage)
                CONFIGURE_STORAGE=false
                shift
                ;;
            -d|--debug)
                INSTALL_DEBUG_TOOLS=true
                shift
                ;;
            --stage)
                INSTALLATION_STAGE="$2"
                shift 2
                ;;
            --force)
                FORCE_STAGE=true
                shift
                ;;
            -v|--version|-t|--tag)
                GIT_VERSION="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate platform
    if [[ "$PLATFORM" != "aws" && "$PLATFORM" != "ibm" ]]; then
        echo "Error: Platform must be 'aws' or 'ibm'"
        show_usage
        exit 1
    fi

    # Require --habana-version if --gaudi is set
    if [[ "$INSTALL_GAUDI_DRIVER" == "true" && -z "$HABANA_VERSION" ]]; then
        echo "Error: --habana-version is required when using --gaudi"
        show_usage
        exit 1
    fi

    # Validate stage if provided
    if [[ -n "$INSTALLATION_STAGE" ]]; then
        case "$INSTALLATION_STAGE" in
            system|cluster|application)
                log_info "Running stage: $INSTALLATION_STAGE"
                ;;
            *)
                echo "Error: Invalid stage '$INSTALLATION_STAGE'. Must be: system, cluster, or application"
                show_usage
                exit 1
                ;;
        esac
    fi
}

#==============================================================================
# STATE MANAGEMENT FUNCTIONS
#==============================================================================

create_state_dir() {
    mkdir -p "$STATE_DIR"
    chmod 700 "$STATE_DIR"
}

mark_stage_completed() {
    local stage="$1"
    create_state_dir
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "${STATE_DIR}/${stage}.completed"
    log_info "Marked stage '$stage' as completed"
}

is_stage_completed() {
    local stage="$1"
    [[ -f "${STATE_DIR}/${stage}.completed" ]]
}

should_run_stage() {
    local stage="$1"

    # If specific stage requested, check if we should run it
    if [[ -n "$INSTALLATION_STAGE" && "$INSTALLATION_STAGE" != "$stage" ]]; then
        return 1  # Don't run this stage
    fi

    # If stage already completed and not forced, skip it
    if is_stage_completed "$stage" && [[ "$FORCE_STAGE" != "true" ]]; then
        log_info "Stage '$stage' already completed, skipping (use --force to re-run)"
        return 1  # Don't run this stage
    fi

    # If specific stage requested or full install, run it
    return 0  # Run this stage
}

show_installation_status() {
    log_info "=== Installation Status ==="
    for stage in system cluster application; do
        if is_stage_completed "$stage"; then
            local completion_time
            completion_time=$(cat "${STATE_DIR}/${stage}.completed" 2>/dev/null || echo "unknown")
            log_info "  ✅ $stage (completed: $completion_time)"
        else
            log_info "  ❌ $stage (not completed)"
        fi
    done
}

#==============================================================================
# PLATFORM-SPECIFIC CONFIGURATION
#==============================================================================

configure_platform_defaults() {
    case "$PLATFORM" in
        aws)
            log_info "Configuring AWS platform defaults"
            CONFIGURE_STORAGE=false
            ;;
        ibm)
            log_info "Configuring IBM Cloud platform defaults"
            if [[ "$INSTALL_GAUDI_DRIVER" == "true" ]]; then
                STORAGE_DEVICE="/dev/nvme1n1"
                STORAGE_MOUNT_POINT="/mnt/nvme1"
            else
                STORAGE_DEVICE="/dev/vdb"
                STORAGE_MOUNT_POINT="/mnt/vdb1"
            fi
            CONTAINERD_STORAGE_DIR="${STORAGE_MOUNT_POINT}/containerd"
            LOCAL_PATH_STORAGE_DIR="${STORAGE_MOUNT_POINT}/local-path-provisioner"
            ETCD_DATA_DIR="${STORAGE_MOUNT_POINT}/etcd"
            ;;
    esac

    log_info "Storage device: $STORAGE_DEVICE"
    log_info "Mount point: $STORAGE_MOUNT_POINT"
}

#==============================================================================
# LOGGING AND ERROR HANDLING
#==============================================================================

setup_logging() {
    touch "${LOG_FILE}"
    chmod 644 "${LOG_FILE}"
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
    log_info "🔍 Validating system prerequisites..."

    # Check if running as non-root user with sudo access
    if [[ $EUID -eq 0 ]]; then
        log_fatal "This script should not be run as root. Please run as a regular user with sudo access."
    fi

    # Verify sudo access
    if ! sudo -n true 2>/dev/null; then
        log_fatal "This script requires sudo access. Please ensure passwordless sudo is configured."
    fi

    # Validate storage device if storage configuration is enabled
    if [[ "$CONFIGURE_STORAGE" == "true" && ! -b "$STORAGE_DEVICE" ]]; then
        log_warn "Storage device not found: $STORAGE_DEVICE"
        log_info "Use --skip-storage if storage configuration is not needed"
    fi

    # Check Gaudi hardware if driver installation is enabled
    if [[ "$INSTALL_GAUDI_DRIVER" == "true" ]]; then
        if ! lspci | grep -i habana >/dev/null 2>&1; then
            log_warn "No Habana Gaudi hardware detected"
            log_info "Gaudi drivers will be installed but may not function without hardware"
        fi
    fi

    log_info "Prerequisites validation completed"
}

#==============================================================================
# SYSTEM SETUP FUNCTIONS
#==============================================================================

install_system_dependencies() {
    log_info "Installing system dependencies..."

    # Update package lists
    sudo apt-get update

    # Detect Python version and install appropriate venv package
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP 'Python \K\d+\.\d+')
    log_info "Detected Python version: $PYTHON_VERSION"

    # Install required packages
    local packages=("python3-pip" "git" "curl" "wget")

    # Add Python version-specific venv package
    packages+=("python${PYTHON_VERSION}-venv")

    # Also try generic python3-venv as fallback
    packages+=("python3-venv")

    # Add storage-related packages if storage configuration is enabled
    if [[ "$CONFIGURE_STORAGE" == "true" ]]; then
        packages+=("parted")
    fi

    # Install packages individually to handle failures gracefully
    for package in "${packages[@]}"; do
        if sudo apt-get install -y "$package" 2>/dev/null; then
            log_info "Successfully installed: $package"
        else
            log_warn "Failed to install: $package (continuing anyway)"
        fi
    done

    # Verify python3-venv is available
    if ! python3 -m venv --help >/dev/null 2>&1; then
        log_fatal "Python venv module is not available. Please install python3-venv or python${PYTHON_VERSION}-venv manually."
    fi

    log_info "System dependencies installed successfully"
}

#==============================================================================
# REPOSITORY MANAGEMENT
#==============================================================================

prepare_repository() {
    log_info "Preparing Enterprise RAG repository..."

    # Clean up existing repository
    if [[ -d "$REPO_DIR" ]]; then
        log_info "Removing existing repository: $REPO_DIR"
        rm -rf $REPO_DIR
    fi

    # Clone repository
    log_info "Cloning repository from: $REPO_URL"
    git clone $REPO_URL $REPO_DIR

    cd $REPO_DIR

    # Checkout specified version (try as tag first, then as branch)
    if [[ "$GIT_VERSION" != "main" && "$GIT_VERSION" != "" ]]; then
        log_info "Fetching all tags and branches..."
        git fetch --all --tags
        
        # Try to checkout as a tag first
        if git show-ref --tags --quiet --verify "refs/tags/$GIT_VERSION"; then
            log_info "Checking out tag: $GIT_VERSION"
            git checkout "tags/$GIT_VERSION"
        else
            # If not a tag, try as a branch
            log_info "Version '$GIT_VERSION' is not a tag, checking out as branch"
            git checkout "$GIT_VERSION" 2>/dev/null || {
                log_warn "Failed to checkout '$GIT_VERSION' as branch, using main"
                git checkout main
            }
        fi
    else
        log_info "Using default branch: main"
    fi

    log_info "Repository prepared successfully"
}

setup_ansible_configuration() {
    log_info "Setting up Ansible configuration..."

    # Change to deployment directory
    cd $DEPLOYMENT_DIR

    # Copy sample configuration
    if [[ ! -d "${INVENTORY_DIR}/sample" ]]; then
        log_fatal "Sample configuration directory not found: ${INVENTORY_DIR}/sample"
    fi

    cp -r ${INVENTORY_DIR}/sample/ $CLUSTER_CONFIG_DIR

    # Copy configuration files if they exist
    for config_file in "/tmp/inventory.ini" "/tmp/config-override.yaml"; do
        if [[ -f "$config_file" ]]; then
            cp $config_file ${CLUSTER_CONFIG_DIR}/
            log_info "Copied: $(basename $config_file)"
        else
            log_warn "Configuration file not found: $config_file"
        fi
    done

    log_info "Ansible configuration setup completed"
}

#==============================================================================
# PYTHON ENVIRONMENT SETUP
#==============================================================================

setup_python_environment() {
    log_info "Setting up Python virtual environment..."

    # Check if virtual environment already exists and is valid
    if [[ -f "${PYTHON_VENV_PATH}/bin/activate" ]] && [[ -f "${PYTHON_VENV_PATH}/bin/python3" ]]; then
        log_info "Valid Python virtual environment already exists at: $PYTHON_VENV_PATH"
    else
        # Remove incomplete/invalid virtual environment if it exists
        if [[ -d "$PYTHON_VENV_PATH" ]]; then
            log_info "Removing incomplete virtual environment: $PYTHON_VENV_PATH"
            rm -rf "$PYTHON_VENV_PATH"
        fi

        # Create virtual environment
        log_info "Creating new Python virtual environment..."
        python3 -m venv "$PYTHON_VENV_PATH"
        log_info "Created new Python virtual environment at: $PYTHON_VENV_PATH"
    fi

    # Activate virtual environment
    # shellcheck source=/dev/null
    source "${PYTHON_VENV_PATH}/bin/activate"
    pip install --upgrade pip

    # Install Python requirements if file exists
    if [[ -f "$DEPLOYMENT_DIR/requirements.txt" ]]; then
        pip install -r "$DEPLOYMENT_DIR/requirements.txt"
    fi

    # Install Ansible Galaxy requirements if file exists
    if [[ -f "$DEPLOYMENT_DIR/requirements.yaml" ]]; then
        ansible-galaxy collection install -r "$DEPLOYMENT_DIR/requirements.yaml" --upgrade
    fi

    log_info "Python environment setup completed"
}

#==============================================================================
# STORAGE MANAGEMENT
#==============================================================================

configure_storage_setup() {
    if [[ "$CONFIGURE_STORAGE" == "false" ]]; then
        log_info "Skipping storage configuration as requested"
        return 0
    fi

    log_info "Configuring storage setup..."

    # Create partition and format storage
    create_partition_and_format_storage "$STORAGE_DEVICE" "$STORAGE_MOUNT_POINT"

    # Setup storage directories
    setup_storage_directories

    # Verify storage mount
    verify_storage_mount

    log_info "Storage configuration completed"
}

create_partition_and_format_storage() {
    local device="$1"
    local mount_point="$2"

    log_info "🔧 Setting up storage on device: $device"

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
        sudo parted -s $device mklabel gpt
        sudo parted -s $device mkpart primary ext4 0% 100%
        sudo partprobe $device

        # Wait for partition to be available (up to 10 seconds)
        for i in {1..10}; do
            if [[ -b "$partition_device" ]]; then
                break
            fi
            sleep 1
        done
        if [[ ! -b "$partition_device" ]]; then
            log_fatal "Partition device not found after creation: $partition_device"
        fi
    fi

    # Format partition if needed
    if ! sudo blkid "$partition_device" | grep -q ext4; then
        log_info "Formatting partition with ext4: $partition_device"
        sudo mkfs.ext4 -F $partition_device
    else
        log_info "Partition already formatted with ext4: $partition_device"
    fi

    # Create mount point and mount
    sudo mkdir -p $mount_point

    if ! mountpoint -q "$mount_point"; then
        log_info "Mounting partition: $partition_device -> $mount_point"
        sudo mount $partition_device $mount_point

        # Add to fstab for persistent mounting
        if ! grep -q "$partition_device" /etc/fstab; then
            log_info "Adding to /etc/fstab for persistent mounting"
            echo "$partition_device $mount_point ext4 defaults 0 2" | sudo tee -a /etc/fstab
        fi
    else
        log_info "Mount point already mounted: $mount_point"
    fi

    # Set appropriate permissions
    sudo chown -R $USER:$USER $mount_point

    log_info "Storage setup completed successfully"
}

setup_storage_directories() {
    log_info "Setting up storage directories..."

    # Create storage subdirectories
    local storage_dirs=("$CONTAINERD_STORAGE_DIR" "$LOCAL_PATH_STORAGE_DIR" "$ETCD_DATA_DIR")

    for dir in "${storage_dirs[@]}"; do
        sudo mkdir -p $dir
        log_info "Created storage directory: $dir"
    done

    log_info "Storage directories setup completed"
}

verify_storage_mount() {
    log_info "Verifying storage mount..."

    if mountpoint -q "$STORAGE_MOUNT_POINT"; then
        log_info "Storage successfully mounted at: $STORAGE_MOUNT_POINT"

        # Display mount information
        df -h "$STORAGE_MOUNT_POINT" | tail -1 | while read -r _filesystem size used avail use_percent _mount; do
            log_info "Storage info - Size: $size, Used: $used, Available: $avail, Use: $use_percent"
        done
    else
        log_fatal "Storage mount verification failed: $STORAGE_MOUNT_POINT"
    fi
}

#==============================================================================
# SYSTEM CONFIGURATION
#==============================================================================

configure_system_limits() {
    log_info "Configuring system limits for Enterprise RAG deployment..."

    # Configure sysctl parameters
    log_info "Setting up sysctl parameters..."

    cat <<EOF | sudo tee /etc/sysctl.d/99-enterprise-rag.conf
# Enterprise RAG optimizations
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
fs.file-max = 2097152
vm.max_map_count = 262144
EOF

    # Apply sysctl changes
    sudo sysctl --system

    # Configure user limits
    log_info "Setting up user limits..."

    cat <<EOF | sudo tee /etc/security/limits.d/99-enterprise-rag.conf
# Enterprise RAG limits
*               soft    nofile          1048576
*               hard    nofile          1048576
*               soft    nproc           1048576
*               hard    nproc           1048576
root            soft    nofile          1048576
root            hard    nofile          1048576
root            soft    nproc           1048576
root            hard    nproc           1048576
EOF

    # Configure PAM limits
    if ! grep -q "pam_limits.so" /etc/pam.d/common-session; then
        log_info "Adding pam_limits.so to PAM configuration..."
        echo 'session required pam_limits.so' | sudo tee -a /etc/pam.d/common-session
    fi

    log_info "System limits configuration completed"
}

#==============================================================================
# HABANA AI DRIVER INSTALLATION
#==============================================================================

install_habana_driver() {
    if [[ "$INSTALL_GAUDI_DRIVER" == "false" ]]; then
        log_info "⏭️ Skipping Habana AI driver installation as requested"
        return 0
    fi

    log_info "Installing Habana AI driver and container runtime..."

    # Download Habana driver installer
    log_info "Downloading Habana driver installer version: $HABANA_VERSION_MINOR"
    wget -nv https://vault.habana.ai/artifactory/gaudi-installer/$HABANA_VERSION_MINOR/habanalabs-installer.sh

    # Install driver
    chmod +x habanalabs-installer.sh
    log_info "Installing Habana driver (base installation)..."
    ./habanalabs-installer.sh install --type base -y

    # Install container runtime
    log_info "Installing Habana container runtime version: $HABANA_VERSION"
    sudo apt install habanalabs-container-runtime=$HABANA_VERSION -y

    # Configure containerd
    configure_containerd_for_habana

    # Deploy Kubernetes device plugin
    if command -v kubectl >/dev/null 2>&1; then
        log_info "Deploying Habana Kubernetes device plugin..."
        kubectl apply -f /tmp/habana-k8s-device-plugin.yaml
    fi

    # Cleanup
    rm -f habanalabs-installer.sh

    log_info "Habana AI driver installation completed successfully"
}

configure_containerd_for_habana() {
    log_info "Configuring containerd for Habana runtime..."

    # Backup existing configuration
    sudo mv /etc/containerd/config.toml /etc/containerd/config.toml.bak 2>/dev/null || true

    # Determine containerd root directory line
    local containerd_root_line=""
    if [[ -n "$CONTAINERD_STORAGE_DIR" ]]; then
        containerd_root_line="root = \"$CONTAINERD_STORAGE_DIR\""
        log_info "Using custom containerd storage: $CONTAINERD_STORAGE_DIR"
    else
        log_info "Using default containerd storage location"
    fi

    # Create new containerd configuration
    cat <<EOF | sudo tee /etc/containerd/config.toml
$containerd_root_line
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

    # Restart containerd
    sudo systemctl restart containerd

    log_info "Containerd configured for Habana runtime"
}

#==============================================================================
# STAGE-SPECIFIC EXECUTION FUNCTIONS
#==============================================================================

run_system_stage() {
    if ! should_run_stage "system"; then
        return 0
    fi

    log_info "=== STARTING SYSTEM STAGE ==="

    # Validation phase
    validate_prerequisites

    # System setup phase
    install_system_dependencies

    # Python environment setup (now that dependencies are installed)
    setup_python_environment

    # Repository setup phase
    prepare_repository
    setup_ansible_configuration

    # System configuration
    configure_system_limits

    # Storage configuration
    configure_storage_setup

    # SSH setup for Ansible
    log_info "Setting up SSH for Ansible..."
    echo -e 'y\n' | ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/ansible -q && cat ~/.ssh/ansible.pub >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys

    mark_stage_completed "system"
    log_info "=== SYSTEM STAGE COMPLETED ==="
}

run_cluster_stage() {
    if ! should_run_stage "cluster"; then
        return 0
    fi

    log_info "=== STARTING CLUSTER STAGE ==="

    # Ensure Python environment is available
    setup_python_environment

    # Ensure we're in the right directory and virtual environment
    cd "$DEPLOYMENT_DIR" || log_fatal "Failed to change to deployment directory"

    # Activate Python virtual environment
    # shellcheck source=/dev/null
    source "${PYTHON_VENV_PATH}/bin/activate"

    # Run Ansible playbooks for infrastructure
    run_setup_playbook
    run_infrastructure_playbook

    # Install Habana AI driver (one-time setup)
    install_habana_driver

    # Install debug tools
    install_debug_tools

    # Setup kubeconfig
    log_info "Setting up kubeconfig..."
    mkdir -p ~/.kube/
    cp "$KUBECONFIG_PATH" ~/.kube/config

    mark_stage_completed "cluster"
    log_info "=== CLUSTER STAGE COMPLETED ==="
}

run_application_stage() {
    if ! should_run_stage "application"; then
        return 0
    fi

    log_info "=== STARTING APPLICATION STAGE ==="

    # Ensure Python environment is available
    setup_python_environment

    # Ensure we're in the right directory and virtual environment
    cd "$DEPLOYMENT_DIR" || log_fatal "Failed to change to deployment directory"

    # Activate Python virtual environment
    # shellcheck source=/dev/null
    source "${PYTHON_VENV_PATH}/bin/activate"

    # Run application deployment
    run_application_playbook

    # Copy ansible logs
    cp -r "$DEPLOYMENT_DIR/ansible-logs" "/home/$USER/ansible-logs"

    mark_stage_completed "application"
    log_info "=== APPLICATION STAGE COMPLETED ==="
}

#==============================================================================
# DEBUG TOOLS INSTALLATION
#==============================================================================

install_debug_tools() {
    if [[ "$INSTALL_DEBUG_TOOLS" == "false" ]]; then
        log_info "Skipping debug tools installation as requested"
        return 0
    fi

    log_info "Installing debug tools..."

    # Install system monitoring tools
    local debug_packages=("htop" "iotop" "nethogs" "tcpdump" "nmap" "curl" "wget" "jq" "tree")
    sudo apt-get install -y "${debug_packages[@]}"

    # Install k9s (Kubernetes CLI)
    log_info "Installing k9s..."
    wget https://github.com/derailed/k9s/releases/download/v0.50.9/k9s_Linux_amd64.tar.gz
    tar xf k9s_Linux_amd64.tar.gz
    sudo mv k9s /usr/local/bin/
    rm k9s_Linux_amd64.tar.gz

    log_info "Debug tools installation completed"
}

#==============================================================================
# ANSIBLE PLAYBOOK EXECUTION
#==============================================================================

run_setup_playbook() {
    log_info "Running Ansible setup playbook..."

    # Set Kubernetes configuration
    export KUBECONFIG=$KUBECONFIG_PATH

    # Execute setup playbook
    ansible-playbook playbooks/setup.yaml --tags configure -i ${CLUSTER_CONFIG_DIR}/inventory.ini -e @${CLUSTER_CONFIG_DIR}/config.yaml -e @${CLUSTER_CONFIG_DIR}/config-override.yaml

    log_info "Setup playbook completed successfully"
}

run_infrastructure_playbook() {
    log_info "Running Ansible infrastructure playbook..."

    # Define infrastructure parameters
    local infrastructure_params=(
        "--tags" "install"
        "-i" "${CLUSTER_CONFIG_DIR}/inventory.ini"
        "-e" "@${CLUSTER_CONFIG_DIR}/config.yaml"
        "-e" "@${CLUSTER_CONFIG_DIR}/config-override.yaml"
        "-e" "kubeconfig=${KUBECONFIG_PATH}"
        "-e" "deploy_k8s=true"
        "-e" "install_csi=local-path-provisioner"
    )

    if $CONFIGURE_STORAGE; then
        infrastructure_params+=("-e" "local_path_provisioner_claim_root=${LOCAL_PATH_STORAGE_DIR}")
        infrastructure_params+=("-e" "containerd_storage_dir=${CONTAINERD_STORAGE_DIR}")
        infrastructure_params+=("-e" "etcd_data_dir=${ETCD_DATA_DIR}")
    fi

    # Execute infrastructure playbook
    ansible-playbook playbooks/infrastructure.yaml "${infrastructure_params[@]}"

    log_info "Infrastructure playbook completed successfully"
}

run_application_playbook() {
    log_info "Running Ansible application playbook..."

    # Define application parameters
    local application_params=(
        "--tags" "install"
        "-e" "@${CLUSTER_CONFIG_DIR}/config.yaml"
        "-e" "@${CLUSTER_CONFIG_DIR}/config-override.yaml"
        "-e" "helm_timeout=${HELM_TIMEOUT}"
        "-e" "kubeconfig=${KUBECONFIG_PATH}"
    )

    # Execute application playbook
    ansible-playbook playbooks/application.yaml "${application_params[@]}"

    log_info "Application playbook completed successfully"
}

#==============================================================================
# MAIN EXECUTION FLOW
#==============================================================================

show_configuration() {
    log_info "Current Configuration:"
    log_info "  Platform: $PLATFORM"
    log_info "  Install Gaudi Driver: $INSTALL_GAUDI_DRIVER"
    log_info "  Configure Storage: $CONFIGURE_STORAGE"
    log_info "  Install Debug Tools: $INSTALL_DEBUG_TOOLS"
    log_info "  Git Version: $GIT_VERSION"
    log_info "  Storage Device: $STORAGE_DEVICE"
    log_info "  Storage Mount: $STORAGE_MOUNT_POINT"
}

main() {
    # Set up error handling
    trap cleanup_on_exit EXIT

    # Parse command line arguments
    parse_arguments "$@"

    # Configure platform-specific defaults
    configure_platform_defaults

    # Setup logging
    setup_logging

    # Create state directory for tracking
    create_state_dir

    # Show banner
    log_info "Enterprise RAG Installation Script v${SCRIPT_VERSION}"
    log_info "Target Platform: $PLATFORM"

    # Show configuration
    show_configuration

    # Handle status display
    if [[ "$INSTALLATION_STAGE" == "status" ]]; then
        show_installation_status
        exit 0
    fi

    # Execute installation stages
    log_info "=== Starting Enterprise RAG Installation ==="
    log_info "Started at: $(date)"
    log_info "Log file: $LOG_FILE"

    # Execute specific stage or all stages
    case "$INSTALLATION_STAGE" in
        "system")
            run_system_stage
            ;;
        "cluster")
            run_cluster_stage
            ;;
        "application")
            run_application_stage
            ;;
        "all"|*)
            # Run all stages in sequence
            run_system_stage
            run_cluster_stage
            run_application_stage
            ;;
    esac

    # Final success message
    log_info "=== Enterprise RAG Installation Completed Successfully ==="
    log_info "Completed at: $(date)"
    log_info "Next steps:"
    log_info "  1. Verify deployment: kubectl get pods --all-namespaces"
    log_info "  2. Access logs: tail -f ${LOG_FILE}"

    if [[ "$INSTALL_DEBUG_TOOLS" == "true" ]]; then
        log_info "  3. Monitor with k9s: k9s"
    fi

    # Show final status
    show_installation_status
}

# Execute main function with all arguments
main "$@"
