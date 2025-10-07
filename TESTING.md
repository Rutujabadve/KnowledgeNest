# 🧪 Testing KnowledgeNest

## Quick Start Testing Guide

### Prerequisites
- Docker installed
- Python 3.10+
- `jq` installed (for JSON formatting): `brew install jq`

### Option 1: Automated Testing (Recommended)

**Step 1: Start Databases**
```bash
cd /Users/rutujabadve/Desktop/projects/KnowledgeNest
docker-compose -f ci_cd/docker-compose.yml up -d mysql postgres
```

Wait ~10 seconds for databases to initialize.

**Step 2: Start All Services**
```bash
./start_services.sh
```

**Step 3: Run Tests**
```bash
./test_api.sh
```

### Option 2: Manual Testing

**Start each service individually:**

```bash
# Terminal 1 - Auth Service
cd services/auth_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Terminal 2 - Course Service
cd services/course_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Terminal 3 - Review Service
cd services/review_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Terminal 4 - API Gateway
cd api_gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Then test manually:**

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123","name":"Test"}'

# 2. Login (save the token)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# 3. Create Course
curl -X POST http://localhost:5000/api/courses \
  -H "Content-Type: application/json" \
  -d '{"title":"Python 101","description":"Learn Python"}'

# 4. List Courses
curl http://localhost:5000/api/courses

# 5. Enroll (use token from step 2)
curl -X POST http://localhost:5000/api/courses/1/enroll \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 6. Review (use token from step 2)
curl -X POST http://localhost:5000/api/courses/1/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"rating":5,"comment":"Great!"}'
```

## API Endpoints

### Auth Service (via Gateway)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Course Service (via Gateway)
- `GET /api/courses` - List all courses
- `POST /api/courses` - Create course
- `POST /api/courses/:id/enroll` - Enroll in course (JWT required)

### Review Service (via Gateway)
- `POST /api/courses/:id/reviews` - Create review (JWT required)

## Troubleshooting

**Database connection errors?**
```bash
# Check if databases are running
docker ps

# View database logs
docker-compose -f ci_cd/docker-compose.yml logs mysql
docker-compose -f ci_cd/docker-compose.yml logs postgres
```

**Service not starting?**
```bash
# Check logs
tail -f logs/auth.log
tail -f logs/course.log
tail -f logs/review.log
tail -f logs/gateway.log
```

**Stop all services:**
```bash
# Stop Docker databases
docker-compose -f ci_cd/docker-compose.yml down

# Kill Python processes
pkill -f "python app.py"
```
