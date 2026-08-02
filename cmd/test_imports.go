// This file ensures test dependencies are retained in go.mod
// These packages are flagged in blackduck_report.json for E2E testing

package main

import (
	_ "github.com/google/uuid"
	_ "gopkg.in/yaml.v2"
)

func main() {
	// This is a stub file to ensure test dependencies are not removed by go mod tidy
}
