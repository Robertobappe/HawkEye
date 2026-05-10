package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/Robertobappe/price-alert-microservices/services/price-watcher/internal/rabbitmq"
	"github.com/Robertobappe/price-alert-microservices/services/price-watcher/internal/watcher"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
	Version string `json:"version"`
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func main() {
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)

	rabbitURL := getEnv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
	productServiceURL := getEnv("PRODUCT_SERVICE_URL", "http://product-service:8000")
	checkInterval := getEnv("CHECK_INTERVAL", "30s")

	interval, err := time.ParseDuration(checkInterval)
	if err != nil {
		log.Fatalf("Invalid CHECK_INTERVAL: %v", err)
	}

	publisher, err := rabbitmq.NewPublisher(rabbitURL)
	if err != nil {
		log.Fatalf("Failed to create publisher: %v", err)
	}
	defer publisher.Close()

	w := watcher.New(productServiceURL, publisher, interval)

	// Health check endpoint
	http.HandleFunc("/health", func(resp http.ResponseWriter, req *http.Request) {
		resp.Header().Set("Content-Type", "application/json")
		json.NewEncoder(resp).Encode(HealthResponse{
			Status:  "healthy",
			Service: "price-watcher",
			Version: "1.0.0",
		})
	})

	go func() {
		log.Println("[Main] Health check server starting on :8081")
		if err := http.ListenAndServe(":8081", nil); err != nil {
			log.Fatalf("Health check server error: %v", err)
		}
	}()

	log.Println("[Main] Price Watcher Service started")
	w.Start()
}
