#!/bin/bash
set -e

echo "========================================="
echo "  Google Ads AI Agent - Setup"
echo "========================================="

# Check prerequisites
echo ""
echo "[1/5] Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: node is required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "ERROR: npm is required"; exit 1; }

echo "  python3: $(python3 --version)"
echo "  node: $(node --version)"
echo "  npm: $(npm --version)"

# Check Docker or PostgreSQL
if command -v docker >/dev/null 2>&1; then
    echo "  docker: available"
    HAS_DOCKER=1
elif command -v psql >/dev/null 2>&1; then
    echo "  psql: available (using local PostgreSQL)"
    HAS_DOCKER=0
else
    echo ""
    echo "WARNING: Neither Docker nor PostgreSQL found."
    echo "Please install one of the following:"
    echo "  - Docker: https://www.docker.com/get-started"
    echo "  - PostgreSQL: brew install postgresql@16"
    echo ""
    echo "After installing, run this script again."
    exit 1
fi

# Start PostgreSQL
echo ""
echo "[2/5] Starting PostgreSQL..."

if [ "$HAS_DOCKER" = "1" ]; then
    docker compose up -d
    echo "  PostgreSQL started via Docker"
    sleep 3
else
    echo "  Using local PostgreSQL"
    echo "  Make sure it's running and has database 'googleads_analyzer'"
    echo "  Create it with: createdb googleads_analyzer"
fi

# Setup Backend
echo ""
echo "[3/5] Setting up backend..."

cd backend

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

pip install -q fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic \
    "google-ads>=25.1.0" anthropic pydantic-settings python-dotenv \
    google-auth-oauthlib httpx pytest pytest-asyncio

echo "  Python dependencies installed"

# Run migrations
echo ""
echo "[4/5] Running database migrations..."

cd /Users/mukaitakaaki/projects/googleadsanalyzerv2/backend
.venv/bin/python -m alembic upgrade head
echo "  Migrations complete"

# Setup Frontend
echo ""
echo "[5/5] Setting up frontend..."

cd /Users/mukaitakaaki/projects/googleadsanalyzerv2/frontend
npm install --cache /tmp/npm-cache 2>/dev/null || npm install
echo "  Frontend dependencies installed"

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit backend/.env with your API keys:"
echo "   - GOOGLE_ADS_* credentials"
echo "   - ANTHROPIC_API_KEY"
echo ""
echo "2. Start the backend:"
echo "   cd backend && .venv/bin/uvicorn app.main:app --reload"
echo ""
echo "3. Start the frontend (in another terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "4. Open http://localhost:3000"
echo ""
echo "5. Click 'Run Analysis' to generate your first report"
echo ""
