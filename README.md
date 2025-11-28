# 🎓 KnowledgeNest

[![CI/CD](https://github.com/Rutujabadve/KnowledgeNest/actions/workflows/ci.yml/badge.svg)](https://github.com/Rutujabadve/KnowledgeNest/actions)

A production-ready microservices-based online learning platform built with Flask, React, MySQL, and PostgreSQL.

## 🏗️ Architecture

KnowledgeNest uses a microservices architecture with:
- **API Gateway** - Central routing and authentication (Port 8000)
- **Auth Service** - User authentication with JWT (Flask + MySQL, Port 5001)
- **Course Service** - Course management and enrollment (Flask + PostgreSQL, Port 5002)
- **Review Service** - Course reviews and ratings (Flask + PostgreSQL, Port 5003)
- **Notification Service** - Event consumer for asynchronous notifications (RabbitMQ)
- **Frontend** - React-based user interface (Port 3000)
- **Message Queue** - RabbitMQ for event-driven communication (Port 5672, Management UI: 15672)
- **Databases** - MySQL (Auth), PostgreSQL (Courses & Reviews)

## 🚀 Tech Stack

- **Backend**: Flask (Python 3.10)
- **Frontend**: React 19, Vite, React Router, Axios
- **Databases**: MySQL 8.0, PostgreSQL 15
- **Messaging**: RabbitMQ
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Authentication**: JWT (JSON Web Tokens)

## 📦 Quick Start with Docker

### Prerequisites
- Docker Desktop installed
- Git

### Run the Application

```bash
# Clone the repository
git clone https://github.com/your_username/KnowledgeNest.git
cd KnowledgeNest

# Start all services with Docker
docker-compose -f ci_cd/docker-compose.yml up -d

# Wait ~30 seconds for services to initialize

# Access the application
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# RabbitMQ Management: http://localhost:15672 (admin/password)
```

### Stop the Application

```bash
docker-compose -f ci_cd/docker-compose.yml down
```

## 🛠️ Local Development Setup

### Backend Services

Each service can be run independently:

```bash
# Auth Service
cd services/auth_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Course Service
cd services/course_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Review Service
cd services/review_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# API Gateway
cd api_gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Databases

Start databases with Docker:

```bash
docker-compose -f ci_cd/docker-compose.yml up -d mysql postgres
```

## 🧪 Testing

Run the automated test suite:

```bash
# Test all endpoints
./test_api.sh

# Or test manually
curl http://localhost:8000/health
curl http://localhost:8000/api/courses
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Course Endpoints

- `GET /api/courses` - List all courses
- `POST /api/courses` - Create new course
- `POST /api/courses/:id/enroll` - Enroll in course (requires JWT)

### Review Endpoints

- `GET /api/courses/:id/reviews` - Get course reviews
- `POST /api/courses/:id/reviews` - Submit review (requires JWT)

## 🔐 Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Key variables:
- `JWT_SECRET` - Secret key for JWT tokens
- `DATABASE_URL` - Database connection strings
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASS` - RabbitMQ connection
- Service URLs and ports

## 📁 Project Structure

```
KnowledgeNest/
├── api_gateway/          # API Gateway service
├── services/
│   ├── auth_service/     # Authentication service (publishes user.registered events)
│   ├── course_service/   # Course management service (publishes course.* events)
│   ├── review_service/   # Review service (publishes review.created events)
│   └── notification_service/  # Event consumer service
├── frontend/             # React frontend
├── database/
│   ├── mysql/           # MySQL init scripts
│   └── postgres/        # PostgreSQL schemas
├── ci_cd/
│   └── docker-compose.yml
├── .github/
│   └── workflows/       # GitHub Actions CI/CD
└── docs/                # Documentation

```

## 🔄 Event-Driven Architecture

KnowledgeNest implements an **event-driven architecture** using RabbitMQ:

- **Event Publishers**: Auth, Course, and Review services publish events
- **Event Consumer**: Notification service consumes and processes events
- **Event Types**: `user.registered`, `course.created`, `course.enrolled`, `review.created`

For detailed implementation guide, see [RABBITMQ_IMPLEMENTATION.md](./RABBITMQ_IMPLEMENTATION.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👥 Authors

- Rutuja Badve - Initial work

## 🙏 Acknowledgments

- Built as a learning project for microservices architecture
- Demonstrates modern full-stack development practices
