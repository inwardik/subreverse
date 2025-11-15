.PHONY: test test-backend test-admin install-test-deps clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  make test              - Run all backend tests"
	@echo "  make test-admin        - Run only admin access control tests"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make install-test-deps - Install test dependencies"
	@echo "  make clean             - Clean test artifacts and cache"

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
