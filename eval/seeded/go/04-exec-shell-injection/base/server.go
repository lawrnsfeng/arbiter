// Package netdiag serves network diagnostics over HTTP.
package netdiag

import (
	"fmt"
	"net/http"
)

// NewMux returns the diagnostics HTTP handler.
func NewMux() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", handleHealth)
	return mux
}

func handleHealth(w http.ResponseWriter, _ *http.Request) {
	fmt.Fprintln(w, "ok")
}
