//go:build !windows

package main

import (
	"os"

	"golang.org/x/sys/unix"
)

// Duplicate synchronously while the caller still owns its descriptor. Keep the
// duplicate above stderr: Go's os.File write handles EPIPE without killing the host.
func duplicateNotifyFD(fd int) (*os.File, error) {
	duplicate, err := unix.FcntlInt(uintptr(fd), unix.F_DUPFD_CLOEXEC, 3)
	if err != nil {
		return nil, err
	}
	return os.NewFile(uintptr(duplicate), "cycletls-notify"), nil
}
