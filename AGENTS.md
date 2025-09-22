# AGENTS.md - My Proxy Collector

## Project Overview
This is a Python FastAPI backend + React TypeScript frontend application for proxy collection and validation, with Docker containerization and monitoring.

**Development Environment:** Windows 10 OS with PowerShell

## Development Environment Setup

### Backend (Python/FastAPI)
- Create Python virtual environment: `python -m venv .venv`
- Activate virtual environment (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r backend\requirements.txt`
- For development with auto-reload: `cd backend` then `python main.py`
- Database setup: Run `python backend\setup_sqlite_dev.py` for SQLite development setup
- Check database connection: `python backend\test_database_connection.py`

### Frontend (React/TypeScript)
- Navigate to frontend: `cd frontend-react`
- Install dependencies: `npm install` (or `yarn install`)
- Start development server: `npm run dev` (or `yarn dev`)
- Build for production: `npm run build` (or `yarn build`)

### Docker Development
- Full stack with docker-compose: `docker-compose up --build`
- SQLite development: `docker-compose -f docker-compose.sqlite.yml up --build`
- Individual services: `docker-compose up <service_name>`

## Testing Instructions

### Backend Testing
- Run all tests: `cd backend` then `python -m pytest`
- Run specific test file: `python -m pytest tests\unit\test_models.py`
- Run with coverage: `python -m pytest --cov=app`
- Quick integration test: `python tests\quick_test.py`
- Database functionality test: `python test_sqlite_functionality.py`

### Frontend Testing
- Run tests: `cd frontend-react` then `npm test`
- Run tests in watch mode: `npm test -- --watch`
- Generate coverage: `npm test -- --coverage`

### E2E Testing
- End-to-end tests: `python backend\tests\e2e\test_e2e.py`
- Integration tests: `python backend\tests\integration\test_integration.py`

## Code Quality & Linting

**Important: Check all syntax and formatting before every Git Push!**

### 🚀 Local Code Quality Check (Must run before Git Push)
Use local PowerShell script for fast and comprehensive code quality checks!

```powershell
# Complete check (including tests) - Recommended before Git Push
.\scripts\check-code-quality.ps1

# Auto-fix format issues
.\scripts\check-code-quality.ps1 -FixFormat

# Check only without running tests (faster)
.\scripts\check-code-quality.ps1 -SkipTests

# Check backend only
.\scripts\check-code-quality.ps1 -SkipFrontend

# Check frontend only
.\scripts\check-code-quality.ps1 -SkipBackend
```

### Manual Check (if step-by-step execution needed)

#### Backend (Python) - Execute in order
```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Format code
black backend\app

# 3. Sort imports
isort backend\app

# 4. Type checking
mypy backend\app

# 5. Syntax checking
flake8 backend\app
```

#### Frontend (TypeScript/React) - Execute in order
```powershell
# 1. Navigate to frontend directory
cd frontend-react

# 2. TypeScript type checking
npx tsc --noEmit

# 3. ESLint syntax checking
npm run lint

# 4. Format code (if prettier is configured)
npm run format
```

## Database Operations

### SQLite (Development)
- Initialize: `python backend\setup_sqlite_dev.py`
- Test connection: `python backend\test_database_connection.py`
- View schema: Check [`backend\database_schema.sql`](backend/database_schema.sql)

## Monitoring & Health Checks

### Health Endpoints
- Backend health: `GET http://localhost:8000/health`
- Database health: `GET http://localhost:8000/health/database`
- Monitoring metrics: `GET http://localhost:8000/metrics`

### Grafana & Prometheus
- Grafana dashboard: `http://localhost:3001` (when using docker-compose)
- Prometheus: `http://localhost:9090`
- Configuration: [`monitoring\prometheus.yml`](monitoring/prometheus.yml)

## Development Workflow

### Adding New Features
1. Create feature branch: `git checkout -b feature/your-feature`
2. Backend changes: Update models, services, and add tests
3. Frontend changes: Update components, types, and add tests
4. Test locally: Run both backend and frontend tests
5. Test integration: Use docker-compose to test full stack
6. Update documentation if needed

### Before Git Push (Required Checklist)

**Using Local Script (Fast and Comprehensive) - Recommended**
```powershell
# 🚀 Complete check before Git Push (Required)
.\scripts\check-code-quality.ps1

# 🔧 Auto-fix format issues + check
.\scripts\check-code-quality.ps1 -FixFormat

# ⚡ Quick check (skip tests but still check syntax)
.\scripts\check-code-quality.ps1 -SkipTests

# 🐳 Verify Docker build (only if Docker-related files changed)
# Check if Docker files have changed before running:
# git diff --name-only | Select-String "Dockerfile|docker-compose|\.dockerignore"
# If any matches found, then run:
docker-compose build

# 🏥 Test health check endpoints
# Start services then visit http://localhost:8000/health
```

**Manual Check (if step-by-step execution needed)**
```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Backend code quality checks (in order)
black backend\app
isort backend\app
mypy backend\app
flake8 backend\app

# 3. Frontend code quality checks
cd frontend-react
npx tsc --noEmit
npm run lint

# 4. Run all tests
cd ..
python -m pytest
cd frontend-react
npm test

# 5. Verify Docker build (only if Docker-related files changed)
cd ..
# Check for Docker-related changes first:
$dockerChanges = git diff --name-only | Select-String "Dockerfile|docker-compose|\.dockerignore"
if ($dockerChanges) {
    Write-Host "Docker files changed, running build verification..."
    docker-compose build
} else {
    Write-Host "No Docker files changed, skipping build verification"
}

# 6. Test health check endpoints
# Start services then visit http://localhost:8000/health
```

**⚠️ Important: All checks must pass before Git Push!**

**When to run Docker build:**
- Modified `Dockerfile` or `docker-compose.yml` files
- Changed `requirements.txt` or `package.json` (dependency changes)
- Added new environment variables or configuration
- Modified `.dockerignore` files
- First time setup or after major infrastructure changes

## Common Commands (PowerShell)

### Code Quality (Must run before Git Push)
```powershell
# 🚀 Complete check before Git Push (including tests)
.\scripts\check-code-quality.ps1

# 🔧 Auto-fix format issues + check
.\scripts\check-code-quality.ps1 -FixFormat

# ⚡ Quick check (skip tests but still check syntax)
.\scripts\check-code-quality.ps1 -SkipTests

# 🐍 Check backend only
.\scripts\check-code-quality.ps1 -SkipFrontend

# ⚛️ Check frontend only
.\scripts\check-code-quality.ps1 -SkipBackend

# 📝 Verbose output
.\scripts\check-code-quality.ps1 -Verbose
```

### Development
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start backend only
cd backend
python main.py

# Start frontend only (in new PowerShell window)
cd frontend-react
npm run dev

# Start full stack with Docker
docker-compose up --build

# Start with SQLite (development)
docker-compose -f docker-compose.sqlite.yml up --build
```

### Testing
```powershell
# Backend tests (with venv activated)
.\.venv\Scripts\Activate.ps1
cd backend
python -m pytest tests\

# Frontend tests (in new PowerShell window)
cd frontend-react
npm test

# Quick system test
python backend\tests\quick_test.py
```

### Utilities
```powershell
# Database diagnostics
python backend\system_diagnostics.py

# Proxy validation test
python backend\proxy_validator.py

# Task executor test
python backend\test_task_executor.py
```

## Project Structure Notes
- [`backend\app\`](backend/app/) - Main application code
- [`backend\app\core\`](backend/app/core/) - Core utilities and configuration
- [`backend\app\services\`](backend/app/services/) - Business logic services
- [`backend\app\etl\`](backend/app/etl/) - ETL and validation logic
- [`frontend-react\src\`](frontend-react/src/) - React application source
- [`Docs\`](Docs/) - Project documentation
- [`monitoring\`](monitoring/) - Monitoring configuration
- [`scripts\`](scripts/) - Development scripts and utilities

## Pull Request Guidelines
- Title format: `[Backend|Frontend|DevOps] <Description>`
- **Must pass local code quality checks** - Use `.\scripts\check-code-quality.ps1` for verification
- Must run complete local code quality checklist first (see above "Before Git Push")
- Include relevant documentation updates
- Test Docker build only if Docker-related files changed (see "When to run Docker build" above)
- Update health check tests if adding new endpoints

## Code Quality Checks

### Local Script Check (Must run before Git Push)
Use [`scripts\check-code-quality.ps1`](scripts/check-code-quality.ps1) for local code quality checks:
- 🚀 **Fast and comprehensive local checks**
- 🎨 Auto formatting (black, isort, prettier)
- 🔍 Syntax checks (flake8, ESLint, TypeScript)
- 🧪 Run tests
- 🔧 Support auto-fixing format issues
- ⚡ Flexible execution options (skip tests, frontend/backend only, etc.)

### Check items include
- Python code formatting and syntax checks (black, isort, mypy, flake8)
- TypeScript/React syntax and type checks (ESLint, TypeScript)
- All unit tests and integration tests
- Docker container build verification
- Health check endpoint tests

## Windows 10 Environment Notes
- Use PowerShell for all command line operations
- Virtual environment activation: `.\.venv\Scripts\Activate.ps1`
- Path separators: Use backslashes `\` for local paths
- Use semicolons `;` for command chaining in PowerShell