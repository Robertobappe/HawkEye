package watcher

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/Robertobappe/price-alert-microservices/services/price-watcher/internal/rabbitmq"
)

type Product struct {
	ID           string  `json:"id"`
	Name         string  `json:"name"`
	CurrentPrice float64 `json:"current_price"`
}

type Alert struct {
	ID          string  `json:"id"`
	ProductID   string  `json:"product_id"`
	TargetPrice float64 `json:"target_price"`
	Email       string  `json:"email"`
	IsActive    string  `json:"is_active"`
}

type PriceDropEvent struct {
	AlertID      string  `json:"alert_id"`
	ProductID    string  `json:"product_id"`
	ProductName  string  `json:"product_name"`
	CurrentPrice float64 `json:"current_price"`
	TargetPrice  float64 `json:"target_price"`
	Email        string  `json:"email"`
	Timestamp    string  `json:"timestamp"`
}

type Watcher struct {
	productServiceURL string
	publisher         *rabbitmq.Publisher
	interval          time.Duration
}

func New(productServiceURL string, publisher *rabbitmq.Publisher, interval time.Duration) *Watcher {
	return &Watcher{
		productServiceURL: productServiceURL,
		publisher:         publisher,
		interval:          interval,
	}
}

func (w *Watcher) Start() {
	log.Printf("[Watcher] Starting price watcher (interval: %s)", w.interval)

	// Initial check
	w.checkPrices()

	ticker := time.NewTicker(w.interval)
	defer ticker.Stop()

	for range ticker.C {
		w.checkPrices()
	}
}

func (w *Watcher) checkPrices() {
	log.Println("[Watcher] Checking prices...")

	alerts, err := w.fetchAlerts()
	if err != nil {
		log.Printf("[Watcher] Error fetching alerts: %v", err)
		return
	}

	for _, alert := range alerts {
		product, err := w.fetchProduct(alert.ProductID)
		if err != nil {
			log.Printf("[Watcher] Error fetching product %s: %v", alert.ProductID, err)
			continue
		}

		if product.CurrentPrice <= alert.TargetPrice {
			log.Printf("[Watcher] Price drop detected! Product: %s | Current: %.2f | Target: %.2f",
				product.Name, product.CurrentPrice, alert.TargetPrice)

			event := PriceDropEvent{
				AlertID:      alert.ID,
				ProductID:    product.ID,
				ProductName:  product.Name,
				CurrentPrice: product.CurrentPrice,
				TargetPrice:  alert.TargetPrice,
				Email:        alert.Email,
				Timestamp:    time.Now().UTC().Format(time.RFC3339),
			}

			data, err := json.Marshal(event)
			if err != nil {
				log.Printf("[Watcher] Error marshaling event: %v", err)
				continue
			}

			if err := w.publisher.Publish(data); err != nil {
				log.Printf("[Watcher] Error publishing event: %v", err)
				continue
			}

			log.Printf("[Watcher] Event published for alert %s", alert.ID)
		}
	}
}

func (w *Watcher) fetchAlerts() ([]Alert, error) {
	resp, err := http.Get(fmt.Sprintf("%s/api/v1/alerts", w.productServiceURL))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var alerts []Alert
	if err := json.Unmarshal(body, &alerts); err != nil {
		return nil, err
	}
	return alerts, nil
}

func (w *Watcher) fetchProduct(productID string) (*Product, error) {
	resp, err := http.Get(fmt.Sprintf("%s/api/v1/products/%s", w.productServiceURL, productID))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var product Product
	if err := json.Unmarshal(body, &product); err != nil {
		return nil, err
	}
	return &product, nil
}
