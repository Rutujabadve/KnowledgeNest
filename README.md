# KnowledgeNest

A microservices-based online learning platform built with Flask, React, MySQL, and PostgreSQL.

## Architecture

KnowledgeNest uses a microservices architecture with:
- **API Gateway** - Central routing and authentication
- **Auth Service** - User authentication (Flask + MySQL)
- **Course Service** - Course management and enrollment (Flask + PostgreSQL)
- **Review Service** - Course reviews and ratings (Flask + PostgreSQL)
- **Frontend** - React-based user interface
- **Analytics** - Metrics collection and visualization
- **Message Queue** - Event-driven communication between services

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: React, Redux Toolkit, TailwindCSS
- **Databases**: MySQL (Auth), PostgreSQL (Courses & Reviews)
- **Messaging**: RabbitMQ
- **CI/CD**: GitHub Actions, Docker, AWS
- **Monitoring**: Prometheus, Grafana

## Getting Started

See individual service directories for setup instructions.
