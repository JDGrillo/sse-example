# Text Correction Application

Real-time text correction web application powered by **Azure OpenAI GPT-4o** with streaming suggestions.

## 🎯 Overview

A modern web application that provides intelligent text correction suggestions as users type. The React frontend displays inline suggestions with smooth animations, while the Python FastAPI backend streams corrections from Azure OpenAI GPT-4o via APIM using Server-Sent Events.

### Key Features

✅ **Real-time streaming suggestions** - Corrections appear progressively as the model generates them  
✅ **Non-blocking UI** - Continue typing while the model processes previous text  
✅ **Automatic request cancellation** - Previous requests cancelled when you keep typing  
✅ **Staggered animations** - Suggestions cascade in smoothly (150ms delay between each)  
✅ **Visual feedback** - Live chunk counter and streaming preview in dev mode  
✅ **Accept/Reject controls** - Easy suggestion management with keyboard shortcuts  
✅ **Smart debouncing** - 3-second delay prevents excessive API calls  

---

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │
│   (TypeScript)  │
│                 │
│  • TextEditor   │ ← User types text
│  • StreamingClient │
│  • SuggestionRenderer │
└────────┬────────┘
         │ HTTP POST /api/corrections/stream
         │ (Server-Sent Events)
         ▼
┌─────────────────┐
│ FastAPI Backend │
│    (Python)     │
│                 │
│  • SSE Endpoint │
│  • AgentService │
└────────┬────────┘
         │ AsyncAzureOpenAI
         │ (APIM Authentication)
         ▼
┌─────────────────┐
│ Azure OpenAI    │
│    GPT-4o       │
│  (via APIM)     │
└─────────────────┘
```

### Technology Stack

**Frontend:**
- React 18.2 with TypeScript
- Vite (build tool)
- Server-Sent Events (SSE) client
- CSS animations & transitions

**Backend:**
- Python 3.10+
- FastAPI 0.100.0
- AsyncAzureOpenAI 2.26.0
- Uvicorn (ASGI server)

---

## 📦 Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Azure OpenAI** deployment with GPT-4o model
- **Azure APIM** endpoint with API key

---

## 🚀 Quick Start

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (see .env.example)
# Create .env file with:
# AZURE_OPENAI_ENDPOINT=https://your-apim-endpoint.azure-api.net
# AZURE_OPENAI_API_KEY=your-api-key
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
# AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Start server
python -m uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**

### 2. Frontend Setup

```powershell
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## 🎮 Usage

1. **Open browser** to http://localhost:3000
2. **Start typing** in the text area
3. **Wait 3 seconds** - Suggestions will start streaming in
4. **Keep typing** - Previous request auto-cancels, new one starts
5. **Click numbered badges** - View suggestion details
6. **Accept or Reject** - Apply or dismiss suggestions

### Manual Trigger

Click **"Correct Text"** button to bypass debouncing and get immediate corrections.

---

## 🔄 Server-Sent Events Flow

The application uses SSE for true streaming:

```
User types → Debounce (3s) → POST to /api/corrections/stream
                                    ↓
                            Backend fetches from Azure OpenAI
                                    ↓
                            Chunks stream back via SSE:
                            • event: start
                            • event: chunk (multiple)
                            • event: complete
                            • event: close
                                    ↓
                            Frontend parses events → Updates UI
                            Suggestions appear with cascade animation
```

### Event Types

- **start**: Stream initiated
- **chunk**: Single token/word from GPT-4o (real-time)
- **complete**: Full JSON with parsed corrections
- **error**: Error occurred
- **close**: Connection closed

---

## 🎨 Recent Improvements

### v1.1 - Non-Blocking UI (March 2026)

**Problem:** Textarea locked during processing, suggestions appeared all at once

**Solution:**
1. ✅ Removed `disabled` attribute from textarea
2. ✅ Implemented request cancellation when user continues typing
3. ✅ Added staggered animations (150ms delay per suggestion)
4. ✅ Enhanced visual feedback with chunk counters
5. ✅ Added live streaming preview (dev mode)

**Impact:**
- Truly async/non-blocking experience
- No more "frozen" feeling during API calls
- Smooth cascading suggestion appearance
- Console logs: "🚫 Cancelled previous request - user is still typing"

### Technical Details

**Request Cancellation:**
```typescript
// When user types again, abort previous stream
if (abortControllerRef.current) {
  abortControllerRef.current.abort();
  console.log('🚫 Cancelled previous request - user is still typing');
}
```

**Staggered Animations:**
```typescript
// Each suggestion gets increasing delay
animationDelay: `${index * 150}ms`
```

**Non-Blocking Architecture:**
```typescript
// Returns AbortController immediately
const controller = await streamingAPIClient.streamCorrections(...);
// Stream processes in background
```

---

## 📁 Project Structure

```
suggestion-streaming/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── config/
│   │   └── settings.py        # Environment configuration
│   ├── routes/
│   │   └── corrections.py     # SSE streaming endpoint
│   └── services/
│       └── agent_service.py   # Azure OpenAI integration
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts         # Vite configuration (proxy to port 8000)
│   ├── src/
│   │   ├── App.tsx           # Main app component
│   │   ├── components/
│   │   │   ├── TextEditor.tsx         # Text input with debouncing
│   │   │   ├── TextEditor.css         # Editor styles & animations
│   │   │   ├── SuggestionRenderer.tsx # Sidebar suggestion display
│   │   │   └── SuggestionRenderer.css
│   │   ├── services/
│   │   │   └── streamingClient.ts    # SSE client
│   │   ├── hooks/
│   │   │   └── useDebounce.ts        # Debouncing hook
│   │   └── types/
│   │       └── corrections.ts        # TypeScript interfaces
│
└── docs/
    └── plan/
        └── text-correction-app-001/
            ├── task_breakdown.yaml     # Project plan & task tracking
            └── logs/                   # Task completion logs
```

---

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.azure-api.net
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Application Settings
ENVIRONMENT=development
MAX_TEXT_LENGTH=10000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend Configuration

The frontend automatically proxies `/api/*` requests to `http://localhost:8000` (configured in `vite.config.ts`).

---

## 🐛 Troubleshooting

### Frontend won't start

**Issue:** `npm run dev` returns Exit Code: 1  
**Solution:** Ensure backend is running on port 8000. Check `vite.config.ts` proxy target.

### CORS errors

**Issue:** `Access-Control-Allow-Origin` errors in console  
**Solution:** Verify `CORS_ORIGINS` in backend `.env` includes your frontend URL.

### Streaming not working

**Issue:** Chunks don't appear progressively  
**Solution:** 
1. Check browser DevTools Network tab for SSE connection
2. Verify Azure OpenAI credentials in `.env`
3. Check backend logs for errors

### Port conflicts

**Issue:** `Address already in use`  
**Solution:**
```powershell
# Find process using port 8000
netstat -ano | Select-String "8000"
# Kill process by PID
taskkill /PID <pid> /F
```

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:3000  
- [ ] Typing triggers debounced request (3 seconds)
- [ ] Manual button triggers immediate request
- [ ] Suggestions appear with cascade animation
- [ ] Typing during processing cancels previous request
- [ ] Accept button applies suggestion
- [ ] Reject button dismisses suggestion
- [ ] Numbered badges clickable and show details
- [ ] Browser console shows chunk counters

### Validation Status

✅ **Integration Testing** - Completed (March 17, 2026)
- Status: Pass with minor issues
- All core features validated
- Code quality: Good
- See: `docs/plan/text-correction-app-001/logs/task-validator_integration-testing_20260317_120000.yaml`

⏳ **Browser Testing** - Pending
⏳ **Documentation** - In Progress

---

## 📊 Performance

- **Debounce delay:** 3 seconds (configurable in `TextEditor.tsx`)
- **Animation stagger:** 150ms per suggestion (inline), 100ms (sidebar)
- **Target TTFT:** <5 seconds (Time To First Token)
- **Request cancellation:** Immediate (AbortController)

---

## 🔐 Security Notes

- **API keys** stored in `.env` (never commit!)
- **CORS** restricted to localhost in development
- **Input validation** on backend (max 10,000 characters)
- **Request cancellation** prevents resource waste

---

## 🚧 Known Limitations

1. **Local deployment only** - Azure deployment not implemented
2. **No automated tests** - Manual testing only (unit tests planned)
3. **Single concurrent stream** - Multiple requests cancelled
4. **No retry logic** - Failed requests require manual retry

---

## 📝 Contributing

### Code Style

- **Backend:** Follow PEP 8, use type hints, lazy logging
- **Frontend:** TypeScript strict mode, functional components, hooks

### Linting Issues (To Fix)

1. **Lazy logging:** Replace f-strings with `%` formatting
   ```python
   # ❌ Bad
   logger.info(f"Value: {x}")
   
   # ✅ Good
   logger.info("Value: %s", x)
   ```

2. **Specific exceptions:** Catch specific types instead of `Exception`
   ```python
   # ❌ Bad
   except Exception as e:
   
   # ✅ Good
   except (json.JSONDecodeError, httpx.HTTPError) as e:
   ```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [React Hooks](https://react.dev/reference/react)

---

## 📄 License

Copyright © 2026. All rights reserved.

---

## 🙋‍♂️ Support

For issues or questions, check:
1. This README's troubleshooting section
2. Backend logs in terminal
3. Browser DevTools console
4. Task breakdown: `docs/plan/text-correction-app-001/task_breakdown.yaml`

---

**Status:** ✅ Core implementation complete | ⏳ Browser testing pending  
**Last Updated:** March 17, 2026  
**Validated By:** task-validator agent
