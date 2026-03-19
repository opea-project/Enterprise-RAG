# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.PHONY: fmt
fmt: ## Run go fmt against code.
	go fmt ./...

.PHONY: vet
vet: ## Run go vet against code.
	go vet ./...

.PHONY: test
test: fmt vet ## Run tests.
	go test ./... -coverprofile cover.out

##@ Build

.PHONY: build
build: fmt vet ## Build manager binary.
	go build -o bin/manager main.go

.PHONY: run
run: fmt vet ## Run a controller from your host.
	go run ./main.go

.PHONY: docker-build
docker-build: ## Build docker image.
	docker build -t nri-balloons-controller:latest .

.PHONY: docker-push
docker-push: ## Push docker image.
	docker push nri-balloons-controller:latest

##@ Deployment

.PHONY: helm-install
helm-install: ## Install using Helm chart.
	helm install nri-balloons-controller ../../../deployment/components/nri-balloons-controller -n nri-balloons-system --create-namespace

.PHONY: helm-uninstall
helm-uninstall: ## Uninstall using Helm chart.
	helm uninstall nri-balloons-controller -n nri-balloons-system

.PHONY: helm-upgrade
helm-upgrade: ## Upgrade using Helm chart.
	helm upgrade nri-balloons-controller ../../deployment/components/nri-balloons-controller -n nri-balloons-system

.PHONY: install
install: helm-install ## Alias for helm-install

.PHONY: uninstall
uninstall: helm-uninstall ## Alias for helm-uninstall

.PHONY: deploy
deploy: helm-install ## Alias for helm-install

.PHONY: undeploy
undeploy: helm-uninstall ## Alias for helm-uninstall
