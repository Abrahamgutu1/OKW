# Full Stack AI Application Challenge

Complete implementation of both frontend (Job Board) and backend (Real-time Digital Human) challenges.

## 📋 Table of Contents

- [Overview](#overview)
- [Part 1: Frontend - Job Board](#part-1-frontend---job-board)
- [Part 2: Backend - Real-time Digital Human](#part-2-backend---real-time-digital-human)
- [Setup Instructions](#setup-instructions)
- [Architecture](#architecture)
- [Features](#features)
- [Demo Video](#demo-video)

## 🎯 Overview

This project demonstrates:
1. **Frontend Engineering**: Responsive job board with AI recommendations
2. **Backend Engineering**: Real-time digital human using LiveKit + Tavus integration

## 📱 Part 1: Frontend - Job Board

### Features Implemented

✅ **Core Requirements**
- Responsive design (Desktop + Mobile H5 view)
- AI-powered job recommendations section
- Job listings with filters and search
- Professional UI based on best practices

✅ **Enhanced Features**
- Smooth animations and transitions
- Interactive filters (job type, experience level, salary range, work mode)
- Bookmark functionality
- Real-time search with location
- Quick filter tags
- Pagination
- Mobile-responsive navigation

### Tech Stack
- **HTML5**: Semantic markup
- **CSS3**: Custom properties, Grid, Flexbox, animations
- **Vanilla JavaScript**: ES6+, async/await
- **No frameworks**: Pure implementation for performance

### Key Features

1. **AI Recommendations**
   - Match score display (percentage)
   - Personalized job cards
   - Visual indicators for high matches

2. **Advanced Filtering**
   - Multiple filter categories
   - Real-time filter application
   - Salary range slider
   - Clear all functionality

3. **Responsive Design**
   - Mobile-first approach
   - Breakpoints: 480px, 768px, 1024px
   - Adaptive layouts and navigation

4. **Interactive Elements**
   - Hover effects
   - Click animations
   - Toast notifications
   - Smooth scrolling

### File Structure
```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Complete styling with responsive design
└── script.js           # Interactive functionality
```

## 🤖 Part 2: Backend - Real-time Digital Human

### Features Implemented

✅ **Core Requirements**
- LiveKit integration for real-time audio streaming
- Tavus Persona API integration
- Real-time 2D/3D avatar rendering
- Low-latency audio-video synchronization
- Text input → AI avatar response pipeline

✅ **Enhanced Features**
- RESTful API for session management
- WebSocket support for real-time communication
- Conversation history tracking
- Health check endpoints
- Session lifecycle management

### Tech Stack
- **Python 3.8+**
- **FastAPI**: High-performance async web framework
- **LiveKit**: Real-time communication
- **Tavus API**: Digital human rendering
- **WebSockets**: Real-time bidirectional communication
- **Uvicorn**: ASGI server

### Architecture Components

1. **API Server (main.py)**
   - Session creation and management
   - Tavus integration
   - LiveKit token generation
   - WebSocket endpoints

2. **LiveKit Agent (agent.py)**
   - Audio stream handling
   - Real-time audio processing
   - Participant management
   - Audio synchronization

3. **Frontend Demo (demo.html)**
   - Interactive UI
   - WebSocket client
   - Video embedding
   - Real-time messaging

### API Endpoints

```
GET  /                          # Health check
GET  /health                    # System status
POST /api/sessions              # Create new session
GET  /api/sessions/{id}         # Get session details
POST /api/sessions/{id}/end     # End session
POST /api/personas              # Create Tavus persona
WS   /ws/{session_id}           # WebSocket connection
```

### File Structure
```
backend/
├── main.py              # FastAPI server with Tavus integration
├── agent.py             # LiveKit agent for audio processing
├── demo.html            # Frontend demo interface
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js (optional, for frontend development server)
- LiveKit server (can use cloud or local)
- Tavus API key

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Open in browser**
```bash
# Option 1: Direct file
open index.html

# Option 2: Use a local server (recommended)
python -m http.server 8080
# Then visit http://localhost:8080
```

3. **No build required** - Pure HTML/CSS/JS

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Tavus Configuration
TAVUS_API_KEY=your_tavus_api_key
TAVUS_REPLICA_ID=your_replica_id
TAVUS_PERSONA_ID=your_persona_id
```

5. **Start the server**
```bash
python main.py
```

Server will start on `http://localhost:8000`

6. **Access demo interface**
```
http://localhost:8000/demo.html
```

### Getting API Keys

**LiveKit:**
1. Sign up at [livekit.io](https://livekit.io)
2. Create a project
3. Get API key and secret from dashboard

**Tavus:**
1. Sign up at [tavus.io](https://tavus.io)
2. Navigate to API section
3. Generate API key
4. Create a replica and persona
5. Copy IDs

## 🏗️ Architecture

### Frontend Architecture

```
┌─────────────────────────────────────┐
│         User Interface              │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────┐    │
│  │  Hero    │  │ Search Bar   │    │
│  └──────────┘  └──────────────┘    │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │  AI Recommendations         │   │
│  │  (Match scores, cards)      │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────┐    │
│  │ Filters  │  │  Jobs List   │    │
│  │ Sidebar  │  │  (Paginated) │    │
│  └──────────┘  └──────────────┘    │
└─────────────────────────────────────┘
```

### Backend Architecture

```
┌──────────────────────────────────────────┐
│           Client Browser                  │
│  ┌────────────┐      ┌──────────────┐   │
│  │ Demo HTML  │◄────►│  WebSocket   │   │
│  └────────────┘      └──────────────┘   │
└──────────────────────────────────────────┘
              │                │
              │ HTTP           │ WS
              ▼                ▼
┌──────────────────────────────────────────┐
│         FastAPI Server (main.py)          │
│  ┌────────────────────────────────────┐  │
│  │  Session Manager                   │  │
│  │  ├─ Create/End sessions            │  │
│  │  ├─ Token generation                │  │
│  │  └─ WebSocket handling             │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
              │                │
    ┌─────────┴────────┐      │
    │                  │      │
    ▼                  ▼      ▼
┌─────────┐     ┌──────────────────┐
│ LiveKit │     │   Tavus API      │
│ Server  │     │  ┌─────────────┐ │
│         │     │  │ Personas    │ │
│ Audio   │◄───►│  │ Replicas    │ │
│ Streams │     │  │ Conversations│ │
└─────────┘     │  └─────────────┘ │
                └──────────────────┘
```

## ✨ Features

### Frontend Features

1. **Search & Discovery**
   - Full-text search
   - Location filtering
   - Quick filter tags
   - Sort options

2. **AI-Powered Matching**
   - Percentage match scores
   - Personalized recommendations
   - Skill-based matching
   - Visual indicators

3. **Interactive Filtering**
   - Job type selection
   - Experience level
   - Salary range slider
   - Work mode (Remote/Hybrid/On-site)

4. **User Experience**
   - Smooth animations
   - Toast notifications
   - Responsive design
   - Accessibility features

### Backend Features

1. **Session Management**
   - Create/end sessions
   - Token generation
   - Session tracking
   - Lifecycle management

2. **Real-time Communication**
   - WebSocket support
   - Bidirectional messaging
   - Connection monitoring
   - Error handling

3. **Tavus Integration**
   - Persona creation
   - Conversation management
   - Avatar rendering
   - TTS/STT processing

4. **LiveKit Integration**
   - Audio streaming
   - Room management
   - Participant handling
   - Quality optimization

## 🎥 Demo Video

Create a video walkthrough covering:

1. **Frontend Demo (5-7 minutes)**
   - Homepage tour
   - Search functionality
   - AI recommendations
   - Filter usage
   - Mobile responsiveness
   - Interactive elements

2. **Backend Demo (8-10 minutes)**
   - Environment setup
   - API endpoints
   - Session creation
   - Live conversation
   - Avatar interaction
   - WebSocket communication
   - Error handling

## 📝 Implementation Notes

### Frontend Development Decisions

1. **No Framework**: Used vanilla JavaScript for:
   - Better performance
   - Smaller bundle size
   - Full control over implementation
   - Educational value

2. **CSS Architecture**: 
   - CSS custom properties for theming
   - Mobile-first responsive design
   - BEM-like naming conventions
   - Modular component styles

3. **JavaScript Patterns**:
   - Module pattern for organization
   - Event delegation for performance
   - Async/await for cleaner code
   - Intersection Observer for animations

### Backend Development Decisions

1. **FastAPI**: Chosen for:
   - High performance (async support)
   - Automatic API documentation
   - Type hints and validation
   - WebSocket support

2. **Architecture**:
   - Separation of concerns
   - Manager pattern for state
   - Async operations throughout
   - Error handling and logging

3. **Integration Strategy**:
   - LiveKit for audio transport
   - Tavus for avatar rendering
   - WebSocket for real-time updates
   - RESTful API for management

## 🧪 Testing

### Frontend Testing

```bash
# Open in different browsers
- Chrome
- Firefox
- Safari
- Mobile browsers

# Test different screen sizes
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667
```

### Backend Testing

```bash
# Test API endpoints
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_name": "Test User"}'

# Check WebSocket
# Use browser console or wscat
```

## 🔧 Troubleshooting

### Frontend Issues

**Issue**: Styles not loading
- Clear browser cache
- Check file paths
- Verify CSS file is accessible

**Issue**: JavaScript not working
- Check browser console for errors
- Verify script.js is loaded
- Check for syntax errors

### Backend Issues

**Issue**: API not starting
- Check Python version (3.8+)
- Verify all dependencies installed
- Check port 8000 is available

**Issue**: Tavus connection failed
- Verify API key is correct
- Check network connectivity
- Ensure replica and persona IDs are valid

**Issue**: LiveKit errors
- Verify LiveKit server is running
- Check API credentials
- Review LiveKit logs

## 📚 API Documentation

When running the server, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Security Notes

- Never commit `.env` file
- Use environment variables for secrets
- Implement rate limiting in production
- Add authentication for production use
- Validate all user inputs
- Use HTTPS in production

## 🚀 Production Deployment

### Frontend

```bash
# Deploy to static hosting
- Netlify
- Vercel
- GitHub Pages
- AWS S3 + CloudFront
```

### Backend

```bash
# Deploy using
- Docker + AWS ECS
- Google Cloud Run
- Heroku
- DigitalOcean App Platform

# Use production ASGI server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📄 License

This project is created for the Full Stack Software Engineer challenge.

## 📧 Contact

For questions or clarifications, contact: kevin@libaspace.com

---

## Completion Checklist

### Frontend ✅
- [x] Responsive job board design
- [x] AI recommendation section
- [x] Mobile H5 view
- [x] Interactive JS effects
- [x] Search functionality
- [x] Filter system
- [x] Professional styling

### Backend ✅
- [x] LiveKit integration
- [x] Tavus API integration
- [x] Real-time audio streaming
- [x] Avatar rendering
- [x] Text-to-speech
- [x] Audio-video synchronization
- [x] Low latency implementation
- [x] WebSocket support
- [x] Demo interface

### Documentation ✅
- [x] Setup instructions
- [x] API documentation
- [x] Architecture diagrams
- [x] Feature descriptions
- [x] Troubleshooting guide

**Estimated Completion Time**: 
- Frontend: 1 day ✅
- Backend: 4 days ✅
- Total: 5 days ✅
