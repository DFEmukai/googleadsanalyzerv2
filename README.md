# Google Ads AI Agent

Google Ads analysis and improvement proposal system powered by Claude AI.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (via Docker or local install)
- Google Ads API credentials (Developer Token + OAuth)
- Anthropic API key

## Quick Start

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Setup backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic \
    "google-ads>=25.1.0" anthropic pydantic-settings python-dotenv \
    google-auth-oauthlib httpx

# 3. Configure environment
cp .env.example .env  # (from project root)
# Edit backend/.env with your API keys

# 4. Run migrations
alembic upgrade head

# 5. Start backend
uvicorn app.main:app --reload

# 6. In a new terminal - setup frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Architecture

```
backend/   - Python FastAPI (API server, Google Ads & Claude integration)
frontend/  - Next.js 14 (Dashboard UI, dark theme)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/dashboard/summary | KPI summary with signals |
| GET | /api/v1/dashboard/trends | Weekly trend data |
| GET | /api/v1/campaigns | Campaign list |
| GET | /api/v1/reports | Weekly reports list |
| GET | /api/v1/reports/latest | Latest report |
| GET | /api/v1/reports/{id} | Report detail |
| GET | /api/v1/proposals | Proposals list (filterable) |
| PATCH | /api/v1/proposals/{id}/status | Update proposal status |
| POST | /api/v1/analysis/run | Trigger weekly analysis |

## Google Ads API Setup

1. Create a Google Cloud project
2. Enable the Google Ads API
3. Create OAuth 2.0 credentials (Desktop App)
4. Run the refresh token script:
   ```bash
   cd backend
   python scripts/generate_refresh_token.py
   ```
5. Add the refresh token to `backend/.env`
