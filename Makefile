.PHONY: test test-backend test-admin install-test-deps clean migrate migrate-auto migrate-history migrate-downgrade migrate-current help

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run all backend tests"
	@echo "  make test-admin        - Run only admin access control tests"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make install-test-deps - Install test dependencies"
	@echo "  make clean             - Clean test artifacts and cache"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make migrate           - Run pending database migrations"
	@echo "  make migrate-auto      - Generate new migration from model changes"
	@echo "  make migrate-history   - Show migration history"
	@echo "  make migrate-current   - Show current migration version"
	@echo "  make migrate-downgrade - Rollback last migration (use with caution)"

# Run all backend tests
test:
	@echo "Running all backend tests..."
	cd backend && pytest tests/ -v

# Run only admin access control tests
test-admin:
	@echo "Running admin access control tests..."
	cd backend && pytest tests/test_admin_access_control.py -v

# Run tests with coverage report
test-coverage:
	@echo "Running tests with coverage..."
	cd backend && pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Install test dependencies
install-test-deps:
	@echo "Installing test dependencies..."
	cd backend && pip install -r requirements-test.txt

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "Clean complete!"

# ============================================================================
# Database Migration Commands
# ============================================================================

# Run pending migrations
migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head
	@echo "✓ Migrations applied successfully!"

# Auto-generate migration from model changes
migrate-auto:
	@echo "Generating migration from model changes..."
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"
	@echo "✓ Migration file created! Review it before applying."

# Show migration history
migrate-history:
	@echo "Migration history:"
	cd backend && alembic history --verbose

# Show current migration version
migrate-current:
	@echo "Current migration version:"
	cd backend && alembic current

# Rollback last migration
migrate-downgrade:
	@echo "WARNING: This will rollback the last migration!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd backend && alembic downgrade -1; \
		echo "✓ Migration rolled back!"; \
	else \
		echo "Cancelled."; \
	fi
