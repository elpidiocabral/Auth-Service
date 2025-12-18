#!/bin/bash
set -e

# Test Script for Auth Service

echo "=== Auth Service Test Script ==="
echo ""

BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to print test result
print_result() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC}: $2"
  else
    echo -e "${RED}✗ FAILED${NC}: $2"
  fi
}

# Test 1: Health check
echo -e "${YELLOW}1. Testing health endpoint...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ Health check passed${NC}"
  echo "$RESPONSE" | head -n-1 | python3 -m json.tool
else
  echo -e "${RED}✗ Health check failed (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Test 2: Register a new user
echo -e "${YELLOW}2. Testing user registration (local)...${NC}"
REG_RESPONSE=$(curl -s -X POST "$BASE_URL/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpass123"
  }')
echo "$REG_RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$REG_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
echo ""

# Test 3: Login with username/password
echo -e "${YELLOW}3. Testing login (local authentication)...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }')
echo "$LOGIN_RESPONSE" | python3 -m json.tool
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
echo ""

# Test 4: Get user profile
if [ ! -z "$TOKEN" ]; then
  echo -e "${YELLOW}4. Testing /profile endpoint...${NC}"
  PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/profile" \
    -H "Authorization: Bearer $TOKEN")
  echo "$PROFILE_RESPONSE" | python3 -m json.tool
  echo ""
fi

# Test 5: Invalid login attempt
echo -e "${YELLOW}5. Testing invalid login (should fail)...${NC}"
INVALID_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "wrongpassword"
  }')
HTTP_CODE=$(echo "$INVALID_LOGIN" | tail -n1)
echo -e "HTTP Code: ${YELLOW}$HTTP_CODE${NC} (expected 401)"
echo ""

# Test 6: Duplicate registration
echo -e "${YELLOW}6. Testing duplicate registration (should fail)...${NC}"
DUPLICATE_REG=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "another@example.com",
    "password": "pass123"
  }')
HTTP_CODE=$(echo "$DUPLICATE_REG" | tail -n1)
echo -e "HTTP Code: ${YELLOW}$HTTP_CODE${NC} (expected 400)"
echo ""

echo -e "${GREEN}=== Basic Tests Completed ===${NC}"
echo ""
echo "Note: To test Google OAuth2 flow:"
echo "1. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
echo "2. Visit: $BASE_URL/auth/google/login"
echo "3. You'll be redirected to Google login"
echo "4. After authorization, you'll receive a JWT token"
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
