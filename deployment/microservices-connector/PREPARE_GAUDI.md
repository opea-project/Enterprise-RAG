# Gaudi configure preparation

To fully utilize Enterprise RAG the LLM should be run on top of Gaudi accelerators hardware.
Gaudi instances requieres to be prepared before they can be used.

After K8s is setup on Cluster follow bellow procedure of preparing Gaudi nodes

## Install Gaudi firmware

Make sure Firmware is installed on Gaudi nodes. Follow [Gaudi Firmware installation](https://docs.habana.ai/en/latest/Installation_Guide/Bare_Metal_Fresh_OS.html#driver-fw-install-bare) 

Run habanalabs-installer.sh to install the firmware
Next `sudo apt install -y habanalabs-container-runtime``
Follow Habanalabs instructions and setup `/etc/containerd/config.toml` to point to habana-container-runtime
```
sudo tee /etc/containerd/config.toml <<EOF
disabled_plugins = []
version = 2

[plugins]
  [plugins."io.containerd.grpc.v1.cri"]
    [plugins."io.containerd.grpc.v1.cri".containerd]
      default_runtime_name = "habana"
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.habana]
          runtime_type = "io.containerd.runc.v2"
          [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.habana.options]
            BinaryName = "/usr/bin/habana-container-runtime"
  [plugins."io.containerd.runtime.v1.linux"]
    runtime = "habana-container-runtime"
EOF
```
and `sudo systemctl restart containerd`

Next configure `/etc/habana-container-runtime/config.toml` according [Gaudi Firmware installation](https://docs.habana.ai/en/latest/Installation_Guide/Bare_Metal_Fresh_OS.html#driver-fw-install-bare)
Uncomment lines:
```
    #visible_devices_all_as_default = false

    #mount_accelerators = false
```

Next install K8s plugin following instruction [install K8s lugin for Gaudi] (https://docs.habana.ai/en/latest/Orchestration/Gaudi_Kubernetes/Device_Plugin_for_Kubernetes.html)
Once the plugin is installed verify it is working by checking if k8s can see gaudi resources on node. 8 Gaudi devices should be vissible.
```
  capacity:
    cpu: "192"
    ephemeral-storage: 1817309532Ki
    habana.ai/gaudi: "8"
    hugepages-1Gi: "0"
    hugepages-2Mi: 442Mi
    memory: 1056298408Ki
    pods: "110"
```
