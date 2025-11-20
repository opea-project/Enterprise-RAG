#compdef installer.sh ./installer.sh

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# EXPERIMENTAL FEATURE
# This completion script is currently an experimental feature and may undergo
# significant changes. Use with caution in production environments.

# Zsh completion script for installer.sh
# Location: deployment/scripts/_installer.sh
#
# Quick start (temporary, current session only):
#   source scripts/_installer.sh
#   compdef _installer_sh installer.sh
#   compdef _installer_sh ./installer.sh
#
# Permanent installation - copy to fpath:
#   mkdir -p ~/.zsh/completion
#   cp scripts/_installer.sh ~/.zsh/completion/
#   Add to ~/.zshrc: fpath=(~/.zsh/completion $fpath)
#   Then run: autoload -Uz compinit && compinit
#
# For detailed installation instructions, see: COMPLETION.md

_installer_sh() {
    local curcontext="$curcontext" state line ret=1
    typeset -A opt_args
    local component action

    # Define common options that apply after component and action
    local -a common_opts
    common_opts=(
        '--config=[Path to config.yaml file]:config file:_files -g "*.yaml"'
        '--inventory=[Path to inventory file]:inventory file:_files -g "*.ini"'
        '--tag=[Docker image tag]:tag:(latest v1.5.0 v1.4.0 v1.3.0 custom dev)'
        '--registry=[Docker registry URL]:registry:(docker.io/opea localhost:5000 localhost:32000 ghcr.io quay.io)'
        '--non-interactive[Run without prompts]'
        '(-v -vv -vvv)-v[Verbose output]'
        '(-v -vv -vvv)-vv[More verbose output]'
        '(-v -vv -vvv)-vvv[Maximum verbosity]'
        '(- *)'{-h,--help}'[Show help message]'
    )

    # Parse based on position
    _arguments -C \
        '1: :->component' \
        '2: :->action' \
        '*::arg:->args' \
        && ret=0
    
    # Extract component and action from words array
    [[ -n ${words[2]} ]] && component=${words[2]}
    [[ -n ${words[3]} ]] && action=${words[3]}

    case $state in
        component)
            local -a components
            components=(
                'setup:Setup and configuration'
                'validate:Validation operations'
                'cluster:Kubernetes cluster operations'
                'application:Application operations'
                'stack:Complete stack operations'
            )
            _describe -t commands 'component' components && ret=0
            ;;
        action)
            case $component in
                setup)
                    local -a setup_actions
                    setup_actions=(
                        'python-env:Initialize Python virtual environment'
                        'configure:Configure deployment environment'
                        'images:Build and push application images'
                        'config:Generate configuration files interactively'
                        'info:Display virtual environment status'
                    )
                    _describe -t commands 'setup actions' setup_actions && ret=0
                    ;;
                validate)
                    local -a validate_actions
                    validate_actions=(
                        'config:Validate configuration'
                        'hardware:Validate hardware requirements'
                    )
                    _describe -t commands 'validate actions' validate_actions && ret=0
                    ;;
                cluster)
                    local -a cluster_actions
                    cluster_actions=(
                        'deploy:Deploy Kubernetes cluster'
                        'post-install:Post-installation tasks'
                        'delete:Delete Kubernetes cluster'
                    )
                    _describe -t commands 'cluster actions' cluster_actions && ret=0
                    ;;
                application)
                    local -a application_actions
                    application_actions=(
                        'install:Install the application'
                        'uninstall:Uninstall the application'
                        'show-config:Display current configuration'
                    )
                    _describe -t commands 'application actions' application_actions && ret=0
                    ;;
                stack)
                    local -a stack_actions
                    stack_actions=(
                        'deploy-complete:Deploy complete Enterprise RAG stack'
                        'delete-complete:Delete complete Enterprise RAG stack'
                    )
                    _describe -t commands 'stack actions' stack_actions && ret=0
                    ;;
            esac
            ;;
        args)
            # Handle arguments and options after component and action
            # Check if we're completing a flag value or offering flags
            local expl
            
            case ${words[$CURRENT]} in
                --config=*)
                    # Complete config file path
                    _files -g "*.yaml" && ret=0
                    ;;
                --inventory=*)
                    # Complete inventory file path
                    _files -g "*.ini" && ret=0
                    ;;
                --tag=*)
                    # Complete tag value
                    _wanted tags expl 'tag' compadd latest v1.5.0 v1.4.0 v1.3.0 custom dev && ret=0
                    ;;
                --registry=*)
                    # Complete registry value
                    _wanted registries expl 'registry' compadd docker.io/opea localhost:5000 localhost:32000 ghcr.io quay.io && ret=0
                    ;;
                *)
                    # Check previous word for flags that take values
                    case ${words[$((CURRENT-1))]} in
                        --config)
                            _files -g "*.yaml" && ret=0
                            ;;
                        --inventory)
                            _files -g "*.ini" && ret=0
                            ;;
                        --tag)
                            _wanted tags expl 'tag' compadd latest v1.5.0 v1.4.0 v1.3.0 custom dev && ret=0
                            ;;
                        --registry)
                            _wanted registries expl 'registry' compadd docker.io/opea localhost:5000 localhost:32000 ghcr.io quay.io && ret=0
                            ;;
                        *)
                            # Offer all flags
                            local -a flags
                            flags=(
                                '--config:Path to config.yaml file'
                                '--inventory:Path to inventory file'
                                '--tag:Docker image tag'
                                '--registry:Docker registry URL'
                                '--non-interactive:Run without prompts'
                                '-v:Verbose output'
                                '-vv:More verbose output'
                                '-vvv:Maximum verbosity'
                                '--help:Show help message'
                                '-h:Show help message'
                            )
                            
                            # For setup config, also offer directories
                            if [[ $component == "setup" && $action == "config" ]]; then
                                _directories && ret=0
                            fi
                            
                            _describe -t options 'option' flags && ret=0
                            ;;
                    esac
                    ;;
            esac
            ;;
    esac
    
    return 0
}
# If being sourced (not in fpath), register the completion function
if [[ -n "${ZSH_VERSION}" ]]; then
    compdef _installer_sh installer.sh
    compdef _installer_sh ./installer.sh
fi
