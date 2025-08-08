# Preparing for Evaluation of Backup Feature

This document provides a list of steps necessary to prepare evaluation environment for backup feature with VMWare Velero.

The important assumption that is made here is about storage provider:
- The provider with easiest setup is NFS CSI.
- Yet the NFS storage provider may not be suitable for production.

## Installing NFS Server

### Prerequisites

* `nerdctl` command - available on GitHub repository [containerd/nerdctl](https://github.com/containerd/nerdctl).

### Server Installation

Firstly the NFS server needs to be set up, open for connections from other hosts.
```bash
sudo mkdir -p /opt/nfs-data/data
sudo chown -R nobody:nogroup /opt/nfs-data
sudo chmod -R 0777 /opt/nfs-data
sudo nerdctl run --name nfs-server --network host -td --privileged \
--restart unless-stopped -e SHARED_DIRECTORY=/data -v /opt/nfs-data:/data \
-p 2049:2049 itsthenetwork/nfs-server-alpine:12
```
Please verify the NFS Server ip address. It will be needed for next step.

## Installing CSI Driver from Helm Chart

> **Note**: `NFS_SERVER_IP` is needed for this step. That must be a routable IP address of the host where NFS server was installed in the previous step.

```bash
## https://github.com/kubernetes-csi/csi-driver-nfs/tree/master/charts
helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
[[ -z $NFS_SERVER_IP ]] && echo "Unset variable NFS_SERVER_IP" || helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system --version 4.11.0 --set externalSnapshotter.enabled=true --set controller.useTarCommandInSnapshot=true --set storageClass.create=true --set storageClass.name=nfs-csi --set storageClass.parameters.server=${NFS_SERVER_IP} --set storageClass.parameters.share=/data --set storageClass.volumeBindingMode=WaitForFirstConsumer --set storageClass.mountOptions="{nfsvers=4}"
```

The above command will start storage driver in cluster and will create and register a `StorageClass`.

### Register NFS StorageClass as default

```bash
## Review the name of now default StorageClass and make in non-default:
DEF_SC_NAME="$(kubectl get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}')"

annotate_sc_default() { sc_name=$1; toggle=${2:-true}; kubectl patch sc $sc_name -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"'$toggle'"}}}'; }

## unset previously default storage class and annotate nfs-csi the default one
[[ -n $DEF_SC_NAME ]] && annotate_sc_default $DEF_SC_NAME false
annotate_sc_default nfs-csi true
```

## Install VolumeSnapshotClass

This step is necessary for Velero to call correct class for making a snapshot.

Create a manifest document for `VolumeSnapshotClass` for applying it with `kubectl`:
```shell
cat <<EOF>> csi-snapclass.yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-nfs-snapclass
  labels:
    velero.io/csi-volumesnapshot-class: "true"
driver: nfs.csi.k8s.io
deletionPolicy: Delete

EOF

kubectl apply -f csi-snapclass.yaml
```

## Summary

After completing all of these steps velero should be able to create and restore PV snapshots.
