#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# EXPERIMENTAL FEATURE
# This completion script is currently an experimental feature and may undergo
# significant changes. Use with caution in production environments.

# Bash completion script for installer.sh
# Location: deployment/scripts/installer-completion.bash
#
# To enable, source this file or add it to your bash completion directory:
#   source scripts/installer-completion.bash
# Or system-wide:
#   sudo cp scripts/installer-completion.bash /etc/bash_completion.d/installer
#
# For detailed installation instructions, see: COMPLETION.md

_installer_completion() {
    local cur prev words cword
    _init_completion || return

    # Get the script directory to find config/inventory files
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Components
    local components="setup validate cluster application stack"
    
    # Actions per component
    local setup_actions="python-env configure images config info"
    local validate_actions="config hardware"
    local cluster_actions="deploy post-install delete"
    local application_actions="install uninstall show-config"
    local stack_actions="deploy-complete delete-complete"
    
    # Options
    local options="--config --inventory --tag --registry --non-interactive -v -vv -vvv -h --help"

    # Get component and action from the command line
    local component=""
    local action=""
    local i
    for ((i=1; i < ${#words[@]}; i++)); do
        case "${words[i]}" in
            --*|-*)
                # Skip options
                continue
                ;;
            *)
                if [[ -z "$component" ]]; then
                    component="${words[i]}"
                elif [[ -z "$action" ]]; then
                    action="${words[i]}"
                    break
                fi
                ;;
        esac
    done

    # Determine what to complete based on position and previous word
    case "$prev" in
        --config|--config=*)
            # Complete with .yaml files
            if [[ "$cur" == *"/"* ]]; then
                _filedir yaml
            else
                # Suggest common config locations
                local config_suggestions="inventory/sample/config.yaml"
                # Add suggestions for custom config directories
                [[ -d "inventory/cluster" ]] && config_suggestions+=" inventory/cluster/config.yaml"
                [[ -d "inventory/prod" ]] && config_suggestions+=" inventory/prod/config.yaml"
                [[ -d "inventory/dev" ]] && config_suggestions+=" inventory/dev/config.yaml"
                [[ -d "inventory/test" ]] && config_suggestions+=" inventory/test/config.yaml"
                COMPREPLY=( $(compgen -W "$config_suggestions" -- "$cur") )
                _filedir yaml
            fi
            return 0
            ;;
        --inventory|--inventory=*)
            # Complete with .ini files
            if [[ "$cur" == *"/"* ]]; then
                _filedir ini
            else
                # Suggest common inventory locations
                local inventory_suggestions="inventory/sample/inventory.ini inventory/localhost/inventory.ini"
                # Add suggestions for custom inventory directories
                [[ -d "inventory/cluster" ]] && inventory_suggestions+=" inventory/cluster/inventory.ini"
                [[ -d "inventory/prod" ]] && inventory_suggestions+=" inventory/prod/inventory.ini"
                [[ -d "inventory/dev" ]] && inventory_suggestions+=" inventory/dev/inventory.ini"
                [[ -d "inventory/test" ]] && inventory_suggestions+=" inventory/test/inventory.ini"
                COMPREPLY=( $(compgen -W "$inventory_suggestions" -- "$cur") )
                _filedir ini
            fi
            return 0
            ;;
        --tag|--tag=*)
            # Complete with common tags
            COMPREPLY=( $(compgen -W "latest v1.5.0 v1.4.0 v1.3.0 custom dev" -- "$cur") )
            return 0
            ;;
        --registry|--registry=*)
            # Complete with common registries
            COMPREPLY=( $(compgen -W "docker.io/opea localhost:5000 localhost:32000 ghcr.io quay.io" -- "$cur") )
            return 0
            ;;
        config)
            # For 'setup config', complete with directory paths
            if [[ "$component" == "setup" && "$action" == "config" ]]; then
                # Suggest common configuration directory names
                local dir_suggestions="inventory/cluster inventory/prod inventory/dev inventory/test"
                COMPREPLY=( $(compgen -W "$dir_suggestions" -- "$cur") )
                _filedir -d
                return 0
            fi
            ;;
    esac

    # Handle --option=value format
    if [[ "$cur" == --*=* ]]; then
        local opt="${cur%%=*}"
        local val="${cur#*=}"
        case "$opt" in
            --config)
                local config_suggestions="inventory/sample/config.yaml"
                [[ -d "inventory/cluster" ]] && config_suggestions+=" inventory/cluster/config.yaml"
                [[ -d "inventory/prod" ]] && config_suggestions+=" inventory/prod/config.yaml"
                [[ -d "inventory/dev" ]] && config_suggestions+=" inventory/dev/config.yaml"
                [[ -d "inventory/test" ]] && config_suggestions+=" inventory/test/config.yaml"
                COMPREPLY=( $(compgen -W "$config_suggestions" -- "$val") )
                compopt -o nospace
                _filedir yaml
                return 0
                ;;
            --inventory)
                local inventory_suggestions="inventory/sample/inventory.ini inventory/localhost/inventory.ini"
                [[ -d "inventory/cluster" ]] && inventory_suggestions+=" inventory/cluster/inventory.ini"
                [[ -d "inventory/prod" ]] && inventory_suggestions+=" inventory/prod/inventory.ini"
                [[ -d "inventory/dev" ]] && inventory_suggestions+=" inventory/dev/inventory.ini"
                [[ -d "inventory/test" ]] && inventory_suggestions+=" inventory/test/inventory.ini"
                COMPREPLY=( $(compgen -W "$inventory_suggestions" -- "$val") )
                compopt -o nospace
                _filedir ini
                return 0
                ;;
            --tag)
                COMPREPLY=( $(compgen -W "latest v1.5.0 v1.4.0 v1.3.0 custom dev" -- "$val") )
                return 0
                ;;
            --registry)
                COMPREPLY=( $(compgen -W "docker.io/opea localhost:5000 localhost:32000 ghcr.io quay.io" -- "$val") )
                return 0
                ;;
        esac
    fi

    # If no component yet, suggest components ONLY (no options)
    if [[ -z "$component" ]]; then
        COMPREPLY=( $(compgen -W "$components" -- "$cur") )
        return 0
    fi

    # If component is set but no action, suggest actions for that component ONLY (no options yet)
    if [[ -z "$action" ]]; then
        case "$component" in
            setup)
                COMPREPLY=( $(compgen -W "$setup_actions" -- "$cur") )
                ;;
            validate)
                COMPREPLY=( $(compgen -W "$validate_actions" -- "$cur") )
                ;;
            cluster)
                COMPREPLY=( $(compgen -W "$cluster_actions" -- "$cur") )
                ;;
            application)
                COMPREPLY=( $(compgen -W "$application_actions" -- "$cur") )
                ;;
            stack)
                COMPREPLY=( $(compgen -W "$stack_actions" -- "$cur") )
                ;;
            *)
                # Unknown component, don't suggest anything
                return 0
                ;;
        esac
        return 0
    fi

    # If both component and action are set, NOW suggest options (only when user types --)
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$options" -- "$cur") )
    else
        # For certain actions, suggest additional arguments
        if [[ "$component" == "setup" && "$action" == "config" ]]; then
            # Suggest directory names for 'setup config'
            local dir_suggestions="inventory/cluster inventory/prod inventory/dev inventory/test"
            COMPREPLY=( $(compgen -W "$dir_suggestions" -- "$cur") )
            _filedir -d
        fi
    fi
    return 0
}

# Register the completion function
complete -F _installer_completion installer.sh
complete -F _installer_completion ./installer.sh
