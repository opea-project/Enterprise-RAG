# Preparing for Evaluation of Backup Feature

This document provides a list of steps necessary to prepare evaluation environment for backup feature with VMWare Velero.

The important assumption that is made here is about storage provider:
- The provider with easiest setup is NFS CSI.
- Yet the NFS storage provider may not be suitable for production.

## Installing NFS Server

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
```bash
## https://github.com/kubernetes-csi/csi-driver-nfs/tree/master/charts
helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system --version 4.11.0 --set externalSnapshotter.enabled=true --set storageClass.create=true --set storageClass.name=nfs-csi --set storageClass.parameters.server=${NFS_SERVER_IP} --set storageClass.parameters.share=/data --set storageClass.volumeBindingMode=WaitForFirstConsumer --set storageClass.mountOptions="{nfsvers=4}"
```

The above command will start storage driver in cluster and will create and register a `StorageClass`.

### Register NFS StorageClass as default

```bash
## Review the name of now default StorageClass and make in non-default:
kubectl get sc

kubectl patch sc DEF_SC_NAME -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'

## Annotate nfs-csi storageclass as default
kubectl patch sc nfs-csi -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## Install VolumeSnapshotClass

This step is necessary for Velero to call correct class for making a snapshot.

Create a document with following contents:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-nfs-snapclass
  labels:
    velero.io/csi-volumesnapshot-class: "true"
driver: nfs.csi.k8s.io
deletionPolicy: Delete
```

And apply it with `kubectl apply`.

> __Note__
>
> It is a known issue that NFS CSI snapshot function may restore some volumes to a suboptimal state.<br>
> It was found that ownership data may not reflect the source volume of snapshot. <br>
> The workaround is to apply expected ownership by mounting the same NFS share outside of cluster, and fix ownership with `chown`.
> This fix is needed for database services like: Postgresql and Minio.

## Summary

After completing all of these steps velero should be able to create and restore PV snapshots.
