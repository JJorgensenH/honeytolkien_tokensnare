package main

import (
	"crypto/tls"
	"net/http"
	"strings"
	"time"
)

// String a parchear con la URL objetivo al crear el honey token
var TargetURL = "PLACEHOLDER_URL_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

func main() {
	url := strings.TrimRight(TargetURL, "\x00")
	url = strings.TrimSpace(url)

	if strings.Contains(url, "PLACEHOLDER") {
		return
	}

	// Configuración para ignorar errores de certificados (opcional, por si usas https auto-firmado)
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	client := &http.Client{
		Transport: tr,
		Timeout:   10 * time.Second,
	}

	// Hacemos la petición GET silenciosa
	resp, err := client.Get(url)
	if err == nil {
		defer resp.Body.Close()
	}
}
