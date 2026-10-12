//go:build windows

package main

import "testing"

func TestFFINotifyUnsupportedOnWindows(t *testing.T) {
	file, err := duplicateNotifyFD(3)
	if file != nil || err == nil {
		t.Fatalf("expected unsupported notification, got %v %v", file, err)
	}
}
