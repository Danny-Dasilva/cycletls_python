package main

import (
	"fmt"
	"strings"

	http2 "github.com/Danny-Dasilva/fhttp/http2"
)

// HTTP2Fingerprint represents an HTTP/2 client fingerprint.
// The canonical string format is:
//
//	SETTINGS|WINDOW_UPDATE|PRIORITY_FRAMES|PSEUDO_HEADERS
//
// Example Firefox:
//
//	1:65536,4:131072,5:16384|12517377|3:0:0:201,5:0:0:1,7:0:0:1,9:0:7:1,11:0:3:1,13:0:0:241|m,p,a,s
//
// Example Chrome:
//
//	1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p
type HTTP2Fingerprint struct {
	Settings          []http2.Setting
	ConnectionFlow    int
	PriorityFrames    []http2.PriorityFrame
	HeaderPriority    *http2.PriorityParam
	HeaderTableSize   uint32
	InitialWindowSize uint32
	MaxHeaderListSize uint32
	PriorityOrder     []string
}

// NewHTTP2Fingerprint creates a new HTTP2Fingerprint from a canonical
// HTTP/2 fingerprint string.
//
// The four pipe-separated parts are:
//  1. SETTINGS: a list of "id:value" pairs separated by ',' or ';'.
//  2. WINDOW_UPDATE: the connection-level flow-control increment.
//  3. PRIORITY_FRAMES: either "0" (none) or a comma-separated list of
//     "stream:exclusive:dep:weight" priority frames.
//  4. PSEUDO_HEADERS: the order of pseudo-headers, e.g. "m,p,a,s".
func NewHTTP2Fingerprint(fingerprint string) (*HTTP2Fingerprint, error) {
	parts := strings.Split(fingerprint, "|")
	if len(parts) != 4 {
		return nil, fmt.Errorf("invalid HTTP/2 fingerprint format: expected 4 parts, got %d", len(parts))
	}

	// Parse SETTINGS.
	settingsStr := parts[0]

	// Determine the separator used in the settings string.
	var settingsParts []string
	if strings.Contains(settingsStr, ";") && !strings.Contains(settingsStr, ",") {
		settingsParts = strings.Split(settingsStr, ";")
	} else {
		settingsParts = strings.Split(settingsStr, ",")
	}

	settings := make([]http2.Setting, 0, len(settingsParts))
	var headerTableSize, initialWindowSize, maxHeaderListSize uint32

	for _, setting := range settingsParts {
		if !strings.Contains(setting, ":") {
			return nil, fmt.Errorf("invalid setting format: %s - expected ID:VALUE", setting)
		}
		var id, val uint32
		if _, err := fmt.Sscanf(setting, "%d:%d", &id, &val); err != nil {
			return nil, fmt.Errorf("invalid setting format: %s", setting)
		}
		settings = append(settings, http2.Setting{ID: http2.SettingID(id), Val: val})

		switch http2.SettingID(id) {
		case http2.SettingHeaderTableSize:
			headerTableSize = val
		case http2.SettingInitialWindowSize:
			initialWindowSize = val
		case http2.SettingMaxHeaderListSize:
			maxHeaderListSize = val
		}
	}

	// Parse WINDOW_UPDATE value (connection-level flow-control increment).
	var connectionFlow uint32
	if _, err := fmt.Sscanf(parts[1], "%d", &connectionFlow); err != nil {
		return nil, fmt.Errorf("invalid WINDOW_UPDATE value: %s", parts[1])
	}

	// Parse PRIORITY frames.
	var priorityFrames []http2.PriorityFrame
	priorityStr := parts[2]
	if priorityStr != "" && priorityStr != "0" {
		priorityParts := strings.Split(priorityStr, ",")
		priorityFrames = make([]http2.PriorityFrame, 0, len(priorityParts))
		for _, p := range priorityParts {
			if p == "" {
				continue
			}
			var streamID, exclusive, dep, weight uint32
			n, err := fmt.Sscanf(p, "%d:%d:%d:%d", &streamID, &exclusive, &dep, &weight)
			if err != nil || n != 4 {
				return nil, fmt.Errorf("invalid priority frame format: %s", p)
			}
			// The fingerprint string uses wire display weights (1-256), but
			// fhttp stores the raw 8-bit value (0-255).
			if weight > 0 {
				weight--
			}
			priorityFrames = append(priorityFrames, http2.PriorityFrame{
				FrameHeader: http2.FrameHeader{StreamID: streamID},
				PriorityParam: http2.PriorityParam{
					StreamDep: dep,
					Exclusive: exclusive != 0,
					Weight:    uint8(weight),
				},
			})
		}
	}

	// Parse pseudo-header order.
	priorityOrder := strings.Split(parts[3], ",")

	return &HTTP2Fingerprint{
		Settings:          settings,
		ConnectionFlow:    int(connectionFlow),
		PriorityFrames:    priorityFrames,
		HeaderPriority:    nil,
		HeaderTableSize:   headerTableSize,
		InitialWindowSize: initialWindowSize,
		MaxHeaderListSize: maxHeaderListSize,
		PriorityOrder:     priorityOrder,
	}, nil
}

// String returns the canonical string representation of the HTTP/2 fingerprint.
func (f *HTTP2Fingerprint) String() string {
	settingStrs := make([]string, len(f.Settings))
	for i, setting := range f.Settings {
		settingStrs[i] = fmt.Sprintf("%d:%d", setting.ID, setting.Val)
	}
	settingsStr := strings.Join(settingStrs, ",")

	priorityStr := "0"
	if len(f.PriorityFrames) > 0 {
		parts := make([]string, 0, len(f.PriorityFrames))
		for _, pf := range f.PriorityFrames {
			exclusive := 0
			if pf.Exclusive {
				exclusive = 1
			}
			// Convert the raw 0-255 weight back to the wire display value (1-256).
			weight := uint32(pf.Weight) + 1
			parts = append(parts, fmt.Sprintf("%d:%d:%d:%d", pf.StreamID, exclusive, pf.StreamDep, weight))
		}
		priorityStr = strings.Join(parts, ",")
	}

	pseudoStr := strings.Join(f.PriorityOrder, ",")

	return fmt.Sprintf("%s|%d|%s|%s", settingsStr, f.ConnectionFlow, priorityStr, pseudoStr)
}

// Navigator guesses the underlying browser family from the fingerprint.
// This is used to drive fhttp defaults that are still required when a
// fingerprint omits explicit priority frames.
func (f *HTTP2Fingerprint) Navigator() string {
	if len(f.PriorityFrames) > 0 {
		return firefox
	}
	for _, s := range f.Settings {
		if s.ID == http2.SettingMaxConcurrentStreams || s.ID == http2.SettingMaxHeaderListSize {
			return chrome
		}
	}
	return chrome
}

// PseudoHeaderOrder maps the fingerprint's pseudo-header order letters to
// actual HTTP/2 pseudo-header names, e.g. "m,p,a,s" -> [":method", ":path", ":authority", ":scheme"].
func (f *HTTP2Fingerprint) PseudoHeaderOrder() []string {
	if len(f.PriorityOrder) == 0 {
		return nil
	}
	order := make([]string, 0, len(f.PriorityOrder))
	for _, c := range f.PriorityOrder {
		switch c {
		case "m":
			order = append(order, ":method")
		case "a":
			order = append(order, ":authority")
		case "s":
			order = append(order, ":scheme")
		case "p":
			order = append(order, ":path")
		}
	}
	return order
}

// Apply configures the HTTP/2 transport with the specified fingerprint.
func (f *HTTP2Fingerprint) Apply(conn *http2.Transport) {
	conn.HTTP2Settings = &http2.HTTP2Settings{
		Settings:       f.Settings,
		ConnectionFlow: f.ConnectionFlow,
		PriorityFrames: f.PriorityFrames,
		HeaderPriority: f.HeaderPriority,
	}

	// These are used by fhttp for local flow control and HPACK state. They
	// may be overwritten by Transport.AutoUpdate depending on the Navigator,
	// but we set them here so they match the advertised SETTINGS when possible.
	if f.HeaderTableSize != 0 {
		conn.HeaderTableSize = f.HeaderTableSize
	}
	if f.InitialWindowSize != 0 {
		conn.InitialWindowSize = f.InitialWindowSize
	}
	if f.MaxHeaderListSize != 0 {
		conn.MaxHeaderListSize = f.MaxHeaderListSize
	}
}
