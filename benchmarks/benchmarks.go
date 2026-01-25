package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/Danny-Dasilva/CycleTLS/cycletls"
	"github.com/valyala/fasthttp"
)

func benchmarkCycleTLS(url string, repetitions int) (float64, int) {
	client := cycletls.Init()
	defer client.Close()

	errors := 0
	start := time.Now()

	for i := 0; i < repetitions; i++ {
		_, err := client.Do(url, cycletls.Options{
			EnableConnectionReuse: true,
		}, "GET")

		if err != nil {
			errors++
			log.Printf("CycleTLS request %d failed: %v", i, err)
		}
	}

	duration := time.Since(start)
	return duration.Seconds(), errors
}

func benchmarkFastHTTP(url string, repetitions int) (float64, int) {
	client := &fasthttp.Client{
		MaxConnsPerHost: 1, // Connection pooling
	}

	errors := 0
	start := time.Now()

	for i := 0; i < repetitions; i++ {
		req := fasthttp.AcquireRequest()
		resp := fasthttp.AcquireResponse()

		req.SetRequestURI(url)

		err := client.Do(req, resp)

		fasthttp.ReleaseRequest(req)
		fasthttp.ReleaseResponse(resp)

		if err != nil {
			errors++
			log.Printf("fasthttp request %d failed: %v", i, err)
		}
	}

	duration := time.Since(start)
	return duration.Seconds(), errors
}

func benchmarkNetHTTP(url string, repetitions int) (float64, int) {
	client := &http.Client{
		Transport: &http.Transport{
			MaxIdleConnsPerHost: 1,
		},
	}

	errors := 0
	start := time.Now()

	for i := 0; i < repetitions; i++ {
		resp, err := client.Get(url)

		if err != nil {
			errors++
			log.Printf("net/http request %d failed: %v", i, err)
			continue
		}

		// Must read and close body to reuse connection
		resp.Body.Close()
	}

	duration := time.Since(start)
	return duration.Seconds(), errors
}

func runAllBenchmarks(url string, repetitions int, outputFile string) {
	fmt.Printf("Running benchmarks with %d repetitions to %s\n\n", repetitions, url)

	results := [][]string{
		{"library", "time"},
	}

	// Benchmark CycleTLS
	cycleDuration, cycleErrors := benchmarkCycleTLS(url, repetitions)
	fmt.Printf("CYCLETLS =\t%.4f\n", cycleDuration)
	if cycleErrors > 0 {
		fmt.Printf("  (Errors: %d)\n", cycleErrors)
	}
	fmt.Println()
	results = append(results, []string{"cycletls", fmt.Sprintf("%.4f", cycleDuration)})

	// Benchmark fasthttp
	fastDuration, fastErrors := benchmarkFastHTTP(url, repetitions)
	fmt.Printf("FASTHTTP =\t%.4f\n", fastDuration)
	if fastErrors > 0 {
		fmt.Printf("  (Errors: %d)\n", fastErrors)
	}
	fmt.Println()
	results = append(results, []string{"fasthttp", fmt.Sprintf("%.4f", fastDuration)})

	// Benchmark net/http
	netDuration, netErrors := benchmarkNetHTTP(url, repetitions)
	fmt.Printf("NET/HTTP =\t%.4f\n", netDuration)
	if netErrors > 0 {
		fmt.Printf("  (Errors: %d)\n", netErrors)
	}
	fmt.Println()
	results = append(results, []string{"net/http", fmt.Sprintf("%.4f", netDuration)})

	// Write CSV output
	if outputFile != "" {
		file, err := os.Create(outputFile)
		if err != nil {
			log.Fatalf("Failed to create output file: %v", err)
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		for _, record := range results {
			if err := writer.Write(record); err != nil {
				log.Fatalf("Failed to write to CSV: %v", err)
			}
		}

		fmt.Printf("Results written to %s\n", outputFile)
	}
}

func main() {
	url := flag.String("url", "http://localhost:5001/", "URL to benchmark")
	repetitions := flag.Int("repetitions", 10000, "Number of repetitions")
	outputFile := flag.String("output", "results.csv", "Output CSV file")

	flag.Parse()

	if *url == "" {
		log.Fatal("URL must not be an empty string")
	}

	if *repetitions < 100 {
		log.Fatal("Repetitions must be > 100")
	}

	fmt.Printf("Configuration: url=%s, repetitions=%d, output=%s\n\n", *url, *repetitions, *outputFile)

	runAllBenchmarks(*url, *repetitions, *outputFile)
}
