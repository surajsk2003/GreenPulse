# 🌱 GreenPulse: Smart Energy Management Platform

> An AI-powered energy management system for campuses that provides real-time monitoring, analytics, and optimization recommendations through an intelligent dashboard.

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Angular](https://img.shields.io/badge/angular-17-red)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Status](https://img.shields.io/badge/status-prototype-yellow)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Project Architecture](#project-architecture)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Known Issues](#known-issues)
- [Future Work](#future-work)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

## 🧠 Overview

GreenPulse addresses the critical need for intelligent energy management in campus environments. With rising energy costs and environmental concerns, educational institutions require sophisticated tools to monitor, analyze, and optimize their energy consumption patterns.

**Problem Statement:** Campus energy management systems are often fragmented, reactive, and lack predictive capabilities, leading to inefficient energy usage and increased operational costs.

**Our Solution:** GreenPulse provides a unified platform with real-time monitoring, AI-powered analytics, and actionable insights to optimize campus energy consumption and reduce environmental impact.

**Context:** This project was developed as a hackathon prototype to demonstrate modern web development practices and smart energy management concepts.

## ✨ Features

### 🎯 Core Functionality
- 📊 **Real-time Energy Dashboard** - Live monitoring of campus energy consumption
- 🏢 **Multi-Building Management** - Monitor multiple campus buildings simultaneously
- 📈 **Interactive Analytics** - Visual charts and graphs for energy patterns
- 🤖 **AI-Powered Insights** - Smart recommendations for energy optimization
- 🔄 **WebSocket Integration** - Real-time data updates without page refresh
- 📱 **Responsive Design** - Works seamlessly across desktop and mobile devices

### 🎨 UI/UX Features
- 🌟 **Glassmorphism Design** - Modern, elegant user interface
- 🌙 **Dark/Light Theme** - Customizable viewing experience
- 📊 **Interactive Charts** - Built with Chart.js for engaging data visualization
- 🎯 **Intuitive Navigation** - User-friendly interface design

### 🚀 Technical Features
- ⚡ **High Performance** - Fast API responses and optimized frontend
- 🔐 **Secure Architecture** - CORS protection and secure API endpoints
- 🐳 **Containerized Deployment** - Docker support for easy deployment
- ☁️ **Cloud Ready** - AWS deployment configurations included
- 📝 **API Documentation** - Auto-generated OpenAPI/Swagger docs

## 🛠️ Tech Stack

### Frontend
- **Framework:** Angular 17
- **Language:** TypeScript
- **Styling:** SCSS with Glassmorphism effects
- **Charts:** Chart.js
- **HTTP Client:** Angular HttpClient
- **Real-time:** WebSocket integration

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL with TimescaleDB
- **Caching:** Redis
- **Authentication:** JWT tokens
- **WebSockets:** Native FastAPI WebSocket support
- **Validation:** Pydantic models

### Infrastructure & DevOps
- **Containerization:** Docker & Docker Compose
- **Cloud Platform:** AWS (EC2, RDS, S3, CloudFront)
- **Web Server:** Nginx (reverse proxy)
- **Process Management:** Uvicorn with Gunicorn
- **Monitoring:** Built-in health checks

### Data & Analytics
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** Scikit-learn
- **Time Series:** TimescaleDB extensions
- **Data Format:** ASHRAE Building Performance Dataset

## 🚀 Installation & Setup

### Prerequisites
- **Node.js** (v18 or higher)
- **Python** (3.7 or higher)
- **PostgreSQL** (12 or higher)
- **Docker** (optional, for containerized setup)

### Quick Start (Local Development)

1. **Clone the repository**
```bash
git clone https://github.com/surajsk2003/GreenPulse.git
cd GreenPulse
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run the backend
python -m app.main
```

3. **Frontend Setup**
```bash
cd frontend/greenpulse-dashboard
npm install

# Start development server
ng serve
```

4. **Database Setup (Optional)**
```bash
# Using Docker
docker-compose up -d db redis

# Or set up PostgreSQL manually and create database
createdb greenpulse
```

### 🐳 Docker Setup (Recommended)

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access the application:**
- Frontend: http://localhost:4200
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📖 Usage

### Dashboard Navigation

1. **Building Selection**
   - Choose from available campus buildings
   - View building-specific energy metrics

2. **Real-time Monitoring**
   - Monitor live energy consumption
   - Track cost and carbon emissions
   - View efficiency scores

3. **Analytics & Insights**
   - Analyze historical energy patterns
   - View optimization recommendations
   - Compare building performance

4. **Leaderboard**
   - See building efficiency rankings
   - Track improvement metrics
   - Identify top performers

### API Integration

The REST API provides programmatic access to all features:

```bash
# Get building list
curl http://localhost:8000/api/buildings

# Get real-time analytics
curl http://localhost:8000/api/analytics/campus/stats

# Access API documentation
open http://localhost:8000/docs
```

## 🏗️ Project Architecture

```
GreenPulse/
├── frontend/                    # Angular application
│   └── greenpulse-dashboard/
│       ├── src/
│       │   ├── app/
│       │   │   ├── components/  # Angular components
│       │   │   └── services/    # HTTP services
│       │   └── environments/    # Environment configs
│       └── package.json
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── core/               # Configuration & database
│   │   ├── routers/            # API route handlers
│   │   ├── models/             # Pydantic models
│   │   └── main.py             # Application entry point
│   └── requirements.txt
├── docker-config/              # Docker configurations
│   ├── docker-compose.yml
│   └── nginx.conf
├── ml-models/                  # Machine learning modules
├── ashrae-energy-data/         # Energy dataset
└── deploy-aws.sh              # AWS deployment script
```

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Angular)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 4200    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────────────────────────────────────────────────────────┐
    │                     Docker Network                          │
    └─────────────────────────────────────────────────────────────┘
```

## 📚 API Documentation

The API follows RESTful principles and provides comprehensive documentation:

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API docs |
| GET | `/api/buildings` | List all buildings |
| GET | `/api/analytics/campus/stats` | Campus-wide statistics |
| GET | `/api/insights/recommendations` | AI recommendations |
| WebSocket | `/api/ws` | Real-time data stream |

### Response Format

All API responses follow a consistent format:

```json
{
  "status": "success",
  "data": {
    // Actual response data
  },
  "total": 42,
  "message": "Optional message"
}
```

## ☁️ Deployment

### AWS Cloud Deployment

The project includes automated AWS deployment with the following architecture:

- **Frontend:** S3 Static Website + CloudFront CDN
- **Backend:** EC2 instance with Nginx reverse proxy
- **Database:** RDS PostgreSQL (optional)
- **Storage:** S3 for static assets

```bash
# Configure AWS CLI
aws configure

# Deploy to AWS (update script with your credentials first)
chmod +x deploy-aws.sh
./deploy-aws.sh
```

**Note:** Update the deployment script with your specific AWS credentials and configuration before running.

### Local Production Setup

```bash
# Build frontend for production
cd frontend/greenpulse-dashboard
ng build --configuration=production

# Run backend with Gunicorn
cd ../../backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🧩 Known Issues

As this is a **prototype**, there are several known limitations:

### Current Limitations
- 🔧 **Database Integration:** Some endpoints use mock data instead of live database
- 📊 **ML Models:** Machine learning features are placeholder implementations
- 🔐 **Authentication:** User authentication system not fully implemented
- 📱 **Mobile Optimization:** Some UI components need mobile refinement
- 🔄 **Data Validation:** Limited input validation on some forms

### Mock Data Usage
Currently using mock data for:
- Building energy readings
- Historical analytics
- ML model predictions
- User management

## 🛠️ Future Work

### Phase 1: Data Integration
- [ ] Connect real energy monitoring hardware
- [ ] Implement ASHRAE dataset processing
- [ ] Add real-time data ingestion pipeline
- [ ] Create data validation and cleaning workflows

### Phase 2: AI/ML Enhancement
- [ ] Develop energy consumption prediction models
- [ ] Implement anomaly detection algorithms
- [ ] Add optimization recommendation engine
- [ ] Create automated reporting system

### Phase 3: Production Features
- [ ] User authentication and authorization
- [ ] Multi-tenant campus support
- [ ] Advanced dashboard customization
- [ ] Mobile application development
- [ ] Integration with campus management systems

### Phase 4: Advanced Analytics
- [ ] Carbon footprint tracking
- [ ] Cost optimization algorithms
- [ ] Predictive maintenance alerts
- [ ] Weather-based energy forecasting
- [ ] Sustainability reporting

## 🤝 Contributing

Contributions are welcome! This project serves as a foundation for energy management solutions.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Backend:** Follow PEP 8 for Python code
- **Frontend:** Use Angular style guide and TypeScript best practices
- **Comments:** Document complex logic and API endpoints
- **Testing:** Add tests for new features (when applicable)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Suraj Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 👨‍💻 Author

**Suraj Kumar**  
B.Tech, NITK Surathkal

[![Portfolio](https://img.shields.io/badge/Portfolio-surajsk2003.github.io-blue)](https://surajsk2003.github.io/Suraj.in/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/suraj-singh-96b45220a/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/surajsk2003)

---

## 🙏 Acknowledgments

- **ASHRAE:** For providing the building performance dataset
- **FastAPI Community:** For excellent documentation and support
- **Angular Team:** For the robust frontend framework
- **Open Source Community:** For the various libraries and tools used

---

## ⚠️ Prototype Disclaimer

**This is a prototype/proof-of-concept developed for educational and demonstration purposes.** 

- Not intended for production use without further development
- Mock data is used in several components
- Security features require enhancement for production deployment
- Database connections and ML models need real-world calibration

For production deployment, additional work is required in security, scalability, and data integration.

---

<div align="center">

**🌱 Built with passion for sustainable energy management 🌍**

*If this project helped you or inspired your work, please consider giving it a ⭐*

</div>