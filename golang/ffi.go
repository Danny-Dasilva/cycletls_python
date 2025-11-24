package main

/*
#include <stdlib.h>
#include <stdint.h>
*/
import "C"

import (
    "encoding/base64"
    "log"
    nhttp "net/http"
    "runtime/cgo"
    "strings"
    "sync"
    "time"
    "unsafe"

    "github.com/vmihailenco/msgpack/v5"
)

var (
    ffiClientOnce sync.Once
    ffiClient     *CycleTLS

    // Async result store for non-blocking requests
    asyncResults sync.Map // map[uintptr]chan *asyncResult
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

//export freeString
func freeString(ptr *C.char) {
    if ptr != nil {
        C.free(unsafe.Pointer(ptr))
    }
}

