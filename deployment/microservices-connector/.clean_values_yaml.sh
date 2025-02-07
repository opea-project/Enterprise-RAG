#!/bin/bash

# This script is designed to ignore specific changes in the values.yaml file when using Git.
# It focuses on ignoring changes to proxy settings and tokens while allowing other modifications to be tracked.

# Steps to set up the script:

# 1. Change to the microservices-connector directory:
#    cd deployment/microservices-connector

# 2. create a .gitattributes file like this:
#    echo "helm/values.yaml filter=ignoreChanges" > .gitattributes

# 2. Add a new filter to your git configuration:
#    git config filter.ignoreChanges.clean "$(pwd)/.clean_values_yaml.sh"

# 3. add the values.yaml file to git to apply the filter:
# $ git add helm/values.yaml


sed -e 's#\(\(httpProxy\|httpsProxy\|noProxy\|hugToken\):\s*"\).*#\1"#g'
