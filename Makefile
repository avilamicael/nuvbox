.PHONY: help up down logs lint test clean reset webhook-test db-recent db-size db-debug db-full

help:
	@echo "Jarvis Backend - Development Commands"
	@echo ""
	@echo "🐳 CONTAINERS:"
	@echo "  make up              - Start Docker services"
	@echo "  make down            - Stop Docker services"
	@echo "  make logs            - View backend logs"
	@echo "  make logs-postgres   - View PostgreSQL logs"
	@echo ""
	@echo "📊 DATABASE & DADOS:"
	@echo "  make db-stats        - Database statistics"
	@echo "  make db-backup       - Backup PostgreSQL to SQL file"
	@echo "  make shell-db        - Open psql shell"
	@echo "  make db-recent       - Last 10 transcriptions (preview 80 chars)"
	@echo "  make db-debug        - Last 10 transcriptions (texto completo + duração)"
	@echo "  make db-full N=5     - Ver texto completo do último N registro"
	@echo "  make db-size         - Database size"
	@echo ""
	@echo "🧪 TESTES:"
	@echo "  make test            - Test microphone"
	@echo "  make webhook-test    - Test Alexa webhook"
	@echo ""
	@echo "🧹 LIMPEZA:"
	@echo "  make clean           - Remove logs"
	@echo "  make db-reset        - Clear all data"
	@echo "  make reset           - Full reset"
	@echo ""

up:
	docker-compose up -d
	@echo "✅ Services starting..."
	@sleep 2
	docker-compose ps

down:
	docker-compose down
	@echo "✅ Services stopped"

logs:
	docker-compose logs -f backend

logs-postgres:
	docker-compose logs -f postgres

lint:
	@echo "Checking Python code..."
	docker-compose run --rm backend python -m py_compile backend/*.py backend/**/*.py
	@echo "✅ Code check passed"

test:
	@echo "Listing audio devices..."
	docker-compose run --rm backend python -c "import sounddevice as sd; print(sd.query_devices())"

webhook-test:
	@echo "Testing Alexa webhook..."
	@curl -s -X POST http://localhost:5001/webhook/alexa \
		-H "Content-Type: application/json" \
		-H "X-Alexa-Secret: mude_antes_do_ngrok" \
		-d '{"text": "test webhook", "session_id": "make-test", "timestamp": "'$$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' | jq .

db-recent:
	@echo "Recent transcriptions..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"SELECT id, LEFT(texto, 80) as preview, fonte, criado_em FROM transcricoes ORDER BY id DESC LIMIT 10;"

db-debug:
	@echo "Debug: últimas 10 transcrições (texto completo)..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"SELECT id, fonte, criado_em, length(texto) as chars, duracao_ms, texto FROM transcricoes ORDER BY id DESC LIMIT 10;"

db-full:
	@echo "Texto completo do último registro..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"SELECT id, fonte, criado_em, length(texto) as chars, duracao_ms, chr(10)||texto||chr(10) as texto_completo FROM transcricoes ORDER BY id DESC LIMIT $${N:-1};"

db-size:
	@echo "Database size..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"SELECT pg_size_pretty(pg_database_size('jarvis_db')) as tamanho;"

db-reset:
	@echo "⚠️  Resetting database (ALL DATA WILL BE DELETED)"
	@read -p "Are you sure? (type 'yes'): " confirm && [ "$$confirm" = "yes" ] && \
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"TRUNCATE transcricoes CASCADE;" && \
	echo "✅ Database reset"

db-backup:
	@echo "Backing up database..."
	docker-compose exec -T postgres pg_dump -U jarvis jarvis_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup saved: backup_$(shell date +%Y%m%d_%H%M%S).sql"

db-stats:
	@echo "Database statistics..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"SELECT fonte, COUNT(*) as count, MIN(criado_em) as first_at, MAX(criado_em) as last_at FROM transcricoes GROUP BY fonte ORDER BY count DESC;"

clean:
	@echo "Cleaning logs and temp files..."
	rm -rf logs/*.log logs/*.log.*
	rm -rf backup_*.sql
	@echo "✅ Cleaned"

reset:
	@echo "⚠️  FULL RESET - removing everything"
	@read -p "Are you sure? (type 'yes'): " confirm && [ "$$confirm" = "yes" ] && \
	docker-compose down -v && \
	rm -rf logs/*.log logs/*.log.* && \
	rm -rf backup_*.sql && \
	echo "✅ Reset complete"

shell:
	docker-compose run --rm backend /bin/bash

shell-db:
	docker-compose exec postgres psql -U jarvis -d jarvis_db
