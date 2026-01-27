# Frontend Integration Guide

Complete guide for integrating the MediGuide FastAPI backend with your React frontend.

## Base URL

```typescript
const API_BASE_URL = 'http://localhost:8000/api/v1'; // Development
// const API_BASE_URL = 'https://api.mediguide.ai/api/v1'; // Production
```

## Authentication

All API requests require a Supabase JWT token:

```typescript
import { supabase } from '@/lib/supabase';

// Get current session token
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Use in API calls
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## API Client Helper

Create a reusable API client:

```typescript
// lib/api.ts
import { supabase } from '@/lib/supabase';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  return {
    'Authorization': `Bearer ${session?.access_token}`,
    'Content-Type': 'application/json'
  };
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'API request failed');
  }
  
  return response.json();
}

// Upload file helper
export async function uploadFile(
  endpoint: string,
  file: File,
  additionalData?: Record<string, string>
): Promise<any> {
  const { data: { session } } = await supabase.auth.getSession();
  
  const formData = new FormData();
  formData.append('file', file);
  
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session?.access_token}`
    },
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Upload failed');
  }
  
  return response.json();
}
```

## Report Upload

```typescript
// In ScanScreen.tsx or similar
import { uploadFile } from '@/lib/api';

const handleScan = async (imageFile: File) => {
  try {
    const result = await uploadFile('/reports/upload', imageFile);
    
    console.log('Report uploaded:', result.report_id);
    console.log('Status:', result.status);
    
    // Navigate to scanning screen
    setCurrentScreen('scanning');
    
    // Poll for status
    pollReportStatus(result.report_id);
  } catch (error) {
    console.error('Upload failed:', error);
    setCurrentScreen('scan-error');
  }
};

// Poll report status
const pollReportStatus = async (reportId: string) => {
  const interval = setInterval(async () => {
    try {
      const status = await apiRequest<{
        report_id: string;
        status: 'processing' | 'completed' | 'failed';
        progress?: number;
      }>(`/reports/${reportId}/status`);
      
      if (status.status === 'completed') {
        clearInterval(interval);
        setCurrentScreen('report-result');
        // Load report data
      } else if (status.status === 'failed') {
        clearInterval(interval);
        setCurrentScreen('scan-error');
      }
    } catch (error) {
      console.error('Status check failed:', error);
    }
  }, 2000); // Poll every 2 seconds
};
```

## List Reports

```typescript
// In HistoryScreen.tsx
import { apiRequest } from '@/lib/api';

const loadReports = async () => {
  try {
    const response = await apiRequest<{
      items: Report[];
      total: number;
      page: number;
      limit: number;
      has_next: boolean;
      has_prev: boolean;
    }>(`/reports?page=1&limit=20&flag_level=${filters.flag}&time_range=${filters.time}`);
    
    setReports(response.items);
  } catch (error) {
    console.error('Failed to load reports:', error);
  }
};
```

## Get Report Details

```typescript
// In ReportResultScreen.tsx
const loadReportDetails = async (reportId: string) => {
  try {
    // Get report
    const report = await apiRequest<ReportResponse>(`/reports/${reportId}`);
    
    // Get parameters with explanations
    const { parameters } = await apiRequest<{ parameters: TestParameter[] }>(
      `/reports/${reportId}/parameters`
    );
    
    setReport(report);
    setParameters(parameters);
  } catch (error) {
    console.error('Failed to load report:', error);
  }
};
```

## Chatbot

```typescript
// In ReportResultScreen.tsx
const sendChatMessage = async (message: string) => {
  try {
    const response = await apiRequest<ChatMessageResponse>({
      method: 'POST',
      endpoint: `/chat/reports/${reportId}/message`,
      body: JSON.stringify({ message, report_id: reportId })
    });
    
    // Add to chat history
    setChatHistory(prev => [...prev, {
      role: 'user',
      content: message
    }, {
      role: 'assistant',
      content: response.response
    }]);
  } catch (error) {
    console.error('Chat failed:', error);
  }
};
```

## Premium Status

```typescript
// In HomeScreen.tsx or AppContext
const checkPremiumStatus = async () => {
  try {
    const status = await apiRequest<PremiumStatusResponse>('/premium/status');
    
    setFreeScansLeft(
      status.reports_limit 
        ? status.reports_limit - status.reports_used_this_month 
        : null
    );
    setIsPremium(status.is_premium);
  } catch (error) {
    console.error('Failed to check premium:', error);
  }
};
```

## Error Handling

```typescript
try {
  const result = await apiRequest('/reports');
} catch (error) {
  if (error.message.includes('PREMIUM_REQUIRED')) {
    // Show premium modal
    setShowPremiumModal(true);
  } else if (error.message.includes('403')) {
    // Free tier limit reached
    toast.error('Free tier limit reached. Upgrade to premium.');
  } else {
    // Generic error
    toast.error('An error occurred. Please try again.');
  }
}
```

## TypeScript Types

Add these types to your frontend:

```typescript
// types/api.ts
export interface ReportResponse {
  id: string;
  user_id: string;
  date: string;
  type: string;
  lab_name?: string;
  flag_level: 'green' | 'yellow' | 'red';
  uploaded_to_abdm: boolean;
  status: 'processing' | 'completed' | 'failed';
  image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface TestParameter {
  id: string;
  report_id: string;
  name: string;
  value: string;
  unit?: string;
  normal_range: string;
  flag: 'normal' | 'high' | 'low';
  explanation?: {
    what: string;
    meaning: string;
    causes: string[];
    next_steps: string[];
  };
}

export interface PremiumStatusResponse {
  is_premium: boolean;
  subscription_tier: 'free' | 'premium';
  expires_at?: string;
  reports_used_this_month: number;
  reports_limit: number | null;
  family_members_count: number;
  family_members_limit: number | null;
}
```

## Environment Variables

Add to your frontend `.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Complete Example: Report Upload Flow

```typescript
// Complete example in ScanScreen.tsx
import { useState } from 'react';
import { uploadFile, apiRequest } from '@/lib/api';
import { useApp } from '@/contexts/AppContext';

export function ScanScreen() {
  const { setCurrentScreen } = useApp();
  const [uploading, setUploading] = useState(false);
  
  const handleUpload = async (file: File) => {
    setUploading(true);
    
    try {
      // 1. Upload image
      const { report_id } = await uploadFile('/reports/upload', file);
      
      // 2. Navigate to scanning screen
      setCurrentScreen('scanning');
      
      // 3. Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const status = await apiRequest(`/reports/${report_id}/status`);
          
          if (status.status === 'completed') {
            clearInterval(pollInterval);
            setCurrentScreen('report-result');
            // Report is ready
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setCurrentScreen('scan-error');
          }
        } catch (error) {
          console.error('Status check failed:', error);
        }
      }, 2000);
      
    } catch (error: any) {
      if (error.message.includes('limit reached')) {
        // Show premium modal
        setShowPremiumModal(true);
      } else {
        setCurrentScreen('scan-error');
      }
    } finally {
      setUploading(false);
    }
  };
  
  return (
    // Your UI
  );
}
```
