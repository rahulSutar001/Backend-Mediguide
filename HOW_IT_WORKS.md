# How the MediGuide Backend Works

## 🏗️ Architecture Overview

```
Frontend (React) → FastAPI Backend → Supabase (Database + Storage) → OpenAI (AI)
```

## 📊 Data Flow

### 1. **Report Upload Flow**

```
User uploads image
    ↓
Frontend sends POST /api/v1/reports/upload
    ↓
Backend receives image file
    ↓
Backend uploads to Supabase Storage
    ↓
Backend creates report record in database (status: "processing")
    ↓
Backend triggers background task
    ↓
Background Task:
    1. OCR extracts text from image (Tesseract)
    2. Parse structured data (report type, parameters)
    3. For each parameter:
       - Classify flag (normal/high/low)
       - Generate AI explanation (OpenAI)
       - Store in database
    4. Calculate overall flag level
    5. Update report status to "completed"
    ↓
Frontend polls GET /api/v1/reports/{id}/status
    ↓
When status = "completed", frontend loads report
```

### 2. **Report List Flow**

```
User opens History screen
    ↓
Frontend calls GET /api/v1/reports?page=1&limit=20
    ↓
Backend queries Supabase (respects RLS)
    ↓
Returns paginated list of reports
    ↓
Frontend displays reports
```

### 3. **Chatbot Flow**

```
User asks question about report
    ↓
Frontend sends POST /api/v1/chat/reports/{id}/message
    ↓
Backend:
    1. Verifies report ownership
    2. Gets report context
    3. Checks for diagnosis requests (safety)
    4. Generates response (OpenAI)
    5. Saves conversation
    ↓
Returns response
    ↓
Frontend displays in chat
```

## 🔐 Security Flow

```
Frontend sends request with JWT token
    ↓
Backend verifies JWT with Supabase
    ↓
Extracts user_id from token
    ↓
All database queries use user_id (RLS enforced)
    ↓
User can only access their own data
```

## 🎯 Key Components

### **Report Service** (`app/services/report_service.py`)
- Handles report upload, processing, retrieval
- Orchestrates OCR → AI → Storage pipeline
- Manages background processing

### **OCR Service** (`app/utils/ocr.py`)
- Extracts text from medical report images
- Parses structured data (parameters, values, ranges)
- Detects report type and lab name

### **AI Service** (`app/ai/explanations.py`)
- Generates educational explanations
- **NO diagnosis** - only educational info
- Uses OpenAI with safety prompts

### **Safety Engine** (`app/services/safety_service.py`)
- Classifies test values (normal/high/low)
- Detects critical values
- Calculates overall flag level

### **Premium Service** (`app/services/premium_service.py`)
- Checks subscription status
- Enforces free tier limits
- Tracks usage

## 📡 API Endpoints

### Reports
- `POST /api/v1/reports/upload` - Upload report image
- `GET /api/v1/reports/{id}/status` - Check processing status
- `GET /api/v1/reports/{id}` - Get report details
- `GET /api/v1/reports` - List reports (with filters)
- `GET /api/v1/reports/{id}/parameters` - Get test parameters

### Chat
- `POST /api/v1/chat/reports/{id}/message` - Send message
- `GET /api/v1/chat/reports/{id}/history` - Get chat history

### Premium
- `GET /api/v1/premium/status` - Get subscription status

## 🗄️ Database Schema

### Tables (in Supabase)
- `reports` - Report metadata
- `report_parameters` - Test parameters
- `report_explanations` - AI-generated explanations
- `chat_messages` - Chatbot conversations
- `family_connections` - Family member links
- `subscriptions` - Premium subscriptions

### Row Level Security (RLS)
- Users can only see their own reports
- Family members can see connected reports
- All queries respect RLS automatically

## 🔄 Background Processing

Currently uses FastAPI BackgroundTasks (simple, good for MVP)

**Future:** Can upgrade to Celery + Redis for:
- Better scalability
- Retry logic
- Queue management
- Multiple workers

## 🚀 Current Status

✅ Backend is **fully functional**
✅ All endpoints implemented
✅ Security (JWT + RLS) working
✅ AI explanations working
✅ OCR working

❌ Frontend is **NOT connected** yet
- Still using mock data
- No API calls to backend
- Need to integrate API client

## 🔌 Next Step: Connect Frontend

See `FRONTEND_INTEGRATION.md` for step-by-step guide.
