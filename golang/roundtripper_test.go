package main

import (
	"os"
	"regexp"
	"testing"

	http "github.com/Danny-Dasilva/fhttp"
)

// readRoundTripperSource loads roundtripper.go from disk so tests can pin
// invariants over the http.Transport literals without standing up a full
// HTTPS handshake harness.
func readRoundTripperSource(t *testing.T) string {
	t.Helper()
	b, err := os.ReadFile("roundtripper.go")
	if err != nil {
		t.Fatalf("failed to read roundtripper.go: %v", err)
	}
	return string(b)
}

// TestIdleConnTimeoutMatchesStdlibDefault asserts that every http.Transport
// constructed in roundtripper.go uses an IdleConnTimeout no larger than 60s.
//
// Background: peer servers fronted by nginx typically idle-close at
// ~65–75s. With cycletls's previous 90s timeout, requests #2+ would race
// the peer's keep-alive close, surfacing as bare "EOF" or
// "http: server closed idle connection". Lowering to ≤60s gives a 5–10s
// safety margin under the typical peer window and matches Go's net/http
// stdlib default.
//
// We assert by scanning the source: each `&http.Transport{...}` literal
// must declare `IdleConnTimeout: <=60s`. This is a layered defense — the
// http.Transport literals are deeply nested inside dialTLS / retry paths
// that require real network I/O to exercise, so a source-level assertion
// is the most reliable invariant we can pin without a network harness.
func TestIdleConnTimeoutMatchesStdlibDefault(t *testing.T) {
	src := readRoundTripperSource(t)

	// Match `IdleConnTimeout:       <number> * time.Second`
	re := regexp.MustCompile(`IdleConnTimeout:\s*(\d+)\s*\*\s*time\.Second`)
	matches := re.FindAllStringSubmatch(src, -1)

	if len(matches) == 0 {
		t.Fatalf("no IdleConnTimeout declarations found in roundtripper.go")
	}

	for _, m := range matches {
		got := m[1]
		// Allowed values: any integer ≤ 60.
		switch got {
		case "60", "30", "15":
			// fine
		default:
			t.Errorf("IdleConnTimeout: %s * time.Second exceeds the 60s safety bound; "+
				"see test comment for rationale", got)
		}
	}

	// And there must be at least 4 transports (HTTP scheme path + HTTPS HTTP1
	// path + 2 TLS retry paths). If the count drops, the test should fail
	// loudly because someone may have removed a path without adjusting this
	// invariant.
	if len(matches) < 4 {
		t.Errorf("expected at least 4 IdleConnTimeout declarations (HTTP scheme + HTTP/1 + 2 retry paths); got %d", len(matches))
	}
}

// TestNoStaleNinetySecondIdleConnTimeout is a focused regression: the literal
// "90 * time.Second" must not reappear next to IdleConnTimeout.
func TestNoStaleNinetySecondIdleConnTimeout(t *testing.T) {
	src := readRoundTripperSource(t)
	re := regexp.MustCompile(`IdleConnTimeout:\s*90\s*\*\s*time\.Second`)
	if re.MatchString(src) {
		t.Errorf("found IdleConnTimeout: 90 * time.Second — must be lowered to ≤60s to undercut peer keep-alives")
	}
}

// TestDisableKeepAlivesPropagatedFromBrowser asserts that the
// DisableKeepAlives field set on the Browser struct flows through
// newRoundTripper to the roundTripper instance.
//
// Background: when callers pass enable_connection_reuse=False from Python,
// getOrCreateClient bypasses the global client cache but historically did
// nothing else — every constructed http.Transport hardcoded
// DisableKeepAlives: false, so the inner transport still pooled connections
// across the same request. The flag was a half-fix.
//
// Wiring DisableKeepAlives onto Browser → roundTripper is the precondition
// for the http.Transport sites picking it up; this test pins that wiring.
func TestDisableKeepAlivesPropagatedFromBrowser(t *testing.T) {
	rt := newRoundTripper(Browser{DisableKeepAlives: true})

	rrt, ok := rt.(*roundTripper)
	if !ok {
		t.Fatalf("newRoundTripper returned unexpected concrete type %T", rt)
	}
	if !rrt.DisableKeepAlives {
		t.Fatalf("expected DisableKeepAlives=true on roundTripper; got false")
	}
}

// TestHTTP1TransportRespectsDisableKeepAlives constructs the HTTP-scheme
// transport (the simplest of the 4 paths — it does not require a real TLS
// handshake) and asserts that DisableKeepAlives is honoured.
func TestHTTP1TransportRespectsDisableKeepAlives(t *testing.T) {
	rt := newRoundTripper(Browser{DisableKeepAlives: true}).(*roundTripper)

	// The "http" scheme branch in getTransport constructs an http.Transport
	// directly without doing any I/O. We bypass dialTLS by going through the
	// branch under test.
	req, _ := http.NewRequest("GET", "http://example.test/", nil)
	if err := rt.getTransport(req, "example.test:80"); err != nil {
		t.Fatalf("getTransport(http) unexpectedly returned error: %v", err)
	}
	tr, ok := rt.cachedTransports["example.test:80"].(*http.Transport)
	if !ok {
		t.Fatalf("cachedTransport is not *http.Transport: %T", rt.cachedTransports["example.test:80"])
	}
	if !tr.DisableKeepAlives {
		t.Fatalf("expected DisableKeepAlives=true on the constructed http.Transport; got false")
	}
}

// TestSourcePropagatesDisableKeepAlivesToAllFourTransports pins the
// invariant that all 4 http.Transport literals in roundtripper.go carry a
// DisableKeepAlives entry that is bound to rt.DisableKeepAlives — not the
// hardcoded false. We assert this at the source level because three of the
// four constructions are nested inside dialTLS / TLS-retry paths that
// require live network I/O to reach.
func TestSourcePropagatesDisableKeepAlivesToAllFourTransports(t *testing.T) {
	src := readRoundTripperSource(t)

	// All DisableKeepAlives lines under an http.Transport literal should
	// reference rt.DisableKeepAlives (not the literal `false`).
	hardcoded := regexp.MustCompile(`DisableKeepAlives:\s*false\b`)
	if hardcoded.MatchString(src) {
		t.Errorf("found hardcoded DisableKeepAlives: false — must be bound to rt.DisableKeepAlives so enable_connection_reuse=False propagates through")
	}

	// And there must be at least 4 references to rt.DisableKeepAlives, one
	// per http.Transport literal.
	bound := regexp.MustCompile(`DisableKeepAlives:\s*rt\.DisableKeepAlives\b`)
	if got := len(bound.FindAllString(src, -1)); got < 4 {
		t.Errorf("expected at least 4 DisableKeepAlives: rt.DisableKeepAlives bindings (HTTP scheme + HTTP/1 + 2 retry paths); got %d", got)
	}
}

// (sanity check) the http import is referenced so that gofmt/imports does
// not strip it if other tests are removed in the future.
var _ = http.MethodGet
