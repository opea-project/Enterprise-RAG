# Intel® AI for Enterprise RAG Chatbot on VMware - Deployment Guide

<p align="center">
    <img src="images/vmware-logo.png" alt="VMware by Broadcom" width="500" />
</p>

## Capacity Requirements

| Resource Type | Guidance |
|---|---|
| VMs | 5 VMs: 3 control plane VMs + 2 worker VMs |
| Logical Cores | 152 vCPUs total |
| RAM Memory | 352 GB total |
| Disk Space | 784 GB total |
| Operating System | Ubuntu 24.04 Server |
| Hypervisor | VMware vSphere / ESXi 8.0 |

### Intel AMX Requirements

>

| Requirement | Specification | Notes |
|---|---|---|
| BIOS Configuration | Intel AMX must be Enabled | Check "Intel AMX" or "Advanced Matrix Extensions" in BIOS |
| Minimum ESXi Version | 7.0 Update 3 or later (8.x preferred) | Required for AMX instruction support |
| VM Hardware Compatibility | Version 20 (introduced with vSphere 8.0) | Older versions mask AMX features |
| EVC Mode | Must be set to Sapphire Rapids or higher or Disabled | If set to older generations (Ice Lake, Cascade Lake), AMX will be masked |

**Pre-deployment Checklist:**
- Is Intel AMX enabled in the host BIOS?
- Are hosts running ESXi 7.0 U3 or later?
- Is VM hardware version set to v20?
- Is cluster EVC baseline set to Sapphire Rapids or disabled?

## Node Reference

| Node | Role | vCPUs | RAM | Storage |
|---|---|---|---|---|
| controlVM0 | Control Plane | 8 | 32 GB | 128 GB |
| controlVM1 | Control Plane | 8 | 32 GB | 128 GB |
| controlVM2 | Control Plane | 8 | 32 GB | 128 GB |
| workerVM3 | Worker (Primary) | 64 | 128 GB | 200 GB |
| workerVM4 | Worker | 64 | 128 GB | 200 GB |
| **Total** | | **152 vCPUs** | **352 GB** | **784 GB** |

Control plane nodes handle Kubernetes orchestration only. All AI inference workloads run on worker nodes.

## AI Sizing Guide

| Resource Type | Guidance | Comments / Examples |
|---|---|---|
| LLM Model Size | Up to 8B parameters | casperhansen/llama-3-8b-instruct-awq — AWQ quantized, served via vLLM on CPU |
| Embedding Model | ~0.1B parameters | nomic-ai/nomic-embed-text-v1 |
| Reranking Model | ~0.3B parameters | BAAI/bge-reranker-base |
| Model Storage | 130 Gi total | 100 Gi LLM + 20 Gi embedding + 10 Gi reranker |

> **Note**: These specifications are guidance for a baseline deployment. Larger models can be used depending on your specific use case requirements and SLA targets. Consider scaling compute resources accordingly for larger model deployments.

## Steps

1. Tools Installation
2. Deploy Kubernetes Cluster on vSphere
3. Deploy Intel® AI for Enterprise RAG Application

### 1. Tools Installation

Install the following tools on your deployment machine (the VM you will be running commands from — recommended: workerVM3).



**Virtual Environment Setup**

Playbooks can be executed after creating a virtual environment and installing all prerequisites that allow running Ansible on your local machine. Use the below script to create a virtual environment:

```bash
SSH into one of the VMs (ex. SSH into vm3)

# Git clone the repo
git clone https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution.git

cd deployment
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yaml --upgrade
```



### 2. Deploy Kubernetes Cluster on vSphere

Follow the instructions in [cluster_deployment_guide.md](../cluster_deployment_guide.md)

### 3. Deploy Intel® AI for Enterprise RAG

Follow the instructions in [application_deployment_guide.md](../application_deployment_guide.md)



## Debugging Commands

For comprehensive debugging guidance, see [debug_tool.md](../debug_tool.md).

| Command | What it does |
|---|---|
| `kubectl get pods -A` | Check status of all pods |
| `kubectl get nodes` | Check all nodes are registered |
| `kubectl describe pod <n> --namespace <ns>` | Get detail on a specific pod |
| `kubectl logs -n chatqa <pod name>` | View logs for a ChatQNA pod |
| `kubectl describe node <node name>` | Get detail on a specific node |
| `kubectl get services --namespace ingress-nginx` | Check ingress controller services and external access |


