/*
* Copyright (C) 2024 Intel Corporation
* SPDX-License-Identifier: Apache-2.0
 */

/* Modifications made to this file by [Intel] on [2024]
*  Portions of this file are derived from kserve: https://github.com/kserve/kserve
*  Copyright 2022 The KServe Author
 */

package main

import (
	// "bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"

	// "regexp"
	"strconv"
	"strings"
	"time"

	"github.com/MrAlias/otlpr"
	"github.com/go-logr/logr"
	"github.com/tidwall/gjson"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"

	// "crypto/rand"
	// "math/big"

	mcv1alpha3 "github.com/opea-project/GenAIInfra/microservices-connector/api/v1alpha3"
	flag "github.com/spf13/pflag"

	// OpenTelemetry/Metrics: Prometheus and opentelemetry imports
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/exporters/prometheus"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/metric"
	api "go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/propagation"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.opentelemetry.io/otel/trace"

	// OpenTelemetry/Traces:

	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

const (
	BufferSize    = 1024
	MaxGoroutines = 1024
	ServiceURL    = "serviceUrl"
	ServiceNode   = "node"
	DataPrep      = "DataPrep"
	Parameters    = "parameters"
	OtelVersion   = "v0.3.0"

	CallClientTimeoutSeconds   = 3600
	GraphHandlerTimeoutSeconds = 3600
)

var (
	OtelServiceName  = "router-service" // will be overwriteen by OTEL_SERVICE_NAME
	OtelExcludedUrls = []string{}
	debugRequestLogs = false
	log              logr.Logger

	jsonGraph       = flag.String("graph-json", "", "serialized json graph def")
	mcGraph         *mcv1alpha3.GMConnector
	defaultNodeName = "root"
	semaphore       = make(chan struct{}, MaxGoroutines)
	transport       = &http.Transport{
		MaxIdleConns:          1000,
		MaxIdleConnsPerHost:   100,
		IdleConnTimeout:       2 * time.Minute,
		TLSHandshakeTimeout:   time.Minute,
		ExpectContinueTimeout: 30 * time.Second,
	}
)

type EnsembleStepOutput struct {
	StepResponse   map[string]interface{}
	StepStatusCode int
}

type GMCGraphRoutingError struct {
	ErrorMessage string `json:"error"`
	Cause        string `json:"cause"`
}

type ReadCloser struct {
	*bytes.Reader
}

var (
	firstTokenLatencyMeasure metric.Float64Histogram
	nextTokenLatencyMeasure  metric.Float64Histogram
	allTokenLatencyMeasure   metric.Float64Histogram
	pipelineLatencyMeasure   metric.Float64Histogram
)

func initMeter() {
	// The exporter embeds a default OpenTelemetry Reader and
	// implements prometheus.Collector, allowing it to be used as
	// both a Reader and Collector.
	exporter, err := prometheus.New()
	if err != nil {
		log.Error(err, "metrics: cannot init prometheus collector")
	}
	provider := sdkmetric.NewMeterProvider(sdkmetric.WithReader(exporter))
	otel.SetMeterProvider(provider)

	// ppalucki: Own metrics defintion bellow
	const meterName = "entrag-telemetry"
	meter := provider.Meter(meterName)

	firstTokenLatencyMeasure, err = meter.Float64Histogram(
		"llm.first.token.latency",
		metric.WithUnit("ms"),
		metric.WithDescription("Measures the duration of first token generation."),
		api.WithExplicitBucketBoundaries(1, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16364),
	)
	if err != nil {
		log.Error(err, "metrics: cannot register first token histogram measure")
	}
	nextTokenLatencyMeasure, err = meter.Float64Histogram(
		"llm.next.token.latency",
		metric.WithUnit("ms"),
		metric.WithDescription("Measures the duration of generating all but first tokens."),
		api.WithExplicitBucketBoundaries(1, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16364),
	)
	if err != nil {
		log.Error(err, "metrics: cannot register next token histogram measure")
	}

	allTokenLatencyMeasure, err = meter.Float64Histogram(
		"llm.all.token.latency",
		metric.WithUnit("ms"),
		metric.WithDescription("Measures the duration to generate response with all tokens."),
		api.WithExplicitBucketBoundaries(1, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16364),
	)
	if err != nil {
		log.Error(err, "metrics: cannot register all token histogram measure")
	}

	pipelineLatencyMeasure, err = meter.Float64Histogram(
		"llm.pipeline.latency",
		metric.WithUnit("ms"),
		metric.WithDescription("Measures the duration to going through pipeline steps until first token is being generated (including read data time from client)."),
		api.WithExplicitBucketBoundaries(1, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16364),
	)
	if err != nil {
		log.Error(err, "metrics: cannot register pipeline histogram measure")
	}
	println("otel/metrics: configured")
}

func initLogs() {
	// if OTEL_LOGS_GRPC_ENDPOINT is set to grpc otlp endpoint like this OTEL_LOGS_GRPC_ENDPOINT=127.0.0.1:4317
	// then global variable log (logr.Logger) will be replaced with logr with sink that sends data to otlp endpoint https://github.com/MrAlias/otlpr
	// otherwise log uses zap from controller-runtime logf.WithName...
	otlpTarget, configured := os.LookupEnv("OTEL_LOGS_GRPC_ENDPOINT")
	if configured {
		conn, err := grpc.NewClient(otlpTarget, grpc.WithTransportCredentials(insecure.NewCredentials()))
		if err != nil {
			fmt.Println("error", err)
			//log.Error(err, "failed to configure logger grpc connection")
			os.Exit(1)
		}
		res := resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceNameKey.String(OtelServiceName),
		)
		log = otlpr.NewWithOptions(conn, otlpr.Options{
			LogCaller:     otlpr.All,
			LogCallerFunc: true,
			Batcher:       otlpr.Batcher{Messages: 1, Timeout: 5 * time.Second},
		})
		log = otlpr.WithResource(log, res)

		println("otel/logs: enabled - otlpr logger configured with:", otlpTarget)
		log.Info("OTEL OTLPR sink configured")
	} else {
		log = logf.Log.WithName("GMCGraphRouter")
		logf.SetLogger(zap.New())
		println("otel/logs: disabled - otlrp not configured (OTEL_LOGS_GRPC_ENDPOINT empty)")
	}

}

func initTraces() {
	// BY DEFAULT DO NOT INSTALL TRACES if URLS is NOT GIVEN
	otlpEndpoint, endpointFound := os.LookupEnv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if !endpointFound {
		println("otel/traces: disabled - OTEL_EXPORTER_OTLP_ENDPOINT not set")
		return
	}
	if otlpEndpoint == "" {
		println("otel/traces: disabled - OTEL_EXPORTER_OTLP_ENDPOINT is empty ")
		return
	}

	if os.Getenv("OTEL_TRACES_DISABLED") == "true" {
		println("otel/traces: disabled - because of OTEL_TRACES_DISABLED=true")
		return
	}

	println("otel/traces: enabled OTEL_EXPORTER_OTLP_ENDPOINT (or default localhost will be used):", os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))

	excludedUrlsStr, urlsFound := os.LookupEnv("OTEL_GO_EXCLUDED_URLS")
	if urlsFound {
		OtelExcludedUrls = strings.Split(excludedUrlsStr, ",")
	}
	fmt.Println("otel/traces: OTEL_GO_EXCLUDED_URLS =", OtelExcludedUrls)

	ctx := context.Background()
	exporterOtlp, err := otlptracehttp.New(ctx)
	if err != nil {
		log.Error(err, "failed to init trace exporters")
		os.Exit(1)
	}

	samplerRatio := 1.0
	ratioStr, ratioFound := os.LookupEnv("OTEL_TRACES_SAMPLER_FRACTION")
	if ratioFound {
		if samplerRatio, err = strconv.ParseFloat(ratioStr, 64); err == nil {
			if err != nil {
				log.Error(err, "failed to conver sampler ratio to float64")
				os.Exit(1)
			}
		}

	}
	fmt.Println("otel/traces: OTEL_TRACES_SAMPLER_FRACTION =", samplerRatio)

	// Use sdktrace.AlwaysSample sampler to sample all traces.
	// In a production application, use sdktrace.ProbabilitySampler with a desired probability.
	var tp trace.TracerProvider
	if os.Getenv("OTEL_TRACES_CONSOLE_EXPORTER") == "true" {
		println("otel/traces: console exporter enabled (OTEL_TRACES_CONSOLE_EXPORTER=true)")
		exporterStdout, err := stdouttrace.New(
			stdouttrace.WithPrettyPrint(),
			//stdouttrace.WithWriter(os.Stderr),
		)
		if err != nil {
			log.Error(err, "failed to init trace console exporter")
			os.Exit(1)
		}
		tp = sdktrace.NewTracerProvider(
			sdktrace.WithSampler(sdktrace.TraceIDRatioBased(samplerRatio)),
			sdktrace.WithBatcher(exporterOtlp),
			sdktrace.WithSyncer(exporterStdout),
			sdktrace.WithResource(resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceName(OtelServiceName))),
		)
	} else {
		println("otel/traces: console exporter disabled (missing OTEL_TRACES_CONSOLE_EXPORTER=true)")
		tp = sdktrace.NewTracerProvider(
			sdktrace.WithSampler(sdktrace.TraceIDRatioBased(samplerRatio)),
			sdktrace.WithBatcher(exporterOtlp),
			sdktrace.WithResource(resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceName(OtelServiceName))),
		)
	}

	// Later us this like this: mainTracer := otel.GetTracerProvider().Tracer("graphtracer")
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}))
}

func init() {
	println("otel: version:", OtelVersion)
	serviceNameFromEnv, found := os.LookupEnv("OTEL_SERVICE_NAME")
	if found {
		OtelServiceName = serviceNameFromEnv
	}
	println("otel: servicename:", OtelServiceName)
	initMeter()
	initLogs()
	initTraces()

	// any value of ENABLE_DEBUG_REQUEST_LOGS will enable debug logs
	_, debugEnvFound := os.LookupEnv("ENABLE_DEBUG_REQUEST_LOGS")
	if debugEnvFound {
		debugRequestLogs = true
	}
}

func (ReadCloser) Close() error {
	// Typically, you would release resources here, but for bytes.Reader, there's nothing to do.
	return nil
}

func NewReadCloser(b []byte) io.ReadCloser {
	return ReadCloser{bytes.NewReader(b)}
}

func (e *GMCGraphRoutingError) Error() string {
	return fmt.Sprintf("%s. %s", e.ErrorMessage, e.Cause)
}

func timeTrack(start time.Time, nodeOrStep string, name string) {
	elapsed := time.Since(start)
	log.Info("elapsed time", nodeOrStep, name, "time", elapsed)
}

func isSuccessFul(statusCode int) bool {
	if statusCode >= 200 && statusCode <= 299 {
		return true
	}
	return false
}

func pickupRouteByCondition(initInput []byte, condition string) bool {
	//sample config supported by gjson
	//"instances" : [
	//	{"model_id", "1"},
	//  ]
	// sample condition support by gjson query: "instances.#(modelId==\"1\")""
	if !gjson.ValidBytes(initInput) {
		fmt.Println("the initInput json format is invalid")
		return false
	}

	if gjson.GetBytes(initInput, condition).Exists() {
		return true
	}
	// ' and # will define a gjson query
	if strings.ContainsAny(condition, ".") || strings.ContainsAny(condition, "#") {
		return false
	}
	// key == value without nested json
	// sample config support by direct query {"model_id", "1"}
	// smaple condition support by json query: "modelId==\"1\""
	index := strings.Index(condition, "==")
	if index == -1 {
		fmt.Println("No '==' found in the route with condition [", condition, "]")
		return false
	} else {
		key := strings.TrimSpace(condition[:index])
		value := strings.TrimSpace(condition[index+2:])
		v := gjson.GetBytes(initInput, key).String()
		if v == value {
			return true
		}
	}
	return false
}

func prepareErrorResponse(err error, errorMessage string) []byte {
	igRoutingErr := &GMCGraphRoutingError{
		errorMessage,
		fmt.Sprintf("%v", err),
	}
	errorResponseBytes, err := json.Marshal(igRoutingErr)
	if err != nil {
		log.Error(err, "marshalling error")
	}
	return errorResponseBytes
}

func callService(
	ctx context.Context,
	step *mcv1alpha3.Step,
	serviceUrl string,
	input []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	semaphore <- struct{}{}
	defer func() { <-semaphore }()

	defer timeTrack(time.Now(), "step", serviceUrl)
	log.Info("Entering callService", "url", serviceUrl)

	// log the http header from the original request
	if debugRequestLogs {
		log.Info("Print the http request headers", "HTTP_Header", headers)
	}
	if step.InternalService.Config != nil {
		err := os.Setenv("no_proxy", step.InternalService.Config["no_proxy"])
		if err != nil {
			log.Error(err, "Error setting environment variable", "no_proxy", step.InternalService.Config["no_proxy"])
			return nil, 400, err
		}
	}

	//req, err := http.NewRequest("POST", serviceUrl, bytes.NewBuffer(input))
	req, err := http.NewRequestWithContext(ctx, "POST", serviceUrl, bytes.NewBuffer(input))
	if err != nil {
		log.Error(err, "An error occurred while preparing request object with serviceUrl.", "serviceUrl", serviceUrl)
		return nil, 500, err
	}

	if val := req.Header.Get("Content-Type"); val == "" {
		req.Header.Add("Content-Type", "application/json")
	}
	// normal client
	// callClient := http.Client{
	// 	Transport: transport,
	// 	Timeout:   600 * time.Second,
	// }

	// otel client
	// we want to use existing tracer instad creating a new one, but how !!!
	callClient := http.Client{
		Transport: otelhttp.NewTransport(
			transport,
			otelhttp.WithServerName(serviceUrl),
			otelhttp.WithSpanNameFormatter(
				func(operation string, r *http.Request) string {
					return "HTTP " + r.Method + " " + r.URL.String()
				}),
			otelhttp.WithFilter(func(r *http.Request) bool {
				for _, excludedUrl := range OtelExcludedUrls {
					if r.RequestURI == excludedUrl {
						return false
					}
				}
				return true
			}),
			otelhttp.WithMessageEvents(otelhttp.ReadEvents, otelhttp.WriteEvents),
			// ////  GEnerate EXTRA spans for dns/sent/reciver
			// otelhttp.WithClientTrace(
			// 	func(ctx context.Context) *httptrace.ClientTrace {
			// 		return otelhttptrace.NewClientTrace(ctx)
			// 	},
			// ),
		),
		Timeout: CallClientTimeoutSeconds * time.Second,
	}
	resp, err := callClient.Do(req)
	if err != nil {
		log.Error(err, "An error has occurred while calling service", "service", serviceUrl)
		return nil, 500, err
	}

	return resp.Body, resp.StatusCode, nil
}

// Use step service name to create a K8s service if serviceURL is empty
// TODO: add more features here, such as K8s service selector, labels, etc.
func getServiceURLByStepTarget(step *mcv1alpha3.Step, svcNameSpace string) string {
	if step.ServiceURL == "" {
		serviceURL := fmt.Sprintf("http://%s.%s.svc.cluster.local", step.StepName, svcNameSpace)
		return serviceURL
	}
	return step.ServiceURL
}

func executeStep(
	ctx context.Context,
	step *mcv1alpha3.Step,
	graph mcv1alpha3.GMConnector,
	initInput []byte,
	input []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	if step.NodeName != "" {
		// when nodeName is specified make a recursive call for routing to next step
		return routeStep(ctx, step.NodeName, graph, initInput, input, headers)
	}
	serviceURL := getServiceURLByStepTarget(step, graph.Namespace)
	return callService(ctx, step, serviceURL, input, headers)
}

func mergeRequests(respReq []byte, initReqData map[string]interface{}) []byte {
	var respReqData map[string]interface{}

	if _, exists := initReqData[Parameters]; exists {
		if err := json.Unmarshal(respReq, &respReqData); err != nil {
			log.Error(err, "Error unmarshaling respReqData:")
			return nil
		}
		// Merge init request into respReq
		for key, value := range initReqData[Parameters].(map[string]interface{}) {
			/*if _, exists := respReqData[key]; !exists {
				respReqData[key] = value
			}*/
			// overwrite the respReq by initial request
			respReqData[key] = value
		}
		mergedBytes, err := json.Marshal(respReqData)
		if err != nil {
			log.Error(err, "Error marshaling merged data:")
			return nil
		}
		return mergedBytes
	}
	return respReq
}

func handleSwitchNode(
	ctx context.Context,
	route *mcv1alpha3.Step,
	graph mcv1alpha3.GMConnector,
	initInput []byte,
	request []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	var statusCode int
	var responseBody io.ReadCloser
	var err error
	stepType := ServiceURL
	if route.NodeName != "" {
		stepType = ServiceNode
	}
	log.Info("Starting execution of step", "Node Name", route.NodeName, "type", stepType, "stepName", route.StepName)
	if responseBody, statusCode, err = executeStep(ctx, route, graph, initInput, request, headers); err != nil {
		return nil, 500, err
	}

	if route.Dependency == mcv1alpha3.Hard && !isSuccessFul(statusCode) {
		log.Info(
			"This step is a hard dependency and it is unsuccessful",
			"stepName",
			route.StepName,
			"statusCode",
			statusCode,
		)
	}
	return responseBody, statusCode, nil
}

func handleSwitchPipeline(
	ctx context.Context,
	nodeName string,
	graph mcv1alpha3.GMConnector,
	initInput []byte,
	input []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	currentNode := graph.Spec.Nodes[nodeName]
	var statusCode int
	var responseBody io.ReadCloser
	var responseBytes []byte
	var err error

	initReqData := make(map[string]interface{})
	if err = json.Unmarshal(initInput, &initReqData); err != nil {
		log.Error(err, "Error unmarshaling initReqData:")
		return nil, 500, err
	}

	for index, route := range currentNode.Steps {
		if route.InternalService.IsDownstreamService {
			log.Info(
				"InternalService DownstreamService is true, skip the execution of step",
				"type",
				currentNode.RouterType,
				"stepName",
				route.StepName,
			)
			continue
		}

		// make sure that the process goes to the correct step
		if route.Condition != "" {
			if !pickupRouteByCondition(initInput, route.Condition) {
				continue
			}
		}

		log.Info("Current Step Information", "Node Name", nodeName, "Step Index", index)
		request := input
		if responseBody != nil {
			responseBytes, err = io.ReadAll(responseBody)
			if err != nil {
				log.Error(err, "Error while reading the response body")
				return nil, 500, err
			}
			if debugRequestLogs {
				log.Info("Print Previous Response Bytes", "Previous Response Bytes",
					responseBytes, "Previous Status Code", statusCode)
			}
			err = responseBody.Close()
			if err != nil {
				log.Error(err, "Error while trying to close the responseBody in handleSwitchPipeline")
			}
		}

		if debugRequestLogs {
			log.Info("Print Original Request Bytes", "Request Bytes", request)
		}
		if route.Data == "$response" && index > 0 {
			request = mergeRequests(responseBytes, initReqData)
		}
		if debugRequestLogs {
			log.Info("Print New Request Bytes", "Request Bytes", request)
		}
		responseBody, statusCode, err = handleSwitchNode(ctx, &route, graph, initInput, request, headers)
		if err != nil {
			return nil, statusCode, err
		}
	}
	return responseBody, statusCode, err
}

func handleEnsemblePipeline(
	ctx context.Context,
	nodeName string,
	graph mcv1alpha3.GMConnector,
	initInput []byte,
	input []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	currentNode := graph.Spec.Nodes[nodeName]
	ensembleRes := make([]chan EnsembleStepOutput, len(currentNode.Steps))
	errChan := make(chan error)
	for i := range currentNode.Steps {
		step := &currentNode.Steps[i]
		stepType := ServiceURL
		if step.NodeName != "" {
			stepType = ServiceNode
		}
		log.Info("Starting execution of step", "type", stepType, "stepName", step.StepName)
		resultChan := make(chan EnsembleStepOutput)
		ensembleRes[i] = resultChan
		go func() {
			responseBody, statusCode, err := executeStep(ctx, step, graph, initInput, input, headers)
			if err == nil {
				output, rerr := io.ReadAll(responseBody)
				if rerr != nil {
					log.Error(rerr, "Error while reading the response body")
				}
				var res map[string]interface{}
				if err = json.Unmarshal(output, &res); err == nil {
					resultChan <- EnsembleStepOutput{
						StepResponse:   res,
						StepStatusCode: statusCode,
					}
					return
				}
			}
			rerr := responseBody.Close()
			if rerr != nil {
				log.Error(rerr, "Error while trying to close the responseBody in handleEnsemblePipeline")
			}
			errChan <- err
		}()
	}
	// merge responses from parallel steps
	response := map[string]interface{}{}
	ensembleStepOutput := EnsembleStepOutput{}
	for i, resultChan := range ensembleRes {
		key := currentNode.Steps[i].StepName
		if key == "" {
			key = strconv.Itoa(i) // Use index if no step name
		}
		select {
		case ensembleStepOutput = <-resultChan:
			if !isSuccessFul(ensembleStepOutput.StepStatusCode) && currentNode.Steps[i].Dependency == mcv1alpha3.Hard {
				log.Info(
					"This step is a hard dependency and it is unsuccessful",
					"stepName",
					currentNode.Steps[i].StepName,
					"statusCode",
					ensembleStepOutput.StepStatusCode,
				)
				stepResponse, _ := json.Marshal(ensembleStepOutput.StepResponse)
				stepIOReader := NewReadCloser(stepResponse)
				return stepIOReader, ensembleStepOutput.StepStatusCode, nil
			} else {
				response[key] = ensembleStepOutput.StepResponse
			}
		case err := <-errChan:
			return nil, 500, err
		}
	}
	// return json.Marshal(response)
	combinedResponse, _ := json.Marshal(response) // TODO check if you need err handling for Marshalling
	combinedIOReader := NewReadCloser(combinedResponse)
	return combinedIOReader, 200, nil
}

func handleSequencePipeline(
	ctx context.Context,
	nodeName string,
	graph mcv1alpha3.GMConnector,
	initInput []byte,
	input []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	currentNode := graph.Spec.Nodes[nodeName]
	var statusCode int
	var responseBody io.ReadCloser
	var responseBytes []byte
	var err error

	initReqData := make(map[string]interface{})
	if err = json.Unmarshal(initInput, &initReqData); err != nil {
		log.Error(err, "Error unmarshaling initReqData:")
		return nil, 500, err
	}
	for i := range currentNode.Steps {
		step := &currentNode.Steps[i]
		stepType := ServiceURL
		if step.NodeName != "" {
			stepType = ServiceNode
		}
		if step.InternalService.IsDownstreamService {
			log.Info(
				"InternalService DownstreamService is true, skip the execution of step",
				"type",
				stepType,
				"stepName",
				step.StepName,
			)
			continue
		}
		log.Info("Starting execution of step", "type", stepType, "stepName", step.StepName)
		request := input
		if debugRequestLogs {
			log.Info("Print Original Request Bytes", "Request Bytes", request)
		}
		if responseBody != nil {
			responseBytes, err = io.ReadAll(responseBody)
			if err != nil {
				log.Error(err, "Error while reading the response body")
				return nil, 500, err
			}
			if debugRequestLogs {
				log.Info("Print Previous Response Bytes", "Previous Response Bytes",
					responseBytes, "Previous Status Code", statusCode)
			}
			err := responseBody.Close()
			if err != nil {
				log.Error(err, "Error while trying to close the responseBody in handleSequencePipeline")
			}
		}

		if step.Data == "$response" && i > 0 {
			request = mergeRequests(responseBytes, initReqData)
		}
		if debugRequestLogs {
			log.Info("Print New Request Bytes", "Request Bytes", request)
		}
		if step.Condition != "" {
			if !gjson.ValidBytes(responseBytes) {
				return nil, 500, fmt.Errorf("invalid response")
			}
			// if the condition does not match for the step in the sequence we stop and return the response
			if !gjson.GetBytes(responseBytes, step.Condition).Exists() {
				return responseBody, 500, nil
			}
		}
		if responseBody, statusCode, err = executeStep(ctx, step, graph, initInput, request, headers); err != nil {
			return nil, 500, err
		}
		/*
		   Only if a step is a hard dependency, we will check for its success.
		*/
		if step.Dependency == mcv1alpha3.Hard {
			if !isSuccessFul(statusCode) {
				log.Info(
					"This step is a hard dependency and it is unsuccessful",
					"stepName",
					step.StepName,
					"statusCode",
					statusCode,
				)
				// Stop the execution of sequence right away if step is a hard dependency and is unsuccessful
				return responseBody, statusCode, nil
			}
		}
	}
	return responseBody, statusCode, nil
}

func routeStep(
	ctx context.Context,
	nodeName string,
	graph mcv1alpha3.GMConnector,
	initInput, input []byte,
	headers http.Header,
) (io.ReadCloser, int, error) {
	defer timeTrack(time.Now(), "node", nodeName)
	currentNode := graph.Spec.Nodes[nodeName]
	log.Info("Current Node", "Node Name", nodeName)

	if currentNode.RouterType == mcv1alpha3.Switch {
		return handleSwitchPipeline(ctx, nodeName, graph, initInput, input, headers)
	}

	if currentNode.RouterType == mcv1alpha3.Ensemble {
		return handleEnsemblePipeline(ctx, nodeName, graph, initInput, input, headers)
	}

	if currentNode.RouterType == mcv1alpha3.Sequence {
		return handleSequencePipeline(ctx, nodeName, graph, initInput, input, headers)
	}
	log.Error(nil, "invalid route type", "type", currentNode.RouterType)
	return nil, 500, fmt.Errorf("invalid route type: %v", currentNode.RouterType)
}

func mcGraphHandler(w http.ResponseWriter, req *http.Request) {
	ctx, cancel := context.WithTimeout(req.Context(), GraphHandlerTimeoutSeconds*time.Second)
	defer cancel()

	done := make(chan struct{})
	go func() {
		defer close(done)

		mainTracer := otel.GetTracerProvider().Tracer("graphtracer")
		_, span := mainTracer.Start(ctx, "read initial request")

		// ### Example event
		// uk := attribute.Key("foo")
		// bag := baggage.FromContext(ctx)
		// span.AddEvent("handling this...", trace.WithAttributes(uk.String(bag.Member("bar").Value())))
		// ### Example log entry
		// otlpr.WithContext(log, ctx).Info("Example entry log with some data", "foz", "baz")

		allTokensStartTime := time.Now()
		inputBytes, err := io.ReadAll(req.Body)
		if err != nil {
			log.Error(err, "failed to read request body")
			http.Error(w, "failed to read request body", http.StatusBadRequest)
			return
		}
		span.SetAttributes(attribute.Int("initial request body size", len(inputBytes)))
		span.End()

		allStepsCtx, span := mainTracer.Start(ctx, "router all steps") // this context will be used for callClient instrumenation (POSTs)
		responseBody, statusCode, err := routeStep(allStepsCtx, defaultNodeName, *mcGraph, inputBytes, inputBytes, req.Header)
		pipeLatencyMilliseconds := float64(time.Since(allTokensStartTime)) / float64(time.Millisecond)
		pipelineLatencyMeasure.Record(ctx, pipeLatencyMilliseconds)

		span.SetAttributes(attribute.Int("last_step.statusCode", statusCode))
		span.SetAttributes(attribute.Float64("llm.pipeline.latency.ms", pipeLatencyMilliseconds))

		span.End()

		if statusCode == 466 { // Guardrails code!
			log.Error(err, "Guardrails activated!")
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(statusCode)
			respBytes, _ := io.ReadAll(responseBody)
			w.Write(prepareErrorResponse(err, string(respBytes)))
			return
		}

		if err != nil {
			log.Error(err, "failed to process request")
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(statusCode)
			if _, err := w.Write(prepareErrorResponse(err, "Failed to process request")); err != nil {
				log.Error(err, "failed to write mcGraphHandler response")
			}
			return
		}
		defer func() {
			err := responseBody.Close()
			if err != nil {
				log.Error(err, "Error while trying to close the responseBody in mcGraphHandler")
			}
		}()

		w.Header().Set("Content-Type", "application/json")
		firstTokenCollected := false
		firstTokenLatencyMilliseconds := 0.0
		nextTokenLatencyTotal := 0.0
		nextTokenLatencyCount := 0.0
		buffer := make([]byte, BufferSize)
		ctx, spanFor := mainTracer.Start(ctx, "tokens")
		for {

			// DETAILED spans (disabled because number of tokens generated!)
			// _, span = mainTracer.Start(ctx, "read response partial")

			// measure time of reading another portion of response
			tokenStartTime := time.Now()
			n, err := responseBody.Read(buffer)

			// span.End() // "read response partial"

			elapsedTimeMilisecond := float64(time.Since(tokenStartTime)) / float64(time.Millisecond)

			if !firstTokenCollected {
				firstTokenCollected = true
				firstTokenLatencyMeasure.Record(ctx, elapsedTimeMilisecond)
				firstTokenLatencyMilliseconds = elapsedTimeMilisecond
			} else {
				nextTokenLatencyMeasure.Record(ctx, elapsedTimeMilisecond)
				nextTokenLatencyTotal += elapsedTimeMilisecond
				nextTokenLatencyCount += 1.0
			}

			if err != nil && err != io.EOF {
				log.Error(err, "failed to read from response body")
				http.Error(w, "failed to read from response body", http.StatusInternalServerError)
				return
			}
			if n == 0 {
				break
			}

			// Write the chunk to the ResponseWriter

			// DETAILED spans (disabled because number of tokens generated!)
			// _, span = mainTracer.Start(ctx, "reponse write partial")

			// measure time of reading another portion of response
			if _, err := w.Write(buffer[:n]); err != nil {
				log.Error(err, "failed to write to ResponseWriter")
				return
			}

			// span.End() // "response write partial"

			// Flush the data to the client immediately
			if flusher, ok := w.(http.Flusher); ok {
				flusher.Flush()
			} else {
				log.Error(errors.New("unable to flush data"), "ResponseWriter does not support flushing")
				return
			}
		}

		// Statisitcs for metrics and traces attributes
		allTokensElapsedTimeMilisecond := float64(time.Since(allTokensStartTime)) / float64(time.Millisecond)
		allTokenLatencyMeasure.Record(ctx, allTokensElapsedTimeMilisecond)
		spanFor.SetAttributes(attribute.Float64("llm.first.token.latency.ms", firstTokenLatencyMilliseconds))
		spanFor.SetAttributes(attribute.Float64("llm.next.token.latency.total.ms", nextTokenLatencyTotal))
		spanFor.SetAttributes(attribute.Float64("llm.next.token.latency.count", nextTokenLatencyCount))
		spanFor.SetAttributes(attribute.Float64("llm.next.token.latency.avg.ms", nextTokenLatencyTotal/nextTokenLatencyCount))
		spanFor.SetAttributes(attribute.Float64("llm.all.token.latency.ms", allTokensElapsedTimeMilisecond))
		spanFor.End()

	}()

	select {
	case <-ctx.Done():
		log.Error(errors.New("request timed out"), "failed to process request")
		http.Error(w, "request timed out", http.StatusGatewayTimeout)
	case <-done:
		log.Info("mcGraphHandler is done")
	}
}

func mcDataHandler(w http.ResponseWriter, r *http.Request) {
	var isDataHandled bool
	serviceName := r.Header.Get("SERVICE_NAME")
	defaultNode := mcGraph.Spec.Nodes[defaultNodeName]
	for i := range defaultNode.Steps {
		step := &defaultNode.Steps[i]
		if DataPrep == step.StepName {
			if serviceName != "" && serviceName != step.InternalService.ServiceName {
				continue
			}
			log.Info("Starting execution of step", "stepName", step.StepName)
			serviceURL := getServiceURLByStepTarget(step, mcGraph.Namespace)
			log.Info("ServiceURL is", "serviceURL", serviceURL)
			// Parse the multipart form in the request
			// err := r.ParseMultipartForm(64 << 20) // 64 MB is the default used by ParseMultipartForm

			// Set no limit on multipart form size
			err := r.ParseMultipartForm(0)
			if err != nil {
				http.Error(w, "Failed to parse multipart form", http.StatusBadRequest)
				return
			}
			// Create a buffer to hold the new form data
			var buf bytes.Buffer
			writer := multipart.NewWriter(&buf)
			// Copy all form fields from the original request to the new request
			for key, values := range r.MultipartForm.Value {
				for _, value := range values {
					err := writer.WriteField(key, value)
					if err != nil {
						handleMultipartError(writer, err)
						http.Error(w, "Failed to write form field", http.StatusInternalServerError)
						return
					}
				}
			}
			// Copy all files from the original request to the new request
			for key, fileHeaders := range r.MultipartForm.File {
				for _, fileHeader := range fileHeaders {
					file, err := fileHeader.Open()
					if err != nil {
						handleMultipartError(writer, err)
						http.Error(w, "Failed to open file", http.StatusInternalServerError)
						return
					}
					defer func() {
						if err := file.Close(); err != nil {
							log.Error(err, "error closing file")
						}
					}()
					part, err := writer.CreateFormFile(key, fileHeader.Filename)
					if err != nil {
						handleMultipartError(writer, err)
						http.Error(w, "Failed to create form file", http.StatusInternalServerError)
						return
					}
					_, err = io.Copy(part, file)
					if err != nil {
						handleMultipartError(writer, err)
						http.Error(w, "Failed to copy file", http.StatusInternalServerError)
						return
					}
				}
			}

			err = writer.Close()
			if err != nil {
				http.Error(w, "Failed to close writer", http.StatusInternalServerError)
				return
			}

			req, err := http.NewRequest(r.Method, serviceURL, &buf)
			if err != nil {
				http.Error(w, "Failed to create new request", http.StatusInternalServerError)
				return
			}
			// Copy headers from the original request to the new request
			for key, values := range r.Header {
				for _, value := range values {
					req.Header.Add(key, value)
				}
			}
			req.Header.Set("Content-Type", writer.FormDataContentType())
			client := &http.Client{}
			resp, err := client.Do(req)
			if err != nil {
				http.Error(w, "Failed to send request to backend", http.StatusInternalServerError)
				return
			}
			defer func() {
				if err := resp.Body.Close(); err != nil {
					log.Error(err, "error closing response body stream")
				}
			}()
			// Copy the response headers from the backend service to the original client
			for key, values := range resp.Header {
				for _, value := range values {
					w.Header().Add(key, value)
				}
			}
			w.WriteHeader(resp.StatusCode)
			// Copy the response body from the backend service to the original client
			_, err = io.Copy(w, resp.Body)
			if err != nil {
				log.Error(err, "failed to copy response body")
			}
			isDataHandled = true
		}
	}

	if !isDataHandled {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(404)
		if _, err := w.Write([]byte("\n Message: None dataprep endpoint is available! \n")); err != nil {
			log.Info("Message: ", "failed to write mcDataHandler response")
		}
	}
}

func handleMultipartError(writer *multipart.Writer, err error) {
	// In case of an error, close the writer to clean up
	werr := writer.Close()
	if werr != nil {
		log.Error(werr, "Error during close writer")
		return
	}
	// Handle the error as needed, such as logging or returning an error response
	log.Error(err, "Error during multipart creation")
}

func initializeRoutes() *http.ServeMux {
	mux := http.NewServeMux()

	// Wrap connector handlers with otelhttp wrappers
	// "http.server.request.size" -  Int64Counter -  "Measures the size of HTTP request messages" (Incoming request bytes total)
	// "http.server.response.size" - Int64Counter  - "Measures the size of HTTP response messages" (Incoming response bytes total)
	// "http.server.duration" - Float64histogram "Measures the duration of inbound HTTP requests." (Incoming end to end duration, milliseconds)
	handleFunc := func(pattern string, handlerFunc func(http.ResponseWriter, *http.Request), operation string) {
		// Wrap with otelhttp handler.
		handler := otelhttp.NewHandler(
			otelhttp.WithRouteTag(pattern, http.HandlerFunc(handlerFunc)),
			operation,
			otelhttp.WithFilter(func(r *http.Request) bool {
				for _, excludedUrl := range OtelExcludedUrls {
					if r.RequestURI == excludedUrl {
						return false
					}
				}
				return true
			}),
		)
		mux.Handle(pattern, handler)

		// Original code with wrapping with OTLP.
		// mux.Handle(pattern, http.HandlerFunc(handlerFunc))
	}

	handleFunc("/", mcGraphHandler, "mcGraphHandler")
	handleFunc("/dataprep", mcDataHandler, "mcDataHandler")

	promHandler := promhttp.Handler()
	handleFunc("/metrics", promHandler.ServeHTTP, "metrics")
	log.Info("Metrics exposed on /metrics.", "version", OtelVersion)

	return mux
}

func main() {
	flag.Parse()

	mcGraph = &mcv1alpha3.GMConnector{}
	err := json.Unmarshal([]byte(*jsonGraph), mcGraph)
	if err != nil {
		log.Error(err, "failed to unmarshall gmc graph json")
		os.Exit(1)
	}

	log.Info("Listen on :8080", "GraphTimeout(s):", CallClientTimeoutSeconds, "CallClientTimeout(s):", GraphHandlerTimeoutSeconds)
	mcRouter := initializeRoutes()

	server := &http.Server{
		// specify the address and port
		Addr: ":8080",
		// specify the HTTP routers
		Handler: mcRouter,
		// set the maximum duration for reading the entire request, including the body
		ReadTimeout: GraphHandlerTimeoutSeconds * time.Second,
		// set the maximum duration before timing out writes of the response
		WriteTimeout: GraphHandlerTimeoutSeconds * time.Second,
		// set the maximum amount of time to wait for the next request when keep-alive are enabled
		IdleTimeout: 3 * time.Minute,
	}
	err = server.ListenAndServe()

	if err != nil {
		log.Error(err, "failed to listen on 8080")
		os.Exit(1)
	}
}
