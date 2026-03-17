#!/bin/bash
# Test Alexa webhook endpoint

set -e

# Get secret from .env
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

SECRET=$(grep "ALEXA_WEBHOOK_SECRET" .env | cut -d= -f2)
if [ -z "$SECRET" ]; then
    SECRET="change_me_before_ngrok"
fi

URL="http://localhost:5001/webhook/alexa"

echo "🧪 Testing Alexa Webhook"
echo "======================================"
echo "URL: $URL"
echo "Secret: $SECRET"
echo ""

# Test with curl
echo "Sending test request..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-Alexa-Secret: $SECRET" \
  -d '{
    "text": "teste de integração alexa",
    "session_id": "test-session-'$(date +%s)'",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "Response ($HTTP_CODE):"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Webhook test successful!"

    # Check if stored in DB
    echo ""
    echo "Checking if stored in database..."
    COUNT=$(docker-compose exec -T postgres psql -U cerebro -d cerebro_db -t -c \
        "SELECT COUNT(*) FROM transcricoes WHERE fonte = 'alexa' AND texto LIKE '%teste de integração%';" 2>/dev/null || echo "0")

    if [ "$COUNT" -gt "0" ]; then
        echo "✅ Found $COUNT transcription(s) in database"
    else
        echo "⚠️  No matching transcriptions found in database yet"
    fi
else
    echo "❌ Webhook test failed (HTTP $HTTP_CODE)"
    exit 1
fi
