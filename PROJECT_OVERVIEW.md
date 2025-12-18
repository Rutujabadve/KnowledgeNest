# KnowledgeNest - Comprehensive Project Overview

## 🎯 Project Description

**KnowledgeNest** is a production-ready, microservices-based online learning platform that demonstrates modern full-stack development practices. The platform enables users to register, browse courses, enroll in learning programs, and submit reviews - all built with a scalable, event-driven architecture.

## 🏗️ System Architecture

### Microservices Architecture

The project follows a **microservices architecture pattern** with the following services:

1. **API Gateway** (Port 8000)
   - Single entry point for all client requests
   - Handles JWT authentication and token validation
   - Routes requests to appropriate microservices
   - Implements CORS for cross-origin requests

2. **Auth Service** (Port 5001)
   - User registration and authentication
   - Password hashing with bcrypt
   - JWT token generation and validation
   - MySQL database for user data
   - **Publishes events**: `user.registered`

3. **Course Service** (Port 5002)
   - Course creation and management
   - Course enrollment functionality
   - PostgreSQL database for course data
   - **Publishes events**: `course.created`, `course.enrolled`

4. **Review Service** (Port 5003)
   - Course review and rating system
   - Rating validation (1-5 stars)
   - PostgreSQL database for review data
   - **Publishes events**: `review.created`

5. **Notification Service**
   - Event consumer service
   - Processes events asynchronously
   - Handles notifications for user actions
   - Demonstrates event-driven communication

6. **Frontend** (Port 3000)
   - React 19 with Vite
   - React Router for navigation
   - Axios for API communication
   - Modern, responsive UI

### Event-Driven Communication

**RabbitMQ** is used as the message broker for asynchronous, event-driven communication:

- **Exchange**: `knowledge_nest_events` (Topic exchange)
- **Event Types**:
  - `user.registered` - New user registration
  - `course.created` - New course added
  - `course.enrolled` - User enrollment
  - `review.created` - New review submitted

**Benefits:**
- Loose coupling between services
- Asynchronous processing
- Scalability and reliability
- Real-time event processing

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python 3.10)
- **Authentication**: JWT (JSON Web Tokens)
- **Password Security**: bcrypt for hashing
- **Message Queue**: RabbitMQ with pika library
- **API Communication**: RESTful APIs

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite
- **Routing**: React Router
- **HTTP Client**: Axios
- **Styling**: CSS3

### Databases
- **MySQL 8.0**: User authentication data
- **PostgreSQL 15**: Course and review data
- **ORM**: SQLAlchemy

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Message Broker**: RabbitMQ 3-management

## 📊 Data Flow

### User Registration Flow
```
User → Frontend → API Gateway → Auth Service → MySQL
                                    ↓
                              RabbitMQ (user.registered event)
                                    ↓
                          Notification Service (Welcome email)
```

### Course Enrollment Flow
```
User → Frontend → API Gateway → Course Service → PostgreSQL
                                    ↓
                              RabbitMQ (course.enrolled event)
                                    ↓
                          Notification Service (Enrollment confirmation)
```

### Review Submission Flow
```
User → Frontend → API Gateway → Review Service → PostgreSQL
                                    ↓
                              RabbitMQ (review.created event)
                                    ↓
                          Notification Service (Review processed)
```

## 🔐 Security Features

1. **JWT Authentication**
   - Token-based authentication
   - 24-hour token expiration
   - Secure token validation

2. **Password Security**
   - bcrypt hashing with salt
   - No plaintext password storage
   - Secure password verification

3. **API Security**
   - Token validation on protected routes
   - CORS configuration
   - Input validation

## 🚀 Key Features

### For Users
- User registration and login
- Browse available courses
- Enroll in courses
- Submit reviews and ratings
- View course reviews

### For System
- Event-driven architecture
- Asynchronous event processing
- Scalable microservices
- Containerized deployment
- Health check endpoints

## 📁 Project Structure

```
KnowledgeNest/
├── api_gateway/              # API Gateway service
│   ├── app.py                # Main gateway application
│   └── requirements.txt
├── services/
│   ├── auth_service/         # Authentication microservice
│   │   ├── app.py           # Auth endpoints + event publishing
│   │   ├── rabbitmq_client.py  # RabbitMQ utility
│   │   ├── models/          # User model
│   │   └── database.py      # Database connection
│   ├── course_service/       # Course management microservice
│   │   ├── app.py           # Course endpoints + event publishing
│   │   ├── rabbitmq_client.py  # RabbitMQ utility
│   │   └── models/          # Course and Enrollment models
│   ├── review_service/       # Review microservice
│   │   ├── app.py           # Review endpoints + event publishing
│   │   ├── rabbitmq_client.py  # RabbitMQ utility
│   │   └── models/          # Review model
│   └── notification_service/ # Event consumer service
│       ├── app.py           # Event consumer and handlers
│       └── requirements.txt
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── App.jsx          # Main app component
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   └── utils/           # API utilities
│   └── package.json
├── database/
│   ├── mysql/               # MySQL initialization scripts
│   └── postgres/            # PostgreSQL schemas
├── ci_cd/
│   └── docker-compose.yml   # Docker Compose configuration
└── README.md                 # Project documentation
```

## 🔄 RabbitMQ Implementation Details

### Architecture Pattern
- **Publisher-Subscriber Pattern**: Services publish events, consumers subscribe
- **Topic Exchange**: Flexible routing based on routing keys
- **Persistent Messages**: Messages survive broker restarts

### Event Publishing
Each service includes a `RabbitMQClient` utility that:
- Manages connections and reconnections
- Declares exchanges automatically
- Publishes events with persistent delivery
- Handles errors gracefully

### Event Consumption
The Notification Service:
- Consumes all events from the exchange
- Processes events asynchronously
- Implements message acknowledgment
- Handles different event types with specific handlers

### Configuration
- Environment-based configuration
- Docker service discovery
- Health checks and monitoring

## 🧪 Testing & Quality

- Health check endpoints for all services
- API testing scripts
- Docker-based testing environment
- Error handling and logging

## 📈 Scalability Considerations

1. **Horizontal Scaling**: Each service can be scaled independently
2. **Database Separation**: Different databases for different concerns
3. **Event-Driven**: Asynchronous processing reduces bottlenecks
4. **Containerization**: Easy deployment and scaling with Docker
5. **Load Balancing**: API Gateway can be load-balanced

## 🎓 Learning Outcomes

This project demonstrates:

1. **Microservices Architecture**
   - Service decomposition
   - Inter-service communication
   - Database per service pattern

2. **Event-Driven Architecture**
   - Message queue implementation
   - Event publishing and consumption
   - Asynchronous processing

3. **Full-Stack Development**
   - RESTful API design
   - Frontend-backend integration
   - Authentication and authorization

4. **DevOps Practices**
   - Docker containerization
   - Docker Compose orchestration
   - CI/CD pipeline setup

5. **Database Design**
   - Relational database modeling
   - Database selection (MySQL vs PostgreSQL)
   - ORM usage with SQLAlchemy

## 🚀 Deployment

### Docker Compose
All services are containerized and can be deployed with:
```bash
docker-compose -f ci_cd/docker-compose.yml up -d
```

### Services Access
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- RabbitMQ Management: http://localhost:15672
- Auth Service: http://localhost:5001
- Course Service: http://localhost:5002
- Review Service: http://localhost:5003

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Courses
- `GET /api/courses` - List all courses
- `POST /api/courses` - Create new course
- `POST /api/courses/:id/enroll` - Enroll in course (requires JWT)

### Reviews
- `GET /api/courses/:id/reviews` - Get course reviews
- `POST /api/courses/:id/reviews` - Submit review (requires JWT)

## 🔍 Monitoring & Observability

- Health check endpoints (`/health`) for all services
- RabbitMQ Management UI for queue monitoring
- Service logs for debugging
- Event logging in notification service

## 🎯 Use Cases

1. **E-Learning Platform**: Complete course management system
2. **Event-Driven System**: Demonstrates RabbitMQ integration
3. **Microservices Example**: Production-ready microservices architecture
4. **Full-Stack Application**: End-to-end development showcase

## 💡 Future Enhancements

- Email notifications via SMTP
- Real-time analytics dashboard
- Course recommendation engine
- Payment integration
- Video streaming for course content
- Advanced search and filtering
- User profiles and progress tracking

## 📚 Documentation

- **README.md**: Quick start and basic documentation
- **RABBITMQ_IMPLEMENTATION.md**: Detailed RabbitMQ implementation guide
- **PROJECT_OVERVIEW.md**: This comprehensive overview

## 🏆 Project Highlights

✅ **Production-Ready**: Error handling, logging, health checks  
✅ **Scalable Architecture**: Microservices with event-driven communication  
✅ **Modern Tech Stack**: Latest versions of React, Flask, and databases  
✅ **Best Practices**: Security, containerization, CI/CD  
✅ **Complete Implementation**: Frontend, backend, databases, messaging  
✅ **Well-Documented**: Comprehensive documentation for all components  

---

This project serves as an excellent demonstration of:
- Microservices architecture design and implementation
- Event-driven architecture with RabbitMQ
- Full-stack development skills
- DevOps and containerization practices
- Database design and management
- API design and security

Perfect for showcasing in a portfolio or resume!


