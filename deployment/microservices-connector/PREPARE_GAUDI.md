# Gaudi Configuration Preparation

To fully utilize Enterprise RAG, the LLM should be run on Gaudi accelerator hardware.
Gaudi instances need to be prepared before they can be used.

After setting up Kubernetes on the cluster, follow the procedure below to prepare the Gaudi nodes.

## Install Gaudi Firmware

Make sure Firmware is installed on Gaudi nodes. Follow the [Gaudi Firmware Installation](https://docs.habana.ai/en/latest/Installation_Guide/Bare_Metal_Fresh_OS.html#driver-fw-install-bare) guide for detailed instructions. Below are simplified steps:

1. Install the Intel Gaudi SW stack:
    ```bash
    habanalabs-installer.sh
    ```

2. Install Habana Container Runtime:
    ```bash
    sudo apt install -y habanalabs-container-runtime
    ```

3. Setup `/etc/containerd/config.toml` to point to habana-container-runtime:
    ```bash
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

    Then, restart the containerd service:
    ```
    sudo systemctl restart containerd
    ```

4. Next, uncomment the following lines in `/etc/habana-container-runtime/config.toml`:
    ```
    #visible_devices_all_as_default = false

    #mount_accelerators = false
    ```
    For more details, refer to the [Gaudi Firmware installation](https://docs.habana.ai/en/latest/Installation_Guide/Bare_Metal_Fresh_OS.html#driver-fw-install-bare) guide.

5. Finally, install the K8s plugin by following the instructions in [How to install K8s Plugin for Gaudi](https://docs.habana.ai/en/latest/Orchestration/Gaudi_Kubernetes/Device_Plugin_for_Kubernetes.html). Once the plugin is installed, verify its functionality by checking if Kubernetes can detect Gaudi resources on the node. You should see Gaudi devices listed:
    ```
    capacity:
      cpu: "192"
      ephemeral-storage: 1817309532Ki
      habana.ai/gaudi: "8" # <-- Number of Gaudi devices to be used.
      hugepages-1Gi: "0"
      hugepages-2Mi: 442Mi
      memory: 1056298408Ki
      pods: "110"
    ```
