// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

package pod

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/go-logr/logr"
	corev1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

const (
	defaultInitContainerImage = "busybox:latest"
	defaultInitContainerName  = "wait-for-balloons"
	defaultBalloonsNamespace  = "default"
	defaultBalloonsDaemonSet  = "nri-balloons"
	defaultWaitTimeout        = 300
)

// PodMutator mutates Pods
type PodMutator struct {
	Client  client.Client
	Log     logr.Logger
	decoder admission.Decoder
}

// Handle handles admission requests
func (m *PodMutator) Handle(ctx context.Context, req admission.Request) admission.Response {
	pod := &corev1.Pod{}

	// Check if decoder is initialized
	if m.decoder == nil {
		return admission.Errored(http.StatusInternalServerError, fmt.Errorf("decoder not initialized"))
	}

	err := m.decoder.Decode(req, pod)
	if err != nil {
		return admission.Errored(http.StatusBadRequest, err)
	}

	podName := pod.Name
	if podName == "" {
		podName = pod.GenerateName
	}
	log := m.Log.WithValues("pod", podName, "namespace", pod.Namespace)

	// Get target container name from environment
	targetContainerName := getEnv("TARGET_CONTAINER_NAME", "")
	if targetContainerName == "" {
		err := fmt.Errorf("TARGET_CONTAINER_NAME environment variable not set")
		log.Error(err, "configuration error")
		return admission.Errored(http.StatusInternalServerError, err)
	}

	// Check if pod contains target container
	if !m.containsTargetContainer(pod, targetContainerName) {
		log.V(1).Info("pod does not contain target container, skipping", "targetContainer", targetContainerName)
		return admission.Allowed("target container not found")
	}

	// Check if init container already exists
	if m.hasInitContainer(pod) {
		log.V(1).Info("init container already exists, skipping")
		return admission.Allowed("init container exists")
	}

	// Add init container
	initContainer := m.createInitContainer()

	// Handle service account configuration
	serviceAccountName := pod.Spec.ServiceAccountName
	if serviceAccountName == "" {
		serviceAccountName = "default"
	}

	if serviceAccountName == "default" {
		// If pod uses default service account, switch to the dedicated init container service account
		// to avoid granting elevated permissions to the default service account
		initContainerServiceAccount := getEnv("INIT_CONTAINER_SERVICE_ACCOUNT", "")
		if initContainerServiceAccount != "" {
			// Ensure the dedicated service account exists in the pod's namespace
			if err := m.ensureServiceAccountExists(ctx, initContainerServiceAccount, pod.Namespace); err != nil {
				log.Error(err, "failed to ensure service account exists", "serviceAccount", initContainerServiceAccount)
			} else {
				// Ensure the dedicated service account has the necessary permissions
				if err := m.ensureServiceAccountPermissions(ctx, initContainerServiceAccount, pod.Namespace); err != nil {
					log.Error(err, "failed to ensure permissions for dedicated service account", "serviceAccount", initContainerServiceAccount)
				}

				pod.Spec.ServiceAccountName = initContainerServiceAccount
				log.Info("switched pod service account to init container service account",
					"oldServiceAccount", serviceAccountName,
					"newServiceAccount", initContainerServiceAccount)
			}
		}
	} else {
		// If pod uses a custom service account, ensure it has the necessary permissions
		if err := m.ensureServiceAccountPermissions(ctx, serviceAccountName, pod.Namespace); err != nil {
			log.Error(err, "failed to ensure permissions for service account", "serviceAccount", serviceAccountName)
			// We don't fail admission here, just log error
		}
	}

	// Modify the pod directly
	pod.Spec.InitContainers = append([]corev1.Container{initContainer}, pod.Spec.InitContainers...)

	log.Info("mutating pod to add init container",
		"initContainer", initContainer.Name,
		"initContainersCount", len(pod.Spec.InitContainers))

	// Marshal the modified pod
	marshaledPod, err := json.Marshal(pod)
	if err != nil {
		return admission.Errored(http.StatusInternalServerError, err)
	}

	log.Info("marshaled modified pod",
		"originalSize", len(req.Object.Raw),
		"modifiedSize", len(marshaledPod))

	// Create patch response
	resp := admission.PatchResponseFromRaw(req.Object.Raw, marshaledPod)
	log.Info("patch response created",
		"allowed", resp.Allowed,
		"patchesCount", len(resp.Patches))

	return resp
}

// createInitContainer creates the init container to be injected
func (m *PodMutator) createInitContainer() corev1.Container {
	initContainerName := getEnv("INIT_CONTAINER_NAME", defaultInitContainerName)
	initContainerImage := getEnv("INIT_CONTAINER_IMAGE", defaultInitContainerImage)
	balloonsNamespace := getEnv("BALLOONS_NAMESPACE", defaultBalloonsNamespace)
	balloonsDaemonSet := getEnv("BALLOONS_DAEMONSET", defaultBalloonsDaemonSet)
	waitTimeout := getEnv("WAIT_TIMEOUT", fmt.Sprintf("%d", defaultWaitTimeout))

	script := fmt.Sprintf(`set -e
echo "Waiting for all %s DaemonSet pods to be ready..."
SECONDS=0
TIMEOUT=%s
while true; do
  DESIRED=$(kubectl get daemonset %s -n %s -o jsonpath="{.status.desiredNumberScheduled}")
  READY=$(kubectl get daemonset %s -n %s -o jsonpath="{.status.numberReady}")
  if [ "$DESIRED" = "$READY" ] && [ "$DESIRED" != "" ]; then
    echo "All pods ready: $READY/$DESIRED"
    break
  fi
  if [ "$SECONDS" -ge "$TIMEOUT" ]; then
    echo "Timeout waiting for all pods to be ready ($READY/$DESIRED)"
    exit 1
  fi
  echo "Waiting... ($READY/$DESIRED ready)"
  sleep 5
done`, balloonsDaemonSet, waitTimeout, balloonsDaemonSet, balloonsNamespace, balloonsDaemonSet, balloonsNamespace)

	return corev1.Container{
		Name:  initContainerName,
		Image: initContainerImage,
		Command: []string{
			"/bin/sh",
			"-c",
			script,
		},
		SecurityContext: &corev1.SecurityContext{
			RunAsUser:                &[]int64{1000}[0],
			AllowPrivilegeEscalation: &[]bool{false}[0],
			Capabilities: &corev1.Capabilities{
				Drop: []corev1.Capability{"ALL"},
			},
		},
		Resources: corev1.ResourceRequirements{
			Limits: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("100m"),
				corev1.ResourceMemory: resource.MustParse("128Mi"),
			},
			Requests: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("10m"),
				corev1.ResourceMemory: resource.MustParse("32Mi"),
			},
		},
	}
}

// containsTargetContainer checks if pod contains a container with the target name
func (m *PodMutator) containsTargetContainer(pod *corev1.Pod, targetName string) bool {
	for _, container := range pod.Spec.Containers {
		if container.Name == targetName {
			return true
		}
	}
	return false
}

// hasInitContainer checks if the pod already has our init container
func (m *PodMutator) hasInitContainer(pod *corev1.Pod) bool {
	initContainerName := getEnv("INIT_CONTAINER_NAME", defaultInitContainerName)
	for _, initContainer := range pod.Spec.InitContainers {
		if initContainer.Name == initContainerName {
			return true
		}
	}
	return false
}

// ensureServiceAccountExists checks if the service account exists and creates it if not
func (m *PodMutator) ensureServiceAccountExists(ctx context.Context, name, namespace string) error {
	sa := &corev1.ServiceAccount{}
	err := m.Client.Get(ctx, client.ObjectKey{Name: name, Namespace: namespace}, sa)
	if err == nil {
		return nil // Exists
	}
	if !errors.IsNotFound(err) {
		return fmt.Errorf("failed to check existing service account: %v", err)
	}

	// Create service account
	sa = &corev1.ServiceAccount{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "nri-balloons-controller",
			},
		},
		AutomountServiceAccountToken: &[]bool{true}[0],
	}

	if err := m.Client.Create(ctx, sa); err != nil {
		if errors.IsAlreadyExists(err) {
			return nil
		}
		return fmt.Errorf("failed to create service account: %v", err)
	}

	m.Log.Info("created service account", "serviceAccount", name, "namespace", namespace)
	return nil
}

// ensureServiceAccountPermissions creates a ClusterRoleBinding for the service account
func (m *PodMutator) ensureServiceAccountPermissions(ctx context.Context, serviceAccountName, namespace string) error {
	clusterRoleName := getEnv("INIT_CONTAINER_CLUSTER_ROLE", "")
	if clusterRoleName == "" {
		return fmt.Errorf("INIT_CONTAINER_CLUSTER_ROLE environment variable not set")
	}

	bindingName := fmt.Sprintf("nri-balloons-init-%s-%s", namespace, serviceAccountName)

	// Check if binding already exists
	binding := &rbacv1.ClusterRoleBinding{}
	err := m.Client.Get(ctx, client.ObjectKey{Name: bindingName}, binding)
	if err == nil {
		// Binding exists, we assume it's correct
		return nil
	}
	if !errors.IsNotFound(err) {
		return fmt.Errorf("failed to check existing binding: %v", err)
	}

	// Create binding
	binding = &rbacv1.ClusterRoleBinding{
		ObjectMeta: metav1.ObjectMeta{
			Name: bindingName,
			Labels: map[string]string{
				"app.kubernetes.io/managed-by": "nri-balloons-controller",
			},
		},
		Subjects: []rbacv1.Subject{
			{
				Kind:      "ServiceAccount",
				Name:      serviceAccountName,
				Namespace: namespace,
			},
		},
		RoleRef: rbacv1.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "ClusterRole",
			Name:     clusterRoleName,
		},
	}

	if err := m.Client.Create(ctx, binding); err != nil {
		if errors.IsAlreadyExists(err) {
			return nil
		}
		return fmt.Errorf("failed to create cluster role binding: %v", err)
	}

	m.Log.Info("created cluster role binding for service account", "binding", bindingName, "serviceAccount", serviceAccountName)
	return nil
}

// InjectDecoder injects the decoder into the PodMutator
func (m *PodMutator) InjectDecoder(d admission.Decoder) error {
	m.decoder = d
	return nil
}

// getEnv gets environment variable with default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
