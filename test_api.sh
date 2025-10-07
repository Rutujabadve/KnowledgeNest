#!/bin/bash

# KnowledgeNest API Test Script
# This tests the complete flow through the API Gateway

BASE_URL="http://localhost:5000"
echo "🧪 Testing KnowledgeNest API Gateway"
echo "===================================="

# 1. Health Check
echo -e "\n1️⃣  Health Check"
curl -s $BASE_URL/health | jq .

# 2. Register User
echo -e "\n2️⃣  Register User"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}')
echo $REGISTER_RESPONSE | jq .

# 3. Login
echo -e "\n3️⃣  Login"
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}')
echo $LOGIN_RESPONSE | jq .

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"

# 4. Create Course
echo -e "\n4️⃣  Create Course"
COURSE_RESPONSE=$(curl -s -X POST $BASE_URL/api/courses \
  -H "Content-Type: application/json" \
  -d '{"title":"Introduction to Python","description":"Learn Python basics","content_url":"https://example.com/python"}')
echo $COURSE_RESPONSE | jq .

COURSE_ID=$(echo $COURSE_RESPONSE | jq -r '.id')
echo "Course ID: $COURSE_ID"

# 5. List Courses
echo -e "\n5️⃣  List All Courses"
curl -s $BASE_URL/api/courses | jq .

# 6. Enroll in Course (requires JWT)
echo -e "\n6️⃣  Enroll in Course (with JWT)"
curl -s -X POST $BASE_URL/api/courses/$COURSE_ID/enroll \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}' | jq .

# 7. Create Review (requires JWT)
echo -e "\n7️⃣  Create Review (with JWT)"
curl -s -X POST $BASE_URL/api/courses/$COURSE_ID/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"rating":5,"comment":"Great course!"}' | jq .

# 8. Test without JWT (should fail)
echo -e "\n8️⃣  Test Enroll WITHOUT JWT (should fail with 401)"
curl -s -X POST $BASE_URL/api/courses/$COURSE_ID/enroll \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

echo -e "\n✅ Test Complete!"
