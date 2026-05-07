#!/bin/bash
# Test script to verify backend connectivity and API keys

echo "=========================================="
echo "  Backend Connectivity Test"
echo "=========================================="
echo ""

# Test 1: Check if server is running
echo "1. Checking if backend server is running on port 8000..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200"; then
    echo "   ✓ Server is responding"
else
    echo "   ❌ Server is not responding"
    echo "   Please start the server with: python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo "2. Testing root endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool 2>/dev/null || echo "   (Response received)"

echo ""
echo "3. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null
    echo ""
    # Check for errors
    if echo "$HEALTH_RESPONSE" | grep -q "error"; then
        echo "⚠️  Health check reports issues with some services"
    else
        echo "✓ All services appear healthy"
    fi
else
    echo "❌ Health endpoint failed"
fi

echo ""
echo "4. Testing analyze endpoint with sample code..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"hello\")","language":"python"}' 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$TEST_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ Analysis successful'); print('  Understanding:', data.get('understanding', 'N/A')[:50] + '...')" 2>/dev/null || echo "$TEST_RESPONSE" | head -c 200
else
    echo "❌ Analyze endpoint failed"
    echo "   This may indicate an API key issue or the server needs to be restarted after changing .env"
fi

echo ""
echo "=========================================="
echo "  Test Complete"
echo "=========================================="
