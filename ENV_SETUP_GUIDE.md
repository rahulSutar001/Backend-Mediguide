# Environment Variables Setup Guide

## 📍 File Location

The `.env` file should be located at:
```
mediguide-backend/.env
```

**Important:** The `.env` file is in the same directory as `app/` and `requirements.txt`.

## ✅ Required Credentials

### 1. **Supabase Configuration** (REQUIRED)

Get these from your Supabase project dashboard: https://app.supabase.com

```env
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
```

**Where to find:**
- Go to your Supabase project → Settings → API
- `SUPABASE_URL` = Project URL
- `SUPABASE_ANON_KEY` = anon/public key
- `SUPABASE_SERVICE_ROLE_KEY` = service_role key (⚠️ Keep secret!)

### 2. **OpenAI Configuration** (REQUIRED for AI features)

Get from: https://platform.openai.com/api-keys

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

**Note:** 
- `gpt-4o-mini` is cost-effective (recommended)
- Can upgrade to `gpt-4` for better quality (more expensive)

### 3. **OCR Configuration** (Optional - defaults to Tesseract)

```env
OCR_SERVICE=tesseract
```

**Options:**
- `tesseract` - Free, local (default)
- `google_vision` - Requires `GOOGLE_VISION_API_KEY`
- `aws_textract` - Requires AWS credentials

### 4. **Application Settings** (Optional - has defaults)

```env
API_V1_PREFIX=/api/v1
PROJECT_NAME=MediGuide API
VERSION=1.0.0
DEBUG=False
```

### 5. **CORS Origins** (Update for your frontend)

```env
CORS_ORIGINS=http://localhost:8080,http://localhost:3000,http://localhost:5173
```

Add your frontend URL(s) here.

### 6. **Storage** (Optional - has default)

```env
STORAGE_BUCKET=medical-reports
```

### 7. **Free Tier Limits** (Optional - has defaults)

```env
FREE_TIER_REPORTS_PER_MONTH=3
FREE_TIER_FAMILY_MEMBERS=2
```

## 📋 Complete .env Template

```env
# ============================================
# REQUIRED - Fill these in
# ============================================

# Supabase (Get from Supabase Dashboard → Settings → API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# OpenAI (Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# ============================================
# OPTIONAL - Has defaults, can leave as-is
# ============================================

# OCR Configuration
OCR_SERVICE=tesseract

# Application Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=MediGuide API
VERSION=1.0.0
DEBUG=False

# CORS Origins (Update with your frontend URL)
CORS_ORIGINS=http://localhost:8080,http://localhost:3000,http://localhost:5173

# Storage
STORAGE_BUCKET=medical-reports

# Free Tier Limits
FREE_TIER_REPORTS_PER_MONTH=3
FREE_TIER_FAMILY_MEMBERS=2
```

## 🔍 How to Verify

After creating `.env`, test if it loads correctly:

```bash
cd mediguide-backend
python -c "from app.core.config import settings; print('✅ Config loaded:', settings.SUPABASE_URL[:20] + '...')"
```

If you see an error about missing `SUPABASE_URL`, the `.env` file is not being read correctly.

## ⚠️ Important Notes

1. **Never commit `.env` to Git** - It's already in `.gitignore`
2. **Service Role Key is Secret** - Never expose it in frontend code
3. **OpenAI API Key** - Keep it secret, has billing implications
4. **File Location** - Must be in `mediguide-backend/` root (same level as `app/`)

## 🚀 Quick Setup Steps

1. Copy `env.example` to `.env`:
   ```bash
   cd mediguide-backend
   copy env.example .env
   ```

2. Open `.env` in a text editor

3. Fill in the **REQUIRED** fields:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENAI_API_KEY`

4. Update `CORS_ORIGINS` with your frontend URL

5. Save the file

6. Test: `python -c "from app.core.config import settings; print(settings.SUPABASE_URL)"`
