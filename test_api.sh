#!/bin/bash
set -e

# Test Script for Auth Service

echo "=== Auth Service Test Script ==="
echo ""

# Test 1: Root endpoint
echo "1. Testing root endpoint..."
curl -s http://localhost:8000/
echo -e "\n"

# Test 2: Register a new user
echo "2. Testing user registration..."
curl -s -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demouser",
    "email": "demo@example.com",
    "password": "demopass123"
  }'
echo -e "\n"

# Test 3: Login and get token
echo "3. Testing login..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demouser",
    "password": "demopass123"
  }')
echo "$TOKEN_RESPONSE"
echo -e "\n"

# Extract token
TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Test 4: Get user info with token
echo "4. Testing /me endpoint with JWT token..."
curl -s -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer $TOKEN"
echo -e "\n"

# Test 5: Test duplicate registration
echo "5. Testing duplicate username registration (should fail)..."
curl -s -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demouser",
    "email": "another@example.com",
    "password": "password123"
  }'
echo -e "\n"

# Test 6: Test wrong password
echo "6. Testing login with wrong password (should fail)..."
curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demouser",
    "password": "wrongpassword"
  }'
echo -e "\n"

# Test 7: Test invalid token
echo "7. Testing /me with invalid token (should fail)..."
curl -s -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer invalid_token_here"
echo -e "\n"

echo "=== All tests completed ==="
