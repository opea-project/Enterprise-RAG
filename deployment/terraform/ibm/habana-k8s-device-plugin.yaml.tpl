# Copyright (C) 2025 Intel Corporation

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or later, as published
# by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

# SPDX-License-Identifier: GPL-2.0-or-later

# Adjusted version for plugin version
# Original source: https://vault.habana.ai/artifactory/docker-k8s-device-plugin/habana-k8s-device-plugin.yaml

---
apiVersion: v1
kind: Namespace
metadata:
  name: habana-system
---
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  labels:
    app.kubernetes.io/name: habana
    app.kubernetes.io/component: runtime
  name: habana
handler: habana
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: habanalabs-device-plugin-daemonset
  namespace: habana-system
spec:
  selector:
    matchLabels:
      name: habanalabs-device-plugin-ds
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      # This annotation is deprecated. Kept here for backward compatibility
      # See https://kubernetes.io/docs/tasks/administer-cluster/guaranteed-scheduling-critical-addon-pods/
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ""
      labels:
        name: habanalabs-device-plugin-ds
    spec:
      priorityClassName: "system-node-critical"
      containers:
      - image: vault.habana.ai/docker-k8s-device-plugin/docker-k8s-device-plugin:${habana_plugin_version}
        name: habanalabs-device-plugin-ctr
        securityContext:
           privileged: true
        volumeMounts:
          - name: device-plugin
            mountPath: /var/lib/kubelet/device-plugins
      volumes:
        - name: device-plugin
          hostPath:
            path: /var/lib/kubelet/device-plugins
