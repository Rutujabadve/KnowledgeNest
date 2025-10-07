#!/bin/bash

# KnowledgeNest - Start All Services
echo "🚀 Starting KnowledgeNest Services"
echo "==================================="

# Check if databases are running
echo -e "\n📦 Step 1: Starting Databases (MySQL & PostgreSQL)"
echo "Run this command in a separate terminal:"
echo "  cd /Users/rutujabadve/Desktop/projects/KnowledgeNest"
echo "  docker-compose -f ci_cd/docker-compose.yml up mysql postgres"
echo ""
read -p "Press Enter once databases are running..."

# Install dependencies and start services in background
echo -e "\n📦 Step 2: Installing Dependencies & Starting Services"

# Auth Service
echo "Starting Auth Service (port 5001)..."
cd services/auth_service
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
python app.py > ../../logs/auth.log 2>&1 &
AUTH_PID=$!
echo "  ✓ Auth Service started (PID: $AUTH_PID)"
cd ../..

# Course Service
echo "Starting Course Service (port 5002)..."
cd services/course_service
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
python app.py > ../../logs/course.log 2>&1 &
COURSE_PID=$!
echo "  ✓ Course Service started (PID: $COURSE_PID)"
cd ../..

# Review Service
echo "Starting Review Service (port 5003)..."
cd services/review_service
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
python app.py > ../../logs/review.log 2>&1 &
REVIEW_PID=$!
echo "  ✓ Review Service started (PID: $REVIEW_PID)"
cd ../..

# API Gateway
echo "Starting API Gateway (port 5000)..."
cd api_gateway
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
python app.py > ../logs/gateway.log 2>&1 &
GATEWAY_PID=$!
echo "  ✓ API Gateway started (PID: $GATEWAY_PID)"
cd ..

# Wait for services to start
echo -e "\n⏳ Waiting for services to initialize..."
sleep 5

# Health checks
echo -e "\n🏥 Health Checks:"
curl -s http://localhost:5001/health | jq -r '"  Auth Service: " + .status' 2>/dev/null || echo "  Auth Service: ❌"
curl -s http://localhost:5002/health | jq -r '"  Course Service: " + .status' 2>/dev/null || echo "  Course Service: ❌"
curl -s http://localhost:5003/health | jq -r '"  Review Service: " + .status' 2>/dev/null || echo "  Review Service: ❌"
curl -s http://localhost:5000/health | jq -r '"  API Gateway: " + .service' 2>/dev/null || echo "  API Gateway: ❌"

echo -e "\n✅ All services running!"
echo -e "\n📝 Service PIDs:"
echo "  Auth: $AUTH_PID"
echo "  Course: $COURSE_PID"
echo "  Review: $REVIEW_PID"
echo "  Gateway: $GATEWAY_PID"
echo -e "\n💡 To test the API, run: ./test_api.sh"
echo "💡 To stop all services, run: kill $AUTH_PID $COURSE_PID $REVIEW_PID $GATEWAY_PID"
echo "💡 Logs are in: logs/"
