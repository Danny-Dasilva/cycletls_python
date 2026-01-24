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
    "runtime/cgo"
    "strings"
    "sync"
    "time"
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
    asyncResults sync.Map // map[uintptr]chan *asyncResult

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

    payload := map[string]interface{}{
        "RequestID": requestID,
        "Status":    resp.Status,
        "Body":      resp.Body,
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
        resp, err := client.Do(request.Options.URL, request.Options, request.Options.Method)
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

    // Decode base64 to get msgpack data
    b64str := C.GoString(data)
    msgpackData, err := base64.StdEncoding.DecodeString(b64str)
    if err != nil {
        return 0
    }

    request := cycleTLSRequest{}
    if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
        return 0
    }

    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }

    request.Options.Method = normalizeMethod(request.Options.Method)

    // Create result channel (buffered to prevent goroutine leak)
    resultCh := make(chan *C.char, 1)

    // Create handle using cgo.Handle (safe pointer passing)
    handle := cgo.NewHandle(resultCh)

    // Store handle for later retrieval
    handleID := uintptr(handle)
    asyncResults.Store(handleID, resultCh)

    // Spawn goroutine directly (no worker pool)
    go func() {
        client := getFFIClient()

        // Execute HTTP request
        resp, err := client.Do(request.Options.URL, request.Options, request.Options.Method)
        if err != nil {
            resultCh <- marshalPayload(buildErrorPayload(request.RequestID, err.Error()))
        } else {
            resultCh <- marshalPayload(buildResponsePayload(request.RequestID, resp))
        }
    }()

    return C.uintptr_t(handleID)
}

//export checkRequestAsync
func checkRequestAsync(handlePtr C.uintptr_t) *C.char {
    if handlePtr == 0 {
        return nil
    }

    handleID := uintptr(handlePtr)

    // Retrieve channel from store
    val, ok := asyncResults.Load(handleID)
    if !ok {
        return nil
    }

    resultCh := val.(chan *C.char)

    // Non-blocking check
    select {
    case result := <-resultCh:
        // Result ready - cleanup and return
        asyncResults.Delete(handleID)
        handle := cgo.Handle(handlePtr)
        handle.Delete()

        return result

    default:
        // Not ready yet
        return nil
    }
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
    mu        sync.Mutex
}

// asyncNotifyResults stores results for callback-based async requests
var asyncNotifyResults sync.Map // map[uintptr]*asyncResultWithNotify

//export submitRequestAsyncWithNotify
func submitRequestAsyncWithNotify(data *C.char, dataLen C.int, notifyFD C.int) C.uintptr_t {
    if data == nil || dataLen <= 0 {
        return 0
    }

    // Convert C bytes to Go slice (zero-copy style)
    msgpackData := C.GoBytes(unsafe.Pointer(data), dataLen)

    request := cycleTLSRequest{}
    if err := msgpack.Unmarshal(msgpackData, &request); err != nil {
        return 0
    }

    if request.RequestID == "" {
        request.RequestID = "cycleTLSRequest"
    }

    request.Options.Method = normalizeMethod(request.Options.Method)

    // Create result storage
    resultStore := &asyncResultWithNotify{
        requestID: request.RequestID,
        ready:     false,
    }

    // Create handle using cgo.Handle
    handle := cgo.NewHandle(resultStore)
    handleID := uintptr(handle)
    asyncNotifyResults.Store(handleID, resultStore)

    // Spawn goroutine to execute request
    go func() {
        client := getFFIClient()

        var payload map[string]interface{}
        resp, err := client.Do(request.Options.URL, request.Options, request.Options.Method)
        if err != nil {
            payload = buildErrorPayload(request.RequestID, err.Error())
        } else {
            payload = buildResponsePayload(request.RequestID, resp)
        }

        // Marshal result to msgpack
        resultBytes, marshalErr := msgpack.Marshal(payload)
        if marshalErr != nil {
            // Fallback error response
            fallback := buildErrorPayload(request.RequestID, "failed to marshal response")
            resultBytes, _ = msgpack.Marshal(fallback)
        }

        // Store result
        resultStore.mu.Lock()
        resultStore.result = resultBytes
        resultStore.ready = true
        resultStore.mu.Unlock()

        // Notify Python by writing to pipe
        // Write a single byte to signal completion
        var notifyByte [1]byte
        notifyByte[0] = 1
        C.write(notifyFD, unsafe.Pointer(&notifyByte[0]), 1)
    }()

    return C.uintptr_t(handleID)
}

//export getAsyncResult
func getAsyncResult(handlePtr C.uintptr_t, outLen *C.int) *C.char {
    if handlePtr == 0 {
        return nil
    }

    handleID := uintptr(handlePtr)

    // Retrieve result from store
    val, ok := asyncNotifyResults.Load(handleID)
    if !ok {
        return nil
    }

    resultStore := val.(*asyncResultWithNotify)

    // Check if ready (should always be true if pipe was written)
    resultStore.mu.Lock()
    if !resultStore.ready {
        resultStore.mu.Unlock()
        return nil
    }
    resultBytes := resultStore.result
    resultStore.mu.Unlock()

    // Cleanup
    asyncNotifyResults.Delete(handleID)
    handle := cgo.Handle(handlePtr)
    handle.Delete()

    // Return result (caller must free with freeString)
    *outLen = C.int(len(resultBytes))
    return C.CString(string(resultBytes))
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
            resp, err := client.Do(r.Options.URL, r.Options, r.Options.Method)
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

    // Use goroutine-based execution
    resultCh := make(chan map[string]interface{}, 1)

    go func() {
        client := getFFIClient()
        resp, err := client.Do(request.Options.URL, request.Options, request.Options.Method)
        if err != nil {
            log.Printf("cycletls: request failed: %v", err)
            resultCh <- buildErrorPayload(request.RequestID, err.Error())
        } else {
            resultCh <- buildResponsePayload(request.RequestID, resp)
        }
    }()

    // Block until result is ready
    payload := <-resultCh
    return marshalPayloadZeroCopy(payload, outLen)
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
            resp, err := client.Do(r.Options.URL, r.Options, r.Options.Method)
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

