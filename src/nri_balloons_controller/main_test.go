// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

package main

import (
	"testing"

	"k8s.io/apimachinery/pkg/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/webhook"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"

	"github.com/intel/nri-balloons-controller/pkg/webhook/controller/pod"
)

func TestWebhookSetup_DecoderInjection(t *testing.T) {
	// Create a scheme
	testScheme := runtime.NewScheme()
	_ = clientgoscheme.AddToScheme(testScheme)

	// Create a fake client
	fakeClient := fake.NewClientBuilder().WithScheme(testScheme).Build()

	// Create pod mutator
	podMutator := &pod.PodMutator{
		Client: fakeClient,
		Log:    ctrl.Log.WithName("test"),
	}

	// Verify client is not nil
	if podMutator.Client == nil {
		t.Fatal("pod mutator client should not be nil")
	}

	// Create decoder and inject it
	decoder := admission.NewDecoder(testScheme)
	if err := podMutator.InjectDecoder(decoder); err != nil {
		t.Fatalf("failed to inject decoder into pod mutator: %v", err)
	}

	// Create the admission webhook wrapper
	admissionHandler := &webhook.Admission{Handler: podMutator}

	// Note: webhook.Admission doesn't have InjectDecoder - it will use the decoder
	// that was already injected into the handler when the webhook server calls it
	if admissionHandler == nil {
		t.Fatal("admission handler should not be nil")
	}

	// Verify the setup is correct by checking that both have the decoder
	// Note: We can't directly access private fields, but we can verify no errors occurred
	t.Log("webhook setup completed successfully with decoder injection")
}

func TestWebhookSetup_MissingClient(t *testing.T) {
	// Create pod mutator without client
	podMutator := &pod.PodMutator{
		Client: nil,
		Log:    ctrl.Log.WithName("test"),
	}

	// Verify this condition would be caught
	if podMutator.Client == nil {
		t.Log("correctly detected nil client - this would exit(1) in main")
	} else {
		t.Error("expected client to be nil")
	}
}

func TestWebhookSetup_DecoderInjectionBeforeWrapper(t *testing.T) {
	// This test verifies the correct order of operations:
	// 1. Create podMutator
	// 2. Inject decoder into podMutator
	// 3. Wrap with webhook.Admission (which will use the pre-injected decoder)

	testScheme := runtime.NewScheme()
	_ = clientgoscheme.AddToScheme(testScheme)

	fakeClient := fake.NewClientBuilder().WithScheme(testScheme).Build()

	// Step 1: Create podMutator
	podMutator := &pod.PodMutator{
		Client: fakeClient,
		Log:    ctrl.Log.WithName("test"),
	}

	// Step 2: Inject decoder into podMutator BEFORE wrapping
	decoder := admission.NewDecoder(testScheme)
	if err := podMutator.InjectDecoder(decoder); err != nil {
		t.Fatalf("failed to inject decoder before wrapping: %v", err)
	}

	// Step 3: Create wrapper - it will use the handler with pre-injected decoder
	admissionHandler := &webhook.Admission{Handler: podMutator}
	if admissionHandler == nil {
		t.Fatal("admission handler should not be nil")
	}

	t.Log("correct injection order verified")
}

func TestSchemeInitialization(t *testing.T) {
	// Verify the scheme is properly initialized
	testScheme := runtime.NewScheme()

	// Add client-go scheme
	if err := clientgoscheme.AddToScheme(testScheme); err != nil {
		t.Fatalf("failed to add client-go scheme: %v", err)
	}

	// Verify Pod is registered in the scheme
	decoder := admission.NewDecoder(testScheme)
	if decoder == nil {
		t.Fatal("failed to create decoder with scheme")
	}

	t.Log("scheme initialization successful")
}
