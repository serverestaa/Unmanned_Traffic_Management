# Unmanned Traffic Management System

A comprehensive platform for managing unmanned aerial vehicle (drone) traffic, flight plans, and real-time monitoring in controlled airspace.

## 🚀 Features

- **Authentication & Authorization**
- **Drone Management**
- **Flight Planning**
- **Real-time Monitoring**
- **Restricted Zone Management**
- **Telemetry Data Processing**
- **Structured Logging System**

## 🏗️ Architecture

The project follows a microservices architecture with three main components:

1. **Backend (FastAPI)**
   - RESTful API endpoints
   - Real-time telemetry processing
   - PostgreSQL database integration
   - JWT authentication
   - Structured JSON logging

2. **Frontend (Next.js)**
   - Redux state management
   - Real-time updates
   - Google Maps integration
   - Responsive design

3. **Database (PostgreSQL)**
   - Stores user data, drone information, flight plans
   - Manages restricted zones
   - Tracks telemetry data

## 🛠️ Tech Stack

- **Backend:**
  - Python 3.11
  - FastAPI
  - SQLAlchemy (async)
  - Alembic
  - PostgreSQL
  - JSON logging

- **Frontend:**
  - Next.js
  - Redux Toolkit
  - TypeScript
  - Tailwind CSS

- **Infrastructure:**
  - Docker
  - Docker Compose

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.11 (for local backend development)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd unmanned-traffic-management
```

2. **Environment Setup:**
```bash
# Backend
cp backend/app/.env.example backend/app/.env

# Frontend (if needed)
cp frontend/.env.example frontend/.env
```

3. **Start the services:**
```bash
docker-compose up -d
```

The services will be available at:
- Backend API: http://localhost:8010
- Frontend: http://localhost:3000 (when enabled)
- Database: localhost:5432

## 📝 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8010/docs
- ReDoc: http://localhost:8010/redoc

## 🔍 Monitoring & Logs

- **Backend Logs:** Available in `backend/logs/utm.log*`
- **Structured JSON Logging:** All application events are logged in JSON format
- **Health Check:** Available at `GET /health`

## 🔒 Security

- CORS configuration for specified origins
- JWT-based authentication
- PostgreSQL with secure credentials

## 🧪 Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── drones/
│   │   ├── flights/
│   │   ├── monitoring/
│   │   └── utils/
│   ├── alembic/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── store/
│   │   └── components/
│   └── Dockerfile
└── docker-compose.yml
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
