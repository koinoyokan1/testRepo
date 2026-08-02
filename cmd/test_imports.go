// This file ensures test dependencies are retained in go.mod
// These packages are flagged in blackduck_report.json for E2E testing
// FRESH E2E TEST - Updated 2026-08-02

package main

import (
	_ "github.com/sirupsen/logrus"
	_ "github.com/gorilla/mux"
	// Note: github.com/insecure/crypto-utils doesn't actually exist (unfixable vuln for testing)
)

func main() {
	// This is a stub file to ensure test dependencies are not removed by go mod tidy
}
