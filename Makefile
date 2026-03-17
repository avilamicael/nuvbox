.PHONY: help up down logs lint test clean reset

help:
	@echo "Jarvis Backend - Development Commands"
	@echo ""
	@echo "  make up              - Start Docker services"
	@echo "  make down            - Stop Docker services"
	@echo "  make logs            - View backend logs"
	@echo "  make logs-postgres   - View PostgreSQL logs"
	@echo "  make lint            - Run Python linter"
	@echo "  make test            - Test microphone detection"
	@echo "  make db-reset        - Reset database (DELETE ALL DATA)"
	@echo "  make db-query        - Run query on database"
	@echo "  make clean           - Remove logs and temp files"
	@echo "  make reset           - Full reset (down + clean + remove volumes)"
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

test-db:
	@echo "Testing database connection..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c "SELECT NOW();"

test-transcription:
	@echo "Checking recent transcriptions..."
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c \
		"SELECT id, LEFT(texto, 50), fonte, criado_em FROM transcricoes ORDER BY id DESC LIMIT 5;"

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
	docker-compose exec -T postgres psql -U jarvis -d jarvis_db << EOF
SELECT
  fonte,
  COUNT(*) as count,
  MIN(criado_em) as first_at,
  MAX(criado_em) as last_at,
  AVG(duracao_ms) as avg_duration_ms
FROM transcricoes
GROUP BY fonte
ORDER BY count DESC;
EOF

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
