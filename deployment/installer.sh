#!/bin/bash
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# EXPERIMENTAL FEATURE
# This installer script is currently an experimental feature and may undergo
# significant changes. Use with caution in production environments.

set -e
set -o pipefail
#set -x # Uncomment for debugging

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_DIR="inventory"
DEFAULT_CONFIG="${ERAG_CONFIG_DIR:-${CONFIG_DIR}/cluster}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Display experimental feature warning
echo -e "${YELLOW}EXPERIMENTAL FEATURE${NC}"
echo -e "${YELLOW}This installer script is currently an experimental feature and may undergo significant changes.${NC}"
echo -e "${YELLOW}Use with caution in production environments.${NC}"
echo ""

log() {
    local level=$1
    local message=$2
    local color=$NC

    case $level in
        "INFO") color=$BLUE ;;
        "DEBUG") color=$NC ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "SUCCESS") color=$GREEN ;;
    esac

    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message${NC}"
}

# Check virtual environment status  
check_venv() {
    if [[ -d "$VENV_PATH" ]]; then
        log "INFO" "Using Enterprise RAG virtual environment: $VENV_PATH"
        # Check if ansible is available in the venv
        if [[ -f "$VENV_PATH/bin/ansible-playbook" ]]; then
            log "INFO" "Ansible found in virtual environment"
        else
            log "WARN" "Ansible not found in virtual environment"
            log "INFO" "Run: $0 setup python-env"
        fi
    else
        log "WARN" "Enterprise RAG virtual environment not found"
        log "INFO" "To create one: $0 setup python-env"
    fi
}

show_help() {
    echo -e "${BLUE}Enterprise RAG Deployment Tool${NC}"
    echo -e "${BLUE}============================${NC}"
    echo "Usage: $0 <component> <action> [options]"
    echo ""
    echo "Components and actions:"
    echo "  setup"
    echo "    python-env            - Initialize Python virtual environment and install packages"
    echo "                            After creation, activate with: source erag-venv/bin/activate"
    echo "    configure             - Configure deployment environment"
    echo "    images                - Build and push application images"
    echo "    config [directory]    - Generate configuration variables interactively in specified directory"
    echo ""
    echo "  validate"
    echo "    config                - Validate configuration"
    echo "    hardware              - Validate hardware"
    echo ""
    echo "  cluster"
    echo "    deploy                - Deploy Kubernetes cluster"
    echo "    post-install          - Post-installation tasks for Kubernetes cluster"
    echo "    delete                - Delete Kubernetes cluster"
    echo ""
    echo "  application"
    echo "    install               - Install the application"
    echo "    uninstall             - Uninstall the application"
    echo "    show-config           - Display current configuration and validation status"
    echo ""
    echo "  stack"
    echo "    deploy-complete       - Deploy complete Enterprise RAG stack"
    echo "    delete-complete       - Delete complete Enterprise RAG stack"
    echo ""
    echo "Options:"
    echo "  --config=<path>         - Path to config.yaml file"
    echo "  --inventory=<path>      - Path to Ansible inventory file"
    echo "  --tag=<tag>             - Specify image tag (overrides config value)"
    echo "  --registry=<registry>   - Specify image registry (overrides config value)"
    echo "  --non-interactive       - Run configuration with default values (no prompts)"
    echo "  -v, -vv, -vvv           - Set verbosity level for Ansible"
    echo "  -h, --help              - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ERAG_CONFIG_DIR         - Default config directory path (config.yaml/inventory.ini will be loaded from this directory)"
    echo "  HF_TOKEN                - Hugging Face token for private model access"
    echo "  KUBECONFIG              - Path to kubeconfig file for cluster access"
    echo ""
    echo "Examples:"
    echo "  # Virtual environment setup"
    echo "  $0 setup python-env"
    echo ""
    echo "  # Interactive configuration"
    echo "  $0 setup config"
    echo "  $0 setup config /path/to/new-config-dir"
    echo ""
    echo "  # Validate hardware and configuration"
    echo "  $0 validate hardware --config=/path/to/config.yaml --inventory=/path/to/inventory.ini"
    echo "  $0 validate config --config=/path/to/config.yaml"
    echo ""
    echo "  # Complete stack deployment (recommended)"
    echo "  $0 stack deploy-complete --config=/path/to/config.yaml --inventory=/path/to/inventory.ini"
    echo ""
    echo "  # Manual step-by-step deployment"
    echo "  $0 setup configure --config=/path/to/config.yaml --inventory=/path/to/inventory.ini"
    echo "  $0 cluster deploy --config=/path/to/config.yaml --inventory=/path/to/inventory.ini"
    echo "  $0 cluster post-install --config=/path/to/config.yaml --inventory=/path/to/inventory.ini"
    echo "  $0 application install --config=/path/to/config.yaml --inventory=/path/to/inventory.ini"
    echo ""
    echo "  # Build and push custom images"
    echo "  $0 setup images --tag=custom_build --registry=your-registry.com"
    echo ""
    echo "  # Using environment variable for config directory:"
    echo "  export ERAG_CONFIG_DIR=/path/to/your/config-dir"
    echo "  $0 application install --config=\$ERAG_CONFIG_DIR/config.yaml --inventory=\$ERAG_CONFIG_DIR/inventory.ini"
    echo ""
}



VENV_NAME="erag-venv"
VENV_PATH="$SCRIPT_DIR/$VENV_NAME"

setup_initialize() {
    log "INFO" "Initializing Enterprise RAG virtual environment..."
    
    if ! python3 -m venv --help &> /dev/null; then
        log "WARN" "python3-venv module not found. Installing..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y python3-venv
        else
            log "ERROR" "This script is designed for Ubuntu/Debian systems. Please install python3-venv manually."
            return 1
        fi
    fi
    
    if [[ ! -d "$VENV_PATH" ]]; then
        log "INFO" "Creating virtual environment at: $VENV_PATH"
        python3 -m venv "$VENV_PATH"
        if [[ $? -ne 0 ]]; then
            log "ERROR" "Failed to create virtual environment"
            return 1
        fi
    else
        log "INFO" "Virtual environment already exists at: $VENV_PATH"
    fi
    
    log "INFO" "Installing packages into virtual environment..."
    # Use the venv's pip directly instead of sourcing
    "$VENV_PATH/bin/pip" install --upgrade pip
    
    local requirements_file="$SCRIPT_DIR/requirements.txt"
    if [[ -f "$requirements_file" ]]; then
        log "INFO" "Installing Python requirements (including Ansible)..."
        "$VENV_PATH/bin/pip" install -r "$requirements_file"
        if [[ $? -ne 0 ]]; then
            log "ERROR" "Failed to install Python requirements"
            return 1
        fi
    else
        log "WARN" "No requirements.txt found - installing Ansible directly"
        "$VENV_PATH/bin/pip" install ansible
    fi
    
    local requirements_yaml="$SCRIPT_DIR/requirements.yaml"
    if [[ -f "$requirements_yaml" ]]; then
        log "INFO" "Installing Ansible collections..."
        "$VENV_PATH/bin/ansible-galaxy" collection install -r "$requirements_yaml" --upgrade
        if [[ $? -ne 0 ]]; then
            log "ERROR" "Failed to install Ansible collections"
            return 1
        fi
    else
        log "WARN" "No requirements.yaml found"
    fi
    
    log "SUCCESS" "Virtual environment initialized successfully!"
    log "INFO" "Virtual environment path: $VENV_PATH"
    log "INFO" ""
    log "INFO" "To activate the virtual environment, run:"
    log "INFO" "    source $VENV_PATH/bin/activate"
    log "INFO" ""
    log "INFO" "When activated, you can run ansible commands directly or use the installer.sh"
    return 0
}

# Parse command-line options
parse_options() {
    PARSED_COMPONENT=""
    PARSED_ACTION=""
    PARSED_CONFIG_DIR="$DEFAULT_CONFIG"
    PARSED_CONFIG_FILE=""
    PARSED_CONFIG_EXPLICIT=false  # Track if --config was explicitly provided
    PARSED_INVENTORY_FILE=""
    PARSED_CUSTOM_TAG=""
    PARSED_CUSTOM_REGISTRY=""
    PARSED_NON_INTERACTIVE=false
    PARSED_VERBOSITY=""
    PARSED_EXTRA_ARGS=()
    
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    # First argument is component
    if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
        PARSED_COMPONENT="$1"
        shift
    fi
    
    # Second argument is action
    if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
        PARSED_ACTION="$1"
        shift
    fi
    
    # Parse remaining options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config=*)
                PARSED_CONFIG_FILE="${1#*=}"
                PARSED_CONFIG_EXPLICIT=true
                PARSED_CONFIG_DIR="$(dirname "$PARSED_CONFIG_FILE")"
                shift
                ;;
            --config)
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                    PARSED_CONFIG_FILE="$2"
                    PARSED_CONFIG_EXPLICIT=true
                    PARSED_CONFIG_DIR="$(dirname "$PARSED_CONFIG_FILE")"
                    shift 2
                else
                    log "ERROR" "Option --config requires a config file path"
                    exit 1
                fi
                ;;
            --inventory=*)
                PARSED_INVENTORY_FILE="${1#*=}"
                shift
                ;;
            --inventory)
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                    PARSED_INVENTORY_FILE="$2"
                    shift 2
                else
                    log "ERROR" "Option --inventory requires an inventory file path"
                    exit 1
                fi
                ;;
            --tag=*)
                PARSED_CUSTOM_TAG="${1#*=}"
                shift
                ;;
            --tag)
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                    PARSED_CUSTOM_TAG="$2"
                    shift 2
                else
                    log "ERROR" "Option --tag requires a tag value"
                    exit 1
                fi
                ;;
            --registry=*)
                PARSED_CUSTOM_REGISTRY="${1#*=}"
                shift
                ;;
            --registry)
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                    PARSED_CUSTOM_REGISTRY="$2"
                    shift 2
                else
                    log "ERROR" "Option --registry requires a registry URL"
                    exit 1
                fi
                ;;
            --non-interactive)
                PARSED_NON_INTERACTIVE=true
                shift
                ;;

            -v|-vv|-vvv)
                PARSED_VERBOSITY="$1"
                shift
                ;;
            -h|--help|help)
                show_help
                exit 0
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                echo ""
                show_help
                exit 1
                ;;
            *)
                # Collect remaining arguments for commands that need them (like setup config)
                PARSED_EXTRA_ARGS+=("$1")
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$PARSED_COMPONENT" ]]; then
        log "ERROR" "Component is required"
        echo ""
        show_help
        exit 1
    fi
    
    if [[ -z "$PARSED_ACTION" ]]; then
        log "ERROR" "Action is required"
        echo ""
        show_help
        exit 1
    fi
    
    # Export all parsed values
    export PARSED_CONFIG_DIR
    export PARSED_CONFIG_FILE
    export PARSED_INVENTORY_FILE
    export PARSED_CUSTOM_TAG
    export PARSED_CUSTOM_REGISTRY
    export PARSED_VERBOSITY
    export PARSED_COMPONENT
    export PARSED_ACTION
    export PARSED_NON_INTERACTIVE
    export PARSED_CONFIG_EXPLICIT

    # Handle config file path resolution
    if [[ -z "$PARSED_CONFIG_FILE" ]]; then
        # No --config file specified, use config.yaml from the config directory
        PARSED_CONFIG_FILE="$PARSED_CONFIG_DIR/config.yaml"
        export PARSED_CONFIG_FILE
    fi

    # Handle inventory file path resolution
    if [[ -z "$PARSED_INVENTORY_FILE" ]]; then
        # No --inventory file specified, use inventory.ini from the config directory
        PARSED_INVENTORY_FILE="$PARSED_CONFIG_DIR/inventory.ini"
        export PARSED_INVENTORY_FILE
    fi

    # Log configuration
    if [[ -n "$PARSED_CONFIG_FILE" && "$PARSED_CONFIG_DIR" == "$ERAG_CONFIG_DIR" && -n "$ERAG_CONFIG_DIR" ]]; then
        log "INFO" "Using config from ERAG_CONFIG_DIR directory: $PARSED_CONFIG_FILE"
    elif [[ -n "$PARSED_CONFIG_FILE" && "$PARSED_CONFIG_DIR" == "$DEFAULT_CONFIG" ]]; then
        log "INFO" "Using default config: $PARSED_CONFIG_FILE"
    elif [[ "$PARSED_CONFIG_EXPLICIT" == "true" ]]; then
        log "INFO" "Using config from --config flag: $PARSED_CONFIG_FILE"
    fi

    # Log inventory
    if [[ -n "$PARSED_INVENTORY_FILE" && "$PARSED_CONFIG_DIR" == "$ERAG_CONFIG_DIR" && -n "$ERAG_CONFIG_DIR" ]]; then
        log "INFO" "Using inventory from ERAG_CONFIG_DIR directory: $PARSED_INVENTORY_FILE"
    elif [[ -n "$PARSED_INVENTORY_FILE" && "$PARSED_CONFIG_DIR" == "$DEFAULT_CONFIG" ]]; then
        log "INFO" "Using default inventory: $PARSED_INVENTORY_FILE"
    elif [[ -n "$PARSED_INVENTORY_FILE" ]]; then
        log "INFO" "Using inventory from --inventory flag: $PARSED_INVENTORY_FILE"
    fi

    if [[ -n "$PARSED_CUSTOM_TAG" ]]; then
        log "INFO" "Using custom tag: $PARSED_CUSTOM_TAG"
    fi
    if [[ -n "$PARSED_CUSTOM_REGISTRY" ]]; then
        log "INFO" "Using custom registry: $PARSED_CUSTOM_REGISTRY"
    fi
}

# Build and update container images
build_and_update_images() {
    log "INFO" "Building and updating container images..."
    
    if [[ ! -x "$SCRIPT_DIR/update_images.sh" ]]; then
        log "ERROR" "update_images.sh script not found or not executable"
        log "INFO" "Expected location: $SCRIPT_DIR/update_images.sh"
        exit 1
    fi
    
    # Build script arguments
    local script_args=()
    
    # Add registry if specified
    if [[ -n "$PARSED_CUSTOM_REGISTRY" ]]; then
        script_args+=("--registry" "$PARSED_CUSTOM_REGISTRY")
        log "INFO" "Using custom registry: $PARSED_CUSTOM_REGISTRY"
    fi
    
    # Add tag if specified
    if [[ -n "$PARSED_CUSTOM_TAG" ]]; then
        script_args+=("--tag" "$PARSED_CUSTOM_TAG")
        log "INFO" "Using custom tag: $PARSED_CUSTOM_TAG"
    fi
    
    # Execute the script with arguments
    cd "$SCRIPT_DIR"
    if ./update_images.sh --build --push "${script_args[@]}"; then
        log "SUCCESS" "Container images updated successfully"
    else
        log "ERROR" "Image update failed"
        exit 1
    fi
}

# Run an Ansible playbook
run_ansible_playbook() {
    local playbook=$1
    local tags=$2
    local config_dir=${3:-$PARSED_CONFIG_DIR}
    local need_become=${4:-false}
    local extra_args=${5:-""}

    # Determine config file path
    local config_file
    if [[ -n "$PARSED_CONFIG_FILE" ]]; then
        config_file="$PARSED_CONFIG_FILE"
    else
        config_file="$config_dir/config.yaml"
    fi

    if [ ! -f "$config_file" ]; then
        log "ERROR" "Config file not found at $config_file"
        return 1
    fi

    log "INFO" "Running Ansible playbook: $playbook with tags: $tags"
    log "INFO" "Using config from $config_file"

    local become_flag=""
    if [ "$need_become" = true ]; then
        become_flag="--become"
        log "INFO" "This operation requires sudo privileges (passwordless sudo required)"
    fi

    # Always use inventory file
    local inventory_flag=""
    local inventory_file
    
    if [[ -n "$PARSED_INVENTORY_FILE" ]]; then
        inventory_file="$PARSED_INVENTORY_FILE"
    else
        inventory_file="$config_dir/inventory.ini"
    fi
    
    if [ -f "$inventory_file" ]; then
        inventory_flag="-i $inventory_file"
        log "INFO" "Using inventory file: $inventory_file"
    else
        log "ERROR" "Inventory file not found at $inventory_file - exiting"
        exit 1
    fi

    if [ -n "$PARSED_CUSTOM_TAG" ]; then
        extra_args+=" -e tag=$PARSED_CUSTOM_TAG"
    fi
    if [ -n "$PARSED_CUSTOM_REGISTRY" ]; then
        extra_args+=" -e registry=$PARSED_CUSTOM_REGISTRY"
    fi

    # Use virtual environment ansible-playbook if available, otherwise use system ansible
    local ansible_cmd="ansible-playbook"
    if [ -f "$VENV_PATH/bin/ansible-playbook" ]; then
        ansible_cmd="$VENV_PATH/bin/ansible-playbook"
        log "DEBUG" "Using virtual environment ansible-playbook: $ansible_cmd"
    else
        log "WARNING" "Virtual environment not found, using system ansible-playbook"
        log "INFO" "For better isolation, create venv with: $0 setup python-env"
        log "INFO" "Then activate it with: source $VENV_PATH/bin/activate"
    fi
    
    local cmd="$ansible_cmd -u $USER $become_flag $inventory_flag $SCRIPT_DIR/playbooks/$playbook.yaml --tags $tags -e @$config_file $PARSED_VERBOSITY $extra_args"
    
    log "INFO" "Command: $cmd"

    eval "$cmd"
    local result=$?

    if [ $result -eq 0 ]; then
        log "SUCCESS" "Playbook execution completed successfully."
    else
        log "ERROR" "Playbook execution failed with exit code $result."
    fi

    return $result
}

# Interactive configuration setup
setup_interactive_config() {
    local config_dir=${1:-$PARSED_CONFIG_DIR}
    local use_defaults=${2:-false}
    
    log "INFO" "Setting up interactive configuration for Enterprise RAG"
    
    if [ ! -d "$config_dir" ]; then
        log "INFO" "Creating configuration directory: $config_dir"
        mkdir -p "$config_dir"
    else
        log "ERROR" "This configuration directory already exists: $config_dir"
        exit 1
    fi

    # Skip interactive input if default config is requested
    if [ "$use_defaults" = true ]; then
        log "INFO" "Using default configuration without interactive prompts"
        # Copy sample configuration (config.yaml is always from sample)
        if [ ! -f "$config_dir/config.yaml" ]; then
            log "INFO" "Copying sample configuration to $config_dir"
            cp "$CONFIG_DIR/sample/config.yaml" "$config_dir/"
            cp "$CONFIG_DIR/sample/inventory.ini" "$config_dir/"
        fi
        log "WARN" "Please manually edit $config_dir/config.yaml before deployment"
        return 0
    fi

    # Interactive inventory type selection
    log "INFO" "Starting interactive configuration setup..."
    echo ""
    echo -e "${BLUE}=== Inventory Type Selection ===${NC}"
    echo "Choose inventory type for your deployment:"
    echo "  1) localhost  - Deploy applications on existing Kubernetes cluster (localhost only)"
    echo "  2) sample     - Multi-node cluster deployment with sample inventory"
    echo ""
    echo -n "Select inventory type (1 or 2) [1]: "
    read -r inventory_choice
    inventory_choice=${inventory_choice:-1}
    
    local inventory_type
    if [[ "$inventory_choice" == "1" ]]; then
        inventory_type="localhost"
        log "INFO" "Selected localhost inventory"
    elif [[ "$inventory_choice" == "2" ]]; then
        inventory_type="sample"
        log "INFO" "Selected sample inventory for multi-node cluster"
    else
        log "ERROR" "Invalid selection. Please choose 1 or 2"
        exit 1
    fi
    
    # Copy configuration files - config.yaml is always from sample, inventory.ini from selected type
    if [ ! -f "$config_dir/config.yaml" ]; then
        log "INFO" "Copying configuration files to $config_dir"
        log "INFO" "Using config.yaml from sample (shared across all deployments)"
        cp "$CONFIG_DIR/sample/config.yaml" "$config_dir/"
        log "INFO" "Using inventory.ini from $inventory_type"
        cp "$CONFIG_DIR/$inventory_type/inventory.ini" "$config_dir/"
    fi

    log "INFO" "Press Enter to keep current values, or type new values"
    
    # Log environment variable usage
    if [[ -n "$HF_TOKEN" ]]; then
        log "INFO" "Using HF_TOKEN environment variable for Hugging Face token"
    fi
    if [[ -n "$KUBECONFIG" ]]; then
        log "INFO" "Using KUBECONFIG environment variable: $KUBECONFIG"
    fi
    if [[ -n "${http_proxy:-${HTTP_PROXY:-}}" ]]; then
        log "INFO" "Using proxy environment variables"
    fi
    
    echo ""

    # Set defaults from environment variables
    local default_hf_token="${HF_TOKEN:-}"
    local default_kubeconfig="${KUBECONFIG:-$HOME/.kube/config}"
    local default_deploy_k8s="true"
    local default_fqdn="erag.com"
    local default_http_proxy="${http_proxy:-${HTTP_PROXY:-}}"
    local default_https_proxy="${https_proxy:-${HTTPS_PROXY:-}}"
    local default_no_proxy="${no_proxy:-${NO_PROXY:-}}"

    # Interactive prompts
    echo -e "${BLUE}=== Basic Configuration ===${NC}"
    
    # Hugging Face Token
    echo -n "Hugging Face Token (required for gated model downloads) [$default_hf_token]: "
    read -r hf_token
    hf_token=${hf_token:-$default_hf_token}

    # FQDN
    echo -n "FQDN (Fully Qualified Domain Name for deployment) [$default_fqdn]: "
    read -r fqdn
    fqdn=${fqdn:-$default_fqdn}

    # Deploy Kubernetes cluster
    echo -n "Deploy new Kubernetes cluster? (true/false) [$default_deploy_k8s]: "
    read -r deploy_k8s
    deploy_k8s=${deploy_k8s:-$default_deploy_k8s}

    # Conditional prompts based on deploy_k8s choice
    if [[ "$deploy_k8s" == "true" ]]; then
        # Set default kubeconfig for new cluster deployment
        kubeconfig_path="$(cd "$config_dir" && pwd)/artifacts/admin.conf"
        log "INFO" "Using kubeconfig for deployed cluster: $kubeconfig_path"
    else
        # Handle existing cluster kubeconfig
        if [[ -n "$KUBECONFIG" ]]; then
            log "INFO" "KUBECONFIG environment variable is set - will be used for further actions"
            kubeconfig_path="# KUBECONFIG environment variable will be used: $KUBECONFIG"
        else
            # Kubeconfig path - only ask when using existing cluster and no KUBECONFIG env
            echo -n "Kubeconfig file path [$default_kubeconfig]: "
            read -r kubeconfig_path
            kubeconfig_path=${kubeconfig_path:-$default_kubeconfig}
            
            # Expand tilde in path
            kubeconfig_path="${kubeconfig_path/#\~/$HOME}"
        fi
    fi

    echo ""
    echo -e "${BLUE}=== Advanced Configuration (Optional) ===${NC}"

    # HTTP Proxy settings
    echo -n "HTTP Proxy [$default_http_proxy]: "
    read -r http_proxy
    http_proxy=${http_proxy:-$default_http_proxy}
    
    echo -n "HTTPS Proxy [$default_https_proxy]: "
    read -r https_proxy
    https_proxy=${https_proxy:-$default_https_proxy}

    echo -n "Additional No Proxy entries (common entries added automatically) [$default_no_proxy]: "
    read -r additional_no_proxy
    additional_no_proxy=${additional_no_proxy:-$default_no_proxy}

    # Apply configuration changes
    log "INFO" "Applying configuration changes..."

    # Update config.yaml with new values
    sed -i "s|^huggingToken:.*|huggingToken: \"$hf_token\"|" "$config_dir/config.yaml"
    sed -i "s|^FQDN:.*|FQDN: \"$fqdn\"|" "$config_dir/config.yaml"
    
    # Handle kubeconfig - comment out if using environment variable
    if [[ "$kubeconfig_path" == "# KUBECONFIG environment variable will be used:"* ]]; then
        sed -i "s|^kubeconfig:.*|$kubeconfig_path|" "$config_dir/config.yaml"
    else
        sed -i "s|^kubeconfig:.*|kubeconfig: \"$kubeconfig_path\"|" "$config_dir/config.yaml"
    fi
    
    sed -i "s|^deploy_k8s:.*|deploy_k8s: $deploy_k8s|" "$config_dir/config.yaml"

    if [[ -n "$http_proxy" ]]; then
        sed -i "s|^httpProxy:.*|httpProxy: \"$http_proxy\"|" "$config_dir/config.yaml"
    fi
    if [[ -n "$https_proxy" ]]; then
        sed -i "s|^httpsProxy:.*|httpsProxy: \"$https_proxy\"|" "$config_dir/config.yaml"
    fi

    if [[ -n "$additional_no_proxy" ]]; then
        sed -i "s|^additionalNoProxy:.*|additionalNoProxy: \"$additional_no_proxy\"|" "$config_dir/config.yaml"
    fi

    # Validate critical settings
    if [[ -z "$hf_token" ]]; then
        log "WARN" "Hugging Face token is required for downloading gated models"
        log "WARN" "If needed, please set it manually in $config_dir/config.yaml"
    fi

    # Skip kubeconfig file validation if using environment variable or deploying new cluster
    if [[ "$kubeconfig_path" == "# KUBECONFIG environment variable will be used:"* ]]; then
        log "INFO" "Using KUBECONFIG environment variable for cluster access"
    elif [[ ! -f "$kubeconfig_path" && "$deploy_k8s" != "true" ]]; then
        log "WARN" "Kubeconfig file not found at: $kubeconfig_path"
        log "WARN" "Make sure the path is correct or set deploy_k8s to true"
    fi

    log "SUCCESS" "Configuration updated successfully!"
    log "INFO" "Configuration file: $(realpath "$config_dir/config.yaml")"
    log "INFO" "Inventory file: $(realpath "$config_dir/inventory.ini")"
    
    echo ""
    echo -e "${GREEN}Configuration Summary:${NC}"
    echo "  Hugging Face Token: $([ -n "$hf_token" ] && echo "✓ Set" || echo "✗ Not set")"
    echo "  FQDN: $fqdn"
    if [[ "$kubeconfig_path" == "# KUBECONFIG environment variable will be used:"* ]]; then
        if [[ -n "$KUBECONFIG" ]]; then
            echo "  Kubeconfig: Using KUBECONFIG environment variable ($KUBECONFIG)"
        else
            echo "  Kubeconfig: Using KUBECONFIG environment variable (currently not set)"
        fi
    else
        echo "  Kubeconfig: $kubeconfig_path"
    fi
    echo "  Deploy K8s: $deploy_k8s"
    if [[ -n "$http_proxy" ]]; then
        echo "  HTTP Proxy: $http_proxy"
    fi
    if [[ -n "$https_proxy" ]]; then
        echo "  HTTPS Proxy: $https_proxy"
    fi
    if [[ -n "$additional_no_proxy" ]]; then
        echo "  Additional No Proxy: $additional_no_proxy"
    fi
    echo ""

}

# Deploy complete Enterprise RAG stack
deploy_complete_stack() {
    local config_dir=${1:-$PARSED_CONFIG_DIR}
    local start_time
    start_time=$(date +%s)
    
    log "INFO" "=== Starting Complete Enterprise RAG Stack Deployment ==="
    log "INFO" "This comprehensive deployment includes:"
    log "INFO" "  • Python virtual environment setup"
    log "INFO" "  • System dependencies and tools configuration"
    log "INFO" "  • Kubernetes cluster deployment"
    log "INFO" "  • Enterprise RAG application deployment"
    log "INFO" "Prerequisites: config.yaml and inventory file must be provided"
    echo ""
    
    # Initialize virtual environment
    log "INFO" "Step 1/4: Initializing Python virtual environment..."
    if [[ -d "$VENV_PATH" ]]; then
        log "INFO" "Virtual environment already exists at: $VENV_PATH - skipping initialization"
    else
        if ! setup_initialize; then
            log "ERROR" "Failed to initialize Python virtual environment"
            exit 1
        fi
    fi
    log "SUCCESS" "Virtual environment ready"
    echo ""
    
    # Validate configuration
    log "INFO" "Step 2/4: Configure machine to prepare for deployment..."
    if ! run_ansible_playbook "setup" "configure" "$config_dir" true ""; then
        log "ERROR" "Configuration failed"
        exit 1
    fi
    log "SUCCESS" "Configuration setup completed"
    echo ""


    log "INFO" "Step 3/4: Deploying Kubernetes cluster..."
    if ! run_ansible_playbook "infrastructure" "install" "$config_dir" true "-e deploy_k8s=true"; then
        log "ERROR" "Kubernetes cluster deployment failed"
        exit 1
    fi
    log "SUCCESS" "Kubernetes cluster deployment completed"
    echo ""

    # Deploy Enterprise RAG application
    log "INFO" "Step 4/4: Deploying Enterprise RAG application stack..."
    if ! run_ansible_playbook "application" "install" "$config_dir" false ""; then
        log "ERROR" "Enterprise RAG application deployment failed"
        exit 1
    fi
    log "SUCCESS" "Enterprise RAG application deployment completed"
    echo ""

    # Calculate deployment time
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))

    # Deployment summary
    log "SUCCESS" "=== Enterprise RAG Stack Deployment Completed Successfully! ==="
    echo ""
    echo -e "${GREEN}Deployment Summary:${NC}"
    echo "  ✓ System prerequisites validated"
    echo "  ✓ Configuration setup completed"
    echo "  ✓ Kubernetes cluster deployed"
    echo "  ✓ Post-installation tasks completed"
    echo "  ✓ Enterprise RAG application deployed"
    echo ""
    printf "  ${GREEN}Total deployment time: "
    if [[ $hours -gt 0 ]]; then
        printf "%dh " $hours
    fi
    if [[ $minutes -gt 0 ]]; then
        printf "%dm " $minutes
    fi
    printf "%ds${NC}\n" $seconds
    echo ""
    
    # Access information
    log "INFO" "=== Access Information ==="
    log "INFO" "Configuration files:"
    log "INFO" "  • Config: $(realpath "$config_dir/config.yaml")"
    log "INFO" "  • Inventory: $(realpath "$config_dir/inventory.ini")"
    echo ""
    log "INFO" "Next steps:"
    log "INFO" "  1. Check application logs and access information"
    log "INFO" "  2. Access the web interface and start using Enterprise RAG"
    echo ""
    log "SUCCESS" "Your Enterprise RAG solution is ready for use!"
}

# Delete complete Enterprise RAG stack
delete_complete_stack() {
    local config_dir=${1:-$PARSED_CONFIG_DIR}
    local start_time
    start_time=$(date +%s)
    
    log "WARN" "=== Starting Complete Enterprise RAG Stack Deletion ==="
    log "WARN" "This will completely remove:"
    log "WARN" "  • Enterprise RAG applications and data"
    log "WARN" "  • Monitoring and observability stack"
    log "WARN" "  • Kubernetes cluster (if deployed by this tool)"
    log "WARN" "  • All persistent volumes and data"
    echo ""
    
    # Confirmation prompt
    echo -e "${RED}WARNING: This operation is DESTRUCTIVE and IRREVERSIBLE!${NC}"
    echo -e "${RED}All Enterprise RAG data, configurations, and deployed resources will be permanently deleted.${NC}"
    echo ""
    echo -n "Are you absolutely sure you want to proceed? Type 'DELETE' to confirm: "
    read -r confirmation
    
    if [[ "$confirmation" != "DELETE" ]]; then
        log "INFO" "Deletion cancelled by user"
        exit 0
    fi
    
    echo ""
    log "WARN" "Starting deletion process in 5 seconds... Press Ctrl+C to abort"
    sleep 5
    
    # Initialize virtual environment
    log "INFO" "Initializing Python virtual environment..."
    if [[ -d "$VENV_PATH" ]]; then
        log "INFO" "Virtual environment already exists at: $VENV_PATH - skipping initialization"
    else
        if ! setup_initialize; then
            log "ERROR" "Failed to initialize Python virtual environment"
            exit 1
        fi
    fi
    log "SUCCESS" "Virtual environment ready"
    echo ""
    
    # Validate configuration exists
    if [[ ! -f "$config_dir/config.yaml" ]]; then
        log "ERROR" "Configuration file not found at $config_dir/config.yaml"
        log "ERROR" "Cannot proceed with deletion without configuration"
        exit 1
    fi
    
    # Step 1: Uninstall Enterprise RAG application
    log "INFO" "Step 1/3: Uninstalling Enterprise RAG application..."
    if ! run_ansible_playbook "application" "uninstall" "$config_dir" false ""; then
        log "WARN" "Some issues occurred during application uninstall, continuing..."
    else
        log "SUCCESS" "Enterprise RAG application uninstalled"
    fi
    echo ""
    
    # Force deploy_k8s=true for complete stack deletion
    local deploy_k8s="true"
    log "INFO" "Stack deletion always includes Kubernetes cluster (deploy_k8s=true)"
    
    if [[ "$deploy_k8s" == "true" ]]; then
        log "INFO" "Step 2/3: Deleting Kubernetes cluster..."
        if ! run_ansible_playbook "infrastructure" "delete" "$config_dir" true "-e deploy_k8s=true"; then
            log "ERROR" "Some issues occurred during cluster deletion, exiting..."
            exit 1
        fi
        log "SUCCESS" "Kubernetes cluster deleted"
        echo ""
        
        log "INFO" "Step 3/3: Cleaning up remaining resources..."
        # Remove configuration directory and its contents
        if [[ -d "$config_dir" ]]; then
            echo -e "${YELLOW}Do you want to delete the configuration directory: $config_dir? (yes/no)${NC}"
            echo -n "Answer: "
            read -r delete_config_confirm
            
            if [[ "$delete_config_confirm" == "yes" || "$delete_config_confirm" == "y" ]]; then
                log "INFO" "Removing configuration directory: $config_dir"
                rm -rf "$config_dir" 2>/dev/null || {
                    log "WARN" "Could not remove config directory $config_dir - you may need to remove it manually"
                }
                log "SUCCESS" "Configuration directory removed"
            else
                log "INFO" "Configuration directory preserved at: $config_dir"
            fi
        fi

        log "SUCCESS" "Cleanup completed"
    fi
    echo ""
    
    # Calculate deletion time
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    # Deletion summary with actual status
    log "SUCCESS" "=== Enterprise RAG Stack Deletion Completed ==="
    echo ""
    printf "  ${GREEN}Total deletion time: "
    if [[ $hours -gt 0 ]]; then
        printf "%dh " $hours
    fi
    if [[ $minutes -gt 0 ]]; then
        printf "%dm " $minutes
    fi
    printf "%ds${NC}\n" $seconds
    echo ""
}

# Prepare the configuration
# Main function to process commands
main() {
    # Parse all command-line options first
    parse_options "$@"

    # Check virtual environment status
    if [[ -d "$VENV_PATH" ]]; then
        log "INFO" "Enterprise RAG virtual environment found at: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
    else
        log "WARN" "No Enterprise RAG virtual environment found"
        log "INFO" "To create and install packages: $0 setup python-env"
    fi

    # Process commands based on component and action
    case "$PARSED_COMPONENT" in
        "setup")
            case "$PARSED_ACTION" in
                "python-env")
                    setup_initialize
                    ;;
                "configure")
                    log "INFO" "You will be asked for sudo password for localhost to install required tools."
                    run_ansible_playbook "setup" "configure" "$PARSED_CONFIG_DIR" true ""
                    ;;
                "images")
                    build_and_update_images
                    ;;
                "config")
                    # setup config creates NEW configuration in a directory
                    # Takes directory as positional argument: setup config /path/to/dir
                    local target_dir
                    
                    if [[ "$PARSED_CONFIG_EXPLICIT" == "true" ]]; then
                        log "ERROR" "setup config should not use --config flag (that's for existing configs)"
                        log "INFO" "Use: $0 setup config /path/to/new-directory"
                        log "INFO" "The --config flag is for referencing existing configurations"
                        exit 1
                    fi
                    
                    # Get target directory from positional argument or use default
                    if [[ ${#PARSED_EXTRA_ARGS[@]} -gt 0 ]]; then
                        target_dir="${PARSED_EXTRA_ARGS[0]}"
                        log "INFO" "Creating new configuration in: $target_dir"
                    else
                        # Use default/environment variable
                        target_dir="$PARSED_CONFIG_DIR"
                        log "INFO" "No directory specified, using default: $target_dir"
                        log "INFO" "To specify custom directory: $0 setup config /path/to/directory"
                    fi
                    
                    setup_interactive_config "$target_dir" "$PARSED_NON_INTERACTIVE"
                    ;;
                "info")
                    check_venv
                    ;;
                *)
                    log "ERROR" "Unknown action for setup: $PARSED_ACTION"
                    log "INFO" "Available actions: python-env, configure, images, config, info"
                    exit 1
                    ;;
            esac
            ;;
        "cluster")
            case "$PARSED_ACTION" in
                "deploy")
                    run_ansible_playbook "infrastructure" "install" "$PARSED_CONFIG_DIR" true "-e deploy_k8s=true"
                    ;;
                "post-install")
                    run_ansible_playbook "infrastructure" "post-install" "$PARSED_CONFIG_DIR" true "-e deploy_k8s=false"
                    ;;
                "delete")
                    run_ansible_playbook "infrastructure" "delete" "$PARSED_CONFIG_DIR" true "-e deploy_k8s=true"
                    ;;
                *)
                    log "ERROR" "Unknown action for cluster: $PARSED_ACTION"
                    log "INFO" "Available actions: deploy, post-install, delete"
                    exit 1
                    ;;
            esac
            ;;
        "application")
            case "$PARSED_ACTION" in
                "install")
                    run_ansible_playbook "application" "install" "$PARSED_CONFIG_DIR" false ""
                    ;;
                "uninstall")
                    run_ansible_playbook "application" "uninstall" "$PARSED_CONFIG_DIR" false ""
                    ;;
                "show-config")
                    log "INFO" "Displaying configuration and validation status..."
                    run_ansible_playbook "application" "display-configuration" "$PARSED_CONFIG_DIR" false ""
                    ;;
                *)
                    log "ERROR" "Unknown action for application: $PARSED_ACTION"
                    log "INFO" "Available actions: install, uninstall, show-config"
                    exit 1
                    ;;
            esac
            ;;
        "validate")
            case "$PARSED_ACTION" in
                "config")
                    run_ansible_playbook "validate" "config" "$PARSED_CONFIG_DIR" false ""
                    ;;
                "hardware")
                    run_ansible_playbook "validate" "hardware" "$PARSED_CONFIG_DIR" true ""
                    ;;
                *)
                    log "ERROR" "Unknown action for validate: $PARSED_ACTION"
                    log "INFO" "Available actions: config, hardware"
                    exit 1
                    ;;
            esac
            ;;
        "stack")
            case "$PARSED_ACTION" in
                "deploy-complete")
                    deploy_complete_stack "$PARSED_CONFIG_DIR"
                    ;;
                "delete-complete")
                    delete_complete_stack "$PARSED_CONFIG_DIR"
                    ;;
                *)
                    log "ERROR" "Unknown action for stack: $PARSED_ACTION"
                    log "INFO" "Available actions: deploy-complete, delete-complete"
                    exit 1
                    ;;
            esac
            ;;
        *)
            log "ERROR" "Unknown component: $PARSED_COMPONENT"
            log "INFO" "Available components: setup, cluster, application, validate, stack"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
