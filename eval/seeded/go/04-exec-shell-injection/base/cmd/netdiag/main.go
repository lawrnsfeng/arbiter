package main

import (
	"log"
	"net/http"

	"example.com/netdiag"
)

func main() {
	log.Fatal(http.ListenAndServe(":8080", netdiag.NewMux()))
}
