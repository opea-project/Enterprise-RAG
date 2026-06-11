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

func TestParseLabelSelectors(t *testing.T) {
	tests := []struct {
		name     string
		raw      string
		expected map[string]map[string]struct{}
	}{
		{
			name:     "empty string",
			raw:      "",
			expected: map[string]map[string]struct{}{},
		},
		{
			name: "single selector",
			raw:  "endpoint=bge-reranker-base",
			expected: map[string]map[string]struct{}{
				"endpoint": {"bge-reranker-base": {}},
			},
		},
		{
			name: "multiple values for same key",
			raw:  "endpoint=meta-llama-3-1-8b-in,endpoint=bge-reranker-base,endpoint=bge-base-en-v1-5",
			expected: map[string]map[string]struct{}{
				"endpoint": {
					"meta-llama-3-1-8b-in": {},
					"bge-reranker-base":    {},
					"bge-base-en-v1-5":     {},
				},
			},
		},
		{
			name: "multiple keys",
			raw:  "endpoint=foo,component=predictor",
			expected: map[string]map[string]struct{}{
				"endpoint":  {"foo": {}},
				"component": {"predictor": {}},
			},
		},
		{
			name: "whitespace is trimmed",
			raw:  " endpoint = foo , endpoint=bar ",
			expected: map[string]map[string]struct{}{
				"endpoint": {"foo": {}, "bar": {}},
			},
		},
		{
			name:     "malformed entries are skipped",
			raw:      "noequalsign,=novalue,nokey=,,",
			expected: map[string]map[string]struct{}{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parseLabelSelectors(tt.raw)
			assert.Equal(t, tt.expected, got)
		})
	}
}

func TestMatchesTargetLabels(t *testing.T) {
	m := &PodMutator{}

	tests := []struct {
		name      string
		podLabels map[string]string
		selectors map[string]map[string]struct{}
		expected  bool
	}{
		{
			name:      "matching label value",
			podLabels: map[string]string{"endpoint": "bge-reranker-base"},
			selectors: map[string]map[string]struct{}{"endpoint": {"bge-reranker-base": {}}},
			expected:  true,
		},
		{
			name:      "matching one of several values",
			podLabels: map[string]string{"endpoint": "bge-base-en-v1-5"},
			selectors: map[string]map[string]struct{}{"endpoint": {"meta-llama-3-1-8b-in": {}, "bge-base-en-v1-5": {}}},
			expected:  true,
		},
		{
			name:      "label key present but value not accepted",
			podLabels: map[string]string{"endpoint": "some-other-model"},
			selectors: map[string]map[string]struct{}{"endpoint": {"bge-reranker-base": {}}},
			expected:  false,
		},
		{
			name:      "label key absent",
			podLabels: map[string]string{"app": "foo"},
			selectors: map[string]map[string]struct{}{"endpoint": {"bge-reranker-base": {}}},
			expected:  false,
		},
		{
			name:      "no labels on pod",
			podLabels: nil,
			selectors: map[string]map[string]struct{}{"endpoint": {"bge-reranker-base": {}}},
			expected:  false,
		},
		{
			name:      "empty selectors",
			podLabels: map[string]string{"endpoint": "bge-reranker-base"},
			selectors: map[string]map[string]struct{}{},
			expected:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			pod := &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{Labels: tt.podLabels},
			}
			assert.Equal(t, tt.expected, m.matchesTargetLabels(pod, tt.selectors))
		})
	}
}

func TestPodMutator_Handle_LabelMatching(t *testing.T) {
	scheme := runtime.NewScheme()
	_ = corev1.AddToScheme(scheme)
	_ = rbacv1.AddToScheme(scheme)
	decoder := admission.NewDecoder(scheme)
	logger := zap.New(zap.UseDevMode(true))

	tests := []struct {
		name          string
		pod           *corev1.Pod
		envVars       map[string]string
		expectedPatch bool
	}{
		{
			name: "pod matched by endpoint label gets init container",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "bge-reranker-base-predictor-abc",
					Namespace: "nai-admin",
					Labels:    map[string]string{"endpoint": "bge-reranker-base"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "kserve-container", Image: "img"}},
				},
			},
			envVars: map[string]string{
				"TARGET_POD_LABELS": "endpoint=meta-llama-3-1-8b-in,endpoint=bge-reranker-base",
			},
			expectedPatch: true,
		},
		{
			name: "pod with non-target endpoint label is skipped",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "other-predictor-abc",
					Namespace: "nai-admin",
					Labels:    map[string]string{"endpoint": "some-other-model"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "kserve-container", Image: "img"}},
				},
			},
			envVars: map[string]string{
				"TARGET_POD_LABELS": "endpoint=bge-reranker-base",
			},
			expectedPatch: false,
		},
		{
			name: "container-name match still works alongside label config",
			pod: &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "vllm-pod",
					Namespace: "chatqa",
					Labels:    map[string]string{"app": "vllm"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "vllm", Image: "img"}},
				},
			},
			envVars: map[string]string{
				"TARGET_CONTAINER_NAME": "vllm",
				"TARGET_POD_LABELS":     "endpoint=bge-reranker-base",
			},
			expectedPatch: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			for k, v := range tt.envVars {
				os.Setenv(k, v)
				defer os.Unsetenv(k)
			}
			defer os.Unsetenv("TARGET_CONTAINER_NAME")
			defer os.Unsetenv("TARGET_POD_LABELS")

			fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
			mutator := &PodMutator{Client: fakeClient, Log: logger, decoder: decoder}

			podBytes, err := json.Marshal(tt.pod)
			require.NoError(t, err)
			req := admission.Request{
				AdmissionRequest: admissionv1.AdmissionRequest{
					Object: runtime.RawExtension{Raw: podBytes},
				},
			}

			resp := mutator.Handle(context.Background(), req)
			assert.True(t, resp.Allowed)
			if tt.expectedPatch {
				assert.NotEmpty(t, resp.Patches, "expected init container patch")
			} else {
				assert.Empty(t, resp.Patches, "expected no patch")
			}
		})
	}
}
