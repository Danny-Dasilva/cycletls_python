//go:build !windows

package main

import (
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"testing"
)

type panickingDoer struct{}

func (panickingDoer) Do(string, Options, string) (Response, error) { panic("regression panic") }

func TestFFISafeDoRecovers(t *testing.T) {
	_, err := safeDo(panickingDoer{}, cycleTLSRequest{})
	if err == nil || !strings.Contains(err.Error(), "regression panic") {
		t.Fatalf("panic error: %v", err)
	}
}

func TestFFINotifyOwnsDescriptor(t *testing.T) {
	reader, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer reader.Close()
	original := int(writer.Fd())
	owned, err := duplicateNotifyFD(original)
	if err != nil {
		t.Fatal(err)
	}
	otherReader, otherWriter, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer otherReader.Close()
	defer otherWriter.Close()
	writer.Close()
	if int(otherWriter.Fd()) != original {
		if err := syscall.Dup2(int(otherWriter.Fd()), original); err != nil {
			t.Fatal(err)
		}
		defer syscall.Close(original)
	}
	notifyCompletion(owned)
	b := make([]byte, 1)
	n, err := reader.Read(b)
	if err != nil || n != 1 || b[0] != 1 {
		t.Fatalf("original pipe notification: %d %v %v", n, b, err)
	}
	otherReaderFD := int(otherReader.Fd())
	if err := syscall.SetNonblock(otherReaderFD, true); err != nil {
		t.Fatal(err)
	}
	if n, err := syscall.Read(otherReaderFD, b); n > 0 || err != syscall.EAGAIN {
		t.Fatalf("reused descriptor received a stray notification: %d %v", n, err)
	}
}

func TestFFINotifyBrokenPipe(t *testing.T) {
	reader, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	owned, err := duplicateNotifyFD(int(writer.Fd()))
	if err != nil {
		t.Fatal(err)
	}
	reader.Close()
	writer.Close()
	notifyCompletion(owned)
}

func TestFFICancelDropsLateResult(t *testing.T) {
	for _, legacy := range []bool{false, true} {
		state := &asyncResultWithNotify{}
		id := registerAsyncResult(state, legacy)
		cancelAsync(id)
		cancelAsync(id)
		completeAsyncResult(state, []byte("late response"))
		if data, ok := takeAsyncResult(id); ok || data != nil {
			t.Fatal("cancelled result available")
		}
		if state.result != nil {
			t.Fatal("late response retained")
		}
	}
}

func TestFFIRetrievalAndCancelRace(t *testing.T) {
	for i := 0; i < 100; i++ {
		state := &asyncResultWithNotify{}
		id := registerAsyncResult(state, i%2 == 0)
		completeAsyncResult(state, []byte("response"))
		var count atomic.Int32
		var wg sync.WaitGroup
		for j := 0; j < 8; j++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				if _, ok := takeAsyncResult(id); ok {
					count.Add(1)
				}
			}()
		}
		wg.Add(1)
		go func() { defer wg.Done(); cancelAsync(id) }()
		wg.Wait()
		if count.Load() > 1 {
			t.Fatal("duplicate result")
		}
		if _, ok := takeAsyncResult(id); ok {
			t.Fatal("result survived cleanup")
		}
	}
}
