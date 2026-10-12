package main

/*
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
*/
import "C"

import (
    "context"
    "encoding/base64"
    "fmt"
    "log"
    nhttp "net/http"
	"os"
    "runtime/cgo"
	"runtime/debug"
    "strings"
    "sync"
    "time"
    "unicode/utf8"
    "unsafe"

    fhttp "github.com/Danny-Dasilva/fhttp"
    "github.com/gorilla/websocket"
    "github.com/vmihailenco/msgpack/v5"
)

// BatchRequest holds multiple requests to be processed in parallel
type BatchRequest struct {
    Requests []cycleTLSRequest `msgpack:"requests"`
}

// BatchResponse holds responses for all requests in a batch
type BatchResponse struct {
    Responses []map[string]interface{} `msgpack:"responses"`
}

var (
    ffiClientOnce sync.Once
    ffiClient     *CycleTLS

    // Async result store for non-blocking requests
	asyncResults sync.Map // map[uintptr]*asyncResultWithNotify

    // WebSocket connection store
    wsConnections sync.Map // map[uintptr]*websocket.Conn

    // SSE connection store
    sseConnections sync.Map // map[uintptr]*SSEResponse
)

func getFFIClient() *CycleTLS {
    ffiClientOnce.Do(func() {
        client := Init()
        ffiClient = &client
    })
    return ffiClient
}

func normalizeMethod(method string) string {
    if method == "" {
        return nhttp.MethodGet
    }
    upper := strings.ToUpper(method)
    if !isValidMethod(upper) {
        return nhttp.MethodGet
    }
    return upper
}

func isValidMethod(method string) bool {
    switch method {
    case nhttp.MethodGet,
        nhttp.MethodPost,
        nhttp.MethodPut,
        nhttp.MethodDelete,
        nhttp.MethodHead,
        nhttp.MethodOptions,
        nhttp.MethodPatch,
        nhttp.MethodConnect,
        nhttp.MethodTrace:
        return true
    default:
        return false
    }
}

func convertCookies(cookies []*nhttp.Cookie) []map[string]interface{} {
    if len(cookies) == 0 {
        return nil
    }

    result := make([]map[string]interface{}, 0, len(cookies))
    for _, c := range cookies {
        if c == nil {
            continue
        }

        cookie := map[string]interface{}{
            "name":  c.Name,
            "value": c.Value,
        }

        if c.Path != "" {
            cookie["path"] = c.Path
        }
        if c.Domain != "" {
            cookie["domain"] = c.Domain
        }
        if !c.Expires.IsZero() {
            cookie["expires"] = c.Expires.UTC().Format(time.RFC3339Nano)
        }
        if c.MaxAge != 0 {
            cookie["maxAge"] = c.MaxAge
        }
        if c.Secure {
            cookie["secure"] = true
        }
        if c.HttpOnly {
            cookie["httpOnly"] = true
        }
        switch c.SameSite {
        case nhttp.SameSiteDefaultMode:
            cookie["sameSite"] = "Default"
        case nhttp.SameSiteLaxMode:
            cookie["sameSite"] = "Lax"
        case nhttp.SameSiteStrictMode:
            cookie["sameSite"] = "Strict"
        case nhttp.SameSiteNoneMode:
            cookie["sameSite"] = "None"
        }

        result = append(result, cookie)
    }

    if len(result) == 0 {
        return nil
    }
    return result
}

func buildResponsePayload(requestID string, resp Response) map[string]interface{} {
    headers := resp.Headers
    if headers == nil {
        headers = map[string]string{}
    }

    // Check if body is valid UTF-8 for msgpack string compatibility
    // If not valid UTF-8 (binary data), use empty string and rely on BodyBytes
    bodyStr := resp.Body
    if !utf8.ValidString(bodyStr) {
        bodyStr = "" // Binary data - Python should use BodyBytes instead
    }

    payload := map[string]interface{}{
        "RequestID": requestID,
        "Status":    resp.Status,
        "Body":      bodyStr,
        "Headers":   headers,
        "FinalUrl":  resp.FinalUrl,
    }

    if len(resp.BodyBytes) > 0 {
        payload["BodyBytes"] = resp.BodyBytes
    }

    if cookies := convertCookies(resp.Cookies); cookies != nil {
        payload["Cookies"] = cookies
    } else {
        payload["Cookies"] = []map[string]interface{}{}
    }

    return payload
}

func buildErrorPayload(requestID, message string) map[string]interface{} {
    return map[string]interface{}{
        "RequestID": requestID,
        "Status":    0,
        "Body":      message,
        "Headers":   map[string]string{},
        "FinalUrl":  "",
        "Cookies":   []map[string]interface{}{},
    }
}

func marshalPayload(payload map[string]interface{}) *C.char {
    // Use msgpack for binary serialization (3-5x faster than JSON)
    bytes, err := msgpack.Marshal(payload)
    if err != nil {
        log.Printf("cycletls: failed to marshal payload: %v", err)
        fallback := map[string]interface{}{
            "RequestID": payload["RequestID"],
            "Status":    0,
            "Body":      "failed to encode response",
            "Headers":   map[string]string{},
            "FinalUrl":  "",
            "Cookies":   []map[string]interface{}{},
        }
        bytes, _ = msgpack.Marshal(fallback)
    }
    // Base64 encode to avoid null bytes in C string
    b64 := base64.StdEncoding.EncodeToString(bytes)
    return C.CString(b64)
}

// Removed worker pool - using direct goroutine spawn for simplicity

// safeDo recovers only panics raised in the goroutine executing Do.
type requestDoer interface {
	Do(string, Options, string) (Response, error)
}

func safeDo(client requestDoer, request cycleTLSRequest) (resp Response, err error) {
	defer func() {
		if p := recover(); p != nil {
			err = fmt.Errorf("cycletls: internal panic: %v\n%s", p, debug.Stack())
		}
	}()
	return client.Do(request.Options.URL, request.Options, request.Options.Method)
}

func notifyCompletion(file *os.File) {
	if file == nil {
		return
	}
	defer file.Close()
	_, _ = file.Write([]byte{1})
}
func registerAsyncResult(state *asyncResultWithNotify, legacy bool) uintptr {
	id := uintptr(cgo.NewHandle(state))
	if legacy {
		asyncResults.Store(id, state)
	} else {
		asyncNotifyResults.Store(id, state)
	}
	return id
}
func findAsyncResult(id uintptr) (*asyncResultWithNotify, *sync.Map) {
	for _, store := range []*sync.Map{&asyncResults, &asyncNotifyResults} {
		if value, ok := store.Load(id); ok {
			return value.(*asyncResultWithNotify), store
		}
	}
	return nil, nil
}
func completeAsyncResult(state *asyncResultWithNotify, data []byte) {
	state.mu.Lock()
	defer state.mu.Unlock()
	if state.finished {
		return
	}
	state.result, state.ready = data, true
}
func takeAsyncResult(id uintptr) ([]byte, bool) {
	state, store := findAsyncResult(id)
	if state == nil {
		return nil, false
	}
	state.mu.Lock()
	defer state.mu.Unlock()
	if state.finished || !state.ready {
		return nil, false
	}
	state.finished = true
	store.Delete(id)
	cgo.Handle(id).Delete()
	data := state.result
	state.result = nil
	return data, true
}
func cancelAsync(id uintptr) {
	state, store := findAsyncResult(id)
	if state == nil {
		return
	}
	state.mu.Lock()
	defer state.mu.Unlock()
	if state.finished {
		return
	}
	state.finished = true
	state.result = nil
	store.Delete(id)
	cgo.Handle(id).Delete()
	// CycleTLS.Do has no context parameter. The network operation finishes
	// naturally under its existing timeout; its result is discarded above.
}

//export cancelAsyncRequest
func cancelAsyncRequest(handlePtr C.uintptr_t) { cancelAsync(uintptr(handlePtr)) }

func executeAsync(request cycleTLSRequest, legacy bool, notify *os.File) uintptr {
	state := &asyncResultWithNotify{requestID: request.RequestID}
	id := registerAsyncResult(state, legacy)
	go func() {
		if notify != nil {
			defer notifyCompletion(notify)
		}
		resp, err := safeDo(getFFIClient(), request)
		var payload map[string]interface{}
		if err != nil {
			payload = buildErrorPayload(request.RequestID, err.Error())
		} else {
			payload = buildResponsePayload(request.RequestID, resp)
		}
		result, marshalErr := msgpack.Marshal(payload)
		if marshalErr != nil {
			result, _ = msgpack.Marshal(buildErrorPayload(request.RequestID, "failed to marshal response"))
		}
		completeAsyncResult(state, result)
	}()
	return id
}

//export getRequest
func getRequest(data *C.char) *C.char {
    if data == nil {
        return marshalPayload(buildErrorPayload("", "empty payload"))
    }

    // Decode base64 to get msgpack data
    b64str := C.GoString(data)
    msgpackData, err := base64.StdEncoding.DecodeString(b64str)
    if err != nil {
        return marshalPayload(buildErrorPayload("", "invalid base64: "+err.Error()))
    }

    request := cycleTLSRequest{}
    // Use msgpack for binary deserialization (3-5x faster than JSON)
    if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
        return marshalPayload(buildErrorPayload("", "invalid payload: "+err.Error()))
    }

    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }

    request.Options.Method = normalizeMethod(request.Options.Method)

    // Use goroutine-based execution to allow Go scheduler to handle concurrency
    // This ensures sync calls benefit from goroutine parallelism when called from multiple threads
    resultCh := make(chan *C.char, 1)

    go func() {
        client := getFFIClient()
		resp, err := safeDo(client, request)
        if err != nil {
            log.Printf("cycletls: request failed: %v", err)
            resultCh <- marshalPayload(buildErrorPayload(request.RequestID, err.Error()))
        } else {
            resultCh <- marshalPayload(buildResponsePayload(request.RequestID, resp))
        }
    }()

    // Block until result is ready (maintains sync semantics)
    return <-resultCh
}

//export submitRequestAsync
func submitRequestAsync(data *C.char) C.uintptr_t {
    if data == nil {
        return 0
    }
	request := cycleTLSRequest{}
	msgpackData, err := base64.StdEncoding.DecodeString(C.GoString(data))
    if err != nil {
        return 0
    }
    if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
        return 0
    }
    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }
    request.Options.Method = normalizeMethod(request.Options.Method)
	return C.uintptr_t(executeAsync(request, true, nil))
}

//export checkRequestAsync
func checkRequestAsync(handlePtr C.uintptr_t) *C.char {
	result, ok := takeAsyncResult(uintptr(handlePtr))
    if !ok {
        return nil
    }
	return C.CString(base64.StdEncoding.EncodeToString(result))
}

// ============================================================================
// Callback-Based Async FFI Functions (Zero Polling)
// ============================================================================
// These functions use pipe notification instead of polling, reducing FFI calls
// from 10-200 per request to exactly 2 (submit + get result).

// asyncResultWithNotify stores both the result and notification state
type asyncResultWithNotify struct {
    result    []byte // Raw msgpack bytes
    requestID string
    ready     bool
	finished  bool
    mu        sync.Mutex
}

// asyncNotifyResults stores results for callback-based async requests
var asyncNotifyResults sync.Map // map[uintptr]*asyncResultWithNotify

//export submitRequestAsyncWithNotify
func submitRequestAsyncWithNotify(data *C.char, dataLen C.int, notifyFD C.int) C.uintptr_t {
	if data == nil {
        return 0
    }
	request := cycleTLSRequest{}
	if dataLen <= 0 {
		return 0
	}
    msgpackData := C.GoBytes(unsafe.Pointer(data), dataLen)
    if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
        return 0
    }
    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }
    request.Options.Method = normalizeMethod(request.Options.Method)
	owned, err := duplicateNotifyFD(int(notifyFD))
	if err != nil {
		return 0
    }
	return C.uintptr_t(executeAsync(request, false, owned))
}

//export getAsyncResult
func getAsyncResult(handlePtr C.uintptr_t, outLen *C.int) *C.char {
	if outLen == nil {
        return nil
    }
	*outLen = 0
	result, ok := takeAsyncResult(uintptr(handlePtr))
    if !ok {
        return nil
    }
	*outLen = C.int(len(result))
	return C.CString(string(result))
}

//export freeString
func freeString(ptr *C.char) {
    if ptr != nil {
        C.free(unsafe.Pointer(ptr))
    }
}

//export sendBatchRequest
func sendBatchRequest(data *C.char) *C.char {
    if data == nil {
        return marshalPayload(buildErrorPayload("", "empty payload"))
    }

    // Decode base64 to get msgpack data
    b64str := C.GoString(data)
    msgpackData, err := base64.StdEncoding.DecodeString(b64str)
    if err != nil {
        return marshalPayload(buildErrorPayload("", "invalid base64: "+err.Error()))
    }

    var batch BatchRequest
    if err := msgpack.Unmarshal(msgpackData, &batch); err != nil {
        return marshalPayload(buildErrorPayload("", "invalid batch payload: "+err.Error()))
    }

    // Handle empty batch case
    if len(batch.Requests) == 0 {
        batchResp := BatchResponse{Responses: []map[string]interface{}{}}
        bytes, _ := msgpack.Marshal(batchResp)
        b64 := base64.StdEncoding.EncodeToString(bytes)
        return C.CString(b64)
    }

    // Process all requests in parallel using goroutines
    responses := make([]map[string]interface{}, len(batch.Requests))
    var wg sync.WaitGroup

    for i, req := range batch.Requests {
        wg.Add(1)
        go func(idx int, r cycleTLSRequest) {
            defer wg.Done()

            if r.RequestID == "" {
                r.RequestID = fmt.Sprintf("batch_%d", idx)
            }
            r.Options.Method = normalizeMethod(r.Options.Method)

            client := getFFIClient()
			resp, err := safeDo(client, r)
            if err != nil {
                responses[idx] = buildErrorPayload(r.RequestID, err.Error())
            } else {
                responses[idx] = buildResponsePayload(r.RequestID, resp)
            }
        }(i, req)
    }
    wg.Wait()

    // Marshal batch response
    batchResp := BatchResponse{Responses: responses}
    bytes, err := msgpack.Marshal(batchResp)
    if err != nil {
        return marshalPayload(buildErrorPayload("", "failed to marshal batch response: "+err.Error()))
    }
    b64 := base64.StdEncoding.EncodeToString(bytes)
    return C.CString(b64)
}

// ============================================================================
// WebSocket FFI Functions
// ============================================================================

// wsConnectOptions holds WebSocket connection options
type wsConnectOptions struct {
    URL       string            `msgpack:"url"`
    Headers   map[string]string `msgpack:"headers"`
    JA3       string            `msgpack:"ja3"`
    UserAgent string            `msgpack:"userAgent"`
    Proxy     string            `msgpack:"proxy"`
    Timeout   int               `msgpack:"timeout"`
}

//export wsConnect
func wsConnect(data *C.char) C.uintptr_t {
    if data == nil {
        return 0
    }

    // Decode options
    b64str := C.GoString(data)
    msgpackData, err := base64.StdEncoding.DecodeString(b64str)
    if err != nil {
        log.Printf("cycletls: wsConnect invalid base64: %v", err)
        return 0
    }

    var options wsConnectOptions
    if err := msgpack.Unmarshal(msgpackData, &options); err != nil {
        log.Printf("cycletls: wsConnect invalid options: %v", err)
        return 0
    }

    // Build HTTP headers
    headers := nhttp.Header{}
    for k, v := range options.Headers {
        headers.Set(k, v)
    }
    if options.UserAgent != "" {
        headers.Set("User-Agent", options.UserAgent)
    }

    // Create WebSocket client with TLS fingerprinting
    // Note: TLS config is nil - WebSocket uses standard TLS for now
    wsClient := NewWebSocketClient(nil, headers)

    // Connect
    conn, _, err := wsClient.Connect(options.URL)
    if err != nil {
        log.Printf("cycletls: wsConnect failed: %v", err)
        return 0
    }

    // Store connection
    handle := cgo.NewHandle(conn)
    handleID := uintptr(handle)
    wsConnections.Store(handleID, conn)

    log.Printf("cycletls: WebSocket connected to %s (handle=%d)", options.URL, handleID)
    return C.uintptr_t(handleID)
}

//export wsSend
func wsSend(handlePtr C.uintptr_t, msgType C.int, data *C.char, dataLen C.int) C.int {
    if handlePtr == 0 {
        return -1
    }

    handleID := uintptr(handlePtr)
    val, ok := wsConnections.Load(handleID)
    if !ok {
        return -2
    }

    conn := val.(*websocket.Conn)

    // Decode base64 data
    b64str := C.GoString(data)
    msgData, err := base64.StdEncoding.DecodeString(b64str)
    if err != nil {
        log.Printf("cycletls: wsSend invalid base64: %v", err)
        return -3
    }

    // Send message
    err = conn.WriteMessage(int(msgType), msgData)
    if err != nil {
        log.Printf("cycletls: wsSend failed: %v", err)
        return -4
    }

    return 0
}

//export wsReceive
func wsReceive(handlePtr C.uintptr_t) *C.char {
    if handlePtr == 0 {
        return nil
    }

    handleID := uintptr(handlePtr)
    val, ok := wsConnections.Load(handleID)
    if !ok {
        return nil
    }

    conn := val.(*websocket.Conn)

    // Read message
    msgType, msgData, err := conn.ReadMessage()
    if err != nil {
        log.Printf("cycletls: wsReceive failed: %v", err)
        // Return error response
        payload := map[string]interface{}{
            "error": err.Error(),
        }
        return marshalPayload(payload)
    }

    // Build response
    payload := map[string]interface{}{
        "type": msgType,
    }

    // For binary messages, base64 encode the data
    if msgType == websocket.BinaryMessage {
        payload["data"] = base64.StdEncoding.EncodeToString(msgData)
    } else {
        payload["data"] = string(msgData)
    }

    return marshalPayload(payload)
}

//export wsClose
func wsClose(handlePtr C.uintptr_t) {
    if handlePtr == 0 {
        return
    }

    handleID := uintptr(handlePtr)
    val, ok := wsConnections.Load(handleID)
    if !ok {
        return
    }

    conn := val.(*websocket.Conn)

    // Send close message
    conn.WriteMessage(websocket.CloseMessage,
        websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
    conn.Close()

    // Cleanup
    wsConnections.Delete(handleID)
    handle := cgo.Handle(handlePtr)
    handle.Delete()

    log.Printf("cycletls: WebSocket closed (handle=%d)", handleID)
}

// ============================================================================
// SSE (Server-Sent Events) FFI Functions
// ============================================================================

// sseConnectOptions holds SSE connection options
type sseConnectOptions struct {
    URL       string            `msgpack:"url"`
    Headers   map[string]string `msgpack:"headers"`
    JA3       string            `msgpack:"ja3"`
    UserAgent string            `msgpack:"userAgent"`
    Proxy     string            `msgpack:"proxy"`
    Timeout   int               `msgpack:"timeout"`
}

//export sseConnect
func sseConnect(data *C.char) C.uintptr_t {
    if data == nil {
        return 0
    }

    // Decode options
    b64str := C.GoString(data)
    msgpackData, err := base64.StdEncoding.DecodeString(b64str)
    if err != nil {
        log.Printf("cycletls: sseConnect invalid base64: %v", err)
        return 0
    }

    var options sseConnectOptions
    if err := msgpack.Unmarshal(msgpackData, &options); err != nil {
        log.Printf("cycletls: sseConnect invalid options: %v", err)
        return 0
    }

    // Build HTTP headers (use fhttp.Header for SSE compatibility)
    headers := fhttp.Header{}
    for k, v := range options.Headers {
        headers.Set(k, v)
    }
    if options.UserAgent != "" {
        headers.Set("User-Agent", options.UserAgent)
    }

    // Create SSE client (nil client uses fhttp.DefaultClient)
    sseClient := NewSSEClient(nil, headers)

    // Connect with timeout context
    timeout := time.Duration(options.Timeout) * time.Second
    if timeout == 0 {
        timeout = 30 * time.Second
    }
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    sseResp, err := sseClient.Connect(ctx, options.URL)
    if err != nil {
        log.Printf("cycletls: sseConnect failed: %v", err)
        return 0
    }

    // Store connection
    handle := cgo.NewHandle(sseResp)
    handleID := uintptr(handle)
    sseConnections.Store(handleID, sseResp)

    log.Printf("cycletls: SSE connected to %s (handle=%d)", options.URL, handleID)
    return C.uintptr_t(handleID)
}

//export sseNextEvent
func sseNextEvent(handlePtr C.uintptr_t) *C.char {
    if handlePtr == 0 {
        return nil
    }

    handleID := uintptr(handlePtr)
    val, ok := sseConnections.Load(handleID)
    if !ok {
        return nil
    }

    sseResp := val.(*SSEResponse)

    // Read next event
    event, err := sseResp.NextEvent()
    if err != nil {
        log.Printf("cycletls: sseNextEvent error: %v", err)
        // Return error or EOF
        payload := map[string]interface{}{
            "error": err.Error(),
            "eof":   true,
        }
        return marshalPayload(payload)
    }

    if event == nil {
        // End of stream
        payload := map[string]interface{}{
            "eof": true,
        }
        return marshalPayload(payload)
    }

    // Build response
    payload := map[string]interface{}{
        "data":  event.Data,
        "event": event.Event,
    }
    if event.ID != "" {
        payload["id"] = event.ID
    }
    if event.Retry != 0 {
        payload["retry"] = event.Retry
    }

    return marshalPayload(payload)
}

//export sseClose
func sseClose(handlePtr C.uintptr_t) {
    if handlePtr == 0 {
        return
    }

    handleID := uintptr(handlePtr)
    val, ok := sseConnections.Load(handleID)
    if !ok {
        return
    }

    sseResp := val.(*SSEResponse)
    sseResp.Close()

    // Cleanup
    sseConnections.Delete(handleID)
    handle := cgo.Handle(handlePtr)
    handle.Delete()

    log.Printf("cycletls: SSE closed (handle=%d)", handleID)
}

// ============================================================================
// Zero-Copy FFI Functions
// ============================================================================
// These functions accept raw msgpack bytes (no base64 encoding) for better
// performance. They eliminate the ~33% size overhead and CPU cycles of base64.

// marshalPayloadZeroCopy returns raw msgpack bytes and sets the output length
func marshalPayloadZeroCopy(payload map[string]interface{}, outLen *C.int) *C.char {
    bytes, err := msgpack.Marshal(payload)
    if err != nil {
        log.Printf("cycletls: failed to marshal payload: %v", err)
        fallback := map[string]interface{}{
            "RequestID": payload["RequestID"],
            "Status":    0,
            "Body":      "failed to encode response",
            "Headers":   map[string]string{},
            "FinalUrl":  "",
            "Cookies":   []map[string]interface{}{},
        }
        bytes, _ = msgpack.Marshal(fallback)
    }
    *outLen = C.int(len(bytes))
    // Copy bytes to C memory (caller must free with freeString)
    return C.CString(string(bytes))
}

//export getRequestZeroCopy
func getRequestZeroCopy(data *C.char, dataLen C.int, outLen *C.int) *C.char {
    if data == nil || dataLen <= 0 {
        return marshalPayloadZeroCopy(buildErrorPayload("", "empty payload"), outLen)
    }

    // Convert C bytes to Go slice without base64 decoding
    // Use C.GoBytes to copy the exact number of bytes (handles null bytes correctly)
    msgpackData := C.GoBytes(unsafe.Pointer(data), dataLen)

    request := cycleTLSRequest{}
    if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
        return marshalPayloadZeroCopy(buildErrorPayload("", "invalid payload: "+err.Error()), outLen)
    }

    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }

    request.Options.Method = normalizeMethod(request.Options.Method)

    client := getFFIClient()
	resp, err := safeDo(client, request)
    if err != nil {
        log.Printf("cycletls: request failed: %v", err)
        return marshalPayloadZeroCopy(buildErrorPayload(request.RequestID, err.Error()), outLen)
    }
    return marshalPayloadZeroCopy(buildResponsePayload(request.RequestID, resp), outLen)
}

//export submitRequestAsyncZeroCopy
func submitRequestAsyncZeroCopy(data *C.char, dataLen C.int) C.uintptr_t {
	if data == nil {
        return 0
    }
    request := cycleTLSRequest{}
	if dataLen <= 0 {
        return 0
    }
	msgpackData := C.GoBytes(unsafe.Pointer(data), dataLen)
	if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
		return 0
	}
    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }
    request.Options.Method = normalizeMethod(request.Options.Method)
	return C.uintptr_t(executeAsync(request, false, nil))
}

//export getAsyncResultZeroCopy
func getAsyncResultZeroCopy(handlePtr C.uintptr_t, outLen *C.int) *C.char {
	if outLen == nil {
        return nil
    }
	*outLen = 0
	result, ok := takeAsyncResult(uintptr(handlePtr))
    if !ok {
        return nil
    }
	*outLen = C.int(len(result))
	return C.CString(string(result))
}

//export freeMemory
func freeMemory(ptr *C.char) {
    if ptr != nil {
        C.free(unsafe.Pointer(ptr))
    }
}

//export sendBatchRequestZeroCopy
func sendBatchRequestZeroCopy(data *C.char, dataLen C.int, outLen *C.int) *C.char {
    if data == nil || dataLen <= 0 {
        return marshalPayloadZeroCopy(buildErrorPayload("", "empty payload"), outLen)
    }

    // Convert C bytes to Go slice without base64 decoding
    msgpackData := C.GoBytes(unsafe.Pointer(data), dataLen)

    var batch BatchRequest
    if err := msgpack.Unmarshal(msgpackData, &batch); err != nil {
        return marshalPayloadZeroCopy(buildErrorPayload("", "invalid batch payload: "+err.Error()), outLen)
    }

    // Handle empty batch case
    if len(batch.Requests) == 0 {
        batchResp := BatchResponse{Responses: []map[string]interface{}{}}
        bytes, _ := msgpack.Marshal(batchResp)
        *outLen = C.int(len(bytes))
        return C.CString(string(bytes))
    }

    // Process all requests in parallel using goroutines
    responses := make([]map[string]interface{}, len(batch.Requests))
    var wg sync.WaitGroup

    for i, req := range batch.Requests {
        wg.Add(1)
        go func(idx int, r cycleTLSRequest) {
            defer wg.Done()

            if r.RequestID == "" {
                r.RequestID = fmt.Sprintf("batch_%d", idx)
            }
            r.Options.Method = normalizeMethod(r.Options.Method)

            client := getFFIClient()
			resp, err := safeDo(client, r)
            if err != nil {
                responses[idx] = buildErrorPayload(r.RequestID, err.Error())
            } else {
                responses[idx] = buildResponsePayload(r.RequestID, resp)
            }
        }(i, req)
    }
    wg.Wait()

    // Marshal batch response (raw msgpack, no base64)
    batchResp := BatchResponse{Responses: responses}
    bytes, err := msgpack.Marshal(batchResp)
    if err != nil {
        return marshalPayloadZeroCopy(buildErrorPayload("", "failed to marshal batch response: "+err.Error()), outLen)
    }
    *outLen = C.int(len(bytes))
    return C.CString(string(bytes))
}
