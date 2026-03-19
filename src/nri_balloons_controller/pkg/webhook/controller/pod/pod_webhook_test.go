// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

package pod

import (
	"context"
	"encoding/json"
	"net/http"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	jsonpatch "gomodules.xyz/jsonpatch/v2"
	admissionv1 "k8s.io/api/admission/v1"
	corev1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

func TestPodMutator_Handle(t *testing.T) {
	// Setup scheme
	scheme := runtime.NewScheme()
	_ = corev1.AddToScheme(scheme)
	_ = rbacv1.AddToScheme(scheme)
	decoder := admission.NewDecoder(scheme)

	// Setup logger
	logger := zap.New(zap.UseDevMode(true))

	tests := []struct {
		name           string
		pod            *corev1.Pod
		envVars        map[string]string
		expectedAllow  bool
		expectedPatch  bool
		expectedStatus int32
		validateFunc   func(t *testing.T, patches []jsonpatch.Operation, client client.Client)
	}{
		{
			name: "Decoder not initialized",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
			},
			expectedStatus: http.StatusInternalServerError,
		},
		{
			name: "Target container not set in env",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
			},
			expectedStatus: http.StatusInternalServerError,
		},
		{
			name: "Target container not found in pod",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{Name: "other-container"},
					},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME": "target-container",
			},
			expectedAllow: true,
			expectedPatch: false,
		},
		{
			name: "Init container already exists",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{Name: "target-container"},
					},
					InitContainers: []corev1.Container{
						{Name: defaultInitContainerName},
					},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME": "target-container",
			},
			expectedAllow: true,
			expectedPatch: false,
		},
		{
			name: "Successful mutation",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{Name: "target-container"},
					},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME": "target-container",
			},
			expectedAllow: true,
			expectedPatch: true,
			validateFunc: func(t *testing.T, patches []jsonpatch.Operation, c client.Client) {
				assert.NotEmpty(t, patches)
				// We expect a patch to add init container
				foundInitContainer := false
				for _, patch := range patches {
					if patch.Operation == "add" && patch.Path == "/spec/initContainers" {
						foundInitContainer = true
						// Verify init container details
						containers, ok := patch.Value.([]interface{})
						if ok && len(containers) > 0 {
							containerMap, ok := containers[0].(map[string]interface{})
							if ok {
								assert.Equal(t, defaultInitContainerName, containerMap["name"])
								assert.Equal(t, defaultInitContainerImage, containerMap["image"])
							}
						}
					}
				}
				assert.True(t, foundInitContainer, "Should have added init container")
			},
		},
		{
			name: "Successful mutation with Service Account - Switch SA",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{Name: "target-container"},
					},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME":          "target-container",
				"INIT_CONTAINER_SERVICE_ACCOUNT": "custom-sa",
				"INIT_CONTAINER_CLUSTER_ROLE":    "test-role",
			},
			expectedAllow: true,
			expectedPatch: true,
			validateFunc: func(t *testing.T, patches []jsonpatch.Operation, c client.Client) {
				assert.NotEmpty(t, patches)
				foundSA := false
				for _, patch := range patches {
					if patch.Operation == "add" && patch.Path == "/spec/serviceAccountName" {
						foundSA = true
						assert.Equal(t, "custom-sa", patch.Value)
					}
				}
				assert.True(t, foundSA, "Should have switched service account")

				// Verify NO ClusterRoleBinding creation for default service account
				binding := &rbacv1.ClusterRoleBinding{}
				err := c.Get(context.Background(), client.ObjectKey{Name: "nri-balloons-init-default-default"}, binding)
				assert.Error(t, err)
				assert.True(t, errors.IsNotFound(err))
			},
		},
		{
			name: "Service Account is default - Switch SA",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
				Spec: corev1.PodSpec{
					ServiceAccountName: "default",
					Containers: []corev1.Container{
						{Name: "target-container"},
					},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME":          "target-container",
				"INIT_CONTAINER_SERVICE_ACCOUNT": "custom-sa",
				"INIT_CONTAINER_CLUSTER_ROLE":    "test-role",
			},
			expectedAllow: true,
			expectedPatch: true,
			validateFunc: func(t *testing.T, patches []jsonpatch.Operation, c client.Client) {
				assert.NotEmpty(t, patches)
				foundSA := false
				for _, patch := range patches {
					if (patch.Operation == "add" || patch.Operation == "replace") && patch.Path == "/spec/serviceAccountName" {
						foundSA = true
						assert.Equal(t, "custom-sa", patch.Value)
					}
				}
				assert.True(t, foundSA, "Should have switched service account")

				// Verify NO ClusterRoleBinding creation for default service account
				binding := &rbacv1.ClusterRoleBinding{}
				err := c.Get(context.Background(), client.ObjectKey{Name: "nri-balloons-init-default-default"}, binding)
				assert.Error(t, err)
				assert.True(t, errors.IsNotFound(err))

				// Verify ServiceAccount creation
				sa := &corev1.ServiceAccount{}
				err = c.Get(context.Background(), client.ObjectKey{Name: "custom-sa", Namespace: "default"}, sa)
				assert.NoError(t, err)
				assert.Equal(t, "custom-sa", sa.Name)

				// Verify ClusterRoleBinding creation for custom-sa
				bindingName := "nri-balloons-init-default-custom-sa"
				err = c.Get(context.Background(), client.ObjectKey{Name: bindingName}, binding)
				assert.NoError(t, err)
				assert.Equal(t, "custom-sa", binding.Subjects[0].Name)
			},
		},
		{
			name: "Service Account already set - Create Binding",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pod",
					Namespace: "default",
				},
				Spec: corev1.PodSpec{
					ServiceAccountName: "existing-sa",
					Containers: []corev1.Container{
						{Name: "target-container"},
					},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME":          "target-container",
				"INIT_CONTAINER_SERVICE_ACCOUNT": "custom-sa",
				"INIT_CONTAINER_CLUSTER_ROLE":    "test-role",
			},
			expectedAllow: true,
			expectedPatch: true,
			validateFunc: func(t *testing.T, patches []jsonpatch.Operation, c client.Client) {
				assert.NotEmpty(t, patches)
				foundSA := false
				for _, patch := range patches {
					if patch.Path == "/spec/serviceAccountName" {
						foundSA = true
					}
				}
				assert.False(t, foundSA, "Should NOT have modified service account")

				// Verify ClusterRoleBinding creation
				binding := &rbacv1.ClusterRoleBinding{}
				err := c.Get(context.Background(), client.ObjectKey{Name: "nri-balloons-init-default-existing-sa"}, binding)
				assert.NoError(t, err)
				assert.Equal(t, "existing-sa", binding.Subjects[0].Name)
				assert.Equal(t, "test-role", binding.RoleRef.Name)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Set env vars
			for k, v := range tt.envVars {
				os.Setenv(k, v)
				defer os.Unsetenv(k)
			}
			// Ensure cleanup of env vars that might not be in the map but set in previous tests or defaults
			defer os.Unsetenv("TARGET_CONTAINER_NAME")
			defer os.Unsetenv("INIT_CONTAINER_SERVICE_ACCOUNT")
			defer os.Unsetenv("INIT_CONTAINER_CLUSTER_ROLE")

			// Create fake client
			fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()

			mutator := &PodMutator{
				Client: fakeClient,
				Log:    logger,
			}
			if tt.name != "Decoder not initialized" {
				mutator.InjectDecoder(decoder)
			}

			// Create request
			rawPod, err := json.Marshal(tt.pod)
			require.NoError(t, err)

			req := admission.Request{
				AdmissionRequest: admissionv1.AdmissionRequest{
					Object: runtime.RawExtension{
						Raw: rawPod,
					},
					Namespace: tt.pod.Namespace,
				},
			}

			resp := mutator.Handle(context.Background(), req)

			if tt.expectedStatus != 0 {
				assert.Equal(t, tt.expectedStatus, resp.Result.Code)
			} else {
				assert.True(t, resp.Allowed)
				if tt.expectedPatch {
					assert.NotEmpty(t, resp.Patches)
				} else {
					assert.Empty(t, resp.Patches)
				}
			}

			if tt.validateFunc != nil {
				tt.validateFunc(t, resp.Patches, fakeClient)
			}
		})
	}
}

func TestGetEnv(t *testing.T) {
	key := "TEST_ENV_VAR"
	val := "test-value"
	def := "default-value"

	// Test default
	os.Unsetenv(key)
	assert.Equal(t, def, getEnv(key, def))

	// Test set value
	os.Setenv(key, val)
	defer os.Unsetenv(key)
	assert.Equal(t, val, getEnv(key, def))
}
