# MediGuide Backend API

Production-grade FastAPI backend for MediGuide AI - Medical Report Analysis Platform.

## Features

- ✅ **Medical Report Upload & Processing** - OCR extraction, AI analysis
- ✅ **AI Explanations** - Educational explanations of test results (NO diagnosis)
- ✅ **Chatbot** - Report-context aware Q&A with strict safety constraints
- ✅ **Premium Features** - Free tier limits, premium unlocks
- ✅ **Family Connections** - Share reports with family members
- ✅ **Safety Engine** - Critical value detection, flag classification
- ✅ **Supabase Integration** - JWT auth, RLS, storage

## Architecture

- **FastAPI** - Async web framework
- **Supabase** - Auth, database, storage (respects RLS)
- **OpenAI** - LLM for explanations and chatbot
- **Tesseract** - OCR for text extraction
- **Background Tasks** - Async processing pipeline

## Setup

### 1. Prerequisites

- Python 3.11+
- Supabase project
- OpenAI API key
- Tesseract OCR installed

### 2. Install Dependencies

```bash
cd mediguide-backend
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (for storage)
- `OPENAI_API_KEY` - OpenAI API key

### 5. Database Setup

Run SQL migrations in Supabase SQL Editor:

1. `supabase/migrations/001_create_tables.sql` - Creates all tables and RLS policies
2. `supabase/migrations/002_create_storage_bucket.sql` - Creates storage bucket

### 6. Run Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API will be available at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

## API Endpoints

### Reports

- `POST /api/v1/reports/upload` - Upload report image
- `GET /api/v1/reports/{report_id}/status` - Check processing status
- `GET /api/v1/reports/{report_id}` - Get report details
- `GET /api/v1/reports` - List reports (with filters)
- `GET /api/v1/reports/{report_id}/parameters` - Get test parameters
- `POST /api/v1/reports/compare` - Compare reports (Premium)
- `DELETE /api/v1/reports/{report_id}` - Delete report

### Chat

- `POST /api/v1/chat/reports/{report_id}/message` - Send message
- `GET /api/v1/chat/reports/{report_id}/history` - Get chat history

### Family

- `GET /api/v1/family/members` - List family members
- `POST /api/v1/family/invite` - Send invite (Premium for unlimited)
- `POST /api/v1/family/accept/{connection_id}` - Accept connection
- `DELETE /api/v1/family/connections/{connection_id}` - Remove connection

### Premium

- `GET /api/v1/premium/status` - Get subscription status

## Authentication

All endpoints require JWT authentication:

```http
Authorization: Bearer <supabase_jwt_token>
```

## Frontend Integration

### Upload Report

```typescript
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('http://api.mediguide.ai/api/v1/reports/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${supabaseToken}`
  },
  body: formData
});

const { report_id, status } = await response.json();
```

### Get Report Status

```typescript
const response = await fetch(
  `http://api.mediguide.ai/api/v1/reports/${reportId}/status`,
  {
    headers: {
      'Authorization': `Bearer ${supabaseToken}`
    }
  }
);

const { status, progress } = await response.json();
```

### List Reports

```typescript
const response = await fetch(
  `http://api.mediguide.ai/api/v1/reports?page=1&limit=20&flag_level=red`,
  {
    headers: {
      'Authorization': `Bearer ${supabaseToken}`
    }
  }
);

const { items, total, has_next } = await response.json();
```

## Safety Constraints

**CRITICAL:** This API enforces strict safety rules:

- ❌ **NO medical diagnosis**
- ❌ **NO treatment recommendations**
- ❌ **NO prescription suggestions**
- ✅ **ONLY educational information**
- ✅ **Always suggests "consult your doctor" for abnormal values**

## Premium Features

Free tier limits:
- 3 reports/month
- 2 family members
- Basic AI explanations

Premium unlocks:
- Unlimited reports
- Unlimited family members
- Detailed AI explanations
- Report comparison
- Health trends

## Development

### Project Structure

```
mediguide-backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/                 # Core config, security
│   ├── api/routes/          # API endpoints
│   ├── services/            # Business logic
│   ├── schemas/             # Pydantic models
│   ├── supabase/            # Supabase integration
│   ├── ai/                  # AI services
│   └── utils/               # Utilities
├── supabase/migrations/     # SQL migrations
└── requirements.txt
```

### Running Tests

```bash
pytest
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use production-grade ASGI server (Gunicorn + Uvicorn)
3. Set up proper CORS origins
4. Use Redis + Celery for background tasks (optional)
5. Configure proper logging
6. Set up monitoring (Sentry, etc.)

## License

Proprietary - MediGuide AI
