package rabbitmq

import (
	"context"
	"fmt"
	"log"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

const (
	ExchangeName   = "price_alerts"
	QueueName      = "price.alerts.notify"
	DeadLetterExch = "price_alerts.dlx"
	DeadLetterQ    = "price.alerts.dead"
	RoutingKey     = "price.dropped"
)

type Publisher struct {
	conn    *amqp.Connection
	channel *amqp.Channel
}

func NewPublisher(url string) (*Publisher, error) {
	var conn *amqp.Connection
	var err error

	for i := 0; i < 10; i++ {
		conn, err = amqp.Dial(url)
		if err == nil {
			break
		}
		log.Printf("[RabbitMQ] Connection attempt %d failed: %v. Retrying in 3s...", i+1, err)
		time.Sleep(3 * time.Second)
	}
	if err != nil {
		return nil, fmt.Errorf("failed to connect to RabbitMQ after retries: %w", err)
	}

	ch, err := conn.Channel()
	if err != nil {
		return nil, fmt.Errorf("failed to open channel: %w", err)
	}

	if err := setupTopology(ch); err != nil {
		return nil, fmt.Errorf("failed to setup topology: %w", err)
	}

	log.Println("[RabbitMQ] Connected and topology configured")
	return &Publisher{conn: conn, channel: ch}, nil
}

func setupTopology(ch *amqp.Channel) error {
	// Dead-letter exchange and queue
	if err := ch.ExchangeDeclare(DeadLetterExch, "direct", true, false, false, false, nil); err != nil {
		return err
	}
	_, err := ch.QueueDeclare(DeadLetterQ, true, false, false, false, nil)
	if err != nil {
		return err
	}
	if err := ch.QueueBind(DeadLetterQ, RoutingKey, DeadLetterExch, false, nil); err != nil {
		return err
	}

	// Main exchange and queue with dead-letter config
	if err := ch.ExchangeDeclare(ExchangeName, "direct", true, false, false, false, nil); err != nil {
		return err
	}
	_, err = ch.QueueDeclare(QueueName, true, false, false, false, amqp.Table{
		"x-dead-letter-exchange":    DeadLetterExch,
		"x-dead-letter-routing-key": RoutingKey,
		"x-message-ttl":             int32(60000),
	})
	if err != nil {
		return err
	}
	return ch.QueueBind(QueueName, RoutingKey, ExchangeName, false, nil)
}

func (p *Publisher) Publish(message []byte) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	return p.channel.PublishWithContext(ctx,
		ExchangeName,
		RoutingKey,
		false,
		false,
		amqp.Publishing{
			ContentType:  "application/json",
			Body:         message,
			DeliveryMode: amqp.Persistent,
			Timestamp:    time.Now(),
		},
	)
}

func (p *Publisher) Close() {
	if p.channel != nil {
		p.channel.Close()
	}
	if p.conn != nil {
		p.conn.Close()
	}
}
