//go:build windows

package main

import (
	"errors"
	"os"
)

func duplicateNotifyFD(fd int) (*os.File, error) {
	return nil, errors.New("cycletls: pipe notification is unsupported on Windows; use async polling")
}
