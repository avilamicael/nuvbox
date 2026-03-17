#!/bin/bash
# Jarvis Backend Health Check Script

set -e

echo "🏥 Jarvis Backend Health Check"
echo "======================================"

# Check Docker
echo ""
echo "1️⃣  Docker Status"
if command -v docker &> /dev/null; then
    echo "   ✅ Docker installed"
else
    echo "   ❌ Docker not found"
    exit 1
fi

if docker ps &> /dev/null; then
    echo "   ✅ Docker daemon running"
else
    echo "   ❌ Docker daemon not running"
    exit 1
fi

# Check containers
echo ""
echo "2️⃣  Container Status"
if docker-compose ps &> /dev/null; then
    docker-compose ps
else
    echo "   ❌ docker-compose not found"
    exit 1
fi

# Check services
echo ""
echo "3️⃣  Service Health"

# PostgreSQL
if docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c "SELECT NOW();" &> /dev/null; then
    echo "   ✅ PostgreSQL: Connected"
else
    echo "   ❌ PostgreSQL: Connection failed"
fi

# Backend API
if curl -s http://localhost:5001/health &> /dev/null; then
    echo "   ✅ Backend API: Responding"
else
    echo "   ❌ Backend API: Not responding"
fi

# Microphone
echo ""
echo "4️⃣  Microphone"
if docker-compose run --rm backend python -c "import sounddevice as sd; print('Found', len(sd.query_devices()), 'devices')" &> /dev/null; then
    DEVICES=$(docker-compose run --rm backend python -c "import sounddevice as sd; print(len(sd.query_devices()))" 2>/dev/null)
    echo "   ✅ Audio devices: $DEVICES found"
else
    echo "   ⚠️  Audio check failed"
fi

# Database stats
echo ""
echo "5️⃣  Database Statistics"
docker-compose exec -T postgres psql -U jarvis -d jarvis_db << EOF
SELECT
  'Total transcriptions' as metric,
  COUNT(*)::TEXT as value
FROM transcricoes
UNION ALL
SELECT
  'Microphone (last 24h)',
  COUNT(*)::TEXT
FROM transcricoes
WHERE fonte = 'mic_usb' AND criado_em > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
  'Alexa (last 24h)',
  COUNT(*)::TEXT
FROM transcricoes
WHERE fonte = 'alexa' AND criado_em > NOW() - INTERVAL '24 hours';
EOF

# Logs
echo ""
echo "6️⃣  Recent Logs"
echo "   Last 5 lines of backend logs:"
docker-compose logs --tail 5 backend | sed 's/^/     /'

echo ""
echo "======================================"
echo "✅ Health check complete!"
